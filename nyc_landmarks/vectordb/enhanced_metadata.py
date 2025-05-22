"""
Enhanced metadata collection for the NYC Landmarks Vector Database.

This module handles the collection and formatting of rich metadata from
the CoreDataStore API to enhance vector database entries.
"""

import logging
from typing import Dict, List

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.models.landmark_models import LandmarkMetadata, PlutoDataModel

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

    def collect_landmark_metadata(self, landmark_id: str) -> LandmarkMetadata:
        """Collect comprehensive metadata for a landmark from CoreDataStore API.

        Args:
            landmark_id: ID of the landmark (LP number)

        Returns:
            LandmarkMetadata object containing enhanced landmark metadata
        """
        # Start with basic landmark metadata
        metadata = self.db_client.get_landmark_metadata(landmark_id)

        # If not using CoreDataStore API, return basic metadata
        if not self.using_api:
            logger.info(
                f"Using basic metadata for landmark {landmark_id} (API calls disabled)"
            )
            return metadata

        try:
            # Add rich metadata only available from the API
            # Existing basic metadata already includes: landmark_id, name, location, borough, type, designation_date

            # Initialize variables
            landmark_details = None
            landmark_details_found = False

            # 1. First, attempt to get the main landmark details - this is the primary source of metadata
            try:
                landmark_details = self.db_client.get_landmark_by_id(landmark_id)
                landmark_details_found = True

                # Explicitly include architect, neighborhood, and style from landmark details
                if landmark_details:
                    # Extract fields regardless of whether landmark_details is a dictionary or an object
                    if isinstance(landmark_details, dict):
                        metadata["architect"] = landmark_details.get("architect")
                        metadata["neighborhood"] = landmark_details.get("neighborhood")
                        metadata["style"] = landmark_details.get("style")
                    else:
                        metadata["architect"] = getattr(
                            landmark_details, "architect", None
                        )
                        metadata["neighborhood"] = getattr(
                            landmark_details, "neighborhood", None
                        )
                        metadata["style"] = getattr(landmark_details, "style", None)

                    logger.info(
                        f"Added architect, neighborhood, and style metadata for landmark {landmark_id}"
                    )

            except Exception as e:
                logger.error(f"Error getting landmark details: {e}")
                # Continue with other metadata even if landmark details fails

            # 2. Add building information - collect ALL buildings
            # Use direct API access instead of going through DB client to preserve BBL data
            from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI

            # We'll add the buildings key only if we find building data

            try:
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

                # Add building data to metadata only if we found buildings
                if building_data:
                    metadata["buildings"] = building_data
                else:
                    # Skip building-related operations if no building data
                    logger.debug(f"No buildings found for landmark {landmark_id}")

                # Add the building from landmark details only if we have a valid BBL from landmark details
                # and landmark_details was successfully retrieved AND we have a buildings list already
                if (
                    "buildings" in metadata
                    and landmark_details_found
                    and landmark_details
                ):
                    # Extract BBL from landmark details
                    landmark_bbl_value = None
                    if isinstance(landmark_details, dict):
                        landmark_bbl_value = landmark_details.get("bbl")
                    else:
                        landmark_bbl_value = getattr(landmark_details, "bbl", None)

                    # Only add if we have a valid BBL and it's not already in the buildings list
                    if landmark_bbl_value and not any(
                        b.get("bbl") == landmark_bbl_value
                        for b in metadata["buildings"]
                    ):
                        # Add to buildings list
                        metadata["buildings"].append(
                            {
                                "bbl": landmark_bbl_value,
                                "name": (
                                    landmark_details.get("name")
                                    if isinstance(landmark_details, dict)
                                    else getattr(landmark_details, "name", "")
                                ),
                                "source": "landmark_details",
                            }
                        )
                        logger.debug(
                            f"Added building from landmark details with BBL: {landmark_bbl_value}"
                        )
            except Exception as e:
                logger.error(f"Error getting building information: {e}")
                # Continue with other metadata even if building information fails

            # 3. Add PLUTO data summary
            try:
                pluto_data = self.db_client.get_landmark_pluto_data(landmark_id)
                if pluto_data:
                    # The pluto_data is now a list of PlutoDataModel instances
                    pluto_model = pluto_data[0]
                    metadata.update(
                        {
                            "has_pluto_data": True,
                            "year_built": pluto_model.yearBuilt or "",
                            "land_use": pluto_model.landUse or "",
                            "historic_district": pluto_model.historicDistrict or "",
                            "zoning_district": pluto_model.zoneDist1 or "",
                        }
                    )
                else:
                    metadata["has_pluto_data"] = False
            except Exception as e:
                logger.error(f"Error getting PLUTO data: {e}")
                # Continue with other metadata even if PLUTO data fails

            logger.info(f"Collected enhanced metadata for landmark {landmark_id}")
            return metadata

        except Exception as e:
            logger.error(f"Error collecting enhanced metadata: {e}")
            # Fall back to basic metadata
            return metadata

    def collect_batch_metadata(
        self, landmark_ids: List[str]
    ) -> Dict[str, LandmarkMetadata]:
        """Collect enhanced metadata for multiple landmarks.

        Args:
            landmark_ids: List of landmark IDs

        Returns:
            Dictionary mapping landmark IDs to their enhanced metadata as LandmarkMetadata objects
        """
        result = {}
        for landmark_id in landmark_ids:
            try:
                result[landmark_id] = self.collect_landmark_metadata(landmark_id)
            except Exception as e:
                logger.error(f"Error processing landmark {landmark_id}: {e}")
                # Skip this landmark and continue with others
                continue

        return result


# Factory function to get a metadata collector
def get_metadata_collector() -> EnhancedMetadataCollector:
    """Get a metadata collector instance.

    Returns:
        EnhancedMetadataCollector instance
    """
    return EnhancedMetadataCollector()
