from fastapi import APIRouter, Request, HTTPException
from app.services.user_sync import create_user_from_clerk, update_user_from_clerk
import logging

router = APIRouter()

@router.post("/webhooks/clerk")
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
        else:
            logging.warning(f"Unhandled event type: {event_type}")

        return {"status": "ok"}

    except Exception as e:
        logging.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing failed.") 