"""
Unit tests for PineconeDB class.

Tests the core vector database operations, focusing on:
- Initialization and connection
- Vector storage and retrieval
- Metadata handling
- Query operations
- Error handling
"""

import os
import unittest
from typing import Any, Dict
from unittest.mock import Mock, patch

from nyc_landmarks.vectordb.pinecone_db import PineconeDB


class TestPineconeDBInitialization(unittest.TestCase):
    """Test PineconeDB initialization and configuration."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_config = {
            "PINECONE_API_KEY": "test-api-key",
            "PINECONE_ENVIRONMENT": "test-env",
            "PINECONE_INDEX_NAME": "test-index",
            "PINECONE_NAMESPACE": "test-namespace",
        }

    @patch.dict(
        os.environ,
        {"PINECONE_API_KEY": "test-api-key", "PINECONE_INDEX_NAME": "test-index"},
    )
    @patch("nyc_landmarks.vectordb.pinecone_db.Pinecone")
    def test_initialization_with_env_vars(self, mock_pinecone: Mock) -> None:
        """Test initialization using environment variables."""
        mock_pc = Mock()
        mock_pinecone.return_value = mock_pc
        mock_index = Mock()
        mock_pc.Index.return_value = mock_index

        db = PineconeDB()

        self.assertEqual(db.api_key, "test-api-key")
        self.assertEqual(db.index_name, "test-index")
        mock_pinecone.assert_called_once_with(api_key="test-api-key")
        mock_pc.Index.assert_called_once_with("test-index")

    @patch("nyc_landmarks.vectordb.pinecone_db.Pinecone")
    def test_initialization_with_custom_index_name(self, mock_pinecone: Mock) -> None:
        """Test initialization with custom index name."""
        mock_pc = Mock()
        mock_pinecone.return_value = mock_pc
        mock_index = Mock()
        mock_pc.Index.return_value = mock_index

        custom_index = "custom-test-index"
        db = PineconeDB(index_name=custom_index)

        self.assertEqual(db.index_name, custom_index)
        mock_pc.Index.assert_called_once_with(custom_index)

    @patch("nyc_landmarks.vectordb.pinecone_db.Pinecone")
    def test_initialization_connection_failure(self, mock_pinecone: Mock) -> None:
        """Test initialization with connection failure."""
        mock_pc = Mock()
        mock_pinecone.return_value = mock_pc
        mock_pc.Index.side_effect = Exception("Connection failed")

        with self.assertRaises(Exception) as context:
            PineconeDB()

        self.assertIn("Connection failed", str(context.exception))

    def test_initialization_without_index_name(self) -> None:
        """Test that initialization fails gracefully without index name."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("nyc_landmarks.vectordb.pinecone_db.settings") as mock_settings:
                mock_settings.PINECONE_INDEX_NAME = None
                mock_settings.PINECONE_API_KEY = "test-key"
                mock_settings.PINECONE_ENVIRONMENT = "test-env"
                mock_settings.PINECONE_NAMESPACE = "test-ns"
                mock_settings.PINECONE_DIMENSIONS = 1536

                with patch("nyc_landmarks.vectordb.pinecone_db.Pinecone"):
                    with self.assertRaises(ValueError) as context:
                        PineconeDB()

                    self.assertIn("index name cannot be None", str(context.exception))


