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
import sys

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)


def check_metadata():
    """
    Examine the metadata of vectors in the Pinecone index.
    """
    print("Examining vectors in Pinecone...")

    # Initialize Pinecone
    pinecone_db = PineconeDB()

    # Get all vectors with source_type=wikipedia
    response = pinecone_db.list_vectors_by_source("wikipedia")

    if not response or "matches" not in response or not response["matches"]:
        print("No Wikipedia vectors found in Pinecone.")
        return

    vectors = response["matches"]
    print(f"Found {len(vectors)} Wikipedia vectors")

    # Check first few vectors
    for i, vector in enumerate(vectors[:3], 1):
        vector_id = vector.get("id", "Unknown ID")
        metadata = vector.get("metadata", {})

        print(f"\n{i}. Vector ID: {vector_id}")
        print(f"   Metadata keys: {list(metadata.keys()) if metadata else 'None'}")
        print(f"   Full metadata: {json.dumps(metadata, indent=2, default=str)}")

    # Count metadata fields
    field_counts = {}
    for vector in vectors:
        metadata = vector.get("metadata", {})
        for key in metadata.keys():
            field_counts[key] = field_counts.get(key, 0) + 1

    print("\nMetadata field counts:")
    for field, count in sorted(field_counts.items()):
        print(
            f"- {field}: {count}/{len(vectors)} vectors ({count/len(vectors)*100:.1f}%)"
        )

    # Check for article_title and article_url
    missing_article_title = sum(
        1 for v in vectors if "article_title" not in v.get("metadata", {})
    )
    missing_article_url = sum(
        1 for v in vectors if "article_url" not in v.get("metadata", {})
    )

    print(f"\nMissing article_title: {missing_article_title}/{len(vectors)}")
    print(f"Missing article_url: {missing_article_url}/{len(vectors)}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Verify vector metadata structure in Pinecone"
    )

    args = parser.parse_args()

    # Check metadata
    check_metadata()


if __name__ == "__main__":
    main()
