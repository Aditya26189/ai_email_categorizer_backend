from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from bson import ObjectId


# --- Helpers ---
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


# --- Email Schemas ---

class EmailIdentifier(BaseModel):
    sender: str = Field(..., description="Email sender address")
    subject: str = Field(..., description="Email subject line")
    timestamp: datetime = Field(..., description="Email timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "sender": "john.doe@example.com",
                "subject": "Meeting Request: Project Kickoff",
                "timestamp": "2024-02-20T12:00:00"
            }
        }


class EmailRequest(BaseModel):
    gmail_id: Optional[str] = Field(None, description="Gmail message ID for Gmail-sourced emails")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    sender: Optional[str] = Field(None, description="Email sender")

    class Config:
        json_schema_extra = {
            "example": {
                "gmail_id": "587289",
                "sender": "john.doe@example.com",
                "subject": "Meeting Request: Project Kickoff",
                "body": "Hi Team, I'd like to schedule a meeting...",
                "timestamp": "2024-02-20T12:00:00"
            }
        }


class EmailResponse(BaseModel):
    gmail_id: Optional[str] = Field(None, description="Gmail message ID")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    category: str = Field(..., description="AI-classified category")
    summary: List[str] = Field(default_factory=list, description="AI-generated bullet point summary")
    sender: str = Field(..., description="Email sender")
    timestamp: str = Field(..., description="When the email was processed")

    class Config:
        json_schema_extra = {
            "example": {
                "sender": "john.doe@example.com",
                "subject": "Meeting Request: Project Kickoff",
                "body": "Hi Team, I'd like to schedule a meeting...",
                "category": "Meeting Request",
                "timestamp": "2024-02-20T12:00:00",
                "summary": [
                    "Request to schedule a project kickoff meeting",
                    "Asking for team availability"
                ]
            }
        }


class ClassifiedEmail(BaseModel):
    gmail_id: Optional[str] = Field(None, description="Gmail message ID")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    category: str = Field(..., description="AI-classified category")
    summary: List[str] = Field(default_factory=list, description="AI-generated bullet point summary")
    sender: str = Field(..., description="Email sender")
    timestamp: str = Field(..., description="When the email was processed")


# --- User Schemas (MongoDB version) ---

class User(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    google_sub: Optional[str] = Field(None, description="Google subject identifier")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="User's email address")
    hashed_password: Optional[str] = Field(None, description="Hashed password")
    name: Optional[str] = Field(None, description="User's full name")
    picture: Optional[str] = Field(None, description="URL to user's profile picture")
    created_at: Optional[datetime] = Field(None, description="User creation timestamp")

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "name": "John Doe",
                "picture": "https://example.com/profile.jpg",
                "created_at": "2024-03-13T15:30:45Z"
            }
        }


class CreateUserRequest(BaseModel):
    username: str = Field(..., description="Username for the new user")
    password: str = Field(..., description="Password for the new user")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john.doe@example.com",
                "password": "securepassword123"
            }
        }


# --- Auth Token Schemas ---

class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(..., description="Type of token (e.g., 'bearer')")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="JWT refresh token")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


# --- Google Auth Schema ---

class GoogleUser(BaseModel):
    sub: str = Field(..., description="Google subject identifier")
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., description="User's full name")
    picture: str = Field(..., description="URL to user's profile picture")


class Email(BaseModel):
    sender: str = Field(..., description="Email sender's address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")
    category: str = Field(..., description="Categorized type of email")
    timestamp: datetime = Field(..., description="Email timestamp")
    summary: List[str] = Field(..., description="Bullet-point summary of email content")

    class Config:
        json_schema_extra = {
            "example": {
                "sender": "john.doe@example.com",
                "subject": "Meeting Request: Project Kickoff",
                "body": "Hi Team, I'd like to schedule a meeting...",
                "category": "Meeting Request",
                "timestamp": "2024-02-20T12:00:00",
                "summary": [
                    "Request to schedule a project kickoff meeting",
                    "Asking for team availability"
                ]
            }
        }


class EmailResponse(BaseModel):
    message: str = Field(..., description="Response message")
    file_path: str = Field(..., description="Path to stored email file")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")
    category: str = Field(..., description="Categorized type of email")
    sender: str = Field(..., description="Email sender's address")
    timestamp: str = Field(..., description="Email timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Email retrieved successfully",
                "file_path": "emails/meeting_request_123.txt",
                "subject": "Meeting Request: Project Kickoff",
                "body": "Hi Team, I'd like to schedule a meeting...",
                "category": "Meeting Request",
                "sender": "john.doe@example.com",
                "timestamp": "2024-02-20T12:00:00"
            }
        }


class EmailListResponse(BaseModel):
    message: str = Field(..., description="Response message")
    emails: List[EmailResponse] = Field(..., description="List of email responses")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Emails retrieved successfully",
                "emails": [
                    {
                        "message": "Email retrieved successfully",
                        "file_path": "emails/meeting_request_123.txt",
                        "subject": "Meeting Request: Project Kickoff",
                        "body": "Hi Team, I'd like to schedule a meeting...",
                        "category": "Meeting Request",
                        "sender": "john.doe@example.com",
                        "timestamp": "2024-02-20T12:00:00"
                    },
                    {
                        "message": "Email retrieved successfully",
                        "file_path": "emails/update_456.txt",
                        "subject": "Project Update: Q1 Review",
                        "body": "Here's the latest update on our project...",
                        "category": "Project Update",
                        "sender": "jane.smith@example.com",
                        "timestamp": "2024-02-21T14:30:00"
                    }
                ]
            }
        }


class CategoryListResponse(BaseModel):
    message: str = Field(..., description="Response message")
    categories: List[str] = Field(..., description="List of available categories")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Categories retrieved successfully",
                "categories": [
                    "Meeting Request",
                    "Project Update",
                    "Task Assignment",
                    "General Communication"
                ]
            }
        }


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Authentication failed"
            }
        }
