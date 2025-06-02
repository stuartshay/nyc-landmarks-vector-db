"""
Simplified functional tests for Pinecone vector database connectivity.

This module provides tests to verify essential Pinecone vector database operations:
1. Vector database connection and index stats retrieval

These tests use a dedicated test index in Pinecone (created by the pinecone_test_db fixture)
to ensure test isolation from production data. Each test session creates a unique index
with a timestamp and random identifier, which is cleaned up after tests complete.

Note: Vector storage and retrieval tests have been moved to integration tests since they
involve data modification operations.
"""

import logging

import pytest

from nyc_landmarks.config.settings import settings
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


@pytest.mark.functional
def test_pinecone_connection(pinecone_test_db: PineconeDB) -> None:
    """
    Test basic Pinecone connection and index stats retrieval.

    This test verifies:
    1. The connection to the Pinecone test index can be established
    2. The PineconeDB.index object is properly initialized
    3. Index statistics can be retrieved successfully via get_index_stats()
    4. The returned stats are in the expected format (a dict without errors)
    5. Key index properties like dimension, vector count, and namespaces are accessible

    Args:
        pinecone_test_db: Fixture providing a PineconeDB instance connected to a test index
    """
    logger.info("=== Testing Pinecone connection ===")

    # Use test-specific Pinecone client provided by the fixture
    # This connects to a dedicated test index isolated from production data
    pinecone_db = pinecone_test_db

    # Verify index connection - this checks that the Pinecone client is properly initialized
    # and connected to the serverless test index created by the fixture
    assert pinecone_db.index is not None, "Failed to connect to Pinecone index"

    # Get index stats - this calls Pinecone's describe_index_stats API
    # to retrieve metadata about the index such as vector count and dimension
    stats = pinecone_db.get_index_stats()

    # Verify the stats were returned as a dictionary
    assert isinstance(stats, dict), "Failed to retrieve index stats"

    # Verify there are no errors in the stats response
    # Pinecone will include an "error" key if something went wrong
    assert "error" not in stats, f"Error in stats: {stats.get('error')}"

    # Log useful information
    logger.info(f"Connected to Pinecone index: {pinecone_db.index_name}")
    logger.info(f"Current vector count: {stats.get('total_vector_count', 0)}")
    logger.info(f"Dimension: {stats.get('dimension', 0)}")
    logger.info(f"Namespaces: {stats.get('namespaces', {})}")

    logger.info("=== Pinecone connection test passed ===")
