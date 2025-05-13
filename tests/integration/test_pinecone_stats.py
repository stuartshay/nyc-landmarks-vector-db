"""
Pinecone Vector Database Integration Tests

This module contains integration tests for validating the connection and functionality
of the Pinecone vector database integration within the NYC Landmarks Vector DB project.
These tests verify that:

1. We can successfully connect to the configured Pinecone index
2. We can retrieve index statistics properly (dimensions, namespaces, vector counts)
3. We can execute vector queries against the index and receive properly formatted results

These tests are marked with the 'integration' marker and require a valid Pinecone API key
and an existing index to be configured in the application settings. They serve as validation
that the vector database component is functioning correctly in the pipeline.

Key functionality tested:
- Pinecone connection and authentication
- Index stats retrieval
- Vector query execution and result processing

Notes:
- These tests interact with the actual Pinecone service and may incur usage costs
- They verify the structure and format of responses but don't validate specific content
- These tests are meant to validate the NYC Landmarks data stored in the vector index
"""

import logging

import numpy as np
import pytest

from nyc_landmarks.config.settings import settings
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging for tests
# This ensures that test output provides sufficient detail for debugging Pinecone interactions
logger = logging.getLogger(__name__)
logger.setLevel(settings.LOG_LEVEL.value)
logging.basicConfig(
    level=settings.LOG_LEVEL.value,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@pytest.mark.integration
def test_get_pinecone_stats() -> None:
    """
    Tests the connection to Pinecone and retrieval of index stats.

    This test validates that:
    1. We can initialize a PineconeDB client with credentials from settings
    2. The client can connect to the configured NYC Landmarks index
    3. We can successfully retrieve index statistics via the get_index_stats method
    4. The returned stats include expected keys like 'dimension' and 'namespaces'

    This test is critical for validating that the vector database is properly
    configured and accessible for landmark data storage and retrieval.
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
def test_vector_query() -> None:
    """
    Tests the functionality of querying vectors from Pinecone.

    This test validates that:
    1. We can generate a random vector with the correct dimensions for the NYC Landmarks index
    2. We can execute a vector similarity search against the index
    3. The query results are properly structured with expected fields (id, score)
    4. Any metadata associated with the vectors is retrievable and formatted correctly

    This test ensures that the semantic search functionality of the landmark vector database
    is working correctly, which is fundamental to the application's ability to find
    landmarks based on semantic similarity.
    """
    logger.info("--- Starting test_vector_query ---")

    try:
        # Initialize the PineconeDB client
        logger.info("Initializing PineconeDB client...")
        pinecone_db = PineconeDB()

        # Check if initialization was successful
        assert (
            pinecone_db.index is not None
        ), "PineconeDB index object was not initialized."

        # Generate a random query vector with the right dimensions
        # We use numpy to generate a random vector matching the NYC Landmarks index dimensions
        # This simulates a vector that might be generated from landmark text or descriptions
        logger.info(
            f"Generating random query vector with {pinecone_db.dimensions} dimensions..."
        )
        random_vector = np.random.rand(pinecone_db.dimensions).tolist()

        # Query for similar vectors
        # This simulates searching for landmarks with similar characteristics
        # We request top_k=5 to retrieve the 5 most similar landmark vectors
        logger.info("Executing vector query...")
        results = pinecone_db.query_vectors(query_vector=random_vector, top_k=5)
        logger.info(f"Query returned {len(results)} results")

        # Assert that results are returned as a list
        assert isinstance(
            results, list
        ), f"Expected query results to be a list, but got {type(results)}"

        # If there are results, validate their structure
        # For NYC Landmarks, results should contain landmark IDs and similarity scores
        # as well as metadata about the landmarks (name, location, etc.)
        if results:
            sample = results[0]
            logger.info(f"Validating sample result: {sample}")
            assert "id" in sample, "Result missing 'id' field"
            assert "score" in sample, "Result missing 'score' field"
            assert isinstance(
                sample.get("score"), float
            ), f"Expected score to be float, got {type(sample.get('score'))}"

            # Check if metadata exists and is a dictionary
            # Metadata is critical as it contains the actual landmark information
            # (name, borough, designation date, architectural style, etc.)
            if "metadata" in sample:
                assert isinstance(
                    sample["metadata"], dict
                ), f"Expected metadata to be dict, got {type(sample.get('metadata'))}"

        logger.info("Vector query test completed successfully.")

    except Exception as e:
        logger.exception(
            f"An exception occurred during test_vector_query: {e}", exc_info=True
        )
        pytest.fail(f"Test failed due to exception: {e}")
    finally:
        logger.info("--- Finished test_vector_query ---")
