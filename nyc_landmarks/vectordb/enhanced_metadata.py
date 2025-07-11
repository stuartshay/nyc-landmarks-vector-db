"""
Enhanced metadata collection for the NYC Landmarks Vector Database.

This module handles the collection and formatting of rich metadata from
the CoreDataStore API to enhance vector database entries.
"""

import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import DbClient, get_db_client
from nyc_landmarks.models.landmark_models import PlutoDataModel
from nyc_landmarks.models.metadata_models import LandmarkMetadata
from nyc_landmarks.utils.logger import configure_basic_logging_safely

# Configure logging
logger = logging.getLogger(__name__)
configure_basic_logging_safely(level=getattr(logging, settings.LOG_LEVEL.value))


class EnhancedMetadataCollector:
    """Collects and formats enhanced metadata from CoreDataStore API."""

    db_client: DbClient

    # Cache constants
    DEFAULT_CACHE_TTL_HOURS = 24  # Cache validity period in hours

    def __init__(self) -> None:
        """Initialize the metadata collector with database client and cache."""
        self.db_client = get_db_client()
        # Check if we're using the CoreDataStore API
        self.using_api = settings.COREDATASTORE_USE_API

        # Initialize metadata cache
        self._metadata_cache: Dict[str, Tuple[datetime.datetime, LandmarkMetadata]] = {}
        self._cache_ttl = datetime.timedelta(hours=self.DEFAULT_CACHE_TTL_HOURS)

        logger.info(
            f"Initialized EnhancedMetadataCollector with {self.DEFAULT_CACHE_TTL_HOURS}h cache TTL"
        )

    def _remove_empty_buildings(self, metadata_dict: dict) -> None:
        if not metadata_dict.get("buildings"):
            metadata_dict.pop("buildings", None)

    def _sanitize_boolean_fields(self, metadata_dict: dict) -> None:
        for key in ["has_pluto_data"]:
            val = metadata_dict.get(key)
            if val is not None and not isinstance(val, bool):
                # Try to convert to boolean, default to False if invalid
                if hasattr(val, "__bool__"):
                    try:
                        metadata_dict[key] = bool(val)
                    except Exception:
                        metadata_dict[key] = False
                elif str(val).lower() in ["true", "1", "yes"]:
                    metadata_dict[key] = True
                elif str(val).lower() in ["false", "0", "no", ""]:
                    metadata_dict[key] = False
                else:
                    metadata_dict[key] = False

    def _remove_pluto_fields_if_needed(self, metadata_dict: dict) -> None:
        pluto_fields = [
            "year_built",
            "land_use",
            "historic_district",
            "zoning_district",
        ]
        if not metadata_dict.get("has_pluto_data"):
            for field in pluto_fields:
                metadata_dict.pop(field, None)

    def _sanitize_string_fields(self, metadata_dict: dict) -> None:
        for key in [
            "architect",
            "style",
            "neighborhood",
            "year_built",
            "land_use",
            "historic_district",
            "zoning_district",
        ]:
            val = metadata_dict.get(key)
            if val is not None and not isinstance(val, str):
                metadata_dict[key] = str(val) if hasattr(val, "__str__") else None

    def _postprocess_metadata(self, metadata_dict: dict) -> LandmarkMetadata:
        self._remove_empty_buildings(metadata_dict)
        self._sanitize_boolean_fields(metadata_dict)
        self._remove_pluto_fields_if_needed(metadata_dict)
        self._sanitize_string_fields(metadata_dict)

        # DEBUG: Log metadata dict keys before cleaning
        logger.info(
            f"DEBUG: metadata_dict before cleaning has {len(metadata_dict)} keys"
        )
        building_fields = [k for k in metadata_dict.keys() if k.startswith("building_")]
        logger.info(f"DEBUG: Building fields before cleaning: {building_fields}")

        clean_metadata = {k: v for k, v in metadata_dict.items() if v is not None}

        # DEBUG: Log clean_metadata keys after cleaning
        logger.info(
            f"DEBUG: clean_metadata after cleaning has {len(clean_metadata)} keys"
        )
        building_fields_clean = [
            k for k in clean_metadata.keys() if k.startswith("building_")
        ]
        logger.info(f"DEBUG: Building fields after cleaning: {building_fields_clean}")

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

    def _flatten_buildings_metadata(
        self, buildings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Flatten building data to be compatible with Pinecone metadata requirements.

        Converts a list of building objects:
        [{"name": "Building A", "address": "123 Main St"}, {"name": "Building B", ...}]

        Into a flattened dictionary format:
        {"building_0_name": "Building A", "building_0_address": "123 Main St",
         "building_1_name": "Building B", ...}

        Args:
            buildings: List of building dictionaries with metadata

        Returns:
            Flattened dictionary with building data in Pinecone-compatible format
        """
        flattened_metadata = {}
        building_names = []

        for i, building in enumerate(buildings):
            # Add each field with index prefix
            for key, value in building.items():
                if value is not None and value != "":
                    flattened_key = f"building_{i}_{key}"
                    flattened_metadata[flattened_key] = (
                        str(value) if not isinstance(value, bool) else value
                    )

            # Add name to the list of building names (for filtering)
            if building.get("name") and building.get("name") != "":
                building_names.append(building["name"])

        # Add array of building names for easier filtering
        if building_names:
            flattened_metadata["building_names"] = building_names  # type: ignore  # Pinecone supports arrays of strings

        return flattened_metadata

    def _add_building_data(
        self,
        landmark_id: str,
        metadata_dict: Dict[str, Any],
        landmark_details: Optional[dict[str, Any]],
        landmark_details_found: bool,
    ) -> List[Dict[str, Any]]:
        """Fetch and add building data to metadata_dict as flattened fields.

        Returns:
            List of building dictionaries (for internal processing only)
        """
        try:
            logger.debug(f"Entering _add_building_data for landmark {landmark_id}")
            building_data = []

            # Get buildings using the standard DbClient method
            buildings = self.db_client.get_landmark_buildings(landmark_id)

            if buildings:
                for building in buildings:
                    # Handle both dict and object building data
                    if isinstance(building, dict):
                        # Handle dictionary building data (from mocks)
                        bbl_value = building.get("bbl")
                        if bbl_value == "":
                            bbl_value = None

                        building_info = {
                            "bbl": bbl_value,
                            "binNumber": building.get("binNumber"),
                            "block": building.get("block"),
                            "lot": building.get("lot"),
                            "latitude": building.get("latitude"),
                            "longitude": building.get("longitude"),
                            "address": building.get("designatedAddress")
                            or building.get("address", ""),
                            "name": building.get("name", ""),
                            "boroughId": building.get("boroughId"),
                            "objectType": building.get("objectType"),
                            "city": building.get("city"),
                            "designatedDate": building.get("designatedDate"),
                            "historicDistrict": building.get("historicDistrict"),
                        }
                    else:
                        # Handle object building data (from actual API)
                        bbl_value = getattr(building, "bbl", None)
                        if bbl_value == "":
                            bbl_value = None

                        building_info = {
                            "bbl": bbl_value,
                            "binNumber": getattr(building, "binNumber", None),
                            "block": getattr(building, "block", None),
                            "lot": getattr(building, "lot", None),
                            "latitude": getattr(building, "latitude", None),
                            "longitude": getattr(building, "longitude", None),
                            "address": getattr(building, "designatedAddress", None)
                            or getattr(building, "address", ""),
                            "name": getattr(building, "name", ""),
                            "boroughId": getattr(building, "boroughId", None),
                            "objectType": getattr(building, "objectType", None),
                            "city": getattr(building, "city", None),
                            "designatedDate": getattr(building, "designatedDate", None),
                            "historicDistrict": getattr(
                                building, "historicDistrict", None
                            ),
                        }

                    # Only add building if it has meaningful data
                    if any(v is not None and v != "" for v in building_info.values()):
                        building_data.append(building_info)

                # Add flattened building data to metadata_dict
                if building_data:
                    flattened_buildings = self._flatten_buildings_metadata(
                        building_data
                    )
                    metadata_dict.update(flattened_buildings)
                    logger.info(
                        f"Added {len(building_data)} buildings as flattened metadata for landmark {landmark_id}"
                    )
                else:
                    logger.warning(f"No building data found for landmark {landmark_id}")
            else:
                logger.warning(
                    f"No buildings returned from db_client for landmark {landmark_id}"
                )

            return building_data

        except Exception as e:
            logger.error(f"Error getting building information: {e}")
            return []

    def _add_pluto_data(self, landmark_id: str, metadata_dict: dict) -> None:
        """Fetch and add PLUTO data to metadata_dict if has_pluto_data is True."""
        try:
            # Only call get_landmark_pluto_data() if has_pluto_data is True from get_landmark_by_id()
            if metadata_dict.get("has_pluto_data", False):
                pluto_data = self.db_client.get_landmark_pluto_data(landmark_id)
                if pluto_data:
                    pluto_model = pluto_data[0]
                    if not isinstance(pluto_model, PlutoDataModel):
                        raise TypeError(
                            f"Expected pluto_model to be an instance of PlutoDataModel, "
                            f"but got {type(pluto_model).__name__} instead."
                        )
                    metadata_dict.update(
                        {
                            "year_built": (
                                str(pluto_model.yearbuilt)
                                if pluto_model.yearbuilt
                                else ""
                            ),
                            "land_use": pluto_model.landUse or "",
                            "historic_district": pluto_model.historicDistrict or "",
                            "zoning_district": pluto_model.zoneDist1 or "",
                            "lot_area": (
                                str(pluto_model.lotArea) if pluto_model.lotArea else ""
                            ),
                            "building_area": (
                                str(pluto_model.bldgArea)
                                if pluto_model.bldgArea
                                else ""
                            ),
                            "num_floors": (
                                str(pluto_model.numFloors)
                                if pluto_model.numFloors
                                else ""
                            ),
                            "property_address": pluto_model.address or "",
                            "borough_code": pluto_model.borough or "",
                            "owner_name": pluto_model.ownername or "",
                            "building_class": pluto_model.bldgclass or "",
                            "assessed_land_value": (
                                str(pluto_model.assessland)
                                if pluto_model.assessland
                                else ""
                            ),
                            "assessed_total_value": (
                                str(pluto_model.assesstot)
                                if pluto_model.assesstot
                                else ""
                            ),
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

    def collect_landmark_metadata(self, landmark_id: str) -> LandmarkMetadata:
        """Collect comprehensive metadata for a landmark from CoreDataStore API.

        Args:
            landmark_id: ID of the landmark (LP number)

        Returns:
            LandmarkMetadata object containing enhanced landmark metadata
        """
        # Check cache first
        if landmark_id in self._metadata_cache:
            timestamp, cached_metadata = self._metadata_cache[landmark_id]
            # Check if cache is still valid
            if datetime.datetime.now() - timestamp < self._cache_ttl:
                logger.info(
                    f"Using cached metadata for landmark {landmark_id} (from {timestamp.isoformat()})"
                )
                return cached_metadata
            else:
                logger.info(
                    f"Cached metadata for landmark {landmark_id} expired (from {timestamp.isoformat()})"
                )
                # We'll proceed to fetch fresh metadata

        try:
            metadata = self.db_client.get_landmark_metadata(landmark_id)
            metadata_dict = (
                dict(metadata) if not isinstance(metadata, dict) else metadata
            )

            # Ensure the required fields exist
            if "landmark_id" not in metadata_dict:
                metadata_dict["landmark_id"] = landmark_id

            if "name" not in metadata_dict:
                # Set a default name if none exists
                metadata_dict["name"] = f"Landmark {landmark_id}"
                logger.warning(
                    f"No name found for landmark {landmark_id}, using default"
                )

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
                _ = self._add_building_data(
                    landmark_id, metadata_dict, landmark_details, landmark_details_found
                )
                self._add_pluto_data(landmark_id, metadata_dict)
                logger.info(f"Collected enhanced metadata for landmark {landmark_id}")
                processed_metadata = self._postprocess_metadata(metadata_dict)

                # Store in cache
                self._metadata_cache[landmark_id] = (
                    datetime.datetime.now(),
                    processed_metadata,
                )
                logger.info(f"Cached metadata for landmark {landmark_id}")

                return processed_metadata
            except Exception as e:
                logger.error(f"Error collecting enhanced metadata: {e}")
                return self._fallback_metadata(metadata, metadata_dict)

        except Exception as outer_e:
            # If we can't even get basic metadata, create a minimal valid object
            logger.error(
                f"Critical error getting metadata for landmark {landmark_id}: {outer_e}"
            )
            # Create a minimal valid metadata object
            minimal_metadata = {
                "landmark_id": landmark_id,
                "name": f"Unknown Landmark {landmark_id}",
                "location": None,
                "borough": None,
                "type": None,
                "designation_date": None,
                "architect": None,
                "style": None,
                "neighborhood": None,
                "has_pluto_data": False,
            }
            minimal_metadata_obj = LandmarkMetadata(**minimal_metadata)

            # Cache even minimal metadata to prevent repeated failures
            self._metadata_cache[landmark_id] = (
                datetime.datetime.now(),
                minimal_metadata_obj,
            )
            logger.info(f"Cached minimal fallback metadata for landmark {landmark_id}")

            return minimal_metadata_obj

    def collect_batch_metadata(self, landmark_ids: List[str]) -> Dict[str, dict]:
        """Collect enhanced metadata for multiple landmarks.

        Args:
            landmark_ids: List of landmark IDs

        Returns:
            Dictionary mapping landmark IDs to their enhanced metadata as dicts
        """
        result = {}
        cache_hits = 0
        cache_misses = 0

        for landmark_id in landmark_ids:
            try:
                # This will use cache if available
                meta = self.collect_landmark_metadata(landmark_id)

                # Track cache hit/miss statistics
                if landmark_id in self._metadata_cache:
                    timestamp, _ = self._metadata_cache[landmark_id]
                    if datetime.datetime.now() - timestamp < self._cache_ttl:
                        cache_hits += 1
                    else:
                        cache_misses += 1
                else:
                    cache_misses += 1

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

        # Log cache statistics
        total = cache_hits + cache_misses
        hit_ratio = cache_hits / total if total > 0 else 0
        logger.info(
            f"Metadata cache statistics: {cache_hits} hits, {cache_misses} misses, {hit_ratio:.1%} hit ratio"
        )

        return result


# Factory function to get a metadata collector
def get_metadata_collector() -> EnhancedMetadataCollector:
    """Get a metadata collector instance.

    Returns:
        EnhancedMetadataCollector instance
    """
    return EnhancedMetadataCollector()


def clear_metadata_cache() -> None:
    """Clear the metadata cache in all collector instances.

    This is useful for testing or when you need to force fresh metadata fetching.
    """
    collector = get_metadata_collector()
    cache_size = len(collector._metadata_cache)
    collector._metadata_cache.clear()
    logger.info(f"Cleared metadata cache ({cache_size} entries)")
