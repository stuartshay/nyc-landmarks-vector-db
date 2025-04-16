import logging
import numpy as np
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


@pytest.mark.integration
def test_vector_query():
    """
    Tests the functionality of querying vectors from Pinecone.
    """
    logger.info("--- Starting test_vector_query ---")

    try:
        # Initialize the PineconeDB client
        logger.info("Initializing PineconeDB client...")
        pinecone_db = PineconeDB()

        # Check if initialization was successful
        assert pinecone_db.index is not None, "PineconeDB index object was not initialized."

        # Generate a random query vector with the right dimensions
        logger.info(f"Generating random query vector with {pinecone_db.dimensions} dimensions...")
        random_vector = np.random.rand(pinecone_db.dimensions).tolist()

        # Query for similar vectors
        logger.info("Executing vector query...")
        results = pinecone_db.query_vectors(query_vector=random_vector, top_k=5)
        logger.info(f"Query returned {len(results)} results")

        # Assert that results are returned as a list
        assert isinstance(results, list), f"Expected query results to be a list, but got {type(results)}"

        # If there are results, validate their structure
        if results:
            sample = results[0]
            logger.info(f"Validating sample result: {sample}")
            assert "id" in sample, "Result missing 'id' field"
            assert "score" in sample, "Result missing 'score' field"
            assert isinstance(sample.get("score"), float), f"Expected score to be float, got {type(sample.get('score'))}"

            # Check if metadata exists and is a dictionary
            if "metadata" in sample:
                assert isinstance(sample["metadata"], dict), f"Expected metadata to be dict, got {type(sample.get('metadata'))}"

        logger.info("Vector query test completed successfully.")

    except Exception as e:
        logger.exception(f"An exception occurred during test_vector_query: {e}", exc_info=True)
        pytest.fail(f"Test failed due to exception: {e}")
    finally:
        logger.info("--- Finished test_vector_query ---")
