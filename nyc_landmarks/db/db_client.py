"""
Database client interface for the NYC Landmarks Vector Database.

This module provides a unified interface for database operations,
using the CoreDataStore API to retrieve landmark information.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI
from nyc_landmarks.models.landmark_models import (
    LpcReportDetailResponse,
    LpcReportModel,
    LpcReportResponse,
)
from nyc_landmarks.models.wikipedia_models import WikipediaArticleModel

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class DbClient:
    """Database client interface for CoreDataStore API."""

    client: CoreDataStoreAPI

    def __init__(self, client: CoreDataStoreAPI) -> None:
        """Initialize the CoreDataStore API client."""
        self.client = client

    def get_landmark_by_id(
        self, landmark_id: str
    ) -> Optional[Union[Dict[str, Any], LpcReportDetailResponse]]:
        """Get landmark information by ID.

        Args:
            landmark_id: ID of the landmark (LP number)

        Returns:
            LpcReportDetailResponse object or dictionary containing landmark information,
            or None if not found
        """
        # Try to get the detailed response first
        try:
            # Ensure landmark_id is properly formatted with LP prefix
            if not landmark_id.startswith("LP-"):
                lpc_id = f"LP-{landmark_id.zfill(5)}"
            else:
                lpc_id = landmark_id

            # Get the LPC report using the API - use public methods instead of protected _make_request
            if hasattr(self.client, "get_landmark_by_id"):
                landmark_data = self.client.get_landmark_by_id(lpc_id)
                if isinstance(landmark_data, dict):
                    return LpcReportDetailResponse(**landmark_data)
                return None
        except Exception as e:
            logger.warning(f"Could not parse response as LpcReportDetailResponse: {e}")
            # Fall back to the older dictionary-based method
            return self.client.get_landmark_by_id(landmark_id)

    def get_all_landmarks(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all landmarks.

        Args:
            limit: Maximum number of landmarks to return (optional)

        Returns:
            List of dictionaries containing landmark information
        """
        return self.client.get_all_landmarks(limit)

    def get_landmarks_page(
        self, page_size: int = 10, page: int = 1
    ) -> Union[List[Dict[str, Any]], List[LpcReportModel]]:
        """Get a page of landmarks.

        Args:
            page_size: Number of landmarks per page
            page: Page number (starting from 1)

        Returns:
            List of landmarks for the requested page, either as dictionaries
            or as LpcReportModel objects
        """
        # Try to use the Pydantic model-based approach first
        try:
            # Use the proper get_lpc_reports method instead of _make_request directly
            response = self.get_lpc_reports(page=page, limit=page_size)
            if isinstance(response, LpcReportResponse):
                # Converting to list to address type conversion issues
                return list(response.results)
        except Exception as e:
            logger.warning(f"Error using Pydantic model for landmarks page: {e}")
            # Fall back to the dictionary-based approach
            pass

        # Use the legacy approach as fallback
        # If we're using the CoreDataStore API, it supports pagination directly
        if hasattr(self.client, "get_landmarks_page"):
            return self.client.get_landmarks_page(page_size, page)

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

    def search_landmarks(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for landmarks by name or other attributes.

        Args:
            search_term: Search term

        Returns:
            List of dictionaries containing landmark information
        """
        return self.client.search_landmarks(search_term)

    def get_landmark_metadata(self, landmark_id: str) -> Dict[str, Any]:
        """Get metadata for a landmark suitable for storing with vector embeddings.

        Args:
            landmark_id: ID of the landmark

        Returns:
            Dictionary containing landmark metadata
        """
        return self.client.get_landmark_metadata(landmark_id)

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

        # Fallback implementation if client doesn't support get_lpc_reports
        try:
            # If not available, try a more generic approach
            if hasattr(self.client, "get_landmarks_page"):
                landmarks = self.client.get_landmarks_page(limit, page)

                # Convert to models if needed to satisfy type checker
                model_results = []
                for item in landmarks:
                    if isinstance(item, dict):
                        try:
                            model_results.append(LpcReportModel(**item))
                        except Exception as conversion_error:
                            logger.warning(
                                f"Error converting item to LpcReportModel: {conversion_error}"
                            )
                            # Create a minimal model with required fields
                            model_results.append(
                                LpcReportModel(
                                    name="Unknown",
                                    lpNumber="Unknown",
                                    lpcId="",
                                    objectType="",
                                    architect="",
                                    style="",
                                    street="",
                                    borough="",
                                    dateDesignated="",
                                    photoStatus=False,
                                    mapStatus=False,
                                    neighborhood="",
                                    zipCode="",
                                    photoUrl=None,
                                    pdfReportUrl=None,
                                )
                            )
                    else:
                        model_results.append(item)

                # Use "from" parameter via dictionary unpacking to avoid naming issues
                start_record = int((page - 1) * limit + 1)
                end_record = int(
                    min((page - 1) * limit + len(landmarks), len(landmarks))
                )

                return LpcReportResponse(
                    total=len(landmarks),
                    page=page,
                    limit=limit,
                    **{"from": start_record},  # Use unpacking for the "from" field
                    to=end_record,
                    results=model_results,
                )
            else:
                raise ValueError("Client does not support getting landmarks page")
        except Exception as e:
            logger.error(f"Error getting LPC reports: {e}")
            raise Exception(f"Error getting LPC reports: {e}")

    def get_landmark_pdf_url(self, landmark_id: str) -> Optional[str]:
        """Get the PDF report URL for a landmark.

        Args:
            landmark_id: ID of the landmark

        Returns:
            URL string if available, None otherwise
        """
        # Try to get the PDF URL from the detailed response first
        try:
            response = self.get_landmark_by_id(landmark_id)
            if isinstance(response, LpcReportDetailResponse) and response.pdfReportUrl:
                return response.pdfReportUrl
        except Exception as e:
            logger.warning(f"Error getting PDF URL from response: {e}")

        # Fall back to the direct method if needed
        if hasattr(self.client, "get_landmark_pdf_url"):
            return self.client.get_landmark_pdf_url(landmark_id)
        return None

    def get_landmark_buildings(
        self, landmark_id: str, limit: int = 50
    ) -> List[LpcReportModel]:
        """Get buildings associated with a landmark.

        Args:
            landmark_id: ID of the landmark
            limit: Maximum number of buildings to return

        Returns:
            List of buildings (as LpcReportModel objects or dictionaries)
        """
        try:
            # Try to get buildings with Pydantic models - avoid direct _make_request
            # Use proper API methods when available
            if hasattr(self.client, "get_landmark_buildings"):
                buildings = self.client.get_landmark_buildings(landmark_id, limit)
                if isinstance(buildings, list):
                    # Try to convert to LpcReportModel list if possible
                    # Always convert to LpcReportModel objects to satisfy type checker
                    model_results = []
                    for bldg in buildings:
                        if isinstance(bldg, dict):
                            try:
                                model_results.append(LpcReportModel(**bldg))
                            except Exception as e:
                                logger.warning(
                                    f"Error converting dict to LpcReportModel: {e}"
                                )
                                model_results.append(
                                    LpcReportModel(
                                        name="Unknown Building",
                                        lpNumber="Unknown",
                                        lpcId="",
                                        objectType="",
                                        architect="",
                                        style="",
                                        street="",
                                        borough="",
                                        dateDesignated="",
                                        photoStatus=False,
                                        mapStatus=False,
                                        neighborhood="",
                                        zipCode="",
                                        photoUrl=None,
                                        pdfReportUrl=None,
                                    )
                                )
                        elif isinstance(bldg, LpcReportModel):
                            model_results.append(bldg)
                    return model_results
        except Exception as e:
            logger.warning(f"Error using Pydantic model for landmark buildings: {e}")

        # Fall back to the legacy method
        if hasattr(self.client, "get_landmark_buildings"):
            buildings = self.client.get_landmark_buildings(landmark_id, limit)
            # Convert all items to LpcReportModel - this is safer than a cast
            model_buildings = []
            for bldg in buildings:
                if isinstance(bldg, dict):
                    try:
                        model_buildings.append(LpcReportModel(**bldg))
                    except Exception as e:
                        logger.warning(f"Error converting building to model: {e}")
                        model_buildings.append(
                            LpcReportModel(
                                name="Unknown Building",
                                lpNumber="Unknown",
                                lpcId="",
                                objectType="",
                                architect="",
                                style="",
                                street="",
                                borough="",
                                dateDesignated="",
                                photoStatus=False,
                                mapStatus=False,
                                neighborhood="",
                                zipCode="",
                                photoUrl=None,
                                pdfReportUrl=None,
                            )
                        )
                elif isinstance(bldg, LpcReportModel):
                    model_buildings.append(bldg)
            return model_buildings
        return []

    def get_wikipedia_articles(self, landmark_id: str) -> List[WikipediaArticleModel]:
        """Get Wikipedia articles associated with a landmark.

        Args:
            landmark_id: ID of the landmark (LP number)

        Returns:
            List of WikipediaArticleModel objects, empty list if none found
        """
        if hasattr(self.client, "get_wikipedia_articles"):
            return self.client.get_wikipedia_articles(landmark_id)
        return []

    def get_landmark_pluto_data(self, landmark_id: str) -> List[Dict[str, Any]]:
        """Get PLUTO data for a landmark.

        Args:
            landmark_id: ID of the landmark

        Returns:
            List of PLUTO data records
        """
        if hasattr(self.client, "get_landmark_pluto_data"):
            return self.client.get_landmark_pluto_data(landmark_id)
        return []

    def get_total_record_count(self) -> int:
        """Get the total number of landmarks available in the database.

        This method first tries to make a minimal API request to get metadata including
        the total record count. If that fails, it falls back to estimating the count
        by fetching pages until no more records are found.

        Returns:
            int: Total number of landmark records
        """
        try:
            # First attempt: Try to get the count from the API metadata
            count_from_metadata = self._get_count_from_api_metadata()
            if count_from_metadata > 0:
                return count_from_metadata

            # Second attempt: Estimate by fetching pages
            return self._estimate_count_from_pages()

        except Exception as e:
            logger.error(f"Error getting total record count: {e}")
            return 100  # Return a reasonable default if all else fails

    def _get_count_from_api_metadata(self) -> int:
        """Try to get the record count from API metadata.

        Returns:
            int: The total record count or 0 if not found
        """
        try:
            # Get the first page with minimal records
            response = self.get_lpc_reports(page=1, limit=1)
            if hasattr(response, "total"):
                return response.total
            return 0
        except Exception as e:
            logger.warning(f"Error getting total record count from API metadata: {e}")
            return 0

    def _estimate_count_from_pages(self) -> int:
        """Estimate the total record count by fetching pages.

        Returns:
            int: The estimated total record count
        """
        logger.info("Falling back to page-based count estimation")
        page_size = 50  # Use larger page size for efficiency
        estimated_count = 0
        max_pages = 5  # Limit to prevent too many API calls
        reached_end = False

        for page in range(1, max_pages + 1):
            page_data = self.get_landmarks_page(page_size=page_size, page=page)
            if not page_data:
                reached_end = True
                break

            estimated_count += len(page_data)

            # If we got fewer records than the page size, we've reached the end
            if len(page_data) < page_size:
                reached_end = True
                break

        # If we hit the max pages without reaching the end, log a warning
        if not reached_end:
            logger.info(
                f"Reached max pages ({max_pages}). Count is likely higher than {estimated_count}"
            )
        else:
            logger.info(f"Estimated total record count: {estimated_count}")

        return max(1, estimated_count)  # Ensure we return at least 1


def get_db_client() -> DbClient:
    """Get a database client instance.

    Returns:
        DbClient instance
    """
    logger.info("Using CoreDataStore API client")
    api_client = CoreDataStoreAPI()
    return DbClient(api_client)
