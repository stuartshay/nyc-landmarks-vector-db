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
import uuid
from typing import Any, Dict, List, Optional, Tuple

from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI
from nyc_landmarks.models.landmark_models import LandmarkMetadata
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.enhanced_metadata import EnhancedMetadataCollector
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)


def initialize_components() -> (
    Tuple[CoreDataStoreAPI, EnhancedMetadataCollector, PineconeDB]
):
    """Initialize API client, metadata collector, and Pinecone DB."""
    api_client = CoreDataStoreAPI()
    metadata_collector = EnhancedMetadataCollector()
    pinecone_db = PineconeDB()
    return api_client, metadata_collector, pinecone_db


def get_landmark_info(
    api_client: CoreDataStoreAPI, landmark_id: str
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Retrieve landmark information and buildings from the API."""
    # Get landmark details
    landmark = api_client.get_landmark_by_id(landmark_id)
    if not landmark:
        logger.error(f"Landmark not found: {landmark_id}")
        return None, []

    logger.info(f"Found landmark: {landmark['name']}")

    # Get buildings for the landmark
    buildings = api_client.get_landmark_buildings(landmark_id)
    logger.info(f"Found {len(buildings)} buildings for this landmark")

    return landmark, buildings


def print_building_details(buildings: List[Dict[str, Any]], verbose: bool) -> None:
    """Print detailed information about buildings if verbose mode is enabled."""
    if verbose:
        for i, building in enumerate(buildings):
            logger.info(f"Building {i + 1}:")
            for key, value in building.items():
                if value:  # Only show non-empty fields
                    logger.info(f"  {key}: {value}")


def print_enhanced_metadata(enhanced_metadata: LandmarkMetadata, verbose: bool) -> None:
    """Print information about enhanced metadata structure."""
    logger.info("Enhanced Metadata Structure:")
    if "buildings" in enhanced_metadata:
        logger.info(f"- Number of buildings: {len(enhanced_metadata['buildings'])}")

        # Print BBL values from buildings
        if verbose:
            for i, building in enumerate(enhanced_metadata["buildings"]):
                bbl = building.get("bbl", "None")
                name = building.get("name", "Unnamed")
                address = building.get("address", "No address")
                logger.info(f"- Building {i + 1}: {name}, {address}, BBL: {bbl}")
                # Print all properties for debugging
                for key, value in building.items():
                    logger.info(f"    - {key}: {value}")

    # Note: We no longer have standalone all_bbls and bbl fields
    # as that information is now stored in the buildings complex object
    logger.info("- BBLs are now stored in the buildings complex object")


def convert_enhanced_metadata_to_dict(
    enhanced_metadata: LandmarkMetadata,
) -> Dict[str, Any]:
    """Convert enhanced metadata to dictionary format."""
    if hasattr(enhanced_metadata, "model_dump"):
        return dict(enhanced_metadata.model_dump())
    elif hasattr(enhanced_metadata, "dict"):
        return dict(enhanced_metadata.dict())
    else:
        # Handle edge cases to ensure Dict[str, Any] return type
        if isinstance(enhanced_metadata, dict):
            return dict(enhanced_metadata)
        else:
            try:
                return dict(enhanced_metadata)
            except (TypeError, ValueError):
                logger.warning(
                    "Could not convert enhanced_metadata to dict, returning empty dict"
                )
                return {}


def create_pinecone_metadata(
    pinecone_db: PineconeDB, landmark_id: str, enhanced_metadata_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Create metadata for Pinecone from enhanced metadata."""
    mock_chunk = {"text": "Test chunk", "embedding": [0.1] * 1536}

    return pinecone_db._create_metadata_for_chunk(
        chunk=mock_chunk,
        source_type="test",
        chunk_index=0,
        landmark_id=landmark_id,
        enhanced_metadata=enhanced_metadata_dict,
    )


def print_pinecone_metadata(pinecone_metadata: Dict[str, Any], verbose: bool) -> None:
    """Print formatted metadata for Pinecone."""
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


def create_and_upload_test_vector(
    pinecone_db: PineconeDB, pinecone_metadata: Dict[str, Any]
) -> str:
    """Create and upload a test vector to Pinecone."""
    logger.info("Creating and uploading a test vector to Pinecone...")
    test_vector_id = str(uuid.uuid4())
    embedding_dimension = 1536  # Standard dimension for OpenAI embeddings

    # Format the vector as expected by Pinecone SDK
    vectors_to_upsert = [
        {
            "id": test_vector_id,
            "values": [0.5] * embedding_dimension,
            "metadata": pinecone_metadata,
        }
    ]

    pinecone_db.index.upsert(vectors=vectors_to_upsert)
    logger.info(f"Uploaded test vector to Pinecone with ID: {test_vector_id}")

    return test_vector_id


def test_landmark_metadata(
    landmark_id: str, verbose: bool = False, create_vector: bool = False
) -> None:
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
        api_client, metadata_collector, pinecone_db = initialize_components()

        # Step 2: Get landmark details and buildings
        landmark, buildings = get_landmark_info(api_client, landmark_id)
        if not landmark:
            return  # Exit if landmark not found

        # Step 3: Print building details if verbose
        print_building_details(buildings, verbose)

        # Step 4: Collect enhanced metadata
        enhanced_metadata = metadata_collector.collect_landmark_metadata(landmark_id)

        # Step 5: Print the enhanced metadata
        print_enhanced_metadata(enhanced_metadata, verbose)

        # Step 6: Test how this would be formatted for Pinecone
        # Convert enhanced_metadata to dict for compatibility
        enhanced_metadata_dict = convert_enhanced_metadata_to_dict(enhanced_metadata)

        # Create metadata for Pinecone
        pinecone_metadata = create_pinecone_metadata(
            pinecone_db, landmark_id, enhanced_metadata_dict
        )

        # Print formatted metadata for Pinecone
        print_pinecone_metadata(pinecone_metadata, verbose)

        # Step 7: (Optional) Create and upload a test vector to Pinecone
        if create_vector:
            create_and_upload_test_vector(pinecone_db, pinecone_metadata)

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
