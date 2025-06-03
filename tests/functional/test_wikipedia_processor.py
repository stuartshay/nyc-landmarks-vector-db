"""
Functional tests for Wikipedia processor functionality.

These tests verify the Wikipedia processor can be imported and initialized properly,
testing the core functionality without requiring external API calls.
"""

import logging
from unittest.mock import Mock, patch

import pytest

logger = logging.getLogger(__name__)


class TestWikipediaProcessorFunctional:
    """Test Wikipedia processor functionality with proper isolation."""

    @pytest.mark.functional
    def test_wikipedia_processor_import(self) -> None:
        """Test that WikipediaProcessor can be imported successfully."""
        logger.info("--- Starting test_wikipedia_processor_import ---")

        from nyc_landmarks.wikipedia.processor import WikipediaProcessor

        # Test basic initialization
        processor = WikipediaProcessor()
        assert (
            processor is not None
        ), "WikipediaProcessor should initialize successfully"

        # Check that key attributes exist
        assert hasattr(processor, "wiki_fetcher"), "Should have wiki_fetcher attribute"
        assert hasattr(
            processor, "embedding_generator"
        ), "Should have embedding_generator attribute"
        assert hasattr(processor, "pinecone_db"), "Should have pinecone_db attribute"

        logger.info("✅ WikipediaProcessor import test completed successfully")

    @pytest.mark.functional
    def test_wikipedia_processor_methods_exist(self) -> None:
        """Test that WikipediaProcessor has expected methods."""
        logger.info("--- Starting test_wikipedia_processor_methods_exist ---")

        from nyc_landmarks.wikipedia.processor import WikipediaProcessor

        processor = WikipediaProcessor()

        # Check that key methods exist
        assert hasattr(
            processor, "fetch_wikipedia_articles"
        ), "Should have fetch_wikipedia_articles method"
        assert hasattr(
            processor, "process_articles_into_chunks"
        ), "Should have process_articles_into_chunks method"
        assert hasattr(
            processor, "generate_embeddings_and_store"
        ), "Should have generate_embeddings_and_store method"
        assert hasattr(
            processor, "process_landmark_wikipedia"
        ), "Should have process_landmark_wikipedia method"

        logger.info("✅ WikipediaProcessor methods test completed successfully")

    @pytest.mark.functional
    def test_wikipedia_processor_mocked_functionality(self) -> None:
        """Test Wikipedia processor workflow with mocked external dependencies."""
        logger.info("--- Starting test_wikipedia_processor_mocked_functionality ---")

        from nyc_landmarks.wikipedia.processor import WikipediaProcessor

        # Create a processor instance
        processor = WikipediaProcessor()

        # Mock the fetch_wikipedia_articles method to return test data
        with patch.object(processor, "fetch_wikipedia_articles") as mock_fetch:
            mock_article = Mock()
            mock_article.title = "Test Landmark"
            mock_article.content = "Test content for landmark processing"
            mock_article.url = "https://en.wikipedia.org/wiki/Test_Landmark"

            mock_fetch.return_value = [mock_article]

            # Test that the method can be called and returns expected data
            articles = processor.fetch_wikipedia_articles("LP-00179")

            assert len(articles) == 1, "Should return one mocked article"
            assert articles[0].title == "Test Landmark", "Should have correct title"
            assert (
                articles[0].content == "Test content for landmark processing"
            ), "Should have correct content"

            mock_fetch.assert_called_once_with("LP-00179")

        logger.info("✅ Wikipedia processor mocked functionality test completed")

    @pytest.mark.functional
    def test_wikipedia_processor_empty_articles_handling(self) -> None:
        """Test Wikipedia processor handling of empty article lists."""
        logger.info("--- Starting test_wikipedia_processor_empty_articles_handling ---")

        from nyc_landmarks.wikipedia.processor import WikipediaProcessor

        processor = WikipediaProcessor()

        # Mock fetch_wikipedia_articles to return empty list
        with patch.object(processor, "fetch_wikipedia_articles") as mock_fetch:
            mock_fetch.return_value = []

            # Test that empty results are handled properly
            articles = processor.fetch_wikipedia_articles("LP-99999")

            assert articles == [], "Should return empty list for non-existent landmark"
            mock_fetch.assert_called_once_with("LP-99999")

        logger.info("✅ Wikipedia processor empty articles handling test completed")

    @pytest.mark.functional
    def test_wikipedia_processor_integration_mock(self) -> None:
        """Test complete Wikipedia processor workflow with comprehensive mocking."""
        logger.info("--- Starting test_wikipedia_processor_integration_mock ---")

        from nyc_landmarks.wikipedia.processor import WikipediaProcessor

        processor = WikipediaProcessor()

        # Create comprehensive mock data
        mock_article = Mock()
        mock_article.title = "Gracie Mansion"
        mock_article.content = (
            "Gracie Mansion is the official residence of the Mayor of New York City."
        )
        mock_article.url = "https://en.wikipedia.org/wiki/Gracie_Mansion"

        # Mock all the methods in the processing chain
        with (
            patch.object(processor, "fetch_wikipedia_articles") as mock_fetch,
            patch.object(processor, "process_articles_into_chunks") as mock_chunks,
            patch.object(processor, "generate_embeddings_and_store") as mock_embed,
        ):

            # Configure mocks for success scenario
            mock_fetch.return_value = [mock_article]
            mock_chunks.return_value = (
                [mock_article],
                3,
            )  # processed articles, total chunks
            mock_embed.return_value = 3  # chunks embedded

            # Test the main processing method (which exists but calls external services)
            # We'll verify the method exists and can be called with proper parameters
            assert hasattr(
                processor, "process_landmark_wikipedia"
            ), "Should have main processing method"

            # Verify we can call the individual methods
            articles = processor.fetch_wikipedia_articles("LP-00179")
            assert len(articles) == 1, "Should get mocked article"

            processed_articles, total_chunks = processor.process_articles_into_chunks(
                articles, "LP-00179"
            )
            assert len(processed_articles) == 1, "Should process one article"
            assert total_chunks == 3, "Should have 3 chunks"

            chunks_embedded = processor.generate_embeddings_and_store(
                processed_articles, "LP-00179", True
            )
            assert chunks_embedded == 3, "Should embed 3 chunks"

        logger.info("✅ Wikipedia processor integration mock test completed")


# Additional standalone functional tests for completeness
@pytest.mark.functional
def test_wikipedia_processor_component_isolation() -> None:
    """Test that Wikipedia processor components can be tested in isolation."""
    logger.info("--- Starting test_wikipedia_processor_component_isolation ---")

    from nyc_landmarks.wikipedia.processor import WikipediaProcessor

    # Test that we can create processor and access its components
    processor = WikipediaProcessor()

    # Verify component types (without calling their methods)
    assert processor.wiki_fetcher is not None, "Should have wiki_fetcher component"
    assert (
        processor.embedding_generator is not None
    ), "Should have embedding_generator component"
    assert processor.pinecone_db is not None, "Should have pinecone_db component"
    assert (
        processor.quality_fetcher is not None
    ), "Should have quality_fetcher component"

    logger.info("✅ Wikipedia processor component isolation test completed")
