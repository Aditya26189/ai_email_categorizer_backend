from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    # Gmail Configuration
    GMAIL_CREDENTIALS_FILE: str = os.getenv("GMAIL_CREDENTIALS_FILE", "")
    GMAIL_TOKEN_FILE: str = os.getenv("GMAIL_TOKEN_FILE", "")
    GMAIL_API_SCOPES: str = os.getenv("GMAIL_API_SCOPES")
    
    # Gemini AI Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_API_URL: str = os.getenv("GEMINI_API_URL", "")
    
    # MongoDB Configuration
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "")
    MONGODB_EMAIL_COLLECTION_NAME: str = os.getenv("MONGODB_EMAIL_COLLECTION_NAME", "")
    MONGODB_USERS_COLLECTION_NAME: str = os.getenv("MONGODB_USERS_COLLECTION_NAME","")
    
    # Email Categories
    EMAIL_CATEGORIES: List[str] = [
        "Important",
        "Work",
        "Personal",
        "Finance",
        "Travel",
        "Shopping",
        "Entertainment",
        "Health",
        "Education",
        "Other"
    ]
    
    # Clerk Configuration
    CLERK_FRONTEND_API: str = os.getenv("CLERK_FRONTEND_API", "")
    CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY", "")
    CLERK_WEBHOOK_SECRET: str = os.getenv("CLERK_WEBHOOK_SECRET", "")
    
    # OAuth settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID","")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET","")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI","")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL","")

    # Session settings
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY","")  # Change this in production
    
    @staticmethod
    def now_utc() -> datetime:
        """Get current UTC timestamp."""
        return datetime.now(timezone.utc)
    
    class Config:
        env_file = ".env"

# Create settings instance
settings = Settings() 