"""
Integration test for Pinecone metadata handling with null values.

This test verifies that the PineconeDB class correctly filters out null values
in metadata before uploading to Pinecone, which would otherwise cause 400 Bad Request errors.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pytest

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from nyc_landmarks.config.settings import settings
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging for tests
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


@pytest.mark.integration
def test_pinecone_null_metadata_handling(
    pinecone_test_db: Optional[PineconeDB],
) -> None:
    """Test that null values in metadata are properly filtered out."""
    # Skip if Pinecone test database is not available
    if pinecone_test_db is None:
        pytest.skip("Pinecone test database is not available")

    # Use the test-specific PineconeDB instance
    pinecone_db = pinecone_test_db

    # Skip test if no Pinecone connection
    if not pinecone_db.index:
        pytest.skip("No Pinecone index available")

    # Use a test landmark ID to avoid affecting real landmarks
    test_landmark_id = "TEST-NULL-METADATA-001"

    # Create test chunks with metadata containing null values
    # This is similar to the metadata from CoreDataStore API that might have null values
    test_metadata: Dict[str, Any] = {
        "landmark_id": test_landmark_id,
        "name": "Test Landmark with Null Values",
        "source_type": "test",
        "architect": None,  # This would cause a 400 error without filtering
        "style": "Gothic",
        "designation_date": "2025-01-01",
        "address": None,  # Another null value
        "borough": "Manhattan",
        "block": None,  # Another null value
        "lot": "123",
        "null_array": None,  # Test null array value
    }

    try:
        # Clean up any existing vectors for this test landmark first
        logger.info(f"Cleaning up any existing vectors for {test_landmark_id}")
        pinecone_db.delete_vectors_by_filter({"landmark_id": test_landmark_id})

        # Create a test chunk with the problematic metadata
        # Random vector for the test
        embedding = np.random.rand(settings.PINECONE_DIMENSIONS).tolist()

        # Create a chunk
        chunk = {
            "text": f"Test chunk for landmark {test_landmark_id} with null metadata",
            "embedding": embedding,
            "metadata": {
                "landmark_id": test_landmark_id,
                "source_type": "test",
                "chunk_index": 0,
            },
        }

        # Process the vector through the _create_metadata_for_chunk method
        metadata = pinecone_db._create_metadata_for_chunk(
            chunk=chunk,
            source_type="test",
            chunk_index=0,
            landmark_id=test_landmark_id,
            enhanced_metadata=test_metadata,
        )

        # Verify that null values have been removed from the metadata
        assert (
            "architect" not in metadata
        ), "Null 'architect' value should be filtered out"
        assert "address" not in metadata, "Null 'address' value should be filtered out"
        assert "block" not in metadata, "Null 'block' value should be filtered out"
        assert (
            "null_array" not in metadata
        ), "Null 'null_array' value should be filtered out"

        # Verify that non-null values remain
        assert metadata["landmark_id"] == test_landmark_id
        assert metadata["name"] == "Test Landmark with Null Values"
        assert metadata["style"] == "Gothic"

        # Now attempt to store the vector with the filtered metadata
        vector_id = f"{test_landmark_id}-null-test"

        # Direct storage to verify it works end-to-end
        success = pinecone_db.store_vectors_batch([(vector_id, embedding, metadata)])
        assert success, "Vector storage should succeed with filtered metadata"

        # Give Pinecone time to index
        time.sleep(5)

        # Query the vector to make sure it was stored successfully
        results = pinecone_db.query_vectors(
            query_vector=embedding,
            top_k=1,
            filter_dict={"landmark_id": test_landmark_id},
        )

        assert len(results) == 1, "Should retrieve exactly one vector"
        retrieved_metadata = results[0].get("metadata", {})

        # Verify the retrieved metadata matches what we expect
        assert retrieved_metadata["landmark_id"] == test_landmark_id
        assert (
            "architect" not in retrieved_metadata
        ), "Null 'architect' value should not be present in retrieved metadata"

        logger.info(
            "Successfully stored and retrieved vector with null metadata values filtered out"
        )

    finally:
        # Clean up
        logger.info(f"Cleaning up test vectors for {test_landmark_id}")
        pinecone_db.delete_vectors_by_filter({"landmark_id": test_landmark_id})


@pytest.mark.integration
def test_wikipedia_null_metadata_handling(
    pinecone_test_db: Optional[PineconeDB],
) -> None:
    """Test that null values in Wikipedia article metadata are properly filtered out."""
    # Skip if Pinecone test database is not available
    if pinecone_test_db is None:
        pytest.skip("Pinecone test database is not available")

    # Use the test-specific PineconeDB instance
    pinecone_db = pinecone_test_db

    # Skip test if no Pinecone connection
    if not pinecone_db.index:
        pytest.skip("No Pinecone index available")

    # Use a test landmark ID to avoid affecting real landmarks
    test_landmark_id = "TEST-WIKI-NULL-001"
    test_article_title = "Test Wikipedia Article"

    try:
        # Clean up any existing vectors for this test landmark first
        logger.info(f"Cleaning up any existing vectors for {test_landmark_id}")
        pinecone_db.delete_vectors_by_filter({"landmark_id": test_landmark_id})

        # Create a test chunk with Wikipedia article metadata containing null values
        embedding = np.random.rand(settings.PINECONE_DIMENSIONS).tolist()

        # Create a chunk with Wikipedia article metadata
        chunk = {
            "text": f"Test Wikipedia chunk for landmark {test_landmark_id}",
            "embedding": embedding,
            "article_metadata": {
                "title": test_article_title,
                "url": None,  # This would cause a 400 error without filtering
                "source": "Wikipedia",
                "extract": None,  # Another null value
            },
        }

        # Process the vector through the _create_metadata_for_chunk method
        metadata = pinecone_db._create_metadata_for_chunk(
            chunk=chunk,
            source_type="wikipedia",
            chunk_index=0,
            landmark_id=test_landmark_id,
            enhanced_metadata={},
        )

        # Verify that null values have been filtered out from article metadata
        assert "article_title" in metadata, "Article title should be present"
        assert metadata["article_title"] == test_article_title
        assert "article_url" not in metadata, "Null article URL should be filtered out"

        # Now attempt to store the vector with the filtered metadata
        vector_id = f"wiki-{test_article_title}-{test_landmark_id}-chunk-0"

        # Direct storage to verify it works end-to-end
        success = pinecone_db.store_vectors_batch([(vector_id, embedding, metadata)])
        assert success, "Vector storage should succeed with filtered Wikipedia metadata"

        # Give Pinecone time to index
        time.sleep(5)

        # Query the vector to make sure it was stored successfully
        results = pinecone_db.query_vectors(
            query_vector=embedding,
            top_k=1,
            filter_dict={"landmark_id": test_landmark_id},
        )

        assert len(results) == 1, "Should retrieve exactly one vector"
        retrieved_metadata = results[0].get("metadata", {})

        # Verify the retrieved metadata matches what we expect
        assert retrieved_metadata["landmark_id"] == test_landmark_id
        assert retrieved_metadata["source_type"] == "wikipedia"
        assert retrieved_metadata["article_title"] == test_article_title
        assert (
            "article_url" not in retrieved_metadata
        ), "Null article_url should not be present in retrieved metadata"

        logger.info(
            "Successfully stored and retrieved Wikipedia vector with null metadata values filtered out"
        )

    finally:
        # Clean up
        logger.info(f"Cleaning up test vectors for {test_landmark_id}")
        pinecone_db.delete_vectors_by_filter({"landmark_id": test_landmark_id})
