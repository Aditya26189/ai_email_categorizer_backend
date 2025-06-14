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

    def save_email(self, email: Dict) -> bool:
        """
        Save an email to MongoDB with timestamp and duplicate checking.
        
        Args:
            email (Dict): Email data to save
            
        Returns:
            bool: True if email was saved, False if duplicate
        """
        try:
            # Debug: Print connection info
            print(f"\nMongoDB Connection Info:")
            print(f"URI: {self.mongodb_uri}")
            print(f"Database: {self.db_name}")
            print(f"Collection: {self.collection_name}")
            
            # Debug: Check if email exists
            existing = self.collection.find_one({"subject": email['subject']})
            if existing:
                print(f"\nFound existing email:")
                print(f"Subject: {existing['subject']}")
                print(f"Category: {existing.get('category', 'N/A')}")
                print(f"Timestamp: {existing.get('timestamp', 'N/A')}")
                return False
            
            # Add timestamp
            email['timestamp'] = datetime.utcnow().isoformat()
            
            # Insert the email
            result = self.collection.insert_one(email)
            print(f"\nSuccessfully saved email:")
            print(f"Subject: {email['subject']}")
            print(f"Category: {email['category']}")
            print(f"Timestamp: {email['timestamp']}")
            return True
            
        except Exception as e:
            print(f"\nError saving email: {str(e)}")
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

# Create a singleton instance
storage = MongoDBStorage() 