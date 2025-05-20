"""
Enhanced metadata collection for the NYC Landmarks Vector Database.

This module handles the collection and formatting of rich metadata from
the CoreDataStore API to enhance vector database entries.
"""

import logging
from typing import Any, Dict, List

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import get_db_client

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class EnhancedMetadataCollector:
    """Collects and formats enhanced metadata from CoreDataStore API."""

    def __init__(self) -> None:
        """Initialize the metadata collector with database client."""
        self.db_client = get_db_client()
        # Check if we're using the CoreDataStore API
        self.using_api = settings.COREDATASTORE_USE_API

    def collect_landmark_metadata(self, landmark_id: str) -> Dict[str, Any]:
        """Collect comprehensive metadata for a landmark from CoreDataStore API.

        Args:
            landmark_id: ID of the landmark (LP number)

        Returns:
            Dictionary containing enhanced landmark metadata
        """
        # Start with basic landmark metadata
        metadata = self.db_client.get_landmark_metadata(landmark_id)

        # If not using CoreDataStore API, return basic metadata
        if not self.using_api:
            logger.info(
                f"Using basic metadata for landmark {landmark_id} (PostgreSQL mode)"
            )
            return metadata

        try:
            # Add rich metadata only available from the API
            # Existing basic metadata already includes: landmark_id, name, location, borough, type, designation_date

            # 1. Add building information - now collect ALL buildings (not limited to 1)
            # Use direct API access instead of going through DB client to preserve BBL data
            from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI

            direct_api = CoreDataStoreAPI()
            buildings = direct_api.get_landmark_buildings(landmark_id)

            # Log what we're getting from the direct API call
            logger.debug(f"Direct API returned {len(buildings)} buildings")
            if buildings and len(buildings) > 0:
                logger.debug(f"First building BBL: {buildings[0].get('bbl')}")

            # Create a list to store all building data including BBLs
            building_data = []
            primary_bbl = None

            if buildings:
                # Process all buildings
                for building in buildings:
                    building_info = {}

                    # Handle both Dict and Pydantic model types
                    if isinstance(building, dict):
                        # Make sure to get BBL properly with our consistent null handling
                        bbl_value = building.get("bbl")
                        # Ensure it's not an empty string
                        if bbl_value == "":
                            bbl_value = None

                        building_info = {
                            "bbl": bbl_value,  # This should now be properly None or a valid value
                            "bin": building.get("bin", ""),
                            "block": building.get("block", ""),
                            "lot": building.get("lot", ""),
                            "latitude": building.get("latitude", ""),
                            "longitude": building.get("longitude", ""),
                            "address": building.get("address", ""),
                            "name": building.get("name", ""),
                        }
                        # Set the first building's BBL as the primary if not already set
                        if primary_bbl is None and bbl_value:
                            primary_bbl = bbl_value

                        # Debug logging
                        logger.debug(
                            f"Building BBL from API: {bbl_value}, Type: {type(bbl_value)}"
                        )
                    else:
                        # Access as attributes for Pydantic model
                        bbl_value = getattr(building, "bbl", None)
                        # Ensure it's not an empty string
                        if bbl_value == "":
                            bbl_value = None

                        building_info = {
                            "bbl": bbl_value,  # This should now be properly None or a valid value
                            "bin": getattr(building, "bin", ""),
                            "block": getattr(building, "block", ""),
                            "lot": getattr(building, "lot", ""),
                            "latitude": getattr(building, "latitude", ""),
                            "longitude": getattr(building, "longitude", ""),
                            "address": getattr(building, "address", ""),
                            "name": getattr(building, "name", ""),
                        }
                        # Set the first building's BBL as the primary if not already set
                        if primary_bbl is None and bbl_value:
                            primary_bbl = bbl_value

                        # Debug logging
                        logger.debug(
                            f"Building BBL from Pydantic model: {bbl_value}, Type: {type(bbl_value)}"
                        )

                    # Only add the building if it has valid data
                    if any(building_info.values()):
                        building_data.append(building_info)

                # Add the buildings list to metadata
                metadata["buildings"] = building_data

                # Note: We're no longer including separate bbl and all_bbls fields
                # as this information is now available in the complex building objects

            # 2. Set photo information and get BBL from landmark details
            landmark_details = self.db_client.get_landmark_by_id(landmark_id)

            # Check if we have photo information from various sources
            has_photos = False
            if landmark_details:
                # Get photo status
                if isinstance(landmark_details, dict) and landmark_details.get(
                    "photoStatus"
                ):
                    has_photos = True
                elif hasattr(landmark_details, "photoStatus") and getattr(
                    landmark_details, "photoStatus", False
                ):
                    has_photos = True

                # Get BBL from landmark details if available
                bbl_value = None
                if isinstance(landmark_details, dict) and "bbl" in landmark_details:
                    bbl_value = landmark_details.get("bbl")
                    if bbl_value == "":
                        bbl_value = None
                elif hasattr(landmark_details, "bbl"):
                    bbl_value = getattr(landmark_details, "bbl", None)
                    if bbl_value == "":
                        bbl_value = None

                # If BBL from landmark details exists and is not already in a building,
                # add a new building entry for it
                if bbl_value and not any(
                    b.get("bbl") == bbl_value for b in building_data
                ):
                    building_data.append(
                        {
                            "bbl": bbl_value,
                            "name": (
                                landmark_details.get("name")
                                if isinstance(landmark_details, dict)
                                else getattr(landmark_details, "name", "")
                            ),
                            "source": "landmark_details",
                        }
                    )
                    logger.debug(
                        f"Added building from landmark details with BBL: {bbl_value}"
                    )

            metadata["has_photos"] = has_photos

            # 3. Add PLUTO data summary
            pluto_data = self.db_client.get_landmark_pluto_data(landmark_id)
            if pluto_data:
                # Extract key PLUTO fields from the first record
                pluto = pluto_data[0]
                metadata.update(
                    {
                        "has_pluto_data": True,
                        "year_built": pluto.get("yearBuilt", ""),
                        "land_use": pluto.get("landUse", ""),
                        "historic_district": pluto.get("historicDistrict", ""),
                        "zoning_district": pluto.get("zoneDist1", ""),
                    }
                )
            else:
                metadata["has_pluto_data"] = False

            logger.info(f"Collected enhanced metadata for landmark {landmark_id}")
            return metadata

        except Exception as e:
            logger.error(f"Error collecting enhanced metadata: {e}")
            # Fall back to basic metadata
            return metadata

    def collect_batch_metadata(
        self, landmark_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Collect enhanced metadata for multiple landmarks.

        Args:
            landmark_ids: List of landmark IDs

        Returns:
            Dictionary mapping landmark IDs to their enhanced metadata
        """
        result = {}
        for landmark_id in landmark_ids:
            result[landmark_id] = self.collect_landmark_metadata(landmark_id)

        return result


# Factory function to get a metadata collector
def get_metadata_collector() -> EnhancedMetadataCollector:
    """Get a metadata collector instance.

    Returns:
        EnhancedMetadataCollector instance
    """
    return EnhancedMetadataCollector()
