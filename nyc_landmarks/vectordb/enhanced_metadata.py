"""
Enhanced metadata collection for the NYC Landmarks Vector Database.

This module handles the collection and formatting of rich metadata from
the CoreDataStore API to enhance vector database entries.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.models.metadata_models import LandmarkMetadata

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class EnhancedMetadataCollector:
    def _postprocess_metadata(self, metadata_dict: dict) -> LandmarkMetadata:
        # Only add 'buildings' if there are any
        if not metadata_dict.get("buildings"):
            metadata_dict.pop("buildings", None)

        # Only include PLUTO fields if has_pluto_data is True
        pluto_fields = [
            "year_built",
            "land_use",
            "historic_district",
            "zoning_district",
        ]
        if not metadata_dict.get("has_pluto_data"):
            for field in pluto_fields:
                metadata_dict.pop(field, None)

        # Sanitize string fields to avoid mock objects
        for key in ["architect", "style", "neighborhood"]:
            val = metadata_dict.get(key)
            if val is not None and not isinstance(val, str):
                metadata_dict[key] = str(val) if hasattr(val, "__str__") else None

        # Remove all fields with value None
        clean_metadata = {k: v for k, v in metadata_dict.items() if v is not None}
        return LandmarkMetadata(**clean_metadata)

    def _fallback_metadata(
        self, metadata: object, metadata_dict: dict
    ) -> LandmarkMetadata:
        if isinstance(metadata, LandmarkMetadata):
            return metadata
        return self._postprocess_metadata(metadata_dict)

    def _add_landmark_details(
        self, landmark_id: str, metadata_dict: dict
    ) -> tuple[Optional[dict[str, Any]], bool]:
        """Fetch and add architect, neighborhood, style, and has_pluto_data to metadata_dict."""
        try:
            landmark_details = self.db_client.get_landmark_by_id(landmark_id)
            if landmark_details:
                if isinstance(landmark_details, dict):
                    metadata_dict["architect"] = landmark_details.get("architect")
                    metadata_dict["neighborhood"] = landmark_details.get("neighborhood")
                    metadata_dict["style"] = landmark_details.get("style")
                    metadata_dict["has_pluto_data"] = landmark_details.get(
                        "plutoStatus", False
                    )
                    logger.info(
                        f"Added architect, neighborhood, style, and has_pluto_data metadata for landmark {landmark_id}"
                    )
                    return landmark_details, True
                else:
                    # Convert to dict if possible
                    details_dict = {
                        "architect": getattr(landmark_details, "architect", None),
                        "neighborhood": getattr(landmark_details, "neighborhood", None),
                        "style": getattr(landmark_details, "style", None),
                        "has_pluto_data": getattr(
                            landmark_details, "plutoStatus", False
                        ),
                    }
                    metadata_dict.update(details_dict)
                    logger.info(
                        f"Added architect, neighborhood, style, and has_pluto_data metadata for landmark {landmark_id}"
                    )
                    return details_dict, True
        except Exception as e:
            logger.error(f"Error getting landmark details: {e}")
        return None, False

    def _add_building_data(
        self,
        landmark_id: str,
        metadata_dict: Dict[str, List[Dict[str, Optional[Union[str, float]]]]],
        landmark_details: Optional[dict[str, Any]],
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
        """Fetch and add PLUTO data to metadata_dict if has_pluto_data is True."""
        try:
            # Only call get_landmark_pluto_data() if has_pluto_data is True from get_landmark_by_id()
            if metadata_dict.get("has_pluto_data", False):
                pluto_data = self.db_client.get_landmark_pluto_data(landmark_id)
                if pluto_data:
                    pluto_model = pluto_data[0]
                    metadata_dict.update(
                        {
                            "year_built": pluto_model.yearBuilt or "",
                            "land_use": pluto_model.landUse or "",
                            "historic_district": pluto_model.historicDistrict or "",
                            "zoning_district": pluto_model.zoneDist1 or "",
                        }
                    )
                    logger.info(f"Added PLUTO data fields for landmark {landmark_id}")
                else:
                    # If plutoStatus was True but no actual data found, set has_pluto_data to False
                    metadata_dict["has_pluto_data"] = False
                    logger.warning(
                        f"has_pluto_data was True but no PLUTO data found for landmark {landmark_id}"
                    )
            else:
                logger.debug(
                    f"Skipping PLUTO data fetch for landmark {landmark_id} (has_pluto_data=False)"
                )
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
            # Remove 'buildings' if present (should not be in non-API mode)
            metadata_dict.pop("buildings", None)
            return self._fallback_metadata(metadata, metadata_dict)

        try:
            landmark_details, landmark_details_found = self._add_landmark_details(
                landmark_id, metadata_dict
            )
            self._add_building_data(
                landmark_id, metadata_dict, landmark_details, landmark_details_found
            )
            self._add_pluto_data(landmark_id, metadata_dict)
            logger.info(f"Collected enhanced metadata for landmark {landmark_id}")
            return self._postprocess_metadata(metadata_dict)
        except Exception as e:
            logger.error(f"Error collecting enhanced metadata: {e}")
            return self._fallback_metadata(metadata, metadata_dict)

    def collect_batch_metadata(self, landmark_ids: List[str]) -> Dict[str, dict]:
        """Collect enhanced metadata for multiple landmarks.

        Args:
            landmark_ids: List of landmark IDs

        Returns:
            Dictionary mapping landmark IDs to their enhanced metadata as dicts
        """
        result = {}
        for landmark_id in landmark_ids:
            try:
                meta = self.collect_landmark_metadata(landmark_id)
                # Convert to dict for test compatibility, removing None values
                if hasattr(meta, "dict"):
                    d = meta.dict()
                else:
                    d = dict(meta)
                clean_d = {k: v for k, v in d.items() if v is not None}
                result[landmark_id] = clean_d
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
