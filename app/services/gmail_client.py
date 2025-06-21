import os
import json
from typing import List, Dict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from app.services.classifier import classify_email
from app.db.email_db import email_db
from app.utils.gmail_parser import extract_email_body
from app.utils.llm_utils import summarize_to_bullets
from datetime import datetime
from loguru import logger
import re
from app.services.token_refresh import get_valid_access_token
from app.services.google_oauth import google_oauth_service
from app.db.base import get_mongo_client
from app.core.config import settings

# Gmail API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.settings.basic"
]

async def get_gmail_service_for_user(user_id: str):
    """
    Get authenticated Gmail API service for a specific user.
    
    Args:
        user_id (str): Clerk user ID
        
    Returns:
        Gmail service object
        
    Raises:
        Exception: If authentication fails
    """
    try:
        # Get user credentials from OAuth service
        credentials = await google_oauth_service.get_user_credentials(user_id)
        
        if not credentials:
            # Try to refresh token
            access_token = await get_valid_access_token(user_id)
            
            # Get updated credentials
            credentials = await google_oauth_service.get_user_credentials(user_id)
            
            if not credentials:
                raise Exception(f"No valid credentials found for user: {user_id}")
        
        # Build and return Gmail service
        return build('gmail', 'v1', credentials=credentials)
        
    except Exception as e:
        logger.error(f"Error getting Gmail service for user {user_id}: {e}")
        raise

