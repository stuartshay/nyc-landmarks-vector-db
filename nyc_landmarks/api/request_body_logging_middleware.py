"""
Request body logging middleware for NYC Landmarks Vector DB.

This module provides middleware for logging POST request bodies to help with
debugging and monitoring API usage patterns.

Development Configuration:
- Set DEVELOPMENT_MODE=false to enable production optimizations
- Set LOG_ALL_POST_REQUESTS=true to log ALL POST endpoints (development only)
- Body size limit is 10KB in development mode
- String truncation limit is 1KB in development mode
- Additional headers and timing info included in development mode

Production Configuration:
- DEVELOPMENT_MODE=false reduces logging overhead
- Only configured endpoints are logged
- Lower size and truncation limits
- Minimal header information
"""

import json
import os
import time
from typing import Any, Dict, Optional, Set

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from nyc_landmarks.utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)

# Development mode flag - can be set via environment variable
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "true").lower() == "true"

# Configure which endpoints should have their request bodies logged
REQUEST_BODY_LOGGING_ENDPOINTS: Set[str] = {
    "/api/query/search",
    "/api/query/search/landmark",
    "/api/chat/message",
}

# In development mode, optionally log ALL POST endpoints
LOG_ALL_POST_IN_DEV = os.getenv("LOG_ALL_POST_REQUESTS", "false").lower() == "true"

# Maximum size of request body to log (in bytes) to prevent excessive logging
# Increased for development - can be reduced for production
MAX_BODY_SIZE = 10240  # 10KB limit for development

# Fields to redact from logs for security
SENSITIVE_FIELDS: Set[str] = {
    "password",
    "token",
    "secret",
    "key",
    "authorization",
}


def _should_log_request_body(path: str, method: str) -> bool:
    """
    Determine if request body should be logged for this endpoint.

    Args:
        path: Request path
        method: HTTP method

    Returns:
        True if request body should be logged
    """
    if method != "POST":
        return False

    # In development mode with LOG_ALL_POST_IN_DEV=true, log all POST requests
    if DEVELOPMENT_MODE and LOG_ALL_POST_IN_DEV:
        return True

    # Otherwise, only log configured endpoints
    return path in REQUEST_BODY_LOGGING_ENDPOINTS


