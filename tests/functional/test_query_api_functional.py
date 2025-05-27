"""
Functional tests for the Query API endpoints.

These tests verify the API logic using mocked components to isolate
the endpoint functionality from external dependencies.
"""

import logging
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from nyc_landmarks.main import app

logger = logging.getLogger(__name__)

# Create test client
client = TestClient(app)


@pytest.fixture
def mock_embedding_generator() -> Mock:
    """Mock EmbeddingGenerator for testing."""
    mock = Mock()
    # Return a 1536-dimension embedding vector (matching OpenAI's text-embedding-ada-002)
    mock.generate_embedding.return_value = [0.1] * 1536
    return mock


@pytest.fixture
def mock_vector_db() -> Mock:
    """Mock PineconeDB for testing."""
    mock = Mock()

    # Default empty response
    mock.query_vectors.return_value = []
    mock.get_index_stats.return_value = {"total_vector_count": 100}

    return mock


@pytest.fixture
def mock_db_client() -> Mock:
    """Mock DbClient for testing."""
    mock = Mock()

    # Default landmark data
    mock.get_landmark_by_id.return_value = {
        "id": "LP-00001",
        "name": "Test Landmark",
        "location": "Test Location",
        "borough": "Manhattan",
    }

    mock.get_all_landmarks.return_value = [
        {
            "id": "LP-00001",
            "name": "Test Landmark 1",
            "location": "Test Location 1",
            "borough": "Manhattan",
        },
        {
            "id": "LP-00002",
            "name": "Test Landmark 2",
            "location": "Test Location 2",
            "borough": "Brooklyn",
        },
    ]

    return mock


def create_mock_search_results(count: int = 2) -> List[Dict[str, Any]]:
    """Create mock search results for testing."""
    results = []
    for i in range(count):
        results.append(
            {
                "id": f"vector-{i}",
                "score": 0.9 - (i * 0.1),
                "metadata": {
                    "text": f"This is test text content for landmark {i}.",
                    "landmark_id": f"LP-{i + 1:05d}",
                    "source_type": "pdf",
                    "document_name": f"test_document_{i}.pdf",
                    "document_url": f"https://example.com/doc_{i}.pdf",
                },
            }
        )
    return results


@pytest.mark.functional
@patch("nyc_landmarks.api.query.get_db_client")
@patch("nyc_landmarks.api.query.PineconeDB")
@patch("nyc_landmarks.api.query.EmbeddingGenerator")
def test_query_api_successful_search(
    mock_embedding_cls: Any,
    mock_vector_db_cls: Any,
    mock_db_client_fn: Any,
    mock_embedding_generator: Any,
    mock_vector_db: Any,
    mock_db_client: Any,
) -> None:
    """Test successful search with mocked components."""
    # Setup mocks
    mock_embedding_cls.return_value = mock_embedding_generator
    mock_vector_db_cls.return_value = mock_vector_db
    mock_db_client_fn.return_value = mock_db_client

    # Mock vector search to return test results
    mock_search_results = create_mock_search_results(2)
    mock_vector_db.query_vectors.return_value = mock_search_results

    # Make API request
    payload = {"query": "test historic building", "top_k": 2}

    response = client.post("/api/query/search", json=payload)

    # Verify response
    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "results" in data
    assert "query" in data
    assert "count" in data
    assert data["query"] == "test historic building"
    assert data["count"] == 2

    # Check results structure
    assert len(data["results"]) == 2

    for i, result in enumerate(data["results"]):
        assert "text" in result
        assert "score" in result
        assert "landmark_id" in result
        assert "source_type" in result
        assert result["landmark_id"] == f"LP-{i + 1:05d}"
        assert result["source_type"] == "pdf"
        assert 0 <= result["score"] <= 1

    # Verify mocks were called correctly
    mock_embedding_generator.generate_embedding.assert_called_once_with(
        "test historic building"
    )
    mock_vector_db.query_vectors.assert_called_once()

    # Check the arguments passed to query_vectors
    call_args = mock_vector_db.query_vectors.call_args
    # Arguments are passed positionally, not as keywords
    assert call_args[0][1] == 2  # top_k
    assert call_args[0][2] is None  # filter_dict


