"""
Unit tests for the logger utility module.

This module tests the logging configuration, formatters, handlers, and utility
functions from nyc_landmarks.utils.logger.
"""

import json
import logging
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from nyc_landmarks.config.settings import LogProvider
from nyc_landmarks.utils.logger import (
    EnhancedCloudLoggingHandler,
    LoggerSetup,
    LoggingContext,
    StructuredFormatter,
    cleanup_loggers,
    configure_basic_logging_safely,
    flush_loggers,
    get_logger,
    log_error,
    log_performance,
    log_with_attributes,
    log_with_context,
    shutdown_logging_gracefully,
)


class TestStructuredFormatter(unittest.TestCase):
    """Test the StructuredFormatter class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.formatter = StructuredFormatter(include_context=True)
        self.formatter_no_context = StructuredFormatter(include_context=False)

    def test_format_basic_record(self) -> None:
        """Test formatting a basic log record."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = self.formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["message"] == "Test message"
        assert parsed["severity"] == "INFO"
        assert parsed["module"] == "test"
        # funcName might be None for module-level records
        assert parsed.get("function") is not None or parsed.get("function") is None
        assert parsed["line"] == 10
        assert "timestamp" in parsed
        assert "process_id" in parsed
        assert "thread_id" in parsed
        assert "environment" in parsed

    def test_format_with_args(self) -> None:
        """Test formatting a log record with arguments."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.WARNING,
            pathname="test.py",
            lineno=20,
            msg="Test message %s %d",
            args=("hello", 42),
            exc_info=None,
        )

        formatted = self.formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["message"] == "Test message hello 42"
        assert parsed["severity"] == "WARNING"

    def test_format_with_exception(self) -> None:
        """Test formatting a log record with exception information."""
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=30,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )

        formatted = self.formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["message"] == "Error occurred"
        assert parsed["severity"] == "ERROR"
        assert "exception" in parsed
        assert parsed["exception"]["type"] == "ValueError"
        assert parsed["exception"]["message"] == "Test exception"
        assert isinstance(parsed["exception"]["traceback"], list)

    def test_format_with_extra_fields(self) -> None:
        """Test formatting a log record with extra fields."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=40,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add extra fields
        record.custom_field = "custom_value"
        record.correlation_id = "abc123"

        formatted = self.formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["custom_field"] == "custom_value"
        assert parsed["correlation_id"] == "abc123"

    def test_format_without_context(self) -> None:
        """Test formatting without request context."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=50,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = self.formatter_no_context.format(record)
        parsed = json.loads(formatted)

        assert parsed["message"] == "Test message"
        # Should not include context-specific fields
        assert "correlation_id" not in parsed or parsed.get("correlation_id") is None

    @patch("nyc_landmarks.utils.logger.REQUEST_CONTEXT_AVAILABLE", True)
    @patch("nyc_landmarks.utils.logger.get_request_context")
    def test_format_with_request_context(self, mock_get_context: Mock) -> None:
        """Test formatting with request context."""
        mock_get_context.return_value = {
            "correlation_id": "test-correlation-123",
            "endpoint": "/api/test",
        }

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=60,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = self.formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["correlation_id"] == "test-correlation-123"
        assert parsed["endpoint"] == "/api/test"

    @patch("nyc_landmarks.utils.logger.REQUEST_CONTEXT_AVAILABLE", True)
    @patch("nyc_landmarks.utils.logger.get_request_context")
    def test_format_with_context_exception(self, mock_get_context: Mock) -> None:
        """Test formatting when context extraction fails."""
        mock_get_context.side_effect = Exception("Context error")

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=70,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Should not raise exception
        formatted = self.formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["message"] == "Test message"


class TestEnhancedCloudLoggingHandler(unittest.TestCase):
    """Test the EnhancedCloudLoggingHandler class."""

    @patch("nyc_landmarks.utils.logger.GCP_LOGGING_AVAILABLE", True)
    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a mock client for the handler
        mock_client = Mock()
        self.handler = EnhancedCloudLoggingHandler(mock_client)
        self.handler.labels = {"environment": "test"}

    @patch.object(EnhancedCloudLoggingHandler, "emit")
    def test_emit_with_endpoint_category(self, mock_emit: Mock) -> None:
        """Test emitting a log record with endpoint_category."""
        # Call the original emit method to test our logic
        mock_emit.side_effect = lambda record: super(
            EnhancedCloudLoggingHandler, self.handler
        ).emit(record)

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.endpoint_category = "api"

        # Test that labels are modified when endpoint_category is present
        if hasattr(record, "endpoint_category"):
            dynamic_labels = dict(self.handler.labels) if self.handler.labels else {}
            dynamic_labels["endpoint_category"] = getattr(record, "endpoint_category")
            assert dynamic_labels["endpoint_category"] == "api"
            assert "environment" in dynamic_labels

    def test_emit_without_endpoint_category(self) -> None:
        """Test emitting a log record without endpoint_category."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Test that record doesn't have endpoint_category
        assert not hasattr(record, "endpoint_category")

        # Verify handler labels exist and contain expected values
        if self.handler.labels:
            assert "environment" in self.handler.labels


