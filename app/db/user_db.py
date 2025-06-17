# app/db/user_db.py
from typing import Optional, Dict, Any
from loguru import logger
from app.db.base import db
from motor.motor_asyncio import AsyncIOMotorCollection

class UserDB:
    def __init__(self):
        """Initialize user database access."""
        self._collection: Optional[AsyncIOMotorCollection] = None

    @property
    def collection(self) -> AsyncIOMotorCollection:
        if self._collection is None:
            raise RuntimeError("Collection not initialized. Call init() first.")
        return self._collection

    async def init(self):
        """Initialize the collection connection."""
        self._collection = db.get_collection('users')

    async def _ensure_initialized(self):
        """Ensure collection is initialized."""
        if self._collection is None:
            await self.init()

    async def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create a new user in the database."""
        try:
            if self.collection is None:
                return False
            result = await self.collection.insert_one(user_data)
            logger.info(f"✅ Created user: {user_data.get('email')}")
            return result.inserted_id is not None
        except Exception as e:
            logger.error(f"❌ Error creating user: {str(e)}")
            return False

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a user by their email."""
        try:
            if self.collection is None:
                return None
            user = await self.collection.find_one({"email": email})
            if user:
                logger.info(f"ℹ️ Found user: {email}")
            return user
        except Exception as e:
            logger.error(f"❌ Error getting user by email: {str(e)}")
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by their MongoDB ObjectId (as string)."""
        from bson import ObjectId
        try:
            await self._ensure_initialized()
            return await self.collection.find_one({"_id": ObjectId(user_id)})
        except Exception as e:
            logger.error(f"❌ Error getting user by ID: {e}")
            return None

    async def update_user(self, email: str, updates: Dict[str, Any]) -> bool:
        """Update user fields."""
        try:
            await self._ensure_initialized()
            result = await self.collection.update_one(
                {"email": email}, {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Error updating user: {e}")
            return False

# Singleton instance
user_db = UserDB()
