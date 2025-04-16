"""
Simplified functional tests for Pinecone vector storage functionality.

This module provides tests to verify:
1. Vector database connection
2. Vector storage capability 
3. Vector retrieval capability
"""

import logging
import time
import pytest
import os
from typing import List, Dict, Any

from nyc_landmarks.config.settings import settings
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


@pytest.mark.integration
def test_pinecone_connection():
    """Test basic Pinecone connection and index stats."""
    logger.info("=== Testing Pinecone connection ===")
    
    # Create Pinecone client
    pinecone_db = PineconeDB()
    
    # Verify index connection
    assert pinecone_db.index is not None, "Failed to connect to Pinecone index"
    
    # Get index stats
    stats = pinecone_db.get_index_stats()
    assert isinstance(stats, dict), "Failed to retrieve index stats"
    assert "error" not in stats, f"Error in stats: {stats.get('error')}"
    
    # Log useful information
    logger.info(f"Connected to Pinecone index: {pinecone_db.index_name}")
    logger.info(f"Current vector count: {stats.get('total_vector_count', 0)}")
    logger.info(f"Dimension: {stats.get('dimension', 0)}")
    logger.info(f"Namespaces: {stats.get('namespaces', {})}")
    
    logger.info("=== Pinecone connection test passed ===")


@pytest.mark.integration
def test_vector_storage_and_retrieval():
    """Test vector storage and retrieval capabilities."""
    logger.info("=== Testing vector storage and retrieval ===")
    
    # Create Pinecone client
    pinecone_db = PineconeDB()
    
    # Create sample text chunk with embedding
    test_id = f"test-{int(time.time())}"
    sample_chunk = {
        "text": "This is a test chunk for the NYC Landmarks project.",
        "chunk_index": 0,
        "total_chunks": 1,
        "embedding": [0.1] * settings.PINECONE_DIMENSIONS,  # Create a simple test vector
        "metadata": {
            "landmark_id": "TEST-LANDMARK",
            "chunk_index": 0,
            "total_chunks": 1,
            "source_type": "test",
            "processing_date": time.strftime("%Y-%m-%d"),
        }
    }
    
    # Store the vector
    logger.info(f"Storing test vector with ID prefix: {test_id}")
    vector_ids = pinecone_db.store_chunks(
        chunks=[sample_chunk],
        id_prefix=test_id,
        landmark_id="TEST-LANDMARK"
    )
    
    assert vector_ids, "Failed to store vector in Pinecone"
    logger.info(f"Successfully stored vector with ID: {vector_ids[0]}")
    
    # Let Pinecone update its index (sometimes there's a delay)
    time.sleep(2)
    
    # Try to retrieve the vector
    logger.info("Querying for the stored vector")
    matches = pinecone_db.query_vectors(
        query_vector=sample_chunk["embedding"],
        top_k=5,
        filter_dict={"landmark_id": "TEST-LANDMARK"}
    )
    
    assert matches, "Failed to retrieve vectors from Pinecone"
    logger.info(f"Successfully retrieved {len(matches)} matches")
    
    # Verify if our result is in the matches
    found = False
    for match in matches:
        if match.get('metadata', {}).get('landmark_id') == "TEST-LANDMARK":
            found = True
            logger.info(f"Found our test vector with score: {match.get('score', 0)}")
            break
    
    assert found, "Our test vector was not found in the query results"
    
    # Clean up (optional)
    # Comment out if you want to keep the test vectors for inspection
    if vector_ids:
        logger.info(f"Cleaning up {len(vector_ids)} test vectors")
        pinecone_db.delete_vectors(vector_ids)
    
    logger.info("=== Vector storage and retrieval test passed ===")
