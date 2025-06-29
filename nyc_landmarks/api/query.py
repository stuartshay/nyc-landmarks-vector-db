"""
Query API module for NYC Landmarks Vector Database.

This module provides API endpoints for vector search and querying
landmark information.
"""

from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi import Query as QueryParam
from fastapi import Request
from fastapi.openapi.models import Example
from pydantic import BaseModel, Field

from nyc_landmarks.db.db_client import DbClient
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.examples.search_examples import (
    get_landmark_filter_examples,
    get_text_query_examples,
)
from nyc_landmarks.utils.correlation import get_correlation_id
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.utils.validation import ValidationLogger, get_client_info
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)

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
    index_name: Optional[str] = Field(
        None, description="Pinecone index name where this result was found"
    )
    namespace: Optional[str] = Field(
        None, description="Pinecone namespace where this result was found"
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
    index_name: Optional[str] = Field(
        None, description="Pinecone index name used for this search"
    )
    namespace: Optional[str] = Field(
        None, description="Pinecone namespace used for this search"
    )


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


# --- Helper functions for examples ---


def _convert_to_fastapi_examples(
    examples_dict: Dict[str, Dict[str, Any]],
) -> Dict[str, Example]:
    """Convert structured examples to FastAPI examples format for Swagger UI dropdown."""
    fastapi_examples = {}
    for key, example_data in examples_dict.items():
        fastapi_examples[key] = Example(
            summary=example_data["summary"],
            description=example_data["description"],
            value=example_data["value"],
        )
    return fastapi_examples


# --- Dependency injection functions ---


def get_embedding_generator() -> EmbeddingGenerator:
    """Get an instance of EmbeddingGenerator."""
    return EmbeddingGenerator()


def get_vector_db() -> PineconeDB:
    """Get an instance of PineconeDB."""
    return PineconeDB()


def get_db_client() -> DbClient:
    """Get an instance of DbClient."""
    from nyc_landmarks.db.db_client import get_db_client

    return get_db_client()


# --- API endpoints ---


@router.post(
    "/search",
    response_model=SearchResponse,
)  # type: ignore[misc]
async def search_text(
    request: Request,
    query: TextQuery = Body(
        ..., openapi_examples=_convert_to_fastapi_examples(get_text_query_examples())
    ),
    embedding_generator: EmbeddingGenerator = Depends(get_embedding_generator),
    vector_db: PineconeDB = Depends(get_vector_db),
    db_client: DbClient = Depends(get_db_client),
) -> SearchResponse:
    """Search for text using vector similarity.

    Args:
        query: Text query model
        request: FastAPI request object for logging
        embedding_generator: EmbeddingGenerator instance
        vector_db: PineconeDB instance
        db_client: DbClient instance

    Returns:
        SearchResponse with results
    """
    try:
        # Get client information for logging
        client_ip, user_agent = get_client_info(request)
        endpoint = "/api/query/search"

        # Validate all input parameters
        ValidationLogger.validate_text_query(
            query.query, endpoint, client_ip, user_agent
        )
        ValidationLogger.validate_landmark_id(
            query.landmark_id, endpoint, client_ip, user_agent
        )
        ValidationLogger.validate_top_k(query.top_k, endpoint, client_ip, user_agent)
        ValidationLogger.validate_source_type(
            query.source_type, endpoint, client_ip, user_agent
        )

        # Log successful validation
        ValidationLogger.log_validation_success(
            endpoint,
            {
                "query": query.query,
                "landmark_id": query.landmark_id,
                "source_type": query.source_type,
                "top_k": query.top_k,
            },
            client_ip,
            user_agent,
        )

        logger.info(
            "search_text request: query=%s landmark_id=%s source_type=%s top_k=%s",
            query.query,
            query.landmark_id,
            query.source_type,
            query.top_k,
        )

        # Get correlation ID for embedding generation tracking
        correlation_id = get_correlation_id(request)

        # Generate embedding for the query with correlation tracking
        logger.info(
            "Generating embedding for query",
            extra={
                "correlation_id": correlation_id,
                "query_text": (
                    query.query[:100] + "..." if len(query.query) > 100 else query.query
                ),
                "query_length": len(query.query),
                "landmark_id": query.landmark_id,
                "source_type": query.source_type,
                "operation": "embedding_generation",
                "endpoint": "/api/query/search",
            },
        )
        query_embedding = embedding_generator.generate_embedding(query.query)
        logger.info(
            "Embedding generation completed",
            extra={
                "correlation_id": correlation_id,
                "embedding_dimensions": len(query_embedding) if query_embedding else 0,
                "operation": "embedding_generation_complete",
                "endpoint": "/api/query/search",
            },
        )

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

        # Get index information from vector_db
        index_name = getattr(vector_db, "index_name", None)
        namespace = getattr(vector_db, "namespace", None)

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
                index_name=index_name,
                namespace=namespace,
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
            index_name=index_name,
            namespace=namespace,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/search/landmark",
    response_model=SearchResponse,
)  # type: ignore[misc]
async def search_text_by_landmark(
    request: Request,
    query: TextQuery = Body(
        ...,
        openapi_examples=_convert_to_fastapi_examples(get_landmark_filter_examples()),
    ),
    embedding_generator: EmbeddingGenerator = Depends(get_embedding_generator),
    vector_db: PineconeDB = Depends(get_vector_db),
    db_client: DbClient = Depends(get_db_client),
) -> SearchResponse:
    """Search within a specific landmark's documents by vector similarity.

    Requires a landmark_id for filtering results to a single landmark.
    """
    # Ensure landmark_id is provided
    if not query.landmark_id:
        # Get client information for logging
        client_ip, user_agent = get_client_info(request)
        logger.warning(
            "Invalid API request: landmark_id required but not provided",
            extra={
                "validation_error": "missing_landmark_id",
                "endpoint": "/api/query/search_by_landmark",
                "client_ip": client_ip,
                "user_agent": user_agent,
            },
        )
        raise HTTPException(
            status_code=400, detail="landmark_id is required for this endpoint"
        )

    # Use the existing search_text functionality with enhanced correlation tracking
    result: SearchResponse = await search_text(
        request, query, embedding_generator, vector_db, db_client
    )
    return result


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
    except HTTPException:
        raise
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