@pytest.mark.functional
@patch("nyc_landmarks.api.query.get_db_client")
@patch("nyc_landmarks.api.query.PineconeDB")
@patch("nyc_landmarks.api.query.EmbeddingGenerator")
def test_query_api_with_landmark_filter(
    mock_embedding_cls: Any,
    mock_vector_db_cls: Any,
    mock_db_client_fn: Any,
    mock_embedding_generator: Any,
    mock_vector_db: Any,
    mock_db_client: Any,
) -> None:
    """Test search with landmark_id filter."""
    # Setup mocks
    mock_embedding_cls.return_value = mock_embedding_generator
    mock_vector_db_cls.return_value = mock_vector_db
    mock_db_client_fn.return_value = mock_db_client

    # Mock vector search to return filtered results
    mock_search_results = [
        {
            "id": "vector-1",
            "score": 0.95,
            "metadata": {
                "text": "Specific landmark text content.",
                "landmark_id": "LP-00123",
                "source_type": "pdf",
                "document_name": "specific_landmark.pdf",
            },
        }
    ]
    mock_vector_db.query_vectors.return_value = mock_search_results

    # Make API request with landmark filter
    payload = {"query": "test query", "landmark_id": "LP-00123", "top_k": 5}

    response = client.post("/api/query/search", json=payload)

    # Verify response
    assert response.status_code == 200
    data = response.json()

    assert data["landmark_id"] == "LP-00123"
    assert len(data["results"]) == 1
    assert data["results"][0]["landmark_id"] == "LP-00123"

    # Verify filter was passed to vector database
    call_args = mock_vector_db.query_vectors.call_args
    filter_dict = call_args[0][2]
    assert filter_dict is not None
    assert filter_dict["landmark_id"] == "LP-00123"


@pytest.mark.functional
@patch("nyc_landmarks.api.query.get_db_client")
@patch("nyc_landmarks.api.query.PineconeDB")
@patch("nyc_landmarks.api.query.EmbeddingGenerator")
def test_query_api_with_source_type_filter(
    mock_embedding_cls: Any,
    mock_vector_db_cls: Any,
    mock_db_client_fn: Any,
    mock_embedding_generator: Any,
    mock_vector_db: Any,
    mock_db_client: Any,
) -> None:
    """Test search with source_type filter."""
    # Setup mocks
    mock_embedding_cls.return_value = mock_embedding_generator
    mock_vector_db_cls.return_value = mock_vector_db
    mock_db_client_fn.return_value = mock_db_client

    # Mock vector search to return Wikipedia results
    mock_search_results = [
        {
            "id": "wiki-vector-1",
            "score": 0.88,
            "metadata": {
                "text": "Wikipedia article content about the landmark.",
                "landmark_id": "LP-00456",
                "source_type": "wikipedia",
                "article_title": "Test Landmark Wikipedia",
                "article_url": "https://en.wikipedia.org/wiki/Test_Landmark",
            },
        }
    ]
    mock_vector_db.query_vectors.return_value = mock_search_results

    # Make API request with source type filter
    payload = {"query": "wikipedia content", "source_type": "wikipedia", "top_k": 3}

    response = client.post("/api/query/search", json=payload)

    # Verify response
    assert response.status_code == 200
    data = response.json()

    assert data["source_type"] == "wikipedia"
    assert len(data["results"]) == 1
    assert data["results"][0]["source_type"] == "wikipedia"
    assert "Wikipedia:" in data["results"][0]["source"]

    # Verify filter was passed to vector database
    call_args = mock_vector_db.query_vectors.call_args
    filter_dict = call_args[0][2]
    assert filter_dict is not None
    assert filter_dict["source_type"] == "wikipedia"


@pytest.mark.functional
@patch("nyc_landmarks.api.query.get_db_client")
@patch("nyc_landmarks.api.query.PineconeDB")
@patch("nyc_landmarks.api.query.EmbeddingGenerator")
def test_query_api_no_results(
    mock_embedding_cls: Any,
    mock_vector_db_cls: Any,
    mock_db_client_fn: Any,
    mock_embedding_generator: Any,
    mock_vector_db: Any,
    mock_db_client: Any,
) -> None:
    """Test search that returns no results."""
    # Setup mocks
    mock_embedding_cls.return_value = mock_embedding_generator
    mock_vector_db_cls.return_value = mock_vector_db
    mock_db_client_fn.return_value = mock_db_client

    # Mock vector search to return empty results
    mock_vector_db.query_vectors.return_value = []

    # Make API request
    payload = {"query": "non-existent content", "top_k": 5}

    response = client.post("/api/query/search", json=payload)

    # Verify response structure is correct even with no results
    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert "query" in data
    assert "count" in data
    assert data["query"] == "non-existent content"
    assert data["count"] == 0
    assert len(data["results"]) == 0

    # Verify embedding generation and vector search were still called
    mock_embedding_generator.generate_embedding.assert_called_once_with(
        "non-existent content"
    )
    mock_vector_db.query_vectors.assert_called_once()


