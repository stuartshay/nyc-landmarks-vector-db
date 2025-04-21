"""
Integration tests for validating Pinecone vectors.

These tests validate that:
1. The vectors in Pinecone have the expected format and metadata
2. There are no duplicate vectors for the same landmark
3. The vector IDs follow the deterministic pattern
"""

import os

import numpy as np
import pytest

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB
from tests.verification.test_pinecone_fixed_ids import (
    create_verification_summary,
    save_verification_results,
    verify_landmark_vectors,
)

# Set up logger
logger = get_logger(name="test_pinecone_validation")


@pytest.fixture
def pinecone_db():
    """Return a PineconeDB instance."""
    return PineconeDB()


@pytest.fixture
def random_vector():
    """Return a random vector for testing queries."""
    db = PineconeDB()
    return np.random.rand(db.dimensions).tolist()


@pytest.mark.integration
def test_pinecone_index_exists(pinecone_db):
    """Test that the Pinecone index exists and is accessible."""
    stats = pinecone_db.get_index_stats()
    assert stats, "Failed to get Pinecone index stats"
    assert stats.get("total_vector_count", 0) > 0, "No vectors found in Pinecone index"

    logger.info(f"Pinecone index stats: {stats}")
    logger.info(f"Total vectors: {stats.get('total_vector_count', 0)}")


@pytest.mark.integration
def test_common_landmarks_have_vectors(pinecone_db, random_vector):
    """Test that common landmarks have vectors in Pinecone."""
    # List of common landmark IDs to check
    landmark_ids = ["LP-00001", "LP-00009", "LP-00042", "LP-00066"]

    for landmark_id in landmark_ids:
        # Query vectors for this landmark
        filter_dict = {"landmark_id": landmark_id}
        vectors = pinecone_db.query_vectors(
            query_vector=random_vector,
            top_k=10,
            filter_dict=filter_dict
        )

        # Check that we found vectors
        assert vectors, f"No vectors found for landmark {landmark_id}"
        logger.info(f"Found {len(vectors)} vectors for landmark {landmark_id}")

        # Check vector IDs follow the pattern
        for vector in vectors:
            vector_id = vector.get("id", "")
            assert vector_id.startswith(f"{landmark_id}-chunk-"), \
                f"Vector ID {vector_id} does not follow pattern {landmark_id}-chunk-X"


@pytest.mark.integration
def test_deterministic_ids_consistency(pinecone_db, random_vector):
    """Test that deterministic IDs are consistent across vectors."""
    # Get a couple of landmarks to verify
    test_landmarks = ["LP-00001", "LP-00009"]

    for landmark_id in test_landmarks:
        # Query vectors for this landmark
        filter_dict = {"landmark_id": landmark_id}
        vectors = pinecone_db.query_vectors(
            query_vector=random_vector,
            top_k=20,  # Get more to ensure we see patterns
            filter_dict=filter_dict
        )

        if not vectors:
            pytest.skip(f"No vectors found for {landmark_id}, skipping test")

        # Extract vector IDs and check for expected pattern
        vector_ids = [v.get("id", "") for v in vectors]

        # Check if IDs have the correct format: {landmark_id}-chunk-{index}
        for vid in vector_ids:
            assert vid.startswith(f"{landmark_id}-chunk-"), \
                f"Vector ID {vid} does not start with {landmark_id}-chunk-"

            # Extract chunk index and verify it's a number
            try:
                chunk_index = int(vid.split("-chunk-")[1])
                assert 0 <= chunk_index < 100, f"Chunk index {chunk_index} out of expected range"
            except (ValueError, IndexError):
                assert False, f"Vector ID {vid} does not contain a valid chunk index"

        # Check if we have the expected number of chunks
        # Get the total_chunks value from metadata if available
        if vectors[0].get("metadata", {}).get("total_chunks"):
            expected_chunks = int(vectors[0]["metadata"]["total_chunks"])
            assert len(vectors) <= expected_chunks, \
                f"Found {len(vectors)} vectors but expected {expected_chunks} based on metadata"


@pytest.mark.integration
def test_metadata_consistency(pinecone_db, random_vector):
    """Test that metadata is consistent across vectors for the same landmark."""
    # Sample landmarks to check
    test_landmarks = ["LP-00001", "LP-00009", "LP-00042"]

    for landmark_id in test_landmarks:
        # Query vectors for this landmark
        filter_dict = {"landmark_id": landmark_id}
        vectors = pinecone_db.query_vectors(
            query_vector=random_vector,
            top_k=10,
            filter_dict=filter_dict
        )

        if not vectors:
            pytest.skip(f"No vectors found for {landmark_id}, skipping test")

        # Get the metadata from the first vector
        first_metadata = vectors[0].get("metadata", {})

        # Essential fields that should be consistent across all chunks
        consistent_fields = [
            "landmark_id", "name", "borough", "style",
            "location", "designation_date", "type"
        ]

        # Check that essential fields are consistent across all vectors
        for i, vector in enumerate(vectors):
            metadata = vector.get("metadata", {})

            for field in consistent_fields:
                if field in first_metadata:
                    assert field in metadata, f"Field {field} missing from vector {i}"
                    assert metadata[field] == first_metadata[field], \
                        f"Field {field} is inconsistent: {metadata[field]} vs {first_metadata[field]}"

            # Check chunk-specific fields
            assert "chunk_index" in metadata, f"Missing chunk_index in vector {i}"
            assert "total_chunks" in metadata, f"Missing total_chunks in vector {i}"

            # Check chunk index matches the ID
            if "chunk_index" in metadata:
                chunk_index = metadata["chunk_index"]
                id_index = vector.get("id", "").split("-chunk-")[1]
                assert str(int(chunk_index)) == id_index, \
                    f"Chunk index in metadata {chunk_index} doesn't match ID {id_index}"


@pytest.mark.integration
def test_comprehensive_vector_validation(pinecone_db, random_vector):
    """Run comprehensive validation on a set of landmarks."""
    # Define landmark IDs to test
    landmark_ids = ["LP-00001", "LP-00009", "LP-00042", "LP-00066"]

    results = {}

    # Verify each landmark
    for landmark_id in landmark_ids:
        landmark_results = verify_landmark_vectors(
            pinecone_db, random_vector, landmark_id, verbose=True
        )
        results[landmark_id] = landmark_results

    # Create summary
    summary = create_verification_summary(results)
    results["summary"] = summary

    # Log summary
    logger.info("\nVerification Summary:")
    logger.info(f"Total landmarks checked: {summary['total_landmarks_checked']}")
    logger.info(f"Landmarks with vectors: {summary['landmarks_with_vectors']}")
    logger.info(f"Landmarks with correct ID format: {summary['correct_id_format']}")
    logger.info(f"Landmarks with consistent metadata: {summary['consistent_metadata']}")

    # Save results if output directory is set
    output_dir = os.environ.get("VERIFICATION_OUTPUT_DIR")
    if output_dir:
        save_verification_results(results, output_dir)

    # Assert that all landmarks have vectors and they're valid
    assert summary["landmarks_with_vectors"] == summary["total_landmarks_checked"], \
        "Some landmarks don't have vectors"
    assert summary["correct_id_format"] == summary["total_landmarks_checked"], \
        "Some vectors have incorrect ID format"
    assert summary["consistent_metadata"] == summary["total_landmarks_checked"], \
        "Some vectors have inconsistent metadata"
