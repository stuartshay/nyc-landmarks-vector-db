"""
Integration tests for the Wikipedia article processing pipeline.

These tests validate the complete Wikipedia processing workflow from
fetching articles from the CoreDataStore API to storing vectors in Pinecone.
"""

import logging

import pytest

from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI
from nyc_landmarks.db.wikipedia_fetcher import WikipediaFetcher
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_LANDMARK_ID = "LP-00001"  # Wyckoff House (known to have Wikipedia articles)


@pytest.mark.integration
def test_end_to_end_wikipedia_pipeline():
    """Test the complete Wikipedia processing pipeline from API to vector storage."""
    # Step 1: Retrieve Wikipedia articles from CoreDataStore API
    api_client = CoreDataStoreAPI()
    articles = api_client.get_wikipedia_articles(TEST_LANDMARK_ID)
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

    # Step 4: Store vectors with test prefix to avoid affecting production data
    pinecone_db = PineconeDB()
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

    # Step 6: Clean up test vectors
    deleted_count = pinecone_db.delete_vectors(vector_ids)
    assert deleted_count == len(
        vector_ids
    ), f"Should delete all {len(vector_ids)} test vectors"
    logger.info(f"Cleaned up {deleted_count} test vectors")
