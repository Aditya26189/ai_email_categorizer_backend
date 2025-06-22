from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
from app.services.email_ingestion import fetch_and_process_new_emails
from app.db.base import db, get_user_history_id, set_user_history_id
from app.services.gmail_client import get_incremental_emails, handle_history_id_too_old
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
    webhook_data = {}
    
    if encoded_data:
        try:
            decoded_bytes = base64.b64decode(encoded_data)
            decoded_json = json.loads(decoded_bytes)
            logging.info(f"[Webhook] Decoded Pub/Sub message: {decoded_json}")
            webhook_data = decoded_json
        except Exception as e:
            logging.error(f"[Webhook] Failed to decode Pub/Sub message: {e}")
            return JSONResponse(status_code=400, content={"error": "Failed to decode Pub/Sub message"})
    else:
        # Direct webhook (not through Pub/Sub)
        webhook_data = data

    # Extract email address and historyId from webhook data
    email_address = webhook_data.get("emailAddress")
    webhook_history_id = webhook_data.get("historyId")
    
    if not email_address:
        # Fallback to header or JSON body
        email_address = request.headers.get("X-Goog-Channel-Token")
        if not email_address:
            email_address = data.get("emailAddress")
    
    if not email_address:
        logging.error("[Webhook] No email found in headers or JSON payload")
        return JSONResponse(status_code=400, content={"error": "No email address found"})

    logging.info(f"[Webhook] Push notification for: {email_address}, historyId: {webhook_history_id}")

    # Convert email → user_id from DB
    user_id = await get_user_id_by_email(email_address)
    if not user_id:
        logging.error(f"[Webhook] No user found for email: {email_address}")
        return JSONResponse(status_code=404, content={"error": "User not found"})

    # If we have a webhook_history_id, process only the emails added in that event
    processed_count = 0
    if webhook_history_id:
        try:
            from app.services.gmail_client import get_gmail_service_for_user, process_and_save_gmail_message
            service = await get_gmail_service_for_user(user_id)
            
            # Get user's last known historyId
            last_history_id = await get_user_history_id(user_id)
            logging.info(f"[Webhook] User's last_history_id: {last_history_id}, webhook_history_id: {webhook_history_id}")
            
            if last_history_id:
                # Use the user's last historyId to get changes since last sync
                logging.info(f"[Webhook] Fetching history since {last_history_id}")
                history_response = service.users().history().list(
                    userId='me',
                    startHistoryId=last_history_id,
                    historyTypes=['messageAdded'],
                    maxResults=10
                ).execute()
                
                logging.info(f"[Webhook] History response: {history_response}")
                
                # Extract the current historyId from response for future requests
                current_history_id = history_response.get('historyId')
                if current_history_id:
                    logging.info(f"[Webhook] Current historyId from Gmail: {current_history_id}")
                
                history_records = history_response.get('history', [])
                logging.info(f"[Webhook] Found {len(history_records)} history records")
                
                if not history_records:
                    logging.info(f"[Webhook] No new messages found in history")
                    # Still update to current historyId for future requests
                    if current_history_id:
                        await set_user_history_id(user_id, current_history_id)
                        logging.info(f"[Webhook] Updated user {user_id} last_history_id to: {current_history_id}")
                else:
                    message_ids = []
                    for record in history_records:
                        messages_added = record.get('messagesAdded', [])
                        logging.info(f"[Webhook] Record has {len(messages_added)} messagesAdded")
                        for msg in messages_added:
                            message_ids.append(msg['message']['id'])
                    logging.info(f"[Webhook] Message IDs to process: {message_ids}")
                    
                    for msg_id in message_ids:
                        try:
                            msg = service.users().messages().get(
                                userId='me',
                                id=msg_id,
                                format='full'
                            ).execute()
                            # Process and save the email using the reusable function
                            processed = await process_and_save_gmail_message(msg, user_id)
                            if processed:
                                processed_count += 1
                                logging.info(f"[Webhook] Successfully processed email: {processed.get('subject', 'No Subject')} (ID: {msg_id})")
                            else:
                                logging.info(f"[Webhook] Email already processed or failed: {msg_id}")
                        except Exception as e:
                            logging.error(f"[Webhook] Error processing message {msg_id}: {e}")
                    
                    # Update to current historyId for future requests
                    if current_history_id:
                        await set_user_history_id(user_id, current_history_id)
                        logging.info(f"[Webhook] Updated user {user_id} last_history_id to: {current_history_id}")
            else:
                # No previous historyId, do a regular sync
                logging.info(f"[Webhook] No previous historyId found, doing regular sync")
                processed_count = await fetch_and_process_new_emails(user_id)
            
            # Update the user's last_history_id to the webhook's historyId as fallback
            if not current_history_id:
                await set_user_history_id(user_id, webhook_history_id)
                logging.info(f"[Webhook] Updated user {user_id} last_history_id to webhook historyId: {webhook_history_id}")
            
        except Exception as e:
            logging.error(f"[Webhook] Error processing specific historyId: {e}")
            # Fallback to regular processing
            processed_count = await fetch_and_process_new_emails(user_id)
    else:
        # Fallback to regular processing if no historyId
        logging.info(f"[Webhook] No historyId available, using regular processing")
        processed_count = await fetch_and_process_new_emails(user_id)
    
    logging.info(f"[Webhook] {processed_count} email(s) processed and saved for user_id={user_id}")
    
    return JSONResponse(content={"status": "success", "processed": processed_count}) 