from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.logger import setup_logging
from app.core.middleware import setup_middleware
from app.routers import email_routes, classify_routes, health_routes

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

# Include routers
app.include_router(email_routes.router, prefix="/api/v1")
app.include_router(classify_routes.router, prefix="/api/v1")
app.include_router(health_routes.router ,prefix="/api/v1")
logger.info("API routes configured")

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown initiated")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 