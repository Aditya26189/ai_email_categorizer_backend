from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger

from app.models.schemas import EmailResponse, EmailRequest, EmailIdentifier, ClassifiedEmail
from app.db.email_db import email_db
from app.services.gmail_client import get_latest_emails
from app.utils.llm_utils import summarize_to_bullets
from app.services.classifier import classify_email

router = APIRouter(prefix="/emails", tags=["emails"])

def normalize_category(category: str) -> str:
    """Normalize category string by converting to lowercase and stripping whitespace."""
    return category.lower().strip()

# API Endpoints
@router.get("/emails", response_model=List[EmailResponse])
async def get_emails(
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    q: Optional[str] = Query(None, min_length=2, max_length=100, description="Search in subject, body, and sender")
):
    """
    Get all emails with pagination, search, and filtering.
    Results are sorted by timestamp (newest first).
    
    Args:
        category: Filter by category (case-insensitive)
        page: Page number (starts at 1)
        limit: Items per page (max 100)
        q: Search query for subject/body/sender (2-100 chars)
    """
    try:
        logger.info(f"[EMAILS] Category filter entered: {category}")
        # Initialize empty query
        query = {}
        if category is not None:
            query["category"] = {"$regex": f"^{category}$", "$options": "i"}
        
        # Validate search query if provided
        if q:
            q = q.strip()
            if len(q) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="Search query must be at least 2 characters long"
                )
            if len(q) > 100:
                raise HTTPException(
                    status_code=400,
                    detail="Search query cannot exceed 100 characters"
                )
            # Search in subject, body, and sender
            query["$or"] = [
                {"subject": {"$regex": q, "$options": "i"}},
                {"body": {"$regex": q, "$options": "i"}},
                {"sender": {"$regex": q, "$options": "i"}}
            ]
            logger.info(f"Using search query: {q}")
        
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(
                status_code=400,
                detail="Page number must be greater than 0"
            )
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 100"
            )
        
        logger.info(f"📧 GET /emails - Retrieving emails with filters:")
        logger.info(f"Category: {category}, Page: {page}, Limit: {limit}, Search: {q}")
        
        # Calculate skip value for pagination
        skip = (page - 1) * limit
        
        # Get total count for pagination info
        total = await email_db.collection.count_documents(query)
        
        # Validate if requested page exists
        total_pages = (total + limit - 1) // limit
        if page > total_pages and total > 0:
            raise HTTPException(
                status_code=404,
                detail=f"Page {page} does not exist. Total pages: {total_pages}"
            )
        
        # Get paginated results
        cursor = email_db.collection.find(
            query,
            {'_id': 0}
        ).sort('timestamp', -1).skip(skip).limit(limit)
        
        emails = await cursor.to_list(length=None)
        logger.info(f"Total emails found: {len(emails)}")
        
        # Ensure all emails have required fields
        for email in emails:
            if 'sender' not in email or not email['sender']:
                email['sender'] = email.get('from', '')  # Try 'from' field if 'sender' is missing
                logger.debug(f"Using 'from' field as sender for email: {email.get('subject', 'No subject')}")
            
            if 'timestamp' not in email:
                email['timestamp'] = datetime.utcnow().isoformat()
                logger.warning(f"⚠️ Missing timestamp for {email.get('subject', 'No subject')}, set to: {email['timestamp']}")
            
            if 'summary' not in email:
                email['summary'] = []
                logger.debug(f"Added empty summary for email: {email.get('subject', 'No subject')}")
        
        # Add pagination info to response headers
        headers = {
            "X-Total-Count": str(total),
            "X-Total-Pages": str(total_pages),
            "X-Current-Page": str(page),
            "X-Per-Page": str(limit)
        }
        
        logger.info(f"✅ Retrieved {len(emails)} emails (page {page} of {total_pages})")
        return emails
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"❌ Failed to retrieve emails: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve emails: {str(e)}"
        )

