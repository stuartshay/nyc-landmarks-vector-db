"""
Comprehensive unit tests for WikipediaProcessor class.

This module provides extensive test coverage for the WikipediaProcessor,
testing all major functionality including initialization, article fetching,
content processing, quality assessment, and metadata enrichment.
"""

import unittest
from unittest.mock import Mock, patch

from nyc_landmarks.models.wikipedia_models import (
    WikipediaContentModel,
    WikipediaQualityModel,
)
from nyc_landmarks.wikipedia.processor import WikipediaProcessor


class BaseWikipediaProcessorTest(unittest.TestCase):
    """Base test class for WikipediaProcessor tests."""

    def setUp(self) -> None:
        """Set up common test fixtures."""
        self.mock_wiki_fetcher = Mock()
        self.mock_embedding_generator = Mock()
        self.mock_pinecone_db = Mock()
        self.mock_quality_fetcher = Mock()

        patcher_wiki_fetcher = patch(
            'nyc_landmarks.wikipedia.processor.WikipediaFetcher',
            return_value=self.mock_wiki_fetcher,
        )
        patcher_embedding_gen = patch(
            'nyc_landmarks.wikipedia.processor.EmbeddingGenerator',
            return_value=self.mock_embedding_generator,
        )
        patcher_pinecone_db = patch(
            'nyc_landmarks.wikipedia.processor.PineconeDB',
            return_value=self.mock_pinecone_db,
        )
        patcher_quality_fetcher = patch(
            'nyc_landmarks.wikipedia.processor.WikipediaQualityFetcher',
            return_value=self.mock_quality_fetcher,
        )

        self.addCleanup(patcher_wiki_fetcher.stop)
        self.addCleanup(patcher_embedding_gen.stop)
        self.addCleanup(patcher_pinecone_db.stop)
        self.addCleanup(patcher_quality_fetcher.stop)

        patcher_wiki_fetcher.start()
        patcher_embedding_gen.start()
        patcher_pinecone_db.start()
        patcher_quality_fetcher.start()

        self.processor = WikipediaProcessor()


class TestWikipediaProcessorInitialization(BaseWikipediaProcessorTest):
    """Test WikipediaProcessor initialization and basic setup."""

    def test_initialization_success(self) -> None:
        """Test successful initialization of WikipediaProcessor."""
        # Verify processor attributes are set correctly
        self.assertIsNotNone(self.processor.wiki_fetcher)
        self.assertIsNotNone(self.processor.embedding_generator)
        self.assertIsNotNone(self.processor.pinecone_db)
        self.assertIsNotNone(self.processor.quality_fetcher)
        self.assertIsNone(self.processor.db_client)  # Should be None initially

        # Verify the dependencies are the mock objects we expected
        self.assertEqual(self.processor.wiki_fetcher, self.mock_wiki_fetcher)
        self.assertEqual(
            self.processor.embedding_generator, self.mock_embedding_generator
        )
        self.assertEqual(self.processor.pinecone_db, self.mock_pinecone_db)
        self.assertEqual(self.processor.quality_fetcher, self.mock_quality_fetcher)

    @patch('nyc_landmarks.wikipedia.processor.WikipediaQualityFetcher')
    @patch('nyc_landmarks.wikipedia.processor.PineconeDB')
    @patch('nyc_landmarks.wikipedia.processor.EmbeddingGenerator')
    @patch('nyc_landmarks.wikipedia.processor.WikipediaFetcher')
    def test_initialization_with_dependency_failure(
        self,
        mock_wiki_fetcher: Mock,
        mock_embedding_gen: Mock,
        mock_pinecone_db: Mock,
        mock_quality_fetcher: Mock,
    ) -> None:
        """Test initialization handling of dependency failures."""
        # Make one dependency fail
        mock_pinecone_db.side_effect = Exception("Connection failed")

        with self.assertRaises(Exception):
            WikipediaProcessor()


