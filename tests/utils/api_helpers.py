#!/usr/bin/env python3
"""
Helper utilities for API testing.

Usage patterns:

1. Skip entire test if API is not available (recommended for API-dependent tests):
   ```python
   @pytest.fixture(autouse=True)
   def check_api_availability(self, base_url: str) -> None:
       require_api_or_skip(base_url)
   ```

2. Warn but continue if API is not available (for tests that can partially run):
   ```python
   def test_something(self):
       warning = require_api_or_warn("http://localhost:8000")
       if warning:
           pytest.warn(UserWarning(warning))
       # ... rest of test
   ```

3. Manual check in test logic:
   ```python
   def test_something(self):
       if check_api_availability("http://localhost:8000"):
           # Run API-dependent test
       else:
           # Run alternative test or skip specific parts
   ```
"""

from typing import Optional

import pytest
import requests


def check_api_availability(base_url: str, timeout: int = 5) -> bool:
    """
    Check if the local API is available.

    Args:
        base_url: The base URL of the API (e.g., "http://localhost:8000")
        timeout: Timeout in seconds for the health check

    Returns:
        True if API is available, False otherwise
    """
    try:
        # Try to hit a health endpoint or root endpoint
        health_endpoints = [
            f"{base_url}/health",
            f"{base_url}/api/health",
            f"{base_url}/",
            f"{base_url}/docs",  # FastAPI docs endpoint
        ]

        for endpoint in health_endpoints:
            try:
                response = requests.get(endpoint, timeout=timeout)
                if response.status_code < 500:  # Any non-server error is good
                    return True
            except requests.RequestException:
                continue

        return False

    except Exception:
        return False


def require_api_or_skip(base_url: str) -> None:
    """
    Skip test if API is not available, showing a clear warning message.

    Args:
        base_url: The base URL of the API
    """
    if not check_api_availability(base_url):
        pytest.skip(
            f"⚠️  Local API at {base_url} is not available. "
            f"Please start the API server before running these tests. "
            f"You can start it with: 'uvicorn nyc_landmarks.api.main:app --host 0.0.0.0 --port 8000'"
        )


def require_api_or_warn(base_url: str) -> Optional[str]:
    """
    Check API availability and return a warning message if not available.

    Args:
        base_url: The base URL of the API

    Returns:
        Warning message if API is not available, None if available
    """
    if not check_api_availability(base_url):
        return (
            f"⚠️  WARNING: Local API at {base_url} is not available. "
            f"Please start the API server to run these tests properly. "
            f"Start with: uvicorn nyc_landmarks.api.main:app --host 0.0.0.0 --port 8000"
        )
    return None