@router.get("/categories", response_model=List[str])
async def get_categories():
    """
    Get the list of all available email categories.
    Categories are returned in their original case.
    """
    return await email_db.get_all_categories()

@router.post("/emails/{gmail_id}/re_summary")
async def generate_new_email_summary(gmail_id: str):
    """
    Generate a summary for a specific email using its Gmail ID.
    This will create a new summary even if one already exists.
    """
    try:
        # Find the email
        email = await email_db.get_email_by_gmail_id(gmail_id)
        if not email:
            logger.warning(f"❌ Email not found with Gmail ID: {gmail_id}")
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Email not found",
                    "gmail_id": gmail_id,
                    "help": "Please verify the Gmail ID is correct and the email exists in the database"
                }
            )
            
        # Generate new summary
        new_summary = summarize_to_bullets(email["body"])
        logger.info(f"Generated summary with {len(new_summary)} bullet points for Gmail ID: {gmail_id}")
        
        # Update the email with new summary
        await email_db.collection.update_one(
            {"gmail_id": gmail_id},
            {"$set": {"summary": new_summary}}
        )
        
        return {
            "message": "Summary generated successfully",
            "gmail_id": gmail_id,
            "summary": new_summary
        }
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"❌ Error generating summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )

@router.get("/by-categories", response_model=Dict[str, List[EmailResponse]])
async def get_emails_by_categories(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page per category"),
    q: Optional[str] = Query(None, min_length=2, max_length=100, description="Search in subject, body, and sender")
):
    """
    Get all emails grouped by their categories.
    Each category contains a paginated list of emails.
    Results are sorted by timestamp (newest first) within each category.
    
    Args:
        page: Page number (starts at 1)
        limit: Items per page per category (max 100)
        q: Search query for subject/body/sender (2-100 chars)
    """
    try:
        # Get all categories
        categories = await email_db.get_all_categories()
        if not categories:
            logger.warning("No categories found")
            return {}
            
        logger.info(f"📧 GET /by-categories - Retrieving emails for {len(categories)} categories")
        
        # Initialize result dictionary
        result = {}
        
        # Calculate skip value for pagination
        skip = (page - 1) * limit
        
        # Get emails for each category
        for category in categories:
            try:
                # Build query
                query = {"category": category}
                
                # Add search query if provided
                if q:
                    q = q.strip()
                    if len(q) < 2:
                        raise HTTPException(
                            status_code=400,
                            detail="Search query must be at least 2 characters long"
                        )
                    if len(q) > 100:
                        raise HTTPException(
                            status_code=400,
                            detail="Search query cannot exceed 100 characters"
                        )
                    query["$or"] = [
                        {"subject": {"$regex": q, "$options": "i"}},
                        {"body": {"$regex": q, "$options": "i"}},
                        {"sender": {"$regex": q, "$options": "i"}}
                    ]
                
                # Get total count for this category
                total = await email_db.collection.count_documents(query)
                
                # Validate if requested page exists
                total_pages = (total + limit - 1) // limit
                if page > total_pages and total > 0:
                    logger.warning(f"Page {page} does not exist for category {category}. Total pages: {total_pages}")
                    result[category] = []
                    continue
                
                # Get paginated results for this category
                cursor = email_db.collection.find(
                    query,
                    {'_id': 0}
                ).sort('timestamp', -1).skip(skip).limit(limit)
                
                emails = await cursor.to_list(length=None)
                
                # Ensure all emails have required fields
                for email in emails:
                    if 'sender' not in email or not email['sender']:
                        email['sender'] = email.get('from', '')
                    if 'timestamp' not in email:
                        email['timestamp'] = datetime.utcnow().isoformat()
                    if 'summary' not in email:
                        email['summary'] = []
                
                result[category] = emails
                logger.info(f"Retrieved {len(emails)} emails for category: {category}")
                
            except Exception as e:
                logger.error(f"Error processing category {category}: {str(e)}")
                result[category] = []
                continue
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to retrieve emails by categories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve emails by categories: {str(e)}"
        )
    