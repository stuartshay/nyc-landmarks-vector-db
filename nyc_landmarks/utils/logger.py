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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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

    class EnhancedCloudLoggingHandler(
        CloudLoggingHandler
    ):  # pyright: ignore [reportRedeclaration]
        """
        Custom CloudLoggingHandler that can set labels dynamically based on log record content.
        """

        def emit(self, record: logging.LogRecord) -> None:
            """
            Emit a log record with dynamic labels.

            This method checks for an 'endpoint_category' field in the log record's extra data
            and adds it as a label to improve log sink filtering efficiency.
            """
            # Check if the record has endpoint_category information
            if hasattr(record, "endpoint_category"):
                # Create a copy of the base labels and add the endpoint category
                dynamic_labels = dict(self.labels) if self.labels else {}  # type: ignore
                dynamic_labels["endpoint_category"] = getattr(
                    record, "endpoint_category"
                )

                # Temporarily update labels for this record
                original_labels = self.labels  # type: ignore
                self.labels = dynamic_labels  # type: ignore

                try:
                    super().emit(record)
                finally:
                    # Restore original labels
                    self.labels = original_labels  # type: ignore
            else:
                # No dynamic labels needed, use standard behavior
                super().emit(record)

except Exception:  # pragma: no cover - optional dependency
    GCP_LOGGING_AVAILABLE = False

    # Create a dummy class to avoid import errors when GCP logging is not available
    class EnhancedCloudLoggingHandler(logging.Handler):  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__()

        def emit(self, record: logging.LogRecord) -> None:
            pass


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs JSON formatted logs."""

    def __init__(self, include_context: bool = True):
        """Initialize the formatter with context inclusion flag."""
        super().__init__()
        self.include_context = include_context

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
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

                # Create the enhanced Cloud Logging handler with environment labels
                cloud_handler = EnhancedCloudLoggingHandler(
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


def log_with_attributes(
    logger: logging.Logger,
    level: int,
    message: str,
    extra: Optional[Dict[str, Any]] = None,
    record_attrs: Optional[Dict[str, Any]] = None,
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Log a message with additional attributes set on the log record.

    Args:
        logger: Logger instance to use
        level: Logging level (e.g., logging.INFO)
        message: Message to log
        extra: Additional fields to include in the log entry
        record_attrs: Attributes to set directly on the log record (for custom handlers)
        *args: Arguments for message formatting
        **kwargs: Additional keyword arguments passed to logger
    """
    log_extra = {}

    # Add request context if available
    if REQUEST_CONTEXT_AVAILABLE:
        try:
            context = get_request_context()
            if context:
                log_extra.update(context)
        except Exception:
            pass  # nosec B110

    # Add any extra fields provided
    if extra:
        log_extra.update(extra)

    # Create a custom log record and set additional attributes
    if record_attrs:
        # Make the log call to get the record
        record = logger.makeRecord(
            logger.name,
            level,
            "",
            0,
            message,
            args,
            None,
            func=kwargs.get("func"),
            extra=log_extra,
        )

        # Set additional attributes on the record
        for attr_name, attr_value in record_attrs.items():
            setattr(record, attr_name, attr_value)

        # Handle the record
        logger.handle(record)
    else:
        # Standard logging
        logger.log(level, message, *args, extra=log_extra, **kwargs)


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

    # Extract endpoint_category from extra data to set as record attribute for efficient label filtering
    record_attrs = {}
    if extra and "endpoint_category" in extra:
        record_attrs["endpoint_category"] = extra["endpoint_category"]

    log_with_attributes(
        logger, level, message, extra=log_extra, record_attrs=record_attrs
    )


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


def _get_all_loggers() -> List[logging.Logger]:
    """Get all logger instances, filtering out PlaceHolder objects."""
    loggers = [logging.getLogger()]
    # Filter out PlaceHolder objects and only include actual Logger instances
    for logger_obj in logging.Logger.manager.loggerDict.values():
        if isinstance(logger_obj, logging.Logger):
            loggers.append(logger_obj)
    return loggers


