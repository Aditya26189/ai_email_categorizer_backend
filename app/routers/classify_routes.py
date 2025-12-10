# CrashLensLogger logs are printed to stdout in NDJSON format by default.
# To save logs to a file, run your server with output redirection, e.g.:
#   uvicorn app.main:app > logs.jsonl
# You can then analyze logs in logs.jsonl with any NDJSON tool.
from crashlens_logger import CrashLensLogger
import uuid
from datetime import datetime


from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from typing import List, Dict
from datetime import datetime
from loguru import logger

from app.models.email import EmailRequest, EmailResponse, ClassifiedEmail
from app.db import email_db
from app.services.gmail_client import get_latest_emails
from app.services.classifier import classify_email
from app.utils.llm_utils import summarize_to_bullets
from app.core.clerk import clerk_auth


crashlens_logger = CrashLensLogger()



router = APIRouter(prefix="/classify", tags=["classification"])

async def process_emails_background(emails: List[Dict], batch_size: int = 10, user=None):
    """
    Process emails in the background.
    Handles classification, summarization, and email_db.
    """
    try:
        if user is None:
            raise ValueError("User context is required for background email processing.")
        user_id = user.get("clerk_user_id") or user.get("sub")
        total_emails = len(emails)
        logger.info(f"🔄 Starting background processing of {total_emails} emails for user_id={user_id}")
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
                        "user_id": user_id,
                        "gmail_id": email.get('gmail_id'),
                        "subject": email['subject'],
                        "body": email['body'],
                        "category": category,
                        "timestamp": email.get('timestamp', datetime.utcnow().isoformat()),
                        "sender_name": email.get('sender_name'),
                        "sender_email": email.get('sender_email', email.get('from', 'Unknown')),
                        "summary": summary
                    }
                    # Save to email_db
                    if await email_db.save_email(email_doc):
                        logger.success(f"Successfully processed and saved email: {email.get('gmail_id')}")
                    else:
                        logger.warning(f"Failed to save email: {email.get('gmail_id')}")
                except Exception as e:
                    logger.error(f"Error processing email: {str(e)}")
                    continue
        logger.success(f"✅ Completed background processing of {total_emails} emails")
    except Exception as e:
        logger.error(f"Error in background email processing: {str(e)}")

@router.post("/", response_model=EmailResponse)
async def classify_and_store_email(request: EmailRequest):
<<<<<<< HEAD
=======
  
>>>>>>> 94bb2a09def6d5cf440c6b59f6eebedb12e9c613
    """
    Classify an email and store it in MongoDB.
    Returns 409 if email with same Gmail ID already exists.
    """
    try:
        logger.info(f"\nProcessing new email:")
        logger.info(f"Subject: {request.subject}")
        logger.info(f"Gmail ID: {request.gmail_id}")
<<<<<<< HEAD
        # Use a default user_id since no authentication is required
        clerk_user_id = "anonymous_user"
        # Check if email already exists
=======
        clerk_user_id = "anonymous"
>>>>>>> 94bb2a09def6d5cf440c6b59f6eebedb12e9c613
        if request.gmail_id and await email_db.already_classified(request.gmail_id):
            logger.warning(f"Email with Gmail ID {request.gmail_id} already exists")
            raise HTTPException(
                status_code=409,
                detail="Email with this Gmail ID already exists"
            )
        # --- Gemini Classifier Logging ---
        trace_id = str(uuid.uuid4())
        start_time = datetime.utcnow().isoformat() + "Z"
        category, gemini_prompt, gemini_model = classify_email(request.subject, request.body, return_prompt_and_model=True)
        end_time = datetime.utcnow().isoformat() + "Z"
        prompt_tokens = len(gemini_prompt.split()) if gemini_prompt else 0
        completion_tokens = len(category.split()) if category else 0
        total_tokens = prompt_tokens + completion_tokens
        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }
        crashlens_logger.log_event(
            traceId=trace_id,
            startTime=start_time,
            endTime=end_time,
            input={"model": gemini_model, "prompt": gemini_prompt},
            usage=usage,
            output=category,
            output_file="logs.jsonl"
            
        )
        logger.info(f"Classified as: {category}")
        # --- Summarization Logging (optional, still hardcoded prompt/model) ---
        summary_trace_id = str(uuid.uuid4())
        summary_start_time = datetime.utcnow().isoformat() + "Z"
        summary_prompt = f"Summarize the following text into 5 key bullet points.\nFocus on the most important information and main points.\nKeep each bullet point concise and clear.\n\nText:\n{request.body}\n\nReturn only the bullet points, one per line, starting with '- '."
        summary_model = gemini_model
        summary = summarize_to_bullets(request.body)
        summary_end_time = datetime.utcnow().isoformat() + "Z"
        summary_prompt_tokens = len(summary_prompt.split())
        summary_completion_tokens = sum(len(s.split()) for s in summary)
        summary_total_tokens = summary_prompt_tokens + summary_completion_tokens
        summary_usage = {
            "prompt_tokens": summary_prompt_tokens,
            "completion_tokens": summary_completion_tokens,
            "total_tokens": summary_total_tokens
        }
        crashlens_logger.log_event(
            traceId=summary_trace_id,
            startTime=summary_start_time,
            endTime=summary_end_time,
            input={"model": summary_model, "prompt": summary_prompt},
            usage=summary_usage,
            output=summary,
            output_file="logs.jsonl"
        )
        logger.info(f"Generated summary with {len(summary)} bullet points")
        current_time = datetime.utcnow().isoformat()
