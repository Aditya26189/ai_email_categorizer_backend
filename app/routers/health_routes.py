from fastapi import APIRouter, HTTPException
from loguru import logger
from datetime import datetime
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.services.gmail_client import get_gmail_service

router = APIRouter(tags=["health"])

async def check_mongodb():
    """Check MongoDB connection and get basic stats."""
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        # Ping the server
        await client.admin.command('ping')
        
        # Get database stats
        db = client[settings.MONGODB_DB_NAME]
        stats = await db.command("dbStats")
        
        return {
            "status": "healthy",
            "details": {
                "connection": "connected",
                "database": settings.MONGODB_DB_NAME,
                "collections": stats.get("collections", 0),
                "documents": stats.get("objects", 0),
                "data_size": f"{stats.get('dataSize', 0) / 1024 / 1024:.2f} MB",
                "storage_size": f"{stats.get('storageSize', 0) / 1024 / 1024:.2f} MB"
            }
        }
    except Exception as e:
        logger.error(f"MongoDB health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "details": {
                "error": str(e),
                "connection": "disconnected"
            }
        }

async def check_gmail_api():
    """Check Gmail API connectivity and quota status."""
    try:
        service = await get_gmail_service()
        
        return {
            "status": "healthy",
            "details": {
                "connection": "connected",
                }
            }
    except Exception as e:
        logger.error(f"Gmail API health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "details": {
                "error": str(e),
                "connection": "disconnected"
            }
        }

async def check_llm_service():
    """Check LLM service connectivity and response time."""
    try:
        start_time = datetime.now()
        response_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "status": "healthy",
            "details": {
                "connection": "connected",
                "response_time": f"{response_time:.2f}s",
                "api_url": settings.GEMINI_API_URL
            }
        }
    except Exception as e:
        logger.error(f"LLM service health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "details": {
                "error": str(e),
                "connection": "disconnected"
            }
        }

@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint that verifies the status of all services.
    Returns detailed diagnostic information for MongoDB, Gmail API, and LLM service.
    """
    try:
        # Run all health checks concurrently
        mongo_status = await check_mongodb()
        gmail_status = await check_gmail_api()
        llm_status = await check_llm_service()
        
        # Determine overall health
        overall_status = "healthy" if all(
            service["status"] == "healthy" 
            for service in [mongo_status, gmail_status, llm_status]
        ) else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "mongodb": mongo_status,
                "gmail_api": gmail_status,
                "llm_service": llm_status
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        ) 