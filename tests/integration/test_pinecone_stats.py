import logging

import pytest

from nyc_landmarks.config.settings import settings
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging for tests
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


@pytest.mark.integration
def test_get_pinecone_stats():
    """
    Tests the connection to Pinecone and retrieval of index stats.
    """
    logger.info("--- Starting test_get_pinecone_stats ---")

    try:
        # Initialize the PineconeDB client
        logger.info("Initializing PineconeDB client...")
        pinecone_db = PineconeDB()

        # Check if initialization was successful (index object created)
        assert (
            pinecone_db.index is not None
        ), "PineconeDB index object was not initialized."
        logger.info(
            f"PineconeDB client initialized. Index Name: {pinecone_db.index_name}, Namespace: {pinecone_db.namespace}"
        )

        # Call the get_index_stats method
        logger.info("Calling get_index_stats()...")
        stats = pinecone_db.get_index_stats()
        logger.info(f"Received stats response: {stats}")

        # Assert that the result is a dictionary
        assert isinstance(
            stats, dict
        ), f"Expected stats to be a dict, but got {type(stats)}"

        # Assert that the dictionary does not contain an 'error' key
        assert (
            "error" not in stats
        ), f"get_index_stats returned an error: {stats.get('error')}"

        # Optionally, assert that expected keys are present if successful
        assert "dimension" in stats, "Stats dictionary missing 'dimension' key."
        assert "namespaces" in stats, "Stats dictionary missing 'namespaces' key."

        logger.info("Index stats retrieved successfully and validated.")

    except Exception as e:
        logger.exception(
            f"An exception occurred during test_get_pinecone_stats: {e}", exc_info=True
        )
        pytest.fail(f"Test failed due to exception: {e}")
    finally:
        logger.info("--- Finished test_get_pinecone_stats ---")
