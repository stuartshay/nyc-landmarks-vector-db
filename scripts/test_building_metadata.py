#!/usr/bin/env python3
"""
Test script for the multiple buildings metadata implementation.

This script:
1. Fetches a landmark by ID using the CoreDataStore API
2. Collects enhanced metadata including all buildings and BBLs
3. Formats the data for the vector database
4. Prints the results for verification
"""

import argparse
import json
import logging
import sys
import time
import uuid

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.enhanced_metadata import EnhancedMetadataCollector
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)


def test_landmark_metadata(
    landmark_id: str, verbose: bool = False, create_vector: bool = False
):
    """
    Test the collection of metadata for a landmark, including multiple buildings.

    Args:
        landmark_id: ID of the landmark to process
        verbose: Whether to print detailed results
        create_vector: Whether to create a test vector in Pinecone
    """
    try:
        logger.info(f"Testing metadata collection for landmark: {landmark_id}")

        # Step 1: Initialize components
        api_client = CoreDataStoreAPI()
        metadata_collector = EnhancedMetadataCollector()
        pinecone_db = PineconeDB()

        # Step 2: Get landmark details
        landmark = api_client.get_landmark_by_id(landmark_id)
        if not landmark:
            logger.error(f"Landmark not found: {landmark_id}")
            return

        logger.info(f"Found landmark: {landmark['name']}")

        # Step 3: Get buildings for the landmark
        buildings = api_client.get_landmark_buildings(landmark_id)
        logger.info(f"Found {len(buildings)} buildings for this landmark")

        # Print building details if verbose
        if verbose:
            for i, building in enumerate(buildings):
                logger.info(f"Building {i+1}:")
                for key, value in building.items():
                    if value:  # Only show non-empty fields
                        logger.info(f"  {key}: {value}")

        # Step 4: Collect enhanced metadata
        enhanced_metadata = metadata_collector.collect_landmark_metadata(landmark_id)

        # Step 5: Print the enhanced metadata
        logger.info("Enhanced Metadata Structure:")
        if "buildings" in enhanced_metadata:
            logger.info(f"- Number of buildings: {len(enhanced_metadata['buildings'])}")

            # Print BBL values from buildings
            if verbose:
                for i, building in enumerate(enhanced_metadata["buildings"]):
                    bbl = building.get("bbl", "None")
                    name = building.get("name", "Unnamed")
                    address = building.get("address", "No address")
                    logger.info(f"- Building {i+1}: {name}, {address}, BBL: {bbl}")
                    # Print all properties for debugging
                    for key, value in building.items():
                        logger.info(f"    - {key}: {value}")

        # Note: We no longer have standalone all_bbls and bbl fields
        # as that information is now stored in the buildings complex object
        logger.info("- BBLs are now stored in the buildings complex object")

        # Step 6: Test how this would be formatted for Pinecone
        mock_chunk = {"text": "Test chunk", "embedding": [0.1] * 1536}
        pinecone_metadata = pinecone_db._create_metadata_for_chunk(
            chunk=mock_chunk,
            source_type="test",
            chunk_index=0,
            landmark_id=landmark_id,
            enhanced_metadata=enhanced_metadata,
        )

        # Print formatted metadata for Pinecone
        logger.info("Formatted Metadata for Pinecone:")
        if verbose:
            # Pretty print the metadata
            formatted_json = json.dumps(pinecone_metadata, indent=2)
            logger.info(f"{formatted_json}")
        else:
            # Just print the keys
            logger.info(f"- Metadata fields: {', '.join(pinecone_metadata.keys())}")

            # Look for building-related fields
            building_fields = [
                k for k in pinecone_metadata.keys() if k.startswith("building_")
            ]
            if building_fields:
                logger.info(f"- Building fields: {', '.join(building_fields)}")

            # Look for BBL fields
            bbl_fields = [k for k in pinecone_metadata.keys() if "bbl" in k.lower()]
            if bbl_fields:
                for field in bbl_fields:
                    logger.info(f"- {field}: {pinecone_metadata[field]}")

        # Step 7: (Optional) Create and upload a test vector to Pinecone
        if create_vector:
            logger.info("Creating and uploading a test vector to Pinecone...")
            test_vector_id = str(uuid.uuid4())
            # We'll use pinecone_metadata from step 6 directly
            # Use upsert method to add the test vector
            embedding_dimension = 1536  # Standard dimension for OpenAI embeddings
            pinecone_db.index.upsert(
                vectors=[
                    (test_vector_id, [0.5] * embedding_dimension, pinecone_metadata)
                ]
            )
            logger.info(f"Uploaded test vector to Pinecone with ID: {test_vector_id}")

    except Exception as e:
        logger.error(f"Error testing landmark metadata: {e}", exc_info=True)


def main() -> None:
    """Main function to run the test script."""
    parser = argparse.ArgumentParser(
        description="Test the collection of metadata for landmarks with multiple buildings"
    )
    parser.add_argument(
        "landmark_id", help="ID of the landmark to process (e.g., LP-00001)"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print detailed results"
    )
    parser.add_argument(
        "--create-vector",
        action="store_true",
        help="Create and upload a test vector to Pinecone",
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the test
    test_landmark_metadata(args.landmark_id, args.verbose, args.create_vector)


if __name__ == "__main__":
    main()
