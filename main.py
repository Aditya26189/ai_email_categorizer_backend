from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from classifier import classify_email
from gmail_client import get_latest_emails
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