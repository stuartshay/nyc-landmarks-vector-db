#!/usr/bin/env python3
"""
Validate Pinecone Vector Database Functionality

This script performs basic validation of the Pinecone vector database setup:
1. Connects to the configured Pinecone index
2. Gets index statistics
3. Stores a test vector
4. Retrieves the test vector
5. Cleans up

Usage:
    python validate_pinecone.py
"""

import logging
import sys
import time
import uuid
from pathlib import Path

# Add the project root to the path so we can import nyc_landmarks modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from nyc_landmarks.config.settings import settings
from nyc_landmarks.vectordb.pinecone_db import PineconeDB
from nyc_landmarks.embeddings.generator import EmbeddingGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pinecone-validation")


def validate_pinecone():
    """Run validation tests for Pinecone."""
    logger.info("=== Validating Pinecone Vector Database ===")

    # Step 1: Initialize PineconeDB
    logger.info("Initializing PineconeDB client...")
    try:
        pinecone_db = PineconeDB()
        if pinecone_db.index is None:
            logger.error("Failed to initialize PineconeDB - index is None")
            return False
        logger.info(f"Successfully connected to index: {pinecone_db.index_name}")
    except Exception as e:
        logger.error(f"Error initializing PineconeDB: {e}")
        return False

    # Step 2: Get index statistics
    try:
        logger.info("Getting index statistics...")
        stats = pinecone_db.get_index_stats()
        logger.info(f"Index stats: {stats}")
        if "error" in stats:
            logger.error(f"Error in index stats: {stats['error']}")
            return False
        total_vectors = stats.get("total_vector_count", 0)
        logger.info(f"Current vector count: {total_vectors}")
    except Exception as e:
        logger.error(f"Error getting index statistics: {e}")
        return False

    # Step 3: Create a test vector
    test_id = f"validation-test-{uuid.uuid4()}"
    try:
        logger.info("Creating test embedding...")
        embedding_generator = EmbeddingGenerator()
        test_text = "This is a test vector for the NYC Landmarks project validation."
        test_embedding = embedding_generator.generate_embedding(test_text)
        logger.info(f"Generated embedding with dimension: {len(test_embedding)}")
    except Exception as e:
        logger.error(f"Error creating test embedding: {e}")
        return False

    # Step 4: Store the test vector
    try:
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
            }
        }

        vector_ids = pinecone_db.store_chunks(
            chunks=[test_chunk],
            id_prefix=test_id,
            landmark_id="VALIDATION-TEST"
        )

        if not vector_ids:
            logger.error("Failed to store test vector - no vector IDs returned")
            return False

        logger.info(f"Successfully stored vector with ID: {vector_ids[0]}")
    except Exception as e:
        logger.error(f"Error storing test vector: {e}")
        return False

    # Step 5: Query for the test vector
    try:
        logger.info("Waiting 2 seconds for index to update...")
        time.sleep(2)

        logger.info("Querying for the test vector...")
        matches = pinecone_db.query_vectors(
            query_vector=test_embedding,
            top_k=5,
            filter_dict={"landmark_id": "VALIDATION-TEST"}
        )

        if not matches:
            logger.error("No matches found for test vector")
            return False

        logger.info(f"Found {len(matches)} matches")

        # Print first match details
        if matches and len(matches) > 0:
            match = matches[0]
            logger.info(f"Top match ID: {match.get('id')}")
            logger.info(f"Top match score: {match.get('score')}")
            logger.info(f"Top match metadata: {match.get('metadata')}")
    except Exception as e:
        logger.error(f"Error querying for test vector: {e}")
        return False

    # Step 6: Clean up test vector
    try:
        logger.info("Cleaning up test vector...")
        if vector_ids:
            success = pinecone_db.delete_vectors(vector_ids)
            if not success:
                logger.warning("Failed to clean up test vectors")
            else:
                logger.info("Successfully cleaned up test vectors")
    except Exception as e:
        logger.error(f"Error cleaning up test vector: {e}")
        # Continue even if cleanup fails

    logger.info("=== Validation Completed Successfully ===")
    return True


if __name__ == "__main__":
    success = validate_pinecone()
    if not success:
        logger.error("Validation FAILED")
        sys.exit(1)
    else:
        logger.info("Validation PASSED")
        print("\nTo run the landmark processing script locally:")
        print("python scripts/process_landmarks.py --start-page 1 --end-page 2 --page-size 10 --recreate-index")
        sys.exit(0)
