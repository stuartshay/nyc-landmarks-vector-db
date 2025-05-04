"""
Database client interface for the NYC Landmarks Vector Database.

This module provides a unified interface for database operations,
using the CoreDataStore API to retrieve landmark information.
"""

import logging
from typing import Any, Dict, List, Optional

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class DbClient:
    """Database client interface for CoreDataStore API."""

    def __init__(self) -> None:
        """Initialize the CoreDataStore API client."""
        logger.info("Using CoreDataStore API client")
        self.client = CoreDataStoreAPI()

    def get_landmark_by_id(self, landmark_id: str) -> Optional[Dict[str, Any]]:
        """Get landmark information by ID.

        Args:
            landmark_id: ID of the landmark (LP number)

        Returns:
            Dictionary containing landmark information, or None if not found
        """
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
    ) -> List[Dict[str, Any]]:
        """Get a page of landmarks.

        Args:
            page_size: Number of landmarks per page
            page: Page number (starting from 1)

        Returns:
            List of landmarks for the requested page
        """
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

    def get_landmark_pdf_url(self, landmark_id: str) -> Optional[str]:
        """Get the PDF report URL for a landmark.

        Args:
            landmark_id: ID of the landmark

        Returns:
            URL string if available, None otherwise
        """
        if hasattr(self.client, "get_landmark_pdf_url"):
            return self.client.get_landmark_pdf_url(landmark_id)
        return None

    def get_landmark_buildings(
        self, landmark_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get buildings associated with a landmark.

        Args:
            landmark_id: ID of the landmark
            limit: Maximum number of buildings to return

        Returns:
            List of buildings
        """
        if hasattr(self.client, "get_landmark_buildings"):
            return self.client.get_landmark_buildings(landmark_id, limit)
        return []

    def get_landmark_photos(
        self, landmark_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get photo archive items for a landmark.

        Args:
            landmark_id: ID of the landmark
            limit: Maximum number of photos to return

        Returns:
            List of photos
        """
        if hasattr(self.client, "get_landmark_photos"):
            return self.client.get_landmark_photos(landmark_id, limit)
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
        if not hasattr(self.client, "_make_request"):
            return 0

        try:
            # Make a minimal request with page size 1
            response = self.client._make_request("GET", "/api/LpcReport/1/1")

            # Extract the total count from the response metadata
            if isinstance(response, dict):
                # Check for different possible keys that might contain the total count
                for key in ["totalCount", "total", "count", "totalRecords"]:
                    if key in response and response[key]:
                        total_count = int(response[key])
                        logger.info(
                            f"Retrieved total record count: {total_count} from key: {key}"
                        )
                        return total_count
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
    return DbClient()
