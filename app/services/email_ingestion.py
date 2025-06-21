from app.services.gmail_client import get_latest_emails
from app.services.classifier import classify_email
from app.utils.llm_utils import summarize_to_bullets
from app.db.email_db import email_db
from app.db.base import get_user_history_id, set_user_history_id

async def fetch_and_process_new_emails(user_id: str, max_results: int = 10):
    # Get the user's last processed historyId
    last_history_id = await get_user_history_id(user_id)
    emails = await get_latest_emails(user_id, max_results, last_history_id=last_history_id)
    processed_count = 0
    new_history_id = None
    for email in emails:
        category = classify_email(email['subject'], email['body'])
        summary = summarize_to_bullets(email['body'])
        if summary and category:
            email_doc = {
                **email,
                'user_id': user_id,
                'category': category,
                'summary': summary
            }
            await email_db.save_email(email_doc)
            processed_count += 1
            # Track the highest historyId seen
            if email.get('history_id'):
                if not new_history_id or int(email['history_id']) > int(new_history_id):
                    new_history_id = email['history_id']
    # Update the user's last_history_id if we saw a new one
    if new_history_id:
        await set_user_history_id(user_id, new_history_id)
    return processed_count 