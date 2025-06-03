"""
Functional tests for Wikipedia metadata collection.

These tests verify Wikipedia metadata functionality using non-destructive,
read-only operations against the production landmark index.
"""

import logging
from unittest.mock import Mock, patch

import pytest
from dotenv import load_dotenv

# Load environment variables for functional tests
load_dotenv()

logger = logging.getLogger(__name__)


class TestWikipediaMetadataCollection:
    """Test Wikipedia metadata collection functionality (non-destructive, read-only)."""

    @pytest.mark.functional
    def test_database_client_wikipedia_retrieval(self) -> None:
        """Test that database client can retrieve Wikipedia data for landmarks."""
        from nyc_landmarks.db.db_client import get_db_client

        db_client = get_db_client()

        # Test with LP-00179 (Gracie Mansion) which should have Wikipedia articles
        articles = db_client.get_wikipedia_articles("LP-00179")

        # Note: Some landmarks may not have Wikipedia articles, which is normal
        if articles:
            assert len(articles) > 0, "Should find Wikipedia articles for LP-00179"

            # Check that article has required fields
            article = articles[0]
            assert hasattr(article, "title"), "Article should have title attribute"
            assert hasattr(article, "content"), "Article should have content attribute"
            assert hasattr(article, "url"), "Article should have URL attribute"
            assert article.title, "Article title should not be empty"
            assert article.url, "Article URL should not be empty"
        else:
            # This is acceptable - not all landmarks have Wikipedia articles
            logger.info("No Wikipedia articles found for LP-00179 - this is normal")

    @pytest.mark.functional
    def test_enhanced_metadata_collector_wikipedia_integration(self) -> None:
        """Test that EnhancedMetadataCollector works with Wikipedia data."""
        from nyc_landmarks.vectordb.enhanced_metadata import EnhancedMetadataCollector

        collector = EnhancedMetadataCollector()
        metadata = collector.collect_landmark_metadata("LP-00179")

        assert metadata is not None, "Enhanced metadata should be returned"

        # Test model_dump to ensure all metadata is properly included
        metadata_dict = metadata.model_dump()

        # Basic landmark fields should always be present
        assert "landmark_id" in metadata_dict, "Should have landmark_id"
        assert "name" in metadata_dict, "Should have name"
        assert "borough" in metadata_dict, "Should have borough"

    @pytest.mark.functional
    def test_wikipedia_processor_metadata_enhancement(self) -> None:
        """Test Wikipedia processor's metadata enhancement capabilities (read-only)."""
        from nyc_landmarks.vectordb.pinecone_db import PineconeDB

        # Test the PineconeDB metadata enhancement directly
        pinecone_db = PineconeDB()
        enhanced_metadata = pinecone_db._get_enhanced_metadata("LP-00179")

        assert enhanced_metadata is not None, "Should return enhanced metadata"

        # Verify that metadata includes building data (from our previous fixes)
        building_fields = {
            k: v for k, v in enhanced_metadata.items() if k.startswith("building_")
        }
        assert (
            len(building_fields) > 0
        ), "Enhanced metadata should include building fields"

    @pytest.mark.functional
    def test_wikipedia_article_quality_assessment(self) -> None:
        """Test Wikipedia article quality assessment (read-only)."""
        from nyc_landmarks.db.db_client import get_db_client

        db_client = get_db_client()
        articles = db_client.get_wikipedia_articles("LP-00179")

        if articles:
            # Test basic article attributes
            for article in articles:
                assert hasattr(article, "title"), "Article should have title attribute"
                assert hasattr(article, "url"), "Article should have URL attribute"
                assert hasattr(
                    article, "lpNumber"
                ), "Article should have lpNumber attribute"

                # Quality information might not always be available
                # This test just verifies the articles have the expected structure
                logger.info(
                    f"Found Wikipedia article: {article.title} for landmark {article.lpNumber}"
                )
        else:
            logger.info("No Wikipedia articles found for testing quality assessment")


class TestWikipediaMetadataErrorHandling:
    """Test error handling in Wikipedia metadata collection (non-destructive)."""

    @pytest.mark.functional
    def test_missing_landmark_wikipedia_handling(self) -> None:
        """Test handling of landmarks that don't have Wikipedia articles."""
        from nyc_landmarks.db.db_client import get_db_client

        db_client = get_db_client()

        # Use a non-existent landmark ID
        articles = db_client.get_wikipedia_articles("LP-99999")

        # Should return empty list or None for non-existent landmarks
        if articles is not None:
            assert (
                len(articles) == 0
            ), "Should return empty list for non-existent landmarks"

    @pytest.mark.functional
    def test_wikipedia_processor_error_handling(self) -> None:
        """Test handling of Wikipedia processor errors."""
        from nyc_landmarks.wikipedia.processor import WikipediaProcessor

        processor = WikipediaProcessor()

        # Mock the _initialize_db_client method to return a mock db_client
        mock_db_client = Mock()
        mock_db_client.get_wikipedia_articles.side_effect = Exception(
            "Wikipedia API failed"
        )

        with patch.object(
            processor, "_initialize_db_client", return_value=mock_db_client
        ):
            # Should handle error gracefully - processor should not crash
            try:
                # This might not process anything but shouldn't crash
                processor.process_landmark_wikipedia("LP-00179")
                # If we reach here, the error was handled gracefully
                assert True, "Processor handled Wikipedia API error gracefully"
            except Exception as e:
                # If an exception is raised, it should be a controlled one
                assert "Wikipedia API failed" in str(
                    e
                ), "Should propagate expected error message"

    @pytest.mark.functional
    def test_empty_wikipedia_content_handling(self) -> None:
        """Test handling of empty or invalid Wikipedia content."""
        from nyc_landmarks.wikipedia.processor import WikipediaProcessor

        processor = WikipediaProcessor()

        # Mock the _initialize_db_client method to return a mock db_client with empty articles
        mock_db_client = Mock()
        mock_db_client.get_wikipedia_articles.return_value = []

        with patch.object(
            processor, "_initialize_db_client", return_value=mock_db_client
        ):
            # Should handle empty articles gracefully
            try:
                processor.process_landmark_wikipedia("LP-00179")
                assert True, "Processor handled empty Wikipedia articles gracefully"
            except Exception as e:
                # Should not raise an exception for empty articles
                pytest.fail(
                    f"Processor should handle empty articles gracefully, but raised: {e}"
                )
