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
        Generate OAuth authorization URL with server-side state storage.
        
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
    
    async def store_oauth_state(self, state: str, clerk_user_id: str) -> bool:
        """
        Store OAuth state server-side for security validation.
        
        Args:
            state (str): OAuth state parameter
            clerk_user_id (str): Clerk user ID
            
        Returns:
            bool: True if state stored successfully
        """
        try:
            db = get_mongo_client()
            oauth_states_collection = db["oauth_states"]
            
            # Store state with expiration (5 minutes)
            state_data = {
                "state": state,
                "clerk_user_id": clerk_user_id,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
            }
            
            await oauth_states_collection.insert_one(state_data)
            logger.info(f"✅ OAuth state stored for user: {clerk_user_id}")
            logger.info(f"🔍 Generated State Details:")
            logger.info(f"  - State: {state}")
            logger.info(f"  - Length: {len(state)}")
            logger.info(f"  - Type: {type(state)}")
            logger.info(f"  - Created: {state_data['created_at']}")
            logger.info(f"  - Expires: {state_data['expires_at']}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing OAuth state: {e}")
            return False
    
    async def validate_and_clear_oauth_state(self, state: str, clerk_user_id: str) -> bool:
        """
        Validate OAuth state and clear it after validation.
        
        Args:
            state (str): OAuth state from callback
            clerk_user_id (str): Clerk user ID
            
        Returns:
            bool: True if state is valid and cleared
        """
        try:
            logger.info(f"🔍 Validating OAuth state for user: {clerk_user_id}")
            logger.info(f"📋 Received State Details:")
            logger.info(f"  - State: {state}")
            logger.info(f"  - Length: {len(state) if state else 0}")
            logger.info(f"  - Type: {type(state)}")
            
            db = get_mongo_client()
            oauth_states_collection = db["oauth_states"]
            
            # Find and validate state
            state_doc = await oauth_states_collection.find_one({
                "state": state,
                "clerk_user_id": clerk_user_id
            })
            
            if not state_doc:
                logger.warning(f"❌ Invalid OAuth state for user: {clerk_user_id}")
                logger.warning(f"🔍 State validation failed:")
                logger.warning(f"  - Received state: {state}")
                logger.warning(f"  - User ID: {clerk_user_id}")
                logger.warning(f"  - State not found in database")
                
                # Log all states for this user for debugging
                all_states = await oauth_states_collection.find({"clerk_user_id": clerk_user_id}).to_list(length=10)
                logger.warning(f"🔍 All stored states for user {clerk_user_id}:")
                for i, stored_state in enumerate(all_states):
                    logger.warning(f"  {i+1}. State: {stored_state.get('state')} (Expires: {stored_state.get('expires_at')})")
                
                return False
            
            logger.info(f"✅ Found stored state in database")
            logger.info(f"🔍 Stored State Details:")
            logger.info(f"  - Stored state: {state_doc.get('state')}")
            logger.info(f"  - Stored length: {len(state_doc.get('state', ''))}")
            logger.info(f"  - Created: {state_doc.get('created_at')}")
            logger.info(f"  - Expires: {state_doc.get('expires_at')}")
            
            # Check if state is expired
            expires_at = datetime.fromisoformat(state_doc["expires_at"])
            if datetime.utcnow() > expires_at:
                logger.warning(f"❌ Expired OAuth state for user: {clerk_user_id}")
                logger.warning(f"🔍 State expiration details:")
                logger.warning(f"  - Current time: {datetime.utcnow().isoformat()}")
                logger.warning(f"  - Expires at: {expires_at.isoformat()}")
                logger.warning(f"  - Time difference: {datetime.utcnow() - expires_at}")
                # Clean up expired state
                await oauth_states_collection.delete_one({"_id": state_doc["_id"]})
                return False
            
            # State is valid - delete it to prevent replay attacks
            await oauth_states_collection.delete_one({"_id": state_doc["_id"]})
            logger.info(f"✅ OAuth state validated and cleared for user: {clerk_user_id}")
            logger.info(f"🔍 State validation successful:")
            logger.info(f"  - Received: {state}")
            logger.info(f"  - Stored: {state_doc.get('state')}")
            logger.info(f"  - Match: {state == state_doc.get('state')}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating OAuth state: {e}")
            return False
    
    async def cleanup_expired_states(self):
        """
        Clean up expired OAuth states from database.
        """
        try:
            db = get_mongo_client()
            oauth_states_collection = db["oauth_states"]
            
            # Delete states older than 5 minutes
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            result = await oauth_states_collection.delete_many({
                "expires_at": {"$lt": cutoff_time.isoformat()}
            })
            
            if result.deleted_count > 0:
                logger.info(f"🧹 Cleaned up {result.deleted_count} expired OAuth states")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired states: {e}")
    
    async def handle_oauth_callback(self, code: str, state: str, clerk_user_id: str) -> Dict:
        """
        Handle OAuth callback with server-side state validation.
        
        Args:
            code (str): Authorization code from Google
            state (str): State parameter for security
            clerk_user_id (str): Clerk user ID
            
        Returns:
            Dict: User information and token status
        """
        try:
            # Validate state server-side
            if not await self.validate_and_clear_oauth_state(state, clerk_user_id):
                raise Exception("Invalid OAuth state - possible CSRF attack")
            
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