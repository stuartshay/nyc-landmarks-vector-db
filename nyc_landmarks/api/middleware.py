"""
API middleware for NYC Landmarks Vector DB.

This module provides FastAPI middleware components for request tracking,
performance monitoring, and other cross-cutting concerns.
"""

import time
import uuid

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from nyc_landmarks.api.request_body_logging_middleware import (
    RequestBodyLoggingMiddleware,
)
from nyc_landmarks.utils.logger import get_logger, log_performance
from nyc_landmarks.utils.request_context import setup_request_tracking

# Configure logger
logger = get_logger(__name__)


def _get_correlation_id(request: Request) -> str:
    """
    Get or generate a correlation ID for request tracking.

    Uses the same logic as RequestBodyLoggingMiddleware for consistency.

    Args:
        request: FastAPI request object

    Returns:
        Correlation ID string
    """
    # Try to get from common request ID headers
    correlation_id = (
        request.headers.get("x-request-id")
        or request.headers.get("x-correlation-id")
        or request.headers.get("request-id")
        or request.headers.get("correlation-id")
    )

    # If no header found, generate a new UUID
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    return str(correlation_id)


def _categorize_endpoint(path: str) -> str:
    """
    Categorize an endpoint path for log routing.

    Args:
        path: The request path

    Returns:
        Endpoint category: 'query', 'chat', 'health', or 'other'
    """
    if path.startswith("/api/query"):
        return "query"
    elif path.startswith("/api/chat"):
        return "chat"
    elif path == "/health":
        return "health"
    else:
        return "other"


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor and log API endpoint performance."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request and measure performance."""
        # Get correlation ID for request tracking
        correlation_id = _get_correlation_id(request)

        # Record start time
        start_time = time.time()

        # Process the request
        try:
            response = await call_next(request)
            success = True
        except Exception as e:
            # Log the exception but don't handle it - let FastAPI's exception handlers do that
            logger.exception("Error processing request: %s", str(e))
            success = False
            raise
        finally:
            # Calculate duration in milliseconds
            duration_ms = (time.time() - start_time) * 1000

            # Log performance with structured data
            endpoint = f"{request.method} {request.url.path}"
            status_code = response.status_code if success else 500

            # Determine endpoint category for log routing
            endpoint_category = _categorize_endpoint(request.url.path)

            extra_data = {
                "endpoint": endpoint,
                "endpoint_category": endpoint_category,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "query_params": dict(request.query_params),
                "correlation_id": correlation_id,  # Add correlation ID for log correlation
            }

            log_performance(
                logger,
                endpoint,
                duration_ms,
                success=(status_code < 400),
                extra=extra_data,
            )

        return response


def setup_api_middleware(app: FastAPI) -> None:
    """Configure all middleware for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Set up request context tracking (must be first to initialize context)
    setup_request_tracking(app)

    # Add request body logging middleware
    app.add_middleware(RequestBodyLoggingMiddleware)

    # Add performance monitoring
    app.add_middleware(PerformanceMonitoringMiddleware)

    logger.info("API middleware configured successfully")
