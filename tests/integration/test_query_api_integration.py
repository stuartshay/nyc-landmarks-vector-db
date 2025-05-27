"""
Integration tests for the Query API endpoints.

These tests verify the complete pipeline from API request through
vector search to response formatting.
"""

import json
import logging
from typing import Dict

import pytest
from fastapi.testclient import TestClient

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.main import app
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

logger = logging.getLogger(__name__)

# Create test client
client = TestClient(app)


@pytest.mark.integration
def test_query_api_basic_functionality() -> None:
    """
    Test the basic functionality of the query API endpoint.

    This test verifies:
    1. The API endpoint responds without errors
    2. Response structure is correct
    3. Basic pipeline components are working
    """
    logger.info("Testing basic query API functionality")

    # Test with a simple query
    payload = {"query": "historic building", "top_k": 3}

    response = client.post("/api/query/search", json=payload)

    # Check response status
    assert (
        response.status_code == 200
    ), f"Expected 200 but got {response.status_code}: {response.text}"

    # Parse response
    data = response.json()

    # Validate response structure
    assert "results" in data, "Response missing 'results' field"
    assert "query" in data, "Response missing 'query' field"
    assert "count" in data, "Response missing 'count' field"

    # Check that query was echoed back correctly
    assert (
        data["query"] == "historic building"
    ), f"Query not echoed correctly: {data['query']}"

    # Check count matches results length
    assert data["count"] == len(data["results"]), "Count doesn't match results length"

    logger.info(f"API responded with {data['count']} results")

    # If we have results, validate their structure
    if data["results"]:
        result = data["results"][0]
        required_fields = ["text", "score", "landmark_id", "source_type"]
        for field in required_fields:
            assert field in result, f"Result missing required field: {field}"

        # Check score is a valid float between 0 and 1
        assert isinstance(result["score"], (int, float)), "Score should be numeric"
        assert (
            0 <= result["score"] <= 1
        ), f"Score should be between 0 and 1, got {result['score']}"

        logger.info(
            f"First result: landmark_id={result['landmark_id']}, score={result['score']}"
        )


@pytest.mark.integration
def test_query_api_empire_state_building() -> None:
    """
    Test the specific query mentioned in the user's curl request.

    This test attempts to reproduce the exact scenario that's failing.
    """
    logger.info("Testing Empire State Building query")

    # Exact payload from user's curl request
    payload = {
        "query": "What is the history of the Empire State Building?",
        "source_type": "pdf",
        "top_k": 5,
    }

    response = client.post("/api/query/search", json=payload)

    # Check response status
    assert (
        response.status_code == 200
    ), f"Expected 200 but got {response.status_code}: {response.text}"

    # Parse response
    data = response.json()

    logger.info(f"Empire State Building query returned {data['count']} results")

    # Log the response for debugging
    logger.info(f"Full response: {json.dumps(data, indent=2)}")

    # Validate response structure even if no results
    assert "results" in data
    assert "query" in data
    assert "count" in data
    assert "source_type" in data

    # Check filters were applied correctly
    assert data["source_type"] == "pdf", "PDF source type filter not applied"

    # If we got results, examine them
    if data["results"]:
        for result in data["results"]:
            assert result["source_type"] == "pdf", "Result should be from PDF source"
            logger.info(
                f"Found result: {result['landmark_id']} - {result.get('landmark_name', 'Unknown')}"
            )
    else:
        logger.warning(
            "No results returned for Empire State Building query - this indicates the issue"
        )


@pytest.mark.integration
def test_embedding_generation_component() -> None:
    """Test the embedding generation component in isolation."""
    logger.info("Testing embedding generation component...")
    embedding_generator = EmbeddingGenerator()

    try:
        embedding = embedding_generator.generate_embedding("test query")
        assert embedding is not None, "Embedding generation returned None"
        assert (
            len(embedding) == settings.PINECONE_DIMENSIONS
        ), f"Embedding has wrong dimensions: {len(embedding)}"
        logger.info(f"✓ Embedding generation works, dimensions: {len(embedding)}")
    except Exception as e:
        logger.error(f"✗ Embedding generation failed: {e}")
        pytest.fail(f"Embedding generation failed: {e}")


@pytest.mark.integration
def test_vector_database_component() -> None:
    """Test the vector database connection and basic operations."""
    logger.info("Testing vector database connection...")
    vector_db = PineconeDB()

    try:
        # Try to get index stats
        stats = vector_db.get_index_stats()
        logger.info(f"✓ Vector DB connection works, stats: {stats}")

        # Check if there are any vectors in the database
        total_vectors = stats.get("total_vector_count", 0)
        if total_vectors == 0:
            logger.warning("⚠ Vector database appears to be empty!")
        else:
            logger.info(f"✓ Vector database contains {total_vectors} vectors")

    except Exception as e:
        logger.error(f"✗ Vector database connection failed: {e}")
        pytest.fail(f"Vector database connection failed: {e}")


