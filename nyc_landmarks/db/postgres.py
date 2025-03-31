"""
PostgreSQL database module for NYC Landmarks Vector Database.

This module handles connections to the existing PostgreSQL database
that contains NYC landmark information.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from urllib.parse import quote_plus

import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session

from nyc_landmarks.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class PostgresDB:
    """PostgreSQL database operations."""
    
    def __init__(self):
        """Initialize the PostgreSQL database connection."""
        self.connection_string = settings.POSTGRES_CONNECTION_STRING
        self.engine = None
        self.Session = None
        
        # Initialize database connection if connection string is provided
        if self.connection_string:
            try:
                # Create SQLAlchemy engine
                self.engine = create_engine(self.connection_string)
                
                # Create sessionmaker
                self.Session = sessionmaker(bind=self.engine)
                
                logger.info(f"Initialized PostgreSQL connection")
            except Exception as e:
                logger.error(f"Error connecting to PostgreSQL: {e}")
                raise
        else:
            logger.warning("PostgreSQL connection string not provided")
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a SQL query and return the results.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query (optional)
            
        Returns:
            List of dictionaries containing the query results
        """
        if not self.engine:
            logger.error("PostgreSQL connection not initialized")
            return []
        
        try:
            with self.engine.connect() as connection:
                # Execute the query
                if params:
                    result = connection.execute(text(query), params)
                else:
                    result = connection.execute(text(query))
                
                # Get column names
                columns = result.keys()
                
                # Convert result to list of dictionaries
                results = [dict(zip(columns, row)) for row in result]
                
                logger.info(f"Query returned {len(results)} results")
                return results
        except SQLAlchemyError as e:
            logger.error(f"Error executing query: {e}")
            return []
    
    def get_landmark_by_id(self, landmark_id: str) -> Optional[Dict[str, Any]]:
        """Get landmark information by ID.
        
        Args:
            landmark_id: ID of the landmark
            
        Returns:
            Dictionary containing landmark information, or None if not found
        """
        query = """
        SELECT *
        FROM Landmark
        WHERE id = :landmark_id
        """
        
        results = self.execute_query(query, {"landmark_id": landmark_id})
        
        if results:
            return results[0]
        else:
            logger.warning(f"Landmark not found with ID: {landmark_id}")
            return None
    
    def get_all_landmarks(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all landmarks.
        
        Args:
            limit: Maximum number of landmarks to return (optional)
            
        Returns:
            List of dictionaries containing landmark information
        """
        query = """
        SELECT *
        FROM Landmark
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        return self.execute_query(query)
    
    def search_landmarks(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for landmarks by name or description.
        
        Args:
            search_term: Search term
            
        Returns:
            List of dictionaries containing landmark information
        """
        query = """
        SELECT *
        FROM Landmark
        WHERE 
            name ILIKE :search_pattern OR
            description ILIKE :search_pattern
        """
        
        search_pattern = f"%{search_term}%"
        return self.execute_query(query, {"search_pattern": search_pattern})
    
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
