from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from typing import List, Dict
from datetime import datetime
from loguru import logger

from app.models.email import EmailRequest, EmailResponse, ClassifiedEmail
from app.db.email_db import email_db
from app.services.gmail_client import get_latest_emails
from app.services.classifier import classify_email
from app.utils.llm_utils import summarize_to_bullets
from app.core.clerk import clerk_auth

router = APIRouter(prefix="/classify", tags=["classification"])

async def process_emails_background(emails: List[Dict], batch_size: int = 10):
    """
    Process emails in the background.
    Handles classification, summarization, and email_db.
    """
    try:
        total_emails = len(emails)
        logger.info(f"🔄 Starting background processing of {total_emails} emails")
        
        for i in range(0, total_emails, batch_size):
            batch = emails[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} of {(total_emails + batch_size - 1)//batch_size}")
            
            for email in batch:
                try:
                    # Skip if already classified
                    if email.get('gmail_id') and await email_db.already_classified(email['gmail_id']):
                        logger.info(f"Skipping already classified email: {email.get('gmail_id')}")
                        continue
                    
                    # Classify the email
                    category = classify_email(email['subject'], email['body'])
                    logger.info(f"Classified email {email.get('gmail_id')} as: {category}")
                    
                    # Generate summary
                    summary = summarize_to_bullets(email['body'])
                    logger.info(f"Generated summary with {len(summary)} bullet points")
                    
                    # Prepare email document
                    email_doc = {
                        "gmail_id": email.get('gmail_id'),
                        "subject": email['subject'],
                        "body": email['body'],
                        "category": category,
                        "timestamp": email.get('timestamp', datetime.utcnow().isoformat()),
                        "sender": email.get('sender', email.get('from', 'Unknown')),
                        "summary": summary
                    }
                    
                    # Save to email_db
                    if await email_db.save_email(email_doc):
                        logger.success(f"Successfully processed and saved email: {email.get('gmail_id')}")
                    else:
                        logger.warning(f"Failed to save email: {email.get('gmail_id')}")
                        
                except Exception as e:
                    logger.error(f"Error processing email {email.get('gmail_id')}: {str(e)}")
                    continue
                    
        logger.success(f"✅ Completed background processing of {total_emails} emails")
        
    except Exception as e:
        logger.error(f"❌ Background task failed: {str(e)}")

@router.post("/", response_model=EmailResponse)
async def classify_and_store_email(request: EmailRequest):
    """
    Classify an email and store it in MongoDB.
    Returns 409 if email with same Gmail ID already exists.
    """
    try:
        logger.info(f"\nProcessing new email:")
        logger.info(f"Subject: {request.subject}")
        logger.info(f"Gmail ID: {request.gmail_id}")
        
        # Check if email already exists
        if request.gmail_id and await email_db.already_classified(request.gmail_id):
            logger.warning(f"Email with Gmail ID {request.gmail_id} already exists")
            raise HTTPException(
                status_code=409,
                detail="Email with this Gmail ID already exists"
            )
        
        # Classify the email
        category = classify_email(request.subject, request.body)
        logger.info(f"Classified as: {category}")
        
        # Generate summary for the email
        summary = summarize_to_bullets(request.body)
        logger.info(f"Generated summary with {len(summary)} bullet points")
        
        # Get current timestamp in ISO format
        current_time = datetime.utcnow().isoformat()
        logger.info(f"📅 Timestamp: {current_time}")
        
        # Prepare email document
        email_doc = {
            "gmail_id": request.gmail_id,  # Gmail ID is required
            "subject": request.subject,
            "body": request.body,
            "category": category,
            "timestamp": current_time,
            "sender": request.sender or "Manual Classification",
            "summary": summary
        }
        
        # Save using email_db instance
        if not await email_db.save_email(email_doc):
            logger.warning(f"Failed to save email with Gmail ID {request.gmail_id}")
            raise HTTPException(
                status_code=500,
                detail="Failed to save email"
            )
            
        logger.success(f"Email successfully processed and saved")
        return EmailResponse(**email_doc)
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Error in /classify endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process email: {str(e)}"
        )

@router.get("/emails", response_model=List[ClassifiedEmail])
async def classify_latest_emails(
    background_tasks: BackgroundTasks,
    batch_size: int = Query(10, ge=1, le=50, description="Number of emails to process in each batch"),
    user=Depends(clerk_auth)
):
    """
    Fetch the latest emails from Gmail and start background processing.
    Returns immediately with the list of emails that will be processed.
    """
    try:
        clerk_id = user.get("clerk_id") or user.get("sub")
        emails = await get_latest_emails(clerk_id, 50)  # Fetch more emails than batch size
        if not emails:
            logger.info("No new emails found to process")
            return []
        logger.info(f"📧 Found {len(emails)} emails to process")
        background_tasks.add_task(process_emails_background, emails, batch_size)
        logger.info(f"Started background processing with batch size: {batch_size}")
        return [ClassifiedEmail(**email) for email in emails]
    except Exception as e:
        logger.error(f"❌ Failed to start email processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch or classify emails: {str(e)}"
        ) 