from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class EmailIdentifier(BaseModel):
    """Schema for uniquely identifying an email."""
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
    """Request model for email classification."""
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
    """Response model for email data."""
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
    """Model for classified email data."""
    gmail_id: Optional[str] = Field(None, description="Gmail message ID")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    category: str = Field(..., description="AI-classified category")
    summary: List[str] = Field(default_factory=list, description="AI-generated bullet point summary")
    sender: str = Field(..., description="Email sender")
    timestamp: str = Field(..., description="When the email was processed") 