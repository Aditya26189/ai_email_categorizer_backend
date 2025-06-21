import httpx
from app.core.config import settings
from app.db.base import get_mongo_client
from loguru import logger
from datetime import datetime, timedelta

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

async def refresh_gmail_token(user_id: str):
    """
    Refresh Gmail access token for a user.
    
    Args:
        user_id (str): Clerk user ID
        
    Returns:
        str: New access token
        
    Raises:
        Exception: If refresh fails
    """
    logger.info(f"[Token Refresh] Starting token refresh for user_id={user_id}")
    db = get_mongo_client()
    collection = db[settings.MONGODB_OAUTH_COLLECTION_NAME]
    user = await collection.find_one({"user_id": user_id})
    
    if not user:
        logger.error(f"[Token Refresh] No OAuth credentials found for user_id={user_id}")
        raise Exception("No OAuth credentials found for user")
    
    if "refresh_token" not in user or not user["refresh_token"]:
        logger.error(f"[Token Refresh] No refresh_token found for user_id={user_id}")
        raise Exception("Missing refresh token for user")

    refresh_token = user["refresh_token"]
    logger.info(f"[Token Refresh] Using refresh_token for user_id={user_id}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(GOOGLE_TOKEN_URL, data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            })
        
        logger.info(f"[Token Refresh] HTTP status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"[Token Refresh] Token refresh failed: {response.text}")
            raise Exception(f"Token refresh failed: {response.text}")

        data = response.json()
        access_token = data["access_token"]
        expires_in = data.get("expires_in", 3600)  # Default to 1 hour
        
        # Calculate new expiration time
        expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        
        logger.info(f"[Token Refresh] Token refresh successful for user_id={user_id}")

        # Update stored credentials
        update_data = {
            "access_token": access_token,
            "expires_at": expires_at,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await collection.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        
        logger.info(f"[Token Refresh] Updated access_token in DB for user_id={user_id}")
        return access_token
        
    except Exception as e:
        logger.error(f"[Token Refresh] Exception during token refresh for user_id={user_id}: {e}")
        raise

async def is_token_expired(user_id: str) -> bool:
    """
    Check if a user's access token is expired.
    
    Args:
        user_id (str): Clerk user ID
        
    Returns:
        bool: True if token is expired or missing
    """
    try:
        db = get_mongo_client()
        collection = db[settings.MONGODB_OAUTH_COLLECTION_NAME]
        user = await collection.find_one({"user_id": user_id})
        
        if not user or "expires_at" not in user:
            return True
            
        expires_at = datetime.fromisoformat(user["expires_at"])
        return datetime.utcnow() >= expires_at
        
    except Exception as e:
        logger.error(f"[Token Refresh] Error checking token expiration for user_id={user_id}: {e}")
        return True

async def get_valid_access_token(user_id: str) -> str:
    """
    Get a valid access token for a user, refreshing if necessary.
    
    Args:
        user_id (str): Clerk user ID
        
    Returns:
        str: Valid access token
        
    Raises:
        Exception: If no valid token can be obtained
    """
    try:
        # Check if token is expired
        if await is_token_expired(user_id):
            logger.info(f"[Token Refresh] Token expired for user_id={user_id}, refreshing...")
            return await refresh_gmail_token(user_id)
        
        # Get current token
        db = get_mongo_client()
        collection = db[settings.MONGODB_OAUTH_COLLECTION_NAME]
        user = await collection.find_one({"user_id": user_id})
        
        if not user or "access_token" not in user:
            raise Exception("No access token found for user")
            
        return user["access_token"]
        
    except Exception as e:
        logger.error(f"[Token Refresh] Error getting valid access token for user_id={user_id}: {e}")
        raise 