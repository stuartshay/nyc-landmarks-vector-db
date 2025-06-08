"""
Centralized logging configuration for NYC Landmarks Vector DB.

This module provides a consistent logging setup across all scripts and modules
in the project, with capabilities for:
- Console output
- File logging with timestamped filenames
- Configurable log levels
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from nyc_landmarks.config.settings import LogProvider, settings

try:
    from google.cloud import logging as gcp_logging  # type: ignore
    from google.cloud.logging_v2.handlers import CloudLoggingHandler  # type: ignore

    GCP_LOGGING_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    GCP_LOGGING_AVAILABLE = False


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

        # Create formatter
        formatter = logging.Formatter(log_format)

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
                cloud_handler = CloudLoggingHandler(client, name=logger_name)
                cloud_handler.setFormatter(formatter)
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
) -> logging.Logger:
    """
    Convenience function to get a configured logger.

    Args:
        name: Logger name (default: None, uses the default logger)
        log_level: Logging level (default: logging.INFO)
        log_to_console: Whether to log to console (default: True)
        log_to_file: Whether to log to file (default: True)

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
        )

    return default_logger.setup(
        log_level=log_level,
        log_to_console=log_to_console,
        log_to_file=log_to_file,
        provider=provider,
    )
