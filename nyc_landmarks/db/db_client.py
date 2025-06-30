"""
Database client interface for the NYC Landmarks Vector Database.

This module provides a unified interface for database operations,
using the CoreDataStore API to retrieve landmark information.
"""

import logging
from typing import Any, Dict, List, Optional, Protocol, Union, cast

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db._coredatastore_api import _CoreDataStoreAPI
from nyc_landmarks.models.landmark_models import (
    LpcReportResponse,  # Ensure LpcReportResponse is here
)
from nyc_landmarks.models.landmark_models import (
    LandmarkDetail,
    LpcReportDetailResponse,
    LpcReportModel,
    PlutoDataModel,
)
from nyc_landmarks.models.metadata_models import LandmarkMetadata
from nyc_landmarks.models.wikipedia_models import WikipediaArticleModel
from nyc_landmarks.utils.logger import configure_basic_logging_safely

# Configure logging
logger = logging.getLogger(__name__)
configure_basic_logging_safely(level=getattr(logging, settings.LOG_LEVEL.value))


# Define the protocol for clients that support Wikipedia functions
class SupportsWikipedia(Protocol):
    """Protocol for clients that support Wikipedia article operations."""

    def get_wikipedia_articles(self, landmark_id: str) -> List[WikipediaArticleModel]:
        """Get Wikipedia articles for a landmark."""
        return []  # Protocol requires an actual return value


