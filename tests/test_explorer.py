"""
Test utilities module for VS Code Test Explorer.

This file helps VS Code's Test Explorer discover tests more reliably.
"""

# Import pytest to enable test discovery
import pytest

# Import all test modules to ensure they're discovered
import tests.unit
import tests.functional
import tests.integration
import tests.test_config

# Add any additional test-related imports here
