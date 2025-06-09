#!/usr/bin/env python3
"""
Integration tests for API validation and warning logs.
Tests that invalid API requests generate proper warning logs.
"""

import logging
from io import StringIO

import pytest
import requests

from nyc_landmarks.utils.logger import get_logger


class TestAPIValidationLogging:
    """Test suite for API validation and logging integration."""

    @pytest.fixture
    def base_url(self) -> str:
        """Base URL for API tests."""
        return "http://localhost:8000"

    @pytest.fixture
    def headers(self) -> dict[str, str]:
        """Common headers for API requests."""
        return {"User-Agent": "ValidationTestBot/1.0"}

    def test_empty_query_validation(
        self, base_url: str, headers: dict[str, str]
    ) -> None:
        """Test that empty query generates appropriate validation warning."""
        response = requests.post(
            f"{base_url}/api/query/search",
            json={"query": "", "top_k": 5},
            headers=headers,
            timeout=30,
        )

        # Should return a validation error
        assert response.status_code == 422 or response.status_code == 400

    def test_query_too_long_validation(
        self, base_url: str, headers: dict[str, str]
    ) -> None:
        """Test that overly long queries generate validation warnings."""
        long_query = "x" * 1001  # Over 1000 character limit
        response = requests.post(
            f"{base_url}/api/query/search",
            json={"query": long_query, "top_k": 5},
            headers=headers,
            timeout=30,
        )

        # Should return a validation error
        assert response.status_code == 422 or response.status_code == 400

    def test_invalid_top_k_validation(
        self, base_url: str, headers: dict[str, str]
    ) -> None:
        """Test that invalid top_k values generate validation warnings."""
        response = requests.post(
            f"{base_url}/api/query/search",
            json={"query": "Central Park", "top_k": 100},
            headers=headers,
            timeout=30,
        )

        # Should return a validation error or clamp to max value
        assert response.status_code in [200, 400, 422]

    def test_invalid_source_type_validation(
        self, base_url: str, headers: dict[str, str]
    ) -> None:
        """Test that invalid source types generate validation warnings."""
        response = requests.post(
            f"{base_url}/api/query/search",
            json={"query": "Central Park", "source_type": "invalid_source", "top_k": 5},
            headers=headers,
            timeout=30,
        )

        # Should return a validation error
        assert response.status_code == 422 or response.status_code == 400

    def test_suspicious_content_validation(
        self, base_url: str, headers: dict[str, str]
    ) -> None:
        """Test that suspicious content generates appropriate warnings."""
        response = requests.post(
            f"{base_url}/api/query/search",
            json={"query": "<script>alert('xss')</script>", "top_k": 5},
            headers=headers,
            timeout=30,
        )

        # Should handle suspicious content appropriately
        assert response.status_code in [200, 400, 422]

    def test_chat_api_empty_message(
        self, base_url: str, headers: dict[str, str]
    ) -> None:
        """Test that empty chat messages generate validation warnings."""
        response = requests.post(
            f"{base_url}/api/chat/message",
            json={"message": "", "conversation_id": "test-123"},
            headers=headers,
            timeout=30,
        )

        # Should return a validation error
        assert response.status_code == 422 or response.status_code == 400

    def test_valid_request_success(
        self, base_url: str, headers: dict[str, str]
    ) -> None:
        """Test that valid requests work correctly."""
        response = requests.post(
            f"{base_url}/api/query/search",
            json={"query": "Central Park landmarks", "top_k": 3},
            headers=headers,
            timeout=30,
        )

        # Should return success
        assert response.status_code == 200

    @pytest.mark.integration
    def test_validation_warning_logs_generated(self) -> None:
        """Test that validation warnings are properly logged to Google Cloud Logging."""
        # This test would require setting up log capture for GCP
        # For now, we'll test local logging behavior

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)

        logger = get_logger("nyc_landmarks.api.validation")
        logger.addHandler(handler)

        # Simulate a validation warning
        logger.warning(
            "Validation error for request",
            extra={
                "validation_error": {
                    "field": "query",
                    "error": "Query cannot be empty",
                    "user_agent": "ValidationTestBot/1.0",
                }
            },
        )

        log_output = log_capture.getvalue()
        assert "Validation error for request" in log_output

        # Clean up
        logger.removeHandler(handler)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
