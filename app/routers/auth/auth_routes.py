from fastapi import APIRouter, Request, HTTPException, Depends
from loguru import logger
from app.core.clerk import clerk_auth, get_clerk_user
from app.core.logger import log_request, log_auth_event

router = APIRouter(tags=["auth"])

@router.get("/me", summary="Get current user profile")
async def get_current_user(request: Request, _=Depends(clerk_auth)):
    """Get the current user's profile information."""
    try:
        user = await get_clerk_user(request)
        if not user:
            log_auth_event("user_not_found")
            raise HTTPException(status_code=401, detail="User not found")
        
        log_request(
            method="GET",
            path="/me",
            status_code=200,
            user_id=user["user_id"]
        )
        
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"]
        }
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        log_request(
            method="GET",
            path="/me",
            status_code=500,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/test-auth", summary="Test authentication")
async def test_auth(request: Request, _=Depends(clerk_auth)):
    """Test endpoint to verify Clerk authentication."""
    try:
        user = await get_clerk_user(request)
        if not user:
            log_auth_event("user_not_found")
            raise HTTPException(status_code=401, detail="User not found")
            
        log_request(
            method="GET",
            path="/test-auth",
            status_code=200,
            user_id=user["user_id"]
        )
        
        return {
            "status": "authenticated",
            "message": "Clerk authentication is working",
            "user": user
        }
    except Exception as e:
        logger.error(f"Authentication test failed: {e}")
        log_request(
            method="GET",
            path="/test-auth",
            status_code=401,
            error=str(e)
        )
        raise HTTPException(status_code=401, detail="Authentication failed")
