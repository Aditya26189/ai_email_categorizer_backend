from fastapi import APIRouter, HTTPException, Query, Depends, Body, Response
from fastapi.responses import RedirectResponse
from typing import Dict
from loguru import logger
from app.services.google_oauth import google_oauth_service
from app.services.gmail_client import setup_gmail_watch
from app.core.clerk import clerk_auth
from app.core.config import settings

router = APIRouter(prefix="/gmail", tags=["gmail"])

@router.get("/oauth/status")
async def get_oauth_status(user=Depends(clerk_auth)) -> Dict:
    """
    Check if the current user has Gmail connected.
    
    Returns:
        Dict: Gmail connection status information
    """
    try:
        clerk_user_id = user.get("clerk_user_id") or user.get("sub")
        logger.info(f"Checking Gmail connection status for user: {clerk_user_id}")
        
        # Check user's Gmail connection status
        status = await google_oauth_service.check_gmail_connection_status(clerk_user_id)
        
        return status
        
    except Exception as e:
        logger.error(f"Error checking Gmail connection status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check Gmail connection status: {str(e)}"
        )

@router.get("/oauth/start")
async def start_oauth_flow(user=Depends(clerk_auth)) -> Dict:
    """
    Start the Gmail OAuth flow by generating authorization URL with server-side state storage.
    
    Returns:
        Dict: Contains auth_url and state for frontend to redirect user
    """
    try:
        clerk_user_id = user.get("clerk_user_id") or user.get("sub")
        logger.info(f"🚀 Starting OAuth flow for user: {clerk_user_id}")
        
        # Check if user already has Gmail connected
        status = await google_oauth_service.check_gmail_connection_status(clerk_user_id)
        
        if status.get("is_connected", False):
            logger.info(f"ℹ️ User {clerk_user_id} already has Gmail connected")
            return {
                "already_connected": True,
                "user_id": clerk_user_id,
                "message": "Gmail is already connected"
            }
        
        # Generate OAuth URL
        auth_url, state = google_oauth_service.generate_auth_url()
        logger.info(f"📋 OAuth URL Generation:")
        logger.info(f"  - Generated state: {state}")
        logger.info(f"  - State length: {len(state)}")
        logger.info(f"  - Auth URL length: {len(auth_url)}")
        
        # Store state server-side for security validation
        state_stored = await google_oauth_service.store_oauth_state(state, clerk_user_id)
        
        if not state_stored:
            logger.error(f"❌ Failed to store OAuth state for user: {clerk_user_id}")
            raise HTTPException(
                status_code=500,
                detail="Failed to store OAuth state for security validation"
            )
        
        logger.info(f"✅ OAuth flow started successfully for user: {clerk_user_id}")
        logger.info(f"📋 OAuth Start Response:")
        logger.info(f"  - User ID: {clerk_user_id}")
        logger.info(f"  - State: {state}")
        logger.info(f"  - State stored: {state_stored}")
        logger.info(f"  - Already connected: False")
        
        return {
            "already_connected": False,
            "auth_url": auth_url,
            "state": state,  # Frontend can still use this for debugging
            "user_id": clerk_user_id,
            "message": "OAuth URL generated successfully with server-side state validation"
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting OAuth flow: {e}")
        logger.error(f"🔍 Error details:")
        logger.error(f"  - User ID: {clerk_user_id if 'clerk_user_id' in locals() else 'Unknown'}")
        logger.error(f"  - Error type: {type(e).__name__}")
        logger.error(f"  - Error message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start OAuth flow: {str(e)}"
        )

@router.get("/oauth/url")
async def get_oauth_url(user=Depends(clerk_auth)) -> Dict:
    """
    Generate OAuth URL for Gmail integration.
    
    Returns:
        Dict: Contains auth_url and state for frontend to redirect user
    """
    try:
        clerk_user_id = user.get("clerk_user_id") or user.get("sub")
        logger.info(f"Generating OAuth URL for user: {clerk_user_id}")
        
        auth_url, state = google_oauth_service.generate_auth_url()
        
        return {
            "auth_url": auth_url,
            "state": state,
            "user_id": clerk_user_id
        }
        
    except Exception as e:
        logger.error(f"Error generating OAuth URL: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate OAuth URL: {str(e)}"
        )

@router.post("/callback")
async def oauth_callback_post(
    code: str = Body(..., description="Authorization code from Google"),
    state: str = Body(..., description="State parameter for security"),
    user=Depends(clerk_auth)
) -> Dict:
    """
    Handle OAuth callback from Google with server-side state validation.
    
    Args:
        code: Authorization code from Google
        state: State parameter for security (validated server-side)
        
    Returns:
        Dict: OAuth result with user information
    """
    try:
        clerk_user_id = user.get("clerk_user_id") or user.get("sub")
        logger.info(f"🔄 Processing OAuth callback (POST) for user: {clerk_user_id}")
        logger.info(f"📋 OAuth Callback Details:")
        logger.info(f"  - User ID: {clerk_user_id}")
        logger.info(f"  - Authorization code: {code[:10]}..." if code else "None")
        logger.info(f"  - State parameter: {state}")
        logger.info(f"  - State length: {len(state) if state else 0}")
        logger.info(f"  - State type: {type(state)}")
        
        # Handle OAuth callback with server-side state validation
        result = await google_oauth_service.handle_oauth_callback(
            code=code,
            state=state,
            clerk_user_id=clerk_user_id
        )
        
        logger.info(f"✅ OAuth callback processing completed successfully")
        logger.info(f"📋 OAuth Result:")
        logger.info(f"  - Success: {result.get('success', False)}")
        logger.info(f"  - Email: {result.get('email', 'None')}")
        logger.info(f"  - Gmail Connected: {result.get('is_gmail_connected', False)}")
        
        # Set up Gmail watch for push notifications
        watch_success = await setup_gmail_watch(clerk_user_id)
        logger.info(f"📡 Gmail watch setup: {'Success' if watch_success else 'Failed'}")
        
        return {
            "success": True,
            "message": "Gmail connected successfully with server-side state validation"
        }
        
    except Exception as e:
        logger.error(f"❌ Error handling OAuth callback (POST): {e}")
        logger.error(f"🔍 Error details:")
        logger.error(f"  - User ID: {clerk_user_id if 'clerk_user_id' in locals() else 'Unknown'}")
        logger.error(f"  - State: {state if 'state' in locals() else 'Unknown'}")
        logger.error(f"  - Error type: {type(e).__name__}")
        logger.error(f"  - Error message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"OAuth callback failed: {str(e)}"
        )

@router.delete("/oauth/revoke")
async def revoke_oauth_access(user=Depends(clerk_auth)) -> Dict:
    """
    Revoke OAuth access for the current user.
    
    Returns:
        Dict: Revocation result
    """
    try:
        clerk_user_id = user.get("clerk_user_id") or user.get("sub")
        logger.info(f"Revoking OAuth access for user: {clerk_user_id}")
        
        success = await google_oauth_service.revoke_user_access(clerk_user_id)
        
        if success:
            return {
                "success": True,
                "message": "Gmail access revoked successfully"
            }
        else:
            return {
                "success": False,
                "message": "No Gmail access found to revoke"
            }
        
    except Exception as e:
        logger.error(f"Error revoking OAuth access: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to revoke OAuth access: {str(e)}"
        )

@router.delete("/disconnect")
async def disconnect_gmail(user=Depends(clerk_auth)):
    """
    Disconnect Gmail for the current user (alias for revoke).
    
    Returns:
        204 No Content on success, or error response
    """
    try:
        clerk_user_id = user.get("clerk_user_id") or user.get("sub")
        logger.info(f"Disconnecting Gmail for user: {clerk_user_id}")
        
        success = await google_oauth_service.revoke_user_access(clerk_user_id)
        
        if success:
            return Response(status_code=204)
        else:
            return {
                "success": False,
                "message": "No Gmail connection found to disconnect"
            }
        
    except Exception as e:
        logger.error(f"Error disconnecting Gmail: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect Gmail: {str(e)}"
        )

@router.post("/watch/setup")
async def setup_gmail_watch_endpoint(user=Depends(clerk_auth)) -> Dict:
    """
    Set up Gmail push notifications for the current user.
    
    Returns:
        Dict: Watch setup result
    """
    try:
        clerk_user_id = user.get("clerk_user_id") or user.get("sub")
        logger.info(f"Setting up Gmail watch for user: {clerk_user_id}")
        
        # Check if user has Gmail connected
        status = await google_oauth_service.check_gmail_connection_status(clerk_user_id)
        
        if not status.get("is_connected", False):
            return {
                "success": False,
                "message": "Gmail not connected. Please connect Gmail first."
            }
        
        success = await setup_gmail_watch(clerk_user_id)
        
        if success:
            return {
                "success": True,
                "message": "Gmail push notifications set up successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to set up Gmail push notifications"
            }
        
    except Exception as e:
        logger.error(f"Error setting up Gmail watch: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set up Gmail watch: {str(e)}"
        ) 