def _sanitize_request_body(body_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove or redact sensitive information from request body.

    Args:
        body_data: Request body as dictionary

    Returns:
        Sanitized request body
    """
    sanitized: Dict[str, Any] = {}

    for key, value in body_data.items():
        key_lower = key.lower()

        # Check if field should be redacted
        if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, str) and len(value) > 1000:
            # Truncate very long strings - increased limit for development
            sanitized[key] = value[:1000] + "...[TRUNCATED]"
        elif isinstance(value, dict):
            # Recursively sanitize nested dictionaries
            sanitized[key] = _sanitize_request_body(value)
        else:
            sanitized[key] = value

    return sanitized


def _get_client_info(request: Request) -> Dict[str, str]:
    """
    Extract client information from request.

    Args:
        request: FastAPI request object

    Returns:
        Dictionary with client info
    """
    client_info = {
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        "content_type": request.headers.get("content-type", "unknown"),
    }

    # In development mode, include additional headers for debugging
    if DEVELOPMENT_MODE:
        client_info.update(
            {
                "accept": request.headers.get("accept", "unknown"),
                "accept_encoding": request.headers.get("accept-encoding", "unknown"),
                "request_id": request.headers.get("x-request-id", "unknown"),
                "origin": request.headers.get("origin", "unknown"),
            }
        )

    return client_info


class RequestBodyLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log POST request bodies for debugging and monitoring."""

    async def dispatch(  # noqa: C901
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request and log body if applicable."""
        start_time = time.time() if DEVELOPMENT_MODE else None

        # Check if we should log the request body
        if not _should_log_request_body(request.url.path, request.method):
            # In development mode, log when we skip requests for debugging
            if DEVELOPMENT_MODE and request.method == "POST":
                logger.debug(
                    "Skipping request body logging for endpoint",
                    extra={
                        "endpoint": request.url.path,
                        "method": request.method,
                        "reason": "endpoint_not_configured",
                        "metric_type": "request_skipped",
                    },
                )
            return await call_next(request)

        # Read and log request body
        request_body: Optional[Dict[str, Any]] = None
        body_size = 0
        body_bytes = b""

        try:
            # Read the request body
            body_bytes = await request.body()
            body_size = len(body_bytes)

            # Only process if body is not too large
            if body_size > 0 and body_size <= MAX_BODY_SIZE:
                body_text = body_bytes.decode("utf-8")
                if body_text.strip():  # Only parse non-empty bodies
                    try:
                        request_body = json.loads(body_text)
                        # Sanitize the request body if it's a dictionary
                        if isinstance(request_body, dict):
                            sanitized_body = _sanitize_request_body(request_body)
                        else:
                            sanitized_body = request_body

                        # Get client information
                        client_info = _get_client_info(request)

                        # Log the request body with structured data
                        logger.info(
                            "POST request body logged",
                            extra={
                                "endpoint": request.url.path,
                                "endpoint_category": (
                                    "query"
                                    if "/api/query" in request.url.path
                                    else "chat"
                                ),
                                "method": request.method,
                                "path": request.url.path,
                                "request_body": sanitized_body,
                                "body_size_bytes": body_size,
                                "metric_type": "request_body",
                                **client_info,
                            },
                        )
                    except json.JSONDecodeError:
                        # Log that we couldn't parse the JSON
                        logger.warning(
                            "Failed to parse request body as JSON",
                            extra={
                                "endpoint": request.url.path,
                                "method": request.method,
                                "body_size_bytes": body_size,
                                "content_type": request.headers.get(
                                    "content-type", "unknown"
                                ),
                                **_get_client_info(request),
                            },
                        )
            elif body_size > MAX_BODY_SIZE:
                # Log that body was too large
                logger.info(
                    "Request body too large to log",
                    extra={
                        "endpoint": request.url.path,
                        "method": request.method,
                        "body_size_bytes": body_size,
                        "max_size_bytes": MAX_BODY_SIZE,
                        **_get_client_info(request),
                    },
                )
        except Exception as e:
            # Log any errors in body processing
            logger.error(
                f"Error processing request body for logging: {e}",
                extra={
                    "endpoint": request.url.path,
                    "method": request.method,
                    **_get_client_info(request),
                },
            )

        # Continue with normal request processing
        # Note: We need to reconstruct the request with the body since we consumed it
        try:
            # Store the original receive callable before modification
            original_receive = request.receive

            # Create a new receive callable that returns the body we read
            async def receive() -> Dict[str, Any]:
                return {
                    "type": "http.request",
                    "body": body_bytes,
                    "more_body": False,
                }

            # Temporarily replace the receive callable
            # While this modifies a private attribute, it's the standard pattern
            # for Starlette middleware that needs to consume and restore request bodies
            request._receive = receive  # type: ignore

            # Process the request normally
            response = await call_next(request)

            # Restore original receive callable after processing
            request._receive = original_receive  # type: ignore

        except Exception as e:
            logger.error(f"Error reconstructing request body: {e}")
            # If reconstruction fails, try to restore original and continue
            try:
                request._receive = original_receive  # type: ignore
            except Exception:
                pass  # nosec B110 # Ignore errors restoring original receive

            # Process with potentially broken request (may cause downstream issues)
            response = await call_next(request)

        # Log timing information in development mode
        if DEVELOPMENT_MODE and start_time is not None:
            processing_time = (
                time.time() - start_time
            ) * 1000  # Convert to milliseconds
            logger.debug(
                "Request processing completed",
                extra={
                    "endpoint": request.url.path,
                    "method": request.method,
                    "processing_time_ms": round(processing_time, 2),
                    "status_code": response.status_code,
                    "metric_type": "request_timing",
                },
            )

        return response
