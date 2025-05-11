#!/usr/bin/env python3
"""
Verify Pinecone Vector Integrity

This script verifies the integrity of vectors in the Pinecone index after rebuilding.
It checks for:
1. Total vector count
2. Valid non-zero embeddings
3. Standardized vector ID formats
4. Required metadata fields

Usage:
    python scripts/verify_vectors.py
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np

# Add the project root to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logger
logger = get_logger(__name__)

# Constants
PDF_ID_PATTERN = r"^(LP-\d{5})-chunk-(\d+)$"
WIKI_ID_PATTERN = r"^wiki-(.+)-(LP-\d{5})-chunk-(\d+)$"
REQUIRED_METADATA = ["landmark_id", "source_type", "chunk_index", "text"]
REQUIRED_WIKI_METADATA = ["article_title", "article_url"]


def _verify_id_format(vector_id: str, source_type: str, landmark_id: str) -> bool:
    """
    Verify that a vector ID follows the correct format.

    Args:
        vector_id: The vector ID to verify
        source_type: The source type (wikipedia or pdf)
        landmark_id: The landmark ID

    Returns:
        bool: True if the ID format is valid, False otherwise
    """
    if source_type == "wikipedia":
        # Should match pattern: wiki-{article_title}-{landmark_id}-chunk-{chunk_index}
        match = re.match(WIKI_ID_PATTERN, vector_id)
        return match is not None and landmark_id in vector_id
    else:
        # Should match pattern: {landmark_id}-chunk-{chunk_index}
        match = re.match(PDF_ID_PATTERN, vector_id)
        return match is not None and vector_id.startswith(landmark_id)


def _check_vector_has_embeddings(vector: Dict[str, Any]) -> bool:
    """
    Check if a vector has valid (non-zero) embeddings.

    Args:
        vector: The vector to check

    Returns:
        bool: True if the vector has valid embeddings, False otherwise
    """
    if "values" not in vector:
        logger.warning(f"Vector {vector.get('id', 'unknown')} has no embeddings")
        return False

    values = vector.get("values", [])
    if not values:
        logger.warning(
            f"Vector {vector.get('id', 'unknown')} has empty embeddings array"
        )
        return False

    # Check if embeddings are all zeros
    if np.allclose(np.array(values), 0):
        logger.warning(f"Vector {vector.get('id', 'unknown')} has all-zero embeddings")
        return False

    return True


def _check_metadata_fields(vector: Dict[str, Any], source_type: str) -> bool:
    """
    Check if a vector has all required metadata fields.

    Args:
        vector: The vector to check
        source_type: The source type (wikipedia or pdf)

    Returns:
        bool: True if all required metadata fields are present, False otherwise
    """
    metadata = vector.get("metadata", {})

    # Check common required fields
    for field in REQUIRED_METADATA:
        if field not in metadata:
            logger.warning(
                f"Vector {vector.get('id', 'unknown')} missing required metadata field: {field}"
            )
            return False

    # Check Wikipedia-specific fields
    if source_type == "wikipedia":
        for field in REQUIRED_WIKI_METADATA:
            if field not in metadata:
                logger.warning(
                    f"Wikipedia vector {vector.get('id', 'unknown')} missing field: {field}"
                )
                return False

    return True


def verify_sample_vectors(
    pinecone_db: PineconeDB, source_type: str, limit: int = 100
) -> Tuple[int, int, int, int]:
    """
    Verify a sample of vectors from the specified source type.

    Args:
        pinecone_db: PineconeDB instance
        source_type: Source type to sample (wikipedia or pdf)
        limit: Maximum number of vectors to sample

    Returns:
        Tuple containing counts of total vectors checked, valid ID format, valid embeddings, valid metadata
    """
    # Get a sample of vectors by source type
    response = pinecone_db.list_vectors_by_source(source_type=source_type, limit=limit)
    vectors = response.get("matches", [])

    logger.info(f"Sampling {len(vectors)} vectors from source type: {source_type}")

    # Statistics
    total_checked = len(vectors)
    valid_id_format = 0
    valid_embeddings = 0
    valid_metadata = 0

    landmark_ids = set()

    for vector in vectors:
        vector_id = vector.get("id", "")
        metadata = vector.get("metadata", {})
        landmark_id = metadata.get("landmark_id", "")

        if landmark_id:
            landmark_ids.add(landmark_id)

        # Check ID format
        if _verify_id_format(vector_id, source_type, landmark_id):
            valid_id_format += 1

        # Check embeddings
        if _check_vector_has_embeddings(vector):
            valid_embeddings += 1

        # Check metadata
        if _check_metadata_fields(vector, source_type):
            valid_metadata += 1

    logger.info(f"Found {len(landmark_ids)} unique landmark IDs in sample")

    return total_checked, valid_id_format, valid_embeddings, valid_metadata


def verify_index_integrity(verbose: bool = False) -> bool:
    """
    Verify the integrity of the Pinecone index.

    Args:
        verbose: Whether to print verbose output

    Returns:
        bool: True if the index passes all integrity checks, False otherwise
    """
    # Initialize Pinecone client
    pinecone_db = PineconeDB()
    if not pinecone_db.index:
        logger.error("Failed to connect to Pinecone index")
        return False

    logger.info(f"Connected to Pinecone index: {pinecone_db.index_name}")

    # Get index statistics
    stats = pinecone_db.get_index_stats()
    total_vectors = stats.get("total_vector_count", 0)
    dimension = stats.get("dimension", 0)

    logger.info(f"Index contains {total_vectors} vectors with dimension {dimension}")

    if total_vectors == 0:
        logger.error("Index is empty - no vectors to verify")
        return False

    # Verify PDF vectors
    pdf_checked, pdf_id_valid, pdf_embeddings_valid, pdf_metadata_valid = (
        verify_sample_vectors(pinecone_db, "pdf", limit=100)
    )

    # Verify Wikipedia vectors
    wiki_checked, wiki_id_valid, wiki_embeddings_valid, wiki_metadata_valid = (
        verify_sample_vectors(pinecone_db, "wikipedia", limit=100)
    )

    # Calculate overall statistics
    total_checked = pdf_checked + wiki_checked
    total_id_valid = pdf_id_valid + wiki_id_valid
    total_embeddings_valid = pdf_embeddings_valid + wiki_embeddings_valid
    total_metadata_valid = pdf_metadata_valid + wiki_metadata_valid

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("VECTOR VERIFICATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total vectors in index: {total_vectors}")
    logger.info(f"Vectors checked: {total_checked}")
    logger.info(
        f"Valid ID format: {total_id_valid}/{total_checked} ({total_id_valid / total_checked * 100:.2f}%)"
    )
    logger.info(
        f"Valid embeddings: {total_embeddings_valid}/{total_checked} ({total_embeddings_valid / total_checked * 100:.2f}%)"
    )
    logger.info(
        f"Valid metadata: {total_metadata_valid}/{total_checked} ({total_metadata_valid / total_checked * 100:.2f}%)"
    )
    logger.info("\nPDF Vectors:")
    logger.info(f"  Checked: {pdf_checked}")
    logger.info(
        f"  Valid ID format: {pdf_id_valid}/{pdf_checked} ({pdf_id_valid / pdf_checked * 100 if pdf_checked else 0:.2f}%)"
    )
    logger.info(
        f"  Valid embeddings: {pdf_embeddings_valid}/{pdf_checked} ({pdf_embeddings_valid / pdf_checked * 100 if pdf_checked else 0:.2f}%)"
    )
    logger.info(
        f"  Valid metadata: {pdf_metadata_valid}/{pdf_checked} ({pdf_metadata_valid / pdf_checked * 100 if pdf_checked else 0:.2f}%)"
    )
    logger.info("\nWikipedia Vectors:")
    logger.info(f"  Checked: {wiki_checked}")
    logger.info(
        f"  Valid ID format: {wiki_id_valid}/{wiki_checked} ({wiki_id_valid / wiki_checked * 100 if wiki_checked else 0:.2f}%)"
    )
    logger.info(
        f"  Valid embeddings: {wiki_embeddings_valid}/{wiki_checked} ({wiki_embeddings_valid / wiki_checked * 100 if wiki_checked else 0:.2f}%)"
    )
    logger.info(
        f"  Valid metadata: {wiki_metadata_valid}/{wiki_checked} ({wiki_metadata_valid / wiki_checked * 100 if wiki_checked else 0:.2f}%)"
    )
    logger.info("=" * 60)

    # Determine overall success (at least 95% valid in each category)
    success = (
        (
            total_id_valid / total_checked >= 0.95
            and total_embeddings_valid / total_checked >= 0.95
            and total_metadata_valid / total_checked >= 0.95
        )
        if total_checked > 0
        else False
    )

    if success:
        logger.info(
            "\n✅ Vector verification PASSED! The index appears to be in good shape."
        )
    else:
        logger.error(
            "\n❌ Vector verification FAILED! The index has issues that need to be addressed."
        )

    return success


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Verify the integrity of vectors in the Pinecone index"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Verify index integrity
    success = verify_index_integrity(args.verbose)

    # Return appropriate exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
