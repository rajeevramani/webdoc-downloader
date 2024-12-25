import logging
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger instance."""
    logger = logging.getLogger("webdoc_downloader")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger


def is_valid_file(filename: str, allowed_extensions: Optional[List[str]] = None) -> bool:
    """Check if the file type is allowed based on extension."""
    if not allowed_extensions:
        return True
    return Path(filename).suffix.lower() in allowed_extensions


def sanitize_filename(filename: str) -> str:
    """Clean filename to ensure it's valid for the file system."""
    # TODO: Implement filename sanitization
    return filename
