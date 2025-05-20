#!/usr/bin/env python3
"""
Script to debug and dump the buildings information flow.

This script helps diagnose issues with BBL data by showing the exact data
coming from the API versus what is being processed in the enhanced metadata.
"""

import argparse
import json
import logging
import sys
from pprint import pformat

from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI
from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.enhanced_metadata import EnhancedMetadataCollector

# Configure logging
logger = get_logger(__name__)


def dump_buildings_info(landmark_id: str) -> None:
    """
    Dump the buildings information for a landmark.

    Args:
        landmark_id: ID of the landmark to process
    """
    try:
        logger.info(f"Dumping buildings information for landmark: {landmark_id}")

        # Step 1: Get buildings directly from the CoreDataStore API
        api_client = CoreDataStoreAPI()
        api_buildings = api_client.get_landmark_buildings(landmark_id)

        logger.info(
            f"API returned {len(api_buildings)} buildings for landmark {landmark_id}"
        )
        logger.info("Raw API building data:")
        for i, building in enumerate(api_buildings):
            logger.info(f"Building {i+1}:")
            logger.info(pformat(building))
            logger.info(
                f"BBL: {building.get('bbl')}, Type: {type(building.get('bbl'))}"
            )

        # Step 2: Get buildings via the DB Client
        db_client = get_db_client()
        db_buildings = db_client.get_landmark_buildings(landmark_id)

        logger.info(
            f"DB Client returned {len(db_buildings)} buildings for landmark {landmark_id}"
        )
        logger.info("DB Client building data:")
        for i, building in enumerate(db_buildings):
            logger.info(f"Building {i+1}:")
            if hasattr(building, "dict"):
                # For Pydantic models
                building_dict = building.dict()
                logger.info(pformat(building_dict))
                logger.info(
                    f"BBL: {getattr(building, 'bbl', None)}, Type: {type(getattr(building, 'bbl', None))}"
                )
            elif isinstance(building, dict):
                # For dictionaries
                logger.info(pformat(building))
                logger.info(
                    f"BBL: {building.get('bbl')}, Type: {type(building.get('bbl'))}"
                )
            else:
                # For other types
                logger.info(f"Unexpected type: {type(building)}")
                logger.info(str(building))

        # Step 3: Get enhanced metadata
        metadata_collector = EnhancedMetadataCollector()
        enhanced_metadata = metadata_collector.collect_landmark_metadata(landmark_id)

        logger.info("Enhanced metadata building data:")
        if "buildings" in enhanced_metadata:
            buildings = enhanced_metadata["buildings"]
            logger.info(f"Enhanced metadata has {len(buildings)} buildings")
            for i, building in enumerate(buildings):
                logger.info(f"Building {i+1}:")
                logger.info(pformat(building))
                logger.info(
                    f"BBL: {building.get('bbl')}, Type: {type(building.get('bbl'))}"
                )

            # Note: BBLs are now only stored in the buildings complex object
            # There are no longer standalone BBL fields
            logger.info("BBLs are now stored in the buildings complex object")

            # Extract and display all BBLs from buildings for reference
            bbls = [b.get("bbl") for b in buildings if b.get("bbl") is not None]
            if bbls:
                logger.info(f"All BBLs from buildings: {bbls}")
            else:
                logger.info("No BBLs found in any buildings")
        else:
            logger.info("No buildings in enhanced metadata")

    except Exception as e:
        logger.error(f"Error dumping buildings information: {e}", exc_info=True)


def main() -> None:
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description="Dump buildings information for a landmark"
    )
    parser.add_argument(
        "landmark_id", help="ID of the landmark to process (e.g., LP-00001)"
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the debug function
    dump_buildings_info(args.landmark_id)


if __name__ == "__main__":
    main()