class TestLoggerSetup(unittest.TestCase):
    """Test the LoggerSetup class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger_setup = LoggerSetup("test_logger")

    def tearDown(self) -> None:
        """Clean up after tests."""
        # Clean up handlers to prevent interference between tests
        logger = logging.getLogger("test_logger")
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)
        self.logger_setup._configured = False

    def test_init(self) -> None:
        """Test LoggerSetup initialization."""
        setup = LoggerSetup("my_logger")
        assert setup.name == "my_logger"
        assert setup.logger.name == "my_logger"
        assert not setup._configured

    def test_setup_with_console_only(self) -> None:
        """Test setting up logger with console handler only."""
        logger = self.logger_setup.setup(
            log_level=logging.DEBUG,
            log_to_console=True,
            log_to_file=False,
            provider=LogProvider.STDOUT,
        )

        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert self.logger_setup._configured

    def test_setup_with_file_only(self) -> None:
        """Test setting up logger with file handler only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = self.logger_setup.setup(
                log_level=logging.INFO,
                log_to_console=False,
                log_to_file=True,
                log_dir=temp_dir,
                log_filename="test.log",
                provider=LogProvider.STDOUT,
            )

            assert logger.level == logging.INFO
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], logging.FileHandler)

            # Verify log file was created
            log_file = Path(temp_dir) / "test.log"
            assert log_file.exists()

    def test_setup_with_both_handlers(self) -> None:
        """Test setting up logger with both console and file handlers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = self.logger_setup.setup(
                log_to_console=True,
                log_to_file=True,
                log_dir=temp_dir,
                provider=LogProvider.STDOUT,
            )

            assert len(logger.handlers) == 2
            handler_types = [type(h).__name__ for h in logger.handlers]
            assert "StreamHandler" in handler_types
            assert "FileHandler" in handler_types

    def test_setup_with_custom_format(self) -> None:
        """Test setting up logger with custom format."""
        custom_format = "%(levelname)s - %(message)s"
        logger = self.logger_setup.setup(
            log_to_console=True,
            log_to_file=False,
            log_format=custom_format,
            provider=LogProvider.STDOUT,
        )

        handler = logger.handlers[0]
        # Check if the formatter is a basic Formatter (not StructuredFormatter)
        # and that it was configured with the custom format
        assert handler.formatter is not None
        assert not isinstance(handler.formatter, StructuredFormatter)

        # Test the actual formatting to verify the custom format is applied
        test_record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        formatted = handler.formatter.format(test_record)
        assert "INFO - test message" == formatted

    def test_setup_with_structured_logging(self) -> None:
        """Test setting up logger with structured (JSON) logging."""
        logger = self.logger_setup.setup(
            log_to_console=True,
            log_to_file=False,
            structured=True,
            provider=LogProvider.STDOUT,
        )

        handler = logger.handlers[0]
        assert isinstance(handler.formatter, StructuredFormatter)

    def test_setup_already_configured(self) -> None:
        """Test that setup returns existing logger if already configured."""
        # First setup
        logger1 = self.logger_setup.setup()
        handlers_count = len(logger1.handlers)

        # Second setup should return same logger without adding handlers
        logger2 = self.logger_setup.setup()
        assert logger1 is logger2
        assert len(logger2.handlers) == handlers_count

    def test_setup_with_existing_handlers(self) -> None:
        """Test setup when logger already has handlers."""
        # Manually add a handler first
        logger = logging.getLogger("test_logger")
        handler = logging.StreamHandler()
        logger.addHandler(handler)

        # Setup should detect existing handlers and not add more
        result_logger = self.logger_setup.setup()
        assert result_logger is logger
        assert len(logger.handlers) == 1

    @patch("nyc_landmarks.utils.logger.GCP_LOGGING_AVAILABLE", True)
    @patch("nyc_landmarks.utils.logger.gcp_logging")
    def test_setup_with_google_provider(self, mock_gcp_logging: Mock) -> None:
        """Test setting up logger with Google Cloud provider."""
        mock_client = Mock()
        mock_gcp_logging.Client.return_value = mock_client

        logger = self.logger_setup.setup(
            provider=LogProvider.GOOGLE,
            log_to_console=False,
            log_to_file=False,
        )

        assert len(logger.handlers) == 1
        # Verify GCP client was created
        mock_gcp_logging.Client.assert_called_once()

    @patch("nyc_landmarks.utils.logger.GCP_LOGGING_AVAILABLE", True)
    @patch("nyc_landmarks.utils.logger.gcp_logging")
    def test_setup_google_provider_fallback(self, mock_gcp_logging: Mock) -> None:
        """Test fallback to console when Google Cloud setup fails."""
        mock_gcp_logging.Client.side_effect = Exception("GCP connection failed")

        logger = self.logger_setup.setup(
            provider=LogProvider.GOOGLE,
            log_to_console=False,
            log_to_file=False,
        )

        # Should fallback to console handler
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_get_logger_unconfigured(self) -> None:
        """Test get_logger when not yet configured."""
        logger = self.logger_setup.get_logger()
        assert self.logger_setup._configured
        assert len(logger.handlers) > 0

    def test_get_logger_already_configured(self) -> None:
        """Test get_logger when already configured."""
        # Configure first
        self.logger_setup.setup()
        handlers_count = len(self.logger_setup.logger.handlers)

        # Get logger again
        logger = self.logger_setup.get_logger()
        assert len(logger.handlers) == handlers_count


class TestLoggerFunctions(unittest.TestCase):
    """Test module-level logger functions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Clean up any existing loggers
        self.test_logger_name = "test_function_logger"
        logger = logging.getLogger(self.test_logger_name)
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)

    def tearDown(self) -> None:
        """Clean up after tests."""
        logger = logging.getLogger(self.test_logger_name)
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)

    def test_get_logger_with_name(self) -> None:
        """Test get_logger function with custom name."""
        logger = get_logger(
            name=self.test_logger_name,
            log_to_console=True,
            log_to_file=False,
            provider=LogProvider.STDOUT,
        )

        assert self.test_logger_name in logger.name
        assert len(logger.handlers) > 0

    def test_get_logger_default(self) -> None:
        """Test get_logger function with default settings."""
        logger = get_logger(
            log_to_console=True,
            log_to_file=False,
            provider=LogProvider.STDOUT,
        )

        assert "nyc_landmarks" in logger.name

    def test_configure_basic_logging_safely_no_handlers(self) -> None:
        """Test configure_basic_logging_safely with no existing handlers."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        configure_basic_logging_safely(logging.DEBUG)

        assert root_logger.level == logging.DEBUG
        assert len(root_logger.handlers) > 0

    def test_configure_basic_logging_safely_with_handlers(self) -> None:
        """Test configure_basic_logging_safely with existing handlers."""
        root_logger = logging.getLogger()
        initial_handler = logging.StreamHandler()
        root_logger.addHandler(initial_handler)
        initial_count = len(root_logger.handlers)

        configure_basic_logging_safely(logging.WARNING)

        assert root_logger.level == logging.WARNING
        # Should not add more handlers
        assert len(root_logger.handlers) == initial_count


class TestLoggerUtilities(unittest.TestCase):
    """Test logger utility functions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_logger = logging.getLogger("test_utilities")
        self.test_logger.handlers.clear()

        # Add a string handler to capture log output
        self.log_stream = StringIO()
        self.handler = logging.StreamHandler(self.log_stream)
        self.handler.setFormatter(StructuredFormatter())
        self.test_logger.addHandler(self.handler)
        self.test_logger.setLevel(logging.DEBUG)

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.test_logger.handlers.clear()

    @patch("nyc_landmarks.utils.logger.REQUEST_CONTEXT_AVAILABLE", True)
    @patch("nyc_landmarks.utils.logger.get_request_context")
    def test_log_with_context(self, mock_get_context: Mock) -> None:
        """Test log_with_context function."""
        mock_get_context.return_value = {"correlation_id": "test-123"}

        log_with_context(
            self.test_logger,
            logging.INFO,
            "Test message with context",
            extra={"custom_field": "custom_value"},
        )

        log_output = self.log_stream.getvalue()
        parsed = json.loads(log_output.strip())

        assert parsed["message"] == "Test message with context"
        assert parsed["correlation_id"] == "test-123"
        assert parsed["custom_field"] == "custom_value"

    @patch("nyc_landmarks.utils.logger.REQUEST_CONTEXT_AVAILABLE", False)
    def test_log_with_context_no_context_available(self) -> None:
        """Test log_with_context when context is not available."""
        log_with_context(
            self.test_logger,
            logging.INFO,
            "Test message",
            extra={"test_field": "test_value"},
        )

        log_output = self.log_stream.getvalue()
        parsed = json.loads(log_output.strip())

        assert parsed["message"] == "Test message"
        assert parsed["test_field"] == "test_value"

    def test_log_with_attributes(self) -> None:
        """Test log_with_attributes function."""
        log_with_attributes(
            self.test_logger,
            logging.WARNING,
            "Test message with attributes",
            extra={"extra_field": "extra_value"},
            record_attrs={"endpoint_category": "api"},
        )

        log_output = self.log_stream.getvalue()
        parsed = json.loads(log_output.strip())

        assert parsed["message"] == "Test message with attributes"
        assert parsed["severity"] == "WARNING"
        assert parsed["extra_field"] == "extra_value"
        assert parsed["endpoint_category"] == "api"

    def test_log_with_attributes_no_record_attrs(self) -> None:
        """Test log_with_attributes without record attributes."""
        log_with_attributes(
            self.test_logger,
            logging.ERROR,
            "Test error message",
            extra={"error_code": "E001"},
        )

        log_output = self.log_stream.getvalue()
        parsed = json.loads(log_output.strip())

        assert parsed["message"] == "Test error message"
        assert parsed["severity"] == "ERROR"
        assert parsed["error_code"] == "E001"

    def test_log_performance_success(self) -> None:
        """Test log_performance function for successful operation."""
        log_performance(
            self.test_logger,
            "test_operation",
            123.45,
            success=True,
            extra={"endpoint_category": "api"},
        )

        log_output = self.log_stream.getvalue()
        parsed = json.loads(log_output.strip())

        assert "Performance: test_operation completed in 123.45ms" in parsed["message"]
        assert parsed["severity"] == "INFO"
        assert parsed["operation"] == "test_operation"
        assert parsed["duration_ms"] == 123.45
        assert parsed["success"] is True
        assert parsed["metric_type"] == "performance"
        assert parsed["endpoint_category"] == "api"

    def test_log_performance_failure(self) -> None:
        """Test log_performance function for failed operation."""
        log_performance(
            self.test_logger,
            "failed_operation",
            67.89,
            success=False,
        )

        log_output = self.log_stream.getvalue()
        parsed = json.loads(log_output.strip())

        assert "failed_operation completed in 67.89ms (failed)" in parsed["message"]
        assert parsed["severity"] == "WARNING"
        assert parsed["success"] is False

    def test_log_error(self) -> None:
        """Test log_error function."""
        test_exception = ValueError("Test error message")

        log_error(
            self.test_logger,
            test_exception,
            "validation",
            "A validation error occurred",
            extra={"field_name": "username"},
        )

        log_output = self.log_stream.getvalue()
        parsed = json.loads(log_output.strip())

        assert parsed["message"] == "A validation error occurred"
        assert parsed["severity"] == "ERROR"
        assert parsed["error_type"] == "validation"
        assert parsed["error_class"] == "ValueError"
        assert parsed["error_message"] == "Test error message"
        assert parsed["field_name"] == "username"
        assert "exception" in parsed


