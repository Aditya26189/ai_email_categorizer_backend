import os
from datetime import datetime
from typing import List, Dict, Optional
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, OperationFailure, DuplicateKeyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MongoDBStorage:
    def __init__(self):
        """Initialize MongoDB connection using environment variables."""
        self.mongodb_uri = os.getenv('MONGODB_URI')
        self.db_name = os.getenv('DB_NAME')
        self.collection_name = os.getenv('COLLECTION_NAME')
        
        if not all([self.mongodb_uri, self.db_name, self.collection_name]):
            raise ValueError("Missing required environment variables: MONGODB_URI, DB_NAME, or COLLECTION_NAME")
        
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
            
            print("✅ Successfully connected to MongoDB")
        except ConnectionFailure as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error connecting to MongoDB: {str(e)}")

    def save_email(self, email: Dict) -> bool:
        """
        Save an email to MongoDB with timestamp and duplicate checking.
        
        Args:
            email (Dict): Email data to save
            
        Returns:
            bool: True if email was saved, False if duplicate
        """
        try:
            # Add timestamp
            email['timestamp'] = datetime.utcnow().isoformat()
            
            # Insert the email (will fail if subject is duplicate due to unique index)
            self.collection.insert_one(email)
            print("✅ Email saved to MongoDB")
            return True
            
        except DuplicateKeyError:
            print("⚠️ Email with this subject already exists.")
            return False
        except OperationFailure as e:
            print(f"❌ Failed to save email: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error saving email: {str(e)}")
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

    def close(self):
        """Close the MongoDB connection."""
        try:
            self.client.close()
            print("✅ MongoDB connection closed")
        except Exception as e:
            print(f"❌ Error closing MongoDB connection: {str(e)}")

# Create a singleton instance
storage = MongoDBStorage() 