class TestWikipediaProcessorDatabaseClient(BaseWikipediaProcessorTest):
    """Test database client initialization and management."""

    @patch('nyc_landmarks.db.db_client.get_db_client')
    def test_initialize_db_client_first_time(self, mock_get_db_client: Mock) -> None:
        """Test database client initialization on first access."""
        mock_client = Mock()
        mock_get_db_client.return_value = mock_client

        result = self.processor._initialize_db_client()

        mock_get_db_client.assert_called_once()
        self.assertEqual(self.processor.db_client, mock_client)
        self.assertEqual(result, mock_client)

    @patch('nyc_landmarks.db.db_client.get_db_client')
    def test_initialize_db_client_already_initialized(
        self, mock_get_db_client: Mock
    ) -> None:
        """Test database client when already initialized."""
        existing_client = Mock()
        self.processor.db_client = existing_client

        result = self.processor._initialize_db_client()

        mock_get_db_client.assert_not_called()
        self.assertEqual(result, existing_client)


class TestWikipediaProcessorArticleFetching(BaseWikipediaProcessorTest):
    """Test article fetching and content retrieval functionality."""

    def test_fetch_wikipedia_articles_success(self) -> None:
        """Test successful Wikipedia article fetching."""
        landmark_id = "LP-00179"

        # Mock database client and articles
        mock_db_client = Mock()
        mock_article1 = Mock()
        mock_article1.title = "Gracie Mansion"
        mock_article1.url = "https://en.wikipedia.org/wiki/Gracie_Mansion"
        mock_article1.content = None

        mock_article2 = Mock()
        mock_article2.title = "Test Article"
        mock_article2.url = "https://en.wikipedia.org/wiki/Test_Article"
        mock_article2.content = None

        mock_db_client.get_wikipedia_articles.return_value = [
            mock_article1,
            mock_article2,
        ]

        # Mock wiki fetcher
        self.mock_wiki_fetcher.fetch_wikipedia_content.side_effect = [
            ("Gracie Mansion content here", "123456"),
            ("Test article content here", "789012"),
        ]

        with patch.object(
            self.processor, '_initialize_db_client', return_value=mock_db_client
        ):
            articles = self.processor.fetch_wikipedia_articles(landmark_id)

        # Verify results
        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0].content, "Gracie Mansion content here")
        self.assertEqual(articles[0].rev_id, "123456")
        self.assertEqual(articles[1].content, "Test article content here")
        self.assertEqual(articles[1].rev_id, "789012")

        mock_db_client.get_wikipedia_articles.assert_called_once_with(landmark_id)

    def test_fetch_wikipedia_articles_content_failure(self) -> None:
        """Test handling of Wikipedia content fetch failures."""
        landmark_id = "LP-00180"

        # Mock database client
        mock_db_client = Mock()
        mock_article = Mock()
        mock_article.title = "Test Article"
        mock_article.url = "https://en.wikipedia.org/wiki/Test_Article"
        mock_article.content = None

        mock_db_client.get_wikipedia_articles.return_value = [mock_article]

        # Mock wiki fetcher to return None (failure)
        self.mock_wiki_fetcher.fetch_wikipedia_content.return_value = (None, None)

        with patch.object(
            self.processor, '_initialize_db_client', return_value=mock_db_client
        ):
            articles = self.processor.fetch_wikipedia_articles(landmark_id)

        # Article should still be returned but without content
        self.assertEqual(len(articles), 1)
        self.assertIsNone(articles[0].content)

    def test_fetch_wikipedia_articles_empty_database(self) -> None:
        """Test fetching when no articles exist in database."""
        landmark_id = "LP-99999"

        # Mock empty database response
        mock_db_client = Mock()
        mock_db_client.get_wikipedia_articles.return_value = []

        with patch.object(
            self.processor, '_initialize_db_client', return_value=mock_db_client
        ):
            articles = self.processor.fetch_wikipedia_articles(landmark_id)

        # Verify results
        self.assertEqual(len(articles), 0)
        mock_db_client.get_wikipedia_articles.assert_called_once_with(landmark_id)