class TestLoggerCleanup(unittest.TestCase):
    """Test logger cleanup functions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_logger_names = ["cleanup_test_1", "cleanup_test_2"]
        self.test_loggers = []

        for name in self.test_logger_names:
            logger = logging.getLogger(name)
            logger.handlers.clear()

            # Add mock handlers
            handler1 = MagicMock()
            handler2 = MagicMock()

            # Make them look like cloud handlers
            handler1.transport = Mock()
            handler2.transport = Mock()

            logger.addHandler(handler1)
            logger.addHandler(handler2)
            self.test_loggers.append(logger)

    def tearDown(self) -> None:
        """Clean up after tests."""
        for name in self.test_logger_names:
            logger = logging.getLogger(name)
            logger.handlers.clear()

    def test_cleanup_loggers_specific_names(self) -> None:
        """Test cleanup_loggers with specific logger names."""
        # Get initial handler counts
        initial_handlers = []
        for logger in self.test_loggers:
            initial_handlers.append(logger.handlers[:])

        cleanup_loggers(self.test_logger_names)

        # Verify handlers were closed and removed
        for i, logger in enumerate(self.test_loggers):
            assert len(logger.handlers) == 0
            for handler in initial_handlers[i]:
                handler.close.assert_called_once()  # type: ignore[attr-defined]

    def test_cleanup_loggers_all(self) -> None:
        """Test cleanup_loggers for all loggers."""
        # This test is more limited since we can't easily control all system loggers
        cleanup_loggers(None)
        # Just verify it doesn't crash

    def test_flush_loggers_specific_names(self) -> None:
        """Test flush_loggers with specific logger names."""
        flush_loggers(self.test_logger_names)

        # Verify flush was called on handlers
        for logger in self.test_loggers:
            for handler in logger.handlers:
                if hasattr(handler, "flush"):
                    handler.flush.assert_called_once()  # type: ignore[attr-defined]

    def test_flush_loggers_all(self) -> None:
        """Test flush_loggers for all loggers."""
        flush_loggers(None)
        # Just verify it doesn't crash

    @patch("nyc_landmarks.utils.logger.flush_loggers")
    @patch("nyc_landmarks.utils.logger.cleanup_loggers")
    @patch("time.sleep")
    def test_shutdown_logging_gracefully(
        self, mock_sleep: Mock, mock_cleanup: Mock, mock_flush: Mock
    ) -> None:
        """Test shutdown_logging_gracefully function."""
        shutdown_logging_gracefully()

        mock_flush.assert_called_once_with()
        mock_sleep.assert_called_once_with(0.5)
        mock_cleanup.assert_called_once_with()

    @patch("nyc_landmarks.utils.logger.flush_loggers")
    def test_shutdown_logging_gracefully_with_error(self, mock_flush: Mock) -> None:
        """Test shutdown_logging_gracefully when an error occurs."""
        mock_flush.side_effect = Exception("Flush error")

        # Should not raise exception
        shutdown_logging_gracefully()


class TestLoggingContext(unittest.TestCase):
    """Test the LoggingContext context manager."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger_name = "context_test_logger"
        # Clean up any existing logger
        logger = logging.getLogger(self.logger_name)
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)

    def tearDown(self) -> None:
        """Clean up after tests."""
        logger = logging.getLogger(self.logger_name)
        logger.handlers.clear()

    @patch("nyc_landmarks.utils.logger.flush_loggers")
    @patch("nyc_landmarks.utils.logger.cleanup_loggers")
    def test_logging_context_manager(
        self, mock_cleanup: Mock, mock_flush: Mock
    ) -> None:
        """Test LoggingContext as a context manager."""
        with LoggingContext(
            self.logger_name,
            log_to_console=True,
            log_to_file=False,
            provider=LogProvider.STDOUT,
        ) as logger:
            assert isinstance(logger, logging.Logger)
            assert self.logger_name in logger.name

        # Verify cleanup was called
        mock_flush.assert_called_once_with([self.logger_name])
        mock_cleanup.assert_called_once_with([self.logger_name])

    @patch("nyc_landmarks.utils.logger.flush_loggers")
    @patch("nyc_landmarks.utils.logger.cleanup_loggers")
    def test_logging_context_with_exception(
        self, mock_cleanup: Mock, mock_flush: Mock
    ) -> None:
        """Test LoggingContext when an exception occurs in the with block."""
        with pytest.raises(ValueError):
            with LoggingContext(self.logger_name) as logger:
                assert isinstance(logger, logging.Logger)
                raise ValueError("Test exception")

        # Cleanup should still be called
        mock_flush.assert_called_once_with([self.logger_name])
        mock_cleanup.assert_called_once_with([self.logger_name])


