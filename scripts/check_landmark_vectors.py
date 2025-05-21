#!/usr/bin/env python3
"""
Script to check all vectors in Pinecone for a specific landmark.

This script retrieves and displays all vectors stored in Pinecone for a given landmark ID,
and validates that they contain all required fields.

Examples:
    # Check all vectors for a specific landmark:
    $ python scripts/check_landmark_vectors.py LP-00009
"""

import argparse
import json

from nyc_landmarks.config.settings import settings
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

logger = get_logger(__name__)


def check_landmark_vectors(landmark_id: str, verbose: bool = False) -> None:
    """Check all vectors for a specific landmark.

    Args:
        landmark_id: The ID of the landmark to check
        verbose: Whether to print full metadata details
    """
    pinecone_db = PineconeDB()

    print(f"Checking vectors for landmark: {landmark_id}")

    # Use a dimension of 1536 for OpenAI embeddings
    dimension = settings.OPENAI_EMBEDDING_DIMENSIONS

    # Query all vectors for this landmark
    query_response = pinecone_db.index.query(
        vector=[0.0] * dimension,  # Dummy vector
        filter={"landmark_id": landmark_id},
        top_k=100,  # Increase if neede
        include_metadata=True,
    )

    # Access matches safely
    matches = []
    if hasattr(query_response, "matches"):
        matches = getattr(query_response, "matches")
    elif isinstance(query_response, dict) and "matches" in query_response:
        matches = query_response["matches"]

    print(f"Found {len(matches)} vectors for landmark {landmark_id}")

    if not matches:
        print("No vectors found.")
        return

    # Process each match
    for i, match in enumerate(matches):
        # Get vector ID
        vector_id = match.id if hasattr(match, "id") else match.get("id", "unknown")

        print(f"\nVector {i+1}: {vector_id}")

        # Get metadata
        metadata = {}
        if hasattr(match, "metadata"):
            metadata = match.metadata
        elif isinstance(match, dict) and "metadata" in match:
            metadata = match["metadata"]

        # Check for BBL fields
        if "bbl" in metadata:
            print(
                f"WARNING: Deprecated standalone field 'bbl' found: {metadata['bbl']}"
            )

        if "all_bbls" in metadata:
            print(
                f"WARNING: Deprecated standalone field 'all_bbls' found: {metadata['all_bbls']}"
            )

        # Check for building-related fields
        building_fields = [k for k in metadata.keys() if k.startswith("building_")]
        if building_fields:
            building_count = metadata.get("building_count", 0)
            print(f"Building count: {building_count}")

            # Find all building BBLs
            building_bbls = []
            for i in range(building_count):
                bbl_field = f"building_{i}_bbl"
                if bbl_field in metadata:
                    building_bbls.append(metadata[bbl_field])

            if building_bbls:
                print(f"Building BBLs: {building_bbls}")
            else:
                print("No building BBLs found")
        else:
            print("No building data found")

        # Print full metadata if verbose
        if verbose:
            print("\nFull metadata:")
            try:
                print(json.dumps(metadata, indent=2, default=str))
            except Exception as e:
                print(f"Error serializing metadata: {e}")
                print(f"Raw metadata: {metadata}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check all vectors for a specific landmark"
    )
    parser.add_argument("landmark_id", help="The ID of the landmark to check")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print full metadata details"
    )

    args = parser.parse_args()

    check_landmark_vectors(args.landmark_id, args.verbose)


if __name__ == "__main__":
    main()
