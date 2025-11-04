"""Logging utilities."""

import logging
from pathlib import Path


def setup_logging(level: str, log_file: str) -> None:
    """Setup basic application logging."""
    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Handle log file path
    log_path = Path(log_file)

    # Ensure the directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler(log_path),  # File output
        ],
    )
