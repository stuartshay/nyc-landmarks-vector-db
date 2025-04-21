"""
Test the fixed ID functionality in PineconeDB
"""

import sys
import time
from pathlib import Path

import numpy as np
import pytest

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from nyc_landmarks.config.settings import settings
from nyc_landmarks.vectordb.pinecone_db import PineconeDB


@pytest.mark.integration
def test_fixed_ids_implementation():
    """Test that the fixed ID implementation works as expected."""
    # Initialize PineconeDB
    pinecone_db = PineconeDB()

    # Skip test if no Pinecone connection
    if not pinecone_db.index:
        pytest.skip("No Pinecone index available")

    # Use a test landmark ID
    test_landmark_id = "TEST-FIXED-IDS-001"

    # Clean up any existing vectors for this test landmark
    cleanup_vectors(pinecone_db, test_landmark_id)

    try:
        # Create test chunks
        test_chunks = create_test_chunks(test_landmark_id, 3)

        # First store with fixed IDs
        first_vector_ids = pinecone_db.store_chunks_with_fixed_ids(
            chunks=test_chunks, landmark_id=test_landmark_id
        )

        # Wait for Pinecone to update
        time.sleep(2)

        # Query to verify
        first_count = count_vectors(pinecone_db, test_landmark_id)
        assert first_count == 3, f"Expected 3 vectors, got {first_count}"

        # Verify IDs follow the pattern landmark_id-chunk-X
        expected_ids = [f"{test_landmark_id}-chunk-{i}" for i in range(3)]
        for expected_id in expected_ids:
            assert (
                expected_id in first_vector_ids
            ), f"Expected ID {expected_id} not found"

        # Store again with the same chunks
        second_vector_ids = pinecone_db.store_chunks_with_fixed_ids(
            chunks=test_chunks, landmark_id=test_landmark_id
        )

        # Wait for Pinecone to update
        time.sleep(2)

        # Count again to verify no duplicates
        second_count = count_vectors(pinecone_db, test_landmark_id)
        assert (
            second_count == 3
        ), f"Expected 3 vectors (no duplicates), got {second_count}"

        # Verify IDs are identical
        assert set(first_vector_ids) == set(
            second_vector_ids
        ), "Vector IDs should be identical"

    finally:
        # Clean up test vectors
        cleanup_vectors(pinecone_db, test_landmark_id)


@pytest.mark.integration
def test_store_chunks_with_fixed_ids_flag():
    """Test that store_chunks works with the use_fixed_ids flag."""
    # Initialize PineconeDB
    pinecone_db = PineconeDB()

    # Skip test if no Pinecone connection
    if not pinecone_db.index:
        pytest.skip("No Pinecone index available")

    # Use a test landmark ID
    test_landmark_id = "TEST-FIXED-IDS-002"

    # Clean up any existing vectors for this test landmark
    cleanup_vectors(pinecone_db, test_landmark_id)

    try:
        # Create test chunks
        test_chunks = create_test_chunks(test_landmark_id, 3)

        # First store with use_fixed_ids=True
        vector_ids = pinecone_db.store_chunks(
            chunks=test_chunks,
            landmark_id=test_landmark_id,
            id_prefix="",
            use_fixed_ids=True,
        )

        # Wait for Pinecone to update
        time.sleep(2)

        # Query to verify
        count = count_vectors(pinecone_db, test_landmark_id)
        assert count == 3, f"Expected 3 vectors, got {count}"

        # Verify IDs follow the pattern landmark_id-chunk-X
        expected_ids = [f"{test_landmark_id}-chunk-{i}" for i in range(3)]
        assert set(vector_ids) == set(
            expected_ids
        ), "Vector IDs should match the expected pattern"

    finally:
        # Clean up test vectors
        cleanup_vectors(pinecone_db, test_landmark_id)


@pytest.mark.integration
def test_store_chunks_backward_compatibility():
    """Test that store_chunks maintains backward compatibility."""
    # Initialize PineconeDB
    pinecone_db = PineconeDB()

    # Skip test if no Pinecone connection
    if not pinecone_db.index:
        pytest.skip("No Pinecone index available")

    # Use a test landmark ID
    test_landmark_id = "TEST-FIXED-IDS-003"

    # Clean up any existing vectors for this test landmark
    cleanup_vectors(pinecone_db, test_landmark_id)

    try:
        # Create test chunks
        test_chunks = create_test_chunks(test_landmark_id, 2)
        test_id_prefix = f"{test_landmark_id}-old-"

        # Store with use_fixed_ids=False to use UUID-based IDs
        vector_ids = pinecone_db.store_chunks(
            chunks=test_chunks,
            landmark_id=test_landmark_id,
            id_prefix=test_id_prefix,
            use_fixed_ids=False,
        )

        # Wait for Pinecone to update
        time.sleep(2)

        # Query to verify
        count = count_vectors(pinecone_db, test_landmark_id)
        assert count == 2, f"Expected 2 vectors, got {count}"

        # Verify IDs start with the id_prefix and do NOT follow the fixed ID pattern
        for vector_id in vector_ids:
            assert vector_id.startswith(
                test_id_prefix
            ), f"Vector ID {vector_id} should start with {test_id_prefix}"
            assert not vector_id.endswith(
                "-chunk-0"
            ), f"Vector ID {vector_id} should not use fixed ID pattern"
            assert not vector_id.endswith(
                "-chunk-1"
            ), f"Vector ID {vector_id} should not use fixed ID pattern"

    finally:
        # Clean up test vectors
        cleanup_vectors(pinecone_db, test_landmark_id)


def create_test_chunks(landmark_id, count=3):
    """Create test chunks for the specified landmark."""
    chunks = []

    for i in range(count):
        # Create a test embedding
        embedding = np.random.rand(settings.PINECONE_DIMENSIONS).tolist()

        # Create a chunk
        chunk = {
            "text": f"Test chunk {i} for landmark {landmark_id}",
            "chunk_index": i,
            "total_chunks": count,
            "metadata": {
                "landmark_id": landmark_id,
                "chunk_index": i,
                "total_chunks": count,
                "source_type": "test",
            },
            "embedding": embedding,
        }

        chunks.append(chunk)

    return chunks


def count_vectors(pinecone_db, landmark_id):
    """Count vectors for a landmark."""
    # Create random vector for query
    random_vector = np.random.rand(settings.PINECONE_DIMENSIONS).tolist()

    # Query Pinecone
    filter_dict = {"landmark_id": landmark_id}
    results = pinecone_db.query_vectors(
        query_vector=random_vector,
        top_k=100,  # Set high to get all chunks
        filter_dict=filter_dict,
    )

    return len(results)


def cleanup_vectors(pinecone_db, landmark_id):
    """Clean up any vectors for the test landmark."""
    # Create random vector for query
    random_vector = np.random.rand(settings.PINECONE_DIMENSIONS).tolist()

    # Query Pinecone
    filter_dict = {"landmark_id": landmark_id}
    results = pinecone_db.query_vectors(
        query_vector=random_vector, top_k=100, filter_dict=filter_dict
    )

    # Delete vectors if any found
    if results:
        vector_ids = [r.get("id") for r in results]
        pinecone_db.delete_vectors(vector_ids)
