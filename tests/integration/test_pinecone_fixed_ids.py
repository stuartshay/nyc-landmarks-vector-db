"""
Test the fixed ID functionality in PineconeDB
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, cast  # Removed Tuple

import numpy as np
import pytest

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Set up logger
logger = get_logger(name="test_pinecone_fixed_ids")


@pytest.mark.integration
def test_fixed_ids_implementation() -> None:
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
        test_chunks: List[Dict[str, Any]] = create_test_chunks(test_landmark_id, 3)

        # First store with fixed IDs
        first_vector_ids: List[str] = pinecone_db.store_chunks_with_fixed_ids(
            chunks=test_chunks, landmark_id=test_landmark_id
        )

        # Wait for Pinecone to update
        time.sleep(2)

        # Query to verify
        first_count: int = count_vectors(pinecone_db, test_landmark_id)
        assert first_count == 3, f"Expected 3 vectors, got {first_count}"

        # Verify IDs follow the pattern landmark_id-chunk-X
        expected_ids = [f"{test_landmark_id}-chunk-{i}" for i in range(3)]
        for expected_id in expected_ids:
            assert (
                expected_id in first_vector_ids
            ), f"Expected ID {expected_id} not found"

        # Store again with the same chunks
        second_vector_ids: List[str] = pinecone_db.store_chunks_with_fixed_ids(
            chunks=test_chunks, landmark_id=test_landmark_id
        )

        # Wait for Pinecone to update
        time.sleep(2)

        # Count again to verify no duplicates
        second_count: int = count_vectors(pinecone_db, test_landmark_id)
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
def test_store_chunks_with_fixed_ids_flag() -> None:
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
        test_chunks: List[Dict[str, Any]] = create_test_chunks(test_landmark_id, 3)

        # First store with use_fixed_ids=True
        vector_ids: List[str] = pinecone_db.store_chunks(
            chunks=test_chunks,
            landmark_id=test_landmark_id,
            id_prefix="",
            use_fixed_ids=True,
        )

        # Wait for Pinecone to update
        time.sleep(2)

        # Query to verify
        count: int = count_vectors(pinecone_db, test_landmark_id)
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
def test_store_chunks_backward_compatibility() -> None:
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
        test_chunks: List[Dict[str, Any]] = create_test_chunks(test_landmark_id, 2)

        # Store using default (use_fixed_ids=True)
        vector_ids: List[str] = pinecone_db.store_chunks(
            chunks=test_chunks, landmark_id=test_landmark_id, id_prefix=""
        )

        # Wait for Pinecone to update
        time.sleep(2)

        # Verify count and IDs
        count: int = count_vectors(pinecone_db, test_landmark_id)
        assert count == 2, f"Expected 2 vectors, got {count}"
        expected_ids = [f"{test_landmark_id}-chunk-{i}" for i in range(2)]
        assert set(vector_ids) == set(
            expected_ids
        ), "Vector IDs should match the fixed ID pattern"

    finally:
        # Clean up test vectors
        cleanup_vectors(pinecone_db, test_landmark_id)


# Helper functions
def create_test_chunks(landmark_id: str, count: int = 3) -> List[Dict[str, Any]]:
    """Create dummy chunks for testing."""
    chunks: List[Dict[str, Any]] = []
    embedding_generator = EmbeddingGenerator()
    for i in range(count):
        text = f"This is test chunk {i} for landmark {landmark_id}."
        embedding: List[float] = embedding_generator.generate_embedding(text)
        chunk: Dict[str, Any] = {
            "text": text,
            "metadata": {"source": "test", "landmark_id": landmark_id},
            "embedding": embedding,
            "chunk_index": i,
            "total_chunks": count,
        }
        chunks.append(chunk)
    return chunks


def count_vectors(pinecone_db: PineconeDB, landmark_id: str) -> int:
    """Count vectors for a specific landmark ID."""
    filter_dict = {"landmark_id": landmark_id}
    # Use a dummy random vector for querying
    random_vector = np.random.rand(pinecone_db.dimensions).tolist()
    results: List[Dict[str, Any]] = pinecone_db.query_vectors(
        query_vector=random_vector, top_k=1000, filter_dict=filter_dict
    )
    return len(results)


def cleanup_vectors(pinecone_db: PineconeDB, landmark_id: str) -> None:
    """Delete all vectors for a specific landmark ID."""
    filter_dict = {"landmark_id": landmark_id}
    # Use a dummy random vector for querying
    random_vector = np.random.rand(pinecone_db.dimensions).tolist()
    results: List[Dict[str, Any]] = pinecone_db.query_vectors(
        query_vector=random_vector, top_k=1000, filter_dict=filter_dict
    )

    if results:
        vector_ids: List[str] = [r.get("id", "") for r in results if r.get("id")]
        if vector_ids:
            pinecone_db.delete_vectors(vector_ids)
            logger.info(f"Cleaned up {len(vector_ids)} vectors for {landmark_id}")
            # Wait briefly for deletion to propagate
            time.sleep(1)


# Verification functions (used by test_pinecone_validation.py)


def _check_vector_id_format(
    vector_id: str, metadata: Dict[str, Any], landmark_id: str, verbose: bool
) -> bool:
    """Helper function to check the format and consistency of a vector ID."""
    is_format_correct = True
    expected_prefix = f"{landmark_id}-chunk-"
    if not vector_id.startswith(expected_prefix):
        is_format_correct = False
        if verbose:
            logger.error(f"Vector ID {vector_id} does not start with {expected_prefix}")
    else:
        try:
            chunk_index_from_id = int(vector_id.split("-chunk-")[1])
            if "chunk_index" in metadata:
                chunk_index_from_meta = metadata["chunk_index"]
                if int(chunk_index_from_meta) != chunk_index_from_id:
                    is_format_correct = False
                    if verbose:
                        logger.error(
                            f"ID chunk index {chunk_index_from_id} != metadata chunk index {chunk_index_from_meta}"
                        )
        except (ValueError, IndexError):
            is_format_correct = False
            if verbose:
                logger.error(f"Could not parse chunk index from ID {vector_id}")
    return is_format_correct


def _check_metadata_consistency(
    current_metadata: Dict[str, Any],
    first_metadata: Dict[str, Any],
    fields_to_check: List[str],
    vector_id: str,
    verbose: bool,
) -> bool:
    """Helper function to check consistency of metadata fields against the first vector."""
    is_consistent = True
    for field in fields_to_check:
        if current_metadata.get(field) != first_metadata.get(field):
            is_consistent = False
            if verbose:
                logger.error(
                    f"Inconsistent metadata for {vector_id}: field '{field}' mismatch (Current: {current_metadata.get(field)}, First: {first_metadata.get(field)})"
                )
            # No need to check further fields if one is inconsistent
            break
    return is_consistent


def verify_landmark_vectors(
    pinecone_db: PineconeDB,
    random_vector: List[float],
    landmark_id: str,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Verify vectors for a specific landmark."""
    if verbose:
        logger.info(f"Verifying landmark: {landmark_id}")

    landmark_results: Dict[str, Any] = {
        "landmark_id": landmark_id,
        "found_vectors": False,
        "correct_id_format": True,
        "consistent_metadata": True,
        "vectors": [],
    }

    # Query vectors for this landmark
    filter_dict = {"landmark_id": landmark_id}
    vectors: List[Dict[str, Any]] = pinecone_db.query_vectors(
        query_vector=random_vector, top_k=100, filter_dict=filter_dict
    )

    if not vectors:
        if verbose:
            logger.warning(f"No vectors found for {landmark_id}")
        return landmark_results

    landmark_results["found_vectors"] = True
    landmark_results["vectors"] = vectors  # Store vectors for potential further checks
    if verbose:
        logger.info(f"Found {len(vectors)} vectors for {landmark_id}")

    first_metadata: Optional[Dict[str, Any]] = vectors[0].get("metadata")
    consistent_fields = [
        "landmark_id",
        "name",
        "borough",
        "style",
        "location",
        "designation_date",
        "type",
    ]

    for i, vector in enumerate(vectors):
        vector_id: str = vector.get("id", "")
        metadata: Dict[str, Any] = vector.get("metadata", {})

        # Check ID format using helper
        if not _check_vector_id_format(vector_id, metadata, landmark_id, verbose):
            landmark_results["correct_id_format"] = False

        # Check metadata consistency using helper (skip first vector)
        if i > 0 and first_metadata:
            if not _check_metadata_consistency(
                metadata, first_metadata, consistent_fields, vector_id, verbose
            ):
                landmark_results["consistent_metadata"] = False

    return landmark_results


