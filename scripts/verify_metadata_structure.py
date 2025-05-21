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
from typing import Optional

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)


def print_vector_metadata(limit: int, match_pattern: Optional[str] = None) -> None:
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
    vectors = None
    if match_pattern and match_pattern == "wiki-":
        print("Filtering by source type: wikipedia")
        response = pinecone_db.list_vectors_by_source("wikipedia", limit)
        if response and "matches" in response:
            vectors = response["matches"]
    else:
        # Use the generic query method
        print("Using generic query method (all vectors)")
        # Create a dummy vector for querying
        vector_dimension = pinecone_db.dimensions
        zero_vector = [0.0] * vector_dimension
        vectors = pinecone_db.query_vectors(query_vector=zero_vector, top_k=limit)

    if not vectors:
        print("No vectors found in Pinecone DB.")
        return

    print(f"Retrieved {len(vectors)} vectors")

    # Analyze vectors
    for i, vector in enumerate(vectors, 1):
        # Handle vector object which could be a dict or an object with attributes
        if hasattr(vector, "get"):
            vector_id = vector.get("id", "Unknown ID")
            metadata = vector.get("metadata", {})
        else:
            # Handle case where vector might be a different object type
            vector_id = getattr(vector, "id", "Unknown ID")
            metadata = getattr(vector, "metadata", {})

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
        help="Maximum number of vectors to analyze (default: 5)",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        help="Optional pattern to filter vector IDs (e.g., 'wiki-')",
    )

    args = parser.parse_args()

    # Print metadata for vectors
    print_vector_metadata(args.limit, args.pattern)


if __name__ == "__main__":
    main()
