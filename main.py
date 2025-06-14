from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import os
from dotenv import load_dotenv
from storage import storage
from gmail_client import get_latest_emails

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Email Classifier API",
    description="API for classifying emails using Gemini AI",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define categories list
CATEGORIES = [
    "Internship", "Funding", "Review Request", "Newsletter",
    "Job Offer", "Meeting Request", "Research Collaboration",
    "Security Alert", "Welcome", "Notification"
]

# Helper function to normalize category
def normalize_category(category: str) -> str:
    """
    Normalize category by trimming whitespace and converting to lowercase.
    """
    return category.strip().lower()

# Mock Gemini AI classification function
def classify_email(subject: str, body: str) -> str:
    """
    Classify emails using keyword matching and context analysis.
    """
    # Convert to lowercase for case-insensitive matching
    email_text = (subject + " " + body).lower()
    
    # Security and Alert related keywords
    security_keywords = ["security", "alert", "warning", "suspicious", "unauthorized", "breach", "hack"]
    if any(keyword in email_text for keyword in security_keywords):
        return "Security Alert"
    
    # Welcome and Onboarding related keywords
    welcome_keywords = ["welcome", "get started", "getting started", "onboarding", "new account"]
    if any(keyword in email_text for keyword in welcome_keywords):
        return "Welcome"
    
    # Notification related keywords
    notification_keywords = ["notification", "update", "deleted", "removed", "changed", "modified"]
    if any(keyword in email_text for keyword in notification_keywords):
        return "Notification"
    
    # Meeting related keywords
    meeting_keywords = ["meeting", "schedule", "appointment", "call", "conference", "discussion"]
    if any(keyword in email_text for keyword in meeting_keywords):
        return "Meeting Request"
    
    # Internship related keywords
    internship_keywords = ["intern", "internship", "student", "trainee", "apprentice"]
    if any(keyword in email_text for keyword in internship_keywords):
        return "Internship"
    
    # Funding related keywords
    funding_keywords = ["fund", "grant", "sponsor", "budget", "finance", "payment"]
    if any(keyword in email_text for keyword in funding_keywords):
        return "Funding"
    
    # Review related keywords
    review_keywords = ["review", "paper", "article", "manuscript", "publication", "journal"]
    if any(keyword in email_text for keyword in review_keywords):
        return "Review Request"
    
    # Newsletter related keywords
    newsletter_keywords = ["newsletter", "update", "news", "announcement", "bulletin"]
    if any(keyword in email_text for keyword in newsletter_keywords):
        return "Newsletter"
    
    # Job related keywords
    job_keywords = ["job", "position", "vacancy", "opening", "career", "employment"]
    if any(keyword in email_text for keyword in job_keywords):
        return "Job Offer"
    
    # Research collaboration related keywords
    collaboration_keywords = ["collaborate", "research", "study", "project", "partnership", "team"]
    if any(keyword in email_text for keyword in collaboration_keywords):
        return "Research Collaboration"
    
    # If no specific category is matched, return "Notification" as default
    return "Notification"

# Pydantic models
class EmailRequest(BaseModel):
    subject: str
    body: str

class EmailResponse(BaseModel):
    subject: str
    body: str
    category: str
    timestamp: str

class ClassifiedEmail(BaseModel):
    subject: str
    category: str

# API Endpoints
@app.post("/classify", response_model=EmailResponse)
async def classify_and_store_email(request: EmailRequest):
    """
    Classify an email and store it in MongoDB.
    Returns 409 if email with same subject already exists.
    """
    try:
        print(f"\nProcessing new email:")
        print(f"Subject: {request.subject}")
        
        # Classify the email
        category = classify_email(request.subject, request.body)
        print(f"Classified as: {category}")
        
        # Prepare email document
        email_doc = {
            "subject": request.subject,
            "body": request.body,
            "category": category,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Save using storage instance
        if not storage.save_email(email_doc):
            print(f"Email already exists in database")
            raise HTTPException(
                status_code=409,
                detail="Email with this subject already exists"
            )
            
        print(f"Email successfully processed and saved")
        return EmailResponse(**email_doc)
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        print(f"Error in /classify endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process email: {str(e)}"
        )

@app.get("/emails", response_model=List[EmailResponse])
async def get_stored_emails(category: Optional[str] = Query(None, description="Filter by category")):
    """
    Get all stored emails, optionally filtered by category.
    Results are sorted by timestamp (newest first).
    Category filtering is case-insensitive and ignores leading/trailing whitespace.
    """
    try:
        # Normalize the category filter if provided
        normalized_category = normalize_category(category) if category else None
        print(f"\nFetching emails" + (f" with category: {normalized_category}" if normalized_category else ""))
        
        # Get all emails using load_emails
        emails = storage.load_emails()
        print(f"Total emails found: {len(emails)}")
        
        # Filter by category if specified (case-insensitive)
        if normalized_category:
            emails = [e for e in emails if normalize_category(e['category']) == normalized_category]
            print(f"Emails after category filter: {len(emails)}")
        
        return [EmailResponse(**email) for email in emails]
        
    except Exception as e:
        print(f"Error in /emails endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve emails: {str(e)}"
        )

@app.get("/classify-emails", response_model=List[ClassifiedEmail])
async def classify_latest_emails():
    """
    Fetch the latest 5 emails from Gmail, classify them, and save to database.
    Skips duplicates and returns only successfully classified and saved emails.
    """
    try:
        # Get latest emails
        emails = get_latest_emails(5)
        if not emails:
            return []
        
        # Classify and save each email
        classified_emails = []
        for email in emails:
            try:
                # Classify the email
                category = classify_email(email['subject'], email['body'])
                # Skip if classification returned an error
                if category.startswith("Error:"):
                    continue
                
                # Prepare email document
                email_doc = {
                    "subject": email['subject'].strip(),
                    "body": email['body'].strip(),
                    "category": category.strip(),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Try to save to database
                if storage.save_email(email_doc):
                    classified_emails.append({
                        "subject": email_doc['subject'],
                        "category": email_doc['category']
                    })
                    print(f"Successfully classified and saved email: {email_doc['subject']}")
                else:
                    print(f"Skipped duplicate email: {email_doc['subject']}")
                    
            except Exception as e:
                print(f"Error processing email {email['subject']}: {str(e)}")
                continue
        
        return classified_emails
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch or classify emails: {str(e)}"
        )

@app.get("/categories", response_model=List[str])
async def get_categories():
    """
    Get the list of all available email categories.
    Categories are returned in their original case.
    """
    return CATEGORIES

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 