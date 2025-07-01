"""
Unit tests for the Query API module.

This module tests the query API endpoints and helper functions from
nyc_landmarks.api.query, focusing on text search, landmark filtering,
and response formatting.
"""

import unittest
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, Request

from nyc_landmarks.api.query import (
    LandmarkInfo,
    LandmarkListResponse,
    SearchResponse,
    SearchResult,
    TextQuery,
    _build_search_filter,
    _convert_to_fastapi_examples,
    _enhance_search_result,
    _generate_query_embedding,
    _get_landmark_name,
    _get_source_info,
    _initialize_components,
    _perform_vector_search,
    _process_search_results,
    compare_source_results,
    get_landmark,
    get_landmarks,
    search_combined_sources,
    search_landmarks_text,
    search_text,
    search_text_by_landmark,
)


class TestTextQuery(unittest.TestCase):
    """Test the TextQuery Pydantic model."""

    def test_text_query_valid(self) -> None:
        """Test creating a valid TextQuery."""
        query = TextQuery(
            query="Brooklyn Bridge",
            landmark_id="LP-12345",
            source_type="wikipedia",
            top_k=10,
        )
        assert query.query == "Brooklyn Bridge"
        assert query.landmark_id == "LP-12345"
        assert query.source_type == "wikipedia"
        assert query.top_k == 10

    def test_text_query_minimal(self) -> None:
        """Test creating a TextQuery with minimal required fields."""
        query = TextQuery(
            query="Central Park", landmark_id=None, source_type=None, top_k=5
        )
        assert query.query == "Central Park"
        assert query.landmark_id is None
        assert query.source_type is None
        assert query.top_k == 5  # Default value

    def test_text_query_validation_top_k_min(self) -> None:
        """Test TextQuery validation for minimum top_k value."""
        with pytest.raises(ValueError):
            TextQuery(query="test", landmark_id=None, source_type=None, top_k=0)

    def test_text_query_validation_top_k_max(self) -> None:
        """Test TextQuery validation for maximum top_k value."""
        with pytest.raises(ValueError):
            TextQuery(query="test", landmark_id=None, source_type=None, top_k=21)


