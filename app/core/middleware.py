from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings

def setup_middleware(app: FastAPI) -> None:
    """Configure middleware for the application.
    
    Development configuration:
    - CORS allows all origins for easy local development
    - In production, replace with specific origins
    """
    
    app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET_KEY)

    # CORS middleware - allows all origins in development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Development: allows all origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ) 