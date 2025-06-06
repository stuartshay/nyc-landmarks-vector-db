"""
Pytest fixtures for integration tests.

This module provides fixtures specific to integration tests.
"""

from typing import Generator, List, Optional

import numpy as np
import pytest

from nyc_landmarks.config.settings import settings
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB
from tests.utils.pinecone_test_utils import (  # delete_test_index,  # Commented out since we're keeping indexes for debugging
    create_test_index,
    get_default_test_index_name,
    get_test_db,
)

# Configure logger
logger = get_logger(name="integration_test_fixtures")


@pytest.fixture(scope="session")
def pinecone_test_db() -> Generator[Optional[PineconeDB], None, None]:
    """
    Fixture that provides a PineconeDB instance connected to a dedicated test index.

    This fixture creates a session-specific index at the start of the test session
    and deletes it at the end of the session.

    Each test session gets its own unique index name based on timestamp and random string,
    allowing for parallel test execution without conflicts.

    Tests using this fixture will be skipped if the test index cannot be created.
    """
    # Get the session-specific index name
    test_index_name = get_default_test_index_name()
    logger.info(f"Using session-specific test index: {test_index_name}")

    # Try to create the test index
    index_created = create_test_index(index_name=test_index_name)
    if not index_created:
        pytest.skip(
            "Failed to create test index - skipping tests that require Pinecone test index"
        )
        return None

    try:
        # Get a PineconeDB instance connected to the test index
        test_db = get_test_db(index_name=test_index_name)

        # Skip tests if we couldn't connect to the index
        if not test_db.index:
            pytest.skip("Could not connect to Pinecone test index")
            return None

        # Yield the database instance for tests to use
        yield test_db

    finally:
        # Keep test index for debugging - DO NOT DELETE
        # This allows manual inspection of test data in Pinecone dashboard
        logger.info(f"KEEPING test index {test_index_name} for debugging - NOT DELETED")
        logger.info(
            f"You can inspect this index manually in Pinecone dashboard: {test_index_name}"
        )
        # Commented out the deletion to keep test data for inspection
        # try:
        #     delete_test_index(index_name=test_index_name)
        # except Exception as e:
        #     logger.warning(f"Failed to delete test index {test_index_name}: {e}")


@pytest.fixture
def random_vector() -> List[float]:
    """Return a random vector for testing queries."""
    dimensions = settings.PINECONE_DIMENSIONS
    # Explicitly convert to List[float] to satisfy mypy
    vector: List[float] = np.random.rand(dimensions).tolist()
    return vector
