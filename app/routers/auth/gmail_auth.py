from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from app.core.clerk import clerk_auth
from app.db.user_db import user_db
from app.core.config import settings
from loguru import logger
import os
import requests
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

router = APIRouter(tags=["gmail-oauth"])

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]

@router.get("/auth/gmail/login")
async def gmail_login(user=Depends(clerk_auth)):
    """Redirect user to Gmail OAuth2 consent screen."""
    try:
        logger.info("Starting Gmail OAuth2 login flow.")
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )
        logger.info(f"Redirecting to Gmail OAuth2 consent screen: {auth_url}")
        return RedirectResponse(auth_url)
    except Exception as e:
        logger.error(f"Error starting Gmail OAuth2 flow: {e}")
        raise HTTPException(status_code=500, detail="Failed to start Gmail OAuth2 flow.")

@router.get("/auth/gmail/callback")
async def gmail_callback(request: Request, user=Depends(clerk_auth)):
    """Handle Gmail OAuth2 callback, exchange code for tokens, and update user."""
    try:
        logger.info("Handling Gmail OAuth2 callback.")
        code = request.query_params.get("code")
        if not code:
            logger.error("No code in callback.")
            raise HTTPException(status_code=400, detail="Missing code in callback.")
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials
        access_token = credentials.token
        refresh_token = credentials.refresh_token
        # Calculate expires_in safely
        if hasattr(credentials, 'expiry') and hasattr(credentials, '_issued_at') and credentials.expiry and credentials._issued_at:
            expires_in = credentials.expiry.timestamp() - credentials._issued_at
        else:
            logger.warning("Could not determine token expiry, using default 3600s.")
            expires_in = 3600
        # Fetch user info from Google userinfo endpoint
        userinfo_resp = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        userinfo = userinfo_resp.json()
        gmail_email = userinfo.get("email")
        picture = userinfo.get("picture")
        logger.info(f"Fetched Gmail user info: {gmail_email}")
        # Update MongoDB user document
        gmail_data = {
            "email": gmail_email,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": int(expires_in),
            "picture": picture
        }
        clerk_email = user.get("email")
        await user_db.update_user_gmail(clerk_email, gmail_data)
        # Optionally update Clerk public_metadata
        try:
            clerk_id = user.get("sub") or user.get("clerk_id")
            if clerk_id and settings.CLERK_SECRET_KEY:
                resp = requests.patch(
                    f"https://api.clerk.dev/v1/users/{clerk_id}/metadata",
                    headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"},
                    json={"public_metadata": {"gmail_connected": True}}
                )
                logger.info(f"Updated Clerk public_metadata: {resp.status_code}")
        except Exception as e:
            logger.warning(f"Could not update Clerk public_metadata: {e}")
        # Redirect to frontend with success
        redirect_url = f"{settings.FRONTEND_URL}?gmail_connected=success"
        logger.info(f"Redirecting to frontend: {redirect_url}")
        return RedirectResponse(redirect_url)
    except Exception as e:
        logger.error(f"Error in Gmail OAuth2 callback: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete Gmail OAuth2 callback.") 