@pytest.mark.functional
@patch("nyc_landmarks.api.query.get_db_client")
@patch("nyc_landmarks.api.query.PineconeDB")
@patch("nyc_landmarks.api.query.EmbeddingGenerator")
def test_query_api_embedding_error(
    mock_embedding_cls: Any,
    mock_vector_db_cls: Any,
    mock_db_client_fn: Any,
    mock_embedding_generator: Any,
    mock_vector_db: Any,
    mock_db_client: Any,
) -> None:
    """Test handling of embedding generation errors."""
    # Setup mocks
    mock_embedding_cls.return_value = mock_embedding_generator
    mock_vector_db_cls.return_value = mock_vector_db
    mock_db_client_fn.return_value = mock_db_client

    # Mock embedding generation to raise an error
    mock_embedding_generator.generate_embedding.side_effect = Exception(
        "OpenAI API error"
    )

    # Make API request
    payload = {"query": "test query", "top_k": 3}

    response = client.post("/api/query/search", json=payload)

    # Should return 500 error due to embedding generation failure
    assert response.status_code == 500
    assert "OpenAI API error" in response.json()["detail"]


@pytest.mark.functional
@patch("nyc_landmarks.api.query.get_db_client")
@patch("nyc_landmarks.api.query.PineconeDB")
@patch("nyc_landmarks.api.query.EmbeddingGenerator")
def test_query_api_vector_db_error(
    mock_embedding_cls: Any,
    mock_vector_db_cls: Any,
    mock_db_client_fn: Any,
    mock_embedding_generator: Any,
    mock_vector_db: Any,
    mock_db_client: Any,
) -> None:
    """Test handling of vector database errors."""
    # Setup mocks
    mock_embedding_cls.return_value = mock_embedding_generator
    mock_vector_db_cls.return_value = mock_vector_db
    mock_db_client_fn.return_value = mock_db_client

    # Mock vector database to raise an error
    mock_vector_db.query_vectors.side_effect = Exception("Pinecone connection error")

    # Make API request
    payload = {"query": "test query", "top_k": 3}

    response = client.post("/api/query/search", json=payload)

    # Should return 500 error due to vector database failure
    assert response.status_code == 500
    assert "Pinecone connection error" in response.json()["detail"]


