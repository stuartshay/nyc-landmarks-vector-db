"""
Test real landmark IDs in Pinecone DB
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB
from nyc_landmarks.vectordb.vector_id_validator import check_vector_formats

# Set up logger
logger = get_logger(name="test_real_landmark_ids")


def log_landmark_info(results: List[Dict[str, Any]], landmark_id: str) -> None:
    """
    Log information about the first vector of a landmark.

    Args:
        results: List of vector results from Pinecone
        landmark_id: The landmark ID being logged
    """
    if not results:
        return

    result = results[0]
    vector_id = result.get("id", "unknown")
    metadata = result.get("metadata", {})
    logger.info(f"Landmark {landmark_id} - First vector ID: {vector_id}")
    logger.info(
        f"Landmark {landmark_id} - First vector metadata keys: {list(metadata.keys())}"
    )
    if "name" in metadata:
        logger.info(f"Landmark {landmark_id} - Name: {metadata['name']}")


def log_results_summary(
    results_summary: Dict[str, Dict[str, Any]],
) -> Tuple[bool, bool]:
    """
    Log summary of results and determine if all checks passed.

    Args:
        results_summary: Dictionary with results for each landmark

    Returns:
        Tuple[bool, bool]: (all_found, all_correct_format) status
    """
    logger.info("\nSummary of Landmark Inspections:")
    all_found = True
    all_correct_format = True

    for landmark_id, info in results_summary.items():
        found_status = "✓" if info["found"] else "✗"
        format_status = "✓" if info.get("correct_format", False) else "✗"
        vector_count = info.get("vector_count", 0)

        logger.info(
            f"Landmark {landmark_id}: Found: {found_status} ({vector_count} vectors), Correct Format: {format_status}"
        )

        if not info["found"]:
            all_found = False
        if not info.get("correct_format", False):
            all_correct_format = False

    return all_found, all_correct_format


@pytest.mark.integration
def test_inspect_real_landmark_ids(random_vector: List[float]) -> None:
    """Inspect several real landmark IDs in Pinecone without modifying them."""
    # Using the production PineconeDB instance to inspect real data
    pinecone_db = PineconeDB()

    # Test multiple landmark IDs for consistent ID format
    landmark_ids = ["LP-00029", "LP-00009", "LP-00042", "LP-00066"]

    # Skip test if no Pinecone connection
    if not pinecone_db.index:
        pytest.skip("No Pinecone index available")

    # Track overall results for each landmark
    results_summary: Dict[str, Dict[str, Any]] = {}

    for real_landmark_id in landmark_ids:
        # Query to find vectors for this landmark
        filter_dict = {"landmark_id": real_landmark_id}
        results = pinecone_db.query_vectors(
            query_vector=random_vector, top_k=100, filter_dict=filter_dict
        )

        # Log information about found vectors
        if not results:
            logger.info(f"No vectors found for landmark {real_landmark_id}")
            results_summary[real_landmark_id] = {
                "found": False,
                "correct_format": False,
            }
            continue

        logger.info(f"Found {len(results)} vectors for landmark {real_landmark_id}")
        results_summary[real_landmark_id] = {
            "found": True,
            "correct_format": True,
            "vector_count": len(results),
        }

        # Log sample vector IDs and metadata
        log_landmark_info(results, real_landmark_id)

        # Check if vector IDs follow the expected format
        correct_format = check_vector_formats(results, real_landmark_id)
        results_summary[real_landmark_id]["correct_format"] = correct_format

    # Log summary and get overall status
    all_found, all_correct_format = log_results_summary(results_summary)

    # Make assertions about the inspected landmarks
    assert all_found, "Expected to find vectors for all test landmarks"
    assert (
        all_correct_format
    ), "Expected all landmark vectors to use the standardized ID format"
