from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from classifier import classify_email
from gmail_client import get_latest_emails
from storage import storage
from typing import List, Dict

app = FastAPI(
    title="Email Classifier API",
    description="API for classifying emails into predefined categories using Gemini Pro",
    version="1.0.0"
)

class EmailRequest(BaseModel):
    subject: str
    body: str

class ClassificationResponse(BaseModel):
    category: str

class EmailPreview(BaseModel):
    subject: str
    body: str

class ClassifiedEmail(BaseModel):
    subject: str
    category: str

class ClassifyAndStoreResponse(BaseModel):
    category: str
    status: str

@app.post("/classify-and-store", response_model=ClassifyAndStoreResponse)
async def classify_and_store(request: EmailRequest):
    """
    Classify an email and store the result in the database.
    
    Args:
        request (EmailRequest): The email subject and body
        
    Returns:
        ClassifyAndStoreResponse: The classified category and storage status
        
    Raises:
        HTTPException: If classification or storage fails
    """
    try:
        # Classify the email
        category = classify_email(request.subject, request.body)
        
        # Check if classification was successful
        if category.startswith("Error:"):
            raise HTTPException(status_code=500, detail=category)
        
        # Prepare the email dictionary
        email_dict = {
            "subject": request.subject,
            "body": request.body,
            "category": category
        }
        
        # Save the email
        if storage.save_email(email_dict):
            return ClassifyAndStoreResponse(
                category=category,
                status="saved"
            )
        else:
            return ClassifyAndStoreResponse(
                category=category,
                status="duplicate"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to classify and store email: {str(e)}"
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

@app.get("/emails", response_model=List[EmailPreview])
async def get_emails():
    """
    Get the latest 5 emails from the user's Gmail inbox.
    
    Returns:
        List[EmailPreview]: List of email previews containing subject and body
        
    Raises:
        HTTPException: If fetching emails fails
    """
    try:
        emails = get_latest_emails(5)
        if not emails:
            return []
        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")

@app.post("/classify", response_model=ClassificationResponse)
async def classify_email_endpoint(request: EmailRequest):
    """
    Classify an email based on its subject and body.
    
    Args:
        request (EmailRequest): The email subject and body
        
    Returns:
        ClassificationResponse: The classified category
        
    Raises:
        HTTPException: If classification fails
    """
    result = classify_email(request.subject, request.body)
    
    # Check if the result is an error message
    if result.startswith("Error:"):
        raise HTTPException(status_code=500, detail=result)
    
    return ClassificationResponse(category=result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 