#!/usr/bin/env python3
"""
Script to check if we can query vectors from Pinecone.
"""

import sys
from pathlib import Path

import numpy as np

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from nyc_landmarks.config.settings import settings
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Set up logger
logger = get_logger("check_pinecone")


def main() -> None:
    """Check if vectors are in Pinecone."""
    logger.info("Initializing PineconeDB client...")
    pinecone_db = PineconeDB()

    if not pinecone_db.index:
        logger.error("Pinecone index not initialized.")
        return

    # Get stats
    stats = pinecone_db.get_index_stats()
    logger.info(f"Index stats: {stats}")

    # Check if there's a namespace setting
    namespace = getattr(pinecone_db, "namespace", None)
    logger.info(f"PineconeDB namespace setting: {namespace}")

    # Try to query for specific landmark IDs
    landmark_ids = ["LP-00001", "LP-00009", "LP-00042", "LP-00066"]
    dimensions = settings.PINECONE_DIMENSIONS

    # Generate a random query vector
    query_vector = np.random.rand(dimensions).tolist()

    for landmark_id in landmark_ids:
        logger.info(f"Querying for landmark: {landmark_id}")

        # Set up filter
        filter_dict = {"landmark_id": landmark_id}

        try:
            # Query vectors
            vectors = pinecone_db.query_vectors(
                query_vector=query_vector, top_k=10, filter_dict=filter_dict
            )

            if vectors:
                logger.info(f"Found {len(vectors)} vectors for landmark {landmark_id}")
                # Print first vector ID and metadata
                first = vectors[0]
                logger.info(f"First vector ID: {first.get('id')}")
                logger.info(f"First vector metadata: {first.get('metadata')}")
            else:
                logger.warning(f"No vectors found for landmark {landmark_id}")
        except Exception as e:
            logger.error(f"Error querying for landmark {landmark_id}: {e}")

    # Try to list all vectors (if the index is small)
    try:
        logger.info("Attempting to fetch all vectors...")
        all_vectors = pinecone_db.query_vectors(
            query_vector=query_vector,
            top_k=100,  # Get up to 100 vectors
            filter_dict={},  # No filter, get all vectors
        )
        logger.info(f"Found {len(all_vectors)} total vectors")
        vector_ids = [v.get("id") for v in all_vectors]
        logger.info(f"Vector IDs: {vector_ids}")
    except Exception as e:
        logger.error(f"Error fetching all vectors: {e}")


if __name__ == "__main__":
    main()
