from fastapi import APIRouter, Request, HTTPException, Depends, Body
from loguru import logger
from app.core.clerk import clerk_auth, verify_clerk_jwt
from app.core.logger import log_request, log_auth_event
from app.models.user import UserInDB as User
from app.db.base import get_mongo_client
from app.services.google_oauth import google_oauth_service
from datetime import datetime

router = APIRouter(tags=["auth"])

@router.get("/me", response_model=User)
async def get_me(user=Depends(clerk_auth), request: Request = None):
    """
    Get current user profile with Gmail connection status.
    
    Returns:
        User: User profile with Gmail status information
    """
    logger.info(f"[DEBUG] Clerk token payload: {user}")
    clerk_user_id = user.get("clerk_user_id") or user.get("sub")
    if not clerk_user_id:
        raise HTTPException(status_code=400, detail="No Clerk user ID found in token.")
    
    db = get_mongo_client()
    db_user = await db["users"].find_one({"clerk_user_id": clerk_user_id})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if db_user.get("_id") is not None:
        db_user["_id"] = str(db_user["_id"])
    
    # Get email from Clerk JWT token
    auth_header = request.headers.get("authorization") if request else None
    clerk_email = None
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            jwt_payload = await verify_clerk_jwt(token)
            clerk_email = jwt_payload.get("email")
        except Exception as e:
            logger.warning(f"Could not extract email from JWT: {e}")
    
    email = db_user.get("email")
    if not email or email is None or "@" not in str(email):
        logger.warning(f"User in DB has invalid email: {email}, using Clerk email as fallback")
        if clerk_email and "@" in clerk_email:
            # Update the user record with the Clerk email
            await db["users"].update_one(
                {"clerk_user_id": clerk_user_id},
                {"$set": {"email": clerk_email, "updated_at": datetime.utcnow().isoformat()}}
            )
            db_user["email"] = clerk_email
            logger.info(f"Updated user email from Clerk: {clerk_email}")
        else:
            logger.error(f"User has no valid email in DB or Clerk token")
            raise HTTPException(status_code=500, detail="User record has invalid email address.")
    
    # Get Gmail connection status directly from database
    # This ensures we get the latest status that was updated during OAuth
    is_gmail_connected = db_user.get("is_gmail_connected", False)
    gmail_email = db_user.get("gmail_email")
    gmail_connected_at = db_user.get("gmail_connected_at")
    
    logger.info(f"🔍 Gmail connection status for user {clerk_user_id}:")
    logger.info(f"  - is_gmail_connected: {is_gmail_connected}")
    logger.info(f"  - gmail_email: {gmail_email}")
    logger.info(f"  - gmail_connected_at: {gmail_connected_at}")
    
    # Ensure the fields are set in the response
    db_user["is_gmail_connected"] = is_gmail_connected
    db_user["gmail_email"] = gmail_email
    db_user["gmail_connected_at"] = gmail_connected_at
    
    return User(**db_user)

@router.post("/register", response_model=User)
async def register_user(user_in: User = Body(...)):
    # Create a new user in the database
    user_data = user_in.dict(by_alias=True)
    db = get_mongo_client()
    success = await db["users"].insert_one(user_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create user.")
    return user_in

@router.patch("/me", response_model=User)
async def update_me(update: dict = Body(...), user=Depends(clerk_auth)):
    clerk_user_id = user.get("clerk_user_id") or user.get("sub")
    if not clerk_user_id:
        raise HTTPException(status_code=400, detail="No Clerk user ID found in token.")
    db = get_mongo_client()
    result = await db["users"].update_one({"clerk_user_id": clerk_user_id}, {"$set": update})
    if result.modified_count == 0:
        logger.warning(f"No user updated for clerk_user_id: {clerk_user_id}")
        raise HTTPException(status_code=500, detail="Failed to update user.")
    db_user = await db["users"].find_one({"clerk_user_id": clerk_user_id})
    return User(**db_user)
