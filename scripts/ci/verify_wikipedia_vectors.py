#!/usr/bin/env python3
"""
Script to verify metadata for a batch of Wikipedia vectors.

This script checks multiple Wikipedia vectors to ensure they have the required metadata fields.
"""

from typing import Dict, List

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB
from scripts.vector_utility import validate_vector_metadata

logger = get_logger(__name__)


def _validate_single_vector(pinecone_db: PineconeDB, vector_id: str) -> bool:
    """
    Validate a single vector.

    Args:
        pinecone_db: The PineconeDB client
        vector_id: The vector ID to validate

    Returns:
        True if valid, False otherwise
    """
    print(f"\nChecking vector: {vector_id}")
    try:
        # Fetch vector data using PineconeDB
        # Use "__default__" namespace
        namespace_to_use = "__default__"
        vector_data = pinecone_db.fetch_vector_by_id(vector_id, namespace_to_use)

        if not vector_data:
            print(f"✗ {vector_id} not found in database")
            return False

        # Validate the vector metadata
        is_valid = validate_vector_metadata(vector_data, verbose=True)

        if is_valid:
            print(f"✓ {vector_id} validation passed")
        else:
            print(f"✗ {vector_id} validation failed")

        return is_valid

    except Exception as e:
        print(f"✗ {vector_id} error: {e}")
        return False


def _print_summary(results: Dict[str, bool], vector_ids: List[str]) -> None:
    """
    Print validation summary.

    Args:
        results: Dictionary mapping vector IDs to validation results
        vector_ids: List of vector IDs that were checked
    """
    print("\n" + "=" * 50)
    print("VERIFICATION RESULTS:")
    valid_count = sum(1 for result in results.values() if result)
    print(
        f"Valid vectors: {valid_count} / {len(vector_ids)} ({valid_count / len(vector_ids) * 100:.1f}%)"
    )

    if valid_count < len(vector_ids):
        print("\nInvalid vectors:")
        for vector_id, is_valid in results.items():
            if not is_valid:
                print(f"- {vector_id}")


def verify_batch_vectors(vector_ids: List[str]) -> Dict[str, bool]:
    """
    Verify metadata for a batch of vectors.

    Args:
        vector_ids: List of vector IDs to check

    Returns:
        Dictionary mapping vector IDs to validation result (True if valid, False if not)
    """
    # Initialize PineconeDB client
    try:
        pinecone_db = PineconeDB()
    except Exception as e:
        logger.error(f"Failed to initialize PineconeDB: {e}")
        return dict.fromkeys(vector_ids, False)

    print(f"Verifying {len(vector_ids)} vectors...")
    print("=" * 50)

    # Validate each vector
    results = {}
    for vector_id in vector_ids:
        results[vector_id] = _validate_single_vector(pinecone_db, vector_id)

    # Print summary
    _print_summary(results, vector_ids)

    return results


def main() -> None:
    """Main entry point."""
    # Define the Wikipedia vectors to check - these are the ones we processed earlier
    vector_ids = [
        "wiki-Wyckoff_House-LP-00001-chunk-0",
        "wiki-Brooklyn_Naval_Hospital-LP-00003-chunk-0",
        "wiki-Prospect_Park_Boathouse-LP-00004-chunk-0",
    ]

    # Verify the vectors
    verify_batch_vectors(vector_ids)


if __name__ == "__main__":
    main()