def create_verification_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    """Create a summary of verification results."""
    total_landmarks = len(results)
    summary: Dict[str, Any] = {
        "total_landmarks_checked": total_landmarks,
        "landmarks_with_vectors": 0,
        "correct_id_format": 0,
        "consistent_metadata": 0,
    }

    for landmark_id, data in results.items():
        if data.get("found_vectors"):
            summary["landmarks_with_vectors"] += 1
        if data.get("correct_id_format"):
            summary["correct_id_format"] += 1
        if data.get("consistent_metadata"):
            summary["consistent_metadata"] += 1

    return summary


def save_verification_results(
    results: Dict[str, Any], output_dir: Optional[str] = None
) -> None:
    """Save verification results to a JSON file."""
    if not output_dir:
        logger.info("No output directory specified, skipping saving results.")
        return

    try:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)

        # Save summary
        summary = results.get("summary")
        if summary:
            summary_file = output_path / "verification_summary.json"
            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=2)
            logger.info(f"Saved verification summary to {summary_file}")

        # Save individual landmark results
        for (
            landmark_id,
            data,
        ) in results.items():  # landmark_id is intentionally unused here
            if landmark_id != "summary":
                landmark_file = output_path / f"verification_{landmark_id}.json"
                with open(landmark_file, "w") as f:
                    json.dump(data, f, indent=2)
        logger.info(f"Saved individual landmark results to {output_path}")

    except Exception as e:
        logger.error(f"Error saving verification results: {e}")


