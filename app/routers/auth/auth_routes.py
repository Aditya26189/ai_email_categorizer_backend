from fastapi import APIRouter, Request, HTTPException, Depends, Body
from loguru import logger
from app.core.clerk import clerk_auth
from app.core.logger import log_request, log_auth_event
from app.db.user_db import user_db
from app.models.schemas import User

router = APIRouter(tags=["auth"])

@router.get("/me", response_model=User)
async def get_me(user=Depends(clerk_auth)):
    logger.info(f"[DEBUG] Clerk token payload: {user}")

    clerk_user_id = user.get("clerk_user_id")
    if not clerk_user_id:
        raise HTTPException(status_code=400, detail="No Clerk user ID found in token.")
    db_user = await user_db.get_user_by_clerk_user_id(clerk_user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
    # Convert ObjectId to str for _id
    if db_user.get("_id") is not None:
        db_user["_id"] = str(db_user["_id"])
    # Ensure required fields are present and valid
    if db_user.get("clerk_id") is None and db_user.get("clerk_user_id"):
        db_user["clerk_id"] = db_user["clerk_user_id"]
    email = db_user.get("email")
    if not email or "@" not in email:
        logger.error(f"User in DB has invalid email: {email}")
        raise HTTPException(status_code=500, detail="User record has invalid email address.")
    return User(**db_user)


@router.post("/register", response_model=User)
async def register_user(user_in: User = Body(...)):
    # Create a new user in the database
    user_data = user_in.dict(by_alias=True)
    success = await user_db.create_user(user_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create user.")
    return user_in

@router.patch("/me", response_model=User)
async def update_me(update: dict = Body(...), user=Depends(clerk_auth)):
    # Update the current user's profile
    clerk_id = user.get("sub") or user.get("clerk_id")
    if not clerk_id:
        raise HTTPException(status_code=400, detail="No Clerk user ID found in token.")
    success = await user_db.update_user(clerk_id, update)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update user.")
    db_user = await user_db.get_user_by_clerk_id(clerk_id)
    return User(**db_user)
