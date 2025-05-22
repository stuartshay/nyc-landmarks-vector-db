"""
Integration tests for the Wikipedia article processing pipeline.

These tests validate the complete Wikipedia processing workflow from
fetching articles from the CoreDataStore API to storing vectors in Pinecone.
"""

import logging
import os
from typing import Optional

import pytest

from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TEST_LANDMARK_ID = "LP-00001"  # Wyckoff House (known to have Wikipedia articles)


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Skipping Wikipedia integration test in CI environment",
)
def test_end_to_end_wikipedia_pipeline(pinecone_test_db: Optional[PineconeDB]) -> None:
    """Test the complete Wikipedia processing pipeline from API to vector storage."""
    # Skip imports when in CI to prevent module import errors
    if os.environ.get("CI") == "true":
        pytest.skip("Skipping Wikipedia integration test in CI environment")
        return

    # Only import dependencies when actually running the test
    from nyc_landmarks.db.db_client import get_db_client
    from nyc_landmarks.db.wikipedia_fetcher import WikipediaFetcher
    from nyc_landmarks.embeddings.generator import EmbeddingGenerator

    # Step 1: Retrieve Wikipedia articles from CoreDataStore API
    db_client = get_db_client()
    articles = db_client.get_wikipedia_articles(TEST_LANDMARK_ID)
    assert (
        articles
    ), f"Should retrieve at least one Wikipedia article for {TEST_LANDMARK_ID}"

    # Log the articles found
    logger.info(f"Found {len(articles)} Wikipedia articles for {TEST_LANDMARK_ID}")
    for article in articles:
        logger.info(f"Article: {article.title}, URL: {article.url}")

    # Step 2: Process an article with the Wikipedia fetcher
    fetcher = WikipediaFetcher()
    article = articles[0]  # Process the first article

    content_model = fetcher.process_wikipedia_article(article)
    assert content_model, f"Should process article '{article.title}' successfully"
    assert content_model.chunks, "Should generate chunks from article content"

    # Log chunk information
    logger.info(
        f"Generated {len(content_model.chunks)} chunks from article '{article.title}'"
    )

    # Step 3: Generate embeddings for the chunks
    embedding_generator = EmbeddingGenerator()
    chunks_with_embeddings = embedding_generator.process_chunks(content_model.chunks)
    assert chunks_with_embeddings, "Should generate embeddings for chunks"

    # Log embedding information
    logger.info(f"Generated embeddings for {len(chunks_with_embeddings)} chunks")

    # Step 4: Store vectors with test prefix
    pinecone_db = pinecone_test_db
    if not pinecone_db or not pinecone_db.index:
        pytest.skip("No Pinecone index available")
        return

    test_id_prefix = f"test-wiki-{article.title.replace(' ', '_')}-{TEST_LANDMARK_ID}-"

    vector_ids = pinecone_db.store_chunks(
        chunks=chunks_with_embeddings,
        id_prefix=test_id_prefix,
        landmark_id=TEST_LANDMARK_ID,
        use_fixed_ids=True,
        delete_existing=True,
    )

    assert vector_ids, "Should store vectors successfully"
    logger.info(f"Stored {len(vector_ids)} vectors with prefix '{test_id_prefix}'")

    # Step 5: Query to verify storage
    test_query = "historical building in Brooklyn"
    test_embedding = embedding_generator.generate_embedding(test_query)

    results = pinecone_db.query_vectors(
        query_vector=test_embedding,
        top_k=5,
        filter_dict={"landmark_id": TEST_LANDMARK_ID, "source_type": "wikipedia"},
    )

    assert results, "Should retrieve vectors with Wikipedia source_type"
    logger.info(f"Retrieved {len(results)} Wikipedia vectors for query '{test_query}'")
