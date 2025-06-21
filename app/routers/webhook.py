from fastapi import APIRouter, Request, HTTPException
import logging
from app.services.email_ingestion import fetch_and_process_new_emails

router = APIRouter()

@router.post("/webhook/gmail")
async def gmail_push_webhook(request: Request):
    # Log webhook activation
    logging.info("[Webhook] /webhook/gmail endpoint activated")
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        logging.error("[Webhook] user_id missing in payload")
        raise HTTPException(status_code=400, detail="user_id is required in the webhook payload")
    logging.info(f"[Webhook] Gmail push notification received for user_id={user_id}")
    # Trigger email fetch pipeline
    processed_count = await fetch_and_process_new_emails(user_id)
    logging.info(f"[Webhook] {processed_count} email(s) processed and saved for user_id={user_id}")
    return {"status": "success", "processed": processed_count} 