#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""
Script to quickly check the processing status of landmarks in Pinecone.

This script provides a fast way to determine how many landmarks have been processed
and how many still need processing.
"""

import json
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Import necessary modules
# NOTE: These imports are intentionally placed here after modifying sys.path
# to ensure the project root is in the Python path before importing project modules.
from nyc_landmarks.db.db_client import get_db_client  # noqa: E402
from nyc_landmarks.vectordb.pinecone_db import PineconeDB  # noqa: E402

# Check if our adapter exists, otherwise create a mock
adapter_path = project_root / "notebooks" / "pinecone_adapter.py"
if adapter_path.exists():
    sys.path.append(str(project_root / "notebooks"))
    try:
        # Use a local import to avoid pyright errors when the file doesn't exist
        # The import is conditional and handled by the try-except block
        from pinecone_adapter import get_adapter_from_settings  # noqa

        get_adapter_from_settings_available = True
        print("Using PineconeAdapter")
    except ImportError:
        # Fall back to using PineconeDB directly
        print("Using PineconeDB directly")
        get_adapter_from_settings_available = False
        get_adapter_from_settings = None
else:
    # Fall back to using PineconeDB directly
    print("Using PineconeDB directly")
    get_adapter_from_settings_available = False
    get_adapter_from_settings = None


def fetch_sample_landmarks(limit: int = 100) -> list[str]:
    """Fetch a sample of landmark IDs for testing."""
    print(f"Fetching up to {limit} landmarks from API...")
    db_client = get_db_client()

    # Fetch first page of landmarks
    landmarks = db_client.get_landmarks_page(page_size=limit, page=1)

    landmark_ids: list[str] = []
    for landmark in landmarks:
        # Handle both dictionary and Pydantic model objects
        if isinstance(landmark, dict):
            landmark_id = landmark.get("id", "") or landmark.get("lpNumber", "")
        else:
            # Handle Pydantic model
            landmark_id = getattr(landmark, "lpNumber", "")

        if landmark_id:
            landmark_ids.append(landmark_id)

    print(f"Fetched {len(landmark_ids)} landmark IDs")
    return landmark_ids


def check_landmarks_in_pinecone(
    landmark_ids: list[str],
) -> Optional[dict[str, list[str]]]:
    """Check which landmarks have vectors in Pinecone."""
    # Initialize Pinecone DB
    if get_adapter_from_settings:
        try:
            db = get_adapter_from_settings()
            print("Successfully initialized PineconeAdapter")
        except Exception as e:
            print(f"Error initializing adapter: {e}")
            db = PineconeDB()
            print("Falling back to PineconeDB")
    else:
        db = PineconeDB()
        print("Using PineconeDB directly")

    # Check index connection
    if not db.index:
        print("Error: Failed to connect to Pinecone index")
        return None

    print(f"Connected to Pinecone index: {db.index_name}")

    # Generate random query vector
    random_vector = np.random.rand(db.dimensions).tolist()

    # Check each landmark
    processed = []
    unprocessed = []

    print(f"Checking {len(landmark_ids)} landmarks in Pinecone...")
    for landmark_id in landmark_ids:
        filter_dict = {"landmark_id": landmark_id}
        try:
            vectors = db.query_vectors(
                query_vector=random_vector, top_k=1, filter_dict=filter_dict
            )

            if vectors:
                processed.append(landmark_id)
            else:
                unprocessed.append(landmark_id)

            # Add a small delay to avoid rate limiting
            time.sleep(0.1)
        except Exception as e:
            print(f"Error checking landmark {landmark_id}: {e}")
            unprocessed.append(landmark_id)

    return {"processed": processed, "unprocessed": unprocessed}


def main() -> None:
    """Main entry point."""
    # Fetch landmark IDs
    landmark_ids = fetch_sample_landmarks(limit=100)

    if not landmark_ids:
        print("Error: No landmarks found")
        return

    # Check processing status
    results = check_landmarks_in_pinecone(landmark_ids)

    if not results:
        print("Error: Failed to check landmarks in Pinecone")
        return

    # Calculate percentages
    total = len(landmark_ids)
    processed_count = len(results["processed"])
    unprocessed_count = len(results["unprocessed"])

    processed_percent = (processed_count / total) * 100
    unprocessed_percent = (unprocessed_count / total) * 100

    # Print results
    print("\n=== Processing Status ===")
    print(f"Total landmarks checked: {total}")
    print(f"Processed landmarks: {processed_count} ({processed_percent:.2f}%)")
    print(f"Unprocessed landmarks: {unprocessed_count} ({unprocessed_percent:.2f}%)")

    # Save results to file
    output_dir = project_root / "data" / "processing_status"
    output_dir.mkdir(exist_ok=True, parents=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"quick_check_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_landmarks_checked": total,
                "processed_count": processed_count,
                "unprocessed_count": unprocessed_count,
                "processed_percent": processed_percent,
                "unprocessed_percent": unprocessed_percent,
                "processed_landmarks": results["processed"],
                "unprocessed_landmarks": results["unprocessed"],
            },
            f,
            indent=2,
        )

    print(f"\nSaved results to {output_file}")


if __name__ == "__main__":
    main()
