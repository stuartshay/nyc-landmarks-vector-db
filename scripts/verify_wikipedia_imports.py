#!/usr/bin/env python3
"""
Script to verify Wikipedia article imports in the Pinecone vector database.

This script queries the Pinecone database to verify that Wikipedia articles
have been correctly imported and stored with proper metadata.
"""

import argparse
import logging
from typing import Dict, List, Optional

import pandas as pd

from nyc_landmarks.config.settings import settings
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL.value,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def list_wikipedia_vectors(
    landmark_id: Optional[str] = None, limit: int = 100
) -> List[Dict]:
    """
    List vectors in Pinecone with source_type=wikipedia.

    Args:
        landmark_id: Optional landmark ID to filter by
        limit: Maximum number of vectors to return

    Returns:
        List of vectors with metadata
    """
    # Initialize Pinecone client
    pinecone_db = PineconeDB()

    # Build filter dictionary
    filter_dict = {"source_type": "wikipedia"}
    if landmark_id:
        filter_dict["landmark_id"] = landmark_id

    # Get index stats to check total vector count
    stats = pinecone_db.get_index_stats()
    total_wikipedia_vectors = 0

    try:
        # Try to extract Wikipedia vector count from namespaces
        namespaces = stats.get("namespaces", {})
        for ns_name, ns_data in namespaces.items():
            # Check if we have filter data by metadata
            metadata_counts = ns_data.get("vector_count", 0)
            if metadata_counts:
                total_wikipedia_vectors += metadata_counts
                logger.info(f"Found {metadata_counts} vectors in namespace {ns_name}")
    except (KeyError, AttributeError) as e:
        logger.warning(f"Could not parse metadata counts: {e}")

    logger.info(
        f"Total vectors in Pinecone index: {stats.get('total_vector_count', 0)}"
    )

    # Now let's query for actual vectors with the Wikipedia filter
    # We'll use a dummy query vector of all zeros just to get the metadata
    dummy_vector = [0.0] * pinecone_db.dimensions

    results = pinecone_db.query_vectors(
        dummy_vector, top_k=limit, filter_dict=filter_dict
    )

    if not results:
        logger.warning("No Wikipedia vectors found in query results")
        return []

    logger.info(f"Retrieved {len(results)} Wikipedia vectors")
    return results


def validate_wikipedia_vectors(vectors: List[Dict]) -> bool:  # noqa: C901
    """
    Validate that Wikipedia vectors have the correct metadata structure.

    Args:
        vectors: List of vectors with metadata to validate

    Returns:
        True if all vectors are valid, False otherwise
    """
    if not vectors:
        logger.warning("No vectors to validate")
        return False

    all_valid = True
    required_metadata = {
        "source_type": "wikipedia",
        "article_title": str,
        "article_url": str,
        "landmark_id": str,
    }

    for i, vector in enumerate(vectors):
        vector_id = vector.get("id", f"unknown-{i}")
        metadata = vector.get("metadata", {})

        logger.info(f"Validating vector {vector_id}")

        # Check that the vector ID starts with "wiki-"
        if not vector_id.startswith("wiki-"):
            logger.warning(f"Vector {vector_id} does not have the 'wiki-' prefix")
            all_valid = False

        # Check required metadata fields
        for field, expected_type in required_metadata.items():
            if field not in metadata:
                logger.warning(f"Vector {vector_id} is missing required field: {field}")
                all_valid = False
                continue

            value = metadata[field]
            if field == "source_type":
                if value != "wikipedia":
                    logger.warning(
                        f"Vector {vector_id} has incorrect source_type: {value}"
                    )
                    all_valid = False
            # Skip type checking for source_type as it's checked explicitly above
            elif field != "source_type":
                # Instead of using isinstance directly with a variable type,
                # we handle each type explicitly to avoid mypy errors
                if field == "article_title" and not isinstance(value, str):
                    logger.warning(
                        f"Vector {vector_id} field {field} is not a string: {type(value)}"
                    )
                    all_valid = False
                elif field == "article_url" and not isinstance(value, str):
                    logger.warning(
                        f"Vector {vector_id} field {field} is not a string: {type(value)}"
                    )
                    all_valid = False
                elif field == "landmark_id" and not isinstance(value, str):
                    logger.warning(
                        f"Vector {vector_id} field {field} is not a string: {type(value)}"
                    )
                    all_valid = False

        # Check that the text field is present and not empty
        if "text" not in metadata or not metadata["text"]:
            logger.warning(f"Vector {vector_id} is missing text content")
            all_valid = False

    if all_valid:
        logger.info("All vectors have valid metadata structure")
    else:
        logger.warning("Some vectors have invalid metadata structure")

    return all_valid


def summarize_wikipedia_vectors(vectors: List[Dict]) -> None:
    """
    Summarize the Wikipedia vectors by landmark and article.

    Args:
        vectors: List of vectors with metadata to summarize
    """
    if not vectors:
        logger.warning("No vectors to summarize")
        return

    # Extract key information for summary
    data = []
    for vector in vectors:
        metadata = vector.get("metadata", {})

        data.append(
            {
                "vector_id": vector.get("id", "unknown"),
                "landmark_id": metadata.get("landmark_id", "unknown"),
                "article_title": metadata.get("article_title", "unknown"),
                "text_length": len(metadata.get("text", "")),
                "score": vector.get("score", 0.0),
            }
        )

    # Create and display a DataFrame
    df = pd.DataFrame(data)

    # Group by landmark and article
    summary = (
        df.groupby(["landmark_id", "article_title"])
        .agg(
            {
                "vector_id": "count",
                "text_length": ["mean", "min", "max"],
            }
        )
        .reset_index()
    )

    # Rename columns for clarity
    summary.columns = [
        "Landmark ID",
        "Article Title",
        "Vector Count",
        "Avg Text Length",
        "Min Text Length",
        "Max Text Length",
    ]

    print("\nWikipedia Vector Summary:")
    print(summary)

    # Also show the number of vectors per landmark
    landmark_summary = df.groupby("landmark_id")["vector_id"].count().reset_index()
    landmark_summary.columns = ["Landmark ID", "Vector Count"]

    print("\nVectors per Landmark:")
    print(landmark_summary)


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Verify Wikipedia article imports in the Pinecone vector database"
    )
    parser.add_argument(
        "--landmark-id",
        help="Verify a specific landmark ID (e.g., LP-00001)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of vectors to retrieve for verification",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Display verbose output",
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    # List Wikipedia vectors
    vectors = list_wikipedia_vectors(
        landmark_id=args.landmark_id,
        limit=args.limit,
    )

    if not vectors:
        print("No Wikipedia vectors found in Pinecone")
        return

    print(f"Found {len(vectors)} Wikipedia vectors in Pinecone")

    # Validate the vectors
    is_valid = validate_wikipedia_vectors(vectors)

    if is_valid:
        print("All Wikipedia vectors have valid metadata structure")
    else:
        print("Some Wikipedia vectors have invalid metadata structure")

    # Summarize the vectors
    summarize_wikipedia_vectors(vectors)


if __name__ == "__main__":
    main()
