from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime

class Email(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    user_id: str = Field(..., description="Clerk User ID")
    gmail_id: str = Field(..., description="Unique Gmail message ID")
    gmail_url: Optional[str] = Field(None, description="Direct link to view email in Gmail")
    thread_id: Optional[str] = Field(None, description="Gmail thread ID")
    label_ids: Optional[List[str]] = Field(default_factory=list, description="Gmail label IDs")
    history_id: Optional[str] = Field(None, description="Gmail history ID for incremental sync")
    sender_name: Optional[str] = Field(None, description="Sender's display name")
    sender_email: EmailStr = Field(..., description="Sender's email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Plain text body of the email")
    timestamp: datetime = Field(..., description="Timestamp when email was received")
    category: Optional[str] = Field(None, description="AI-generated category")
    summary: List[str] = Field(default_factory=list, description="AI-generated summary bullets")
    is_read: bool = Field(default=False, description="If email was read by user")
    is_processed: bool = Field(default=False, description="If email was processed by AI")
    is_sensitive: bool = Field(default=False, description="Marks presence of sensitive content")
    status: Literal[
        "new", "read", "reviewed", "archived", "flagged"
    ] = Field(default="new", description="Email triage status")
    fetched_at: datetime = Field(default_factory=datetime.utcnow, description="When email was fetched")
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_abc123",
                "gmail_id": "1853d239248aee99",
                "gmail_url": "https://mail.google.com/mail/u/0/#inbox/1853d239248aee99",
                "thread_id": "1853d239248aee22",
                "label_ids": ["INBOX", "IMPORTANT"],
                "history_id": "7892310",
                "sender_name": "John Doe",
                "sender_email": "hr@openai.com",
                "subject": "Interview Invitation",
                "body": "Hi, we'd love to invite you for an interview...",
                "timestamp": "2025-06-16T12:00:00Z",
                "category": "Job Opportunity",
                "summary": ["Interview invitation from OpenAI", "Contact details included"],
                "is_read": True,
                "is_processed": True,
                "is_sensitive": False,
                "status": "reviewed",
                "fetched_at": "2025-06-16T14:00:00Z"
            }
        }

class GmailTokens(BaseModel):
    access_token: str = Field(..., description="Gmail OAuth2 access token")
    refresh_token: str = Field(..., description="Gmail OAuth2 refresh token")
    expires_at: int = Field(..., description="Unix timestamp for token expiry")
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "ya29.a0AfH6S...",
                "refresh_token": "1//0gL4...",
                "expires_at": 1720000000
            }
        }

class EmailIdentifier(BaseModel):
    sender_name: Optional[str] = Field(None, description="Sender's display name")
    sender_email: str = Field(..., description="Sender's email address")
    subject: str = Field(..., description="Email subject line")
    timestamp: datetime = Field(..., description="Email timestamp")
    class Config:
        json_schema_extra = {
            "example": {
                "sender_name": "John Doe",
                "sender_email": "john.doe@example.com",
                "subject": "Meeting Request: Project Kickoff",
                "timestamp": "2024-02-20T12:00:00"
            }
        }

class EmailRequest(BaseModel):
    gmail_id: Optional[str] = Field(None, description="Gmail message ID for Gmail-sourced emails")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    sender_name: Optional[str] = Field(None, description="Sender's display name")
    sender_email: Optional[str] = Field(None, description="Sender's email address")
    class Config:
        json_schema_extra = {
            "example": {
                "gmail_id": "587289",
                "sender_name": "John Doe",
                "sender_email": "john.doe@example.com",
                "subject": "Meeting Request: Project Kickoff",
                "body": "Hi Team, I'd like to schedule a meeting...",
                "timestamp": "2024-02-20T12:00:00"
            }
        }

class ClassifiedEmail(BaseModel):
    gmail_id: Optional[str] = Field(None, description="Gmail message ID")
    gmail_url: Optional[str] = Field(None, description="Direct link to view email in Gmail")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    category: str = Field(..., description="AI-classified category")
    summary: List[str] = Field(default_factory=list, description="AI-generated bullet point summary")
    sender_name: Optional[str] = Field(None, description="Sender's display name")
    sender_email: str = Field(..., description="Sender's email address")
    timestamp: datetime = Field(..., description="When the email was processed")
    class Config:
        json_schema_extra = {
            "example": {
                "gmail_id": "587289",
                "gmail_url": "https://mail.google.com/mail/u/0/#inbox/587289",
                "sender_name": "John Doe",
                "sender_email": "john.doe@example.com",
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
    gmail_url: Optional[str] = Field(None, description="Direct link to view email in Gmail")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    category: str = Field(..., description="AI-classified category")
    summary: List[str] = Field(default_factory=list, description="AI-generated bullet point summary")
    sender_name: Optional[str] = Field(None, description="Sender's display name")
    sender_email: str = Field(..., description="Sender's email address")
    timestamp: str = Field(..., description="When the email was processed")
    message: Optional[str] = Field(None, description="Response message")
    class Config:
        json_schema_extra = {
            "example": {
                "gmail_id": "587289",
                "gmail_url": "https://mail.google.com/mail/u/0/#inbox/587289",
                "sender_name": "John Doe",
                "sender_email": "john.doe@example.com",
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
                        "sender_name": "John Doe",
                        "sender_email": "john.doe@example.com",
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
                        "sender_name": "Jane Smith",
                        "sender_email": "jane.smith@example.com",
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