def _get_cloud_handlers(logger_obj: logging.Logger) -> List[logging.Handler]:
    """Get CloudLoggingHandler instances from a logger."""
    handlers = []
    # Copy list to avoid modification during iteration
    for handler in logger_obj.handlers[:]:
        # Check if it's a CloudLoggingHandler
        if hasattr(handler, "transport") and hasattr(handler, "close"):
            handlers.append(handler)
    return handlers


def _close_handler_safely(handler: logging.Handler, logger_obj: logging.Logger) -> None:
    """Safely close a handler and remove it from the logger."""
    try:
        handler.close()
        logger_obj.removeHandler(handler)
    except Exception as e:
        # Use basic print since logging might be compromised
        print(f"Warning: Failed to close logging handler: {e}")


def cleanup_loggers(logger_names: Optional[List[str]] = None) -> None:
    """
    Clean up logging handlers to prevent shutdown warnings.

    This function should be called before script exit to properly close
    CloudLoggingHandler instances and avoid the threading shutdown warning.

    Args:
        logger_names: List of logger names to clean up. If None, cleans up all loggers.
    """
    if logger_names is None:
        loggers_to_clean = _get_all_loggers()
    else:
        loggers_to_clean = [logging.getLogger(name) for name in logger_names]

    for logger_obj in loggers_to_clean:
        if not isinstance(logger_obj, logging.Logger):
            continue

        handlers_to_close = _get_cloud_handlers(logger_obj)
        for handler in handlers_to_close:
            _close_handler_safely(handler, logger_obj)


def flush_loggers(logger_names: Optional[List[str]] = None) -> None:
    """
    Flush all logging handlers to ensure logs are sent.

    Args:
        logger_names: List of logger names to flush. If None, flushes all loggers.
    """
    if logger_names is None:
        # Get all loggers
        loggers_to_flush = [logging.getLogger()]
        # Filter out PlaceHolder objects and only include actual Logger instances
        for logger_obj in logging.Logger.manager.loggerDict.values():
            if isinstance(logger_obj, logging.Logger):
                loggers_to_flush.append(logger_obj)
    else:
        loggers_to_flush = [logging.getLogger(name) for name in logger_names]

    for logger_obj in loggers_to_flush:
        if not isinstance(logger_obj, logging.Logger):
            continue

        for handler in logger_obj.handlers:
            try:
                if hasattr(handler, "flush"):
                    handler.flush()
            except Exception as e:
                # Use basic print since logging might be compromised
                print(f"Warning: Failed to flush logging handler: {e}")


def shutdown_logging_gracefully() -> None:
    """
    Gracefully shutdown logging to prevent threading warnings.

    This function should be called at the end of scripts that use CloudLoggingHandler
    to ensure all logs are flushed and handlers are properly closed.
    """
    try:
        # First flush all logs
        flush_loggers()

        # Wait a moment for logs to be sent
        import time

        time.sleep(0.5)

        # Then cleanup handlers
        cleanup_loggers()

    except Exception as e:
        print(f"Warning: Error during logging shutdown: {e}")


# Context manager for proper logging cleanup
class LoggingContext:
    """Context manager that ensures proper logging cleanup."""

    def __init__(self, logger_name: str, **logger_kwargs: Any):
        """
        Initialize the logging context.

        Args:
            logger_name: Name for the logger
            **logger_kwargs: Additional arguments passed to get_logger()
        """
        self.logger_name = logger_name
        self.logger_kwargs = logger_kwargs
        self.logger: Optional[logging.Logger] = None

    def __enter__(self) -> logging.Logger:
        """Enter the context and set up logging."""
        self.logger = get_logger(name=self.logger_name, **self.logger_kwargs)
        return self.logger

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context and clean up logging."""
        if self.logger:
            flush_loggers([self.logger_name])
            cleanup_loggers([self.logger_name])
