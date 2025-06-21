from fastapi import APIRouter, Request, HTTPException
from app.services.user_sync import create_user_from_clerk, update_user_from_clerk
from app.db.base import get_mongo_client
import logging

router = APIRouter()

@router.post("/webhook/clerk")
async def clerk_webhook(request: Request):
    try:
        payload = await request.json()
        event_type = payload.get("type")
        data = payload.get("data")

        if not event_type or not data:
            raise HTTPException(status_code=400, detail="Invalid Clerk webhook payload.")

        if event_type == "user.created":
            logging.info("Webhook: user.created")
            await create_user_from_clerk(data)
        elif event_type == "user.updated":
            logging.info("Webhook: user.updated")
            await update_user_from_clerk(data)
        elif event_type == "user.deleted":
            logging.info(f"Webhook: user.deleted for {data.get('id')}")
            db = get_mongo_client()
            result = await db["users"].delete_one({"clerk_user_id": data.get("id")})
            if result.deleted_count > 0:
                logging.info(f"Deleted user {data.get('id')} from MongoDB.")
            else:
                logging.warning(f"User {data.get('id')} not found for deletion.")
        else:
            logging.warning(f"Unhandled event type: {event_type}")

        return {"status": "ok"}

    except Exception as e:
        logging.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing failed.") 