@pytest.mark.functional
@patch("nyc_landmarks.api.query.PineconeDB")
@patch("nyc_landmarks.api.query.EmbeddingGenerator")
def test_query_api_landmark_name_enrichment(
    mock_embedding_cls: Any,
    mock_vector_db_cls: Any,
    mock_embedding_generator: Any,
    mock_vector_db: Any,
    mock_db_client: Any,
) -> None:
    """Test that landmark names are properly enriched from database."""
    # Setup mocks
    mock_embedding_cls.return_value = mock_embedding_generator
    mock_vector_db_cls.return_value = mock_vector_db

    # Mock vector search results
    mock_search_results = [
        {
            "id": "vector-1",
            "score": 0.95,
            "metadata": {
                "text": "Historic building content.",
                "landmark_id": "LP-00789",
                "source_type": "pdf",
            },
        }
    ]
    mock_vector_db.query_vectors.return_value = mock_search_results

    # Mock database client to return landmark name
    mock_db_client.get_landmark_by_id.return_value = {
        "id": "LP-00789",
        "name": "Famous Historic Building",
        "location": "123 Test Street",
    }

    # Use FastAPI dependency overrides to inject the mock db_client
    from nyc_landmarks.api.query import get_db_client
    from nyc_landmarks.main import app as fastapi_app

    fastapi_app.dependency_overrides[get_db_client] = lambda: mock_db_client
    try:
        payload = {"query": "historic building", "top_k": 1}
        response = client.post("/api/query/search", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        result = data["results"][0]
        assert result["landmark_id"] == "LP-00789"
        assert result["landmark_name"] == "Famous Historic Building"
        mock_db_client.get_landmark_by_id.assert_called_with("LP-00789")
    finally:
        fastapi_app.dependency_overrides = {}


@pytest.mark.functional
def test_query_api_validation_errors() -> None:
    """Test various validation errors."""

    # Test missing query field
    response = client.post("/api/query/search", json={})
    assert response.status_code == 422

    # Test invalid top_k (too high)
    response = client.post(
        "/api/query/search", json={"query": "test", "top_k": 100}  # Max is 20
    )
    assert response.status_code == 422

    # Test invalid top_k (negative)
    response = client.post("/api/query/search", json={"query": "test", "top_k": -1})
    assert response.status_code == 422

    # Test invalid top_k (zero)
    response = client.post("/api/query/search", json={"query": "test", "top_k": 0})
    assert response.status_code == 422


@pytest.mark.functional
@patch("nyc_landmarks.api.query.get_db_client")
@patch("nyc_landmarks.api.query.PineconeDB")
@patch("nyc_landmarks.api.query.EmbeddingGenerator")
def test_query_api_landmark_specific_endpoint(
    mock_embedding_cls: Any,
    mock_vector_db_cls: Any,
    mock_db_client_fn: Any,
    mock_embedding_generator: Any,
    mock_vector_db: Any,
    mock_db_client: Any,
) -> None:
    """Test the landmark-specific endpoint that requires landmark_id."""
    # Setup mocks
    mock_embedding_cls.return_value = mock_embedding_generator
    mock_vector_db_cls.return_value = mock_vector_db
    mock_db_client_fn.return_value = mock_db_client

    # Mock vector search results
    mock_search_results = create_mock_search_results(1)
    mock_vector_db.query_vectors.return_value = mock_search_results

    # Test successful request with landmark_id
    payload = {"query": "architecture details", "landmark_id": "LP-00001", "top_k": 3}

    response = client.post("/api/query/search/landmark", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["landmark_id"] == "LP-00001"

    # Test request without landmark_id (should fail)
    payload_no_id = {"query": "architecture details", "top_k": 3}

    response = client.post("/api/query/search/landmark", json=payload_no_id)
    assert response.status_code == 400
    assert "landmark_id is required" in response.json()["detail"]


@pytest.mark.functional
def test_query_api_empire_state_building_mock() -> None:
    """Test the exact Empire State Building query with mocked successful response."""

    from nyc_landmarks.api.query import get_db_client
    from nyc_landmarks.main import app as fastapi_app

    with (
        patch("nyc_landmarks.api.query.EmbeddingGenerator") as mock_embedding_cls,
        patch("nyc_landmarks.api.query.PineconeDB") as mock_vector_db_cls,
    ):
        # Setup mocks
        mock_embedding_generator = Mock()
        mock_embedding_generator.generate_embedding.return_value = [0.1] * 1536
        mock_embedding_cls.return_value = mock_embedding_generator

        mock_vector_db = Mock()
        mock_search_results = [
            {
                "id": "empire-state-vector",
                "score": 0.92,
                "metadata": {
                    "text": "The Empire State Building is a historic skyscraper located in Manhattan, New York City. Built in 1931, it was the world's tallest building for nearly 40 years.",
                    "landmark_id": "LP-02560",
                    "source_type": "pdf",
                    "document_name": "empire_state_building_designation_report.pdf",
                    "document_url": "https://example.com/empire_state_report.pdf",
                },
            }
        ]
        mock_vector_db.query_vectors.return_value = mock_search_results
        mock_vector_db_cls.return_value = mock_vector_db

        mock_db_client = Mock()
        mock_db_client.get_landmark_by_id.return_value = {
            "id": "LP-02560",
            "name": "Empire State Building",
            "location": "350 Fifth Avenue",
            "borough": "Manhattan",
        }
        fastapi_app.dependency_overrides[get_db_client] = lambda: mock_db_client
        try:
            payload = {
                "query": "What is the history of the Empire State Building?",
                "source_type": "pdf",
                "top_k": 5,
            }
            response = client.post("/api/query/search", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "What is the history of the Empire State Building?"
            assert data["source_type"] == "pdf"
            assert data["count"] == 1
            result = data["results"][0]
            assert result["landmark_id"] == "LP-02560"
            assert result["landmark_name"] == "Empire State Building"
            assert result["source_type"] == "pdf"
            assert "Empire State Building" in result["text"]
        finally:
            fastapi_app.dependency_overrides = {}


if __name__ == "__main__":
    # Allow running this test file directly for debugging
    pytest.main([__file__, "-v", "-s"])