@pytest.mark.integration
def test_database_client_component() -> None:
    """Test the database client functionality."""
    logger.info("Testing database client...")
    db_client = get_db_client()

    try:
        # Try to get some landmarks
        landmarks = db_client.get_all_landmarks(limit=5)
        assert landmarks is not None, "Database client returned None"
        logger.info(f"✓ Database client works, found {len(landmarks)} landmarks")

        # Log some landmark IDs for reference
        for i, landmark in enumerate(landmarks[:3]):
            if isinstance(landmark, dict):
                landmark_id = landmark.get("id", "unknown")
                landmark_name = landmark.get("name", "unknown")
            else:
                landmark_id = getattr(landmark, "lpNumber", "unknown")
                landmark_name = getattr(landmark, "name", "unknown")
            logger.info(f"  Sample landmark {i + 1}: {landmark_id} - {landmark_name}")

    except Exception as e:
        logger.error(f"✗ Database client failed: {e}")
        pytest.fail(f"Database client failed: {e}")


@pytest.mark.integration
def test_vector_search_component() -> None:
    """Test the vector search functionality with simple queries."""
    logger.info("Testing vector search...")
    embedding_generator = EmbeddingGenerator()
    vector_db = PineconeDB()

    try:
        simple_embedding = embedding_generator.generate_embedding("building")
        results = vector_db.query_vectors(simple_embedding, top_k=3)

        logger.info(f"✓ Vector search works, found {len(results)} results")

        if results:
            for i, result in enumerate(results[:2]):
                metadata = result.get("metadata", {})
                landmark_id = metadata.get("landmark_id", "unknown")
                source_type = metadata.get("source_type", "unknown")
                score = result.get("score", 0)
                logger.info(
                    f"  Sample result {i + 1}: {landmark_id} ({source_type}) - score: {score:.3f}"
                )
        else:
            logger.warning("⚠ Vector search returned no results!")

    except Exception as e:
        logger.error(f"✗ Vector search failed: {e}")
        pytest.fail(f"Vector search failed: {e}")


@pytest.mark.integration
def test_query_api_with_filters() -> None:
    """
    Test the query API with various filter combinations.
    """
    logger.info("Testing query API with filters")

    # Get a sample landmark ID from the database
    db_client = get_db_client()
    landmarks = db_client.get_all_landmarks(limit=5)

    if not landmarks:
        pytest.skip("No landmarks available for testing")

    # Extract landmark ID
    sample_landmark = landmarks[0]
    if isinstance(sample_landmark, dict):
        landmark_id = sample_landmark.get("id")
    else:
        landmark_id = getattr(sample_landmark, "lpNumber", None)

    if not landmark_id:
        pytest.skip("Could not extract landmark ID for testing")

    logger.info(f"Testing with landmark ID: {landmark_id}")

    # Test 1: Filter by landmark_id
    payload = {"query": "historic building", "landmark_id": landmark_id, "top_k": 3}

    response = client.post("/api/query/search", json=payload)
    assert response.status_code == 200

    data = response.json()
    logger.info(f"Landmark filter test returned {data['count']} results")

    # If we got results, they should all be for the specified landmark
    for result in data["results"]:
        assert (
            result["landmark_id"] == landmark_id
        ), f"Result landmark_id {result['landmark_id']} doesn't match filter {landmark_id}"

    # Test 2: Filter by source_type
    for source_type in ["pdf", "wikipedia"]:
        payload = {"query": "historic building", "source_type": source_type, "top_k": 3}

        response = client.post("/api/query/search", json=payload)
        assert response.status_code == 200

        data = response.json()
        logger.info(
            f"Source type '{source_type}' filter returned {data['count']} results"
        )

        # All results should match the source type filter
        for result in data["results"]:
            assert (
                result["source_type"] == source_type
            ), f"Result source_type {result['source_type']} doesn't match filter {source_type}"


