"""
Integration test for Pinecone upsert behavior.

This test verifies that the fixed ID implementation correctly replaces existing
vectors instead of creating duplicates when processing the same landmark twice.
"""

import logging
import sys
import time
from pathlib import Path

import numpy as np
import pytest

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from nyc_landmarks.config.settings import settings
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging for tests
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


def get_vector_count(
    pinecone_db: PineconeDB, landmark_id: str
) -> tuple[int, list[dict[str, any]]]:
    """Get the number of vectors for a landmark."""
    # Create random vector for query
    random_vector = np.random.rand(settings.PINECONE_DIMENSIONS).tolist()

    # Query Pinecone
    filter_dict: dict[str, str] = {"landmark_id": landmark_id}
    results: list[dict[str, any]] = pinecone_db.query_vectors(
        query_vector=random_vector,
        top_k=100,  # Set high to get all chunks
        filter_dict=filter_dict,
    )

    return len(results), results


@pytest.mark.integration
def test_fixed_id_upsert_behavior():
    """Test that processing the same landmark twice doesn't create duplicates."""
    # Skip test if no Pinecone connection
    pinecone_db = PineconeDB()
    if not pinecone_db.index:
        pytest.skip("No Pinecone index available")

    # Use a test landmark ID to avoid affecting real landmarks
    test_landmark_id = "TEST-UPSERT-001"

    # Clean up any existing vectors for this test landmark first
    logger.info(f"Cleaning up any existing vectors for {test_landmark_id}")
    initial_count, initial_results = get_vector_count(pinecone_db, test_landmark_id)
    if initial_results:
        vector_ids = [r.get("id") for r in initial_results]
        pinecone_db.delete_vectors(vector_ids)

    try:
        # Create test chunks
        logger.info(f"Creating test chunks for {test_landmark_id}")
        test_chunks = []
        for i in range(3):
            # Create a test embedding
            embedding = np.random.rand(settings.PINECONE_DIMENSIONS).tolist()

            # Create a chunk
            chunk = {
                "text": f"Test chunk {i} for landmark {test_landmark_id}",
                "chunk_index": i,
                "total_chunks": 3,
                "metadata": {
                    "landmark_id": test_landmark_id,
                    "chunk_index": i,
                    "total_chunks": 3,
                    "source_type": "test",
                    "processing_date": time.strftime("%Y-%m-%d"),
                },
                "embedding": embedding,
            }
            test_chunks.append(chunk)

        # Process first time
        logger.info(f"Processing {test_landmark_id} first time with fixed IDs")
        first_vector_ids = pinecone_db.store_chunks(
            chunks=test_chunks,
            landmark_id=test_landmark_id,
            use_fixed_ids=True,
            delete_existing=True,
        )

        # Wait for Pinecone to update
        time.sleep(2)

        # Get first count
        first_count, _ = get_vector_count(pinecone_db, test_landmark_id)
        logger.info(f"Vector count after first processing: {first_count}")

        # Verify IDs follow expected pattern
        expected_ids = [f"{test_landmark_id}-chunk-{i}" for i in range(3)]
        for expected_id in expected_ids:
            assert (
                expected_id in first_vector_ids
            ), f"Expected ID {expected_id} not found"

        # Process second time with the same chunks
        logger.info(f"Processing {test_landmark_id} second time with fixed IDs")
        # Update the processing date to identify the second run
        for chunk in test_chunks:
            chunk["metadata"]["processing_date"] = time.strftime("%Y-%m-%d")

        second_vector_ids = pinecone_db.store_chunks(
            chunks=test_chunks,
            landmark_id=test_landmark_id,
            use_fixed_ids=True,
            delete_existing=True,
        )

        # Wait for Pinecone to update
        time.sleep(2)

        # Get second count
        second_count, second_results = get_vector_count(pinecone_db, test_landmark_id)
        logger.info(f"Vector count after second processing: {second_count}")

        # Verify counts are the same
        assert (
            second_count == first_count
        ), f"Expected count to remain at {first_count}, got {second_count}"

        # Verify IDs are the same
        assert set(first_vector_ids) == set(
            second_vector_ids
        ), "Vector IDs should be identical"

        # Get a result to check the metadata for the most recent processing_date
        if second_results:
            processing_date = (
                second_results[0].get("metadata", {}).get("processing_date")
            )
            logger.info(f"Most recent processing_date: {processing_date}")

            # It should be today's date
            assert processing_date == time.strftime(
                "%Y-%m-%d"
            ), "Processing date should be updated"

    finally:
        # Clean up
        logger.info(f"Cleaning up test vectors for {test_landmark_id}")
        cleanup_count, cleanup_results = get_vector_count(pinecone_db, test_landmark_id)
        if cleanup_results:
            vector_ids = [r.get("id") for r in cleanup_results]
            pinecone_db.delete_vectors(vector_ids)