@pytest.mark.integration
def test_landmark_fixed_ids(
    pinecone_db: PineconeDB, random_vector: List[float]
) -> None:
    """Test fixed IDs for a sample of real landmarks."""
    # Sample of landmark IDs to test
    landmark_ids = ["LP-00001", "LP-00009", "LP-00042", "LP-00066"]

    results: Dict[str, Any] = {}

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

    # Log detailed results for each landmark
    logger.info("\nDetailed Verification Results:")
    for landmark_id, data in results.items():
        if landmark_id != "summary":
            logger.info(f"Landmark {landmark_id}:")
            logger.info(f"  Found vectors: {data['found_vectors']}")
            logger.info(f"  Correct ID format: {data['correct_id_format']}")
            logger.info(f"  Consistent metadata: {data['consistent_metadata']}")

            # If vectors with incorrect format exist, show sample IDs
            if (
                data["found_vectors"]
                and not data["correct_id_format"]
                and data["vectors"]
            ):
                sample_ids = [v.get("id", "unknown") for v in data["vectors"][:3]]
                logger.info(f"  Sample vector IDs: {sample_ids}")

    # Save results if output directory is set
    output_dir = os.environ.get("VERIFICATION_OUTPUT_DIR")
    if output_dir:
        save_verification_results(results, output_dir)

    # Assert that all landmarks have vectors
    assert (
        summary["landmarks_with_vectors"] == summary["total_landmarks_checked"]
    ), "Some landmarks don't have vectors"

    # Check that all vectors have the correct ID format
    assert (
        summary["correct_id_format"] == summary["total_landmarks_checked"]
    ), "Some vectors have incorrect ID format"

    # Check metadata consistency
    assert (
        summary["consistent_metadata"] == summary["total_landmarks_checked"]
    ), "Some vectors have inconsistent metadata"

    # Log confirmation that all IDs are standardized
    logger.info(
        "All landmark vectors have standardized ID formats after index regeneration."
    )


@pytest.mark.integration
def test_pinecone_index_stats(pinecone_db: PineconeDB) -> None:
    """Test that Pinecone index has expected statistics."""
    stats: Dict[str, Any] = pinecone_db.get_index_stats()

    # Log key statistics
    logger.info(f"Total vectors: {stats.get('total_vector_count', 0)}")
    logger.info(f"Dimension: {pinecone_db.dimensions}")

    # Assert basic expectations
    assert stats.get("total_vector_count", 0) > 0, "No vectors found in Pinecone index"
    assert pinecone_db.dimensions == 1536, "Unexpected vector dimension"

    # Check if we can access namespace stats
    namespaces_stats = stats.get("namespaces", {})
    if namespaces_stats and "" in namespaces_stats:
        namespace_stats: Dict[str, Any] = namespaces_stats[""]
        logger.info(f"Namespace vector count: {namespace_stats.get('vector_count', 0)}")


@pytest.fixture
def pinecone_db() -> PineconeDB:
    """Return a PineconeDB instance for testing."""
    return PineconeDB()


@pytest.fixture
def random_vector() -> List[float]:
    """Return a random vector for testing queries."""
    db = PineconeDB()
    # Cast the result to ensure the correct type
    return cast(List[float], np.random.rand(db.dimensions).tolist())
