from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
from app.services.email_ingestion import fetch_and_process_new_emails
from app.db.base import db
import base64
import json

router = APIRouter()

async def get_user_id_by_email(email_address: str) -> str:
    """Get user_id by email address from database."""
    try:
        user = await db.get_collection('users').find_one({"email": email_address})
        if user and user.get("clerk_user_id"):
            return user["clerk_user_id"]
        return None
    except Exception as e:
        logging.error(f"Error looking up user by email {email_address}: {e}")
        return None

@router.post("/webhook/gmail")
async def gmail_push_webhook(request: Request):
    # Log all headers for debugging
    headers = dict(request.headers)
    logging.info(f"[Webhook] Headers received: {headers}")
    
    logging.info("[Webhook] /webhook/gmail endpoint activated")

    # Get the JSON payload
    try:
        data = await request.json()
        logging.info(f"[Webhook] Payload received: {data}")
    except Exception as e:
        logging.error(f"[Webhook] Error parsing JSON payload: {e}")
        return JSONResponse(status_code=400, content={"error": "Invalid JSON payload"})

    # Handle Pub/Sub push: decode base64 message.data
    pubsub_message = data.get("message", {})
    encoded_data = pubsub_message.get("data")
    if encoded_data:
        try:
            decoded_bytes = base64.b64decode(encoded_data)
            decoded_json = json.loads(decoded_bytes)
            logging.info(f"[Webhook] Decoded Pub/Sub message: {decoded_json}")
            email_address = decoded_json.get("emailAddress")
        except Exception as e:
            logging.error(f"[Webhook] Failed to decode Pub/Sub message: {e}")
            return JSONResponse(status_code=400, content={"error": "Failed to decode Pub/Sub message"})
    else:
        # Try to get email from X-Goog-Channel-Token header first, then from JSON body
        email_address = request.headers.get("X-Goog-Channel-Token")
        if not email_address:
            email_address = data.get("emailAddress")
        if not email_address:
            logging.error("[Webhook] No email found in headers or JSON payload")
            return JSONResponse(status_code=400, content={"error": "No email address found"})

    logging.info(f"[Webhook] Push notification for: {email_address}")

    # Convert email → user_id from DB
    user_id = await get_user_id_by_email(email_address)
    if not user_id:
        logging.error(f"[Webhook] No user found for email: {email_address}")
        return JSONResponse(status_code=404, content={"error": "User not found"})

    # Trigger email fetch pipeline
    processed_count = await fetch_and_process_new_emails(user_id)
    logging.info(f"[Webhook] {processed_count} email(s) processed and saved for user_id={user_id}")
    
    return {"status": "success", "processed": processed_count} 