@pytest.mark.integration
def test_query_api_error_handling() -> None:
    """
    Test error handling in the query API.
    """
    logger.info("Testing query API error handling")

    # Test 1: Invalid JSON
    response = client.post(
        "/api/query/search",
        content="invalid json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422, "Should return 422 for invalid JSON"

    # Test 2: Missing required field
    response = client.post("/api/query/search", json={})
    assert response.status_code == 422, "Should return 422 for missing query field"

    # Test 3: Invalid top_k values
    invalid_top_k_values = [0, -1, 25]  # 0, negative, and above max

    for top_k in invalid_top_k_values:
        payload = {"query": "test", "top_k": top_k}
        response = client.post("/api/query/search", json=payload)
        assert (
            response.status_code == 422
        ), f"Should return 422 for invalid top_k: {top_k}"

    # Test 4: Invalid source_type
    payload = {"query": "test", "source_type": "invalid_source"}

    response = client.post("/api/query/search", json=payload)

    # This should still return 200 but ignore the invalid filter
    assert response.status_code == 200
    data = response.json()
    # The invalid source_type should be ignored (not applied as filter)
    assert data["source_type"] == "invalid_source"  # Echoed back but not used as filter


@pytest.mark.integration
def test_query_api_landmark_specific_endpoint() -> None:
    """
    Test the landmark-specific query endpoint.
    """
    logger.info("Testing landmark-specific query endpoint")

    # Get a sample landmark ID
    db_client = get_db_client()
    landmarks = db_client.get_all_landmarks(limit=1)

    if not landmarks:
        pytest.skip("No landmarks available for testing")

    sample_landmark = landmarks[0]
    if isinstance(sample_landmark, dict):
        landmark_id = sample_landmark.get("id")
    else:
        landmark_id = getattr(sample_landmark, "lpNumber", None)

    if not landmark_id:
        pytest.skip("Could not extract landmark ID for testing")

    # Test with landmark_id required
    payload = {"query": "historic architecture", "landmark_id": landmark_id, "top_k": 3}

    response = client.post("/api/query/search/landmark", json=payload)
    assert response.status_code == 200

    data = response.json()
    logger.info(f"Landmark-specific endpoint returned {data['count']} results")

    # Test without landmark_id (should fail)
    payload = {"query": "historic architecture", "top_k": 3}

    response = client.post("/api/query/search/landmark", json=payload)
    assert (
        response.status_code == 400
    ), "Should require landmark_id for landmark-specific endpoint"


@pytest.mark.integration
def test_query_api_diagnostics() -> None:
    """
    Run diagnostic tests to help debug the no-results issue.
    """
    logger.info("Running query API diagnostics")

    # Check what's actually in our vector database
    vector_db = PineconeDB()
    embedding_generator = EmbeddingGenerator()

    # Get some basic stats
    stats = vector_db.get_index_stats()
    logger.info(f"Vector database stats: {stats}")

    # Try a very broad query to see if we get anything
    broad_embedding = embedding_generator.generate_embedding("building")
    broad_results = vector_db.query_vectors(broad_embedding, top_k=10)

    logger.info(f"Broad 'building' query returned {len(broad_results)} results")

    if broad_results:
        # Analyze the results we got
        source_types: Dict[str, int] = {}
        landmark_ids = set()

        for result in broad_results:
            metadata = result.get("metadata", {})
            source_type = metadata.get("source_type", "unknown")
            landmark_id = metadata.get("landmark_id", "unknown")

            source_types[source_type] = source_types.get(source_type, 0) + 1
            landmark_ids.add(landmark_id)

        logger.info(f"Source type distribution: {source_types}")
        logger.info(f"Number of unique landmarks: {len(landmark_ids)}")
        logger.info(f"Sample landmark IDs: {list(landmark_ids)[:5]}")

        # Test specifically with Empire State Building keywords
        empire_queries = [
            "Empire State Building",
            "Empire State",
            "skyscraper",
            "Manhattan building",
            "art deco",
        ]

        for query_text in empire_queries:
            query_embedding = embedding_generator.generate_embedding(query_text)
            results = vector_db.query_vectors(query_embedding, top_k=5)
            logger.info(f"Query '{query_text}' returned {len(results)} results")

            # Check if any results contain Empire State Building
            for result in results:
                metadata = result.get("metadata", {})
                text = metadata.get("text", "").lower()
                if "empire state" in text:
                    logger.info(
                        f"Found Empire State Building match in query '{query_text}'!"
                    )
                    break

    else:
        logger.warning(
            "No results found even for broad query - database may be empty or inaccessible"
        )

        # Try to check if it's a namespace issue
        try:
            # List some vectors to see if the namespace is correct
            vector_list = vector_db.list_vectors_with_filter(prefix="", limit=10)
            logger.info(f"Vector list returned: {len(vector_list)} vectors")
            if vector_list:
                logger.info(
                    f"Sample vector IDs: {[v.get('id', 'unknown') for v in vector_list[:3]]}"
                )
        except Exception as e:
            logger.error(f"Could not list vectors: {e}")


if __name__ == "__main__":
    # Allow running this test file directly for debugging
    pytest.main([__file__, "-v", "-s"])
