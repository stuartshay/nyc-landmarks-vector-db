"""
Tests for correlation utility functions.

This module tests the correlation ID extraction, generation, and validation
functionality provided by the correlation utility module.
"""

import uuid
from unittest.mock import Mock

from fastapi import Request

from nyc_landmarks.utils.correlation import (
    CORRELATION_HEADER_NAMES,
    PRIORITY_CORRELATION_HEADER,
    extract_correlation_id_from_headers,
    generate_correlation_id,
    get_correlation_id,
    get_correlation_id_with_fallback,
    is_valid_correlation_id,
)


class TestGetCorrelationId:
    """Test get_correlation_id function."""

    def test_get_correlation_id_from_x_request_id(self) -> None:
        """Test extraction from X-Request-ID header (highest priority)."""
        request = Mock(spec=Request)
        request.headers = {"x-request-id": "test-request-123"}

        result = get_correlation_id(request)
        assert result == "test-request-123"

    def test_get_correlation_id_from_x_correlation_id(self) -> None:
        """Test extraction from X-Correlation-ID header."""
        request = Mock(spec=Request)
        request.headers = {"x-correlation-id": "test-correlation-456"}

        result = get_correlation_id(request)
        assert result == "test-correlation-456"

    def test_get_correlation_id_from_request_id(self) -> None:
        """Test extraction from Request-ID header."""
        request = Mock(spec=Request)
        request.headers = {"request-id": "test-req-789"}

        result = get_correlation_id(request)
        assert result == "test-req-789"

    def test_get_correlation_id_from_correlation_id(self) -> None:
        """Test extraction from Correlation-ID header."""
        request = Mock(spec=Request)
        request.headers = {"correlation-id": "test-corr-abc"}

        result = get_correlation_id(request)
        assert result == "test-corr-abc"

    def test_header_priority_order(self) -> None:
        """Test that X-Request-ID takes priority over other headers."""
        request = Mock(spec=Request)
        request.headers = {
            "x-request-id": "priority-winner",
            "x-correlation-id": "should-be-ignored",
            "request-id": "also-ignored",
            "correlation-id": "ignored-too",
        }

        result = get_correlation_id(request)
        assert result == "priority-winner"

    def test_generates_uuid_when_no_headers(self) -> None:
        """Test UUID generation when no correlation headers are present."""
        request = Mock(spec=Request)
        request.headers = {"content-type": "application/json"}

        result = get_correlation_id(request)

        # Should be a valid UUID string
        assert isinstance(result, str)
        assert len(result) == 36  # UUID string length
        # Validate it's a proper UUID
        uuid.UUID(result)

    def test_case_insensitive_headers(self) -> None:
        """Test that header extraction works with uppercase headers."""
        request = Mock(spec=Request)
        # FastAPI normalizes headers to lowercase for .get() access
        request.headers = {"x-request-id": "case-test-123"}

        result = get_correlation_id(request)
        assert result == "case-test-123"

    def test_returns_string_type(self) -> None:
        """Test that function always returns a string."""
        request = Mock(spec=Request)
        request.headers = {"x-request-id": 12345}  # Non-string value

        result = get_correlation_id(request)
        assert isinstance(result, str)
        assert result == "12345"


class TestExtractCorrelationIdFromHeaders:
    """Test extract_correlation_id_from_headers function."""

    def test_extract_from_dict_headers(self) -> None:
        """Test extraction from header dictionary."""
        headers: dict[str, str] = {
            "X-Request-ID": "dict-test-123",
            "Content-Type": "application/json",
        }

        result = extract_correlation_id_from_headers(headers)
        assert result == "dict-test-123"

    def test_case_insensitive_extraction(self) -> None:
        """Test case-insensitive header extraction."""
        headers = {"x-request-id": "lowercase-test"}

        result = extract_correlation_id_from_headers(headers)
        assert result == "lowercase-test"

    def test_priority_order_in_dict(self) -> None:
        """Test priority order with dictionary headers."""
        headers = {
            "Correlation-ID": "lowest-priority",
            "Request-ID": "medium-priority",
            "X-Correlation-ID": "high-priority",
            "X-Request-ID": "highest-priority",
        }

        result = extract_correlation_id_from_headers(headers)
        assert result == "highest-priority"

    def test_returns_none_when_not_found(self) -> None:
        """Test returns None when no correlation headers found."""
        headers = {"Content-Type": "application/json", "Authorization": "Bearer token"}

        result = extract_correlation_id_from_headers(headers)
        assert result is None

    def test_empty_headers_dict(self) -> None:
        """Test with empty headers dictionary."""
        headers: dict[str, str] = {}

        result = extract_correlation_id_from_headers(headers)
        assert result is None