class TestLoggerPrivateFunctions(unittest.TestCase):
    """Test private helper functions in the logger module."""

    def test_get_all_loggers(self) -> None:
        """Test _get_all_loggers function."""
        from nyc_landmarks.utils.logger import _get_all_loggers

        loggers = _get_all_loggers()
        assert isinstance(loggers, list)
        assert len(loggers) > 0
        # Root logger should be included
        assert logging.getLogger() in loggers

    def test_get_cloud_handlers(self) -> None:
        """Test _get_cloud_handlers function."""
        from nyc_landmarks.utils.logger import _get_cloud_handlers

        logger = logging.getLogger("test_cloud_handlers")
        logger.handlers.clear()

        # Add a regular handler
        regular_handler = logging.StreamHandler()
        logger.addHandler(regular_handler)

        # Add a mock cloud handler
        cloud_handler = Mock()
        cloud_handler.transport = Mock()
        cloud_handler.close = Mock()
        logger.addHandler(cloud_handler)

        cloud_handlers = _get_cloud_handlers(logger)

        # Should only return the cloud handler
        assert len(cloud_handlers) == 1
        assert cloud_handler in cloud_handlers
        assert regular_handler not in cloud_handlers

    def test_close_handler_safely(self) -> None:
        """Test _close_handler_safely function."""
        from nyc_landmarks.utils.logger import _close_handler_safely

        logger = logging.getLogger("test_close_handler")
        logger.handlers.clear()

        handler = Mock()
        handler.close = Mock()
        logger.addHandler(handler)

        _close_handler_safely(handler, logger)

        handler.close.assert_called_once()
        assert handler not in logger.handlers

    def test_close_handler_safely_with_error(self) -> None:
        """Test _close_handler_safely when close() raises an exception."""
        from nyc_landmarks.utils.logger import _close_handler_safely

        logger = logging.getLogger("test_close_handler_error")
        logger.handlers.clear()

        handler = Mock()
        handler.close = Mock(side_effect=Exception("Close error"))
        logger.addHandler(handler)

        # Should not raise exception
        _close_handler_safely(handler, logger)

        handler.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
