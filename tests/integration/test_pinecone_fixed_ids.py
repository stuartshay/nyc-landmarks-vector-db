"""
Test the fixed ID functionality in PineconeDB
"""

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pytest

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from nyc_landmarks.config.settings import settings
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Set up logger
logger = get_logger(name="test_pinecone_fixed_ids")


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


def save_verification_results(results, output_dir=None):
    """
    Save verification results to files.

    Args:
        results: Dictionary with verification results
        output_dir: Directory to save verification results. If None, won't save.
    """
    if not output_dir:
        return

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    # Save overall results
    results_file = output_dir / "verification_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved verification results to {results_file}")

    # Save individual landmark results
    for landmark_id, landmark_results in results.items():
        if landmark_id == "summary":
            continue

        landmark_file = output_dir / f"verification_{landmark_id}.json"
        with open(landmark_file, "w") as f:
            json.dump(landmark_results, f, indent=2)


def verify_landmark_vectors(pinecone_db, random_vector, landmark_id, verbose=False):
    """
    Verify vectors for a specific landmark.

    Args:
        pinecone_db: PineconeDB instance
        random_vector: Random vector for querying
        landmark_id: Landmark ID to verify
        verbose: Whether to print verbose output

    Returns:
        Dictionary with verification results
    """
    logger.info(f"Verifying vectors for landmark: {landmark_id}")

    # Check if vectors exist with the correct ID format
    filter_dict = {"landmark_id": landmark_id}
    vectors = pinecone_db.query_vectors(
        query_vector=random_vector, top_k=10, filter_dict=filter_dict
    )

    landmark_results = {
        "landmark_id": landmark_id,
        "vectors_found": len(vectors),
        "fixed_id_format_correct": True,
        "metadata_consistent": True,
        "vectors": [],
    }

    if vectors:
        logger.info(f"Found {len(vectors)} vectors for {landmark_id}")

        # Verify each vector's ID format and metadata
        for i, vector in enumerate(vectors):
            vector_id = vector.get("id", "")
            expected_id_format = f"{landmark_id}-chunk-"

            vector_data = {
                "id": vector_id,
                "score": vector.get("score"),
                "metadata": vector.get("metadata", {}),
            }

            # Check ID format
            if not vector_id.startswith(expected_id_format):
                landmark_results["fixed_id_format_correct"] = False
                logger.warning(f"  Vector {i+1} has incorrect ID format: {vector_id}")
                logger.warning(f"  Expected format starting with: {expected_id_format}")

            # Check metadata
            metadata = vector.get("metadata", {})
            if "landmark_id" not in metadata or metadata["landmark_id"] != landmark_id:
                landmark_results["metadata_consistent"] = False
                logger.warning(
                    f"  Vector {i+1} has incorrect metadata: {metadata.get('landmark_id')}"
                )

            # Check for essential metadata fields
            essential_fields = [
                "landmark_id",
                "chunk_index",
                "total_chunks",
                "processing_date",
            ]
            missing_fields = [
                field for field in essential_fields if field not in metadata
            ]

            if missing_fields:
                landmark_results["metadata_consistent"] = False
                logger.warning(
                    f"  Vector {i+1} is missing essential metadata: {missing_fields}"
                )

            # Add vector data to results
            landmark_results["vectors"].append(vector_data)

            if verbose:
                logger.info(f"  Vector {i+1}:")
                logger.info(f"    ID: {vector_id}")
                logger.info(f"    Score: {vector.get('score')}")
                logger.info("    Metadata:")
                for key, value in metadata.items():
                    logger.info(f"      {key}: {value}")
    else:
        logger.warning(f"No vectors found for {landmark_id}")
        landmark_results["fixed_id_format_correct"] = False
        landmark_results["metadata_consistent"] = False

    return landmark_results


def create_verification_summary(results):
    """
    Create a summary of the verification results.

    Args:
        results: Dictionary with verification results

    Returns:
        Summary dictionary
    """
    landmark_ids = [lid for lid in results if lid != "summary"]
    summary = {
        "total_landmarks_checked": len(landmark_ids),
        "landmarks_with_vectors": sum(
            1 for lid in landmark_ids if results[lid]["vectors_found"] > 0
        ),
        "correct_id_format": sum(
            1 for lid in landmark_ids if results[lid]["fixed_id_format_correct"]
        ),
        "consistent_metadata": sum(
            1 for lid in landmark_ids if results[lid]["metadata_consistent"]
        ),
        "all_checks_passed": all(
            results[lid]["fixed_id_format_correct"]
            and results[lid]["metadata_consistent"]
            for lid in landmark_ids
        ),
    }

    return summary


@pytest.mark.integration
def test_landmark_fixed_ids(pinecone_db, random_vector):
    """Test that landmark vectors have fixed IDs and consistent metadata."""
    # Define landmark IDs to test - use a mix of different types
    landmark_ids = ["LP-00001", "LP-00009", "LP-00042", "LP-00066"]

    results = {}

    # Verify each landmark
    for landmark_id in landmark_ids:
        landmark_results = verify_landmark_vectors(
            pinecone_db, random_vector, landmark_id, verbose=False
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

    if summary["all_checks_passed"]:
        logger.info(
            "\n✅ SUCCESS: All vectors have correct fixed ID format and consistent metadata"
        )
    else:
        logger.warning(
            "\n⚠️ WARNING: Some vectors have incorrect ID format or inconsistent metadata"
        )

    # Save results if output directory is provided
    output_dir = os.environ.get("VERIFICATION_OUTPUT_DIR")
    if output_dir:
        save_verification_results(results, output_dir)

    # Assert that all tests passed
    assert summary["landmarks_with_vectors"] > 0, "No vectors found for any landmark"
    assert (
        summary["correct_id_format"] == summary["total_landmarks_checked"]
    ), "Some vectors have incorrect ID format"
    assert (
        summary["consistent_metadata"] == summary["total_landmarks_checked"]
    ), "Some vectors have inconsistent metadata"


@pytest.mark.integration
def test_pinecone_index_stats(pinecone_db):
    """Test that Pinecone index has expected statistics."""
    stats = pinecone_db.get_index_stats()

    # Log key statistics
    logger.info(f"Total vectors: {stats.get('total_vector_count', 0)}")
    logger.info(f"Dimension: {pinecone_db.dimensions}")

    # Assert basic expectations
    assert stats.get("total_vector_count", 0) > 0, "No vectors found in Pinecone index"
    assert pinecone_db.dimensions == 1536, "Unexpected vector dimension"

    # Check if we can access namespace stats
    if stats.get("namespaces") and "" in stats["namespaces"]:
        namespace_stats = stats["namespaces"][""]
        logger.info(f"Namespace vector count: {namespace_stats.get('vector_count', 0)}")


@pytest.fixture
def random_vector():
    """Return a random vector for testing queries."""
    db = PineconeDB()
    return np.random.rand(db.dimensions).tolist()


@pytest.fixture
def embedding_generator():
    """Return an EmbeddingGenerator instance."""
    return EmbeddingGenerator()


@pytest.fixture
def pinecone_db():
    """Return a PineconeDB instance."""
    return PineconeDB()
