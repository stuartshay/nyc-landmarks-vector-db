"""
Enhanced metadata collection for the NYC Landmarks Vector Database.

This module handles the collection and formatting of rich metadata from
the CoreDataStore API to enhance vector database entries.
"""

import logging
from typing import Dict, List, Optional, Union

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.models.metadata_models import LandmarkMetadata

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class EnhancedMetadataCollector:
    def _add_landmark_details(self, landmark_id: str, metadata_dict: dict) -> tuple:
        """Fetch and add architect, neighborhood, and style to metadata_dict."""
        try:
            landmark_details = self.db_client.get_landmark_by_id(landmark_id)
            if landmark_details:
                if isinstance(landmark_details, dict):
                    metadata_dict["architect"] = landmark_details.get("architect")
                    metadata_dict["neighborhood"] = landmark_details.get("neighborhood")
                    metadata_dict["style"] = landmark_details.get("style")
                else:
                    metadata_dict["architect"] = getattr(
                        landmark_details, "architect", None
                    )
                    metadata_dict["neighborhood"] = getattr(
                        landmark_details, "neighborhood", None
                    )
                    metadata_dict["style"] = getattr(landmark_details, "style", None)
                logger.info(
                    f"Added architect, neighborhood, and style metadata for landmark {landmark_id}"
                )
                return landmark_details, True
        except Exception as e:
            logger.error(f"Error getting landmark details: {e}")
        return None, False

    def _add_building_data(
        self,
        landmark_id: str,
        metadata_dict: Dict[str, List[Dict[str, Optional[Union[str, float]]]]],
        landmark_details: dict,
        landmark_details_found: bool,
    ) -> None:
        """Fetch and add building data to metadata_dict."""
        try:
            logger.debug(f"Entering _add_building_data for landmark {landmark_id}")
            buildings = self.db_client.get_landmark_buildings(landmark_id)
            metadata_dict["buildings"] = []
            building_data = []
            primary_bbl = None
            if buildings:
                for building in buildings:
                    building_info = {}
                    bbl_value = (
                        building.get("bbl")
                        if isinstance(building, dict)
                        else getattr(building, "bbl", None)
                    )
                    if bbl_value == "":
                        bbl_value = None
                    building_info = {
                        "bbl": bbl_value,
                        "bin": (
                            building.get("bin", "")
                            if isinstance(building, dict)
                            else getattr(building, "bin", "")
                        ),
                        "block": (
                            building.get("block", "")
                            if isinstance(building, dict)
                            else getattr(building, "block", "")
                        ),
                        "lot": (
                            building.get("lot", "")
                            if isinstance(building, dict)
                            else getattr(building, "lot", "")
                        ),
                        "latitude": (
                            building.get("latitude", 0.0)
                            if isinstance(building, dict)
                            else getattr(building, "latitude", 0.0)
                        ),
                        "longitude": (
                            building.get("longitude", 0.0)
                            if isinstance(building, dict)
                            else getattr(building, "longitude", 0.0)
                        ),
                        "address": (
                            building.get("address", "")
                            if isinstance(building, dict)
                            else getattr(building, "address", "")
                        ),
                        "name": (
                            building.get("name", "")
                            if isinstance(building, dict)
                            else getattr(building, "name", "")
                        ),
                    }
                    if primary_bbl is None and bbl_value:
                        primary_bbl = bbl_value
                    if any(building_info.values()):
                        building_data.append(building_info)
            if building_data:
                metadata_dict["buildings"] = building_data
        except Exception as e:
            logger.error(f"Error getting building information: {e}")

    def _add_pluto_data(self, landmark_id: str, metadata_dict: dict) -> None:
        """Fetch and add PLUTO data to metadata_dict."""
        try:
            pluto_data = self.db_client.get_landmark_pluto_data(landmark_id)
            if pluto_data:
                pluto_model = pluto_data[0]
                metadata_dict.update(
                    {
                        "has_pluto_data": True,
                        "year_built": pluto_model.yearBuilt or "",
                        "land_use": pluto_model.landUse or "",
                        "historic_district": pluto_model.historicDistrict or "",
                        "zoning_district": pluto_model.zoneDist1 or "",
                    }
                )
            else:
                metadata_dict["has_pluto_data"] = False
        except Exception as e:
            logger.error(f"Error getting PLUTO data: {e}")

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
        metadata = self.db_client.get_landmark_metadata(landmark_id)
        metadata_dict = dict(metadata) if not isinstance(metadata, dict) else metadata

        if not self.using_api:
            logger.info(
                f"Using basic metadata for landmark {landmark_id} (API calls disabled)"
            )
            if isinstance(metadata, LandmarkMetadata):
                return metadata
            return LandmarkMetadata(**metadata_dict)

        try:
            landmark_details, landmark_details_found = self._add_landmark_details(
                landmark_id, metadata_dict
            )
            self._add_building_data(
                landmark_id, metadata_dict, landmark_details, landmark_details_found
            )
            self._add_pluto_data(landmark_id, metadata_dict)

            # Filter out invalid or unnecessary fields
            validated_metadata = {
                key: value
                for key, value in metadata_dict.items()
                if value is not None and key not in ["buildings", "year_built"]
            }

            logger.info(f"Collected enhanced metadata for landmark {landmark_id}")
            return LandmarkMetadata(**validated_metadata)
        except Exception as e:
            logger.error(f"Error collecting enhanced metadata: {e}")
            if isinstance(metadata, LandmarkMetadata):
                return metadata
            return LandmarkMetadata(**metadata_dict)

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
