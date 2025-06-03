"""Functional tests for Wikipedia revision ID metadata storage."""

from typing import Any, Dict

import pytest

from nyc_landmarks.models.wikipedia_models import WikipediaContentModel
from nyc_landmarks.wikipedia.processor import WikipediaProcessor


class TestWikipediaRevIdMetadata:
    """Test Wikipedia revision ID metadata storage functionality."""

    @pytest.mark.functional
    def test_rev_id_added_to_chunk_metadata(self) -> None:
        """Test that revision ID is properly added to chunk metadata."""
        processor = WikipediaProcessor()

        # Create test data with revision ID
        wiki_article = WikipediaContentModel(
            lpNumber="LP-00001",
            url="https://en.wikipedia.org/wiki/Test_Article",
            title="Test Article",
            content="This is test content for the article.",
            chunks=None,
            quality=None,
            rev_id="1234567890",
        )

        current_time = "2024-01-01T00:00:00"
        test_chunk: Dict[str, Any] = {
            "text": "Test chunk content",
            "chunk_index": 0,
            "metadata": {},
            "total_chunks": 1,
        }

        # Test dict chunk enrichment
        processor._enrich_dict_chunk(test_chunk, wiki_article, current_time)

        # Verify rev_id is in article_metadata
        assert "article_metadata" in test_chunk
        article_metadata = test_chunk["article_metadata"]
        assert isinstance(article_metadata, dict)
        assert "rev_id" in article_metadata
        assert article_metadata["rev_id"] == "1234567890"

        # Verify rev_id is in direct metadata
        metadata = test_chunk["metadata"]
        assert isinstance(metadata, dict)
        assert "article_rev_id" in metadata
        assert metadata["article_rev_id"] == "1234567890"

    @pytest.mark.functional
    def test_rev_id_handled_when_missing(self) -> None:
        """Test that processing works correctly when revision ID is missing."""
        processor = WikipediaProcessor()

        # Create test data without revision ID
        wiki_article = WikipediaContentModel(
            lpNumber="LP-00001",
            url="https://en.wikipedia.org/wiki/Test_Article",
            title="Test Article",
            content="This is test content for the article.",
            chunks=None,
            quality=None,
            rev_id=None,
        )

        current_time = "2024-01-01T00:00:00"
        test_chunk: Dict[str, Any] = {
            "text": "Test chunk content",
            "chunk_index": 0,
            "metadata": {},
            "total_chunks": 1,
        }

        # Test dict chunk enrichment
        processor._enrich_dict_chunk(test_chunk, wiki_article, current_time)

        # Verify article_metadata exists but no rev_id
        assert "article_metadata" in test_chunk
        article_metadata = test_chunk["article_metadata"]
        assert isinstance(article_metadata, dict)
        assert "rev_id" not in article_metadata

        # Verify no rev_id in direct metadata
        metadata = test_chunk["metadata"]
        assert isinstance(metadata, dict)
        assert "article_rev_id" not in metadata

        # But other metadata should still be present
        assert article_metadata["title"] == "Test Article"
        assert metadata["article_title"] == "Test Article"

    @pytest.mark.functional
    def test_add_metadata_to_dict_includes_rev_id(self) -> None:
        """Test that _add_metadata_to_dict properly includes revision ID."""
        processor = WikipediaProcessor()

        wiki_article = WikipediaContentModel(
            lpNumber="LP-00001",
            url="https://en.wikipedia.org/wiki/Test_Article",
            title="Test Article",
            content="This is test content for the article.",
            chunks=None,
            quality=None,
            rev_id="1234567890",
        )

        metadata: Dict[str, Any] = {}
        current_time = "2024-01-01T00:00:00"

        processor._add_metadata_to_dict(metadata, wiki_article, current_time)

        # Verify all expected metadata fields including rev_id
        assert metadata["article_title"] == "Test Article"
        assert metadata["article_url"] == "https://en.wikipedia.org/wiki/Test_Article"
        assert metadata["processing_date"] == current_time
        assert metadata["source_type"] == "Wikipedia"
        assert metadata["article_rev_id"] == "1234567890"

    @pytest.mark.functional
    def test_add_metadata_to_dict_without_rev_id(self) -> None:
        """Test that _add_metadata_to_dict works correctly without revision ID."""
        processor = WikipediaProcessor()

        wiki_article = WikipediaContentModel(
            lpNumber="LP-00001",
            url="https://en.wikipedia.org/wiki/Test_Article",
            title="Test Article",
            content="This is test content for the article.",
            chunks=None,
            quality=None,
            rev_id=None,
        )

        metadata: Dict[str, Any] = {}
        current_time = "2024-01-01T00:00:00"

        processor._add_metadata_to_dict(metadata, wiki_article, current_time)

        # Verify expected metadata fields but no rev_id
        assert metadata["article_title"] == "Test Article"
        assert metadata["article_url"] == "https://en.wikipedia.org/wiki/Test_Article"
        assert metadata["processing_date"] == current_time
        assert metadata["source_type"] == "Wikipedia"
        assert "article_rev_id" not in metadata

    @pytest.mark.functional
    def test_full_chunk_enrichment_with_rev_id(self) -> None:
        """Test full chunk enrichment process including revision ID."""
        processor = WikipediaProcessor()

        wiki_article = WikipediaContentModel(
            lpNumber="LP-00001",
            url="https://en.wikipedia.org/wiki/Test_Article",
            title="Test Article",
            content="This is test content for the article.",
            chunks=None,
            quality=None,
            rev_id="1234567890",
        )

        current_time = "2024-01-01T00:00:00"

        # Create chunks list
        chunks_with_embeddings = [
            {
                "text": "First chunk content",
                "chunk_index": 0,
                "metadata": {},
                "total_chunks": 2,
                "embedding": [0.1, 0.2, 0.3],  # Mock embedding
            },
            {
                "text": "Second chunk content",
                "chunk_index": 1,
                "metadata": {},
                "total_chunks": 2,
                "embedding": [0.4, 0.5, 0.6],  # Mock embedding
            },
        ]

        # Test full enrichment process
        processor.enrich_chunks_with_article_metadata(
            chunks_with_embeddings, wiki_article, current_time
        )

        # Verify both chunks have rev_id in multiple locations
        for i, chunk in enumerate(chunks_with_embeddings):
            assert isinstance(chunk, dict), f"Chunk {i} should be a dictionary"

            # Check article_metadata
            assert "article_metadata" in chunk
            article_metadata = chunk["article_metadata"]
            assert isinstance(article_metadata, dict)
            assert "rev_id" in article_metadata
            assert article_metadata["rev_id"] == "1234567890"

            # Check direct metadata
            assert "metadata" in chunk
            metadata = chunk["metadata"]
            assert isinstance(metadata, dict)
            assert "article_rev_id" in metadata
            assert metadata["article_rev_id"] == "1234567890"

            # Verify other required fields still present
            assert article_metadata["title"] == "Test Article"
            assert metadata["article_title"] == "Test Article"
            assert chunk["processing_date"] == current_time
