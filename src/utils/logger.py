"""
Logging configuration for CVPilot
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logger(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> logging.Logger:
    """
    Setup logger for CVPilot
    
    Args:
        level: Logging level
        log_file: Path to log file (optional)
        log_format: Log message format
    
    Returns:
        Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger("CVPilot")
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_log_file_path(base_path: Path) -> Path:
    """
    Generate log file path with timestamp
    
    Args:
        base_path: Base directory for logs
    
    Returns:
        Path to log file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return base_path / f"cvpilot_{timestamp}.log"

class LoggerMixin:
    """Mixin class to add logging capabilities to other classes"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(f"CVPilot.{self.__class__.__name__}")
    
    def log_info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def log_error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def log_warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def log_debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
