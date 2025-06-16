from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

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
    MONGODB_COLLECTION_NAME: str = os.getenv("MONGODB_COLLECTION_NAME", "")
    
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
    
    class Config:
        env_file = ".env"

# Create settings instance
settings = Settings() 