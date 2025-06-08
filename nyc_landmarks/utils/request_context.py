"""
Request context utilities for NYC Landmarks API.

This module provides middleware and utilities for tracking request context
across the application, enabling correlated logging and performance monitoring.
"""

import time
import uuid
from contextvars import ContextVar
from typing import Any, Dict

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
request_path_var: ContextVar[str] = ContextVar("request_path", default="")
request_start_time_var: ContextVar[float] = ContextVar(
    "request_start_time", default=0.0
)
client_ip_var: ContextVar[str] = ContextVar("client_ip", default="")
user_agent_var: ContextVar[str] = ContextVar("user_agent", default="")


def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_var.get()


def get_request_path() -> str:
    """Get the current request path from context."""
    return request_path_var.get()


def get_request_duration() -> float:
    """Get the duration of the current request in milliseconds."""
    start_time = request_start_time_var.get()
    if start_time == 0:
        return 0.0
    return (time.time() - start_time) * 1000  # Convert to milliseconds


def get_client_ip() -> str:
    """Get the client IP from context."""
    return client_ip_var.get()


def get_user_agent() -> str:
    """Get the user agent from context."""
    return user_agent_var.get()


def get_request_context() -> Dict[str, Any]:
    """Get all request context as a dictionary for logging."""
    context: Dict[str, Any] = {
        "request_id": get_request_id(),
        "request_path": get_request_path(),
        "client_ip": get_client_ip(),
        "user_agent": get_user_agent(),
    }

    # Only include duration if request has started
    duration = get_request_duration()
    if duration > 0:
        context["duration_ms"] = duration

    return context


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to track request context across the application."""

    def __init__(self, app: ASGIApp):
        """Initialize the middleware."""
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request and set context variables."""
        # Generate a unique request ID if not provided in headers
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(request_id)

        # Store request path
        request_path_var.set(request.url.path)

        # Store start time for duration calculation
        request_start_time_var.set(time.time())

        # Store client info
        client_ip = request.client.host if request.client else ""
        client_ip_var.set(client_ip)

        user_agent = request.headers.get("user-agent", "")
        user_agent_var.set(user_agent)

        # Process the request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


def setup_request_tracking(app: FastAPI) -> None:
    """Configure request tracking middleware for a FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(RequestContextMiddleware)
