"""
API middleware for NYC Landmarks Vector DB.

This module provides FastAPI middleware components for request tracking,
performance monitoring, and other cross-cutting concerns.
"""

import time

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from nyc_landmarks.utils.logger import get_logger, log_performance
from nyc_landmarks.utils.request_context import setup_request_tracking

# Configure logger
logger = get_logger(__name__)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor and log API endpoint performance."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request and measure performance."""
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

            extra_data = {
                "endpoint": endpoint,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "query_params": dict(request.query_params),
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

    # Add performance monitoring
    app.add_middleware(PerformanceMonitoringMiddleware)

    logger.info("API middleware configured successfully")
