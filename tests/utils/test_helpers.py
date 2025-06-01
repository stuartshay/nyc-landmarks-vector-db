"""
Test helper utilities for the NYC Landmarks Vector DB test suite.

This module provides common utilities and helper functions that are used
across multiple test files to reduce code duplication.
"""

from typing import Optional, TypeVar

import pytest

from nyc_landmarks.vectordb.pinecone_db import PineconeDB

T = TypeVar("T")


def assert_not_none(value: Optional[T], skip_message: str = "Value is None") -> T:
    """
    Assert that a value is not None and return it with proper type narrowing.

    This is particularly useful for test fixtures that may return None,
    allowing mypy to understand that the returned value is not None.

    Args:
        value: The value to check for None
        skip_message: Message to show when skipping the test

    Returns:
        The value with None type removed

    Raises:
        pytest.skip: If value is None
    """
    if value is None:
        pytest.skip(skip_message)

    assert value is not None  # for mypy type narrowing
    return value


def get_pinecone_db_or_skip(pinecone_test_db: Optional[PineconeDB]) -> PineconeDB:
    """
    Get a PineconeDB instance or skip the test if not available.

    This helper function encapsulates the common pattern of checking
    for a PineconeDB test instance and skipping if not available.

    Args:
        pinecone_test_db: Optional PineconeDB instance from test fixture

    Returns:
        PineconeDB instance with proper type safety

    Raises:
        pytest.skip: If pinecone_test_db is None
    """
    return assert_not_none(pinecone_test_db, "Pinecone test database is not available")
