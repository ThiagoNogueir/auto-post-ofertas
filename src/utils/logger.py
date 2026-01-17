"""
Logger configuration using loguru.
Outputs to both stdout and rotating log file.
"""

from loguru import logger
import sys
import os

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Remove default handler
logger.remove()

# Add stdout handler with colorized output
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True
)

# Add file handler with rotation
logger.add(
    "logs/bot.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="5 MB",  # Rotate when file reaches 5MB
    retention="10 days",  # Keep logs for 10 days
    compression="zip",  # Compress rotated logs
    encoding="utf-8"
)

# Export configured logger
__all__ = ['logger']
