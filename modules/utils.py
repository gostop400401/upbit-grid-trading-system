import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(name: str = "TradingSystem", log_file: str = "logs/system.log", level=logging.INFO):
    """
    Sets up a logger that writes to console and a rotating file.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.hasHandlers():
        return logger

    # Formatter
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File Handler (Rotating)
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG) # File captures everything

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO) # Console captures INFO and above

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def test_logger():
    """
    Test function to verify logger setup.
    """
    logger = setup_logger()
    logger.info("Logger test: INFO message")
    logger.debug("Logger test: DEBUG message")
    logger.warning("Logger test: WARNING message")
    logger.error("Logger test: ERROR message")
    print("Logger test complete. Check console and logs/system.log")

if __name__ == "__main__":
    test_logger()
