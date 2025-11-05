"""
Logging utilities for the cross-chain framework.

This module provides a centralized logging configuration for the framework.
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: The name of the logger (typically __name__)
        level: Optional logging level (defaults to INFO)

    Returns:
        A configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("This is a log message")
    """
    logger = logging.getLogger(f"langgraph_crosschain.{name}")

    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if level is not None:
        logger.setLevel(level)
    elif logger.level == logging.NOTSET:
        logger.setLevel(logging.INFO)

    return logger


def configure_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    handler: Optional[logging.Handler] = None,
) -> None:
    """
    Configure logging for the entire framework.

    Args:
        level: The logging level to use
        format_string: Optional custom format string
        handler: Optional custom handler to use

    Example:
        >>> import logging
        >>> configure_logging(level=logging.DEBUG)
    """
    root_logger = logging.getLogger("langgraph_crosschain")
    root_logger.setLevel(level)

    # Remove existing handlers
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    # Add new handler
    if handler is None:
        handler = logging.StreamHandler(sys.stdout)

    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def disable_logging() -> None:
    """Disable all logging for the framework."""
    logging.getLogger("langgraph_crosschain").setLevel(logging.CRITICAL + 1)


def enable_debug_logging() -> None:
    """Enable debug-level logging for the framework."""
    configure_logging(level=logging.DEBUG)
