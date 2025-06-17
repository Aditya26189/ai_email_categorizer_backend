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


class ClassifiedEmail(BaseModel):
    gmail_id: Optional[str] = Field(None, description="Gmail message ID")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    category: str = Field(..., description="AI-classified category")
    summary: List[str] = Field(default_factory=list, description="AI-generated bullet point summary")
    sender: str = Field(..., description="Email sender")
    timestamp: datetime = Field(..., description="When the email was processed")

    class Config:
        json_schema_extra = {
            "example": {
                "gmail_id": "587289",
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
    gmail_id: Optional[str] = Field(None, description="Gmail message ID")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    category: str = Field(..., description="AI-classified category")
    summary: List[str] = Field(default_factory=list, description="AI-generated bullet point summary")
    sender: str = Field(..., description="Email sender")
    timestamp: str = Field(..., description="When the email was processed")
    message: Optional[str] = Field(None, description="Response message")

    class Config:
        json_schema_extra = {
            "example": {
                "gmail_id": "587289",
                "sender": "john.doe@example.com",
                "subject": "Meeting Request: Project Kickoff",
                "body": "Hi Team, I'd like to schedule a meeting...",
                "category": "Meeting Request",
                "timestamp": "2024-02-20T12:00:00",
                "summary": [
                    "Request to schedule a project kickoff meeting",
                    "Asking for team availability"
                ],
                "message": "Email retrieved successfully"
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
                        "gmail_id": "587289",
                        "sender": "john.doe@example.com",
                        "subject": "Meeting Request: Project Kickoff",
                        "body": "Hi Team, I'd like to schedule a meeting...",
                        "category": "Meeting Request",
                        "timestamp": "2024-02-20T12:00:00",
                        "summary": [
                            "Request to schedule a project kickoff meeting",
                            "Asking for team availability"
                        ],
                        "message": "Email retrieved successfully"
                    },
                    {
                        "gmail_id": "587290",
                        "sender": "jane.smith@example.com",
                        "subject": "Project Update: Q1 Review",
                        "body": "Here's the latest update on our project...",
                        "category": "Project Update",
                        "timestamp": "2024-02-21T14:30:00",
                        "summary": [
                            "Q1 project progress review",
                            "Key milestones achieved"
                        ],
                        "message": "Email retrieved successfully"
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
