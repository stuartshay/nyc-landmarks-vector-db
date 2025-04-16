#!/usr/bin/env python3
"""
Create Pinecone Index for NYC Landmarks

This script creates a Pinecone index with the correct settings for the NYC Landmarks Vector DB.
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import needed modules
from pinecone import Index, create_index, init, list_indexes

from nyc_landmarks.config.settings import settings
from nyc_landmarks.utils.logger import get_logger

# Configure logger
logger = get_logger(name="create_pinecone_index")


def create_nyc_landmarks_index():
    """Create the NYC Landmarks index in Pinecone."""

    # Use the API key from settings but override the environment to use AWS
    api_key = settings.PINECONE_API_KEY
    index_name = settings.PINECONE_INDEX_NAME
    dimensions = settings.PINECONE_DIMENSIONS
    metric = settings.PINECONE_METRIC

    # Environment for GCP index creation
    environment = "us-central1-gcp"  # GCP environment for index creation

    logger.info(f"Initializing Pinecone with environment: {environment}")
    init(api_key=api_key, environment=environment)

    # Check if index already exists
    indexes = list_indexes()
    if index_name in indexes:
        logger.info(f"Index '{index_name}' already exists")
        return True

    # Create index with the appropriate settings
    try:
        logger.info(f"Creating index '{index_name}' with {dimensions} dimensions")
        create_index(name=index_name, dimension=dimensions, metric=metric)

        # Wait for index to be ready
        logger.info("Waiting for index to initialize (30 seconds)...")
        time.sleep(30)

        # Connect to index to verify it works
        index = Index(index_name)
        stats = index.describe_index_stats()
        logger.info(f"Successfully connected to index. Current stats: {stats}")

        return True
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        return False


if __name__ == "__main__":
    # Update environment variables for this session
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
