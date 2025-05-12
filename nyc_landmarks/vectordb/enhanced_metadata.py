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

            # 1. Add building information (first building only to keep metadata manageable)
            buildings = self.db_client.get_landmark_buildings(landmark_id, limit=1)
            if buildings:
                building = buildings[0]
                # Handle both Dict and Pydantic model types
                if isinstance(building, dict):
                    metadata.update(
                        {
                            "bbl": building.get("bbl", ""),
                            "bin": building.get("bin", ""),
                            "block": building.get("block", ""),
                            "lot": building.get("lot", ""),
                            "latitude": building.get("latitude", ""),
                            "longitude": building.get("longitude", ""),
                        }
                    )
                else:
                    # Access as attributes for Pydantic model
                    metadata.update(
                        {
                            "bbl": getattr(building, "bbl", ""),
                            "bin": getattr(building, "bin", ""),
                            "block": getattr(building, "block", ""),
                            "lot": getattr(building, "lot", ""),
                            "latitude": getattr(building, "latitude", ""),
                            "longitude": getattr(building, "longitude", ""),
                        }
                    )

            # 2. Set photo information (We no longer have the get_landmark_photos method)
            # Instead set has_photos based on photoStatus from landmark metadata or from the metadata directly
            landmark_details = self.db_client.get_landmark_by_id(landmark_id)

            # Check if we have photo information from various sources
            has_photos = False
            if landmark_details:
                if isinstance(landmark_details, dict) and landmark_details.get(
                    "photoStatus"
                ):
                    has_photos = True
                elif hasattr(landmark_details, "photoStatus") and getattr(
                    landmark_details, "photoStatus", False
                ):
                    has_photos = True

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
