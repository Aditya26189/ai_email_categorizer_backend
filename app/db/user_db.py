# app/db/user_db.py

from typing import Optional, Dict, Any
from loguru import logger
from app.db.base import db
from motor.motor_asyncio import AsyncIOMotorCollection

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

user_db = UserDB()
