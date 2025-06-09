#!/usr/bin/env python3
"""
Test to verify API availability checking functionality.
"""

import pytest

from tests.utils.api_helpers import (
    check_api_availability,
    require_api_or_skip,
    require_api_or_warn,
)


def test_api_availability_check_working_server() -> None:
    """Test API availability check with working server."""
    # Test with the running server
    assert check_api_availability("http://localhost:8000") is True


def test_api_availability_check_non_working_server() -> None:
    """Test API availability check with non-working server."""
    # Test with a non-existent port
    assert check_api_availability("http://localhost:9999") is False


def test_require_api_or_warn_working_server() -> None:
    """Test API warning with working server."""
    warning = require_api_or_warn("http://localhost:8000")
    assert warning is None


def test_require_api_or_warn_non_working_server() -> None:
    """Test API warning with non-working server."""
    warning = require_api_or_warn("http://localhost:9999")
    assert warning is not None
    assert "⚠️  WARNING" in warning
    assert "uvicorn" in warning


def test_require_api_or_skip_non_working_server() -> None:
    """Test API skip with non-working server."""
    with pytest.raises(pytest.skip.Exception) as exc_info:
        require_api_or_skip("http://localhost:9999")

    assert "⚠️  Local API at http://localhost:9999 is not available" in str(
        exc_info.value
    )
    assert "uvicorn" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
