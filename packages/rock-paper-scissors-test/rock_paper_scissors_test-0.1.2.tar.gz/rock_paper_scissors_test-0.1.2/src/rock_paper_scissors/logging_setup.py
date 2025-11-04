import logging
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from .config import settings

LOG_FORMAT = logging.Formatter(
    "[%(asctime)s] %(name)-35s %(levelname)-8s [%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def setup_logging(logger_type: str) -> None:
    """Configure the root logger for the application with console and file handlers.

    Args:
        logger_type: The type of file handler to use. Accepts "timed"
            (daily rotation), "size" (rotates when file is full), or "standard"
            (a single, non-rotating file).
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Clear any existing handlers to prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create the logging storage directory if it doesn't exist
    log_dir = settings.LOG_PATH.parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create the appropriate file handler based on the type
    file_handler: logging.Handler

    if logger_type == "timed":
        file_handler = TimedRotatingFileHandler(
            settings.LOG_PATH,
            when="midnight",
            interval=1,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
    elif logger_type == "size":
        file_handler = RotatingFileHandler(
            settings.LOG_PATH,
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
    elif logger_type == "standard":
        file_handler = logging.FileHandler(
            settings.LOG_PATH, mode="a", encoding="utf-8"
        )
    else:
        raise ValueError(
            f"Invalid logger_type '{logger_type}'. "
            "Must be one of 'timed', 'size', or 'standard'."
        )

    # Add handlers to the root logger
    file_handler.setFormatter(LOG_FORMAT)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(LOG_FORMAT)
    logger.addHandler(console_handler)

    logger.info("Logging configured with '%s' file handler.", logger_type)
