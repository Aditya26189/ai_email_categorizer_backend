import os
from datetime import datetime
from typing import List, Dict, Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure, DuplicateKeyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MongoDBStorage:
    def __init__(self):
        """Initialize MongoDB connection using environment variables."""
        self.mongodb_uri = os.getenv('MONGODB_URI')
        self.db_name = os.getenv('DB_NAME', 'email_db')  # Default database name
        self.collection_name = os.getenv('COLLECTION_NAME', 'emails')  # Default collection name
        
        if not self.mongodb_uri:
            raise ValueError("Missing required environment variable: MONGODB_URI")
        
        try:
            # Connect with retryWrites and serverSelectionTimeoutMS options
            self.client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                retryWrites=True
            )
            # Verify connection
            self.client.admin.command('ping')
            self.db = self.client[str(self.db_name)]
            self.collection = self.db[str(self.collection_name)]
            
            # Create indexes for better performance
            self.collection.create_index([("subject", ASCENDING)], unique=True)
            self.collection.create_index([("timestamp", ASCENDING)])
            
            print(f"✅ Successfully connected to MongoDB: {self.db_name}.{self.collection_name}")
        except ConnectionFailure as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error connecting to MongoDB: {str(e)}")

    def save_email(self, email_data: dict, force_regenerate_summary: bool = False) -> bool:
        """
        Save an email to MongoDB if it doesn't already exist.
        If the email exists and force_regenerate_summary is True, update its summary.
        
        Args:
            email_data (dict): Email data including subject, body, category, and summary
            force_regenerate_summary (bool): If True, updates summary for existing email
            
        Returns:
            bool: True if email was saved or updated, False if it already existed without update
        """
        try:
            # Check if email with same subject already exists
            existing = self.collection.find_one({"subject": email_data["subject"]})
            if existing:
                # If force_regenerate_summary is True, update the summary
                if force_regenerate_summary and "body" in email_data:
                    from utils.llm_utils import summarize_to_bullets
                    new_summary = summarize_to_bullets(email_data["body"], force_regenerate=True)
                    self.collection.update_one(
                        {"subject": email_data["subject"]},
                        {"$set": {"summary": new_summary}}
                    )
                    return True
                return False
                
            # Add timestamp if not present
            if "timestamp" not in email_data:
                email_data["timestamp"] = datetime.utcnow().isoformat()
                
            # Ensure all required fields are present
            required_fields = ["subject", "body", "category", "summary"]
            for field in required_fields:
                if field not in email_data:
                    email_data[field] = ""  # Default empty string for missing fields
                
            # Insert the email
            self.collection.insert_one(email_data)
            return True
            
        except DuplicateKeyError:
            print(f"⚠️ Duplicate email found: {email_data.get('subject', 'Unknown')}")
            return False
        except Exception as e:
            print(f"❌ Error saving email: {str(e)}")
            return False

    def load_emails(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Load emails from MongoDB, excluding _id field.
        
        Args:
            limit (Optional[int]): Maximum number of emails to return
            
        Returns:
            List[Dict]: List of email documents
        """
        try:
            # Find all documents, exclude _id field, sort by timestamp descending
            query = self.collection.find(
                {},
                {'_id': 0}
            ).sort('timestamp', -1)
            
            if limit:
                query = query.limit(limit)
                
            return list(query)
        except OperationFailure as e:
            print(f"❌ Failed to load emails: {str(e)}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error loading emails: {str(e)}")
            return []

    def get_email_by_subject(self, subject: str) -> Optional[Dict]:
        """
        Get a single email by its subject.
        
        Args:
            subject (str): Email subject to search for
            
        Returns:
            Optional[Dict]: Email document if found, None otherwise
        """
        try:
            return self.collection.find_one(
                {'subject': subject},
                {'_id': 0}
            )
        except Exception as e:
            print(f"❌ Error finding email: {str(e)}")
            return None

    def get_all_emails(self) -> List[Dict]:
        """
        Get all emails sorted by timestamp (newest first).
        
        Returns:
            List[Dict]: List of email documents sorted by timestamp
        """
        try:
            # Debug: Print connection info
            print(f"\nFetching all emails from:")
            print(f"Database: {self.db_name}")
            print(f"Collection: {self.collection_name}")
            
            emails = list(self.collection.find(
                {}, 
                {'_id': 0}
            ).sort('timestamp', DESCENDING))
            
            print(f"Found {len(emails)} emails")
            return emails
            
        except Exception as e:
            print(f"\nError retrieving emails: {str(e)}")
            return []

    def close(self):
        """Close the MongoDB connection."""
        try:
            self.client.close()
            print("✅ MongoDB connection closed")
        except Exception as e:
            print(f"❌ Error closing MongoDB connection: {str(e)}")

    def update_missing_summaries(self, batch_size: int = 10) -> int:
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
            emails = list(self.collection.find(query).limit(batch_size))
            updated_count = 0
            
            for email in emails:
                if "body" in email:
                    # Generate new summary
                    new_summary = summarize_to_bullets(email["body"])
                    
                    # Update the email
                    self.collection.update_one(
                        {"_id": email["_id"]},
                        {"$set": {"summary": new_summary}}
                    )
                    updated_count += 1
                    
            return updated_count
            
        except Exception as e:
            print(f"Error updating missing summaries: {str(e)}")
            return 0

# Create a singleton instance
storage = MongoDBStorage() 