class TestPineconeDBHelperMethods(unittest.TestCase):
    """Test helper methods for metadata and ID generation."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_pc = Mock()
        self.mock_index = Mock()

        with patch("nyc_landmarks.vectordb.pinecone_db.Pinecone") as mock_pinecone:
            mock_pinecone.return_value = self.mock_pc
            self.mock_pc.Index.return_value = self.mock_index
            self.db = PineconeDB(index_name="test-index")

    def test_get_source_type_from_prefix(self) -> None:
        """Test source type determination from ID prefix."""
        # Test wikipedia prefix
        self.assertEqual(self.db._get_source_type_from_prefix("wiki-"), "wikipedia")
        self.assertEqual(
            self.db._get_source_type_from_prefix("wiki-article"), "wikipedia"
        )

        # Test test prefix
        self.assertEqual(self.db._get_source_type_from_prefix("test-"), "test")
        self.assertEqual(self.db._get_source_type_from_prefix("test-data"), "test")

        # Test default (PDF)
        self.assertEqual(self.db._get_source_type_from_prefix(""), "pdf")
        self.assertEqual(self.db._get_source_type_from_prefix("document-"), "pdf")
        self.assertEqual(self.db._get_source_type_from_prefix("landmark-"), "pdf")

    def test_get_filter_dict_for_deletion(self) -> None:
        """Test filter dictionary creation for deletion."""
        landmark_id = "landmark123"

        # Test wikipedia source
        filter_dict = self.db._get_filter_dict_for_deletion(landmark_id, "wiki-")
        expected = {"landmark_id": landmark_id, "source_type": "wikipedia"}
        self.assertEqual(filter_dict, expected)

        # Test test source
        filter_dict = self.db._get_filter_dict_for_deletion(landmark_id, "test-")
        expected = {"landmark_id": landmark_id, "source_type": "test"}
        self.assertEqual(filter_dict, expected)

        # Test default (PDF) source
        filter_dict = self.db._get_filter_dict_for_deletion(landmark_id, "")
        expected = {"landmark_id": landmark_id, "source_type": "pdf"}
        self.assertEqual(filter_dict, expected)

    def test_generate_vector_id_fixed(self) -> None:
        """Test deterministic vector ID generation."""
        landmark_id = "landmark123"
        id_prefix = "test-"
        index = 5

        vector_id = self.db._generate_vector_id(
            id_prefix, landmark_id, index, use_fixed_ids=True
        )
        expected = f"{id_prefix}{landmark_id}-chunk-{index}"
        self.assertEqual(vector_id, expected)

    def test_generate_vector_id_random(self) -> None:
        """Test random vector ID generation."""
        id_prefix = "test-"

        with patch("nyc_landmarks.vectordb.pinecone_db.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = "mock-uuid-1234"
            vector_id = self.db._generate_vector_id(
                id_prefix, None, 0, use_fixed_ids=False
            )
            expected = f"{id_prefix}mock-uuid-1234"
            self.assertEqual(vector_id, expected)

    def test_build_basic_metadata(self) -> None:
        """Test basic metadata building."""
        chunk = {"text": "Test chunk content", "other_field": "ignored"}
        source_type = "wikipedia"
        chunk_index = 2
        landmark_id = "landmark123"

        metadata = self.db._build_basic_metadata(
            chunk, source_type, chunk_index, landmark_id
        )

        expected = {
            "text": "Test chunk content",
            "source_type": "wikipedia",
            "chunk_index": 2,
            "landmark_id": "landmark123",
        }
        self.assertEqual(metadata, expected)

    def test_build_basic_metadata_without_landmark_id(self) -> None:
        """Test basic metadata building without landmark ID."""
        chunk = {"text": "Test content"}

        metadata = self.db._build_basic_metadata(chunk, "pdf", 0, None)

        expected = {"text": "Test content", "source_type": "pdf", "chunk_index": 0}
        self.assertEqual(metadata, expected)

    def test_add_processing_date_from_chunk(self) -> None:
        """Test adding processing date from chunk."""
        metadata: Dict[str, Any] = {}

        # Test direct processing_date in chunk
        chunk = {"processing_date": "2024-01-01"}
        self.db._add_processing_date(metadata, chunk)
        self.assertEqual(metadata["processing_date"], "2024-01-01")

    def test_add_processing_date_from_chunk_metadata(self) -> None:
        """Test adding processing date from chunk metadata."""
        metadata: Dict[str, Any] = {}

        # Test processing_date in chunk.metadata
        chunk = {"metadata": {"processing_date": "2024-01-02"}}
        self.db._add_processing_date(metadata, chunk)
        self.assertEqual(metadata["processing_date"], "2024-01-02")

    def test_add_processing_date_no_date(self) -> None:
        """Test processing date handling when no date available."""
        metadata: Dict[str, Any] = {}
        chunk = {"text": "content"}

        self.db._add_processing_date(metadata, chunk)
        self.assertNotIn("processing_date", metadata)

    def test_filter_enhanced_metadata(self) -> None:
        """Test enhanced metadata filtering."""
        enhanced_metadata = {
            "landmark_name": "Test Landmark",
            "borough": "Manhattan",
            "source_type": "should_be_filtered",  # Should be filtered out
            "processing_date": "should_be_filtered",  # Should be filtered out
            "complex_dict": {"nested": "data"},  # Should be filtered out
            "complex_list": ["item1", "item2"],  # Should be filtered out
            "building_names": ["Building A", "Building B"],  # Should be kept
            "null_value": None,  # Should be filtered out
            "building_0_name": "Building Name",  # Should be kept
            "valid_string": "keep this",
        }

        filtered = self.db._filter_enhanced_metadata(enhanced_metadata)

        expected = {
            "landmark_name": "Test Landmark",
            "borough": "Manhattan",
            "building_names": ["Building A", "Building B"],
            "building_0_name": "Building Name",
            "valid_string": "keep this",
        }
        self.assertEqual(filtered, expected)


class TestPineconeDBWikipediaMetadata(unittest.TestCase):
    """Test Wikipedia-specific metadata handling."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        with patch("nyc_landmarks.vectordb.pinecone_db.Pinecone") as mock_pinecone:
            mock_pc = Mock()
            mock_pinecone.return_value = mock_pc
            mock_pc.Index.return_value = Mock()
            self.db = PineconeDB(index_name="test-index")

    def test_add_wikipedia_metadata_new_format(self) -> None:
        """Test adding Wikipedia metadata from new format."""
        metadata: Dict[str, Any] = {}
        chunk = {
            "metadata": {
                "article_title": "Test Article",
                "article_url": "https://en.wikipedia.org/wiki/Test_Article",
                "article_quality": "B",
                "article_quality_score": 85,
                "article_quality_description": "Good article",
                "article_rev_id": "123456789",
            }
        }

        self.db._add_wikipedia_metadata(metadata, chunk)

        expected = {
            "article_title": "Test Article",
            "article_url": "https://en.wikipedia.org/wiki/Test_Article",
            "article_quality": "B",
            "article_quality_score": 85,
            "article_quality_description": "Good article",
            "article_rev_id": "123456789",
        }
        self.assertEqual(metadata, expected)

    def test_add_wikipedia_metadata_legacy_format(self) -> None:
        """Test adding Wikipedia metadata from legacy format."""
        metadata: Dict[str, Any] = {}
        chunk = {
            "article_metadata": {
                "title": "Legacy Article",
                "url": "https://en.wikipedia.org/wiki/Legacy_Article",
                "rev_id": "987654321",
            }
        }

        self.db._add_wikipedia_metadata(metadata, chunk)

        expected = {
            "article_title": "Legacy Article",
            "article_url": "https://en.wikipedia.org/wiki/Legacy_Article",
            "article_rev_id": "987654321",
        }
        self.assertEqual(metadata, expected)

    def test_add_wikipedia_metadata_empty_values_filtered(self) -> None:
        """Test that empty values are filtered out."""
        metadata: Dict[str, Any] = {}
        chunk = {
            "metadata": {
                "article_title": "",  # Empty string should be filtered
                "article_url": "https://example.com",  # Non-empty should be kept
                "article_quality": "A",
            }
        }

        self.db._add_wikipedia_metadata(metadata, chunk)

        expected = {"article_url": "https://example.com", "article_quality": "A"}
        self.assertEqual(metadata, expected)


