"""Tests for logging utilities."""

import logging

from langgraph_crosschain.logging import (
    configure_logging,
    disable_logging,
    enable_debug_logging,
    get_logger,
)


class TestLogging:
    """Test suite for logging utilities."""

    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert "langgraph_crosschain.test_module" in logger.name

    def test_get_logger_with_level(self):
        """Test getting a logger with custom level."""
        logger = get_logger("test_module", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_configure_logging(self):
        """Test configuring logging."""
        configure_logging(level=logging.WARNING)
        logger = logging.getLogger("langgraph_crosschain")
        assert logger.level == logging.WARNING

    def test_disable_logging(self):
        """Test disabling logging."""
        disable_logging()
        logger = logging.getLogger("langgraph_crosschain")
        assert logger.level > logging.CRITICAL

    def test_enable_debug_logging(self):
        """Test enabling debug logging."""
        enable_debug_logging()
        logger = logging.getLogger("langgraph_crosschain")
        assert logger.level == logging.DEBUG

    def test_logger_can_log(self):
        """Test that logger can actually log messages."""
        logger = get_logger("test_module")
        # This should not raise an error
        logger.info("Test message")
        logger.debug("Debug message")
        logger.warning("Warning message")
        logger.error("Error message")
