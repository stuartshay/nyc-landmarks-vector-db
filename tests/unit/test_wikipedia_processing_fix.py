"""
Test cases for Wikipedia processing edge cases and fixes.
"""

import unittest
from unittest.mock import Mock, patch

from nyc_landmarks.wikipedia.processor import WikipediaProcessor


class TestWikipediaProcessingFix(unittest.TestCase):
    """Test cases for the Wikipedia processing fix that handles landmarks without articles."""

    @patch("nyc_landmarks.wikipedia.processor.PineconeDB")
    @patch("nyc_landmarks.wikipedia.processor.EmbeddingGenerator")
    @patch("nyc_landmarks.wikipedia.processor.WikipediaFetcher")
    def setUp(
        self, mock_fetcher: Mock, mock_embedding: Mock, mock_pinecone: Mock
    ) -> None:
        """Set up test fixtures."""
        # Mock all external dependencies
        self.mock_fetcher = mock_fetcher.return_value
        self.mock_embedding = mock_embedding.return_value
        self.mock_pinecone = mock_pinecone.return_value

        # Create processor with mocked dependencies
        self.processor = WikipediaProcessor()

    @patch("nyc_landmarks.wikipedia.processor.PineconeDB")
    @patch("nyc_landmarks.wikipedia.processor.EmbeddingGenerator")
    @patch("nyc_landmarks.wikipedia.processor.WikipediaFetcher")
    @patch(
        "nyc_landmarks.wikipedia.processor.WikipediaProcessor.fetch_wikipedia_articles"
    )
    def test_landmark_without_articles_returns_success(
        self,
        mock_fetch: Mock,
        mock_fetcher: Mock,
        mock_embedding: Mock,
        mock_pinecone: Mock,
    ) -> None:
        """Test that landmarks without Wikipedia articles return success=True."""
        # Create processor with mocked dependencies
        processor = WikipediaProcessor()

        # Mock fetch_wikipedia_articles to return empty list (no articles found)
        mock_fetch.return_value = []

        # Process the landmark
        success, articles_processed, chunks_embedded = processor.process_landmark_wikipedia(
            "LP-12345", delete_existing=False
        )

        # Verify that no articles found is treated as success, not failure
        self.assertTrue(
            success, "Landmark without Wikipedia articles should return success=True"
        )
        self.assertEqual(articles_processed, 0, "Should have processed 0 articles")
        self.assertEqual(chunks_embedded, 0, "Should have embedded 0 chunks")

        # Verify the fetch method was called
        mock_fetch.assert_called_once_with("LP-12345")

    @patch("nyc_landmarks.wikipedia.processor.PineconeDB")
    @patch("nyc_landmarks.wikipedia.processor.EmbeddingGenerator")
    @patch("nyc_landmarks.wikipedia.processor.WikipediaFetcher")
    @patch(
        "nyc_landmarks.wikipedia.processor.WikipediaProcessor.fetch_wikipedia_articles"
    )
    @patch(
        "nyc_landmarks.wikipedia.processor.WikipediaProcessor.process_articles_into_chunks"
    )
    def test_landmark_with_articles_but_processing_fails(
        self,
        mock_process: Mock,
        mock_fetch: Mock,
        mock_fetcher: Mock,
        mock_embedding: Mock,
        mock_pinecone: Mock,
    ) -> None:
        """Test that landmarks with articles that fail to process return failure."""
        # Create processor with mocked dependencies
        processor = WikipediaProcessor()

        # Mock fetch to return articles (simulating articles found)
        mock_article = Mock()
        mock_article.title = "Test Article"
        mock_article.url = "https://en.wikipedia.org/wiki/Test"
        mock_fetch.return_value = [mock_article]

        # Mock process_articles_into_chunks to return empty (simulating processing failure)
        mock_process.return_value = ([], 0)

        # Process the landmark
        success, articles_processed, chunks_embedded = processor.process_landmark_wikipedia(
            "LP-12345", delete_existing=False
        )

        # Verify that articles found but processing failed is treated as failure
        self.assertFalse(
            success,
            "Landmark with articles that fail processing should return success=False",
        )
        self.assertEqual(
            articles_processed, 0, "Should have processed 0 articles due to failure"
        )
        self.assertEqual(
            chunks_embedded, 0, "Should have embedded 0 chunks due to failure"
        )

    @patch("nyc_landmarks.wikipedia.processor.PineconeDB")
    @patch("nyc_landmarks.wikipedia.processor.EmbeddingGenerator")
    @patch("nyc_landmarks.wikipedia.processor.WikipediaFetcher")
    @patch(
        "nyc_landmarks.wikipedia.processor.WikipediaProcessor.fetch_wikipedia_articles"
    )
    @patch(
        "nyc_landmarks.wikipedia.processor.WikipediaProcessor.process_articles_into_chunks"
    )
    @patch(
        "nyc_landmarks.wikipedia.processor.WikipediaProcessor.generate_embeddings_and_store"
    )
    def test_landmark_with_successful_processing(
        self,
        mock_store: Mock,
        mock_process: Mock,
        mock_fetch: Mock,
        mock_fetcher: Mock,
        mock_embedding: Mock,
        mock_pinecone: Mock,
    ) -> None:
        """Test that landmarks with successful processing return success=True."""
        # Create processor with mocked dependencies
        processor = WikipediaProcessor()

        # Mock successful fetch
        mock_article = Mock()
        mock_article.title = "Test Article"
        mock_article.url = "https://en.wikipedia.org/wiki/Test"
        mock_fetch.return_value = [mock_article]

        # Mock successful processing
        mock_processed_article = Mock()
        mock_process.return_value = ([mock_processed_article], 3)  # 1 article, 3 chunks

        # Mock successful storage
        mock_store.return_value = 3  # 3 chunks embedded

        # Process the landmark
        success, articles_processed, chunks_embedded = processor.process_landmark_wikipedia(
            "LP-12345", delete_existing=False
        )

        # Verify successful processing
        self.assertTrue(
            success, "Landmark with successful processing should return success=True"
        )
        self.assertEqual(articles_processed, 1, "Should have processed 1 article")
        self.assertEqual(chunks_embedded, 3, "Should have embedded 3 chunks")


if __name__ == "__main__":
    unittest.main()
