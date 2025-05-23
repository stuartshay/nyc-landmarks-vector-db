#!/usr/bin/env python3
"""
Verify Wikipedia Vector Metadata in Pinecone

This script:
1. Lists Wikipedia vectors from Pinecone
2. Verifies if they contain the expected metadata fields
3. Reports on which metadata fields are present or missing
"""

import sys
from pathlib import Path
from typing import Dict, Set

# Add the project root to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logger
logger = get_logger(__name__)


def verify_wiki_vectors() -> bool:
    """
    Verify Wikipedia vectors in Pinecone.

    Returns:
        bool: True if verification was successful, False otherwise
    """
    # Connect to Pinecone
    pinecone_db = PineconeDB()
    if not pinecone_db.index:
        logger.error("Failed to connect to Pinecone index")
        return False

    logger.info(f"Connected to Pinecone index: {pinecone_db.index_name}")

    # Get Wikipedia vectors
    response = pinecone_db.list_vectors_by_source(source_type="wikipedia")
    if not response or "matches" not in response:
        logger.error("No Wikipedia vectors found in Pinecone")
        return False

    vectors = response.get("matches", [])
    logger.info(f"Found {len(vectors)} Wikipedia vectors")

    # Track metadata fields
    total_vectors = len(vectors)
    all_fields: Set[str] = set()
    field_counts: Dict[str, int] = {}
    landmark_ids: Set[str] = set()

    # Analyze all metadata fields present
    for vector in vectors:
        metadata = vector.get("metadata", {})

        # Track metadata fields
        for field in metadata.keys():
            all_fields.add(field)
            field_counts[field] = field_counts.get(field, 0) + 1

        # Track unique landmark IDs
        if "landmark_id" in metadata:
            landmark_ids.add(metadata["landmark_id"])

    # Report on metadata fields
    logger.info("\n===== WIKIPEDIA VECTOR METADATA ANALYSIS =====")
    logger.info(f"Total Wikipedia vectors: {total_vectors}")
    logger.info(f"Unique landmark IDs: {len(landmark_ids)}")
    logger.info(f"All metadata fields found: {', '.join(sorted(all_fields))}")

    logger.info("\nMetadata field coverage:")
    for field in sorted(all_fields):
        count = field_counts.get(field, 0)
        percentage = count / total_vectors * 100 if total_vectors else 0
        logger.info(f"- {field}: {count}/{total_vectors} vectors ({percentage:.1f}%)")

    # Check first vector as an example
    if vectors:
        sample_vector = vectors[0]
        logger.info("\nSample vector metadata:")
        logger.info(f"ID: {sample_vector.get('id', 'unknown')}")
        logger.info(f"Metadata: {sample_vector.get('metadata', {})}")

    return True


def main() -> None:
    """Main entry point for the script."""
    # Run verification
    result = verify_wiki_vectors()
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
