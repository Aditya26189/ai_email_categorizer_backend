# app/db/user_db.py

from typing import Optional, Dict, Any
from loguru import logger
from app.db.base import db
from motor.motor_asyncio import AsyncIOMotorCollection
from datetime import datetime, timedelta

class UserDB:
    def __init__(self):
        self._collection: Optional[AsyncIOMotorCollection] = None

    @property
    def collection(self) -> AsyncIOMotorCollection:
        if self._collection is None:
            raise RuntimeError("Collection not initialized. Call init() first.")
        return self._collection

    async def init(self):
        self._collection = db.get_collection('users')

    async def save_user_metadata(self, clerk_user_id: str, data: Dict[str, Any]) -> bool:
        """Store/update extra info for a Clerk user."""
        try:
            await self.collection.update_one(
                {"clerk_user_id": clerk_user_id},
                {"$set": data},
                upsert=True
            )
            logger.info(f"✅ Saved metadata for Clerk user: {clerk_user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving metadata for Clerk user: {e}")
            return False

    async def get_user_metadata(self, clerk_user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored metadata for a Clerk user."""
        try:
            return await self.collection.find_one({"clerk_user_id": clerk_user_id})
        except Exception as e:
            logger.error(f"❌ Error getting metadata for Clerk user: {e}")
            return None

    async def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create a new user with all User schema fields."""
        try:
            await self.collection.insert_one(user_data)
            logger.info(f"✅ Created user: {user_data.get('clerk_id')}")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating user: {e}")
            return False

    async def update_user(self, clerk_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user fields for a given Clerk user ID."""
        try:
            await self.collection.update_one(
                {"clerk_id": clerk_id},
                {"$set": update_data},
                upsert=True
            )
            logger.info(f"✅ Updated user: {clerk_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error updating user: {e}")
            return False

    async def get_user_by_clerk_user_id(self, clerk_user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by Clerk user ID."""
        try:
            return await self.collection.find_one({"clerk_user_id": clerk_user_id})
        except Exception as e:
            logger.error(f"❌ Error getting user by clerk_user_id: {e}")
            return None

    async def update_user_gmail(self, email: str, gmail_data: dict) -> bool:
        """
        Update a user's Gmail connection info by Clerk email.
        Sets gmail_connected, gmail_email, gmail_tokens, and optionally picture.
        Returns True if updated successfully, False otherwise.
        """
        await self._ensure_initialized()
        try:
            update_fields = {
                "gmail_connected": True,
                "gmail_email": gmail_data["email"],
                "gmail_tokens": {
                    "access_token": gmail_data["access_token"],
                    "refresh_token": gmail_data["refresh_token"],
                    "expires_at": int((datetime.utcnow() + timedelta(seconds=gmail_data["expires_in"])).timestamp())
                }
            }
            if "picture" in gmail_data:
                update_fields["picture"] = gmail_data["picture"]
            result = await self.collection.update_one(
                {"email": email},
                {"$set": update_fields}
            )
            if result.modified_count > 0:
                logger.info(f"✅ Updated Gmail info for user: {email}")
                return True
            else:
                logger.warning(f"⚠️ No user updated for email: {email}")
                return False
        except Exception as e:
            logger.error(f"❌ Error updating Gmail info for user {email}: {e}")
            return False

user_db = UserDB()
