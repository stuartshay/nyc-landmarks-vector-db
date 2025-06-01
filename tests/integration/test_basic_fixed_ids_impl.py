"""
Test the fixed ID implementation in PineconeDB - Simplified test
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Set up logger
logger = get_logger(name="test_basic_fixed_ids_impl")


@pytest.mark.integration
def test_basic_fixed_ids_impl(pinecone_test_db: Optional[PineconeDB]) -> None:
    """Test basic functionality of fixed IDs implementation.

    This test focuses on verifying the type safety and correct format of IDs,
    not on actual Pinecone operations which would require a live connection.
    """
    # Skip if no Pinecone database or connection
    if pinecone_test_db is None:
        pytest.skip("Pinecone test database is not available")

    assert pinecone_test_db is not None  # for mypy
    pinecone_db = pinecone_test_db

    # Skip test if no Pinecone connection
    if not pinecone_db.index:
        pytest.skip("No Pinecone index available")

    # Use a test landmark ID
    test_landmark_id = "TEST-FIXED-IDS-BASIC-001"

    # Create simple test chunks
    test_chunks: List[Dict[str, Any]] = [
        {
            "text": f"Test chunk {i} for landmark {test_landmark_id}",
            "embedding": [0.1, 0.2, 0.3] * 512,  # Simple dummy embedding
            "metadata": {"landmark_id": test_landmark_id},
            "chunk_index": i,
            "total_chunks": 3,
        }
        for i in range(3)
    ]

    # Store with fixed IDs
    first_vector_ids: List[str] = pinecone_db.store_chunks_with_fixed_ids(
        chunks=test_chunks, landmark_id=test_landmark_id
    )

    # Log the IDs that were created
    logger.info(f"Generated vector IDs: {first_vector_ids}")

    # Verify IDs follow the pattern landmark_id-chunk-X
    expected_ids = [f"{test_landmark_id}-chunk-{i}" for i in range(3)]
    for expected_id in expected_ids:
        assert expected_id in first_vector_ids, f"Expected ID {expected_id} not found"

    # Store again with the same chunks
    second_vector_ids: List[str] = pinecone_db.store_chunks_with_fixed_ids(
        chunks=test_chunks, landmark_id=test_landmark_id
    )

    # Verify IDs are identical when storing with same data
    assert set(first_vector_ids) == set(
        second_vector_ids
    ), "Vector IDs should be identical"
