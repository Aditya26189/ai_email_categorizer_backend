from fastapi import FastAPI, Depends
from fastapi.openapi.models import SecurityScheme
from loguru import logger
from app.db.base import db
from app.db import email_db
from app.core.logger import setup_logging, log_request
from app.core.middleware import setup_middleware
from app.routers import email_routes, classify_routes, health_routes, webhook, gmail
from app.routers.auth import auth_routes, clerk_webhook
from app.routers.auth_callback import router as auth_callback_router
from app.routers.oauth_callback import router as oauth_callback_router
from app.core.clerk import clerk_auth
from app.core.config import settings

# Setup logging
setup_logging()
logger.info("Starting application initialization")

app = FastAPI(
    title="AI Email Categorizer",
    description="API for categorizing emails using AI",
    version="1.0.0",
)
logger.info("FastAPI application created")

# Setup middleware
setup_middleware(app)
logger.info("Middleware configured")

# Include routers with Clerk authentication
app.include_router(email_routes.router, prefix="/routers/v1", dependencies=[Depends(clerk_auth)])
app.include_router(classify_routes.router, prefix="/routers/v1")
app.include_router(auth_routes, prefix="/routers/v1", dependencies=[Depends(clerk_auth)])
app.include_router(health_routes.router, prefix="/routers/v1")  # Health check doesn't need auth
app.include_router(clerk_webhook)
app.include_router(webhook.router)
app.include_router(gmail.router, prefix="/routers/v1", dependencies=[Depends(clerk_auth)])
app.include_router(auth_callback_router)  # No prefix - handles /auth/callback directly
app.include_router(oauth_callback_router)  # No prefix - handles /routers/v1/gmail/oauth/callback directly
logger.info("API routes configured")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting database connections")
    try:
        # First connect to the database
        await db.connect_db() 
        logger.info("✅ Database connection established")
        
        # Then initialize the email collection
        logger.info("Initializing email database...")
        await email_db.init()
        logger.info("✅ Email database initialized")
        
        # Ensure indexes are created
        logger.info("Creating database indexes...")
        await email_db.ensure_indexes()
        logger.info("✅ Database indexes created")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        raise
    
    # Clean up expired OAuth states
    try:
        from app.services.google_oauth import google_oauth_service
        await google_oauth_service.cleanup_expired_states()
        logger.info("✅ Cleaned up expired OAuth states")
    except Exception as e:
        logger.warning(f"Could not clean up expired OAuth states: {e}")
    
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown initiated")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server in {'development' if settings.DEBUG else 'production'} mode")
    uvicorn.run(app, host="0.0.0.0", port=8000) 