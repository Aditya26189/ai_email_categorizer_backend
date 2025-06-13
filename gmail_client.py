from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import base64
import email
from email.mime.text import MIMEText
import pickle

# If modifying these scopes, delete the file token_gmail.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Get Gmail API service instance."""
    creds = None
    
    # The file token_gmail.json stores the user's access and refresh tokens
    if os.path.exists('token_gmail.json'):
        creds = Credentials.from_authorized_user_file('token_gmail.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token_gmail.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def get_latest_emails(n=5):
    """
    Fetch the latest n emails from Gmail.
    
    Args:
        n (int): Number of emails to fetch (default: 5)
        
    Returns:
        list: List of dictionaries containing email subject and body
    """
    try:
        # Get Gmail service
        service = get_gmail_service()
        
        # Get list of messages
        results = service.users().messages().list(
            userId='me', 
            maxResults=n,
            labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return []
        
        emails = []
        for message in messages:
            msg = service.users().messages().get(
                userId='me', 
                id=message['id'],
                format='full'
            ).execute()
            
            # Get email headers
            headers = msg['payload']['headers']
            subject = next(
                (header['value'] for header in headers if header['name'].lower() == 'subject'),
                '(No Subject)'
            )
            
            # Get email body
            body = ''
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                        break
            elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
                body = base64.urlsafe_b64decode(
                    msg['payload']['body']['data']
                ).decode('utf-8')
            
            emails.append({
                'subject': subject,
                'body': body
            })
        
        return emails
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []

if __name__ == '__main__':
    # Test the function
    emails = get_latest_emails(5)
    for i, email in enumerate(emails, 1):
        print(f"\nEmail {i}:")
        print(f"Subject: {email['subject']}")
        print(f"Body: {email['body'][:200]}...")  # Print first 200 chars of body 