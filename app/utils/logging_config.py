"""
Logging configuration for the application
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

from config import settings


def setup_logging():
    """
    Configure application-wide logging
    
    Logs to both console and file for audit trail
    """
    # Create logs directory
    logs_dir = settings.BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Create log filename with timestamp
    log_filename = logs_dir / f"tor_correlation_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler (more detailed)
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Log startup
    root_logger.info("=" * 80)
    root_logger.info("TOR Metadata Correlation System - Starting")
    root_logger.info(f"Log file: {log_filename}")
    root_logger.info("=" * 80)