async def get_latest_emails(user_id: str, max_results: int = 10) -> List[Dict]:
    """
    Fetch latest unread emails from Gmail for a specific user.
    Args:
        user_id (str): Clerk user ID
        max_results (int): Maximum number of emails to fetch
    Returns:
        List[Dict]: List of email data including subject, body, category, and summary
    """
    try:
        # Get Gmail service for user
        service = await get_gmail_service_for_user(user_id)
        
        # Get list of unread messages
        results = service.users().messages().list(
            userId='me',
            labelIds=['UNREAD'],
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        if not messages:
            logger.info("No unread messages found.")
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
            
            # Extract subject
            subject = next(
                (h['value'] for h in headers if h['name'].lower() == 'subject'),
                '(No Subject)'
            )
            
            # Extract sender email and name
            from_header = next(
                (h['value'] for h in headers if h['name'].lower() == 'from'),
                ''
            )
            sender_name = None
            sender_email = None
            match = re.match(r'"?(.*?)"?\s*<([^>]+)>', from_header)
            if match:
                sender_name = match.group(1).strip() or None
                sender_email = match.group(2).strip()
            elif '@' in from_header:
                sender_email = from_header.strip()
            else:
                sender_email = from_header.strip()
            logger.info(f"📧 Processing email from: {sender_name} <{sender_email}>")
            
            # Extract date from email headers
            date_header = next(
                (h['value'] for h in headers if h['name'].lower() == 'date'),
                None
            )
            
            if date_header:
                try:
                    # Parse the email date header (e.g., "Wed, 13 Mar 2024 15:30:45 +0000")
                    from email.utils import parsedate_to_datetime
                    timestamp = parsedate_to_datetime(date_header).isoformat()
                    logger.info(f"📅 Email sent date: {timestamp}")
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing date header: {e}")
                    # Fallback to internal date if parsing fails
                    timestamp = datetime.fromtimestamp(int(msg['internalDate']) / 1000).isoformat()
                    logger.warning(f"⚠️ Using internal date instead: {timestamp}")
            else:
                # Fallback to internal date if no date header
                timestamp = datetime.fromtimestamp(int(msg['internalDate']) / 1000).isoformat()
                logger.warning(f"⚠️ No date header found, using internal date: {timestamp}")
            
            # Extract and decode email body using our parser
            body = extract_email_body(msg['payload'])
            
            # Check if already processed using Gmail ID
            if await email_db.already_classified(message['id']):
                logger.warning(f"⚠️ Skipped duplicate: {subject} from {sender_name} <{sender_email}>")
                continue
            
            # Generate summary for new email
            summary = summarize_to_bullets(body)
            
            # Classify the email
            category = classify_email(subject, body)
            if category.startswith("Error:"):
                logger.error(f"❌ Classification failed for '{subject}': {category}")
                continue
            
            # Prepare email data with all new schema fields
            email_data = {
                'user_id': user_id,
                'gmail_id': message['id'],  # Store Gmail message ID
                'thread_id': msg.get('threadId'),
                'history_id': msg.get('historyId'),
                'label_ids': msg.get('labelIds', []),
                'subject': subject,
                'body': body,
                'category': category,
                'summary': summary,
                'sender_name': sender_name,
                'sender_email': sender_email,
                'timestamp': timestamp,
                'internal_date': msg.get('internalDate'),
                'is_read': False,  # Default, update if you track read status
                'is_processed': True,  # Mark as processed by AI
                'is_sensitive': False,  # Set based on your logic if needed
                'status': 'new',  # Default triage status
                'fetched_at': datetime.utcnow().isoformat(),
            }
            # Force user_id just before saving and log for debug
            email_data['user_id'] = user_id
            logger.debug(f"Saving email with user_id={email_data['user_id']} and gmail_id={email_data['gmail_id']} and sender_email={email_data['sender_email']}")
            # Save to MongoDB
            if await email_db.save_email(email_data):
                processed_emails.append(email_data)
                logger.success(f"✅ Processed and saved: {subject} from {sender_name} <{sender_email}>")
            else:
                logger.warning(f"⚠️ Skipped duplicate: {subject} from {sender_name} <{sender_email}>")
        
        return processed_emails
        
    except Exception as e:
        logger.error(f"❌ Error fetching emails: {str(e)}")
        return []

async def setup_gmail_watch(user_id: str):
    """
    Set up Gmail push notifications for a user.
    
    Args:
        user_id (str): Clerk user ID
        
    Returns:
        bool: True if watch was set up successfully
    """
    try:
        # Get Gmail service for user
        service = await get_gmail_service_for_user(user_id)
        
        # Set up watch on INBOX
        watch_request = {
            "labelIds": ["INBOX"],
            "topicName": f"projects/{settings.GOOGLE_PROJECT_ID}/topics/gmail-events"
        }
        
        response = service.users().watch(
            userId="me",
            body=watch_request
        ).execute()
        
        logger.info(f"✅ Gmail watch set up for user {user_id}: {response}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error setting up Gmail watch for user {user_id}: {e}")
        return False

async def fetch_emails_from_gmail(user_id: str, limit: int = 5) -> List[Dict[str, str]]:
    """
    Fetches the latest `limit` emails from the user's Gmail inbox.
    
    Args:
        user_id (str): Clerk user ID
        limit (int): Maximum number of emails to fetch
        
    Returns:
        List[Dict[str, str]]: List of email data with subject and snippet
    """
    try:
        # Get Gmail service for user
        service = await get_gmail_service_for_user(user_id)
        
        # Get list of messages
        results = service.users().messages().list(
            userId='me',
            maxResults=limit
        ).execute()
        
        messages = results.get('messages', [])
        if not messages:
            logger.info("No messages found.")
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
        logger.error(f"Error fetching emails: {str(e)}")
        return []

if __name__ == "__main__":
    import asyncio
    
    async def main():
        logger.info("Fetching latest unread emails...")
        emails = await get_latest_emails(user_id="clerk_user_id")
        logger.info(f"\nProcessed {len(emails)} emails.")

        logger.info("\nFetching latest emails...")
        emails = await fetch_emails_from_gmail(user_id="clerk_user_id", limit=5)
        logger.info(f"\nFetched {len(emails)} emails:")
        for email in emails:
            logger.info(f"\nSubject: {email['subject']}")
            logger.info(f"Snippet: {email['snippet']}")
    
    asyncio.run(main()) 