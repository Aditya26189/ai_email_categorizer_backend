from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response
import time
from app.core.config import settings
from app.core.logger import log_request

async def log_requests_and_responses(request: Request, call_next):
    start_time = time.time()
    request_body = await request.body()
    method = request.method
    path = request.url.path
    try:
        response = await call_next(request)
        status_code = response.status_code
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        # Recreate the response with the body for downstream
        response = Response(content=response_body, status_code=status_code, headers=dict(response.headers), media_type=response.media_type)
        duration_ms = (time.time() - start_time) * 1000
        log_request(method, path, status_code, duration_ms=duration_ms)
        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_request(method, path, 500, duration_ms=duration_ms, error=str(e))
        raise

def setup_middleware(app: FastAPI) -> None:
    """Configure middleware for the application.
    
    Development configuration:
    - CORS allows all origins for easy local development
    - In production, replace with specific origins
    """
    app.middleware('http')(log_requests_and_responses)
    app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET_KEY)

    # CORS middleware - allows all origins in development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # or your deployed frontend
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ) 