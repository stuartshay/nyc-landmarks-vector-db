#!/usr/bin/env python3
"""
Integration tests for API availability checking functionality.
These tests actually connect to API servers and should only be run
when testing the full integration behavior.
"""

import pytest

from tests.utils.api_helpers import (
    check_api_availability,
    require_api_or_skip,
    require_api_or_warn,
)


@pytest.mark.integration
def test_api_availability_check_real_working_server() -> None:
    """Test API availability check with a real working server."""
    # This test only passes if the API server is actually running
    # It will be skipped in CI/CD where no server is running
    if not check_api_availability("http://localhost:8000"):
        pytest.skip("Local API server not available for integration testing")

    assert check_api_availability("http://localhost:8000") is True


@pytest.mark.integration
def test_api_availability_check_real_non_working_server() -> None:
    """Test API availability check with a real non-working server."""
    # This should always fail since port 9999 is unlikely to be in use
    assert check_api_availability("http://localhost:9999") is False


@pytest.mark.integration
def test_require_api_or_warn_real_working_server() -> None:
    """Test API warning with a real working server."""
    # This test only passes if the API server is actually running
    if not check_api_availability("http://localhost:8000"):
        pytest.skip("Local API server not available for integration testing")

    warning = require_api_or_warn("http://localhost:8000")
    assert warning is None


@pytest.mark.integration
def test_require_api_or_warn_real_non_working_server() -> None:
    """Test API warning with a real non-working server."""
    warning = require_api_or_warn("http://localhost:9999")
    assert warning is not None
    assert "⚠️  WARNING" in warning
    assert "uvicorn" in warning


@pytest.mark.integration
def test_require_api_or_skip_real_non_working_server() -> None:
    """Test API skip with a real non-working server."""
    with pytest.raises(pytest.skip.Exception) as exc_info:
        require_api_or_skip("http://localhost:9999")

    assert "⚠️  Local API at http://localhost:9999 is not available" in str(
        exc_info.value
    )
    assert "uvicorn" in str(exc_info.value)


@pytest.mark.integration
def test_api_helpers_integration_workflow() -> None:
    """Test the complete integration workflow of API helpers."""
    # Test that we can detect both available and unavailable APIs
    available = check_api_availability("http://localhost:8000")
    unavailable = check_api_availability("http://localhost:9999")

    # Port 9999 should definitely be unavailable
    assert unavailable is False

    # If local API is running, test the full workflow
    if available:
        # API is available - no warning should be generated
        warning = require_api_or_warn("http://localhost:8000")
        assert warning is None

        # Skip function should not raise when API is available
        try:
            require_api_or_skip("http://localhost:8000")
        except pytest.skip.Exception:
            pytest.fail("require_api_or_skip should not skip when API is available")
    else:
        # API is not available - warning should be generated
        warning = require_api_or_warn("http://localhost:8000")
        assert warning is not None
        assert "⚠️  WARNING" in warning

        # This test demonstrates the skip behavior but doesn't actually skip
        # because we're testing the function behavior
        with pytest.raises(pytest.skip.Exception):
            require_api_or_skip("http://localhost:8000")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
