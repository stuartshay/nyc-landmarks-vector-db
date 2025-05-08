"""
Query API module for NYC Landmarks Vector Database.

This module provides API endpoints for vector search and querying
landmark information.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query as QueryParam
from pydantic import BaseModel, Field

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import DbClient
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)

# Create API router
router = APIRouter(
    prefix="/api/query",
    tags=["query"],
)


# --- Pydantic models for requests and responses ---


class TextQuery(BaseModel):
    """Text query for vector search."""

    query: str = Field(..., description="Text query for semantic search")
    landmark_id: Optional[str] = Field(
        None, description="Optional landmark ID to filter results"
    )
    top_k: int = Field(5, description="Number of results to return", ge=1, le=20)


class SearchResult(BaseModel):
    """Search result model."""

    text: str = Field(..., description="Text content of the search result")
    score: float = Field(..., description="Similarity score")
    landmark_id: str = Field(..., description="ID of the landmark")
    landmark_name: Optional[str] = Field(None, description="Name of the landmark")
    metadata: Dict[str, Any] = Field({}, description="Additional metadata")


class SearchResponse(BaseModel):
    """Response model for text search."""

    results: List[SearchResult] = Field([], description="Search results")
    query: str = Field(..., description="Original query")
    landmark_id: Optional[str] = Field(
        None, description="Landmark ID filter that was applied"
    )
    count: int = Field(0, description="Number of results")


class LandmarkInfo(BaseModel):
    """Landmark information model."""

    id: str = Field(..., description="Landmark ID")
    name: str = Field(..., description="Landmark name")
    location: Optional[str] = Field(None, description="Landmark location")
    borough: Optional[str] = Field(None, description="Borough")
    type: Optional[str] = Field(None, description="Landmark type")
    designation_date: Optional[str] = Field(None, description="Designation date")
    description: Optional[str] = Field(None, description="Description")


class LandmarkListResponse(BaseModel):
    """Response model for landmark list."""

    landmarks: List[LandmarkInfo] = Field([], description="List of landmarks")
    count: int = Field(0, description="Number of landmarks")


# --- Dependency injection functions ---


def get_embedding_generator() -> EmbeddingGenerator:
    """Get an instance of EmbeddingGenerator."""
    return EmbeddingGenerator()


def get_vector_db() -> PineconeDB:
    """Get an instance of PineconeDB."""
    return PineconeDB()


def get_db_client() -> DbClient:
    """Get an instance of DbClient."""
    from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI

    return DbClient(CoreDataStoreAPI())


# --- API endpoints ---


@router.post("/search", response_model=SearchResponse)  # type: ignore[misc]
async def search_text(
    query: TextQuery,
    embedding_generator: EmbeddingGenerator = Depends(get_embedding_generator),
    vector_db: PineconeDB = Depends(get_vector_db),
    db_client: DbClient = Depends(get_db_client),
) -> SearchResponse:
    """Search for text using vector similarity.

    Args:
        query: Text query model
        embedding_generator: EmbeddingGenerator instance
        vector_db: PineconeDB instance
        db_client: DbClient instance

    Returns:
        SearchResponse with results
    """
    try:
        # Generate embedding for the query
        query_embedding = embedding_generator.generate_embedding(query.query)

        # Prepare filter if landmark_id is provided
        filter_dict = None
        if query.landmark_id:
            filter_dict = {"landmark_id": query.landmark_id}

        # Query the vector database
        matches = vector_db.query_vectors(query_embedding, query.top_k, filter_dict)

        # Process results
        results = []
        for match in matches:
            # Extract data from match
            text = match["metadata"].get("text", "")
            landmark_id = match["metadata"].get("landmark_id", "")
            score = match["score"]

            # Get landmark name from database if available
            landmark_name = None
            landmark = db_client.get_landmark_by_id(landmark_id)
            if landmark:
                # Handle both dict and Pydantic model objects
                if isinstance(landmark, dict):
                    landmark_name = landmark.get("name")
                else:
                    landmark_name = getattr(landmark, "name", None)

            # Create SearchResult
            result = SearchResult(
                text=text,
                score=score,
                landmark_id=landmark_id,
                landmark_name=landmark_name,
                metadata={k: v for k, v in match["metadata"].items() if k != "text"},
            )

            results.append(result)

        # Create and return response
        return SearchResponse(
            results=results,
            query=query.query,
            landmark_id=query.landmark_id,
            count=len(results),
        )
    except Exception as e:
        logger.error(f"Error searching text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/landmarks", response_model=LandmarkListResponse)  # type: ignore[misc]
async def get_landmarks(
    limit: int = QueryParam(
        20, description="Maximum number of landmarks to return", ge=1, le=100
    ),
    db_client: DbClient = Depends(get_db_client),
) -> LandmarkListResponse:
    """Get a list of landmarks.

    Args:
        limit: Maximum number of landmarks to return
        db_client: DbClient instance

    Returns:
        LandmarkListResponse with list of landmarks
    """
    try:
        # Get landmarks from database
        landmarks_data = db_client.get_all_landmarks(limit)

        # Convert to LandmarkInfo objects
        landmarks = []
        for landmark_data in landmarks_data:
            if isinstance(landmark_data, dict):
                landmark = LandmarkInfo(
                    id=landmark_data.get("id", ""),
                    name=landmark_data.get("name", ""),
                    location=landmark_data.get("location"),
                    borough=landmark_data.get("borough"),
                    type=landmark_data.get("type"),
                    designation_date=str(landmark_data.get("designation_date", "")),
                    description=landmark_data.get("description"),
                )
            else:
                # Handle Pydantic model
                landmark = LandmarkInfo(
                    id=getattr(landmark_data, "lpNumber", ""),
                    name=getattr(landmark_data, "name", ""),
                    location=getattr(landmark_data, "street", None),
                    borough=getattr(landmark_data, "borough", None),
                    type=getattr(landmark_data, "objectType", None),
                    designation_date=str(getattr(landmark_data, "dateDesignated", "")),
                    description=None,  # Description might not be directly available
                )
            landmarks.append(landmark)

        # Create and return response
        return LandmarkListResponse(
            landmarks=landmarks,
            count=len(landmarks),
        )
    except Exception as e:
        logger.error(f"Error getting landmarks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/landmark/{landmark_id}", response_model=LandmarkInfo)  # type: ignore[misc]
async def get_landmark(
    landmark_id: str,
    db_client: DbClient = Depends(get_db_client),
) -> LandmarkInfo:
    """Get information about a specific landmark.

    Args:
        landmark_id: ID of the landmark
        db_client: DbClient instance

    Returns:
        LandmarkInfo with landmark information
    """
    try:
        # Get landmark from database
        landmark_data = db_client.get_landmark_by_id(landmark_id)

        if not landmark_data:
            raise HTTPException(
                status_code=404, detail=f"Landmark not found: {landmark_id}"
            )

        # Convert to LandmarkInfo
        if isinstance(landmark_data, dict):
            landmark = LandmarkInfo(
                id=landmark_data.get("id", ""),
                name=landmark_data.get("name", ""),
                location=landmark_data.get("location"),
                borough=landmark_data.get("borough"),
                type=landmark_data.get("type"),
                designation_date=str(landmark_data.get("designation_date", "")),
                description=landmark_data.get("description"),
            )
        else:
            # Handle Pydantic model
            landmark = LandmarkInfo(
                id=getattr(landmark_data, "lpNumber", ""),
                name=getattr(landmark_data, "name", ""),
                location=getattr(landmark_data, "street", None),
                borough=getattr(landmark_data, "borough", None),
                type=getattr(landmark_data, "objectType", None),
                designation_date=str(getattr(landmark_data, "dateDesignated", "")),
                description=None,  # Description might not be directly available
            )

        return landmark
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting landmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/text", response_model=LandmarkListResponse)  # type: ignore[misc]
async def search_landmarks_text(
    q: str = QueryParam(..., description="Search query"),
    limit: int = QueryParam(
        20, description="Maximum number of landmarks to return", ge=1, le=100
    ),
    db_client: DbClient = Depends(get_db_client),
) -> LandmarkListResponse:
    """Search for landmarks by text (direct database search, not vector search).

    Args:
        q: Search query
        limit: Maximum number of landmarks to return
        db_client: Database client instance

    Returns:
        LandmarkListResponse with matching landmarks
    """
    try:
        # Search landmarks in database
        landmarks_data = db_client.search_landmarks(q)

        # Limit results
        landmarks_data = landmarks_data[:limit]

        # Convert to LandmarkInfo objects
        landmarks = []
        for landmark_data in landmarks_data:
            if isinstance(landmark_data, dict):
                landmark = LandmarkInfo(
                    id=landmark_data.get("id", ""),
                    name=landmark_data.get("name", ""),
                    location=landmark_data.get("location"),
                    borough=landmark_data.get("borough"),
                    type=landmark_data.get("type"),
                    designation_date=str(landmark_data.get("designation_date", "")),
                    description=landmark_data.get("description"),
                )
            else:
                # Handle Pydantic model
                landmark = LandmarkInfo(
                    id=getattr(landmark_data, "lpNumber", ""),
                    name=getattr(landmark_data, "name", ""),
                    location=getattr(landmark_data, "street", None),
                    borough=getattr(landmark_data, "borough", None),
                    type=getattr(landmark_data, "objectType", None),
                    designation_date=str(getattr(landmark_data, "dateDesignated", "")),
                    description=None,  # Description might not be directly available
                )
            landmarks.append(landmark)

        # Create and return response
        return LandmarkListResponse(
            landmarks=landmarks,
            count=len(landmarks),
        )
    except Exception as e:
        logger.error(f"Error searching landmarks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
