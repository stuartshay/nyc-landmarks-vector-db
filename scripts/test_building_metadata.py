#!/usr/bin/env python3
"""
Test script to diagnose and fix building metadata integration issues.

This script tests how the landmark building data is being processed by:
1. Directly calling the CoreDataStore API
2. Using the DbClient's get_landmark_buildings method
3. Using the EnhancedMetadataCollector to populate building metadata

By comparing these approaches, we can identify where the building metadata
processing is failing and implement appropriate fixes.
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict, List

import requests

from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.models.landmark_models import LpcReportModel
from nyc_landmarks.vectordb.enhanced_metadata import get_metadata_collector

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def direct_api_call(landmark_id: str) -> Dict[str, Any]:
    """
    Call the CoreDataStore API directly to get landmark data.

    Args:
        landmark_id: The LP number of the landmark

    Returns:
        The JSON response from the API
    """
    # Format the landmark ID to ensure LP prefix
    if not landmark_id.startswith("LP-"):
        landmark_id = f"LP-{landmark_id.zfill(5)}"

    # Construct the API URL - this is based on the curl example you provided
    url = f"https://api.coredatastore.com/api/LpcReport/landmark/10/1?LpcNumber={landmark_id}"

    headers = {"accept": "application/json"}

    try:
        logger.info(f"Calling CoreDataStore API directly for landmark: {landmark_id}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for non-2xx responses

        data = response.json()
        logger.info(
            f"Direct API call successful. Results count: {len(data.get('results', []))}"
        )
        return data
    except Exception as e:
        logger.error(f"Error in direct API call: {e}")
        error_dict: Dict[str, Any] = {"error": str(e), "results": []}
        return error_dict


def test_db_client_buildings(landmark_id: str) -> List[LpcReportModel]:
    """
    Test the DbClient's get_landmark_buildings method.

    Args:
        landmark_id: The LP number of the landmark

    Returns:
        List of building models returned by DbClient
    """
    try:
        logger.info(
            f"Testing DbClient.get_landmark_buildings for landmark: {landmark_id}"
        )
        db_client = get_db_client()
        buildings = db_client.get_landmark_buildings(landmark_id)

        logger.info(f"DbClient returned {len(buildings)} buildings")
        return buildings
    except Exception as e:
        logger.error(f"Error in db_client.get_landmark_buildings: {e}")
        return []


def test_enhanced_metadata(landmark_id: str) -> Dict[str, Any]:
    """
    Test the EnhancedMetadataCollector's building metadata collection.

    Args:
        landmark_id: The LP number of the landmark

    Returns:
        The metadata dictionary with building data
    """
    try:
        logger.info(f"Testing EnhancedMetadataCollector for landmark: {landmark_id}")
        collector = get_metadata_collector()
        metadata = collector.collect_landmark_metadata(landmark_id)

        # Convert to dictionary for display
        if hasattr(metadata, "dict"):
            metadata_dict = metadata.dict()
        else:
            metadata_dict = dict(metadata)

        # Check if buildings data exists (look for flattened building fields)
        building_keys = [k for k in metadata_dict.keys() if k.startswith("building_")]
        has_buildings = len(building_keys) > 0
        logger.info(f"EnhancedMetadataCollector has buildings data: {has_buildings}")
        if has_buildings:
            # Count unique building indices
            building_indices = set()
            for key in building_keys:
                # Extract building index from keys like "building_0_name", "building_1_bbl"
                parts = key.split("_")
                if len(parts) >= 2 and parts[1].isdigit():
                    building_indices.add(int(parts[1]))
            logger.info(f"Number of buildings: {len(building_indices)}")
            logger.info(f"Building fields found: {sorted(building_keys)}")

        return metadata_dict
    except Exception as e:
        logger.error(f"Error in EnhancedMetadataCollector: {e}")
        return {}


def debug_api_and_client_mismatch(
    api_data: Dict[str, Any], client_buildings: List[LpcReportModel]
) -> None:
    """
    Debug the mismatch between API data and client data.

    Args:
        api_data: Data from direct API call
        client_buildings: Buildings from DbClient
    """
    logger.info("=== Analyzing API vs Client Data Mismatch ===")

    # Check if API returned buildings in results
    api_buildings = api_data.get("results", [])
    logger.info(f"API returned {len(api_buildings)} building(s) in results")

    # Compare counts
    logger.info(f"DbClient returned {len(client_buildings)} building(s)")

    # Check if the API results are being interpreted correctly
    if api_buildings and not client_buildings:
        logger.warning(
            "API returned buildings but DbClient did not - potential parsing issue"
        )

        # Check the structure of API buildings to see what fields are available
        first_api_building = api_buildings[0] if api_buildings else {}
        logger.info(f"API building fields: {', '.join(first_api_building.keys())}")

        # Check specifically for expected fields that might be missing
        expected_fields = [
            "bbl",
            "binNumber",
            "block",
            "lot",
            "latitude",
            "longitude",
            "designatedAddress",
            "name",
        ]
        for field in expected_fields:
            if field in first_api_building:
                logger.info(
                    f"Field '{field}' exists in API response with value: {first_api_building.get(field)}"
                )
            else:
                logger.warning(f"Field '{field}' is MISSING in API response")


def fix_recommendations(
    landmark_id: str, api_data: Dict[str, Any], metadata: Dict[str, Any]
) -> None:
    """
    Provide recommendations for fixing the building metadata issue.

    Args:
        landmark_id: The LP number of the landmark
        api_data: Data from direct API call
        metadata: Enhanced metadata
    """
    logger.info("=== Fix Recommendations ===")

    # Check if API has results
    api_buildings = api_data.get("results", [])
    if not api_buildings:
        logger.info(
            "No buildings found in API response - may be correct for this landmark"
        )
        return

    # Check if metadata has buildings
    has_buildings = "buildings" in metadata and metadata["buildings"]

    if not has_buildings and api_buildings:
        logger.warning(
            "API has building data but metadata does not - likely a processing issue"
        )

        # Create a potential fix example
        fixed_buildings = []
        for api_building in api_buildings:
            building_info = {
                "bbl": api_building.get("bbl"),
                "binNumber": api_building.get("binNumber"),
                "block": api_building.get("block"),
                "lot": api_building.get("lot"),
                "latitude": api_building.get("latitude"),
                "longitude": api_building.get("longitude"),
                "address": api_building.get("designatedAddress")
                or api_building.get("plutoAddress", ""),
                "name": api_building.get("name", ""),
            }
            # Only add if it has meaningful data
            if any(v is not None and v != "" for v in building_info.values()):
                fixed_buildings.append(building_info)

        logger.info(
            f"Potential fixed building data (would add {len(fixed_buildings)} buildings):"
        )
        if fixed_buildings:
            logger.info(json.dumps(fixed_buildings, indent=2))


def main() -> int:
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(description="Test building metadata integration")
    parser.add_argument("landmark_id", help="Landmark ID to test (LP number)")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    landmark_id = args.landmark_id

    logger.info(f"Testing building metadata integration for landmark: {landmark_id}")

    # Step 1: Direct API call
    api_data = direct_api_call(landmark_id)
    print("\nDirect API Response:")
    print(json.dumps(api_data, indent=2))

    # Step 2: Test DbClient buildings
    client_buildings = test_db_client_buildings(landmark_id)
    print("\nDbClient Buildings:")
    for i, building in enumerate(client_buildings):
        print(f"\nBuilding {i + 1}:")
        if hasattr(building, "model_dump"):
            print(json.dumps(building.model_dump(), indent=2))
        else:
            print(json.dumps(dict(building), indent=2))

    # Step 3: Test enhanced metadata
    metadata = test_enhanced_metadata(landmark_id)
    print("\nEnhanced Metadata (buildings only):")
    # Look for flattened building fields
    building_keys = [k for k in metadata.keys() if k.startswith("building_")]

    if building_keys:
        print("Found flattened building data:")
        # Group by building index
        buildings_by_index: Dict[int, Dict[str, Any]] = {}
        for key in building_keys:
            parts = key.split("_", 2)  # Split into ["building", "0", "name"] format
            if len(parts) >= 3 and parts[1].isdigit():
                index = int(parts[1])
                field_name = parts[2]
                if index not in buildings_by_index:
                    buildings_by_index[index] = {}
                buildings_by_index[index][field_name] = metadata[key]

        for index in sorted(buildings_by_index.keys()):
            print(
                f"Building {index}: {json.dumps(buildings_by_index[index], indent=2)}"
            )
    else:
        print("No buildings data in metadata")

    # Step 4: Debug mismatches
    debug_api_and_client_mismatch(api_data, client_buildings)

    # Step 5: Provide fix recommendations
    fix_recommendations(landmark_id, api_data, metadata)

    return 0


if __name__ == "__main__":
    sys.exit(main())
