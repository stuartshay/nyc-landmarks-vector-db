#!/usr/bin/env python3
"""
Script to analyze which landmarks have been processed and which still need to be processed.

This script uses the existing test infrastructure to check for processed landmarks
and compare against the available landmarks from the API.
"""

import json
import sys
import time
from pathlib import Path
from typing import List, Optional

# Import db client and logger
from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.utils.logger import get_logger

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "notebooks"))


# Configure pinecone dependencies
try:
    # NOTE: These imports are intentionally placed here after modifying sys.path
    # to ensure the project root is in the Python path before importing project modules.
    # pyright: reportMissingImports=false
    from pinecone_adapter import PineconeAdapterDB as PineconeDB  # noqa: E402
    from pinecone_adapter import get_adapter_from_settings  # noqa: E402

    logger = get_logger(name="check_processed_landmarks")
    logger.info("Using PineconeAdapter")
except ImportError:
    # NOTE: This import is intentionally placed here as a fallback if pinecone_adapter is not available
    from nyc_landmarks.vectordb.pinecone_db import PineconeDB  # noqa: E402

    get_adapter_from_settings = None
    logger = get_logger(name="check_processed_landmarks")
    logger.warning("Failed to import PineconeAdapter, falling back to direct import")


# Common landmark IDs that we know exist based on test cases
KNOWN_LANDMARKS = ["LP-00001", "LP-00009", "LP-00042", "LP-00066"]


def fetch_all_landmarks(page_limit: Optional[int] = None) -> List[str]:
    """
    Fetch all landmarks from the API.

    Args:
        page_limit: Maximum number of pages to fetch

    Returns:
        List of all landmark IDs
    """
    db_client = get_db_client()
    all_landmark_ids = []
    page = 1
    page_size = 100

    logger.info(f"Fetching landmarks from API (page_limit={page_limit})...")

    while True:
        if page_limit and page > page_limit:
            logger.info(f"Reached page limit ({page_limit}), stopping fetch")
            break

        try:
            landmarks = db_client.get_landmarks_page(page_size=page_size, page=page)

            if not landmarks:
                logger.info(f"No more landmarks found after page {page - 1}")
                break

            # Process landmark IDs
            for landmark in landmarks:
                # Handle both dictionary and Pydantic model objects
                if isinstance(landmark, dict):
                    landmark_id = landmark.get("id", "") or landmark.get("lpNumber", "")
                else:
                    # Handle Pydantic model
                    landmark_id = getattr(landmark, "lpNumber", "")

                if landmark_id:
                    all_landmark_ids.append(landmark_id)

            logger.info(
                f"Fetched page {page}, found {len(landmarks)} landmarks, total: {len(all_landmark_ids)}"
            )
            page += 1

            # Small delay to avoid rate limiting
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Error fetching page {page}: {e}")
            if page == 1:
                # If we couldn't fetch even the first page, return an empty list
                return []
            break

    logger.info(f"Completed fetching {len(all_landmark_ids)} landmarks")
    return all_landmark_ids


def get_sample_processed_landmarks() -> set[str]:
    """
    Check if sample landmarks have been processed.

    Returns:
        Set of processed landmarks
    """
    processed: set[str] = set()

    # Initialize PineconeDB
    try:
        db = PineconeDB()
        if not db.index:
            logger.error("Failed to connect to Pinecone index")
            return processed

        logger.info(f"Connected to Pinecone index: {db.index_name}")

        # Get index stats
        stats = db.get_index_stats()
        if "error" in stats:
            logger.error(f"Error getting index stats: {stats['error']}")
            return processed

        total_vectors = stats.get("total_vector_count", 0)
        logger.info(f"Total vectors in Pinecone: {total_vectors}")

        # Generate random vector for querying
        import numpy as np

        random_vector = np.random.rand(db.dimensions).tolist()

        # Check each sample landmark
        for landmark_id in KNOWN_LANDMARKS:
            filter_dict = {"landmark_id": landmark_id}
            vectors = db.query_vectors(
                query_vector=random_vector, top_k=1, filter_dict=filter_dict
            )

            if vectors:
                processed.add(landmark_id)
                logger.info(f"Found vectors for landmark {landmark_id}")
            else:
                logger.info(f"No vectors found for landmark {landmark_id}")

    except Exception as e:
        logger.error(f"Error checking processed landmarks: {e}")

    return processed