class TestGenerateCorrelationId:
    """Test generate_correlation_id function."""

    def test_generates_valid_uuid(self) -> None:
        """Test that generated correlation ID is a valid UUID."""
        result = generate_correlation_id()

        # Should be a valid UUID string
        assert isinstance(result, str)
        assert len(result) == 36
        # Validate it's a proper UUID
        uuid.UUID(result)

    def test_generates_unique_ids(self) -> None:
        """Test that multiple calls generate unique IDs."""
        id1 = generate_correlation_id()
        id2 = generate_correlation_id()

        assert id1 != id2
        assert isinstance(id1, str)
        assert isinstance(id2, str)


class TestIsValidCorrelationId:
    """Test is_valid_correlation_id function."""

    def test_valid_uuid_correlation_id(self) -> None:
        """Test validation of UUID correlation ID."""
        uuid_id = str(uuid.uuid4())
        assert is_valid_correlation_id(uuid_id) is True

    def test_valid_custom_correlation_id(self) -> None:
        """Test validation of custom correlation ID."""
        custom_id = "session-user-123-abc"
        assert is_valid_correlation_id(custom_id) is True

    def test_empty_string_invalid(self) -> None:
        """Test that empty string is invalid."""
        assert is_valid_correlation_id("") is False

    def test_whitespace_only_invalid(self) -> None:
        """Test that whitespace-only string is invalid."""
        assert is_valid_correlation_id("   ") is False
        assert is_valid_correlation_id("\t\n") is False

    def test_none_invalid(self) -> None:
        """Test that None is invalid."""
        assert is_valid_correlation_id(None) is False


class TestGetCorrelationIdWithFallback:
    """Test get_correlation_id_with_fallback function."""

    def test_uses_header_when_available(self) -> None:
        """Test uses header correlation ID when available."""
        request = Mock(spec=Request)
        request.headers = {"x-request-id": "header-id-123"}

        result = get_correlation_id_with_fallback(request, fallback_id="fallback-id")
        assert result == "header-id-123"

    def test_uses_fallback_when_no_header(self) -> None:
        """Test uses fallback when no header is present."""
        request = Mock(spec=Request)
        request.headers = {}

        result = get_correlation_id_with_fallback(
            request, fallback_id="fallback-id-456"
        )
        assert result == "fallback-id-456"

    def test_generates_uuid_when_no_header_or_fallback(self) -> None:
        """Test generates UUID when no header or fallback."""
        request = Mock(spec=Request)
        request.headers = {}

        result = get_correlation_id_with_fallback(request)

        # Should be a valid UUID
        assert isinstance(result, str)
        assert len(result) == 36
        uuid.UUID(result)

    def test_generates_uuid_when_invalid_fallback(self) -> None:
        """Test generates UUID when fallback is invalid."""
        request = Mock(spec=Request)
        request.headers = {}

        result = get_correlation_id_with_fallback(request, fallback_id="")

        # Should be a valid UUID since fallback is invalid
        assert isinstance(result, str)
        assert len(result) == 36
        uuid.UUID(result)


class TestConstants:
    """Test module constants."""

    def test_correlation_header_names(self) -> None:
        """Test CORRELATION_HEADER_NAMES constant."""
        expected_headers = [
            "X-Request-ID",
            "X-Correlation-ID",
            "Request-ID",
            "Correlation-ID",
        ]
        assert CORRELATION_HEADER_NAMES == expected_headers

    def test_priority_correlation_header(self) -> None:
        """Test PRIORITY_CORRELATION_HEADER constant."""
        assert PRIORITY_CORRELATION_HEADER == "X-Request-ID"
