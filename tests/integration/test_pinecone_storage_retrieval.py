"""
Integration tests for Pinecone vector storage and retrieval functionality.

This module tests the complete workflow of storing vectors in Pinecone and
retrieving them through similarity search. These tests involve actual data
modification and are potentially destructive, making them integration tests
rather than functional tests.
"""

import logging
import time
from typing import List

import pytest

from nyc_landmarks.config.settings import settings
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


@pytest.mark.integration
def test_vector_storage_and_retrieval(pinecone_test_db: PineconeDB) -> None:
    """
    Test vector storage and retrieval capabilities using a real landmark ID.

    This test performs an end-to-end verification of the vector database workflow:
    1. Creates a sample text chunk with a synthetic embedding vector
    2. Adds landmark metadata with a real landmark ID (LP-00011)
    3. Stores the vector in Pinecone using store_chunks()
    4. Verifies the vector was stored successfully with a unique ID
    5. Waits for Pinecone indexing to complete (10-second delay)
    6. Queries Pinecone with the same vector to perform similarity search
    7. Verifies the query returns matching results
    8. Confirms the stored vector for LP-00011 is found in the results
    9. Cleans up by deleting the test vector from Pinecone

    Args:
        pinecone_test_db: Fixture providing a PineconeDB instance connected to a test index

    Notes:
        - Using LP-00011 as a real landmark ID helps validate the metadata handling
        - The embedding vector is synthetic ([0.1] * dimensions) for test simplicity
        - The test uses a wait period to account for Pinecone's eventual consistency
        - This is an integration test because it modifies data in Pinecone
    """
    logger.info("=== Testing vector storage and retrieval ===")

    # Use test-specific Pinecone client
    pinecone_db = pinecone_test_db

    # Create a unique test identifier using current timestamp
    # This ensures vector IDs don't conflict between test runs
    test_id = f"test-{int(time.time())}"

    # Create sample text chunk with embedding vector and metadata
    # This structure matches what would be produced by the actual chunking and embedding pipeline
    sample_chunk = {
        # The text content that would be extracted from landmark documents
        "text": "This is a test chunk for the NYC Landmarks project.",
        # Positional metadata - which chunk in sequence this is
        "chunk_index": 0,
        "total_chunks": 1,
        # The embedding vector - using a simplified synthetic vector of all 0.1 values
        # with the same dimensions as our production embeddings
        "embedding": [0.1] * settings.PINECONE_DIMENSIONS,
        # Metadata fields that are stored alongside the vector in Pinecone
        # These enable filtering and provide context for search results
        "metadata": {
            # Using a real landmark ID to properly test metadata handling
            "landmark_id": "LP-00011",
            "chunk_index": 0,
            "total_chunks": 1,
            "source_type": "test",  # In production, this would be "pdf", "wikipedia", etc.
            "processing_date": time.strftime("%Y-%m-%d"),
        },
    }

    # Store the vector in Pinecone
    # The store_chunks method will:
    # 1. Extract the embedding from each chunk
    # 2. Process and validate all metadata
    # 3. Enrich metadata with additional landmark details (from enhanced_metadata module)
    # 4. Create a vector ID using the pattern: {id_prefix}{landmark_id}-chunk-{index}
    # 5. Upsert the vector into the Pinecone index
    logger.info(f"Storing test vector with ID prefix: {test_id}")
    vector_ids = pinecone_db.store_chunks(
        chunks=[sample_chunk],  # List of text chunks with embeddings
        id_prefix=test_id,  # Prefix for the vector ID
        landmark_id="LP-00011",  # The landmark ID for metadata enrichment
    )

    # Verify we got back at least one vector ID, indicating successful storage
    assert vector_ids, "Failed to store vector in Pinecone"
    logger.info(f"Successfully stored vector with ID: {vector_ids[0]}")

    # Wait for Pinecone indexing to complete
    # Pinecone has eventual consistency, so there can be a delay between
    # storing a vector and being able to query it. We use a 10-second delay
    # to ensure the vector is fully indexed before querying.
    logger.info("Waiting for Pinecone to update its index (10 seconds)...")
    time.sleep(10)

    # Now try to retrieve the vector using similarity search
    logger.info("Querying for the stored vector")

    # Recreate the same vector that we stored for the query
    # This ensures we'll get a perfect similarity match
    # The type annotation ensures mypy validates this as List[float]
    query_vector: List[float] = [0.1] * settings.PINECONE_DIMENSIONS

    # Execute the similarity search query against Pinecone
    # This will:
    # 1. Find vectors with high cosine similarity to our query vector
    # 2. Return up to top_k matches, sorted by similarity score
    # 3. Include metadata with each matching vector
    matches = pinecone_db.query_vectors(
        query_vector=query_vector,  # The vector to search for
        top_k=10,  # Return up to 10 most similar vectors
        filter_dict={},  # No filters applied - retrieve any matching vector
    )

    # Verify we got back at least one match
    assert matches, "Failed to retrieve vectors from Pinecone"
    logger.info(f"Successfully retrieved {len(matches)} matches")

    # Verify that our specific test vector for LP-00011 is in the matches
    # We search through all returned matches and check their metadata
    found = False
    for match in matches:
        # Each match includes metadata that was stored with the vector
        # We check that the landmark_id in metadata matches what we stored
        if match.get("metadata", {}).get("landmark_id") == "LP-00011":
            found = True
            # Log the similarity score - should be very close to 1.0 (perfect match)
            # since we're querying with the exact same vector we stored
            logger.info(f"Found our test vector with score: {match.get('score', 0)}")
            break

    # Assert that we found our vector - this validates the end-to-end process worked
    assert found, "Our test vector was not found in the query results"

    # Clean up by removing the test vectors from Pinecone
    # This prevents accumulation of test data in the index
    # Note: The entire test index will be deleted by the fixture after all tests,
    # but cleaning up individual vectors is good practice to keep the index clean
    # during test execution
    if vector_ids:
        logger.info(f"Cleaning up {len(vector_ids)} test vectors")
        pinecone_db.delete_vectors(vector_ids)

    logger.info("=== Vector storage and retrieval test passed ===")
