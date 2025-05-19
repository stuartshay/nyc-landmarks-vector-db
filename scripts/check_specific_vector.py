#!/usr/bin/env python3
"""
Script to check metadata for a specific vector in Pinecone.

This script retrieves and displays metadata for a specific vector stored in Pinecone,
and validates that it contains all required fields based on its type.

Examples:
    # Check a specific vector by ID:
    $ python scripts/check_specific_vector.py "wiki-83_and_85_Sullivan_Street-LP-02344-chunk-0"

    # Check a Wikipedia vector to validate required fields:
    $ python scripts/check_specific_vector.py "wiki-Wyckoff_House-LP-00001-chunk-0"

    # Check a landmark report vector:
    $ python scripts/check_specific_vector.py "report-LP-00001-chunk-0"
"""

import argparse
import json

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

logger = get_logger(__name__)


def check_vector(vector_id: str) -> None:
    """Check metadata for a specific vector ID.

    This function retrieves the vector from Pinecone and checks its metadata,
    including required fields. For Wikipedia vectors, it verifies that
    article_title and article_url fields are present.

    Args:
        vector_id: The ID of the vector to check

    Returns:
        None. Results are printed to stdout.
    """
    pinecone_db = PineconeDB()

    print(f"Checking vector: {vector_id}")

    # Fetch the vector - first try to query by ID
    try:
        # Get index stats and extract dimension
        dimension = 1536  # Default dimension for OpenAI embeddings

        # Initialize found flag
        found = False

        # Query by exact ID
        query_response = pinecone_db.index.query(
            vector=[0.0] * dimension,  # Dummy vector
            filter={"id": vector_id},  # Simple filter
            top_k=1,
            include_metadata=True
        )

        # Access matches safely
        matches = []
        try:
            # Try accessing as attribute
            if hasattr(query_response, "matches"):
                matches = getattr(query_response, "matches")
            # Try accessing as dictionary
            elif isinstance(query_response, dict) and "matches" in query_response:
                matches = query_response["matches"]
        except Exception as e:
            logger.warning(f"Error accessing matches: {e}")

        if not matches:
            print(f"Vector not found using ID filter: {vector_id}")
            # Try different approach
            # Query by landmark ID extracted from vector ID
            landmark_id = None
            if "-LP-" in vector_id:
                landmark_id = vector_id.split("-LP-")[1].split("-")[0]
                landmark_id = f"LP-{landmark_id}"

            query_response = pinecone_db.index.query(
                vector=[0.0] * dimension,  # Use the dimension from earlier
                filter={"landmark_id": landmark_id, "source_type": "wikipedia"} if landmark_id else None,
                top_k=10,
                include_metadata=True
            )

            # Access matches safely
            matches = []
            try:
                # Try accessing as attribute
                if hasattr(query_response, "matches"):
                    matches = getattr(query_response, "matches")
                # Try accessing as dictionary
                elif isinstance(query_response, dict) and "matches" in query_response:
                    matches = query_response["matches"]
            except Exception as e:
                logger.warning(f"Error accessing matches: {e}")

            # Find the exact match in the response
            found = False
            vector = None
            for match in matches:
                match_id = None
                # Try to get id attribute/key
                if hasattr(match, "id"):
                    match_id = getattr(match, "id")
                elif isinstance(match, dict) and "id" in match:
                    match_id = match["id"]

                if match_id == vector_id:
                    vector = match
                    found = True
                    break

            if not found:
                print(f"Vector not found: {vector_id}")
                print(f"Found these vectors for landmark {landmark_id}:")
                for match in matches:
                    # Try to get id attribute/key
                    match_id = None
                    if hasattr(match, "id"):
                        match_id = getattr(match, "id")
                    elif isinstance(match, dict) and "id" in match:
                        match_id = match["id"]
                    print(f"  - {match_id}")
                return
        else:
            vector = matches[0]
    except Exception as e:
        print(f"Error querying vector: {e}")
        return

    # Handle metadata dynamically
    metadata = {}
    try:
        # Try accessing metadata as attribute
        if hasattr(vector, "metadata"):
            metadata = getattr(vector, "metadata")
        # Try accessing as dictionary
        elif isinstance(vector, dict) and "metadata" in vector:
            metadata = vector["metadata"]

        # Ensure metadata is a dictionary
        if not isinstance(metadata, dict):
            if hasattr(metadata, "__dict__"):
                metadata = vars(metadata)
            else:
                metadata = {"raw_value": str(metadata)}
    except Exception as e:
        print(f"Error accessing metadata: {e}")
        metadata = {}

    # Print metadata details
    print(f"Vector ID: {vector_id}")
    print(f"Metadata type: {type(metadata)}")
    print(f"Metadata keys: {list(metadata.keys()) if metadata else 'None'}")

    # Try to serialize metadata safely
    try:
        print(f"Full metadata: {json.dumps(metadata, indent=2, default=str)}")
    except Exception as e:
        print(f"Could not serialize metadata: {e}")
        print(f"Raw metadata: {metadata}")

    # Check required fields for Wikipedia vectors
    if vector_id.startswith("wiki-"):
        # Note: Testing on May 18, 2025 revealed that some Wikipedia vectors
        # were missing article_title and article_url fields, which should be
        # added by process_wikipedia_articles.py
        required_fields = ["landmark_id", "source_type", "chunk_index", "text", "article_title", "article_url"]

        # Check for missing fields
        missing = [field for field in required_fields if field not in metadata]

        if missing:
            print(f"\nMissing required Wikipedia fields: {missing}")
        else:
            print("\nAll required Wikipedia fields are present")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check metadata for a specific vector")
    parser.add_argument("vector_id", help="The ID of the vector to check")

    args = parser.parse_args()

    check_vector(args.vector_id)


if __name__ == "__main__":
    main()
