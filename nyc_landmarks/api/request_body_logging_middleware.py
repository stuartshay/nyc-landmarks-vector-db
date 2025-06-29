"""
Request body logging middleware for NYC Landmarks Vector DB.

This module provides middleware for logging POST request bodies to help with
debugging and monitoring API usage patterns.
"""

import json
from typing import Any, Dict, Optional, Set

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from nyc_landmarks.utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)

# Configure which endpoints should have their request bodies logged
REQUEST_BODY_LOGGING_ENDPOINTS: Set[str] = {
    "/api/query/search",
    "/api/query/search/landmark",
    "/api/chat/message",
}

# Maximum size of request body to log (in bytes) to prevent excessive logging
MAX_BODY_SIZE = 2048  # 2KB limit

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
    return method == "POST" and path in REQUEST_BODY_LOGGING_ENDPOINTS


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
        elif isinstance(value, str) and len(value) > 500:
            # Truncate very long strings
            sanitized[key] = value[:500] + "...[TRUNCATED]"
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
    return {
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        "content_type": request.headers.get("content-type", "unknown"),
    }


class RequestBodyLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log POST request bodies for debugging and monitoring."""

    async def dispatch(  # noqa: C901
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request and log body if applicable."""
        # Check if we should log the request body
        if not _should_log_request_body(request.url.path, request.method):
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
        # Note: We need to create a new request object with the body since we consumed it
        try:
            # Create a new receive callable that returns the body we read
            async def receive() -> Dict[str, Any]:
                return {
                    "type": "http.request",
                    "body": body_bytes,
                    "more_body": False,
                }

            # Replace the receive callable to restore the body for downstream processing
            original_receive = request.receive
            request._receive = receive  # type: ignore

        except Exception as e:
            logger.error(f"Error reconstructing request body: {e}")

        # Process the request normally
        response = await call_next(request)

        # Restore original receive if needed (though request should be done by now)
        try:
            request._receive = original_receive  # type: ignore
        except Exception:
            pass  # nosec B110 # Ignore errors restoring original receive

        return response
