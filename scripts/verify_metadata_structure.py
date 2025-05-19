#!/usr/bin/env python3
"""
Script to verify the structure of vector metadata in Pinecone.

This script:
1. Queries Pinecone DB to retrieve Wikipedia vectors
2. Prints detailed information about the metadata structure
3. Helps diagnose metadata issues
"""

import argparse
import json

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)


def print_vector_metadata(limit: int, match_pattern: str = None):
    """
    Print detailed metadata for vectors in Pinecone.

    Args:
        limit: Maximum number of vectors to retrieve
        match_pattern: Optional filter for vector IDs
    """
    print(f"Retrieving up to {limit} vectors from Pinecone...")

    # Initialize Pinecone
    pinecone_db = PineconeDB()

    # Query vectors
    response = None
    if match_pattern and match_pattern == "wiki-":
        print("Filtering by source type: wikipedia")
        response = pinecone_db.list_vectors_by_source("wikipedia", limit)
    else:
        # Use the generic query method
        print("Using generic query method (all vectors)")
        response = pinecone_db.query_vectors({}, limit=limit, include_metadata=True)

    if not response or "matches" not in response or not response["matches"]:
        print("No vectors found in Pinecone DB.")
        return

    vectors = response["matches"]
    print(f"Retrieved {len(vectors)} vectors")

    # Analyze vectors
    for i, vector in enumerate(vectors, 1):
        vector_id = vector.get("id", "Unknown ID")
        metadata = vector.get("metadata", {})

        print(f"\n{i}. Vector ID: {vector_id}")
        print(f"   Metadata type: {type(metadata)}")
        print(f"   Metadata keys: {list(metadata.keys()) if metadata else 'None'}")
        print(f"   Full metadata: {json.dumps(metadata, indent=2, default=str)}")


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Verify vector metadata structure in Pinecone"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of vectors to analyze (default: 5)"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        help="Optional pattern to filter vector IDs (e.g., 'wiki-')"
    )

    args = parser.parse_args()

    # Print metadata for vectors
    print_vector_metadata(args.limit, args.pattern)


if __name__ == "__main__":
    main()
