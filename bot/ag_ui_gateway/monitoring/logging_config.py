"""
Logging Configuration

Sets up structured logging with Loguru.
"""
import sys
from loguru import logger

from ag_ui_gateway.config.settings import settings


def setup_logging():
    """Configure logging with Loguru."""
    # Remove default handler
    logger.remove()
    
    # Add custom handler
    if settings.LOG_FORMAT == "json":
        logger.add(
            sys.stdout,
            format="{message}",
            level=settings.LOG_LEVEL,
            serialize=True
        )
    else:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level=settings.LOG_LEVEL,
            colorize=True
        )
    
    logger.info("Logging configured")
