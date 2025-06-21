from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse
from loguru import logger
from app.core.config import settings
from app.services.google_oauth import google_oauth_service
from app.db.base import get_mongo_client
from datetime import datetime

router = APIRouter(tags=["oauth-callback"])

@router.get("/routers/v1/gmail/oauth/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State parameter for security")
):
    """
    Handle OAuth callback from Google (GET method for browser redirects).
    This endpoint does NOT require authentication as Google redirects users directly.
    
    Args:
        code: Authorization code from Google
        state: State parameter for security
        
    Returns:
        RedirectResponse: Redirects to frontend with success/error
    """
    try:
        logger.info(f"Processing OAuth callback with code: {code[:10]}... and state: {state}")
        
        # For now, we'll store the code temporarily and let the frontend complete the flow
        # This is because we don't have the user context here (no authentication)
        
        # Store the authorization code temporarily (you might want to use Redis or session storage)
        # For now, we'll just redirect to frontend with the code
        
        # Get frontend URL from settings
        frontend_url = settings.FRONTEND_URL or "http://localhost:3000"
        
        # Redirect to frontend with success
        redirect_url = f"{frontend_url}/dashboard/gmail-callback?success=true&code={code}&state={state}"
        
        logger.info(f"Redirecting to frontend: {redirect_url}")
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        
        # Get frontend URL from settings
        frontend_url = settings.FRONTEND_URL or "http://localhost:3000"
        
        # Redirect to frontend with error
        redirect_url = f"{frontend_url}/dashboard/gmail-callback?success=false&error={str(e)}"
        
        return RedirectResponse(url=redirect_url, status_code=302) 