class TestPineconeDBQueryMethods(unittest.TestCase):
    """Test query-related methods."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        with patch("nyc_landmarks.vectordb.pinecone_db.Pinecone") as mock_pinecone:
            mock_pc = Mock()
            mock_pinecone.return_value = mock_pc
            self.mock_index = Mock()
            mock_pc.Index.return_value = self.mock_index
            self.db = PineconeDB(index_name="test-index")

    def test_build_combined_filter(self) -> None:
        """Test building combined filter from components."""
        # Test with all components
        filter_dict = {"custom_field": "value"}
        landmark_id = "landmark123"
        source_type = "wikipedia"

        combined = self.db._build_combined_filter(filter_dict, landmark_id, source_type)

        expected = {
            "custom_field": "value",
            "landmark_id": "landmark123",
            "source_type": "wikipedia",
        }
        self.assertEqual(combined, expected)

    def test_build_combined_filter_partial(self) -> None:
        """Test building combined filter with partial components."""
        # Test with only landmark_id
        combined = self.db._build_combined_filter(None, "landmark123", None)
        expected = {"landmark_id": "landmark123"}
        self.assertEqual(combined, expected)

        # Test with empty inputs
        combined = self.db._build_combined_filter(None, None, None)
        expected = {}
        self.assertEqual(combined, expected)

    def test_get_query_vector_with_vector(self) -> None:
        """Test query vector handling when vector is provided."""
        query_vector = [0.1, 0.2, 0.3]
        result = self.db._get_query_vector(query_vector)
        self.assertEqual(result, query_vector)

    def test_get_query_vector_without_vector(self) -> None:
        """Test query vector handling when no vector is provided."""
        with patch.object(self.db, 'dimensions', 1536):
            result = self.db._get_query_vector(None)
            self.assertEqual(len(result), 1536)
            self.assertTrue(all(x == 0.0 for x in result))

    def test_apply_prefix_filter(self) -> None:
        """Test ID prefix filtering."""
        # Create mock matches with ID attributes
        mock_matches = []
        for i, id_val in enumerate(["test-001", "TEST-002", "other-003", "test-004"]):
            match = Mock()
            match.id = id_val
            mock_matches.append(match)

        # Test case-insensitive prefix filtering
        filtered = self.db._apply_prefix_filter(mock_matches, "test-", top_k=10)

        # Should return matches with IDs starting with "test-" (case-insensitive)
        self.assertEqual(len(filtered), 3)
        filtered_ids = [match.id for match in filtered]
        self.assertIn("test-001", filtered_ids)
        self.assertIn("TEST-002", filtered_ids)  # Case-insensitive
        self.assertIn("test-004", filtered_ids)
        self.assertNotIn("other-003", filtered_ids)

    def test_apply_prefix_filter_with_limit(self) -> None:
        """Test prefix filtering with top_k limit."""
        mock_matches = []
        for i in range(5):
            match = Mock()
            match.id = f"test-{i:03d}"
            mock_matches.append(match)

        filtered = self.db._apply_prefix_filter(mock_matches, "test-", top_k=3)
        self.assertEqual(len(filtered), 3)

    def test_standardize_match(self) -> None:
        """Test match standardization to dictionary format."""
        # Create mock match object
        match = Mock()
        match.id = "test-123"
        match.score = 0.95
        match.metadata = {"landmark_id": "landmark123"}
        match.values = [0.1, 0.2, 0.3]

        # Test with include_values=True
        result = self.db._standardize_match(match, include_values=True)
        expected = {
            "id": "test-123",
            "score": 0.95,
            "metadata": {"landmark_id": "landmark123"},
            "values": [0.1, 0.2, 0.3],
        }
        self.assertEqual(result, expected)

        # Test with include_values=False
        result = self.db._standardize_match(match, include_values=False)
        expected = {
            "id": "test-123",
            "score": 0.95,
            "metadata": {"landmark_id": "landmark123"},
        }
        self.assertEqual(result, expected)


class TestPineconeDBVectorOperations(unittest.TestCase):
    """Test vector storage and retrieval operations."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        with patch("nyc_landmarks.vectordb.pinecone_db.Pinecone") as mock_pinecone:
            mock_pc = Mock()
            mock_pinecone.return_value = mock_pc
            self.mock_index = Mock()
            mock_pc.Index.return_value = self.mock_index
            self.db = PineconeDB(index_name="test-index")

    def test_upsert_vectors_in_batches_success(self) -> None:
        """Test successful vector upserting in batches."""
        vectors = []
        for i in range(250):  # Test batching with 250 vectors
            vectors.append(
                {"id": f"test-{i}", "values": [0.1] * 1536, "metadata": {"index": i}}
            )

        # Mock successful upsert
        self.mock_index.upsert.return_value = None

        # Should not raise exception
        self.db._upsert_vectors_in_batches(vectors, batch_size=100)

        # Should be called 3 times (3 batches of 100, 100, 50)
        self.assertEqual(self.mock_index.upsert.call_count, 3)

    def test_upsert_vectors_in_batches_with_retries(self) -> None:
        """Test vector upserting with retry logic."""
        vectors = [{"id": "test-1", "values": [0.1], "metadata": {}}]

        # Mock failure followed by success
        self.mock_index.upsert.side_effect = [
            Exception("Network error"),  # First attempt fails
            Exception("Still failing"),  # Second attempt fails
            None,  # Third attempt succeeds
        ]

        # Should not raise exception after retries
        self.db._upsert_vectors_in_batches(vectors, batch_size=100)

        # Should be called 3 times due to retries
        self.assertEqual(self.mock_index.upsert.call_count, 3)

    def test_upsert_vectors_in_batches_complete_failure(self) -> None:
        """Test vector upserting with complete failure after retries."""
        vectors = [{"id": "test-1", "values": [0.1], "metadata": {}}]

        # Mock consistent failure
        self.mock_index.upsert.side_effect = Exception("Persistent error")

        # Should not raise exception but log errors
        self.db._upsert_vectors_in_batches(vectors, batch_size=100)

        # Should be called 3 times (max retries)
        self.assertEqual(self.mock_index.upsert.call_count, 3)

    @patch("nyc_landmarks.vectordb.pinecone_db.EnhancedMetadataCollector")
    def test_store_chunks_basic(self, mock_collector_class: Mock) -> None:
        """Test basic chunk storage functionality."""
        # Mock enhanced metadata collector
        mock_collector = Mock()
        mock_collector_class.return_value = mock_collector
        mock_metadata = Mock()
        mock_metadata.model_dump.return_value = {"landmark_name": "Test Landmark"}
        mock_collector.collect_landmark_metadata.return_value = mock_metadata

        # Test data
        chunks = [
            {
                "text": "Test chunk 1",
                "embedding": [0.1, 0.2, 0.3],
                "metadata": {"source_type": "wikipedia"},
            },
            {
                "text": "Test chunk 2",
                "embedding": [0.4, 0.5, 0.6],
                "metadata": {"source_type": "wikipedia"},
            },
        ]

        # Mock successful upsert
        self.mock_index.upsert.return_value = None

        result = self.db.store_chunks(
            chunks=chunks,
            landmark_id="landmark123",
            id_prefix="test-",
            use_fixed_ids=True,
        )

        # Should return list of vector IDs
        self.assertEqual(len(result), 2)
        self.assertTrue(all(id.startswith("test-landmark123-chunk-") for id in result))

        # Should call upsert
        self.mock_index.upsert.assert_called()

    def test_store_chunks_empty_list(self) -> None:
        """Test storing empty chunk list."""
        result = self.db.store_chunks(chunks=[])
        self.assertEqual(result, [])
        self.mock_index.upsert.assert_not_called()

    @patch("nyc_landmarks.vectordb.pinecone_db.EnhancedMetadataCollector")
    def test_store_chunks_with_delete_existing(
        self, mock_collector_class: Mock
    ) -> None:
        """Test chunk storage with deletion of existing vectors."""
        # Mock enhanced metadata collector
        mock_collector = Mock()
        mock_collector_class.return_value = mock_collector
        mock_collector.collect_landmark_metadata.return_value = None

        chunks = [
            {
                "text": "Test chunk",
                "embedding": [0.1, 0.2, 0.3],
            }
        ]

        # Mock successful operations
        self.mock_index.delete.return_value = None
        self.mock_index.upsert.return_value = None

        result = self.db.store_chunks(
            chunks=chunks, landmark_id="landmark123", delete_existing=True
        )

        # Should call delete before upsert
        self.mock_index.delete.assert_called_once()
        self.mock_index.upsert.assert_called_once()
        self.assertEqual(len(result), 1)

    def test_delete_vectors_success(self) -> None:
        """Test successful vector deletion."""
        vector_ids = [f"test-{i}" for i in range(250)]  # Test batching

        self.mock_index.delete.return_value = None

        deleted_count = self.db.delete_vectors(vector_ids)

        self.assertEqual(deleted_count, 250)
        # Should be called 3 times due to batching (100, 100, 50)
        self.assertEqual(self.mock_index.delete.call_count, 3)

    def test_delete_vectors_empty_list(self) -> None:
        """Test deletion with empty vector list."""
        result = self.db.delete_vectors([])
        self.assertEqual(result, 0)
        self.mock_index.delete.assert_not_called()

    def test_delete_vectors_by_filter_success(self) -> None:
        """Test successful deletion by filter."""
        filter_dict = {"landmark_id": "landmark123"}

        self.mock_index.delete.return_value = None

        result = self.db.delete_vectors_by_filter(filter_dict)

        self.assertEqual(result, 1)  # Returns 1 as approximate count
        self.mock_index.delete.assert_called_once_with(filter=filter_dict)

    def test_delete_vectors_by_filter_failure(self) -> None:
        """Test deletion by filter with failure."""
        filter_dict = {"landmark_id": "landmark123"}

        self.mock_index.delete.side_effect = Exception("Delete failed")

        result = self.db.delete_vectors_by_filter(filter_dict)

        self.assertEqual(result, 0)
        self.mock_index.delete.assert_called_once()


