"""
Custom exceptions for the NYC Landmarks Vector Database project.

This module contains custom exception classes used throughout the project
for better error handling and more specific error reporting.
"""

from typing import Optional


class WikipediaAPIError(Exception):
    """
    Custom exception for Wikipedia API-related errors.

    This exception is raised when there are issues accessing the Wikipedia API,
    such as connection problems, API unreachability, or other Wikipedia-specific errors.

    Attributes:
        message: Human-readable error message
        original_error: The original exception that caused this error (if any)
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """
        Initialize the WikipediaAPIError.

        Args:
            message: A descriptive error message
            original_error: The original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.original_error = original_error

        # Chain the exception if there's an original error
        if original_error:
            self.__cause__ = original_error

    def __str__(self) -> str:
        """Return a string representation of the error."""
        if self.original_error:
            return f"{self.message} (Original error: {self.original_error})"
        return self.message

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        if self.original_error:
            return f"WikipediaAPIError('{self.message}', original_error={repr(self.original_error)})"
        return f"WikipediaAPIError('{self.message}')"
