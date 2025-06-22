import os
import json
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from app.services.classifier import classify_email
from app.db import email_db
from app.utils.gmail_parser import extract_email_body
from app.utils.llm_utils import summarize_to_bullets
from datetime import datetime, timezone, timedelta
from loguru import logger
import re
from app.services.token_refresh import get_valid_access_token
from app.services.google_oauth import google_oauth_service
from app.db.base import get_mongo_client, db, set_user_history_id
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

async def process_and_save_gmail_message(msg, user_id: str) -> Optional[Dict]:
    """
    Process a Gmail message and save it to the database if not already processed.
    Returns the saved email data dict, or None if duplicate or error.
    """
    try:
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(No Subject)')
        from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')

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

        date_header = next((h['value'] for h in headers if h['name'].lower() == 'date'), None)
        if date_header:
            try:
                from email.utils import parsedate_to_datetime
                timestamp = parsedate_to_datetime(date_header).isoformat()
            except Exception as e:
                timestamp = datetime.fromtimestamp(int(msg['internalDate']) / 1000, timezone.utc).isoformat()
        else:
            timestamp = datetime.fromtimestamp(int(msg['internalDate']) / 1000, timezone.utc).isoformat()

        body = extract_email_body(msg['payload'])
        gmail_id = msg['id']

        # Check if already processed
        if await email_db.already_classified(gmail_id):
            logger.warning(f"⚠️ Skipped duplicate: {subject} from {sender_name} <{sender_email}>")
            return None

        summary = summarize_to_bullets(body)
        category = classify_email(subject, body)
        if category.startswith("Error:"):
            logger.error(f"❌ Classification failed for '{subject}': {category}")
            return None

        # Generate Gmail URL for direct access
        gmail_url = f"https://mail.google.com/mail/u/0/#inbox/{gmail_id}"

        email_data = {
            'user_id': user_id,
            'gmail_id': gmail_id,
            'gmail_url': gmail_url,
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
            'is_read': False,
            'is_processed': True,
            'is_sensitive': False,
            'status': 'new',
            'fetched_at': datetime.now(timezone.utc).isoformat(),
        }

        if await email_db.save_email(email_data):
            logger.success(f"✅ Processed and saved: {subject} from {sender_name} <{sender_email}>")
            return email_data
        else:
            logger.warning(f"⚠️ Skipped duplicate: {subject} from {sender_name} <{sender_email}>")
            return None
    except Exception as e:
        logger.error(f"❌ Error processing message {msg.get('id', 'unknown')}: {e}")
        return None

async def get_incremental_emails(user_id: str, last_history_id: str) -> List[Dict]:
    """
    Fetch emails incrementally using Gmail's history API since the last_history_id.
    """
    try:
        service = await get_gmail_service_for_user(user_id)
        # Fetch history since last_history_id
        history = service.users().history().list(
            userId='me',
            startHistoryId=last_history_id,
            historyTypes=['messageAdded']
        ).execute()
        
        # Extract the current historyId from response for future requests
        current_history_id = history.get('historyId')
        if current_history_id:
            logger.info(f"📋 Current historyId from Gmail: {current_history_id}")
        
        history_records = history.get('history', [])
        if not history_records:
            logger.info(f"📭 No new messages found since historyId: {last_history_id}")
            # Still update to current historyId for future requests
            if current_history_id:
                from app.db.base import set_user_history_id
                await set_user_history_id(user_id, current_history_id)
                logger.info(f"✅ Updated user {user_id} historyId to: {current_history_id}")
            return []
        
        messages = []
        for record in history_records:
            for msg in record.get('messagesAdded', []):
                messages.append(msg['message'])
        if not messages:
            logger.info(f"📭 No new messages in history since historyId: {last_history_id}")
            # Still update to current historyId for future requests
            if current_history_id:
                from app.db.base import set_user_history_id
                await set_user_history_id(user_id, current_history_id)
                logger.info(f"✅ Updated user {user_id} historyId to: {current_history_id}")
            return []
        
        logger.info(f"📧 Found {len(messages)} new messages since historyId: {last_history_id}")
        processed_emails = []
        for message in messages:
            try:
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                processed = await process_and_save_gmail_message(msg, user_id)
                if processed:
                    processed_emails.append(processed)
            except Exception as e:
                logger.error(f"❌ Error processing message {message['id']}: {e}")
                continue
        
        # Update to current historyId for future requests
        if current_history_id:
            from app.db.base import set_user_history_id
            await set_user_history_id(user_id, current_history_id)
            logger.info(f"✅ Updated user {user_id} historyId to: {current_history_id}")
        
        logger.info(f"📊 Incremental sync complete: {len(processed_emails)} emails processed")
        return processed_emails
    except Exception as e:
        logger.error(f"❌ Error fetching incremental emails: {str(e)}")
        return []

