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
    source_type: Optional[str] = Field(
        None, description="Optional source type filter ('wikipedia' or 'pdf')"
    )
    top_k: int = Field(5, description="Number of results to return", ge=1, le=20)


class SearchResult(BaseModel):
    """Search result model."""

    text: str = Field(..., description="Text content of the search result")
    score: float = Field(..., description="Similarity score")
    landmark_id: str = Field(..., description="ID of the landmark")
    landmark_name: Optional[str] = Field(None, description="Name of the landmark")
    source_type: str = Field("pdf", description="Source type ('wikipedia' or 'pdf')")
    source: Optional[str] = Field(
        None, description="Source information (article title or document name)"
    )
    source_url: Optional[str] = Field(
        None, description="URL to the source if available"
    )
    metadata: Dict[str, Any] = Field({}, description="Additional metadata")


class SearchResponse(BaseModel):
    """Response model for text search."""

    results: List[SearchResult] = Field([], description="Search results")
    query: str = Field(..., description="Original query")
    landmark_id: Optional[str] = Field(
        None, description="Landmark ID filter that was applied"
    )
    source_type: Optional[str] = Field(
        None, description="Source type filter that was applied"
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

        # Prepare filter
        filter_dict = {}
        if query.landmark_id:
            filter_dict["landmark_id"] = query.landmark_id

        # Add source_type filter if provided
        if query.source_type and query.source_type in ["wikipedia", "pdf"]:
            filter_dict["source_type"] = query.source_type

        # Query the vector database (only pass filter_dict if it has values)
        filter_to_use = filter_dict if filter_dict else None
        matches = vector_db.query_vectors(query_embedding, query.top_k, filter_to_use)

        # Process results
        results = []
        for match in matches:
            # Extract data from match
            metadata = match["metadata"]
            text = metadata.get("text", "")
            landmark_id = metadata.get("landmark_id", "")
            score = match["score"]
            source_type = metadata.get(
                "source_type", "pdf"
            )  # Default to pdf if not specified

            # Get landmark name from database if available
            landmark_name = None
            landmark = db_client.get_landmark_by_id(landmark_id)
            if landmark:
                # Handle both dict and Pydantic model objects
                if isinstance(landmark, dict):
                    landmark_name = landmark.get("name")
                else:
                    landmark_name = getattr(landmark, "name", None)

            # Set source information based on source_type
            source = None
            source_url = None
            if source_type == "wikipedia":
                source = (
                    f"Wikipedia: {metadata.get('article_title', 'Unknown Article')}"
                )
                source_url = metadata.get("article_url", "")
            else:
                source = f"LPC Report: {metadata.get('document_name', metadata.get('file_name', 'Unknown Document'))}"
                source_url = metadata.get("document_url", "")

            # Create SearchResult
            result = SearchResult(
                text=text,
                score=score,
                landmark_id=landmark_id,
                landmark_name=landmark_name,
                source_type=source_type,
                source=source,
                source_url=source_url,
                metadata={k: v for k, v in metadata.items() if k != "text"},
            )

            results.append(result)

        # Create and return response
        return SearchResponse(
            results=results,
            query=query.query,
            landmark_id=query.landmark_id,
            source_type=query.source_type,
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


# --- Non-API functions for combined search ---


def search_combined_sources(
    query_text: str,
    landmark_id: Optional[str] = None,
    source_type: Optional[str] = None,
    top_k: int = 5,
    embedding_generator: Optional[EmbeddingGenerator] = None,
    vector_db: Optional[PineconeDB] = None,
    db_client: Optional[DbClient] = None,
) -> List[Dict[str, Any]]:
    """
    Search for information about landmarks using vector similarity across both Wikipedia and PDF sources.

    This is a non-API function that can be used by scripts and other modules.

    Args:
        query_text: The search query text
        landmark_id: Optional landmark ID to filter results
        source_type: Optional source type filter ('wikipedia' or 'pdf')
        top_k: Maximum number of results to return
        embedding_generator: Optional EmbeddingGenerator instance
        vector_db: Optional PineconeDB instance
        db_client: Optional DbClient instance

    Returns:
        List of search results with metadata and source attribution
    """
    # Initialize components if not provided
    if embedding_generator is None:
        embedding_generator = EmbeddingGenerator()
    if vector_db is None:
        vector_db = PineconeDB()
    if db_client is None:
        from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI

        db_client = DbClient(CoreDataStoreAPI())

    # Generate embedding for query
    embedding = embedding_generator.generate_embedding(query_text)

    # Build filter dictionary
    filter_dict: Dict[str, Any] = {}
    if landmark_id:
        filter_dict["landmark_id"] = landmark_id
    if source_type and source_type in ["wikipedia", "pdf"]:
        filter_dict["source_type"] = source_type

    # Query the vector database (only pass filter_dict if it has values)
    filter_to_use = filter_dict if filter_dict else None
    matches = vector_db.query_vectors(
        query_vector=embedding, top_k=top_k, filter_dict=filter_to_use
    )

    # Enhance results with source attribution
    enhanced_results: List[Dict[str, Any]] = []

    for match in matches:
        metadata = match["metadata"]
        source_type_value = metadata.get("source_type", "pdf")

        enhanced_result = {
            "id": match.get("id", ""),
            "score": match.get("score", 0.0),
            "text": metadata.get("text", ""),
            "landmark_id": metadata.get("landmark_id", ""),
            "source_type": source_type_value,
        }

        # Get landmark name from database if available
        landmark_id_value = metadata.get("landmark_id", "")
        if landmark_id_value:
            landmark = db_client.get_landmark_by_id(landmark_id_value)
            if landmark:
                # Handle both dict and Pydantic model objects
                if isinstance(landmark, dict):
                    enhanced_result["landmark_name"] = landmark.get("name")
                else:
                    enhanced_result["landmark_name"] = getattr(landmark, "name", None)

        # Add source-specific information
        if source_type_value == "wikipedia":
            enhanced_result["source"] = (
                f"Wikipedia: {metadata.get('article_title', 'Unknown Article')}"
            )
            enhanced_result["source_url"] = metadata.get("article_url", "")
        else:
            enhanced_result["source"] = (
                f"LPC Report: {metadata.get('document_name', metadata.get('file_name', 'Unknown Document'))}"
            )
            enhanced_result["source_url"] = metadata.get("document_url", "")

        enhanced_results.append(enhanced_result)

    return enhanced_results


def compare_source_results(
    query_text: str, landmark_id: Optional[str] = None, top_k: int = 3
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Compare search results from different sources for the same query.

    Args:
        query_text: The search query text
        landmark_id: Optional landmark ID to filter results
        top_k: Maximum number of results to return per source

    Returns:
        Dictionary with results from each source type and combined results
    """
    # Get results from Wikipedia sources
    wiki_results = search_combined_sources(
        query_text=query_text,
        landmark_id=landmark_id,
        source_type="wikipedia",
        top_k=top_k,
    )

    # Get results from PDF sources
    pdf_results = search_combined_sources(
        query_text=query_text,
        landmark_id=landmark_id,
        source_type="pdf",
        top_k=top_k,
    )

    # Get combined results (no source filter)
    combined_results = search_combined_sources(
        query_text=query_text,
        landmark_id=landmark_id,
        source_type=None,
        top_k=top_k * 2,
    )

    return {
        "wikipedia_results": wiki_results,
        "pdf_results": pdf_results,
        "combined_results": combined_results,
    }


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
        landmarks: List[LandmarkInfo] = []
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
