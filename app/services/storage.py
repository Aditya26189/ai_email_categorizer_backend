import os
from datetime import datetime
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, OperationFailure, DuplicateKeyError
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

class MongoDBStorage:
    def __init__(self):
        """Initialize MongoDB connection using environment variables."""
        self.mongodb_uri = os.getenv('MONGODB_URI')
        self.db_name = os.getenv('MONGODB_DB_NAME') 
        self.collection_name = os.getenv('MONGODB_COLLECTION_NAME')  
        
        if not self.mongodb_uri:
            raise ValueError("Missing required environment variable: MONGODB_URI")
        
        try:
            # Connect with SSL/TLS settings
            self.client = AsyncIOMotorClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                retryWrites=True,
                tls=True,  # Enable TLS/SSL
                tlsAllowInvalidCertificates=False,  # Don't allow invalid certificates
                tlsAllowInvalidHostnames=False  # Don't allow invalid hostnames
            )
            self.db = self.client[str(self.db_name)]
            self.collection = self.db[str(self.collection_name)]
            
            # Create sparse unique index on Gmail message ID
            self.collection.create_index("gmail_id", unique=True, sparse=True)
            
            logger.info(f"✅ Successfully connected to MongoDB: {self.db_name}.{self.collection_name}")
        except ConnectionFailure as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error connecting to MongoDB: {str(e)}")

    async def already_classified(self, gmail_id: str) -> bool:
        """Check if an email with the given Gmail ID has already been processed."""
        try:
            return await self.collection.find_one({"gmail_id": gmail_id}) is not None
        except Exception as e:
            logger.error(f"❌ Error checking for existing email: {str(e)}")
            return False

    async def save_email(self, email_data: dict, force_regenerate_summary: bool = False) -> bool:
        """
        Save an email to MongoDB if it doesn't already exist.
        If the email exists and force_regenerate_summary is True, update its summary.
        
        Args:
            email_data (dict): Email data including gmail_id, subject, body, category, summary, sender, and timestamp
            force_regenerate_summary (bool): If True, updates summary for existing email
            
        Returns:
            bool: True if email was saved or updated, False if it already existed without update
        """
        try:
            # Ensure gmail_id is present for Gmail-sourced emails
            if "gmail_id" not in email_data and "sender" != "Manual Classification":
                logger.error("❌ Missing gmail_id for Gmail-sourced email")
                return False

            # Check if email with same Gmail ID already exists
            if "gmail_id" in email_data:
                existing = await self.collection.find_one({"gmail_id": email_data["gmail_id"]})
                if existing:
                    # If force_regenerate_summary is True, update the summary
                    if force_regenerate_summary and "body" in email_data:
                        from app.utils.llm_utils import summarize_to_bullets
                        new_summary = summarize_to_bullets(email_data["body"])
                        await self.collection.update_one(
                            {"gmail_id": email_data["gmail_id"]},
                            {"$set": {"summary": new_summary}}
                        )
                        return True
                    return False
                
            # Add timestamp if not present
            if "timestamp" not in email_data:
                email_data["timestamp"] = datetime.utcnow().isoformat()
                
            # Ensure all required fields are present
            required_fields = ["subject", "body", "category", "summary", "sender", "timestamp"]
            for field in required_fields:
                if field not in email_data:
                    email_data[field] = ""  # Default empty string for missing fields
                
            # Insert the email
            await self.collection.insert_one(email_data)
            return True
            
        except DuplicateKeyError:
            logger.warning(f"⚠️ Duplicate email found: {email_data.get('subject', 'Unknown')} from {email_data.get('sender', 'Unknown')}")
            return False
        except Exception as e:
            logger.error(f"❌ Error saving email: {str(e)}")
            return False

    async def load_emails(self) -> List[Dict]:
        """
        Load emails from MongoDB, excluding _id field.
        
        Args:
            limit (Optional[int]): Maximum number of emails to return
            
        Returns:
            List[Dict]: List of email documents
        """
        try:
            # Find all documents, exclude _id field, sort by timestamp descending
            cursor = self.collection.find(
                {},
                {'_id': 0}
            ).sort('timestamp', -1)
                
            return await cursor.to_list(length=None)
        except OperationFailure as e:
            logger.error(f"❌ Failed to load emails: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error loading emails: {str(e)}")
            return []

    async def get_email_by_subject(self, subject: str) -> Optional[Dict]:
        """
        Get a single email by its subject.
        
        Args:
            subject (str): Email subject to search for
            
        Returns:
            Optional[Dict]: Email document if found, None otherwise
        """
        try:
            return await self.collection.find_one(
                {'subject': subject},
                {'_id': 0}
            )
        except Exception as e:
            logger.error(f"❌ Error finding email: {str(e)}")
            return None

    async def get_all_emails(self) -> List[Dict]:
        """
        Get all emails sorted by timestamp (newest first).
        
        Returns:
            List[Dict]: List of email documents sorted by timestamp
        """
        try:
            # Debug: Print connection info
            logger.info(f"\nFetching all emails from:")
            logger.info(f"Database: {self.db_name}")
            logger.info(f"Collection: {self.collection_name}")
            
            cursor = self.collection.find(
                {}, 
                {'_id': 0}
            ).sort('timestamp', -1)
            
            emails = await cursor.to_list(length=None)
            logger.info(f"Found {len(emails)} emails")
            return emails
            
        except Exception as e:
            logger.error(f"\nError retrieving emails: {str(e)}")
            return []

    async def get_emails_by_category(self, category: str) -> List[Dict]:
        """Get all emails for a specific category."""
        try:
            cursor = self.collection.find(
                {"category": category}
            ).sort('timestamp', -1)
            
            emails = await cursor.to_list(length=None)
            # Convert to EmailResponse format
            return [
                {
                    "message": "Email retrieved successfully",
                    "file_path": str(email['_id']),
                    "subject": email.get('subject', ''),
                    "body": email.get('body', ''),
                    "category": email.get('category', ''),
                    "sender": email.get('sender', ''),
                    "timestamp": email.get('timestamp', '')
                }
                for email in emails
            ]
        except Exception as e:
            logger.error(f"❌ Error getting emails for category {category}: {str(e)}")
            return []

    async def get_all_categories(self) -> List[str]:
        """Get all unique categories from the database."""
        try:
            categories = await self.collection.distinct("category")
            return categories
        except Exception as e:
            logger.error(f"❌ Error getting categories: {str(e)}")
            return []

    async def close(self):
        """Close the MongoDB connection."""
        try:
            self.client.close()
            logger.info("✅ MongoDB connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing MongoDB connection: {str(e)}")

    async def update_missing_summaries(self, batch_size: int = 10) -> int:
        """
        Update summaries for emails that don't have them.
        Returns the number of emails updated.
        
        Args:
            batch_size (int): Number of emails to process in one batch
            
        Returns:
            int: Number of emails updated
        """
        try:
            from utils.llm_utils import summarize_to_bullets
            
            # Find emails without summaries or with empty summaries
            query = {
                "$or": [
                    {"summary": {"$exists": False}},
                    {"summary": []},
                    {"summary": [""]},
                    {"summary": {"$size": 0}}
                ]
            }
            
            # Get batch of emails
            cursor = self.collection.find(query).limit(batch_size)
            emails = await cursor.to_list(length=None)
            updated_count = 0
            
            for email in emails:
                if "body" in email:
                    # Generate new summary
                    new_summary = summarize_to_bullets(email["body"])
                    
                    # Update the email
                    await self.collection.update_one(
                        {"_id": email["_id"]},
                        {"$set": {"summary": new_summary}}
                    )
                    updated_count += 1
                    
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating missing summaries: {str(e)}")
            return 0

    async def get_email_by_gmail_id(self, gmail_id: str) -> Optional[Dict]:
        """
        Get a single email by its Gmail ID.
        
        Args:
            gmail_id (str): Gmail message ID to search for
            
        Returns:
            Optional[Dict]: Email document if found, None otherwise
        """
        try:
            return await self.collection.find_one(
                {'gmail_id': gmail_id},
                {'_id': 0}
            )
        except Exception as e:
            logger.error(f"❌ Error finding email by Gmail ID: {str(e)}")
            return None

# Create a singleton instance
storage = MongoDBStorage() 