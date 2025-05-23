# _coredatastore_api.py
#
# Private implementation of the CoreDataStore API for direct CoreDataStore access.
# This module is for internal use by the data access layer only (DbClient).
# Do not import or use this class outside nyc_landmarks.db.db_client.

import logging
from typing import Any, Dict, List, Optional, Union, cast
from urllib.parse import urljoin

import requests

from nyc_landmarks.config.settings import settings
from nyc_landmarks.models.landmark_models import (
    LpcReportDetailResponse,
    LpcReportResponse,
)
from nyc_landmarks.models.wikipedia_models import WikipediaArticleModel

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class _CoreDataStoreAPI:
    """CoreDataStore API client for landmark operations (private, internal use only)."""

    def __init__(self) -> None:
        self.base_url = "https://api.coredatastore.com"
        self.api_key = settings.COREDATASTORE_API_KEY
        self.headers: dict[str, str] = {}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        logger.info("Initialized CoreDataStore API client")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], List[str]]:
        url = urljoin(self.base_url, endpoint)
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data,
                timeout=30,
            )
            response.raise_for_status()
            if response.content:
                json_response = response.json()
                if isinstance(json_response, (dict, list)):
                    return json_response
                logger.warning(f"Unexpected response type: {type(json_response)}")
                return {}
            return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}")
            raise Exception(f"Error making API request: {e}")

    def _standardize_landmark_id(self, landmark_id: str) -> List[str]:
        variations = []
        base_id = landmark_id
        if not landmark_id.startswith("LP-"):
            base_id = f"LP-{landmark_id.lstrip('0').zfill(5)}"
        variations.append(base_id)
        if any(c.isalpha() for c in base_id[3:]):
            prefix = "LP-"
            suffix = ""
            number_part = ""
            for char in base_id[3:]:
                if char.isdigit():
                    number_part += char
                elif char.isalpha():
                    suffix += char
            if suffix:
                variations.append(f"{prefix}{number_part.zfill(5)}")
            clean_numeric = "".join(filter(str.isdigit, base_id))
            if clean_numeric:
                variations.append(f"LP-{clean_numeric.zfill(5)}")
        return list(dict.fromkeys(variations))

    def _find_landmark_with_id_variations(
        self, landmark_id: str
    ) -> Optional[Dict[str, Any]]:
        id_variations = self._standardize_landmark_id(landmark_id)
        for lpc_id in id_variations:
            try:
                response = self._make_request("GET", f"/api/LpcReport/{lpc_id}")
                if response and isinstance(response, dict):
                    logger.debug(f"Found landmark with ID: {lpc_id}")
                    return response
            except Exception as e:
                logger.debug(f"Attempted ID {lpc_id} resulted in error: {e}")
                continue
        logger.warning(f"Landmark not found with ID: {landmark_id}")
        return None

    def _ensure_landmark_has_lp_number(self, response: dict, landmark_id: str) -> dict:
        if "lpNumber" not in response and "id" in response:
            response["lpNumber"] = response["id"]
        elif "lpNumber" not in response:
            id_variations = self._standardize_landmark_id(landmark_id)
            for lpc_id in id_variations:
                if lpc_id.startswith("LP-"):
                    response["lpNumber"] = lpc_id
                    break
            else:
                response["lpNumber"] = landmark_id
        return response

    def get_landmark_by_id(self, landmark_id: str) -> Optional[LpcReportDetailResponse]:
        try:
            response = self._find_landmark_with_id_variations(landmark_id)
            if not response:
                return None
            if not isinstance(response, dict):
                logger.error(
                    f"Expected dictionary response but got {type(response).__name__}"
                )
                return None
            response = self._ensure_landmark_has_lp_number(response, landmark_id)
            try:
                return LpcReportDetailResponse(**response)
            except Exception as e:
                logger.error(
                    f"Failed to parse response as LpcReportDetailResponse: {e}"
                )
                return None
        except Exception as e:
            logger.error(f"Error getting landmark by ID: {e}")
            return None

    def get_landmarks_page(
        self, page_size: int = 10, page: int = 1
    ) -> LpcReportResponse:
        """Get a page of landmarks directly using the API's pagination.

        Args:
            page_size: Number of landmarks per page
            page: Page number (starting from 1)

        Returns:
            LpcReportResponse object containing the requested page of landmarks
        """
        # Use the more comprehensive get_lpc_reports method
        return self.get_lpc_reports(page=page, limit=page_size)

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

        This method directly maps to the GetLpcReports MCP tool functionality and uses
        Pydantic models for data validation. It includes improved handling for pagination
        edge cases, particularly for 404 errors when reaching beyond available pages.

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

        Raises:
            Exception: If there is an error making the API request that is not a pagination boundary issue
        """
        # Build the query parameters for filters only (not pagination)
        params = self._build_lpc_report_params(
            page=None,  # Don't include pagination in query params
            limit=None,  # Don't include pagination in query params
            borough=borough,
            object_type=object_type,
            neighborhood=neighborhood,
            search_text=search_text,
            parent_style_list=parent_style_list,
            sort_column=sort_column,
            sort_order=sort_order,
        )

        # Use path parameters for pagination, following CoreDataStore API format
        endpoint = f"/api/LpcReport/{limit}/{page}"

        try:
            # Make the API request
            response = self._make_request("GET", endpoint, params=params)

            # Ensure the response is a dictionary before validation
            if not isinstance(response, dict):
                logger.error(
                    f"API response for LPC reports was not a dictionary. Got: {type(response)}"
                )
                # Create a default error response or raise a more specific error
                # For now, let's mimic what _validate_lpc_report_response would do with an empty dict
                # or raise a TypeError directly.
                # This path indicates a problem with the API or the _make_request handling.
                raise TypeError(
                    f"Expected dictionary response from API but got {type(response).__name__}"
                )

            return self._validate_lpc_report_response(response)

        except requests.exceptions.HTTPError as e:
            # Check if this is a 404 error, which could indicate we've reached the end of available pages
            if hasattr(e, "response") and e.response and e.response.status_code == 404:
                logger.info(
                    f"Reached pagination boundary at page {page} with limit {limit}. "
                    f"This may indicate no more data is available."
                )

                # Create an empty response with appropriate pagination info
                empty_response = {
                    "results": [],
                    "page": page,
                    "limit": limit,
                    "total": (page - 1) * limit,  # Estimate total based on current page
                    "from_": ((page - 1) * limit) + 1,
                    "to": (page - 1) * limit,
                }

                return self._validate_lpc_report_response(empty_response)
            else:
                # For other HTTP errors, log and re-raise
                logger.error(f"HTTP error getting LPC reports: {e}")
                raise Exception(f"Error getting LPC reports: {e}")
        except Exception as e:
            # For any other type of error
            logger.error(f"Error getting LPC reports: {e}")
            raise Exception(f"Error getting LPC reports: {e}")

    def _build_lpc_report_params(
        self,
        page: Optional[int] = 1,
        limit: Optional[int] = 10,
        borough: Optional[str] = None,
        object_type: Optional[str] = None,
        neighborhood: Optional[str] = None,
        search_text: Optional[str] = None,
        parent_style_list: Optional[List[str]] = None,
        sort_column: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build query parameters for the LpcReport API endpoint.

        Args:
            Same as get_lpc_reports

        Returns:
            Dict of query parameters to send to the API
        """
        # Build the query parameters
        params: Dict[str, Any] = {}

        # Only add pagination to query params if explicitly requested
        # (now these will normally be passed as path parameters)
        if limit is not None:
            params["limit"] = limit
        if page is not None:
            params["page"] = page

        # Add optional filters if provided
        if borough:
            params["Borough"] = borough
        if object_type:
            params["ObjectType"] = object_type
        if neighborhood:
            params["Neighborhood"] = neighborhood
        if search_text:
            params["SearchText"] = search_text
        if parent_style_list:
            params["ParentStyleList"] = parent_style_list
        if sort_column:
            params["SortColumn"] = sort_column
        if sort_order:
            params["SortOrder"] = sort_order

        return params

    def _ensure_pagination_fields(self, mapped_response: Dict[str, Any]) -> None:
        """Ensure essential pagination fields (limit, page, total) are present and valid."""
        current_results = mapped_response.get("results", [])
        num_results = len(current_results) if isinstance(current_results, list) else 0

        # Limit
        limit_val = mapped_response.get("limit")
        if not isinstance(limit_val, int) or limit_val < 0:
            mapped_response["limit"] = num_results

        # Page
        page_val = mapped_response.get("page")
        if not isinstance(page_val, int) or page_val <= 0:
            mapped_response["page"] = 1

        # Total
        total_val = mapped_response.get("total")
        if not isinstance(total_val, int) or total_val < 0:
            mapped_response["total"] = num_results

    def _calculate_from_field(self, mapped_response: Dict[str, Any]) -> None:
        """Calculate the 'from_' field if missing or invalid."""
        from_val = mapped_response.get("from_")
        current_page_for_from = mapped_response.get("page", 1)
        current_limit_for_from = mapped_response.get("limit", 0)

        if not isinstance(from_val, int) or from_val <= 0:
            page_to_calc = (
                current_page_for_from
                if isinstance(current_page_for_from, int) and current_page_for_from > 0
                else 1
            )
            limit_to_calc = (
                current_limit_for_from
                if isinstance(current_limit_for_from, int)
                and current_limit_for_from >= 0
                else 0
            )
            mapped_response["from_"] = (page_to_calc - 1) * limit_to_calc + 1

    def _calculate_to_field(self, mapped_response: Dict[str, Any]) -> None:
        """Calculate the 'to' field if missing or invalid."""
        to_val = mapped_response.get("to")
        current_from_for_to = mapped_response.get("from_", 1)
        current_limit_for_to = mapped_response.get("limit", 0)
        current_total_for_to = mapped_response.get("total", 0)

        if not isinstance(to_val, int) or to_val < 0:
            from_to_calc = (
                current_from_for_to
                if isinstance(current_from_for_to, int) and current_from_for_to > 0
                else 1
            )
            limit_to_calc = (
                current_limit_for_to
                if isinstance(current_limit_for_to, int) and current_limit_for_to >= 0
                else 0
            )
            total_to_calc = (
                current_total_for_to
                if isinstance(current_total_for_to, int) and current_total_for_to >= 0
                else 0
            )

            calculated_to = from_to_calc + limit_to_calc - 1
            final_to = min(calculated_to, total_to_calc)
            mapped_response["to"] = max(final_to, from_to_calc - 1)

    def _validate_lpc_report_response(
        self, response: dict[str, Any]
    ) -> LpcReportResponse:
        """Validate the API response and convert to a LpcReportResponse."""
        mapped_response = dict(response)  # Create a new mutable dict

        # Map API keys to model field names
        if "totalCount" in mapped_response:
            mapped_response["total"] = mapped_response.pop("totalCount")

        mapped_response.pop("pageCount", None)  # Not used by LpcReportResponse model

        if "from" in mapped_response:
            if "from_" not in mapped_response:
                mapped_response["from_"] = mapped_response.pop("from")
            else:
                mapped_response.pop("from")

        # Ensure 'results' is a list of dicts.
        raw_results = mapped_response.get("results")
        if not isinstance(raw_results, list):
            logger.warning(
                f"API 'results' field was not a list or was missing, got {type(raw_results)}. "
                f"Defaulting to empty list."
            )
            mapped_response["results"] = []
        else:
            mapped_response["results"] = [
                item if isinstance(item, dict) else {} for item in raw_results
            ]

        # Ensure and calculate pagination fields
        self._ensure_pagination_fields(mapped_response)
        self._calculate_from_field(mapped_response)
        self._calculate_to_field(mapped_response)

        try:
            validated_response = LpcReportResponse(**mapped_response)
        except Exception as e:
            logger.error(
                f"Pydantic validation error in _validate_lpc_report_response. "
                f"Input data to model: {mapped_response}. Error: {e}"
            )
            raise
        return validated_response

    def get_all_landmarks(self, limit: Optional[int] = None) -> LpcReportResponse:
        """Get all landmarks.

        This method retrieves landmarks by automatically handling pagination.
        If a limit is provided, it will return only up to that number of landmarks.
        Otherwise, it attempts to retrieve all available landmarks by making
        multiple paginated requests as needed.

        Args:
            limit: Maximum number of landmarks to return (optional)

        Returns:
            LpcReportResponse object containing landmark information and pagination data
        """
        try:
            # Get the total count for accurate pagination
            total_records = self.get_total_record_count()
            if total_records == 0:
                logger.warning("No landmarks found or unable to determine total count")

            # Determine how many records we need to fetch
            records_to_fetch = min(limit, total_records) if limit else total_records
            if records_to_fetch == 0:
                # Return empty response if no records to fetch
                return self._validate_lpc_report_response(
                    self._create_empty_landmark_response(limit=0)
                )

            # Configure optimal page size for fetching
            page_size = min(
                100, records_to_fetch
            )  # Use up to 100 records per page for efficiency

            # For simple cases where one page is enough, just use get_lpc_reports directly
            if records_to_fetch <= page_size:
                return self.get_lpc_reports(page=1, limit=records_to_fetch)

            # For multiple pages, we need to fetch all pages and combine results
            all_results = self._fetch_paginated_landmarks(records_to_fetch, page_size)

            # Ensure we don't exceed the requested limit (if specified)
            if limit and len(all_results) > limit:
                all_results = all_results[:limit]

            # Create a combined response
            combined_response = {
                "results": [
                    result.model_dump() if hasattr(result, "model_dump") else result
                    for result in all_results
                ],
                "page": 1,  # We present this as a single page of results
                "limit": len(all_results),
                "total": total_records,
                "from_": 1,
                "to": len(all_results),
            }

            return self._validate_lpc_report_response(combined_response)

        except Exception as e:
            logger.error(f"Error getting all landmarks: {e}")
            # Create an empty response for error cases
            return self._validate_lpc_report_response(
                self._create_empty_landmark_response()
            )

    def _create_empty_landmark_response(self, limit: int = 100) -> Dict[str, Any]:
        """Create an empty landmark response object.

        Args:
            limit: The page size limit

        Returns:
            Empty response dictionary with pagination fields
        """
        return {
            "results": [],
            "page": 1,
            "limit": limit,
            "total": 0,
            "from_": 1,
            "to": 0,
        }

    def _fetch_paginated_landmarks(
        self, records_to_fetch: int, page_size: int
    ) -> List[Any]:
        """Fetch landmarks using pagination.

        Args:
            records_to_fetch: Total number of records to fetch
            page_size: Number of records per page

        Returns:
            List of landmark results
        """
        all_results = []
        pages_needed = (
            records_to_fetch + page_size - 1
        ) // page_size  # Ceiling division

        for page in range(1, pages_needed + 1):
            # For the last page, adjust the limit if needed
            if page == pages_needed and records_to_fetch % page_size != 0:
                current_page_size = records_to_fetch % page_size
            else:
                current_page_size = page_size

            # Get this page of results
            page_response = self.get_lpc_reports(page=page, limit=current_page_size)

            # Add results to our collection
            if hasattr(page_response, "results") and page_response.results:
                all_results.extend(page_response.results)

            # Stop if we've collected enough records or hit the end
            if len(all_results) >= records_to_fetch or not page_response.results:
                break

        return all_results

    def search_landmarks(self, search_term: str) -> LpcReportResponse:
        """Search for landmarks by name or other attributes.

        Args:
            search_term: Search term

        Returns:
            LpcReportResponse object containing landmark information matching the search term
        """
        try:
            # Use the get_lpc_reports method which already returns LpcReportResponse
            return self.get_lpc_reports(
                page=1, limit=10, search_text=search_term  # Default to 10 results
            )
        except Exception as e:
            logger.error(f"Error searching landmarks: {e}")
            # Create an empty response for error cases
            empty_response = {
                "results": [],
                "page": 1,
                "limit": 10,
                "total": 0,
                "from_": 1,
                "to": 0,
            }
            return self._validate_lpc_report_response(empty_response)

    def get_landmark_metadata(self, landmark_id: str) -> Dict[str, Any]:
        """Get metadata for a landmark suitable for storing with vector embeddings.

        Args:
            landmark_id: ID of the landmark

        Returns:
            Dictionary containing landmark metadata
        """
        # Get landmark information
        landmark = self.get_landmark_by_id(landmark_id)

        if not landmark:
            return {"landmark_id": landmark_id}

        # Extract relevant metadata fields
        metadata = {
            "landmark_id": landmark_id,
            "name": landmark.name,
            "location": landmark.street or "",
            "borough": landmark.borough or "",
            "type": landmark.objectType or "",
            "designation_date": str(landmark.dateDesignated or ""),
            "architect": landmark.architect or "",
            "style": landmark.style or "",
            "neighborhood": landmark.neighborhood or "",
        }

        return metadata

    def get_landmark_buildings(
        self, landmark_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get buildings associated with a landmark.

        Args:
            landmark_id: ID of the landmark (LP number)
            limit: Maximum number of buildings to return

        Returns:
            List of dictionaries containing building information
        """
        try:
            # Ensure landmark_id is properly formatted with LP prefix
            if not landmark_id.startswith("LP-"):
                lpc_number = f"LP-{landmark_id.zfill(5)}"
            else:
                lpc_number = landmark_id

            # Make the API request
            response = self._make_request(
                "GET",
                f"/api/LpcReport/landmark/{limit}/1",
                params={"LpcNumber": lpc_number},
            )

            # First check if we have results in a container structure
            if isinstance(response, dict) and "results" in response:
                response = response["results"]

            # The response is an array of landmark buildings
            buildings = []
            if response and isinstance(response, list):
                for building in response:
                    if not isinstance(building, dict):
                        continue
                    # Get BBL value and handle empty/none values properly
                    bbl_value = building.get("bbl")
                    building_info = {
                        "name": building.get("name", ""),
                        "address": building.get("designatedAddress", ""),
                        "bbl": (
                            bbl_value if bbl_value else None
                        ),  # Use None if BBL is empty or missing
                        "bin": building.get("binNumber", None),
                        "block": building.get("block", None),
                        "lot": building.get("lot", None),
                        "borough": building.get("boroughId", ""),
                        "latitude": building.get("latitude", None),
                        "longitude": building.get("longitude", None),
                        "designated_date": building.get("designatedDate", ""),
                    }
                    buildings.append(building_info)

            return buildings

        except Exception as e:
            logger.error(f"Error getting landmark buildings: {e}")
            return []

    def get_landmark_photos(
        self, landmark_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get photo archive items for a landmark.

        Args:
            landmark_id: ID of the landmark (LP number)
            limit: Maximum number of photos to return

        Returns:
            List of dictionaries containing photo information
        """
        try:
            # Ensure landmark_id is properly formatted with LP prefix
            if not landmark_id.startswith("LP-"):
                lpc_id = f"LP-{landmark_id.zfill(5)}"
            else:
                lpc_id = landmark_id

            # Make the API request
            response = self._make_request(
                "GET", f"/api/PhotoArchive/{limit}/1", params={"LpcId": lpc_id}
            )

            photos = []
            if isinstance(response, dict) and "results" in response:
                for photo in response["results"]:
                    if not isinstance(photo, dict):
                        continue
                    photo_info = {
                        "id": photo.get("id", None),
                        "title": photo.get("title", ""),
                        "description": photo.get("description", ""),
                        "collection": photo.get("collection", ""),
                        "photo_url": photo.get("photoUrl", ""),
                        "date_period": f"{photo.get('startDate', '')} - {photo.get('endDate', '')}",
                    }
                    photos.append(photo_info)

            return photos

        except Exception as e:
            logger.error(f"Error getting landmark photos: {e}")
            return []

    def get_landmark_pluto_data(self, landmark_id: str) -> List[Dict[str, Any]]:
        """Get PLUTO data for a landmark.

        Args:
            landmark_id: ID of the landmark (LP number)

        Returns:
            List of dictionaries containing PLUTO data that can be converted to PlutoDataModel
        """
        try:
            # Ensure landmark_id is properly formatted with LP prefix
            if not landmark_id.startswith("LP-"):
                lpc_id = f"LP-{landmark_id.zfill(5)}"
            else:
                lpc_id = landmark_id

            # Make the API request
            response = self._make_request("GET", f"/api/Pluto/{lpc_id}")

            # The response is an array of PLUTO records
            if response and isinstance(response, list):
                # Ensure all required fields are present in each record
                # This helps with conversion to PlutoDataModel later
                standardized_records: List[Dict[str, Any]] = []
                for record in response:
                    if isinstance(record, dict):
                        # Add any missing fields with None value
                        standardized_record = {
                            "yearBuilt": record.get("yearBuilt"),
                            "landUse": record.get("landUse"),
                            "historicDistrict": record.get("historicDistrict"),
                            "zoneDist1": record.get("zoneDist1"),
                        }
                        standardized_records.append(standardized_record)

                return standardized_records
            return []

        except Exception as e:
            logger.error(f"Error getting landmark PLUTO data: {e}")
            return []

    def get_neighborhoods(self, borough: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of neighborhoods.

        Args:
            borough: Optional borough to filter neighborhoods

        Returns:
            List of neighborhoods
        """
        try:
            params = {"borough": borough} if borough else None
            response = self._make_request(
                "GET", "/api/Reference/neighborhood", params=params
            )
            if response and isinstance(response, list):
                return cast(List[Dict[str, Any]], response)
            return []

        except Exception as e:
            logger.error(f"Error getting neighborhoods: {e}")
            return []

    def get_boroughs(self) -> List[str]:
        """Get list of boroughs.

        Returns:
            List of borough names
        """
        try:
            response = self._make_request("GET", "/api/Reference/borough")
            if response and isinstance(response, list):
                return cast(List[str], response)
            return []

        except Exception as e:
            logger.error(f"Error getting boroughs: {e}")
            return []

    def get_object_types(self) -> List[str]:
        """Get list of landmark object types.

        Returns:
            List of object type names
        """
        try:
            response = self._make_request("GET", "/api/Reference/objectType")
            if response and isinstance(response, list):
                return cast(List[str], response)
            return []

        except Exception as e:
            logger.error(f"Error getting object types: {e}")
            return []

    def get_wikipedia_articles(self, landmark_id: str) -> List[WikipediaArticleModel]:
        """Get Wikipedia articles associated with a landmark.

        Args:
            landmark_id: ID of the landmark (LP number)

        Returns:
            List of WikipediaArticleModel objects
        """
        try:
            # Ensure landmark_id is properly formatted with LP prefix
            if not landmark_id.startswith("LP-"):
                lpc_id = f"LP-{landmark_id.zfill(5)}"
            else:
                lpc_id = landmark_id

            # Make the API request using the correct WebContent/batch endpoint with POST
            json_data = {"lpcIds": [lpc_id]}
            logger.info(f"Requesting Wikipedia articles with data: {json_data}")
            response = self._make_request(
                "POST", "/api/WebContent/batch", json_data=json_data
            )

            # Log the raw response for debugging
            logger.info(f"Raw API response: {response}")

            articles = []
            # Check if response is a list or dict with items
            if response:
                items_to_process = self._extract_items_to_process(response, lpc_id)

                # Process each article
                for item in items_to_process:
                    article = self._create_wikipedia_article(item, landmark_id)
                    if article:
                        articles.append(article)

            logger.info(
                f"Retrieved {len(articles)} Wikipedia articles for landmark {landmark_id}"
            )
            return articles

        except Exception as e:
            logger.error(
                f"Error getting Wikipedia articles for landmark {landmark_id}: {e}"
            )
            return []

    def _format_lpc_id(self, landmark_id: str) -> str:
        """Ensure landmark_id is properly formatted with LP prefix.

        Args:
            landmark_id: The original landmark ID

        Returns:
            Properly formatted LP ID
        """
        if not landmark_id.startswith("LP-"):
            return f"LP-{landmark_id.zfill(5)}"
        return landmark_id

    def _extract_items_to_process(
        self,
        response: Union[Dict[str, Any], List[Dict[str, Any]], List[str]],
        lpc_id: str,
    ) -> List[Dict[str, Any]]:
        """Extract items to process from different response formats.

        Args:
            response: API response
            lpc_id: Landmark ID

        Returns:
            List of items to process
        """
        items_to_process: List[Dict[str, Any]] = []

        if isinstance(response, list):
            items_to_process = cast(List[Dict[str, Any]], response)
        elif isinstance(response, dict) and "items" in response:
            items_to_process = cast(List[Dict[str, Any]], response.get("items", []))
        elif isinstance(response, dict):
            # Check for lpc_id in response (case-insensitive)
            lpc_id_lower = lpc_id.lower()
            found_key = None
            for key in response:
                if isinstance(key, str) and key.lower() == lpc_id_lower:
                    found_key = key
                    break

            if found_key:
                items_to_process = cast(
                    List[Dict[str, Any]], response.get(found_key, [])
                )

        return items_to_process

    def _create_wikipedia_article(
        self, item: Dict[str, Any], landmark_id: str
    ) -> Optional[WikipediaArticleModel]:
        """Create a Wikipedia article model from an API response item.

        Args:
            item: API response item
            landmark_id: Landmark ID

        Returns:
            WikipediaArticleModel if valid, None otherwise
        """
        if not isinstance(item, dict):
            return None

        # Check if this is a Wikipedia article (case-insensitive comparison)
        record_type = item.get("recordType", "")
        if isinstance(record_type, str) and record_type.lower() == "wikipedia":
            article = WikipediaArticleModel(
                id=item.get("id"),
                lpNumber=landmark_id,
                url=item.get("url", ""),
                title=item.get("title", ""),
                recordType="Wikipedia",
                content=item.get(
                    "content", ""
                ),  # Get content from the item or use empty string
            )
            logger.debug(f"Found Wikipedia article: {article.title}")
            return article

        return None

    def get_total_record_count(self) -> int:
        """Get the total count of landmarks in the CoreDataStore.

        Returns:
            Total number of landmark records available
        """
        try:
            # Make a request with minimal data (1 record on page 1)
            # to get just the pagination metadata
            response = self._make_request("GET", "/api/LpcReport/1/1")

            if isinstance(response, dict):
                if "total" in response:
                    return int(response["total"])
                # Alternative field names that might contain the count
                for field in ["totalRecords", "count", "totalCount"]:
                    if field in response and response[field] is not None:
                        return int(response[field])

            # If we couldn't find a count, make a second attempt with parameters
            response = self._make_request(
                "GET", "/api/LpcReport", params={"page": 1, "limit": 1}
            )
            if isinstance(response, dict) and "total" in response:
                return int(response["total"])

            logger.warning("Could not determine total record count, returning 0")
            return 0
        except Exception as e:
            logger.error(f"Error getting total record count: {e}")
            return 0

    def get_landmark_pdf_url(self, landmark_id: str) -> Optional[str]:
        """Get the PDF report URL for a landmark.

        Args:
            landmark_id: ID of the landmark (LP number, e.g., "LP-00001")

        Returns:
            The PDF report URL, or None if not found
        """
        try:
            # Ensure landmark_id is properly formatted with LP prefix
            if not landmark_id.startswith("LP-"):
                lpc_id = f"LP-{landmark_id.zfill(5)}"
            else:
                lpc_id = landmark_id

            # Get the LPC report using the API
            response = self._make_request("GET", f"/api/LpcReport/{lpc_id}")

            if not response:
                logger.warning(f"Landmark not found with ID: {landmark_id}")
                return None

            # Check if response is a dictionary before accessing attributes
            if not isinstance(response, dict):
                logger.error(
                    f"Expected dictionary response but got {type(response).__name__}"
                )
                return None

            # Extract the PDF report URL
            pdf_url = response.get("pdfReportUrl")
            if not pdf_url:
                logger.warning(
                    f"No PDF report URL found for landmark ID: {landmark_id}"
                )
                return None

            # Ensure we return a string, not Any
            return str(pdf_url) if pdf_url is not None else None

        except Exception as e:
            logger.error(f"Error getting PDF report URL for landmark: {e}")
            return None
