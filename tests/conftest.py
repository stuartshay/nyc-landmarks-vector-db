"""
Global pytest configuration file.

This file configures pytest to automatically apply markers based on test location.
"""

from typing import List

import pytest


def pytest_collection_modifyitems(items: List[pytest.Item]) -> None:
    """Apply markers automatically based on test directory."""
    for item in items:
        # Get the path to the test file
        test_path = item.fspath.strpath

        # Apply markers based on directory
        if "/tests/unit/" in test_path:
            item.add_marker(pytest.mark.unit)
        elif "/tests/integration/" in test_path:
            item.add_marker(pytest.mark.integration)
        elif "/tests/functional/" in test_path:
            item.add_marker(pytest.mark.functional)
        elif "/tests/scripts/" in test_path:
            item.add_marker(pytest.mark.scripts)
