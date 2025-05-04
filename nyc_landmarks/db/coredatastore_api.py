"""
CoreDataStore API client module for NYC Landmarks Vector Database.

This module handles connections to the CoreDataStore REST API
that provides NYC landmark information and associated web content like Wikipedia articles.
"""

import logging
from typing import Any, Dict, List, Optional, Union, cast
from urllib.parse import urljoin

import requests

from nyc_landmarks.config.settings import settings
from nyc_landmarks.models.landmark_models import LpcReportResponse
from nyc_landmarks.models.wikipedia_models import WikipediaArticleModel

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class CoreDataStoreAPI:
    """CoreDataStore API client for landmark operations."""

    def __init__(self) -> None:
        """Initialize the CoreDataStore API client."""
        self.base_url = "https://api.coredatastore.com"
        self.api_key = settings.COREDATASTORE_API_KEY
        self.headers = {}

        # Set up authorization header if API key is provided
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

        logger.info("Initialized CoreDataStore API client")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict[str, Any], List[Any]]:
        """Make a request to the CoreDataStore API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters (optional)
            json_data: JSON data for POST/PUT requests (optional)

        Returns:
            Response data as dictionary or list

        Raises:
            Exception: If the request fails
        """
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

            # Raise exception for error status codes
            response.raise_for_status()

            # Return JSON response if available
            if response.content:
                json_response = response.json()
                # Ensure we return the correct type
                if isinstance(json_response, (dict, list)):
                    return json_response
                logger.warning(f"Unexpected response type: {type(json_response)}")
                return {}
            return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}")
            raise Exception(f"Error making API request: {e}")

    def get_landmark_by_id(self, landmark_id: str) -> Optional[Dict[str, Any]]:
        """Get landmark information by ID.

        Args:
            landmark_id: ID of the landmark (LP number, e.g., "LP-00001")

        Returns:
            Dictionary containing landmark information, or None if not found
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

            # Convert the response to a format compatible with what the PostgresDB provided
            landmark = {
                "id": response.get("lpNumber", ""),
                "name": response.get("name", ""),
                "location": response.get("street", ""),
                "borough": response.get("borough", ""),
                "type": response.get("objectType", ""),
                "designation_date": response.get("dateDesignated", ""),
                "description": "",  # API doesn't seem to provide a description field
                "architect": response.get("architect", ""),
                "style": response.get("style", ""),
                "neighborhood": response.get("neighborhood", ""),
                "pdfReportUrl": response.get("pdfReportUrl", ""),
                "photoUrl": response.get("photoUrl", ""),
            }

            return landmark

        except Exception as e:
            logger.error(f"Error getting landmark by ID: {e}")
            return None

    def get_landmarks_page(
        self, page_size: int = 10, page: int = 1
    ) -> List[Dict[str, Any]]:
        """Get a page of landmarks directly using the API's pagination.

        Args:
            page_size: Number of landmarks per page
            page: Page number (starting from 1)

        Returns:
            List of landmarks for the requested page
        """
        try:
            # Make API request with pagination parameters
            response = self._make_request("GET", f"/api/LpcReport/{page_size}/{page}")

            results = []
            if isinstance(response, dict) and "results" in response:
                # Convert the API response format to our internal format
                for item in response["results"]:
                    if not isinstance(item, dict):
                        continue
                    landmark = {
                        "id": item.get("lpNumber", ""),
                        "name": item.get("name", ""),
                        "location": item.get("street", ""),
                        "borough": item.get("borough", ""),
                        "type": item.get("objectType", ""),
                        "designation_date": item.get("dateDesignated", ""),
                        "description": "",  # API doesn't seem to provide a description field
                        "architect": item.get("architect", ""),
                        "style": item.get("style", ""),
                        "neighborhood": item.get("neighborhood", ""),
                        "pdfReportUrl": item.get("pdfReportUrl", ""),
                        "photoUrl": item.get("photoUrl", ""),
                    }
                    results.append(landmark)

            return results

        except Exception as e:
            logger.error(f"Error getting landmarks page {page}: {e}")
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

        This method directly maps to the GetLpcReports MCP tool functionality and uses
        Pydantic models for data validation.

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
            Exception: If there is an error making the API request
        """
        try:
            # Build the query parameters and make the request
            params = self._build_lpc_report_params(
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

            # Make the API request
            endpoint = "/api/LpcReport"
            response = self._make_request("GET", endpoint, params=params)

            return self._validate_lpc_report_response(response)

        except Exception as e:
            logger.error(f"Error getting LPC reports: {e}")
            raise Exception(f"Error getting LPC reports: {e}")

    def _build_lpc_report_params(
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
    ) -> Dict[str, Any]:
        """Build query parameters for the LpcReport API endpoint.

        Args:
            Same as get_lpc_reports

        Returns:
            Dict of query parameters to send to the API
        """
        # Build the required query parameters
        params: Dict[str, Any] = {
            "limit": limit,
            "page": page,
        }

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

    def _validate_lpc_report_response(self, response: Any) -> LpcReportResponse:
        """Validate the API response and convert to a LpcReportResponse.

        Args:
            response: The raw API response

        Returns:
            LpcReportResponse: Validated response model

        Raises:
            TypeError: If response is not a dictionary
        """
        # Ensure response is a dictionary
        if not isinstance(response, dict):
            raise TypeError(
                f"Expected dictionary response but got {type(response).__name__}"
            )

        # Validate the response with our Pydantic models
        validated_response = LpcReportResponse(**response)
        return validated_response

    def get_lpc_reports_with_mcp(
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
        fields_list: Optional[List[str]] = None,
    ) -> LpcReportResponse:
        """Get LPC reports using the MCP server GetLpcReports tool.

        This method is intended for use in environments where the MCP
        server is available. It provides a Python interface to the
        MCP tool without having to directly call the use_mcp_tool function.

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
            fields_list: Optional list of fields to return

        Returns:
            LpcReportResponse object containing results and pagination info

        Raises:
            NotImplementedError: This is a placeholder that should be implemented
            by code that has access to the MCP service.
        """
        # This method is a placeholder for future implementation
        # The actual implementation would involve using an MCP tool to fetch data
        raise NotImplementedError(
            "This method requires direct MCP server integration. Use get_lpc_reports() instead."
        )

    def get_all_landmarks(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all landmarks.

        Args:
            limit: Maximum number of landmarks to return (optional)

        Returns:
            List of dictionaries containing landmark information
        """
        try:
            # Set default limit if not provided
            page_limit = min(limit or 100, 100)
            page = 1

            # Make API request
            response = self._make_request("GET", f"/api/LpcReport/{page_limit}/{page}")

            results = []
            if isinstance(response, dict) and "results" in response:
                # Convert the results to the format expected by the application
                for item in response["results"]:
                    if not isinstance(item, dict):
                        continue
                    landmark = {
                        "id": item.get("lpNumber", ""),
                        "name": item.get("name", ""),
                        "location": item.get("street", ""),
                        "borough": item.get("borough", ""),
                        "type": item.get("objectType", ""),
                        "designation_date": item.get("dateDesignated", ""),
                        "description": "",  # API doesn't seem to provide a description field
                        "architect": item.get("architect", ""),
                        "style": item.get("style", ""),
                        "neighborhood": item.get("neighborhood", ""),
                        "pdfReportUrl": item.get("pdfReportUrl", ""),
                        "photoUrl": item.get("photoUrl", ""),
                    }
                    results.append(landmark)

            # If a specific limit was provided and it's less than what we got, truncate
            if limit and len(results) > limit:
                results = results[:limit]

            return results

        except Exception as e:
            logger.error(f"Error getting all landmarks: {e}")
            return []

    def search_landmarks(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for landmarks by name or other attributes.

        Args:
            search_term: Search term

        Returns:
            List of dictionaries containing landmark information
        """
        try:
            # Use the API's search functionality
            response = self._make_request(
                "GET",
                "/api/LpcReport/10/1",  # Default to 10 results on page 1
                params={"SearchText": search_term},
            )

            results = []
            if isinstance(response, dict) and "results" in response:
                # Convert the results to the format expected by the application
                for item in response["results"]:
                    if not isinstance(item, dict):
                        continue
                    landmark = {
                        "id": item.get("lpNumber", ""),
                        "name": item.get("name", ""),
                        "location": item.get("street", ""),
                        "borough": item.get("borough", ""),
                        "type": item.get("objectType", ""),
                        "designation_date": item.get("dateDesignated", ""),
                        "description": "",  # API doesn't seem to provide a description field
                        "architect": item.get("architect", ""),
                        "style": item.get("style", ""),
                        "neighborhood": item.get("neighborhood", ""),
                        "pdfReportUrl": item.get("pdfReportUrl", ""),
                        "photoUrl": item.get("photoUrl", ""),
                    }
                    results.append(landmark)

            return results

        except Exception as e:
            logger.error(f"Error searching landmarks: {e}")
            return []

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
            "name": landmark.get("name", ""),
            "location": landmark.get("location", ""),
            "borough": landmark.get("borough", ""),
            "type": landmark.get("type", ""),
            "designation_date": str(landmark.get("designation_date", "")),
            "architect": landmark.get("architect", ""),
            "style": landmark.get("style", ""),
            "neighborhood": landmark.get("neighborhood", ""),
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

            # The response is an array of landmark buildings
            buildings = []
            if response and isinstance(response, list):
                for building in response:
                    if not isinstance(building, dict):
                        continue
                    building_info = {
                        "name": building.get("name", ""),
                        "address": building.get("designatedAddress", ""),
                        "bbl": building.get("bbl", ""),
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
            List of dictionaries containing PLUTO data
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
                return cast(List[Dict[str, Any]], response)
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

    def get_architecture_styles(self) -> List[str]:
        """Get list of architecture styles.

        Returns:
            List of architecture style names
        """
        try:
            response = self._make_request("GET", "/api/Reference/parentStyle")
            if response and isinstance(response, list):
                return cast(List[str], response)
            return []

        except Exception as e:
            logger.error(f"Error getting architecture styles: {e}")
            return []

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

    def get_wikipedia_articles(self, landmark_id: str) -> List[WikipediaArticleModel]:
        """Get Wikipedia articles associated with a landmark.

        This method queries the WebContent endpoint to retrieve Wikipedia articles
        associated with a specific landmark.

        Args:
            landmark_id: ID of the landmark (LP number, e.g., "LP-00001")

        Returns:
            List of WikipediaArticleModel objects, empty list if none found
        """
        try:
            # Ensure landmark_id is properly formatted with LP prefix
            if not landmark_id.startswith("LP-"):
                lpc_id = f"LP-{landmark_id.zfill(5)}"
            else:
                lpc_id = landmark_id

            # Make the API request
            response = self._make_request("GET", f"/api/WebContent/{lpc_id}")

            # Process the response
            articles = []
            if response and isinstance(response, list):
                for item in response:
                    # Filter for Wikipedia articles only
                    if item.get("recordType") == "Wikipedia":
                        try:
                            # Validate with Pydantic model
                            article = WikipediaArticleModel(**item)
                            articles.append(article)
                        except Exception as e:
                            logger.warning(f"Error validating Wikipedia article: {e}")
                            continue

            if not articles:
                logger.info(f"No Wikipedia articles found for landmark: {landmark_id}")
            else:
                logger.info(
                    f"Found {len(articles)} Wikipedia articles for landmark: {landmark_id}"
                )

            return articles

        except Exception as e:
            logger.error(
                f"Error getting Wikipedia articles for landmark {landmark_id}: {e}"
            )
            return []

    def get_all_landmarks_with_wikipedia(
        self, limit: Optional[int] = None
    ) -> Dict[str, List[WikipediaArticleModel]]:
        """Get all landmarks with their associated Wikipedia articles.

        This method queries all landmarks and checks each for Wikipedia articles,
        building a dictionary mapping landmark IDs to their Wikipedia articles.

        Args:
            limit: Maximum number of landmarks to check (optional)

        Returns:
            Dictionary mapping landmark IDs to lists of WikipediaArticleModel objects
        """
        try:
            # Get all landmarks
            landmarks = self.get_all_landmarks(limit)
            result = {}

            # Process each landmark to check for Wikipedia articles
            for landmark in landmarks:
                landmark_id = landmark.get("id", "")
                if not landmark_id:
                    continue

                # Get Wikipedia articles for this landmark
                articles = self.get_wikipedia_articles(landmark_id)
                if articles:
                    result[landmark_id] = articles

            logger.info(
                f"Found {len(result)} landmarks with Wikipedia articles out of {len(landmarks)} total"
            )
            return result

        except Exception as e:
            logger.error(f"Error getting landmarks with Wikipedia articles: {e}")
            return {}
