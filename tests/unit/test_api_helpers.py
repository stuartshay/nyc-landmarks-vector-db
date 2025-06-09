#!/usr/bin/env python3
"""
Unit tests for API availability checking functionality.
These tests use mocking to avoid requiring a real API server.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from tests.utils.api_helpers import (
    check_api_availability,
    require_api_or_skip,
    require_api_or_warn,
)


@patch("tests.utils.api_helpers.requests.get")
def test_api_availability_check_success(mock_get: Mock) -> None:
    """Test API availability check when server responds successfully."""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    result = check_api_availability("http://localhost:8000")
    assert result is True


@patch("tests.utils.api_helpers.requests.get")
def test_api_availability_check_server_error(mock_get: Mock) -> None:
    """Test API availability check when server returns error but is reachable."""
    # Mock server error (but server is reachable)
    mock_response = Mock()
    mock_response.status_code = 404  # < 500, so considered available
    mock_get.return_value = mock_response

    result = check_api_availability("http://localhost:8000")
    assert result is True


@patch("tests.utils.api_helpers.requests.get")
def test_api_availability_check_connection_error(mock_get: Mock) -> None:
    """Test API availability check when connection fails."""
    # Mock connection error
    mock_get.side_effect = requests.ConnectionError("Connection refused")

    result = check_api_availability("http://localhost:9999")
    assert result is False


@patch("tests.utils.api_helpers.requests.get")
def test_api_availability_check_timeout(mock_get: Mock) -> None:
    """Test API availability check when request times out."""
    # Mock timeout
    mock_get.side_effect = requests.Timeout("Request timed out")

    result = check_api_availability("http://localhost:8000")
    assert result is False


@patch("tests.utils.api_helpers.check_api_availability")
def test_require_api_or_warn_available(mock_check: Mock) -> None:
    """Test API warning when server is available."""
    mock_check.return_value = True

    warning = require_api_or_warn("http://localhost:8000")
    assert warning is None


@patch("tests.utils.api_helpers.check_api_availability")
def test_require_api_or_warn_unavailable(mock_check: Mock) -> None:
    """Test API warning when server is unavailable."""
    mock_check.return_value = False

    warning = require_api_or_warn("http://localhost:9999")
    assert warning is not None
    assert "⚠️  WARNING" in warning
    assert "uvicorn" in warning


@patch("tests.utils.api_helpers.check_api_availability")
def test_require_api_or_skip_unavailable(mock_check: Mock) -> None:
    """Test API skip when server is unavailable."""
    mock_check.return_value = False

    with pytest.raises(pytest.skip.Exception) as exc_info:
        require_api_or_skip("http://localhost:9999")

    assert "⚠️  Local API at http://localhost:9999 is not available" in str(
        exc_info.value
    )
    assert "uvicorn" in str(exc_info.value)


@patch("tests.utils.api_helpers.check_api_availability")
def test_require_api_or_skip_available(mock_check: Mock) -> None:
    """Test API skip when server is available (should not skip)."""
    mock_check.return_value = True

    # Should not raise any exception
    require_api_or_skip("http://localhost:8000")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
