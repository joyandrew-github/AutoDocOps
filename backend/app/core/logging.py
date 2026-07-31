import sys
import json
from loguru import logger
from app.core.config import settings


def _json_sink(message):
    """Structured JSON log sink for production."""
    record = message.record
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "logger": record.get("extra", {}).get("name", record["name"]),
        "function": record["function"],
        "line": record["line"],
        "message": record["message"],
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }
    print(json.dumps(log_entry, default=str), flush=True)


def setup_logging() -> None:
    """Configure application logging using Loguru."""
    
    # Remove default handler
    logger.remove()

    if settings.ENVIRONMENT == "production":
        # Structured JSON output for production
        logger.add(_json_sink, level=settings.LOG_LEVEL)
    else:
        # Add console handler with color
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.LOG_LEVEL,
            colorize=True,
        )
    
    # Add file handler for errors
    logger.add(
        "logs/error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )
    
    # Add file handler for all logs
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )
    
    logger.info(f"Logging configured. Level: {settings.LOG_LEVEL} Environment: {settings.ENVIRONMENT}")


def get_logger(name: str):
    """Get a logger instance for a specific module."""
    return logger.bind(name=name)
