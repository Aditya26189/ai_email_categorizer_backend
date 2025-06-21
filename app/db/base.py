# app/db/base.py
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
from app.core.config import settings
from pymongo.errors import ConnectionFailure

class Database:
    client: AsyncIOMotorClient
    db = None
    collections = {}

    @classmethod
    async def connect_db(cls):
        """Create database connection."""
        try:
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                retryWrites=True,
                tls=True,
                tlsAllowInvalidCertificates=False,
                tlsAllowInvalidHostnames=False
            )
            cls.db = cls.client[settings.MONGODB_DB_NAME]
            
            # Initialize collections using settings
            cls.collections = {
                'users': cls.db[settings.MONGODB_USERS_COLLECTION_NAME],
                'emails': cls.db[settings.MONGODB_EMAIL_COLLECTION_NAME]
            }
            
            # Create indexes
            await cls._create_indexes()
            
            logger.info("✅ Connected to MongoDB")
        except ConnectionFailure as e:
            logger.error(f"❌ Could not connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
            raise

    @classmethod
    async def _create_indexes(cls):
        """Create necessary indexes for collections."""
        try:
            # Users collection indexes
            await cls.collections['users'].create_index("email", unique=True)
            logger.info(f"✅ Created index on {settings.MONGODB_USERS_COLLECTION_NAME}.email")
            
            # Emails collection indexes
            await cls.collections['emails'].create_index("gmail_id", unique=True, sparse=True)
            logger.info(f"✅ Created index on {settings.MONGODB_EMAIL_COLLECTION_NAME}.gmail_id")
        except Exception as e:
            logger.error(f"❌ Error creating indexes: {e}")
            raise

    @classmethod
    async def close_db(cls):
        """Close database connection."""
        if cls.client:
            cls.client.close()
            logger.info("🛑 Closed MongoDB connection")

    @classmethod
    def get_collection(cls, name: str):
        """Get a specific collection by name."""
        if cls.db is None:
            raise ConnectionError("MongoDB is not connected.")
        if name not in cls.collections:
            raise ValueError(f"Collection '{name}' not found")
        return cls.collections[name]

# Singleton
db = Database()

def get_mongo_client():
    if Database.db is None:
        raise ConnectionError("MongoDB is not connected.")
    return Database.db

# Add user historyId helpers
async def get_user_history_id(clerk_user_id: str) -> str:
    user = await db.get_collection('users').find_one({"clerk_user_id": clerk_user_id})
    if user:
        return user.get("last_history_id")
    return None

async def set_user_history_id(clerk_user_id: str, history_id: str):
    await db.get_collection('users').update_one(
        {"clerk_user_id": clerk_user_id},
        {"$set": {"last_history_id": history_id}}
    )
