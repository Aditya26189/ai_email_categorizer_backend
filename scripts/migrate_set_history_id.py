import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import db, get_mongo_client, set_user_history_id
from app.services.gmail_client import get_gmail_service_for_user
from loguru import logger

async def migrate_set_history_id():
    """Migrate existing users to set their historyId."""
    try:
        await get_mongo_client()  # Ensure DB is connected
        users_collection = db.get_collection('users')
        
        # Find users with Gmail connected but no historyId
        users = users_collection.find({"is_gmail_connected": True, "last_history_id": {"$exists": False}})
        
        count = 0
        async for user in users:
            user_id = user["clerk_user_id"]
            logger.info(f"Migrating user: {user_id} ({user.get('email')})")
            
            try:
                service = await get_gmail_service_for_user(user_id)
                profile = service.users().getProfile(userId='me').execute()
                history_id = profile.get("historyId")
                
                if history_id:
                    await set_user_history_id(user_id, history_id)
                    logger.success(f"Set last_history_id for {user_id}: {history_id}")
                    count += 1
                else:
                    logger.warning(f"No historyId found for {user_id}")
                    
            except Exception as e:
                logger.error(f"Failed to set historyId for {user_id}: {e}")
                continue
                
        logger.info(f"Migration complete. Updated {count} users.")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(migrate_set_history_id()) 