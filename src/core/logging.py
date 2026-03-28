import sys
from loguru import logger
from src.core.config import settings

def setup_logging():
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan> - {message}"
    )
    logger.add(
        "logs/agentreview.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        serialize=True
    )
    return logger