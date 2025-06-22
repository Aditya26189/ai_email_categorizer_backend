from app.services.gmail_client import get_latest_emails
from app.db.base import get_user_history_id, set_user_history_id

async def fetch_and_process_new_emails(user_id: str, max_results: int = 10):
    """
    Fetch and process new emails using the user's last historyId.
    This is a fallback method when incremental sync is not available.
    """
    # Get the user's last processed historyId
    last_history_id = await get_user_history_id(user_id)
    emails = await get_latest_emails(user_id, max_results, last_history_id=last_history_id)
    
    # The Gmail client already handles classification, summarization, and saving
    # So we just need to track the highest historyId seen
    processed_count = len(emails)
    new_history_id = None
    
    for email in emails:
        # Track the highest historyId seen
        if email.get('history_id'):
            if not new_history_id or int(email['history_id']) > int(new_history_id):
                new_history_id = email['history_id']
    
    # Update the user's last_history_id if we saw a new one
    if new_history_id:
        await set_user_history_id(user_id, new_history_id)
        print(f"Updated user {user_id} last_history_id to: {new_history_id}")
    
    return processed_count 