class TestPineconeDBIndexOperations(unittest.TestCase):
    """Test index management operations."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        with patch("nyc_landmarks.vectordb.pinecone_db.Pinecone") as mock_pinecone:
            self.mock_pc = Mock()
            mock_pinecone.return_value = self.mock_pc
            self.mock_index = Mock()
            self.mock_pc.Index.return_value = self.mock_index
            self.db = PineconeDB(index_name="test-index")

    def test_get_index_stats_success(self) -> None:
        """Test successful index stats retrieval."""
        # Mock stats object
        mock_stats = Mock()
        mock_stats.namespaces = {"default": {"vector_count": 100}}
        mock_stats.dimension = 1536
        mock_stats.index_fullness = 0.5
        mock_stats.total_vector_count = 100

        self.mock_index.describe_index_stats.return_value = mock_stats

        result = self.db.get_index_stats()

        expected = {
            "namespaces": {"default": {"vector_count": 100}},
            "dimension": 1536,
            "index_fullness": 0.5,
            "total_vector_count": 100,
        }
        self.assertEqual(result, expected)

    def test_get_index_stats_failure(self) -> None:
        """Test index stats retrieval failure."""
        self.mock_index.describe_index_stats.side_effect = Exception("Stats failed")

        result = self.db.get_index_stats()

        self.assertEqual(result, {})

    def test_list_indexes_success(self) -> None:
        """Test successful index listing."""
        # Mock indexes response with proper name attributes
        mock_index1 = Mock()
        mock_index1.name = "index1"
        mock_index2 = Mock()
        mock_index2.name = "index2"
        mock_indexes = [mock_index1, mock_index2]
        self.mock_pc.list_indexes.return_value = mock_indexes

        result = self.db.list_indexes()

        self.assertEqual(result, ["index1", "index2"])

    def test_list_indexes_alternative_format(self) -> None:
        """Test index listing with alternative response format."""
        # Mock alternative response format
        mock_response = Mock()
        mock_response.names = ["index1", "index2"]
        self.mock_pc.list_indexes.return_value = mock_response

        result = self.db.list_indexes()

        self.assertEqual(result, ["index1", "index2"])

    def test_list_indexes_failure(self) -> None:
        """Test index listing failure."""
        self.mock_pc.list_indexes.side_effect = Exception("List failed")

        result = self.db.list_indexes()

        self.assertEqual(result, [])

    def test_check_index_exists_true(self) -> None:
        """Test index existence check when index exists."""
        mock_index = Mock()
        mock_index.name = "test-index"
        self.mock_pc.list_indexes.return_value = [mock_index]

        result = self.db.check_index_exists()

        self.assertTrue(result)

    def test_check_index_exists_false(self) -> None:
        """Test index existence check when index doesn't exist."""
        mock_index = Mock()
        mock_index.name = "other-index"
        self.mock_pc.list_indexes.return_value = [mock_index]

        result = self.db.check_index_exists()

        self.assertFalse(result)

    def test_check_index_exists_custom_name(self) -> None:
        """Test index existence check with custom name."""
        mock_index = Mock()
        mock_index.name = "custom-index"
        self.mock_pc.list_indexes.return_value = [mock_index]

        result = self.db.check_index_exists("custom-index")

        self.assertTrue(result)

    def test_test_connection_success(self) -> None:
        """Test successful connection test."""
        # Mock successful stats call
        mock_stats = Mock()
        mock_stats.namespaces = {}
        self.mock_index.describe_index_stats.return_value = mock_stats

        result = self.db.test_connection()

        self.assertTrue(result)

    def test_test_connection_failure(self) -> None:
        """Test connection test failure."""
        # Mock get_index_stats to return error dict instead of raising exception
        with patch.object(
            self.db, 'get_index_stats', return_value={"error": "Connection failed"}
        ):
            result = self.db.test_connection()
            self.assertFalse(result)

    @patch("nyc_landmarks.vectordb.pinecone_db.time.sleep")
    @patch("pinecone.ServerlessSpec")  # Patch from pinecone module directly
    def test_create_index_if_not_exists_new_index(
        self, mock_serverless_spec: Mock, mock_sleep: Mock
    ) -> None:
        """Test creating new index when it doesn't exist."""
        # Mock index doesn't exist initially, then exists after creation
        mock_index = Mock()
        mock_index.name = "test-index"

        # First call returns empty (doesn't exist), second call returns the index (exists)
        self.mock_pc.list_indexes.side_effect = [[], [mock_index]]

        # Mock successful creation
        self.mock_pc.create_index.return_value = None

        result = self.db.create_index_if_not_exists()

        self.assertTrue(result)
        self.mock_pc.create_index.assert_called_once()
        mock_sleep.assert_called_once_with(30)

    def test_create_index_if_not_exists_existing_index(self) -> None:
        """Test when index already exists."""
        # Mock index exists
        mock_index = Mock()
        mock_index.name = "test-index"
        self.mock_pc.list_indexes.return_value = [mock_index]

        result = self.db.create_index_if_not_exists()

        self.assertTrue(result)
        self.mock_pc.create_index.assert_not_called()


if __name__ == "__main__":
    unittest.main()