class TestWikipediaProcessorArticleProcessing(BaseWikipediaProcessorTest):
    """Test article processing and chunking functionality."""

    def test_process_articles_into_chunks_success(self) -> None:
        """Test successful article processing into chunks."""
        landmark_id = "LP-00179"

        # Create mock articles
        mock_article1 = Mock()
        mock_article1.title = "Test Article 1"
        mock_article1.url = "https://en.wikipedia.org/wiki/Test1"
        mock_article1.content = "Test content 1"
        mock_article1.lpNumber = landmark_id
        mock_article1.rev_id = "123456"

        mock_article2 = Mock()
        mock_article2.title = "Test Article 2"
        mock_article2.url = "https://en.wikipedia.org/wiki/Test2"
        mock_article2.content = "Test content 2"
        mock_article2.lpNumber = landmark_id
        mock_article2.rev_id = "789012"

        articles = [mock_article1, mock_article2]

        # Mock the chunking method
        with patch.object(
            self.processor,
            'split_into_token_chunks',
            side_effect=[["chunk1", "chunk2"], ["chunk3"]],
        ):
            result, total_chunks = self.processor.process_articles_into_chunks(
                articles, landmark_id
            )

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(total_chunks, 3)
        self.assertIsInstance(result[0], WikipediaContentModel)
        self.assertIsInstance(result[1], WikipediaContentModel)

    def test_process_articles_with_quality_filtering(self) -> None:
        """Test processing with quality filtering enabled."""
        landmark_id = "LP-00179"

        # Create mock article with low quality
        mock_article = Mock()
        mock_article.title = "Low Quality Article"
        mock_article.url = "https://en.wikipedia.org/wiki/LowQuality"
        mock_article.content = "Short content"
        mock_article.lpNumber = landmark_id
        mock_article.rev_id = "123456"

        # Mock quality assessment returning low quality
        mock_quality = WikipediaQualityModel(
            prediction="Stub",
            probabilities={"Stub": 0.9, "Start": 0.1},
            rev_id="123456",
        )

        with (
            patch.object(
                self.processor, '_fetch_article_quality', return_value=mock_quality
            ),
            patch.object(
                self.processor, 'split_into_token_chunks', return_value=["chunk1"]
            ),
        ):

            result, total_chunks = self.processor.process_articles_into_chunks(
                [mock_article], landmark_id
            )

        # Low quality article should be skipped
        self.assertEqual(len(result), 0)
        self.assertEqual(total_chunks, 0)


class TestWikipediaProcessorQualityAssessment(BaseWikipediaProcessorTest):
    """Test Wikipedia article quality assessment functionality."""

    def test_fetch_article_quality_success(self) -> None:
        """Test successful article quality fetching."""
        rev_id = "123456"
        quality_data = {
            "prediction": "B",
            "probabilities": {"FA": 0.1, "GA": 0.2, "B": 0.6, "C": 0.1},
            "rev_id": rev_id,
        }

        # Mock the quality fetcher
        self.mock_quality_fetcher.fetch_article_quality.return_value = quality_data

        result = self.processor._fetch_article_quality(rev_id)

        # Verify the result is not None and has correct attributes
        self.assertIsNotNone(result)
        if result is not None:  # Type guard for mypy
            self.assertEqual(result.prediction, "B")
            self.assertEqual(result.probabilities, quality_data["probabilities"])
            self.assertEqual(result.rev_id, rev_id)

    def test_fetch_article_quality_with_empty_rev_id(self) -> None:
        """Test quality fetching with empty revision ID."""
        result = self.processor._fetch_article_quality("")
        self.assertIsNone(result)

    def test_fetch_article_quality_api_returns_none(self) -> None:
        """Test handling when quality API returns None."""
        rev_id = "123456"
        self.mock_quality_fetcher.fetch_article_quality.return_value = None

        result = self.processor._fetch_article_quality(rev_id)
        self.assertIsNone(result)

    def test_fetch_article_quality_with_exception(self) -> None:
        """Test handling of quality API exceptions."""
        rev_id = "123456"
        self.mock_quality_fetcher.fetch_article_quality.side_effect = Exception(
            "API Error"
        )

        result = self.processor._fetch_article_quality(rev_id)
        self.assertIsNone(result)


