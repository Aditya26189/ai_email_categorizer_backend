import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import json
from datetime import datetime

from loguru import logger

class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def setup_logging(
    *,
    log_path: Path = Path("logs"),
    level: str = "INFO",
    retention: str = "1 week",
    rotation: str = "500 MB",
    format: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
) -> None:
    """Configure logging for the application."""
    log_path.mkdir(parents=True, exist_ok=True)

    # Remove all existing handlers
    logging.root.handlers = []

    # Configure loguru
    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "level": level,
                "format": format,
            },
            {
                "sink": log_path / "app.log",
                "level": level,
                "format": format,
                "rotation": rotation,
                "retention": retention,
            },
        ]
    )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Remove uvicorn access log
    logging.getLogger("uvicorn.access").handlers = []

    # Set loguru as the default logger
    for name in ["uvicorn", "uvicorn.error", "fastapi"]:
        logging_logger = logging.getLogger(name)
        logging_logger.handlers = [InterceptHandler()]

    logger.info("Logging configured successfully")

def log_request(
    method: str,
    path: str,
    status_code: int,
    user_id: Optional[str] = None,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None
) -> None:
    """Log HTTP request details."""
    log_data = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
    }
    
    if user_id:
        log_data["user_id"] = user_id
    if error:
        log_data["error"] = error

    logger.info(f"Request: {json.dumps(log_data)}")

def log_db_operation(
    operation: str,
    collection: str,
    document_id: Optional[str] = None,
    error: Optional[str] = None
) -> None:
    """Log database operations."""
    log_data = {
        "operation": operation,
        "collection": collection,
    }
    
    if document_id:
        log_data["document_id"] = document_id
    if error:
        log_data["error"] = error

    logger.info(f"Database: {json.dumps(log_data)}")

def log_auth_event(
    event: str,
    user_id: Optional[str] = None,
    error: Optional[str] = None
) -> None:
    """Log authentication events."""
    log_data = {
        "event": event,
    }
    
    if user_id:
        log_data["user_id"] = user_id
    if error:
        log_data["error"] = error

    logger.info(f"Auth: {json.dumps(log_data)}")

def log_email_operation(
    operation: str,
    email_id: Optional[str] = None,
    category: Optional[str] = None,
    error: Optional[str] = None
) -> None:
    """Log email-related operations."""
    log_data = {
        "operation": operation,
    }
    
    if email_id:
        log_data["email_id"] = email_id
    if category:
        log_data["category"] = category
    if error:
        log_data["error"] = error

    logger.info(f"Email: {json.dumps(log_data)}") 