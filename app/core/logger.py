import logging
import sys
from pathlib import Path
from typing import Any, Dict

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