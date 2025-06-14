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
    "Job Offer", "Meeting Request", "Research Collaboration"
]

# Mock Gemini AI classification function
def classify_email(subject: str, body: str) -> str:
    """
    Mock function to classify emails using Gemini AI.
    In a real implementation, this would call the Gemini API.
    """
    # Simulate API call delay
    import time
    time.sleep(0.5)
    
    # Simple mock logic based on keywords
    email_text = (subject + " " + body).lower()
    
    if "intern" in email_text or "internship" in email_text:
        return "Internship"
    elif "fund" in email_text or "grant" in email_text:
        return "Funding"
    elif "review" in email_text or "paper" in email_text:
        return "Review Request"
    elif "newsletter" in email_text or "update" in email_text:
        return "Newsletter"
    elif "job" in email_text or "position" in email_text:
        return "Job Offer"
    elif "meeting" in email_text or "schedule" in email_text:
        return "Meeting Request"
    elif "collaborate" in email_text or "research" in email_text:
        return "Research Collaboration"
    else:
        # Default to Meeting Request if no clear category is found
        return "Meeting Request"

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
    """
    try:
        print(f"\nFetching emails" + (f" with category: {category}" if category else ""))
        
        # Get all emails using load_emails
        emails = storage.load_emails()
        print(f"Total emails found: {len(emails)}")
        
        # Filter by category if specified
        if category:
            emails = [e for e in emails if e['category'] == category]
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
    Fetch the latest 5 emails and classify each one.
    
    Returns:
        List[ClassifiedEmail]: List of classified emails with their subjects and categories
        
    Raises:
        HTTPException: If fetching or classifying emails fails
    """
    try:
        # Get latest emails
        emails = get_latest_emails(5)
        if not emails:
            return []
        
        # Classify each email
        classified_emails = []
        for email in emails:
            try:
                category = classify_email(email['subject'], email['body'])
                # Skip if classification returned an error
                if category.startswith("Error:"):
                    continue
                classified_emails.append({
                    "subject": email['subject'],
                    "category": category
                })
            except Exception as e:
                # Skip individual email if classification fails
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
    """
    return CATEGORIES

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 