# Update get_latest_emails to use incremental sync if last_history_id is provided
async def get_latest_emails(user_id: str, max_results: int = 10, last_history_id: str = None) -> List[Dict]:
    if last_history_id:
        return await get_incremental_emails(user_id, last_history_id)
    try:
        service = await get_gmail_service_for_user(user_id)
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
            msg = service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()
            processed = await process_and_save_gmail_message(msg, user_id)
            if processed:
                processed_emails.append(processed)
        return processed_emails
    except Exception as e:
        logger.error(f"❌ Error fetching emails: {str(e)}")
        return []

async def get_current_history_id(user_id: str) -> str:
    """
    Get the current historyId for a user from Gmail API.
    This is useful when the stored historyId is too old.
    """
    try:
        service = await get_gmail_service_for_user(user_id)
        profile = service.users().getProfile(userId='me').execute()
        return profile.get("historyId")
    except Exception as e:
        logger.error(f"❌ Error getting current historyId for user {user_id}: {e}")
        return None
    
async def handle_history_id_too_old(user_id: str, old_history_id: str) -> List[Dict]:
    """
    Handle the case when historyId is too old by doing a full sync.
    This is a fallback when incremental sync fails due to old historyId.
    """
    logger.warning(f"🔄 HistoryId {old_history_id} is too old for user {user_id}. Doing full sync.")
    
    try:
        # Get current historyId
        current_history_id = await get_current_history_id(user_id)
        if not current_history_id:
            logger.error(f"❌ Could not get current historyId for user {user_id}")
            return []
        
        # Do a full sync of recent emails (last 50)
        emails = await get_latest_emails(user_id, max_results=50, last_history_id=None)
        
        # Update to current historyId
        from app.db.base import set_user_history_id
        await set_user_history_id(user_id, current_history_id)
        logger.info(f"✅ Updated user {user_id} historyId from {old_history_id} to {current_history_id}")
        
        return emails
        
    except Exception as e:
        logger.error(f"❌ Error handling old historyId for user {user_id}: {e}")
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
        
        # Get user's email address from database
        user = await db.get_collection('users').find_one({"clerk_user_id": user_id})
        if not user or not user.get("email"):
            logger.error(f"❌ No email found for user {user_id}")
            return False
        
        user_email = user["email"]
        
        # Set up watch on INBOX - Python client doesn't support custom headers
        watch_request = {
            "labelIds": ["INBOX"],
            "topicName": settings.gmail_topic_name,
            "labelFilterAction": "include"
        }
        
        response = service.users().watch(
            userId="me",
            body=watch_request
        ).execute()
        
        logger.info(f"✅ Gmail watch set up for user {user_id} ({user_email}): {response}")
        # Store the initial historyId for incremental sync
        history_id = response.get("historyId")
        if history_id:
            await set_user_history_id(user_id, history_id)
            logger.info(f"[Gmail Watch] Set initial last_history_id for user {user_id}: {history_id}")
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