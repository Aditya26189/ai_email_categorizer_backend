from fastapi import FastAPI, Depends
from fastapi.openapi.models import SecurityScheme
from loguru import logger
from app.db.base import db
from app.db import email_db
from app.core.logger import setup_logging, log_request
from app.core.middleware import setup_middleware
from app.routers import email_routes, classify_routes, health_routes
from app.routers.auth import auth_routes, clerk_webhook
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
app.include_router(classify_routes.router, prefix="/routers/v1", dependencies=[Depends(clerk_auth)])
app.include_router(auth_routes.router, prefix="/routers/v1", dependencies=[Depends(clerk_auth)])
app.include_router(health_routes.router, prefix="/routers/v1")  # Health check doesn't need auth
app.include_router(clerk_webhook.router)
logger.info("API routes configured")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting database connections")
    await db.connect_db() 
    await email_db.email_db.init()
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown initiated")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server in {'development' if settings.DEBUG else 'production'} mode")
    uvicorn.run(app, host="0.0.0.0", port=8000) 