def _initialize_components(
    embedding_generator: Optional[EmbeddingGenerator] = None,
    vector_db: Optional[PineconeDB] = None,
    db_client: Optional[DbClient] = None,
) -> Tuple[EmbeddingGenerator, PineconeDB, DbClient]:
    """
    Initialize required components for search if not provided.

    Args:
        embedding_generator: Optional EmbeddingGenerator instance
        vector_db: Optional PineconeDB instance
        db_client: Optional DbClient instance

    Returns:
        Tuple of (EmbeddingGenerator, PineconeDB, DbClient)
    """
    if embedding_generator is None:
        embedding_generator = EmbeddingGenerator()
    if vector_db is None:
        vector_db = PineconeDB()
    if db_client is None:
        from nyc_landmarks.db.db_client import get_db_client

        db_client = get_db_client()
    return embedding_generator, vector_db, db_client


def _build_search_filter(
    landmark_id: Optional[str] = None, source_type: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Build filter dictionary for vector search.

    Args:
        landmark_id: Optional landmark ID to filter results
        source_type: Optional source type filter ('wikipedia' or 'pdf')

    Returns:
        Dictionary with filter parameters or None if no filters
    """
    filter_dict: Dict[str, Any] = {}
    if landmark_id:
        filter_dict["landmark_id"] = landmark_id
    if source_type and source_type in ["wikipedia", "pdf"]:
        filter_dict["source_type"] = source_type
    return filter_dict if filter_dict else None


def _get_landmark_name(landmark_id: str, db_client: DbClient) -> Optional[str]:
    """
    Get landmark name from database by ID.

    Args:
        landmark_id: The landmark ID
        db_client: Database client

    Returns:
        Landmark name or None if not found
    """
    landmark = db_client.get_landmark_by_id(landmark_id)
    if not landmark:
        return None

    # Handle both dict and Pydantic model objects
    if isinstance(landmark, dict):
        name = landmark.get("name")
        if isinstance(name, str) or name is None:
            return name
        return str(name)
    else:
        name = getattr(landmark, "name", None)
        if isinstance(name, str) or name is None:
            return name
        return str(name)


def _get_source_info(metadata: Dict[str, Any]) -> Tuple[str, str]:
    """
    Generate source attribution information based on metadata.

    Args:
        metadata: Vector metadata dictionary

    Returns:
        Tuple of (source_description, source_url)
    """
    source_type = metadata.get("source_type", "pdf")

    if source_type == "wikipedia":
        source = f"Wikipedia: {metadata.get('article_title', 'Unknown Article')}"
        source_url = metadata.get("article_url", "")
    else:
        source = f"LPC Report: {metadata.get('document_name', metadata.get('file_name', 'Unknown Document'))}"
        source_url = metadata.get("document_url", "")

    return source, source_url


def _enhance_search_result(
    match: Dict[str, Any], db_client: DbClient
) -> Dict[str, Any]:
    """
    Enhance a search result with additional information.

    Args:
        match: Raw search result from vector database
        db_client: Database client

    Returns:
        Enhanced search result
    """
    metadata = match["metadata"]
    source_type_value = metadata.get("source_type", "pdf")

    # Create basic result
    enhanced_result = {
        "id": match.get("id", ""),
        "score": match.get("score", 0.0),
        "text": metadata.get("text", ""),
        "landmark_id": metadata.get("landmark_id", ""),
        "source_type": source_type_value,
    }

    # Add landmark name if available
    landmark_id_value = metadata.get("landmark_id", "")
    if landmark_id_value:
        landmark_name = _get_landmark_name(landmark_id_value, db_client)
        if landmark_name:
            enhanced_result["landmark_name"] = landmark_name

    # Add source information
    source, source_url = _get_source_info(metadata)
    enhanced_result["source"] = source
    enhanced_result["source_url"] = source_url

    return enhanced_result


def _generate_query_embedding(
    query_text: str,
    embedding_generator: EmbeddingGenerator,
    correlation_id: Optional[str] = None,
) -> (
    Any
):  # Using Any since the actual return type from embedding_generator is not strictly typed
    """
    Generate embedding vector for a text query.

    Args:
        query_text: The search query text
        embedding_generator: EmbeddingGenerator instance
        correlation_id: Optional correlation ID for logging correlation

    Returns:
        Embedding vector values
    """
    if correlation_id:
        logger.info(
            "Generating embedding for non-API query",
            extra={
                "correlation_id": correlation_id,
                "query_text": (
                    query_text[:100] + "..." if len(query_text) > 100 else query_text
                ),
                "query_length": len(query_text),
                "operation": "embedding_generation",
                "context": "non_api_search",
            },
        )

    embedding = embedding_generator.generate_embedding(query_text)

    if correlation_id:
        logger.info(
            "Embedding generation completed for non-API query",
            extra={
                "correlation_id": correlation_id,
                "embedding_dimensions": len(embedding) if embedding else 0,
                "operation": "embedding_generation_complete",
                "context": "non_api_search",
            },
        )

    return embedding


def _perform_vector_search(
    embedding: List[float],
    top_k: int,
    filter_dict: Optional[Dict[str, Any]],
    vector_db: PineconeDB,
) -> List[Dict[str, Any]]:
    """
    Perform vector search in the database.

    Args:
        embedding: Query embedding vector
        top_k: Maximum number of results to return
        filter_dict: Optional filter dictionary
        vector_db: PineconeDB instance

    Returns:
        List of raw vector search results
    """
    return vector_db.query_vectors(
        query_vector=embedding, top_k=top_k, filter_dict=filter_dict
    )


def _process_search_results(
    matches: List[Dict[str, Any]], db_client: DbClient
) -> List[Dict[str, Any]]:
    """
    Process raw search results into enhanced results with additional information.

    Args:
        matches: Raw search results from vector database
        db_client: Database client

    Returns:
        List of enhanced search results
    """
    return [_enhance_search_result(match, db_client) for match in matches]


def search_combined_sources(
    query_text: str,
    landmark_id: Optional[str] = None,
    source_type: Optional[str] = None,
    top_k: int = 5,
    correlation_id: Optional[str] = None,
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
        correlation_id: Optional correlation ID for logging correlation
        embedding_generator: Optional EmbeddingGenerator instance
        vector_db: Optional PineconeDB instance
        db_client: Optional DbClient instance

    Returns:
        List of search results with metadata and source attribution
    """
    # Initialize components if not provided
    embedding_generator, vector_db, db_client = _initialize_components(
        embedding_generator, vector_db, db_client
    )

    # Generate embedding for query with correlation tracking
    embedding = _generate_query_embedding(
        query_text, embedding_generator, correlation_id
    )

    # Build filter dictionary and query the vector database
    filter_dict = _build_search_filter(landmark_id, source_type)
    matches = _perform_vector_search(embedding, top_k, filter_dict, vector_db)

    # Enhance results with source attribution and additional information
    enhanced_results = _process_search_results(matches, db_client)

    return enhanced_results


def compare_source_results(
    query_text: str,
    landmark_id: Optional[str] = None,
    top_k: int = 3,
    correlation_id: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Compare search results from different sources for the same query.

    Args:
        query_text: The search query text
        landmark_id: Optional landmark ID to filter results
        top_k: Maximum number of results to return per source
        correlation_id: Optional correlation ID for logging correlation

    Returns:
        Dictionary with results from each source type and combined results
    """
    # Get results from Wikipedia sources
    wiki_results = search_combined_sources(
        query_text=query_text,
        landmark_id=landmark_id,
        source_type="wikipedia",
        top_k=top_k,
        correlation_id=correlation_id,
    )

    # Get results from PDF sources
    pdf_results = search_combined_sources(
        query_text=query_text,
        landmark_id=landmark_id,
        source_type="pdf",
        top_k=top_k,
        correlation_id=correlation_id,
    )

    # Get combined results (no source filter)
    combined_results = search_combined_sources(
        query_text=query_text,
        landmark_id=landmark_id,
        source_type=None,
        top_k=top_k * 2,
        correlation_id=correlation_id,
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
        lpc_report_response = db_client.search_landmarks(q)
        # Use the .results attribute and limit the results
        results = lpc_report_response.results[:limit]  # type: ignore[attr-defined]

        # Convert to LandmarkInfo objects
        landmarks: List[LandmarkInfo] = []
        for landmark_data in results:
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching landmarks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
