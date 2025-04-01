"""
CoreDataStore API client module for NYC Landmarks Vector Database.

This module handles connections to the CoreDataStore REST API
that provides NYC landmark information.
"""

import logging
from typing import Any, Dict, List, Optional, Union, cast
from urllib.parse import urljoin

import requests

from nyc_landmarks.config.settings import settings

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

        logger.info(f"Initialized CoreDataStore API client")

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
            Response data as dictionary

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
                return response.json()
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

            # Convert the response to a format compatible with what the PostgresDB provided
            landmark = {
                "id": response.get("lpNumber", ""),
                "name": response.get("name", ""),
                "location": response.get("street", ""),
                "borough": response.get("borough", ""),
                "type": response.get("objectType", ""),
                "designation_date": response.get("dateDesignated", ""),
                "description": "",  # API doesn't seem to provide a description field
            }

            return landmark

        except Exception as e:
            logger.error(f"Error getting landmark by ID: {e}")
            return None

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
            if response and "results" in response:
                # Convert the results to the format expected by the application
                for item in response["results"]:
                    landmark = {
                        "id": item.get("lpNumber", ""),
                        "name": item.get("name", ""),
                        "location": item.get("street", ""),
                        "borough": item.get("borough", ""),
                        "type": item.get("objectType", ""),
                        "designation_date": item.get("dateDesignated", ""),
                        "description": "",  # API doesn't seem to provide a description field
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
            if response and "results" in response:
                # Convert the results to the format expected by the application
                for item in response["results"]:
                    landmark = {
                        "id": item.get("lpNumber", ""),
                        "name": item.get("name", ""),
                        "location": item.get("street", ""),
                        "borough": item.get("borough", ""),
                        "type": item.get("objectType", ""),
                        "designation_date": item.get("dateDesignated", ""),
                        "description": "",  # API doesn't seem to provide a description field
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
            if response and "results" in response:
                for photo in response["results"]:
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

            # Extract the PDF report URL
            pdf_url = response.get("pdfReportUrl")
            if not pdf_url:
                logger.warning(
                    f"No PDF report URL found for landmark ID: {landmark_id}"
                )
                return None

            return pdf_url

        except Exception as e:
            logger.error(f"Error getting PDF report URL for landmark: {e}")
            return None
