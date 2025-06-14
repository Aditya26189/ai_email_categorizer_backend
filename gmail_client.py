import os
import json
from typing import List, Dict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from classifier import classify_email
from storage import storage
from utils.gmail_parser import extract_email_body
from utils.llm_utils import summarize_to_bullets

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Get authenticated Gmail API service."""
    creds = None
    
    # Load credentials from token_gmail.json if it exists
    if os.path.exists('token_gmail.json'):
        with open('token_gmail.json', 'r') as token:
            creds = Credentials.from_authorized_user_info(json.load(token))
    
    # If credentials are invalid or don't exist, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open('token_gmail.json', 'w') as token:
            token.write(creds.to_json())
    
    # Build and return Gmail service
    return build('gmail', 'v1', credentials=creds)

def get_latest_emails(max_results: int = 10) -> List[Dict]:
    """
    Fetch latest unread emails from Gmail.
    
    Args:
        max_results (int): Maximum number of emails to fetch
        
    Returns:
        List[Dict]: List of email data including subject, body, category, and summary
    """
    try:
        # Get Gmail service
        service = get_gmail_service()
        
        # Get list of unread messages
        results = service.users().messages().list(
            userId='me',
            labelIds=['UNREAD'],
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        if not messages:
            print("No unread messages found.")
            return []
        
        processed_emails = []
        for message in messages:
            # Get full message details
            msg = service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()
            
            # Extract headers
            headers = msg['payload']['headers']
            subject = next(
                (h['value'] for h in headers if h['name'].lower() == 'subject'),
                '(No Subject)'
            )
            
            # Extract and decode email body using our parser
            body = extract_email_body(msg['payload'])
            
            # Generate summary for every email
            summary = summarize_to_bullets(body)
            
            # Classify the email
            category = classify_email(subject, body)
            if category.startswith("Error:"):
                print(f"❌ Classification failed for '{subject}': {category}")
                continue
            
            # Prepare email data with summary
            email_data = {
                'subject': subject,
                'body': body,
                'category': category,
                'gmail_id': message['id'],
                'summary': summary  # Include the summary
            }
            
            # Save to MongoDB
            if storage.save_email(email_data):
                processed_emails.append(email_data)
                print(f"✅ Processed and saved: {subject}")
            else:
                print(f"⚠️ Skipped duplicate: {subject}")
        
        return processed_emails
        
    except Exception as e:
        print(f"❌ Error fetching emails: {str(e)}")
        return []

def fetch_emails_from_gmail(limit: int = 5) -> List[Dict[str, str]]:
    """
    Fetches the latest `limit` emails from the user's Gmail inbox.
    
    Args:
        limit (int): Maximum number of emails to fetch
        
    Returns:
        List[Dict[str, str]]: List of email data with subject and snippet
    """
    try:
        # Get Gmail service
        service = get_gmail_service()
        
        # Get list of messages
        results = service.users().messages().list(
            userId='me',
            maxResults=limit
        ).execute()
        
        messages = results.get('messages', [])
        if not messages:
            print("No messages found.")
            return []
        
        emails = []
        for message in messages:
            # Get message details
            msg = service.users().messages().get(
                userId='me',
                id=message['id'],
                format='metadata',
                metadataHeaders=['Subject']
            ).execute()
            
            # Extract subject
            headers = msg['payload']['headers']
            subject = next(
                (h['value'] for h in headers if h['name'].lower() == 'subject'),
                '(No Subject)'
            )
            
            # Get snippet
            snippet = msg.get('snippet', '')
            
            emails.append({
                'subject': subject,
                'snippet': snippet
            })
        
        return emails
        
    except Exception as e:
        print(f"Error fetching emails: {str(e)}")
        return []

if __name__ == "__main__":
    # Test the email fetching
    print("Fetching latest unread emails...")
    emails = get_latest_emails()
    print(f"\nProcessed {len(emails)} emails.")

    print("\nFetching latest emails...")
    emails = fetch_emails_from_gmail(limit=5)
    print(f"\nFetched {len(emails)} emails:")
    for email in emails:
        print(f"\nSubject: {email['subject']}")
        print(f"Snippet: {email['snippet']}") 