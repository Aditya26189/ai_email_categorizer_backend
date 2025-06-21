from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from jose import jwt
import json
import os
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from app.core.config import settings
from app.db.base import get_mongo_client

# Gmail API scopes for full Gmail client capability
GMAIL_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.settings.basic"
]

class GoogleOAuthService:
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
    def create_oauth_flow(self) -> Flow:
        """Create OAuth flow with client credentials."""
        # Create client config dict from environment variables
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=GMAIL_SCOPES,
            redirect_uri=self.redirect_uri
        )
        return flow
    
    def generate_auth_url(self) -> Tuple[str, str]:
        """
        Generate OAuth authorization URL.
        
        Returns:
            Tuple[str, str]: (auth_url, state)
        """
        try:
            flow = self.create_oauth_flow()
            
            auth_url, state = flow.authorization_url(
                access_type="offline",  # 🔥 ensures refresh token
                prompt="consent",       # 🔁 forces token every time
                include_granted_scopes="true"
            )
            
            logger.info(f"Generated OAuth URL with state: {state}")
            return auth_url, state
            
        except Exception as e:
            logger.error(f"Error generating OAuth URL: {e}")
            raise
    
    async def check_gmail_connection_status(self, clerk_user_id: str) -> Dict:
        """
        Check if a user has Gmail connected.
        
        Args:
            clerk_user_id (str): Clerk user ID
            
        Returns:
            Dict: Connection status information in frontend-expected format
        """
        try:
            db = get_mongo_client()
            users_collection = db[settings.MONGODB_USERS_COLLECTION_NAME]
            
            # Check user's Gmail connection status
            user = await users_collection.find_one({"clerk_user_id": clerk_user_id})
            
            if not user:
                return {
                    "is_connected": False,
                    "gmail_email": None,
                    "last_sync": None
                }
            
            is_connected = user.get("is_gmail_connected", False)
            gmail_email = user.get("gmail_email") if is_connected else None
            last_sync = user.get("gmail_connected_at") if is_connected else None
            
            return {
                "is_connected": is_connected,
                "gmail_email": gmail_email,
                "last_sync": last_sync
            }
            
        except Exception as e:
            logger.error(f"Error checking Gmail connection status: {e}")
            return {
                "is_connected": False,
                "gmail_email": None,
                "last_sync": None
            }
    
    async def handle_oauth_callback(self, code: str, state: str, clerk_user_id: str) -> Dict:
        """
        Handle OAuth callback and store credentials.
        
        Args:
            code (str): Authorization code from Google
            state (str): State parameter for security
            clerk_user_id (str): Clerk user ID
            
        Returns:
            Dict: User information and token status
        """
        try:
            flow = self.create_oauth_flow()
            
            # Exchange code for tokens
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Get user info from Google API instead of decoding JWT
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            
            # Prepare credentials data for storage
            creds_data = {
                "user_id": clerk_user_id,
                "google_user_id": user_info.get("id"),
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "expires_at": (datetime.utcnow() + timedelta(seconds=credentials.expiry.timestamp() - datetime.utcnow().timestamp())).isoformat() if credentials.expiry else None,
                "scopes": credentials.scopes,
                "token_uri": credentials.token_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Store OAuth credentials in oauth collection
            db = get_mongo_client()
            oauth_collection = db[settings.MONGODB_OAUTH_COLLECTION_NAME]
            
            # Upsert credentials (update if exists, insert if not)
            await oauth_collection.update_one(
                {"user_id": clerk_user_id},
                {"$set": creds_data},
                upsert=True
            )
            
            # Update user's Gmail connection status
            users_collection = db[settings.MONGODB_USERS_COLLECTION_NAME]
            await users_collection.update_one(
                {"clerk_user_id": clerk_user_id},
                {
                    "$set": {
                        "is_gmail_connected": True,
                        "gmail_email": user_info.get("email"),
                        "gmail_connected_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                },
                upsert=True
            )
            
            logger.info(f"✅ OAuth credentials stored and user updated for: {clerk_user_id}")
            
            return {
                "success": True,
                "user_id": clerk_user_id,
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "scopes": credentials.scopes,
                "is_gmail_connected": True
            }
            
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            raise
    
    async def get_user_credentials(self, clerk_user_id: str) -> Optional[Credentials]:
        """
        Get stored credentials for a user.
        
        Args:
            clerk_user_id (str): Clerk user ID
            
        Returns:
            Optional[Credentials]: Google credentials if available
        """
        try:
            db = get_mongo_client()
            collection = db[settings.MONGODB_OAUTH_COLLECTION_NAME]
            
            user_creds = await collection.find_one({"user_id": clerk_user_id})
            
            if not user_creds:
                logger.warning(f"No OAuth credentials found for user: {clerk_user_id}")
                return None
            
            # Check if token is expired
            expires_at = datetime.fromisoformat(user_creds["expires_at"])
            if datetime.utcnow() >= expires_at:
                logger.info(f"Token expired for user: {clerk_user_id}, refreshing...")
                # Token refresh will be handled by token_refresh.py
                return None
            
            # Create Credentials object
            credentials = Credentials(
                token=user_creds["access_token"],
                refresh_token=user_creds["refresh_token"],
                token_uri=user_creds["token_uri"],
                client_id=user_creds["client_id"],
                client_secret=user_creds["client_secret"],
                scopes=user_creds["scopes"]
            )
            
            return credentials
            
        except Exception as e:
            logger.error(f"Error getting user credentials: {e}")
            return None
    
    async def revoke_user_access(self, clerk_user_id: str) -> bool:
        """
        Revoke OAuth access for a user.
        
        Args:
            clerk_user_id (str): Clerk user ID
            
        Returns:
            bool: True if successfully revoked
        """
        try:
            db = get_mongo_client()
            oauth_collection = db[settings.MONGODB_OAUTH_COLLECTION_NAME]
            users_collection = db[settings.MONGODB_USERS_COLLECTION_NAME]
            
            # Remove OAuth credentials from database
            oauth_result = await oauth_collection.delete_one({"user_id": clerk_user_id})
            
            # Update user's Gmail connection status
            await users_collection.update_one(
                {"clerk_user_id": clerk_user_id},
                {
                    "$set": {
                        "is_gmail_connected": False,
                        "gmail_connected_at": None,
                        "gmail_email": None,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                }
            )
            
            if oauth_result.deleted_count > 0:
                logger.info(f"✅ OAuth access revoked for user: {clerk_user_id}")
                return True
            else:
                logger.warning(f"No OAuth credentials found to revoke for user: {clerk_user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error revoking user access: {e}")
            return False

# Global instance
google_oauth_service = GoogleOAuthService() 