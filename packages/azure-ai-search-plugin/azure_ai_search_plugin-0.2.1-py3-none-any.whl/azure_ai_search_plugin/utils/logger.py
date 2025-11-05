"""
Logging utility for the Azure AI Search Plugin.

This module provides a helper function to configure and return
a standardized logger instance with consistent formatting across
the entire package.
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """Create and return a configured logger instance.

    The logger is configured with:
        - StreamHandler (outputs to console)
        - Standardized timestamped formatter
        - Log level set to INFO by default

    Ensures no duplicate handlers are added if the logger already exists.

    Args:
        name (str): Name of the logger, typically `__name__` of the calling module.

    Returns:
        logging.Logger: Configured logger instance ready for use.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