<<<<<<< HEAD
        logger.info(f"Timestamp: {current_time}")
        # Prepare email document
=======
        logger.info(f"\ud83d\udcc5 Timestamp: {current_time}")
>>>>>>> 94bb2a09def6d5cf440c6b59f6eebedb12e9c613
        email_doc = {
            "user_id": clerk_user_id,
            "gmail_id": request.gmail_id,  # Gmail ID is required
            "subject": request.subject,
            "body": request.body,
            "category": category,
            "timestamp": current_time,
            "sender_name": request.sender_name or "Manual Classification",
            "sender_email": request.sender_email or "Manual Classification",
            "summary": summary
        }
        if not await email_db.save_email(email_doc):
            logger.warning(f"Failed to save email with Gmail ID {request.gmail_id}")
            raise HTTPException(
                status_code=500,
                detail="Failed to save email"
            )
        logger.success(f"Email successfully processed and saved")
        return EmailResponse(**email_doc)
    except HTTPException as e:
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
<<<<<<< HEAD
    batch_size: int = Query(10, ge=1, le=50, description="Number of emails to process in each batch"),
    user_id: str = Query(..., description="User ID to fetch emails for")
=======
    batch_size: int = Query(10, ge=1, le=50, description="Number of emails to process in each batch")
>>>>>>> 94bb2a09def6d5cf440c6b59f6eebedb12e9c613
):
    """
    Fetch the latest emails from Gmail and start background processing.
    Returns immediately with the list of emails that will be processed.
    """
    try:
<<<<<<< HEAD
        clerk_user_id = user_id
        if not isinstance(clerk_user_id, str) or not clerk_user_id.strip():
            logger.error(f"No valid user ID provided: {clerk_user_id}")
            raise HTTPException(status_code=400, detail="No valid user ID provided.")
=======
        # Set user_id to 'anonymous' for unauthenticated requests
        clerk_user_id = "anonymous"
>>>>>>> 94bb2a09def6d5cf440c6b59f6eebedb12e9c613
        emails = await get_latest_emails(clerk_user_id, 50)  # Fetch more emails than batch size
        if not emails:
            logger.info("No new emails found to process")
            return []
<<<<<<< HEAD
        logger.info(f"📧 Found {len(emails)} emails to process")
        # Create a mock user object for background processing
        mock_user = {"clerk_user_id": clerk_user_id, "sub": clerk_user_id}
        background_tasks.add_task(process_emails_background, emails, batch_size, mock_user)
=======
        logger.info(f"\ud83d\udce7 Found {len(emails)} emails to process")
        background_tasks.add_task(process_emails_background, emails, batch_size, {"clerk_user_id": clerk_user_id})
>>>>>>> 94bb2a09def6d5cf440c6b59f6eebedb12e9c613
        logger.info(f"Started background processing with batch size: {batch_size}")
        return [ClassifiedEmail(**email) for email in emails]
    except Exception as e:
        logger.error(f"\u274c Failed to start email processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch or classify emails: {str(e)}"
        ) 