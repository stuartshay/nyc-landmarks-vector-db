"""
Database client interface for the NYC Landmarks Vector Database.

This module provides a unified interface for database operations,
using the CoreDataStore API to retrieve landmark information.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union, cast

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class DbClient:
    """Database client interface for CoreDataStore API."""

    def __init__(self):
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

        # For PostgreSQL or other clients that don't support pagination directly,
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


def get_db_client() -> DbClient:
    """Get a database client instance.

    Returns:
        DbClient instance
    """
    return DbClient()
