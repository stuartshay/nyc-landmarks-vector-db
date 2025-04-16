#!/usr/bin/env python3
"""
Integration test for Pinecone Vector Database validation.

This test performs a complete validation of Pinecone functionality:
1. Connects to the configured Pinecone index
2. Gets index statistics
3. Stores a test vector
4. Retrieves the test vector
5. Cleans up test data
"""

import logging
import time
import uuid
import pytest

from nyc_landmarks.config.settings import settings
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging for tests
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


@pytest.mark.integration
def test_pinecone_full_validation():
    """
    Performs a comprehensive validation test of the Pinecone vector database:
    - Connection
    - Statistics retrieval
    - Vector creation, storage, retrieval and deletion
    """
    logger.info("=== Starting Pinecone Full Validation Test ===")

    try:
        # Step 1: Initialize PineconeDB
        logger.info("Initializing PineconeDB client...")
        pinecone_db = PineconeDB()

        # Verify connection was successful
        assert pinecone_db.index is not None, "Failed to initialize PineconeDB - index is None"
        logger.info(f"Successfully connected to index: {pinecone_db.index_name}")

        # Step 2: Get index statistics
        logger.info("Getting index statistics...")
        stats = pinecone_db.get_index_stats()
        logger.info(f"Index stats: {stats}")

        # Verify stats are returned properly
        assert isinstance(stats, dict), "Expected stats to be a dictionary"
        assert "error" not in stats, f"Error in index stats: {stats.get('error')}"

        total_vectors = stats.get("total_vector_count", 0)
        logger.info(f"Current vector count: {total_vectors}")

        # Step 3: Create a test vector
        test_id = f"validation-test-{uuid.uuid4()}"
        logger.info(f"Test vector ID: {test_id}")

        logger.info("Creating test embedding...")
        embedding_generator = EmbeddingGenerator()
        test_text = "This is a test vector for the NYC Landmarks project validation."
        test_embedding = embedding_generator.generate_embedding(test_text)

        assert len(test_embedding) > 0, "Generated embedding has no values"
        logger.info(f"Generated embedding with dimension: {len(test_embedding)}")

        # Step 4: Store the test vector
        logger.info(f"Storing test vector with ID: {test_id}")
        test_chunk = {
            "text": test_text,
            "chunk_index": 0,
            "total_chunks": 1,
            "embedding": test_embedding,
            "metadata": {
                "landmark_id": "VALIDATION-TEST",
                "chunk_index": 0,
                "total_chunks": 1,
                "source_type": "validation",
                "processing_date": time.strftime("%Y-%m-%d"),
            },
        }

        vector_ids = pinecone_db.store_chunks(
            chunks=[test_chunk], id_prefix=test_id, landmark_id="VALIDATION-TEST"
        )

        assert vector_ids, "Failed to store test vector - no vector IDs returned"
        logger.info(f"Successfully stored vector with ID: {vector_ids[0]}")

        # Step 5: Query for the test vector
        # Wait briefly to ensure the index is updated
        logger.info("Waiting 2 seconds for index to update...")
        time.sleep(2)

        logger.info("Querying for the test vector...")
        matches = pinecone_db.query_vectors(
            query_vector=test_embedding,
            top_k=5,
            filter_dict={"landmark_id": "VALIDATION-TEST"},
        )

        assert matches, "No matches found for test vector"
        logger.info(f"Found {len(matches)} matches")        # Verify the first match
        assert len(matches) > 0, "No matches found in results list"
        match = matches[0]
        logger.info(f"Top match ID: {match.get('id')}")
        logger.info(f"Top match score: {match.get('score')}")
        logger.info(f"Top match metadata: {match.get('metadata')}")

        # Verify it's our test vector (high similarity score)
        assert match.get('score', 0) > 0.9, f"Match score too low: {match.get('score')}"
        # Check for VALIDATION-TEST in metadata instead of ID
        assert match.get('metadata', {}).get('landmark_id') == "VALIDATION-TEST", "Test vector landmark_id not found in results metadata"
        # Also check that the test ID prefix is in the match ID
        assert test_id in match.get('id', ''), "Test ID prefix not found in results"

        # Step 6: Clean up test vector
        logger.info("Cleaning up test vector...")
        if vector_ids:
            success = pinecone_db.delete_vectors(vector_ids)
            assert success, "Failed to clean up test vectors"
            logger.info("Successfully cleaned up test vectors")

        logger.info("=== Pinecone Full Validation Test Completed Successfully ===")

    except Exception as e:
        logger.exception(f"An exception occurred during Pinecone validation: {e}", exc_info=True)
        pytest.fail(f"Test failed due to exception: {e}")
