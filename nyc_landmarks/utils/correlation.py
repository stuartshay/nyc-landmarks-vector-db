"""
Correlation ID utilities for NYC Landmarks API.

This module provides utilities for extracting, generating, and managing
correlation IDs across middleware and API components, enabling end-to-end
request tracking and log correlation.
"""

import uuid
from typing import Optional

from fastapi import Request


def get_correlation_id(request: Request) -> str:
    """
    Get or generate a correlation ID for request tracking.

    Attempts to extract correlation ID from request headers using a priority
    order. If no correlation ID is found in headers, generates a new UUID.

    Supported headers (in priority order):
    1. X-Request-ID (highest priority)
    2. X-Correlation-ID
    3. Request-ID
    4. Correlation-ID (lowest priority)

    Args:
        request: FastAPI request object

    Returns:
        Correlation ID string - either from headers or newly generated UUID

    Example:
        >>> # With header
        >>> request_with_header = Request(headers={"X-Request-ID": "abc-123"})
        >>> correlation_id = get_correlation_id(request_with_header)
        >>> # correlation_id == "abc-123"

        >>> # Without header (generates UUID)
        >>> request_without_header = Request(headers={})
        >>> correlation_id = get_correlation_id(request_without_header)
        >>> # correlation_id == "550e8400-e29b-41d4-a716-446655440000" (example)
    """
    # Try to get from common request ID headers in priority order
    correlation_id = (
        request.headers.get("x-request-id")
        or request.headers.get("x-correlation-id")
        or request.headers.get("request-id")
        or request.headers.get("correlation-id")
    )

    # If no header found, generate a new UUID
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    return str(correlation_id)  # Ensure we always return a string


def extract_correlation_id_from_headers(headers: dict) -> Optional[str]:
    """
    Extract correlation ID from a dictionary of headers.

    This is a lower-level utility for cases where you have headers
    as a dictionary rather than a FastAPI Request object.

    Args:
        headers: Dictionary of HTTP headers (case-insensitive)

    Returns:
        Correlation ID string if found, None otherwise

    Example:
        >>> headers = {"X-Request-ID": "session-123", "Content-Type": "application/json"}
        >>> correlation_id = extract_correlation_id_from_headers(headers)
        >>> # correlation_id == "session-123"
    """
    # Convert headers to lowercase for case-insensitive matching
    lower_headers = {k.lower(): v for k, v in headers.items()}

    # Check headers in priority order
    for header_name in [
        "x-request-id",
        "x-correlation-id",
        "request-id",
        "correlation-id",
    ]:
        if header_name in lower_headers:
            return str(lower_headers[header_name])

    return None


def generate_correlation_id() -> str:
    """
    Generate a new correlation ID using UUID4.

    Returns:
        New UUID4 string suitable for correlation tracking

    Example:
        >>> correlation_id = generate_correlation_id()
        >>> # correlation_id == "550e8400-e29b-41d4-a716-446655440000" (example)
    """
    return str(uuid.uuid4())


def is_valid_correlation_id(correlation_id: Optional[str]) -> bool:
    """
    Validate if a string is a properly formatted correlation ID.

    Currently accepts any non-empty string, but can be extended
    to enforce specific formats (UUID, custom patterns, etc.).

    Args:
        correlation_id: String to validate

    Returns:
        True if valid correlation ID, False otherwise

    Example:
        >>> is_valid_correlation_id("abc-123")
        True
        >>> is_valid_correlation_id("")
        False
        >>> is_valid_correlation_id("   ")
        False
    """
    return bool(correlation_id and correlation_id.strip())


def get_correlation_id_with_fallback(
    request: Request, fallback_id: Optional[str] = None
) -> str:
    """
    Get correlation ID with an optional custom fallback.

    If no correlation ID is found in request headers and a fallback
    is provided, uses the fallback. Otherwise generates a new UUID.

    Args:
        request: FastAPI request object
        fallback_id: Optional fallback correlation ID to use

    Returns:
        Correlation ID string

    Example:
        >>> # With fallback
        >>> correlation_id = get_correlation_id_with_fallback(
        ...     request, fallback_id="custom-session-id"
        ... )

        >>> # Without fallback (same as get_correlation_id)
        >>> correlation_id = get_correlation_id_with_fallback(request)
    """
    # Try to get from headers first
    correlation_id = extract_correlation_id_from_headers(dict(request.headers))

    if correlation_id:
        return correlation_id

    # Use fallback if provided and valid
    if fallback_id and is_valid_correlation_id(fallback_id):
        return fallback_id

    # Generate new UUID as last resort
    return generate_correlation_id()


# Convenience constants for header names
CORRELATION_HEADER_NAMES = [
    "X-Request-ID",
    "X-Correlation-ID",
    "Request-ID",
    "Correlation-ID",
]

PRIORITY_CORRELATION_HEADER = "X-Request-ID"