def estimate_processed_count(processed_samples: set[str], total_count: int) -> int:
    """
    Estimate the total number of processed landmarks based on samples.

    Args:
        processed_samples: Number of processed samples
        total_count: Total number of landmarks

    Returns:
        Estimated number of processed landmarks
    """
    # If we didn't find any processed samples, assume 0
    if not processed_samples:
        return 0

    # If we found all samples are processed, estimate using the sample ratio
    sample_ratio = len(processed_samples) / len(KNOWN_LANDMARKS)
    estimated = int(sample_ratio * total_count)

    # Cap at total count
    return min(estimated, total_count)


def main() -> None:
    """Main function."""
    # Create output directory
    output_dir = project_root / "data" / "processing_status"
    output_dir.mkdir(exist_ok=True, parents=True)

    # Check if the Pinecone index has the sample landmarks
    processed_samples = get_sample_processed_landmarks()

    # Fetch all landmarks
    all_landmarks = fetch_all_landmarks(page_limit=20)  # Limit to 20 pages for testing

    if not all_landmarks:
        logger.error("No landmarks found from API")
        return

    # Calculate the estimated processed count
    total_landmarks = len(all_landmarks)
    sample_processed_count = len(processed_samples)
    estimated_processed = estimate_processed_count(processed_samples, total_landmarks)
    estimated_unprocessed = total_landmarks - estimated_processed

    # Create results dictionary
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_landmarks": total_landmarks,
        "sample_checked": len(KNOWN_LANDMARKS),
        "sample_processed": sample_processed_count,
        "sample_processed_percentage": (
            (sample_processed_count / len(KNOWN_LANDMARKS)) * 100
            if KNOWN_LANDMARKS
            else 0
        ),
        "estimated_processed": estimated_processed,
        "estimated_unprocessed": estimated_unprocessed,
        "estimated_processed_percentage": (
            (estimated_processed / total_landmarks) * 100 if total_landmarks else 0
        ),
        "known_processed_landmarks": list(processed_samples),
        "all_landmarks": all_landmarks,
    }

    # Save results to file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"landmark_status_{timestamp}.json"

    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\n=== Landmark Processing Status ===")
    print(f"Total landmarks found: {total_landmarks}")
    print(f"Sample landmarks checked: {len(KNOWN_LANDMARKS)}")
    print(
        f"Sample landmarks processed: {sample_processed_count} ({results['sample_processed_percentage']:.2f}%)"
    )
    print(
        f"Estimated processed landmarks: {estimated_processed} ({results['estimated_processed_percentage']:.2f}%)"
    )
    print(f"Estimated unprocessed landmarks: {estimated_unprocessed}")
    print(f"\nResults saved to: {results_file}")

    # If no samples were processed, no landmarks are processed
    if sample_processed_count == 0:
        print("\nNo landmarks have been processed. All landmarks need processing.")

    # If all samples were processed, estimate based on the sample ratio
    elif sample_processed_count == len(KNOWN_LANDMARKS):
        # Use a more type-safe approach for the comparison
        if results["estimated_processed_percentage"] > 95:  # type: ignore
            print("\nMost or all landmarks have been processed.")
        else:
            print(
                f"\nAn estimated {estimated_unprocessed} landmarks still need processing."
            )

    # If some samples were processed, give a mixed message
    else:
        print(
            f"\nSome landmarks have been processed ({sample_processed_count} out of {len(KNOWN_LANDMARKS)} samples)."
        )
        print(f"An estimated {estimated_unprocessed} landmarks still need processing.")

    # Give instructions for next steps
    print("\n=== Next Steps ===")
    print("1. To process remaining landmarks, run the GitHub Actions workflow.")
    print(
        "2. Alternatively, run 'scripts/process_landmarks.py' locally for more control."
    )
    print(
        "3. To process all landmarks, use '--start-page 1' and set an appropriate end page."
    )


if __name__ == "__main__":
    main()
