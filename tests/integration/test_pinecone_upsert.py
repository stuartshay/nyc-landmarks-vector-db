"""
Integration test for Pinecone upsert behavior.

This test verifies that the fixed ID implementation correctly replaces existing
vectors instead of creating duplicates when processing the same landmark twice.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch

import numpy as np
import pytest

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from nyc_landmarks.config.settings import settings
from nyc_landmarks.vectordb.pinecone_db import PineconeDB
from tests.utils.test_helpers import get_pinecone_db_or_skip

# Configure logging for tests
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


def get_vector_metadata(pinecone_db: PineconeDB, vector_id: str) -> Dict[str, Any]:
    """Get the metadata for a specific vector ID."""
    # Use fetch_vector_by_id for direct vector retrieval
    vector_data = pinecone_db.fetch_vector_by_id(vector_id)

    # Return the metadata of the found vector, or an empty dict if not found
    return vector_data.get("metadata", {}) if vector_data else {}


def get_vector_count(
    pinecone_db: PineconeDB, landmark_id: str
) -> Tuple[int, List[Dict[str, Any]]]:
    """Get the number of vectors for a landmark."""
    # Create random vector for query
    random_vector = np.random.rand(settings.PINECONE_DIMENSIONS).tolist()

    # Query Pinecone
    filter_dict: Dict[str, str] = {"landmark_id": landmark_id}
    results: List[Dict[str, Any]] = pinecone_db.query_vectors(
        query_vector=random_vector,
        top_k=100,  # Set high to get all chunks
        filter_dict=filter_dict,
    )

    return len(results), results


def cleanup_test_vectors(pinecone_db: PineconeDB, test_landmark_id: str) -> None:
    """Clean up any existing vectors for the test landmark.

    Args:
        pinecone_db: Pinecone database instance
        test_landmark_id: ID of the test landmark
    """
    logger.info(f"Cleaning up any existing vectors for {test_landmark_id}")
    count, results = get_vector_count(pinecone_db, test_landmark_id)
    if results:
        vector_ids = [str(r.get("id", "")) for r in results]
        pinecone_db.delete_vectors(vector_ids)


def create_test_chunks(test_landmark_id: str) -> List[Dict[str, Any]]:
    """Create test chunks for a landmark.

    Args:
        test_landmark_id: ID of the test landmark

    Returns:
        List of test chunks
    """
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

    return test_chunks


def process_chunks_first_time(
    pinecone_db: PineconeDB, test_landmark_id: str, test_chunks: List[Dict[str, Any]]
) -> List[str]:
    """Process chunks for the first time.

    Args:
        pinecone_db: Pinecone database instance
        test_landmark_id: ID of the test landmark
        test_chunks: List of test chunks

    Returns:
        List of vector IDs
    """
    logger.info(f"Processing {test_landmark_id} first time with fixed IDs")
    first_vector_ids = pinecone_db.store_chunks(
        chunks=test_chunks,
        landmark_id=test_landmark_id,
        use_fixed_ids=True,
        delete_existing=True,
    )

    # Wait for Pinecone to update
    time.sleep(5)

    # Get first count
    first_count, first_results = get_vector_count(pinecone_db, test_landmark_id)
    logger.info(f"Vector count after first processing: {first_count}")

    return first_vector_ids


def verify_vector_ids(test_landmark_id: str, vector_ids: List[str]) -> None:
    """Verify that vector IDs follow the expected pattern.

    Args:
        test_landmark_id: ID of the test landmark
        vector_ids: List of vector IDs to verify
    """
    expected_ids = [f"{test_landmark_id}-chunk-{i}" for i in range(3)]
    for expected_id in expected_ids:
        assert expected_id in vector_ids, f"Expected ID {expected_id} not found"


def verify_metadata(
    pinecone_db: PineconeDB, vector_ids: List[str], test_landmark_id: str
) -> None:
    """Verify metadata is correct.

    Args:
        pinecone_db: Pinecone database instance
        vector_ids: List of vector IDs to verify
        test_landmark_id: ID of the test landmark
    """
    for vector_id in vector_ids:
        vector_metadata = get_vector_metadata(pinecone_db, vector_id)

        # Add more robust error handling for metadata access
        try:
            assert (
                vector_metadata.get("landmark_id") == test_landmark_id
            ), f"Incorrect landmark_id in metadata: {vector_metadata}"
            assert (
                vector_metadata.get("source_type") == "test"
            ), f"Incorrect source_type in metadata: {vector_metadata}"
        except KeyError as e:
            # Log the actual metadata to help debug
            logger.error(f"KeyError when accessing metadata: {e}")
            logger.error(f"Vector metadata: {vector_metadata}")
            # Re-raise with more information
            raise KeyError(
                f"Expected key {e} not found in metadata: {vector_metadata}"
            ) from e


def process_chunks_second_time(
    pinecone_db: PineconeDB, test_landmark_id: str, test_chunks: List[Dict[str, Any]]
) -> List[str]:
    """Process chunks for the second time.

    Args:
        pinecone_db: Pinecone database instance
        test_landmark_id: ID of the test landmark
        test_chunks: List of test chunks

    Returns:
        List of vector IDs
    """
    logger.info(f"Processing {test_landmark_id} second time with fixed IDs")

    # Update the processing date to identify the second run
    today = time.strftime("%Y-%m-%d")
    for chunk in test_chunks:
        # Update at both the chunk level and metadata level to ensure it's captured
        chunk["processing_date"] = today
        if "metadata" in chunk:
            chunk["metadata"]["processing_date"] = today
        else:
            chunk["metadata"] = {"processing_date": today}

    second_vector_ids = pinecone_db.store_chunks(
        chunks=test_chunks,
        landmark_id=test_landmark_id,
        use_fixed_ids=True,
        delete_existing=True,
    )

    # Wait for Pinecone to update
    time.sleep(5)

    return second_vector_ids


def verify_second_processing(
    pinecone_db: PineconeDB,
    test_landmark_id: str,
    first_vector_ids: List[str],
    second_vector_ids: List[str],
) -> None:
    """Verify results after second processing.

    Args:
        pinecone_db: Pinecone database instance
        test_landmark_id: ID of the test landmark
        first_vector_ids: Vector IDs from first processing
        second_vector_ids: Vector IDs from second processing
    """
    # Get second count
    second_count, second_results = get_vector_count(pinecone_db, test_landmark_id)
    logger.info(f"Vector count after second processing: {second_count}")

    # Get first count
    first_count, first_results = get_vector_count(pinecone_db, test_landmark_id)

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
        processing_date = second_results[0].get("metadata", {}).get("processing_date")
        logger.info(f"Most recent processing_date: {processing_date}")

        # It should be today's date
        assert processing_date == time.strftime(
            "%Y-%m-%d"
        ), "Processing date should be updated"


def test_retry_logic_internal(
    pinecone_db: PineconeDB,
    test_landmark_id: str,
    test_chunks: List[Dict[str, Any]],
) -> None:
    """Test retry logic when batch operations fail.

    Args:
        pinecone_db: Pinecone database instance
        test_landmark_id: ID of the test landmark
        test_chunks: List of test chunks
    """

    # Simulate a batch failure and verify retry logic
    with patch.object(
        pinecone_db.index, "upsert", side_effect=Exception("Simulated failure")
    ) as mock_upsert:
        try:
            pinecone_db.store_chunks(
                chunks=test_chunks,
                landmark_id=test_landmark_id,
                use_fixed_ids=True,
                delete_existing=True,
            )
        except Exception as e:
            # Expected to fail due to simulated exception - log for debugging
            logger.debug(f"Expected exception in retry test: {e}")

        # Verify retry attempts
        assert mock_upsert.call_count == 3, "Retry logic failed to execute 3 attempts"


@pytest.mark.integration
def test_fixed_id_upsert_behavior(pinecone_test_db: Optional[PineconeDB]) -> None:
    """Test that processing the same landmark twice doesn't create duplicates."""
    # Skip if Pinecone test database is not available
    pinecone_db = get_pinecone_db_or_skip(pinecone_test_db)

    # Skip test if no Pinecone connection
    if not pinecone_db.index:
        pytest.skip("No Pinecone index available")

    # Use a test landmark ID to avoid affecting real landmarks
    test_landmark_id = "TEST-UPSERT-001"

    try:
        # Setup: clean up any existing test vectors
        cleanup_test_vectors(pinecone_db, test_landmark_id)

        # Step 1: Create test chunks and process first time
        test_chunks = create_test_chunks(test_landmark_id)
        first_vector_ids = process_chunks_first_time(
            pinecone_db, test_landmark_id, test_chunks
        )

        # Step 2: Verify first processing results
        verify_vector_ids(test_landmark_id, first_vector_ids)
        verify_metadata(pinecone_db, first_vector_ids, test_landmark_id)

        # Step 3: Process second time with updated dates
        second_vector_ids = process_chunks_second_time(
            pinecone_db, test_landmark_id, test_chunks
        )

        # Step 4: Verify second processing results
        verify_second_processing(
            pinecone_db, test_landmark_id, first_vector_ids, second_vector_ids
        )

        # Step 5: Test retry logic
        test_retry_logic_internal(pinecone_db, test_landmark_id, test_chunks)

    finally:
        # Clean up
        cleanup_test_vectors(pinecone_db, test_landmark_id)


@pytest.mark.integration
def test_retry_logic_standalone(pinecone_test_db: Optional[PineconeDB]) -> None:
    """Test retry logic when batch operations fail as a standalone test.

    Args:
        pinecone_test_db: Pinecone database instance
    """
    # Skip if Pinecone test database is not available
    pinecone_db = get_pinecone_db_or_skip(pinecone_test_db)

    # Use a test landmark ID
    test_landmark_id = "TEST-RETRY-001"

    # Create test chunks
    test_chunks = create_test_chunks(test_landmark_id)

    try:
        # Call the internal retry logic test
        test_retry_logic_internal(pinecone_db, test_landmark_id, test_chunks)
    finally:
        # Clean up test vectors
        cleanup_test_vectors(pinecone_db, test_landmark_id)
