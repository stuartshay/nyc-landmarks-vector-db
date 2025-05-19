#!/usr/bin/env python3
"""
Script to fix metadata in Wikipedia vectors.

This script:
1. Fetches all Wikipedia vectors from Pinecone
2. Extracts article title from the vector ID
3. Adds the missing article_title and article_url metadata fields
4. Updates the vectors in Pinecone
"""

import argparse
import re
import sys
from typing import Any, Dict, List

from tqdm import tqdm

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)

# Constants
WIKI_ID_PATTERN = r"^wiki-(.+)-(LP-\d{5})-chunk-(\d+)$"


def extract_article_title(vector_id: str) -> str:
    """
    Extract the article title from a Wikipedia vector ID.

    Args:
        vector_id: The vector ID (e.g., wiki-Wyckoff_House-LP-00001-chunk-0)

    Returns:
        The article title with underscores replaced by spaces
    """
    match = re.match(WIKI_ID_PATTERN, vector_id)
    if match:
        article_title_with_underscores = match.group(1)
        return article_title_with_underscores.replace("_", " ")
    return "Unknown Article"


def generate_wikipedia_url(article_title: str) -> str:
    """
    Generate a Wikipedia URL from an article title.

    Args:
        article_title: The article title

    Returns:
        The Wikipedia URL
    """
    # Replace spaces with underscores for URL format
    url_title = article_title.replace(" ", "_")
    return f"https://en.wikipedia.org/wiki/{url_title}"


def update_wikipedia_vectors(dry_run: bool = False) -> bool:
    """
    Update Wikipedia vectors with missing metadata.

    Args:
        dry_run: If True, only print what would be done without making changes

    Returns:
        True if successful, False otherwise
    """
    # Initialize Pinecone client
    pinecone_db = PineconeDB()
    if not pinecone_db.index:
        logger.error("Failed to connect to Pinecone index")
        return False

    logger.info(f"Connected to Pinecone index: {pinecone_db.index_name}")

    # Get all Wikipedia vectors
    response = pinecone_db.list_vectors_by_source(source_type="wikipedia")
    vectors = response.get("matches", [])

    if not vectors:
        logger.info("No Wikipedia vectors found in the index")
        return True

    logger.info(f"Found {len(vectors)} Wikipedia vectors")

    # Process vectors
    vectors_to_update = []

    for vector in tqdm(vectors, desc="Processing vectors"):
        vector_id = vector.get("id", "")
        metadata = vector.get("metadata", {})

        # Skip if already has both required fields
        if "article_title" in metadata and "article_url" in metadata:
            logger.info(f"Vector {vector_id} already has article_title and article_url")
            continue

        # Extract article title from ID
        article_title = extract_article_title(vector_id)

        # Generate Wikipedia URL
        article_url = generate_wikipedia_url(article_title)

        # Create updated metadata
        updated_metadata = metadata.copy()
        updated_metadata["article_title"] = article_title
        updated_metadata["article_url"] = article_url

        # Prepare for update
        vectors_to_update.append({
            "id": vector_id,
            "metadata": updated_metadata,
            "values": vector.get("values", [])  # Keep original embeddings
        })

        logger.info(f"Will update vector {vector_id} with article_title='{article_title}'")

    # Update vectors in Pinecone
    if not vectors_to_update:
        logger.info("No vectors need updating")
        return True

    logger.info(f"Updating {len(vectors_to_update)} vectors in Pinecone")

    if dry_run:
        logger.info("DRY RUN - No changes made")
        return True

    # Process in batches to avoid API limits
    batch_size = 100
    success = True

    for i in range(0, len(vectors_to_update), batch_size):
        batch = vectors_to_update[i:i + batch_size]
        try:
            # Update vectors in Pinecone
            pinecone_db.index.upsert(vectors=batch)
            logger.info(f"Successfully updated batch {i//batch_size + 1}/{(len(vectors_to_update) + batch_size - 1)//batch_size}")
        except Exception as e:
            logger.error(f"Error updating batch {i//batch_size + 1}: {e}")
            success = False

    return success


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Fix Wikipedia vector metadata in Pinecone"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes"
    )

    args = parser.parse_args()

    # Update Wikipedia vectors
    success = update_wikipedia_vectors(args.dry_run)

    if success:
        logger.info("Successfully updated Wikipedia vector metadata")
        sys.exit(0)
    else:
        logger.error("Failed to update Wikipedia vector metadata")
        sys.exit(1)


if __name__ == "__main__":
    main()
