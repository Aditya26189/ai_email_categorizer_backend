from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from classifier import classify_email

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