import os
from datetime import datetime
from typing import List, Dict, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
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
            self.client = MongoClient(self.mongodb_uri)
            # Verify connection
            self.client.admin.command('ping')
            # Type assertion since we've checked for None above
            self.db = self.client[str(self.db_name)]
            self.collection = self.db[str(self.collection_name)]
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
            
            # Check for duplicate subject
            if self.collection.find_one({'subject': email['subject']}):
                print("⚠️ Email with this subject already exists.")
                return False
            
            # Insert the email
            self.collection.insert_one(email)
            print("✅ Email saved to MongoDB")
            return True
            
        except OperationFailure as e:
            print(f"❌ Failed to save email: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error saving email: {str(e)}")
            return False

    def load_emails(self) -> List[Dict]:
        """
        Load all emails from MongoDB, excluding _id field.
        
        Returns:
            List[Dict]: List of email documents
        """
        try:
            # Find all documents and exclude _id field
            cursor = self.collection.find({}, {'_id': 0})
            return list(cursor)
        except OperationFailure as e:
            print(f"❌ Failed to load emails: {str(e)}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error loading emails: {str(e)}")
            return []

    def close(self):
        """Close the MongoDB connection."""
        try:
            self.client.close()
            print("✅ MongoDB connection closed")
        except Exception as e:
            print(f"❌ Error closing MongoDB connection: {str(e)}")

# Create a singleton instance
storage = MongoDBStorage() 