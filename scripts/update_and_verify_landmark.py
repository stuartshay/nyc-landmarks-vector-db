#!/usr/bin/env python3
"""
Script to update a specific landmark and verify the results.

This script:
1. Fetches a landmark by ID
2. Processes its enhanced metadata
3. Creates a test vector with the metadata
4. Uploads it to Pinecone
5. Retrieves the vector to verify that the changes were applied correctly

Usage:
    python scripts/update_and_verify_landmark.py LP-00009
"""

import argparse
import json
import time
from typing import Any, Dict

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.enhanced_metadata import EnhancedMetadataCollector
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)


def update_and_verify_landmark(landmark_id: str, verbose: bool = False) -> None:
    """
    Update a landmark in the vector database and verify the results.

    Args:
        landmark_id: ID of the landmark to process
        verbose: Whether to print detailed results
    """
    try:
        logger.info(f"Processing landmark: {landmark_id}")

        # Step 1: Initialize components
        db_client = get_db_client()
        metadata_collector = EnhancedMetadataCollector()
        pinecone_db = PineconeDB()

        # Step 2: Get landmark details
        landmark = db_client.get_landmark_by_id(landmark_id)
        if not landmark:
            logger.error(f"Landmark not found: {landmark_id}")
            return

        if isinstance(landmark, dict):
            landmark_name = landmark.get("name")
        else:
            landmark_name = getattr(landmark, "name", "")

        logger.info(f"Found landmark: {landmark_name}")

        # Step 3: Collect enhanced metadata
        enhanced_metadata = metadata_collector.collect_landmark_metadata(landmark_id)

        # Step 4: Create a test vector
        test_vector_id = f"test-{landmark_id}-update-{int(time.time())}"
        logger.info(f"Creating test vector with ID: {test_vector_id}")

        mock_chunk = {
            "text": f"Test chunk for {landmark_name}",
            "embedding": [0.1] * settings.EMBEDDING_DIMENSION,
        }

        metadata = pinecone_db._create_metadata_for_chunk(
            chunk=mock_chunk,
            source_type="test",
            chunk_index=0,
            landmark_id=landmark_id,
            enhanced_metadata=enhanced_metadata,
        )

        # Step 5: Upload test vector
        pinecone_db.upsert_vector(
            vector_id=test_vector_id, vector=mock_chunk["embedding"], metadata=metadata
        )
        logger.info(f"Uploaded test vector to Pinecone")

        # Step 6: Verify the results
        logger.info("Waiting a moment for indexing...")
        time.sleep(1)

        # Query the vector to verify
        verify_vector(test_vector_id, verbose)

        logger.info("Update and verification complete")

    except Exception as e:
        logger.error(f"Error updating and verifying landmark: {e}", exc_info=True)


def verify_vector(vector_id: str, verbose: bool = False) -> None:
    """Check metadata for a specific vector ID to verify the update.

    Args:
        vector_id: The ID of the vector to check
        verbose: Whether to print detailed results
    """
    pinecone_db = PineconeDB()

    logger.info(f"Verifying vector: {vector_id}")

    # Get index stats and extract dimension
    dimension = settings.EMBEDDING_DIMENSION

    # Query by exact ID
    query_response = pinecone_db.index.query(
        vector=[0.0] * dimension,  # Dummy vector
        filter={"id": vector_id},
        top_k=1,
        include_metadata=True,
    )

    # Access matches safely
    matches = []
    try:
        if hasattr(query_response, "matches"):
            matches = getattr(query_response, "matches")
        elif isinstance(query_response, dict) and "matches" in query_response:
            matches = query_response["matches"]
    except Exception as e:
        logger.warning(f"Error accessing matches: {e}")

    if not matches:
        logger.error(f"Vector not found: {vector_id}")
        return

    vector = matches[0]

    # Handle metadata dynamically
    metadata = {}
    try:
        if hasattr(vector, "metadata"):
            metadata = getattr(vector, "metadata")
        elif isinstance(vector, dict) and "metadata" in vector:
            metadata = vector["metadata"]
    except Exception as e:
        logger.error(f"Error accessing metadata: {e}")

    # Print metadata details
    logger.info(f"Vector ID: {vector_id}")

    # Check for BBL-related fields
    logger.info("Checking BBL-related fields:")

    # Check if buildings are present in the metadata
    if "buildings" in metadata:
        logger.error(
            "Unexpected 'buildings' field found in metadata - complex objects should be flattened"
        )

    # Check if standalone BBL fields are present
    bbl_fields = ["bbl", "all_bbls"]
    for field in bbl_fields:
        if field in metadata:
            logger.error(
                f"Deprecated standalone field '{field}' found in metadata: {metadata[field]}"
            )

    # Check for building structure
    building_fields = [k for k in metadata.keys() if k.startswith("building_")]
    if building_fields:
        logger.info(f"Found {len(building_fields)} building-related fields")

        # Extract building count
        building_count = metadata.get("building_count", 0)
        logger.info(f"Building count: {building_count}")

        # Extract BBLs from building fields
        bbls = []
        for i in range(building_count):
            bbl_field = f"building_{i}_bbl"
            if bbl_field in metadata:
                bbls.append(metadata[bbl_field])

        logger.info(f"BBLs from buildings: {bbls}")

    # Print full metadata if verbose
    if verbose:
        try:
            logger.info(
                f"Full metadata:\n{json.dumps(metadata, indent=2, default=str)}"
            )
        except Exception as e:
            logger.error(f"Could not serialize metadata: {e}")
            logger.info(f"Raw metadata: {metadata}")


def main() -> None:
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description="Update a landmark and verify the results"
    )
    parser.add_argument(
        "landmark_id", help="ID of the landmark to process (e.g., LP-00009)"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print detailed results"
    )

    args = parser.parse_args()

    # Run the update and verification
    update_and_verify_landmark(args.landmark_id, args.verbose)


if __name__ == "__main__":
    main()
