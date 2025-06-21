from app.services.gmail_client import get_latest_emails
from app.services.classifier import classify_email
from app.utils.llm_utils import summarize_to_bullets
from app.db.email_db import email_db

async def fetch_and_process_new_emails(user_id: str, max_results: int = 10):
    emails = await get_latest_emails(user_id, max_results)
    processed_count = 0
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
    return processed_count 