import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def _create_handler(filename: str) -> RotatingFileHandler:
    """Helper to create a rotating file handler."""
    handler = RotatingFileHandler(
        os.path.join(LOG_DIR, filename),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5
    )
    handler.setFormatter(logging.Formatter(DEFAULT_FORMAT))
    return handler


def get_logger(name: str = "app", filename: str = "app.log") -> logging.Logger:
    """
    Factory function to create or return a named logger.
    Each logger writes to its own log file.
    """

    logger = logging.getLogger(name)

    if logger.handlers:  # If already configured, return it.
        return logger

    logger.setLevel(logging.DEBUG)

    # File handler
    file_handler = _create_handler(filename)
    logger.addHandler(file_handler)

    # Console handler (optional)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(DEFAULT_FORMAT))
    logger.addHandler(console_handler)

    return logger


# Pre-defined loggers for convenience
app_log = get_logger("app_logger", "app.log")
agent_log = get_logger("agent_logger", "agent.log")
api_trace_log = get_logger("api_trace_logger", "api_trace.log")