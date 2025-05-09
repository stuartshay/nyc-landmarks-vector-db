#!/usr/bin/env python3
"""
Script to populate Pinecone with test data for running integration tests.

This script generates and uploads test vectors for specific landmark IDs
required by the test_pinecone_validation.py test suite.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from nyc_landmarks.config.settings import settings
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Set up logger
logger = get_logger("populate_pinecone_test_data")


def create_test_landmark_data() -> List[Dict[str, str]]:
    """Create test landmark metadata for sample landmarks."""

    # List of sample landmarks that are tested in test_pinecone_validation.py
    landmarks = [
        {
            "landmark_id": "LP-00001",
            "name": "Empire State Building",
            "borough": "Manhattan",
            "style": "Art Deco",
            "location": "350 Fifth Avenue",
            "designation_date": "1981-05-19",
            "type": "Individual Landmark",
            "architect": "Shreve, Lamb & Harmon",
            "description": "This is a test description for the Empire State Building. It was completed in 1931 and was the world's tallest building for nearly 40 years.",
        },
        {
            "landmark_id": "LP-00009",
            "name": "Chrysler Building",
            "borough": "Manhattan",
            "style": "Art Deco",
            "location": "405 Lexington Avenue",
            "designation_date": "1978-12-08",
            "type": "Individual Landmark",
            "architect": "William Van Alen",
            "description": "This is a test description for the Chrysler Building. It was built between 1928 and 1930 and is known for its distinctive crown.",
        },
        {
            "landmark_id": "LP-00042",
            "name": "Flatiron Building",
            "borough": "Manhattan",
            "style": "Beaux-Arts",
            "location": "175 Fifth Avenue",
            "designation_date": "1966-09-20",
            "type": "Individual Landmark",
            "architect": "Daniel Burnham",
            "description": "This is a test description for the Flatiron Building. It was completed in 1902 and is known for its triangular shape.",
        },
        {
            "landmark_id": "LP-00066",
            "name": "Woolworth Building",
            "borough": "Manhattan",
            "style": "Gothic Revival",
            "location": "233 Broadway",
            "designation_date": "1983-04-12",
            "type": "Individual Landmark",
            "architect": "Cass Gilbert",
            "description": "This is a test description for the Woolworth Building. It was completed in 1913 and was once known as the Cathedral of Commerce.",
        },
    ]

    return landmarks


def generate_test_vectors(
    landmarks_data: List[Dict[str, Any]], chunks_per_landmark: int = 3
) -> List[Dict[str, Any]]:
    """
    Generate test vectors for each landmark with proper IDs and metadata.

    Args:
        landmarks_data: List of landmark metadata dictionaries
        chunks_per_landmark: Number of chunks to generate per landmark

    Returns:
        List of vector dictionaries ready for upload
    """
    vectors = []
    dimensions = settings.PINECONE_DIMENSIONS

    for landmark in landmarks_data:
        landmark_id = landmark["landmark_id"]

        # For each landmark, create multiple chunks
        for chunk_index in range(chunks_per_landmark):
            # Generate a deterministic test vector
            # Using the landmark ID and chunk index for reproducibility
            np.random.seed(int(landmark_id.replace("LP-", "")) + chunk_index)
            vector_data = np.random.rand(dimensions).tolist()

            # Create vector ID with proper format
            vector_id = f"{landmark_id}-chunk-{chunk_index}"

            # Create metadata
            metadata = {
                **landmark,  # Include all landmark properties
                "chunk_index": chunk_index,
                "total_chunks": chunks_per_landmark,
                "source_type": "test",
                "test_data": True,
            }

            vectors.append(
                {"id": vector_id, "values": vector_data, "metadata": metadata}
            )

    return vectors


def upload_vectors(pinecone_db: PineconeDB, vectors: List[Dict[str, Any]]) -> int:
    """
    Upload vectors to Pinecone.

    Args:
        pinecone_db: PineconeDB instance
        vectors: List of vector dictionaries

    Returns:
        Number of vectors uploaded
    """
    # Batch upload vectors
    batch_size = 100
    total_uploaded = 0

    for i in range(0, len(vectors), batch_size):
        batch = vectors[i : i + batch_size]
        vector_batch = [
            {"id": v["id"], "values": v["values"], "metadata": v["metadata"]}
            for v in batch
        ]

        try:
            pinecone_db.index.upsert(vectors=vector_batch)
            total_uploaded += len(batch)
            logger.info(f"Uploaded batch {i//batch_size + 1}, {len(batch)} vectors")
        except Exception as e:
            logger.error(f"Error uploading batch {i//batch_size + 1}: {e}")

    return total_uploaded


def main() -> None:
    """Run the main script."""
    logger.info("Initializing PineconeDB client...")
    pinecone_db = PineconeDB()

    if not pinecone_db.index:
        logger.error(
            "Pinecone index not initialized. Check your API key and environment settings."
        )
        return

    # Get current stats
    stats = pinecone_db.get_index_stats()
    logger.info(f"Current index stats: {stats}")

    # Create test landmarks
    landmarks_data = create_test_landmark_data()
    logger.info(f"Created {len(landmarks_data)} test landmarks")

    # Generate test vectors
    vectors = generate_test_vectors(landmarks_data, chunks_per_landmark=3)
    logger.info(f"Generated {len(vectors)} test vectors")

    # Upload vectors
    uploaded_count = upload_vectors(pinecone_db, vectors)
    logger.info(f"Successfully uploaded {uploaded_count} vectors")

    # Verify the upload
    stats_after = pinecone_db.get_index_stats()
    logger.info(f"Updated index stats: {stats_after}")

    logger.info("Done. The Pinecone database is now populated with test data.")


if __name__ == "__main__":
    main()