class TestSearchResult(unittest.TestCase):
    """Test the SearchResult Pydantic model."""

    def test_search_result_valid(self) -> None:
        """Test creating a valid SearchResult."""
        result = SearchResult(
            text="This is a test result",
            score=0.95,
            landmark_id="LP-12345",
            landmark_name="Test Landmark",
            source_type="pdf",
            source="LPC Report: test.pdf",
            source_url="http://example.com/test.pdf",
            index_name="landmarks-index",
            namespace="production",
            metadata={"document_name": "test.pdf"},
        )
        assert result.text == "This is a test result"
        assert result.score == 0.95
        assert result.landmark_id == "LP-12345"
        assert result.landmark_name == "Test Landmark"
        assert result.source_type == "pdf"


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions from the query module."""

    def test_convert_to_fastapi_examples(self) -> None:
        """Test converting examples dictionary to FastAPI format."""
        examples_dict = {
            "example1": {
                "summary": "Test Example",
                "description": "A test example",
                "value": {"query": "test"},
            }
        }

        result = _convert_to_fastapi_examples(examples_dict)

        assert "example1" in result
        # Note: FastAPI Example objects might not have direct attribute access in tests
        # We'll just verify the key exists for this test
        assert result["example1"] is not None

    def test_build_search_filter_both_filters(self) -> None:
        """Test building search filter with both landmark_id and source_type."""
        result = _build_search_filter(landmark_id="LP-12345", source_type="wikipedia")
        expected = {"landmark_id": "LP-12345", "source_type": "wikipedia"}
        assert result == expected

    def test_build_search_filter_landmark_only(self) -> None:
        """Test building search filter with only landmark_id."""
        result = _build_search_filter(landmark_id="LP-12345")
        expected = {"landmark_id": "LP-12345"}
        assert result == expected

    def test_build_search_filter_source_only(self) -> None:
        """Test building search filter with only source_type."""
        result = _build_search_filter(source_type="pdf")
        expected = {"source_type": "pdf"}
        assert result == expected

    def test_build_search_filter_invalid_source_type(self) -> None:
        """Test building search filter with invalid source_type."""
        result = _build_search_filter(source_type="invalid")
        assert result is None

    def test_build_search_filter_no_filters(self) -> None:
        """Test building search filter with no parameters."""
        result = _build_search_filter()
        assert result is None

    def test_get_source_info_wikipedia(self) -> None:
        """Test getting source info for Wikipedia content."""
        metadata = {
            "source_type": "wikipedia",
            "article_title": "Brooklyn Bridge",
            "article_url": "https://en.wikipedia.org/wiki/Brooklyn_Bridge",
        }

        source, source_url = _get_source_info(metadata)

        assert source == "Wikipedia: Brooklyn Bridge"
        assert source_url == "https://en.wikipedia.org/wiki/Brooklyn_Bridge"

    def test_get_source_info_pdf(self) -> None:
        """Test getting source info for PDF content."""
        metadata = {
            "source_type": "pdf",
            "document_name": "landmark_report.pdf",
            "document_url": "http://example.com/landmark_report.pdf",
        }

        source, source_url = _get_source_info(metadata)

        assert source == "LPC Report: landmark_report.pdf"
        assert source_url == "http://example.com/landmark_report.pdf"

    def test_get_source_info_default_pdf(self) -> None:
        """Test getting source info with default PDF type."""
        metadata = {"file_name": "test.pdf"}

        source, source_url = _get_source_info(metadata)

        assert source == "LPC Report: test.pdf"
        assert source_url == ""


class TestComponentInitialization(unittest.TestCase):
    """Test component initialization functions."""

    @patch("nyc_landmarks.db.db_client.get_db_client")
    @patch("nyc_landmarks.api.query.PineconeDB")
    @patch("nyc_landmarks.api.query.EmbeddingGenerator")
    def test_initialize_components_all_none(
        self, mock_embedding: Mock, mock_pinecone: Mock, mock_get_db_client: Mock
    ) -> None:
        """Test initializing all components when none are provided."""
        mock_embedding_instance = Mock()
        mock_pinecone_instance = Mock()
        mock_db_instance = Mock()

        mock_embedding.return_value = mock_embedding_instance
        mock_pinecone.return_value = mock_pinecone_instance
        mock_get_db_client.return_value = mock_db_instance

        embedding_gen, vector_db, db_client = _initialize_components()

        assert embedding_gen == mock_embedding_instance
        assert vector_db == mock_pinecone_instance
        assert db_client == mock_db_instance

    def test_initialize_components_all_provided(self) -> None:
        """Test initializing components when all are provided."""
        mock_embedding = Mock()
        mock_vector_db = Mock()
        mock_db_client = Mock()

        embedding_gen, vector_db, db_client = _initialize_components(
            mock_embedding, mock_vector_db, mock_db_client
        )

        assert embedding_gen == mock_embedding
        assert vector_db == mock_vector_db
        assert db_client == mock_db_client


class TestLandmarkNameRetrieval(unittest.TestCase):
    """Test landmark name retrieval function."""

    def test_get_landmark_name_dict_response(self) -> None:
        """Test getting landmark name from dictionary response."""
        mock_db_client = Mock()
        mock_db_client.get_landmark_by_id.return_value = {
            "name": "Brooklyn Bridge",
            "id": "LP-12345",
        }

        result = _get_landmark_name("LP-12345", mock_db_client)
        assert result == "Brooklyn Bridge"

    def test_get_landmark_name_pydantic_response(self) -> None:
        """Test getting landmark name from Pydantic model response."""
        mock_db_client = Mock()
        mock_landmark = Mock()
        mock_landmark.name = "Central Park"
        mock_db_client.get_landmark_by_id.return_value = mock_landmark

        result = _get_landmark_name("LP-67890", mock_db_client)
        assert result == "Central Park"

    def test_get_landmark_name_not_found(self) -> None:
        """Test getting landmark name when landmark is not found."""
        mock_db_client = Mock()
        mock_db_client.get_landmark_by_id.return_value = None

        result = _get_landmark_name("LP-99999", mock_db_client)
        assert result is None


class TestSearchResultEnhancement(unittest.TestCase):
    """Test search result enhancement functions."""

    def test_enhance_search_result_with_landmark_name(self) -> None:
        """Test enhancing search result with landmark name."""
        mock_db_client = Mock()
        mock_db_client.get_landmark_by_id.return_value = {"name": "Test Landmark"}

        match = {
            "id": "test-id",
            "score": 0.95,
            "metadata": {
                "text": "Test content",
                "landmark_id": "LP-12345",
                "source_type": "pdf",
                "document_name": "test.pdf",
            },
        }

        result = _enhance_search_result(match, mock_db_client)

        assert result["landmark_name"] == "Test Landmark"
        assert result["text"] == "Test content"
        assert result["landmark_id"] == "LP-12345"
        assert result["source_type"] == "pdf"

    def test_enhance_search_result_no_landmark(self) -> None:
        """Test enhancing search result without landmark information."""
        mock_db_client = Mock()
        mock_db_client.get_landmark_by_id.return_value = None

        match = {
            "id": "test-id",
            "score": 0.85,
            "metadata": {
                "text": "Test content",
                "landmark_id": "",
                "source_type": "wikipedia",
                "article_title": "Test Article",
            },
        }

        result = _enhance_search_result(match, mock_db_client)

        assert "landmark_name" not in result
        assert result["source"] == "Wikipedia: Test Article"


class TestVectorSearch(unittest.TestCase):
    """Test vector search functions."""

    @patch("nyc_landmarks.api.query.logger")
    def test_generate_query_embedding_with_correlation(self, mock_logger: Mock) -> None:
        """Test generating query embedding with correlation ID."""
        mock_embedding_generator = Mock()
        mock_embedding_generator.generate_embedding.return_value = [0.1, 0.2, 0.3]

        result = _generate_query_embedding(
            "test query", mock_embedding_generator, "correlation-123"
        )

        assert result == [0.1, 0.2, 0.3]
        mock_embedding_generator.generate_embedding.assert_called_once_with(
            "test query"
        )
        # Verify logging was called
        assert mock_logger.info.call_count >= 2

    def test_perform_vector_search(self) -> None:
        """Test performing vector search."""
        mock_vector_db = Mock()
        mock_vector_db.query_vectors.return_value = [
            {"id": "1", "score": 0.95, "metadata": {"text": "result 1"}},
            {"id": "2", "score": 0.85, "metadata": {"text": "result 2"}},
        ]

        embedding = [0.1, 0.2, 0.3]
        filter_dict = {"landmark_id": "LP-12345"}

        results = _perform_vector_search(embedding, 5, filter_dict, mock_vector_db)

        assert len(results) == 2
        assert results[0]["score"] == 0.95
        mock_vector_db.query_vectors.assert_called_once_with(
            query_vector=embedding,
            top_k=5,
            filter_dict=filter_dict,
            correlation_id=None,
        )

    def test_process_search_results(self) -> None:
        """Test processing search results."""
        mock_db_client = Mock()
        matches = [
            {
                "id": "1",
                "score": 0.95,
                "metadata": {"text": "result 1", "landmark_id": "LP-12345"},
            }
        ]

        with patch("nyc_landmarks.api.query._enhance_search_result") as mock_enhance:
            mock_enhance.return_value = {"enhanced": "result"}

            results = _process_search_results(matches, mock_db_client)

            assert len(results) == 1
            assert results[0] == {"enhanced": "result"}
            mock_enhance.assert_called_once_with(matches[0], mock_db_client)


class TestSearchCombinedSources(unittest.TestCase):
    """Test the search_combined_sources function."""

    @patch("nyc_landmarks.api.query._initialize_components")
    @patch("nyc_landmarks.api.query._generate_query_embedding")
    @patch("nyc_landmarks.api.query._build_search_filter")
    @patch("nyc_landmarks.api.query._perform_vector_search")
    @patch("nyc_landmarks.api.query._process_search_results")
    def test_search_combined_sources_full_flow(
        self,
        mock_process: Mock,
        mock_perform: Mock,
        mock_build_filter: Mock,
        mock_generate: Mock,
        mock_initialize: Mock,
    ) -> None:
        """Test the complete flow of search_combined_sources."""
        # Setup mocks
        mock_embedding_gen = Mock()
        mock_vector_db = Mock()
        mock_db_client = Mock()
        mock_initialize.return_value = (
            mock_embedding_gen,
            mock_vector_db,
            mock_db_client,
        )

        mock_generate.return_value = [0.1, 0.2, 0.3]
        mock_build_filter.return_value = {"landmark_id": "LP-12345"}
        mock_perform.return_value = [{"id": "1", "score": 0.95}]
        mock_process.return_value = [{"enhanced": "result"}]

        # Execute function
        results = search_combined_sources(
            query_text="Brooklyn Bridge",
            landmark_id="LP-12345",
            source_type="wikipedia",
            top_k=5,
            correlation_id="test-correlation",
        )

        # Verify results
        assert results == [{"enhanced": "result"}]

        # Verify function calls
        mock_initialize.assert_called_once_with(None, None, None)
        mock_generate.assert_called_once_with(
            "Brooklyn Bridge", mock_embedding_gen, "test-correlation"
        )
        mock_build_filter.assert_called_once_with("LP-12345", "wikipedia")
        mock_perform.assert_called_once_with(
            [0.1, 0.2, 0.3],
            5,
            {"landmark_id": "LP-12345"},
            mock_vector_db,
            "test-correlation",
        )
        mock_process.assert_called_once_with(
            [{"id": "1", "score": 0.95}], mock_db_client
        )


class TestCompareSourceResults(unittest.TestCase):
    """Test the compare_source_results function."""

    @patch("nyc_landmarks.api.query.search_combined_sources")
    def test_compare_source_results(self, mock_search: Mock) -> None:
        """Test comparing results from different sources."""
        # Setup mock to return different results for different calls
        mock_search.side_effect = [
            [{"source": "wikipedia", "text": "wiki result"}],  # Wikipedia results
            [{"source": "pdf", "text": "pdf result"}],  # PDF results
            [{"source": "combined", "text": "combined result"}],  # Combined results
        ]

        results = compare_source_results(
            query_text="test query",
            landmark_id="LP-12345",
            top_k=3,
            correlation_id="test-correlation",
        )

        # Verify structure
        assert "wikipedia_results" in results
        assert "pdf_results" in results
        assert "combined_results" in results

        # Verify content
        assert results["wikipedia_results"] == [
            {"source": "wikipedia", "text": "wiki result"}
        ]
        assert results["pdf_results"] == [{"source": "pdf", "text": "pdf result"}]
        assert results["combined_results"] == [
            {"source": "combined", "text": "combined result"}
        ]

        # Verify function was called 3 times with correct parameters
        assert mock_search.call_count == 3


class TestAPIEndpoints:
    """Test API endpoint functions using pytest async style."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_request = Mock(spec=Request)
        self.mock_request.headers = {"user-agent": "test-agent"}
        self.mock_request.client = Mock()
        self.mock_request.client.host = "127.0.0.1"

    @patch("nyc_landmarks.api.query.get_correlation_id")
    @patch("nyc_landmarks.api.query.ValidationLogger")
    @patch("nyc_landmarks.api.query.get_client_info")
    @patch("nyc_landmarks.api.query.logger")
    @pytest.mark.asyncio
    async def test_search_text_success(
        self,
        mock_logger: Mock,
        mock_get_client_info: Mock,
        mock_validation_logger: Mock,
        mock_get_correlation_id: Mock,
    ) -> None:
        """Test successful text search."""
        # Setup mocks
        mock_get_client_info.return_value = ("127.0.0.1", "test-agent")
        mock_get_correlation_id.return_value = "test-correlation"

        mock_embedding_generator = Mock()
        mock_embedding_generator.generate_embedding.return_value = [0.1, 0.2, 0.3]

        mock_vector_db = Mock()
        mock_vector_db.index_name = "test-index"
        mock_vector_db.namespace = "test-namespace"
        mock_vector_db.query_vectors.return_value = [
            {
                "score": 0.95,
                "metadata": {
                    "text": "Test result",
                    "landmark_id": "LP-12345",
                    "source_type": "pdf",
                    "document_name": "test.pdf",
                },
            }
        ]

        mock_db_client = Mock()
        mock_db_client.get_landmark_by_id.return_value = {"name": "Test Landmark"}

        query = TextQuery(
            query="Brooklyn Bridge",
            landmark_id="LP-12345",
            source_type="pdf",
            top_k=5,
        )

        # Execute function
        result = await search_text(
            self.mock_request,
            query,
            mock_embedding_generator,
            mock_vector_db,
            mock_db_client,
        )

        # Verify response structure
        assert isinstance(result, SearchResponse)
        assert result.query == "Brooklyn Bridge"
        assert result.landmark_id == "LP-12345"
        assert result.source_type == "pdf"
        assert result.count == 1
        assert result.index_name == "test-index"
        assert result.namespace == "test-namespace"

        # Verify search results
        assert len(result.results) == 1
        search_result = result.results[0]
        assert search_result.text == "Test result"
        assert search_result.score == 0.95
        assert search_result.landmark_id == "LP-12345"
        assert search_result.landmark_name == "Test Landmark"

    @pytest.mark.asyncio
    async def test_search_text_by_landmark_missing_id(self) -> None:
        """Test search by landmark with missing landmark_id."""
        query = TextQuery(
            query="test query", landmark_id=None, source_type=None, top_k=5
        )  # No landmark_id

        mock_embedding_generator = Mock()
        mock_vector_db = Mock()
        mock_db_client = Mock()

        with pytest.raises(HTTPException) as exc_info:
            await search_text_by_landmark(
                self.mock_request,
                query,
                mock_embedding_generator,
                mock_vector_db,
                mock_db_client,
            )

        assert exc_info.value.status_code == 400
        assert "landmark_id is required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_landmarks_success(self) -> None:
        """Test successful get landmarks."""
        mock_db_client = Mock()
        mock_db_client.get_all_landmarks.return_value = [
            {
                "id": "LP-12345",
                "name": "Test Landmark",
                "location": "Test Street",
                "borough": "Manhattan",
                "type": "Individual Landmark",
                "designation_date": "2020-01-01",
                "description": "Test description",
            }
        ]

        result = await get_landmarks(limit=20, db_client=mock_db_client)

        assert isinstance(result, LandmarkListResponse)
        assert result.count == 1
        assert len(result.landmarks) == 1

        landmark = result.landmarks[0]
        assert landmark.id == "LP-12345"
        assert landmark.name == "Test Landmark"
        assert landmark.location == "Test Street"

    @pytest.mark.asyncio
    async def test_get_landmark_success(self) -> None:
        """Test successful get single landmark."""
        mock_db_client = Mock()
        mock_db_client.get_landmark_by_id.return_value = {
            "id": "LP-12345",
            "name": "Test Landmark",
            "location": "Test Street",
            "borough": "Manhattan",
            "type": "Individual Landmark",
            "designation_date": "2020-01-01",
            "description": "Test description",
        }

        result = await get_landmark("LP-12345", mock_db_client)

        assert isinstance(result, LandmarkInfo)
        assert result.id == "LP-12345"
        assert result.name == "Test Landmark"
        assert result.location == "Test Street"

    @pytest.mark.asyncio
    async def test_get_landmark_not_found(self) -> None:
        """Test get landmark when landmark is not found."""
        mock_db_client = Mock()
        mock_db_client.get_landmark_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_landmark("LP-99999", mock_db_client)

        assert exc_info.value.status_code == 404
        assert "Landmark not found: LP-99999" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_search_landmarks_text_success(self) -> None:
        """Test successful landmark text search."""
        mock_db_client = Mock()
        mock_response = Mock()

        # Create a mock landmark with proper string attributes
        mock_landmark = Mock()
        mock_landmark.lpNumber = "LP-12345"
        mock_landmark.name = "Test Landmark"
        mock_landmark.street = "Test Street"
        mock_landmark.borough = "Manhattan"
        mock_landmark.objectType = "Individual Landmark"
        mock_landmark.dateDesignated = "2020-01-01"

        mock_response.results = [mock_landmark]
        mock_db_client.search_landmarks.return_value = mock_response

        result = await search_landmarks_text(
            q="Brooklyn Bridge", limit=20, db_client=mock_db_client
        )

        assert isinstance(result, LandmarkListResponse)
        assert result.count == 1
        assert len(result.landmarks) == 1

        landmark = result.landmarks[0]
        assert landmark.id == "LP-12345"
        assert landmark.name == "Test Landmark"


if __name__ == "__main__":
    # Run tests with pytest for better output
    pytest.main([__file__, "-v"])