class DbClient:
    """Database client interface for CoreDataStore API."""

    client: "_CoreDataStoreAPI"

    def __init__(self, client: Optional["_CoreDataStoreAPI"] = None) -> None:
        """Initialize the CoreDataStore API client."""
        from nyc_landmarks.db._coredatastore_api import _CoreDataStoreAPI

        self.client = client if client is not None else _CoreDataStoreAPI()
        pass  # Protocol method

    @staticmethod
    def _format_landmark_id(landmark_id: str) -> str:
        """Format landmark ID to ensure it has the proper LP prefix format.

        Args:
            landmark_id: Raw landmark ID

        Returns:
            Properly formatted landmark ID with LP prefix
        """
        if not landmark_id.startswith("LP-"):
            return f"LP-{landmark_id.zfill(5)}"
        return landmark_id

    def _parse_landmark_response(
        self, landmark_data: Dict[str, Any], lpc_id: str
    ) -> Optional[LpcReportDetailResponse]:
        """Parse the landmark API response.

        Args:
            landmark_data: Raw landmark data from the API (must not be None)
            lpc_id: The formatted landmark ID

        Returns:
            Parsed landmark response as LpcReportDetailResponse or None if parsing fails
        """
        # Safety check if somehow a non-dict makes it here
        if not isinstance(landmark_data, dict):
            return None

        try:
            # Ensure lpNumber field is present (it's required by the model)
            if "lpNumber" not in landmark_data and "id" in landmark_data:
                landmark_data["lpNumber"] = landmark_data["id"]
            elif "lpNumber" not in landmark_data:
                landmark_data["lpNumber"] = lpc_id

            return LpcReportDetailResponse(**landmark_data)
        except Exception as e:
            logger.warning(f"Could not parse response as LpcReportDetailResponse: {e}")
            return None  # Return None if validation fails

    def _get_landmark_fallback(
        self, landmark_id: str
    ) -> Optional[LpcReportDetailResponse]:
        """Attempt to get landmark using fallback method.

        Args:
            landmark_id: ID of the landmark

        Returns:
            LpcReportDetailResponse or None if not found
        """
        try:
            # Fall back to the client method directly, which now returns LpcReportDetailResponse
            return self.client.get_landmark_by_id(landmark_id)
        except Exception as e:
            logger.error(f"Failed to get landmark with fallback method: {e}")
            return None

    def get_landmark_by_id(self, landmark_id: str) -> Optional[LpcReportDetailResponse]:
        """Get landmark information by ID.

        Args:
            landmark_id: ID of the landmark (LP number)

        Returns:
            LpcReportDetailResponse object containing landmark information,
            or None if not found
        """
        # Format the landmark ID
        lpc_id = self._format_landmark_id(landmark_id)

        try:
            # Get the LPC report using the API client
            if hasattr(self.client, "get_landmark_by_id"):
                landmark_data = self.client.get_landmark_by_id(lpc_id)
                return landmark_data  # Now directly returns LpcReportDetailResponse
            return None
        except Exception as e:
            logger.warning(f"Could not get landmark response: {e}")
            return None

    def get_all_landmarks(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all landmarks.

        Args:
            limit: Maximum number of landmarks to return (optional)

        Returns:
            List of dictionaries containing landmark information
        """
        # The client.get_all_landmarks now returns LpcReportResponse,
        # so we need to extract the results list
        response = self.client.get_all_landmarks(limit)

        # Handle both LpcReportResponse and list return types for backwards compatibility
        if hasattr(response, "results"):
            # Convert each LpcReportModel to a dictionary
            return [model.model_dump() for model in response.results]
        elif isinstance(response, list):
            # If the API returns a list directly, use that
            return response
        else:
            logger.warning(
                f"Unexpected response type from get_all_landmarks: {type(response)}"
            )
            return []

    def get_landmarks_page(
        self, page_size: int = 10, page: int = 1
    ) -> List[Dict[str, Any]]:
        """Get a page of landmarks.

        Args:
            page_size: Number of landmarks per page
            page: Page number (starting from 1)

        Returns:
            List of dictionaries containing landmark information for the requested page
        """
        # Try to use the Pydantic model-based approach first
        try:
            # Use the proper get_lpc_reports method instead of _make_request directly
            response = self.get_lpc_reports(page=page, limit=page_size)
            # The type of 'response' is LpcReportResponse, so isinstance check is redundant.
            # Convert each LpcReportModel to a dictionary
            return [model.model_dump() for model in response.results]
        except Exception as e:
            logger.warning(f"Error using Pydantic model for landmarks page: {e}")
            # Fall back to the dictionary-based approach

        # Use the legacy approach as fallback
        # If we're using the CoreDataStore API, it supports pagination directly
        if hasattr(self.client, "get_landmarks_page"):
            response = self.client.get_landmarks_page(page_size, page)
            # Handle both LpcReportResponse and list return types
            if hasattr(response, "results"):
                return [model.model_dump() for model in response.results]
            elif isinstance(response, list):
                return response
            else:
                logger.error(
                    f"Unexpected response type from get_landmarks_page: {type(response)}"
                )
                return []

        # For other clients that don't support pagination directly,
        # we'll implement it here
        try:
            # Get all landmarks
            all_landmarks = self.get_all_landmarks()

            # Calculate start and end indices
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            # Return the slice of landmarks for this page
            return all_landmarks[start_idx:end_idx]
        except Exception as e:
            logger.error(f"Error getting landmarks page: {e}")
            return []

    def get_total_record_count(self) -> int:
        """Get the total count of landmarks in the database.

        Returns:
            Total number of landmark records available
        """
        return self.client.get_total_record_count()

    def search_landmarks(self, search_term: str) -> LpcReportResponse:
        """Search for landmarks by name or other attributes.

        Args:
            search_term: Search term

        Returns:
            LpcReportResponse object containing search results and pagination info
        """
        response = self.client.search_landmarks(search_term)

        # If the response is already a LpcReportResponse, return it directly
        if hasattr(response, "results"):
            return response
        elif isinstance(response, list):
            # If the API returns a list directly, convert it to LpcReportResponse
            model_results: List[LpcReportModel] = []
            for item_dict in cast(List[Dict[str, Any]], response):
                try:
                    model_results.append(LpcReportModel(**item_dict))
                except Exception as e:
                    logger.warning(f"Error converting item to LpcReportModel: {e}")
                    # Create a minimal model with required fields and fallback values
                    model_results.append(
                        LpcReportModel(
                            name=item_dict.get("name", "Unknown"),
                            lpNumber=item_dict.get("lpNumber", "Unknown"),
                            lpcId=item_dict.get("lpcId", ""),
                            objectType=item_dict.get("objectType", ""),
                            architect=item_dict.get("architect", ""),
                            style=item_dict.get("style", ""),
                            street=item_dict.get("street", ""),
                            borough=item_dict.get("borough", ""),
                            dateDesignated=item_dict.get("dateDesignated", ""),
                            photoStatus=item_dict.get("photoStatus", False),
                            mapStatus=item_dict.get("mapStatus", False),
                            neighborhood=item_dict.get("neighborhood", ""),
                            zipCode=item_dict.get("zipCode", ""),
                            photoUrl=item_dict.get("photoUrl"),
                            pdfReportUrl=item_dict.get("pdfReportUrl"),
                        )
                    )
            # Create the LpcReportResponse with proper field names using kwargs
            from_dict: Dict[str, Any] = {"from": 1}
            return LpcReportResponse(
                results=model_results,
                total=len(model_results),
                page=1,
                limit=len(model_results),
                to=len(model_results),
                **from_dict,
            )
        else:
            logger.warning(
                f"Unexpected response type from search_landmarks: {type(response)}"
            )
            # Return an empty LpcReportResponse using kwargs
            from_dict_empty: Dict[str, Any] = {"from": 1}
            return LpcReportResponse(
                results=[],
                total=0,
                page=1,
                limit=0,
                to=0,
                **from_dict_empty,
            )

    def get_landmark_metadata(
        self, landmark_id: str
    ) -> Union[Dict[str, Any], LandmarkMetadata]:
        """Get metadata for a landmark suitable for storing with vector embeddings.

        Args:
            landmark_id: ID of the landmark

        Returns:
            Dictionary or LandmarkMetadata object containing structured landmark metadata
        """
        # Get the raw metadata dictionary from the client
        raw_metadata = self.client.get_landmark_metadata(landmark_id)

        # For backward compatibility with tests, return the raw dictionary
        # if it's already in the expected format
        if isinstance(raw_metadata, dict):
            return raw_metadata

        try:
            # Convert the dictionary to a LandmarkMetadata object
            return LandmarkMetadata(**raw_metadata)
        except Exception as e:
            logger.warning(
                f"Error converting metadata to LandmarkMetadata model for {landmark_id}: {e}"
            )
            # Create a model with required fields and all optional fields initialized to None
            # This ensures the model has all the necessary fields while still being valid
            return LandmarkMetadata(
                landmark_id=landmark_id,
                name=raw_metadata.get("name", "Unknown Landmark"),
                location=raw_metadata.get("location"),
                borough=raw_metadata.get("borough"),
                type=raw_metadata.get("type"),
                designation_date=raw_metadata.get("designation_date"),
                architect=raw_metadata.get("architect"),
                style=raw_metadata.get("style"),
                neighborhood=raw_metadata.get("neighborhood"),
                has_pluto_data=raw_metadata.get("has_pluto_data"),
                year_built=raw_metadata.get("year_built"),
                land_use=raw_metadata.get("land_use"),
                historic_district=raw_metadata.get("historic_district"),
                zoning_district=raw_metadata.get("zoning_district"),
            )

    def get_landmark_pluto_data(self, landmark_id: str) -> List[PlutoDataModel]:
        """Get PLUTO data for a landmark.

        Args:
            landmark_id: ID of the landmark (LP number)

        Returns:
            List of PlutoDataModel objects containing property data
        """
        try:
            raw_pluto_data = self.client.get_landmark_pluto_data(landmark_id)
            return [PlutoDataModel(**data) for data in raw_pluto_data]
        except Exception as e:
            logger.error(f"Error retrieving PLUTO data for landmark {landmark_id}: {e}")
            return []

    def get_lpc_reports(
        self,
        page: int = 1,
        limit: int = 10,
        borough: Optional[str] = None,
        object_type: Optional[str] = None,
        neighborhood: Optional[str] = None,
        search_text: Optional[str] = None,
        parent_style_list: Optional[List[str]] = None,
        sort_column: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> LpcReportResponse:
        """Get paginated list of LPC reports with optional filtering using Pydantic models.

        Args:
            page: Page number (starting from 1)
            limit: Number of records per page
            borough: Optional borough filter
            object_type: Optional object type filter
            neighborhood: Optional neighborhood filter
            search_text: Optional text search
            parent_style_list: Optional list of architectural styles
            sort_column: Optional column to sort by
            sort_order: Optional sort direction ("asc" or "desc")

        Returns:
            LpcReportResponse object containing results and pagination info
        """
        if hasattr(self.client, "get_lpc_reports"):
            return self.client.get_lpc_reports(
                page=page,
                limit=limit,
                borough=borough,
                object_type=object_type,
                neighborhood=neighborhood,
                search_text=search_text,
                parent_style_list=parent_style_list,
                sort_column=sort_column,
                sort_order=sort_order,
            )
        return self._get_lpc_reports_fallback(
            page=page,
            limit=limit,
        )

    def _get_lpc_reports_fallback(
        self, page: int = 1, limit: int = 10
    ) -> LpcReportResponse:
        """Fallback implementation for get_lpc_reports if not supported by client."""
        try:
            if not hasattr(self.client, "get_landmarks_page"):
                raise ValueError("Client does not support getting landmarks page")
            response = self.client.get_landmarks_page(limit, page)
            landmarks = self._response_to_landmarks(response)
            model_results = self._convert_to_models(landmarks)
            start_record, end_record = self._pagination(page, limit, len(landmarks))
            return LpcReportResponse(
                total=len(landmarks),
                page=page,
                limit=limit,
                to=end_record,
                results=model_results,
                **{"from": start_record},
            )
        except Exception as e:
            logger.error(f"Error getting LPC reports: {e}")
            raise Exception(f"Error getting LPC reports: {e}")

    @staticmethod
    def _response_to_landmarks(response: Any) -> List[Dict[str, Any]]:
        if hasattr(response, "results"):
            return [model.model_dump() for model in response.results]
        elif isinstance(response, list):
            return response
        else:
            logger.warning(
                f"Unexpected response type from get_landmarks_page: {type(response)}"
            )
            return []

    @staticmethod
    def _safe_lpc_report_model(item: Dict[str, Any]) -> LpcReportModel:
        # If lpNumber is missing or empty, treat as invalid and set name to 'Unknown'
        lp_number = item.get("lpNumber")
        if not lp_number or not isinstance(lp_number, str) or not lp_number.strip():
            return LpcReportModel(
                name="Unknown",
                lpcId=item.get("lpcId", ""),
                lpNumber="Unknown",
                objectType=item.get("objectType", ""),
                architect=item.get("architect", ""),
                style=item.get("style", ""),
                street=item.get("street", ""),
                borough=item.get("borough", ""),
                dateDesignated=item.get("dateDesignated", ""),
                photoStatus=item.get("photoStatus", False),
                mapStatus=item.get("mapStatus", False),
                neighborhood=item.get("neighborhood", ""),
                zipCode=item.get("zipCode", ""),
                photoUrl=item.get("photoUrl"),
                pdfReportUrl=item.get("pdfReportUrl"),
            )
        # Otherwise, use the provided name (or 'Unknown' if missing)
        return LpcReportModel(
            name=item.get("name", "Unknown"),
            lpcId=item.get("lpcId", ""),
            lpNumber=lp_number,
            objectType=item.get("objectType", ""),
            architect=item.get("architect", ""),
            style=item.get("style", ""),
            street=item.get("street", ""),
            borough=item.get("borough", ""),
            dateDesignated=item.get("dateDesignated", ""),
            photoStatus=item.get("photoStatus", False),
            mapStatus=item.get("mapStatus", False),
            neighborhood=item.get("neighborhood", ""),
            zipCode=item.get("zipCode", ""),
            photoUrl=item.get("photoUrl"),
            pdfReportUrl=item.get("pdfReportUrl"),
        )

    @classmethod
    def _convert_to_models(
        cls, landmarks: List[Dict[str, Any]]
    ) -> List[LpcReportModel]:
        model_results: List[LpcReportModel] = []
        for item in landmarks:
            if isinstance(item, dict):
                try:
                    model_results.append(cls._safe_lpc_report_model(item))
                except Exception as conversion_error:
                    logger.warning(
                        f"Error converting item to LpcReportModel: {conversion_error}"
                    )
            else:
                logger.warning(f"Skipping non-dict item in landmarks: {item}")
        return model_results

    @staticmethod
    def _pagination(page: int, limit: int, total: int) -> tuple[int, int]:
        start_record = int((page - 1) * limit + 1)
        end_record = int(min((page - 1) * limit + total, total))
        return start_record, end_record

    def get_landmark_pdf_url(self, landmark_id: str) -> Optional[str]:
        """Get the PDF report URL for a landmark.

        Args:
            landmark_id: ID of the landmark

        Returns:
            URL string if available, None otherwise
        """
        try:
            # Try to get the PDF URL from the detailed response first
            response = self.get_landmark_by_id(landmark_id)
            if isinstance(response, LpcReportDetailResponse):
                if response.pdfReportUrl:
                    return response.pdfReportUrl
                else:
                    logger.info(
                        f"No PDF URL found in LpcReportDetailResponse for landmark ID {landmark_id}."
                    )
        except Exception as e:
            logger.warning(
                f"Error getting PDF URL from response for landmark ID {landmark_id}: {e}"
            )

        try:
            # Fall back to the direct method if needed
            if hasattr(self.client, "get_landmark_pdf_url"):
                result = self.client.get_landmark_pdf_url(landmark_id)
                if isinstance(result, str):
                    return result
                elif result is None:
                    logger.info(
                        f"No PDF URL found using client method for landmark ID {landmark_id}."
                    )
                else:
                    logger.warning(
                        f"get_landmark_pdf_url returned unexpected type {type(result)} for landmark ID {landmark_id}."
                    )
        except Exception as e:
            logger.error(
                f"Error calling client.get_landmark_pdf_url for landmark ID {landmark_id}: {e}"
            )

        return None

    @staticmethod
    @staticmethod
    def _map_borough_id_to_name(borough_id: Optional[str]) -> Optional[str]:
        """Maps a borough ID to its corresponding name."""
        if borough_id is None:
            return None
        mapping = {
            "1": "Manhattan",
            "2": "Bronx",
            "3": "Brooklyn",
            "4": "Queens",
            "5": "Staten Island",
            "MN": "Manhattan",  # Common alternative
            "BX": "Bronx",
            "BK": "Brooklyn",
            "QN": "Queens",
            "SI": "Staten Island",
        }
        return mapping.get(
            borough_id.upper(), borough_id
        )  # Return original if not found, or log warning

    def _convert_item_to_lpc_report_model(
        self,
        item: Union[Dict[str, Any], LandmarkDetail, LpcReportModel],
        landmark_lp_number_context: Optional[str] = None,
    ) -> LpcReportModel:
        """
        Converts a given item (dict, LandmarkDetail, or LpcReportModel)
        into an LpcReportModel instance.
        """
        if isinstance(item, LpcReportModel):
            return item

        if isinstance(item, LandmarkDetail):
            # Map fields from LandmarkDetail to LpcReportModel
            return LpcReportModel(
                name=item.name or "Unknown Building Name",
                lpNumber=item.lpNumber or landmark_lp_number_context or "Unknown LP",
                lpcId=None,  # LandmarkDetail doesn't have lpcId directly
                objectType=item.objectType,
                architect=None,  # LandmarkDetail doesn't have architect
                style=None,  # LandmarkDetail doesn't have style
                street=item.designatedAddress or item.street,
                borough=self._map_borough_id_to_name(item.boroughId),
                dateDesignated=item.designatedDate,
                photoStatus=None,  # Not directly available in LandmarkDetail
                mapStatus=None,  # Not directly available in LandmarkDetail
                neighborhood=item.historicDistrict,  # Using historicDistrict as neighborhood
                zipCode=None,  # Not directly in LandmarkDetail
                photoUrl=None,  # Not in LandmarkDetail
                pdfReportUrl=None,  # Not in LandmarkDetail
            )

        # If execution reaches here, 'item' must be a dict due to the Union type hint
        try:
            # Attempt to directly create LpcReportModel from dict
            return LpcReportModel(**item)
        except Exception as e:
            logger.warning(
                f"Error converting dict to LpcReportModel for LP {landmark_lp_number_context}: {e}. Dict keys: {list(item.keys())}"
            )
            # Fallback to a default model if direct conversion fails
            return LpcReportModel(
                name=item.get("name", "Unknown Building (dict conversion error)"),
                lpNumber=item.get(
                    "lpNumber", landmark_lp_number_context or "Unknown LP"
                ),
                lpcId=item.get("lpcId"),
                objectType=item.get("objectType"),
                architect=item.get("architect"),
                style=item.get("style"),
                street=item.get("street"),
                borough=item.get("borough"),
                dateDesignated=item.get("dateDesignated"),
                photoStatus=item.get("photoStatus"),
                mapStatus=item.get("mapStatus"),
                neighborhood=item.get("neighborhood"),
                zipCode=item.get("zipCode"),
                photoUrl=item.get("photoUrl"),
                pdfReportUrl=item.get("pdfReportUrl"),
            )

    def _standardize_lp_number(self, landmark_id: str) -> str:
        """Standardize landmark_id format to LP-XXXXX format.

        Args:
            landmark_id: Raw landmark ID

        Returns:
            Standardized LP number
        """
        if not landmark_id.startswith("LP-"):
            return f"LP-{landmark_id.zfill(5)}"
        return landmark_id

    def _convert_building_items_to_models(
        self,
        items: List[Union[Dict[str, Any], LandmarkDetail, LpcReportModel]],
        lp_number: str,
    ) -> List[LpcReportModel]:
        """Convert building items to LpcReportModel objects.

        Args:
            items: List of building items
            lp_number: Standardized LP number for context

        Returns:
            List of LpcReportModel objects
        """
        if not items:
            return []

        model_results: List[LpcReportModel] = []
        for item in items:
            model_results.append(
                self._convert_item_to_lpc_report_model(
                    item, landmark_lp_number_context=lp_number
                )
            )

        logger.info(
            f"Processed {len(model_results)} building models for landmark {lp_number}."
        )
        return model_results

    def _convert_building_items_to_landmark_details(
        self,
        items: List[Union[Dict[str, Any], LandmarkDetail, LpcReportModel]],
        lp_number: str,
    ) -> List[LandmarkDetail]:
        """Convert building items to LandmarkDetail objects, preserving all building metadata.

        Args:
            items: List of building items
            lp_number: Standardized LP number for context

        Returns:
            List of LandmarkDetail objects with full building metadata
        """
        if not items:
            return []

        landmark_details: List[LandmarkDetail] = []
        for item in items:
            landmark_details.append(
                self._convert_item_to_landmark_detail(
                    item, landmark_lp_number_context=lp_number
                )
            )

        logger.info(
            f"Processed {len(landmark_details)} LandmarkDetail objects for landmark {lp_number}."
        )
        return landmark_details

    def _convert_item_to_landmark_detail(
        self,
        item: Union[Dict[str, Any], LandmarkDetail, LpcReportModel],
        landmark_lp_number_context: Optional[str] = None,
    ) -> LandmarkDetail:
        """
        Converts a given item (dict, LandmarkDetail, or LpcReportModel)
        into a LandmarkDetail instance, preserving all building metadata.
        """
        if isinstance(item, LandmarkDetail):
            return item

        if isinstance(item, LpcReportModel):
            # Convert LpcReportModel to LandmarkDetail (limited fields available)
            return LandmarkDetail(
                name=item.name,
                lpNumber=item.lpNumber,
                bbl=None,
                binNumber=None,
                boroughId=self._map_borough_name_to_id(item.borough),
                objectType=item.objectType,
                block=None,
                lot=None,
                plutoAddress=None,
                designatedAddress=item.street,  # Use street as designatedAddress
                number=None,
                street=item.street,
                city=None,
                designatedDate=item.dateDesignated,
                calendaredDate=None,
                publicHearingDate=None,
                historicDistrict=item.neighborhood,
                otherHearingDate=None,
                isCurrent=None,
                status=None,
                lastAction=None,
                priorStatus=None,
                recordType=None,
                isBuilding=None,
                isVacantLot=None,
                isSecondaryBuilding=None,
                latitude=None,
                longitude=None,
                # Note: LpcReportModel doesn't have building-specific fields like bbl, binNumber, etc.
            )

        # If execution reaches here, 'item' must be a dict due to the Union type hint
        try:
            # Attempt to directly create LandmarkDetail from dict
            return LandmarkDetail(**item)
        except Exception as e:
            logger.warning(
                f"Error converting dict to LandmarkDetail for LP {landmark_lp_number_context}: {e}. Dict keys: {list(item.keys())}"
            )
            # Fallback to a default model if direct conversion fails
            return LandmarkDetail(
                name=item.get("name", "Unknown Building (dict conversion error)"),
                lpNumber=item.get(
                    "lpNumber", landmark_lp_number_context or "Unknown LP"
                ),
                bbl=item.get("bbl"),
                binNumber=item.get("binNumber"),
                boroughId=item.get("boroughId"),
                objectType=item.get("objectType"),
                block=item.get("block"),
                lot=item.get("lot"),
                plutoAddress=item.get("plutoAddress"),
                designatedAddress=item.get("designatedAddress"),
                number=item.get("number"),
                street=item.get("street"),
                city=item.get("city"),
                designatedDate=item.get("designatedDate"),
                calendaredDate=item.get("calendaredDate"),
                publicHearingDate=item.get("publicHearingDate"),
                historicDistrict=item.get("historicDistrict"),
                otherHearingDate=item.get("otherHearingDate"),
                isCurrent=item.get("isCurrent"),
                status=item.get("status"),
                lastAction=item.get("lastAction"),
                priorStatus=item.get("priorStatus"),
                recordType=item.get("recordType"),
                isBuilding=item.get("isBuilding"),
                isVacantLot=item.get("isVacantLot"),
                isSecondaryBuilding=item.get("isSecondaryBuilding"),
                latitude=item.get("latitude"),
                longitude=item.get("longitude"),
            )

    def _map_borough_name_to_id(self, borough_name: Optional[str]) -> Optional[str]:
        """Map borough name to borough ID."""
        if not borough_name:
            return None

        borough_mapping = {
            "Manhattan": "1",
            "Bronx": "2",
            "Brooklyn": "3",
            "Queens": "4",
            "Staten Island": "5",
        }
        return borough_mapping.get(borough_name)

    def get_landmark_buildings(
        self, landmark_id: str, limit: int = 50
    ) -> List[LandmarkDetail]:
        """Get buildings associated with a landmark.

        Args:
            landmark_id: ID of the landmark (LP number)
            limit: Maximum number of buildings to return

        Returns:
            List of buildings (as LandmarkDetail objects with full building metadata)
        """
        # Standardize the landmark ID
        lp_number = self._standardize_lp_number(landmark_id)

        # Try to fetch buildings from the client first
        buildings = self._fetch_buildings_from_client(lp_number, limit)

        # If no buildings found, try fallback method
        if not buildings:
            buildings = self._fetch_buildings_from_landmark_detail(lp_number, limit)

        # Convert to LandmarkDetail objects (preserving all building metadata)
        return self._convert_building_items_to_landmark_details(buildings, lp_number)

    def get_wikipedia_articles(self, landmark_id: str) -> List[WikipediaArticleModel]:
        """Get Wikipedia articles associated with a landmark.

        Args:
            landmark_id: ID of the landmark (LP number)

        Returns:
            List of WikipediaArticleModel objects, empty list if none found
        """
        if hasattr(self.client, "get_wikipedia_articles"):
            try:
                return self.client.get_wikipedia_articles(landmark_id)
            except Exception as e:
                logger.error(
                    f"Error fetching Wikipedia articles for landmark {landmark_id}: {e}"
                )
                return []
        else:
            logger.debug(
                f"Client does not support Wikipedia articles for landmark {landmark_id}"
            )
            return []

    def _fetch_buildings_from_client(
        self, lp_number: str, limit: int
    ) -> List[Union[Dict[str, Any], LandmarkDetail, LpcReportModel]]:
        """Fetch buildings from the client API.

        Args:
            lp_number: Standardized LP number
            limit: Maximum number of buildings to return

        Returns:
            List of building items (could be dicts, LandmarkDetail, or LpcReportModel objects)
        """
        try:
            # Use the client's get_landmark_buildings method which returns List[LandmarkDetail]
            if hasattr(self.client, "get_landmark_buildings"):
                buildings = self.client.get_landmark_buildings(lp_number, limit)
                logger.info(
                    f"Retrieved {len(buildings)} buildings from client API for {lp_number}"
                )
                # Convert to the expected return type
                return cast(
                    List[Union[Dict[str, Any], LandmarkDetail, LpcReportModel]],
                    buildings,
                )
            else:
                logger.warning("Client does not support get_landmark_buildings method")
                return []
        except Exception as e:
            logger.error(f"Error fetching buildings from client for {lp_number}: {e}")
            return []

    def _fetch_buildings_from_landmark_detail(
        self, lp_number: str, limit: int
    ) -> List[Union[Dict[str, Any], LandmarkDetail, LpcReportModel]]:
        """Fetch buildings from landmark detail response as fallback.

        Args:
            lp_number: Standardized LP number
            limit: Maximum number of buildings to return

        Returns:
            List of building items (could be dicts, LandmarkDetail, or LpcReportModel objects)
        """
        try:
            # Get the landmark detail response
            landmark_response = self.get_landmark_by_id(lp_number)
            if not landmark_response:
                logger.warning(f"No landmark response found for {lp_number}")
                return []

            # Extract buildings from the landmarks field
            if hasattr(landmark_response, "landmarks") and landmark_response.landmarks:
                buildings = landmark_response.landmarks[:limit]  # Apply limit
                logger.info(
                    f"Retrieved {len(buildings)} buildings from landmark detail for {lp_number}"
                )
                # Convert to the expected return type
                return cast(
                    List[Union[Dict[str, Any], LandmarkDetail, LpcReportModel]],
                    buildings,
                )
            else:
                logger.info(f"No buildings found in landmark detail for {lp_number}")
                return []
        except Exception as e:
            logger.error(
                f"Error fetching buildings from landmark detail for {lp_number}: {e}"
            )
            return []


def get_db_client() -> DbClient:
    """Get a configured database client.

    Returns:
        DbClient instance
    """
    return DbClient()
