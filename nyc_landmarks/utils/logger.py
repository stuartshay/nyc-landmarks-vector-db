"""
Centralized logging configuration for NYC Landmarks Vector DB.

This module provides a consistent logging setup across all scripts and modules
in the project, with capabilities for:
- Console output
- File logging with timestamped filenames
- Configurable log levels
- Structured logging with standardized fields
- Request context integration
- Performance monitoring
"""

import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from nyc_landmarks.config.settings import LogProvider, settings

# Try to import request context utilities - they may not be available in all environments
try:
    from nyc_landmarks.utils.request_context import get_request_context

    REQUEST_CONTEXT_AVAILABLE = True
except ImportError:
    REQUEST_CONTEXT_AVAILABLE = False

try:
    from google.cloud import logging as gcp_logging  # type: ignore
    from google.cloud.logging_v2.handlers import CloudLoggingHandler  # type: ignore

    GCP_LOGGING_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    GCP_LOGGING_AVAILABLE = False


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs JSON formatted logs."""

    def __init__(self, include_context: bool = True):
        """Initialize the formatter with context inclusion flag."""
        super().__init__()
        self.include_context = include_context

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "severity": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
            "environment": settings.ENV.value,
        }

        # Add request context if available
        if self.include_context and REQUEST_CONTEXT_AVAILABLE:
            try:
                context = get_request_context()
                if context:
                    log_data.update(context)
            except Exception:
                # Fail silently if context extraction fails
                pass  # nosec B110

        # Add extra fields from the record
        if hasattr(record, "exc_info") and record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else "",
                "message": str(record.exc_info[1]) if record.exc_info[1] else "",
                "traceback": (
                    traceback.format_exception(*record.exc_info)
                    if record.exc_info[2]
                    else []
                ),
            }

        # Add any additional fields set on the record
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in {
                    "args",
                    "asctime",
                    "created",
                    "exc_info",
                    "exc_text",
                    "filename",
                    "funcName",
                    "id",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "message",
                    "msg",
                    "name",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "stack_info",
                    "thread",
                    "threadName",
                }:
                    log_data[key] = value

        # Convert to JSON
        return json.dumps(log_data)


class LoggerSetup:
    """Centralized logging configuration for NYC Landmarks Vector DB."""

    def __init__(self, name: str = "nyc_landmarks") -> None:
        """Initialize the logger setup with default name."""
        self.name = name
        self.logger = logging.getLogger(name)
        self._configured = False

    def setup(
        self,
        log_level: int = logging.INFO,
        log_to_console: bool = True,
        log_to_file: bool = True,
        log_dir: Union[str, Path] = "logs",
        log_filename: Optional[str] = None,
        log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        provider: LogProvider = settings.LOG_PROVIDER,
        structured: bool = False,
    ) -> logging.Logger:
        """
        Configure and return a logger with the specified settings.

        Args:
            log_level: The logging level (default: logging.INFO)
            log_to_console: Whether to log to console (default: True)
            log_to_file: Whether to log to a file (default: True)
            log_dir: Directory to store log files (default: "logs")
            log_filename: Custom log filename (default: None, generates timestamped filename)
            log_format: Format string for log messages
            provider: Logging provider to use (default: settings.LOG_PROVIDER)

        Returns:
            Configured logger instance
        """
        # Only configure once
        if self._configured:
            return self.logger

        # Set log level
        self.logger.setLevel(log_level)

        # Create formatters
        standard_formatter = logging.Formatter(log_format)
        json_formatter = StructuredFormatter(include_context=True)

        # Use structured formatter if requested or when using Google Cloud Logging
        use_structured = structured or provider == LogProvider.GOOGLE
        formatter = json_formatter if use_structured else standard_formatter

        # Add console handler if requested
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # Add file handler if requested
        if log_to_file:
            # Ensure log directory exists
            log_dir_path = Path(log_dir)
            log_dir_path.mkdir(exist_ok=True)

            # Generate timestamped filename if not provided
            if not log_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_filename = f"{self.name}_{timestamp}.log"

            # Create file handler
            log_filepath = log_dir_path / log_filename
            file_handler = logging.FileHandler(log_filepath)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Add provider-specific handlers
        if provider == LogProvider.GOOGLE and GCP_LOGGING_AVAILABLE:
            try:
                client = gcp_logging.Client()
                # Create CloudLoggingHandler with a specific logger name for filtering
                logger_name = f"{settings.LOG_NAME_PREFIX}.{self.name}"

                # Create the Cloud Logging handler with environment labels
                cloud_handler = CloudLoggingHandler(
                    client, name=logger_name, labels={"environment": settings.ENV.value}
                )

                # Set a custom formatter for Cloud Logging to ensure environment is included
                cloud_handler.setFormatter(json_formatter)

                self.logger.addHandler(cloud_handler)
            except Exception as e:
                # Fallback to standard logging if Cloud Logging fails
                self.logger.exception(
                    "Failed to initialize Google Cloud Logging: %s", str(e)
                )

        self._configured = True
        return self.logger

    def get_logger(self) -> logging.Logger:
        """
        Get the configured logger instance.

        If the logger hasn't been configured yet, it will be configured with default settings.

        Returns:
            Configured logger instance
        """
        if not self._configured:
            return self.setup()
        return self.logger


# Singleton instance for easy import
default_logger = LoggerSetup()


def get_logger(
    name: Optional[str] = None,
    log_level: int = logging.INFO,
    log_to_console: bool = True,
    log_to_file: bool = True,
    provider: LogProvider = settings.LOG_PROVIDER,
    structured: bool = False,
) -> logging.Logger:
    """
    Convenience function to get a configured logger.

    Args:
        name: Logger name (default: None, uses the default logger)
        log_level: Logging level (default: logging.INFO)
        log_to_console: Whether to log to console (default: True)
        log_to_file: Whether to log to file (default: True)
        provider: Logging provider to use (default: settings.LOG_PROVIDER)
        structured: Whether to use structured (JSON) logging format (default: False)

    Returns:
        Configured logger instance
    """
    if name:
        logger_setup = LoggerSetup(name)
        return logger_setup.setup(
            log_level=log_level,
            log_to_console=log_to_console,
            log_to_file=log_to_file,
            provider=provider,
            structured=structured,
        )

    return default_logger.setup(
        log_level=log_level,
        log_to_console=log_to_console,
        log_to_file=log_to_file,
        provider=provider,
        structured=structured,
    )


# Helper functions for enhanced logging capabilities


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    *args: Any,
    exc_info: Optional[Exception] = None,
    extra: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> None:
    """
    Log a message with request context automatically included.

    Args:
        logger: Logger instance to use
        level: Logging level (e.g., logging.INFO)
        message: Message to log
        args: Arguments for message formatting
        exc_info: Exception information for error logs
        extra: Additional fields to include in the log entry
        kwargs: Additional keyword arguments passed to logger
    """
    log_extra = {}

    # Add request context if available
    if REQUEST_CONTEXT_AVAILABLE:
        try:
            context = get_request_context()
            if context:
                log_extra.update(context)
        except Exception:
            # Fail silently if context extraction fails
            pass  # nosec B110

    # Add any extra fields provided
    if extra:
        log_extra.update(extra)

    # Log with the combined extra fields
    logger.log(level, message, *args, exc_info=exc_info, extra=log_extra, **kwargs)


def log_performance(
    logger: logging.Logger,
    operation_name: str,
    duration_ms: float,
    success: bool = True,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a performance metric for an operation.

    Args:
        logger: Logger instance to use
        operation_name: Name of the operation being measured
        duration_ms: Duration in milliseconds
        success: Whether the operation succeeded
        extra: Additional fields to include in the log entry
    """
    log_extra = {
        "operation": operation_name,
        "duration_ms": duration_ms,
        "success": success,
        "metric_type": "performance",
    }

    if extra:
        log_extra.update(extra)

    level = logging.INFO if success else logging.WARNING
    message = f"Performance: {operation_name} completed in {duration_ms:.2f}ms"
    if not success:
        message += " (failed)"

    log_with_context(logger, level, message, extra=log_extra)


def log_error(
    logger: logging.Logger,
    error: Exception,
    error_type: str,
    message: str,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an error with standardized classification.

    Args:
        logger: Logger instance to use
        error: The exception that occurred
        error_type: Classification of the error (e.g., "validation", "db", "api")
        message: Descriptive error message
        extra: Additional fields to include in the log entry
    """
    log_extra = {
        "error_type": error_type,
        "error_class": error.__class__.__name__,
        "error_message": str(error),
    }

    if extra:
        log_extra.update(extra)

    log_with_context(logger, logging.ERROR, message, exc_info=error, extra=log_extra)
