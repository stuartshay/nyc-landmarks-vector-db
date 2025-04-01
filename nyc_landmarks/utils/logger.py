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
            log_level=log_level, log_to_console=log_to_console, log_to_file=log_to_file
        )

    return default_logger.setup(
        log_level=log_level, log_to_console=log_to_console, log_to_file=log_to_file
    )
