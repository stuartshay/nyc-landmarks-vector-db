#!/usr/bin/env python3
"""
Script to check a specific vector ID from Pinecone.


"""

import argparse
import json
from typing import Any, Dict, List, Optional

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

logger = get_logger(__name__)

# Constants
REQUIRED_METADATA = ["landmark_id", "source_type", "chunk_index", "text"]
REQUIRED_WIKI_METADATA = ["article_title", "article_url"]


def connect_to_pinecone() -> Optional[PineconeDB]:
    """Connect to Pinecone and return the DB client.

    Returns:
        PineconeDB instance or None if connection failed
    """
    pinecone_db = PineconeDB()
    if not pinecone_db.index:
        logger.error("Failed to connect to Pinecone index")
        return None

    print(f"Connected to Pinecone index: {pinecone_db.index_name}")
    return pinecone_db


def find_vector_by_id(
    pinecone_db: PineconeDB, vector_id: str
) -> Optional[Dict[str, Any]]:
    """Find a specific vector by its ID in the Wikipedia source.

    Args:
        pinecone_db: PineconeDB instance
        vector_id: ID of the vector to find

    Returns:
        Vector dictionary or None if not found
    """
    response = pinecone_db.list_vectors_by_source("wikipedia")

    if not response or "matches" not in response or not response["matches"]:
        print("No Wikipedia vectors found")
        return None

    # Find our specific vector
    for vector in response["matches"]:
        if vector.get("id") == vector_id:
            # Ensure we return a dictionary
            return dict(vector)

    print(f"Vector ID not found: {vector_id}")
    return None


def print_vector_metadata(vector: Dict[str, Any]) -> Dict[str, Any]:
    """Print vector metadata information.

    Args:
        vector: Vector dictionary

    Returns:
        The metadata dictionary
    """
    vector_id = vector.get("id", "Unknown ID")
    metadata = vector.get("metadata", {})

    print(f"\nExamining vector: {vector_id}")
    print(f"Metadata keys: {list(metadata.keys()) if metadata else 'None'}")
    print(f"Full metadata: {json.dumps(metadata, indent=2, default=str)}")

    # Ensure we return a dictionary
    return dict(metadata) if metadata else {}


def check_required_fields(metadata: Dict[str, Any]) -> List[str]:
    """Check if all required fields are present in the metadata.

    Args:
        metadata: Vector metadata

    Returns:
        List of missing fields
    """
    required_fields = REQUIRED_METADATA + REQUIRED_WIKI_METADATA
    missing_fields = [field for field in required_fields if field not in metadata]

    if missing_fields:
        print(f"\nMissing required fields: {missing_fields}")
    else:
        print("\nAll required fields are present")

    return missing_fields


def validate_article_title(vector_id: str, metadata: Dict[str, Any]) -> None:
    """Validate that the article title in the ID matches the metadata.

    Args:
        vector_id: Vector ID
        metadata: Vector metadata
    """
    if not vector_id.startswith("wiki-"):
        return

    parts = vector_id.split("-")
    if len(parts) >= 4:
        # Format is wiki-{article_title}-LP-{id}-chunk-{index}
        article_title_from_id = parts[1].replace("_", " ")
        print(f"\nArticle title extracted from ID: {article_title_from_id}")

        # Check if it matches the metadata
        if "article_title" in metadata:
            if metadata["article_title"] == article_title_from_id:
                print("✓ ID article title matches metadata article title")
            else:
                print(
                    f"✗ ID article title does not match metadata: {metadata['article_title']}"
                )


def check_wiki_vector(vector_id: str) -> None:
    """Check a Wikipedia vector for metadata completeness."""
    # Initialize Pinecone client
    pinecone_db = connect_to_pinecone()
    if not pinecone_db:
        return

    # Find the vector
    target_vector = find_vector_by_id(pinecone_db, vector_id)
    if not target_vector:
        return

    # Examine the vector metadata
    metadata = print_vector_metadata(target_vector)

    # Check required fields
    check_required_fields(metadata)

    # Validate article title
    validate_article_title(vector_id, metadata)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check metadata for a specific Wikipedia vector"
    )
    parser.add_argument(
        "vector_id",
        help="The ID of the vector to check (e.g., wiki-Wyckoff_House-LP-00001-chunk-0)",
    )

    args = parser.parse_args()
    check_wiki_vector(args.vector_id)


if __name__ == "__main__":
    main()
