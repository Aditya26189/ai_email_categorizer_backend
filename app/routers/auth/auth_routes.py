from fastapi import APIRouter, Request, HTTPException, Depends, Body
from loguru import logger
from app.core.clerk import clerk_auth
from app.core.logger import log_request, log_auth_event
from app.models.user import UserInDB as User
from app.db.base import get_mongo_client
from app.services.google_oauth import google_oauth_service

router = APIRouter(tags=["auth"])

@router.get("/me", response_model=User)
async def get_me(user=Depends(clerk_auth)):
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
    
    email = db_user.get("email")
    if not email or "@" not in email:
        logger.error(f"User in DB has invalid email: {email}")
        raise HTTPException(status_code=500, detail="User record has invalid email address.")
    
    # Get Gmail connection status
    try:
        gmail_status = await google_oauth_service.check_gmail_connection_status(clerk_user_id)
        db_user["is_gmail_connected"] = gmail_status.get("is_gmail_connected", False)
        db_user["gmail_email"] = gmail_status.get("gmail_email")
        db_user["gmail_connected_at"] = gmail_status.get("gmail_connected_at")
    except Exception as e:
        logger.warning(f"Could not fetch Gmail status for user {clerk_user_id}: {e}")
        db_user["is_gmail_connected"] = False
        db_user["gmail_email"] = None
        db_user["gmail_connected_at"] = None
    
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
