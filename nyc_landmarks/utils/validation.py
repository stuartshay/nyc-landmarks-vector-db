"""
Input validation utilities for NYC Landmarks API.

This module provides comprehensive validation for API requests
with logging of invalid inputs as warnings.
"""

import re
from typing import Any, Dict, Optional

from fastapi import HTTPException

from nyc_landmarks.utils.logger import get_logger

logger = get_logger(__name__)


class ValidationLogger:
    """Utility class for validating API inputs and logging validation errors."""

    @staticmethod
    def validate_text_query(
        query: str,
        endpoint: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Validate text query input and log warnings for invalid queries.

        Args:
            query: The search query text
            endpoint: The API endpoint being called
            client_ip: Client IP address (optional)
            user_agent: Client user agent (optional)

        Raises:
            HTTPException: If validation fails
        """
        context = {
            "endpoint": endpoint,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "query_length": len(query) if query else 0,
        }

        # Check if query is empty or None
        if not query or not query.strip():
            logger.warning(
                "Invalid API request: Empty query string provided",
                extra={"validation_error": "empty_query", **context},
            )
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Check query length
        if len(query) > 1000:
            logger.warning(
                "Invalid API request: Query too long (%d characters)",
                len(query),
                extra={"validation_error": "query_too_long", **context},
            )
            raise HTTPException(
                status_code=400, detail="Query must be 1000 characters or less"
            )

        # Check for suspicious patterns (potential injection attempts)
        suspicious_patterns = [
            r'<script.*?>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'on\w+\s*=',  # Event handlers
            r'data:text/html',  # Data URLs
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(
                    "Invalid API request: Suspicious content detected in query",
                    extra={
                        "validation_error": "suspicious_content",
                        "pattern_matched": pattern,
                        "query_excerpt": (
                            query[:100] + "..." if len(query) > 100 else query
                        ),
                        **context,
                    },
                )
                raise HTTPException(
                    status_code=400, detail="Invalid characters detected in query"
                )

    @staticmethod
    def validate_landmark_id(
        landmark_id: Optional[str],
        endpoint: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Validate landmark ID format and log warnings for invalid IDs.

        Args:
            landmark_id: The landmark ID to validate
            endpoint: The API endpoint being called
            client_ip: Client IP address (optional)
            user_agent: Client user agent (optional)

        Raises:
            HTTPException: If validation fails
        """
        if landmark_id is None:
            return

        context = {
            "endpoint": endpoint,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "landmark_id": landmark_id,
        }

        # Check format - should be alphanumeric with optional hyphens/underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', landmark_id):
            logger.warning(
                "Invalid API request: Invalid landmark ID format",
                extra={"validation_error": "invalid_landmark_id_format", **context},
            )
            raise HTTPException(
                status_code=400,
                detail="Landmark ID must contain only letters, numbers, hyphens, and underscores",
            )

        # Check length
        if len(landmark_id) > 100:
            logger.warning(
                "Invalid API request: Landmark ID too long",
                extra={"validation_error": "landmark_id_too_long", **context},
            )
            raise HTTPException(
                status_code=400, detail="Landmark ID must be 100 characters or less"
            )

    @staticmethod
    def validate_top_k(
        top_k: int,
        endpoint: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Validate top_k parameter and log warnings for invalid values.

        Args:
            top_k: The number of results to return
            endpoint: The API endpoint being called
            client_ip: Client IP address (optional)
            user_agent: Client user agent (optional)

        Raises:
            HTTPException: If validation fails
        """
        context = {
            "endpoint": endpoint,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "top_k": top_k,
        }

        if top_k < 1:
            logger.warning(
                "Invalid API request: top_k must be positive",
                extra={"validation_error": "invalid_top_k_negative", **context},
            )
            raise HTTPException(status_code=400, detail="top_k must be at least 1")

        if top_k > 50:
            logger.warning(
                "Invalid API request: top_k too large (%d)",
                top_k,
                extra={"validation_error": "top_k_too_large", **context},
            )
            raise HTTPException(status_code=400, detail="top_k must be 50 or less")

    @staticmethod
    def validate_source_type(
        source_type: Optional[str],
        endpoint: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Validate source_type parameter and log warnings for invalid values.

        Args:
            source_type: The source type filter
            endpoint: The API endpoint being called
            client_ip: Client IP address (optional)
            user_agent: Client user agent (optional)

        Raises:
            HTTPException: If validation fails
        """
        if source_type is None:
            return

        valid_source_types = {"wikipedia", "pdf"}
        context = {
            "endpoint": endpoint,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "source_type": source_type,
        }

        if source_type.lower() not in valid_source_types:
            logger.warning(
                "Invalid API request: Invalid source_type '%s'",
                source_type,
                extra={
                    "validation_error": "invalid_source_type",
                    "valid_options": list(valid_source_types),
                    **context,
                },
            )
            raise HTTPException(
                status_code=400,
                detail=f"source_type must be one of: {', '.join(valid_source_types)}",
            )

    @staticmethod
    def validate_session_id(
        session_id: Optional[str],
        endpoint: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Validate session ID format and log warnings for invalid IDs.

        Args:
            session_id: The session ID to validate
            endpoint: The API endpoint being called
            client_ip: Client IP address (optional)
            user_agent: Client user agent (optional)

        Raises:
            HTTPException: If validation fails
        """
        if session_id is None:
            return

        context = {
            "endpoint": endpoint,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "session_id": session_id,
        }

        # Check format - should be alphanumeric with optional hyphens/underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
            logger.warning(
                "Invalid API request: Invalid session ID format",
                extra={"validation_error": "invalid_session_id_format", **context},
            )
            raise HTTPException(
                status_code=400,
                detail="Session ID must contain only letters, numbers, hyphens, and underscores",
            )

        # Check length
        if len(session_id) > 200:
            logger.warning(
                "Invalid API request: Session ID too long",
                extra={"validation_error": "session_id_too_long", **context},
            )
            raise HTTPException(
                status_code=400, detail="Session ID must be 200 characters or less"
            )

    @staticmethod
    def log_validation_success(
        endpoint: str,
        request_data: Dict[str, Any],
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Log successful validation for monitoring purposes.

        Args:
            endpoint: The API endpoint being called
            request_data: The validated request data
            client_ip: Client IP address (optional)
            user_agent: Client user agent (optional)
        """
        logger.info(
            "Valid API request processed",
            extra={
                "endpoint": endpoint,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "request_data": request_data,
                "validation_status": "success",
            },
        )


def get_client_info(request: Any) -> tuple[Optional[str], Optional[str]]:
    """
    Extract client IP and user agent from FastAPI request.

    Args:
        request: FastAPI request object

    Returns:
        Tuple of (client_ip, user_agent)
    """
    try:
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        return client_ip, user_agent
    except Exception:
        return None, None
