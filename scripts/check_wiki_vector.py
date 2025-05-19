#!/usr/bin/env python3
"""
Script to check a specific vector ID from Pinecone.
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

logger = get_logger(__name__)

# Constants
REQUIRED_METADATA = ["landmark_id", "source_type", "chunk_index", "text"]
REQUIRED_WIKI_METADATA = ["article_title", "article_url"]


def check_wiki_vector(vector_id: str) -> None:
    """Check a Wikipedia vector for metadata completeness."""
    # Initialize Pinecone client
    pinecone_db = PineconeDB()
    if not pinecone_db.index:
        logger.error("Failed to connect to Pinecone index")
        return

    print(f"Connected to Pinecone index: {pinecone_db.index_name}")

    # Get vectors by source type
    response = pinecone_db.list_vectors_by_source("wikipedia")

    if not response or "matches" not in response or not response["matches"]:
        print("No Wikipedia vectors found")
        return

    # Find our specific vector
    target_vector = None
    for vector in response["matches"]:
        if vector.get("id") == vector_id:
            target_vector = vector
            break

    if not target_vector:
        print(f"Vector ID not found: {vector_id}")
        return

    # Examine the vector
    vector_id = target_vector.get("id", "Unknown ID")
    metadata = target_vector.get("metadata", {})

    print(f"\nExamining vector: {vector_id}")
    print(f"Metadata keys: {list(metadata.keys()) if metadata else 'None'}")
    print(f"Full metadata: {json.dumps(metadata, indent=2, default=str)}")

    # Check required fields
    required_fields = REQUIRED_METADATA + REQUIRED_WIKI_METADATA
    missing_fields = [field for field in required_fields if field not in metadata]

    if missing_fields:
        print(f"\nMissing required fields: {missing_fields}")
    else:
        print("\nAll required fields are present")

    # Check if article title and URL can be extracted from the ID
    if vector_id.startswith("wiki-"):
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
                    print(f"✗ ID article title does not match metadata: {metadata['article_title']}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check metadata for a specific Wikipedia vector"
    )
    parser.add_argument(
        "vector_id", help="The ID of the vector to check (e.g., wiki-Wyckoff_House-LP-00001-chunk-0)"
    )

    args = parser.parse_args()
    check_wiki_vector(args.vector_id)


if __name__ == "__main__":
    main()
