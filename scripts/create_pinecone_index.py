#!/usr/bin/env python3
"""
Create Pinecone Index for NYC Landmarks

This script creates a Pinecone index with the correct settings for the NYC Landmarks Vector DB.
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from nyc_landmarks.config.settings import settings
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logger
logger = get_logger(name="create_pinecone_index")


def create_nyc_landmarks_index() -> bool:
    """Create the NYC Landmarks index in Pinecone using PineconeDB."""

    # Get settings from configuration
    index_name = settings.PINECONE_INDEX_NAME
    dimensions = settings.PINECONE_DIMENSIONS
    metric = settings.PINECONE_METRIC

    logger.info(f"Creating Pinecone index: {index_name}")

    # Use PineconeDB for index creation
    try:
        pinecone_db = PineconeDB()
        success = pinecone_db.create_index_if_not_exists(
            index_name=index_name, dimensions=dimensions, metric=metric
        )

        if success:
            # Verify connection works
            stats = pinecone_db.get_index_stats()
            logger.info(f"Index verification successful. Stats: {stats}")
            return True
        else:
            return False

    except Exception as e:
        logger.error(f"Error creating index: {e}")
        return False


if __name__ == "__main__":
    # Update environment variables for this session - although this might not be needed with new SDK
    os.environ["PINECONE_ENVIRONMENT"] = (
        "us-central1-gcp"  # Match the environment from above
    )

    # Create the index
    success = create_nyc_landmarks_index()

    if success:
        print("\nPinecone index created successfully!")
        print(
            "\nIMPORTANT: After creating this index, to use it with the main application:"
        )
        print("1. Update your .env file with: PINECONE_ENVIRONMENT=us-central1-gcp")
        print("2. The index is now ready for use with the main pipeline\n")
    else:
        print("\nFailed to create Pinecone index. Check the logs for details.")
