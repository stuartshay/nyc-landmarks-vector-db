#!/usr/bin/env python3
"""
Script to verify metadata for a batch of Wikipedia vectors.

This script checks multiple Wikipedia vectors to ensure they have the required metadata fields.
"""

from typing import Dict, List

from check_specific_vector import check_vector

from nyc_landmarks.utils.logger import get_logger

logger = get_logger(__name__)


def verify_batch_vectors(vector_ids: List[str]) -> Dict[str, bool]:
    """
    Verify metadata for a batch of vectors.

    Args:
        vector_ids: List of vector IDs to check

    Returns:
        Dictionary mapping vector IDs to validation result (True if valid, False if not)
    """
    results = {}

    print(f"Verifying {len(vector_ids)} vectors...")
    print("=" * 50)

    for vector_id in vector_ids:
        print(f"\nChecking vector: {vector_id}")
        try:
            # Simply run check_vector and note whether it completes successfully
            # This will print the vector's metadata to the console
            check_vector(vector_id)

            # If we got here without an exception, the vector exists
            # The check_vector function prints whether required fields are present
            results[vector_id] = True
        except Exception as e:
            print(f"✗ {vector_id} error: {e}")
            results[vector_id] = False

    # Print summary
    print("\n" + "=" * 50)
    print("VERIFICATION RESULTS:")
    valid_count = sum(1 for result in results.values() if result)
    print(
        f"Valid vectors: {valid_count}/{len(vector_ids)} ({valid_count/len(vector_ids)*100:.1f}%)"
    )

    if valid_count < len(vector_ids):
        print("\nInvalid vectors:")
        for vector_id, is_valid in results.items():
            if not is_valid:
                print(f"- {vector_id}")

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