class TestWikipediaProcessorEmbeddingsAndStorage(BaseWikipediaProcessorTest):
    """Test embedding generation and vector storage functionality."""

    def test_generate_embeddings_and_store_success(self) -> None:
        """Test successful embedding generation and storage."""
        landmark_id = "LP-00179"

        # Create test article with proper chunks structure
        article = WikipediaContentModel(
            lpNumber=landmark_id,
            url="https://en.wikipedia.org/wiki/Test",
            title="Test Article",
            content="Test content",
            rev_id="123456",
            chunks=[{"text": "chunk1"}, {"text": "chunk2"}],
            quality=None,
        )

        # Mock embedding generation with proper metadata structure
        chunks_with_embeddings = [
            {"text": "chunk1", "embedding": [0.1, 0.2, 0.3], "metadata": {}},
            {"text": "chunk2", "embedding": [0.4, 0.5, 0.6], "metadata": {}},
        ]
        self.mock_embedding_generator.process_chunks.return_value = (
            chunks_with_embeddings
        )

        # Mock storage - return list of IDs, not just count
        self.mock_pinecone_db.store_chunks.return_value = ["id1", "id2"]

        result = self.processor.generate_embeddings_and_store(
            [article], landmark_id, delete_existing=False
        )

        # Verify calls were made
        self.mock_embedding_generator.process_chunks.assert_called_once()
        self.mock_pinecone_db.store_chunks.assert_called_once()

        # Verify result
        self.assertEqual(result, 2)

    def test_generate_embeddings_and_store_no_chunks(self) -> None:
        """Test embedding generation with articles that have no chunks."""
        landmark_id = "LP-00179"

        # Create test article without chunks
        article = WikipediaContentModel(
            lpNumber=landmark_id,
            url="https://en.wikipedia.org/wiki/Test",
            title="Test Article",
            content="Test content",
            rev_id="123456",
            chunks=[],
            quality=None,
        )

        result = self.processor.generate_embeddings_and_store(
            [article], landmark_id, delete_existing=False
        )

        # Verify no processing occurred
        self.mock_embedding_generator.process_chunks.assert_not_called()
        self.assertEqual(result, 0)

    def test_generate_embeddings_and_store_with_deletion(self) -> None:
        """Test embedding generation with existing vector deletion."""
        landmark_id = "LP-00179"

        # Create test article
        article = WikipediaContentModel(
            lpNumber=landmark_id,
            url="https://en.wikipedia.org/wiki/Test",
            title="Test Article",
            content="Test content",
            rev_id="123456",
            chunks=[{"text": "chunk1"}],
            quality=None,
        )

        # Mock embedding and storage with proper metadata structure
        self.mock_embedding_generator.process_chunks.return_value = [
            {"text": "chunk1", "embedding": [0.1, 0.2, 0.3], "metadata": {}}
        ]
        self.mock_pinecone_db.store_chunks.return_value = ["id1"]

        result = self.processor.generate_embeddings_and_store(
            [article], landmark_id, delete_existing=True
        )

        # Verify store_chunks was called with delete_existing=True
        self.mock_pinecone_db.store_chunks.assert_called_once()
        call_args = self.mock_pinecone_db.store_chunks.call_args
        self.assertTrue(call_args.kwargs.get('delete_existing', False))
        self.assertEqual(result, 1)


if __name__ == '__main__':
    unittest.main()
