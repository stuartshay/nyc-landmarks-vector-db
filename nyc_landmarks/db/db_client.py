"""
Database client module for NYC Landmarks Vector Database.

This module provides a unified interface for database operations that can
switch between PostgreSQL and CoreDataStore API based on configuration.
"""

import logging
from typing import Any, Dict, List, Optional, Union, cast

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.postgres import PostgresDB
from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class DbClient:
    """Database client that can switch between PostgreSQL and CoreDataStore API."""

    def __init__(self) -> None:
        """Initialize the database client.

        The client uses either PostgreSQL or CoreDataStore API based on settings.
        """
        self.use_api = settings.COREDATASTORE_USE_API

        # Initialize the appropriate client based on settings
        if self.use_api:
            logger.info("Using CoreDataStore API for database operations")
            self.api_client = CoreDataStoreAPI()
            self.postgres_client = None
        else:
            logger.info("Using PostgreSQL for database operations")
            self.postgres_client = PostgresDB()
            self.api_client = None

    def get_landmark_by_id(self, landmark_id: str) -> Optional[Dict[str, Any]]:
        """Get landmark information by ID.

        Args:
            landmark_id: ID of the landmark

        Returns:
            Dictionary containing landmark information, or None if not found
        """
        if self.use_api and self.api_client:
            return self.api_client.get_landmark_by_id(landmark_id)
        elif self.postgres_client:
            return self.postgres_client.get_landmark_by_id(landmark_id)
        return None

    def get_all_landmarks(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all landmarks.

        Args:
            limit: Maximum number of landmarks to return (optional)

        Returns:
            List of dictionaries containing landmark information
        """
        if self.use_api and self.api_client:
            return self.api_client.get_all_landmarks(limit)
        elif self.postgres_client:
            return self.postgres_client.get_all_landmarks(limit)
        return []

    def search_landmarks(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for landmarks by name or description.

        Args:
            search_term: Search term

        Returns:
            List of dictionaries containing landmark information
        """
        if self.use_api and self.api_client:
            return self.api_client.search_landmarks(search_term)
        elif self.postgres_client:
            return self.postgres_client.search_landmarks(search_term)
        return []

    def get_landmark_metadata(self, landmark_id: str) -> Dict[str, Any]:
        """Get metadata for a landmark suitable for storing with vector embeddings.

        Args:
            landmark_id: ID of the landmark

        Returns:
            Dictionary containing landmark metadata
        """
        if self.use_api and self.api_client:
            return self.api_client.get_landmark_metadata(landmark_id)
        elif self.postgres_client:
            return self.postgres_client.get_landmark_metadata(landmark_id)
        return {"landmark_id": landmark_id}

    def get_landmark_buildings(self, landmark_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get buildings associated with a landmark.

        Args:
            landmark_id: ID of the landmark
            limit: Maximum number of buildings to return

        Returns:
            List of dictionaries containing building information
        """
        if self.use_api and self.api_client:
            return self.api_client.get_landmark_buildings(landmark_id, limit)
        # PostgreSQL client doesn't have this method
        return []

    def get_landmark_photos(self, landmark_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get photo archive items for a landmark.

        Args:
            landmark_id: ID of the landmark
            limit: Maximum number of photos to return

        Returns:
            List of dictionaries containing photo information
        """
        if self.use_api and self.api_client:
            return self.api_client.get_landmark_photos(landmark_id, limit)
        # PostgreSQL client doesn't have this method
        return []

    def get_landmark_pluto_data(self, landmark_id: str) -> List[Dict[str, Any]]:
        """Get PLUTO data for a landmark.

        Args:
            landmark_id: ID of the landmark

        Returns:
            List of dictionaries containing PLUTO data
        """
        if self.use_api and self.api_client:
            return self.api_client.get_landmark_pluto_data(landmark_id)
        # PostgreSQL client doesn't have this method
        return []

    def get_neighborhoods(self, borough: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of neighborhoods.

        Args:
            borough: Optional borough to filter neighborhoods

        Returns:
            List of neighborhoods
        """
        if self.use_api and self.api_client:
            return self.api_client.get_neighborhoods(borough)
        # PostgreSQL client doesn't have this method
        return []

    def get_boroughs(self) -> List[str]:
        """Get list of boroughs.

        Returns:
            List of borough names
        """
        if self.use_api and self.api_client:
            return self.api_client.get_boroughs()
        # PostgreSQL client doesn't have this method
        return []

    def get_object_types(self) -> List[str]:
        """Get list of landmark object types.

        Returns:
            List of object type names
        """
        if self.use_api and self.api_client:
            return self.api_client.get_object_types()
        # PostgreSQL client doesn't have this method
        return []

    def get_architecture_styles(self) -> List[str]:
        """Get list of architecture styles.

        Returns:
            List of architecture style names
        """
        if self.use_api and self.api_client:
            return self.api_client.get_architecture_styles()
        # PostgreSQL client doesn't have this method
        return []
