import logging
import sys
from datetime import datetime

def setup_logger(name="social_threat_monitor", level=logging.INFO):
    """
    Setup logger with professional formatting

    Args:
        name (str): Logger name (usually module name)
        level: Logging level (INFO, DEBUG, ERROR, etc.)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if logger already exists
    if not logger.handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)

        # Create formatter with timestamp and detailed info
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Set formatter to handler
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

    return logger

def setup_file_logger(name, filename, level=logging.INFO):
    """
    Setup file-based logger for persistent logging

    Args:
        name (str): Logger name
        filename (str): Log file path
        level: Logging level

    Returns:
        logging.Logger: Configured file logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # Create file handler
        file_handler = logging.FileHandler(filename)

        # Create detailed formatter for file logs
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Also add console handler for immediate feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger
