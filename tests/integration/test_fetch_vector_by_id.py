"""
Integration test for fetch_vector_by_id functionality in the PineconeDB class.

This module tests the enhanced fetch_vector_by_id method which provides robust
vector retrieval from Pinecone, including handling vectors in the "__default__"
namespace and fallback to searching all namespaces.
"""

import logging

import pytest

from nyc_landmarks.config.settings import settings
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)

# Test vectors - these should exist in the production index
TEST_VECTOR_IDS = [
    "wiki-Wyckoff_House-LP-00001-chunk-0",  # Known to exist in multiple namespaces
    "wiki-Bohemian_National_Hall-LP-01914-chunk-0",  # Known to exist in multiple namespaces
]


@pytest.mark.integration
def test_fetch_vector_by_id_no_namespace() -> None:
    """
    Test fetching vectors when no namespace is provided.

    This test verifies that:
    1. The PineconeDB.fetch_vector_by_id method can retrieve vectors without specifying a namespace
    2. The method correctly handles the default namespace case
    3. The vector metadata and values are retrieved properly
    """
    logger.info("=== Testing fetch_vector_by_id with no namespace ===")

    try:
        # Initialize PineconeDB client
        pinecone_db = PineconeDB()

        # Fetch the test vector without specifying a namespace
        for vector_id in TEST_VECTOR_IDS:
            logger.info(f"Fetching vector: {vector_id} with no namespace")
            vector_data = pinecone_db.fetch_vector_by_id(vector_id, namespace=None)

            # Verify vector was found
            assert (
                vector_data is not None
            ), f"Failed to retrieve vector {vector_id} with no namespace"

            # Verify expected fields in the vector data
            assert "id" in vector_data, "Vector data should contain 'id'"
            assert "values" in vector_data, "Vector data should contain 'values'"
            assert "metadata" in vector_data, "Vector data should contain 'metadata'"

            # Verify id matches requested id
            assert (
                vector_data["id"] == vector_id
            ), f"Expected ID {vector_id} but got {vector_data['id']}"

            # Verify values is a list of expected dimension
            assert (
                len(vector_data["values"]) == settings.PINECONE_DIMENSIONS
            ), f"Expected {settings.PINECONE_DIMENSIONS} dimensions, got {len(vector_data['values'])}"

            # Verify metadata contains expected fields for landmark vectors
            metadata = vector_data["metadata"]
            assert "landmark_id" in metadata, "Metadata should contain 'landmark_id'"
            assert "source_type" in metadata, "Metadata should contain 'source_type'"
            assert "text" in metadata, "Metadata should contain 'text'"

            logger.info(f"✓ Successfully retrieved vector {vector_id}")

    except Exception as e:
        logger.error(
            f"Error in test_fetch_vector_by_id_no_namespace: {e}", exc_info=True
        )
        raise
    finally:
        logger.info("=== Finished test_fetch_vector_by_id_no_namespace ===")


@pytest.mark.integration
def test_fetch_vector_by_id_with_specific_namespace() -> None:
    """
    Test fetching vectors with specific namespaces.

    This test verifies that:
    1. The PineconeDB.fetch_vector_by_id method can retrieve vectors from specific namespaces
    2. The method correctly handles the case when a namespace is explicitly provided
    """
    logger.info("=== Testing fetch_vector_by_id with specific namespaces ===")

    try:
        # Initialize PineconeDB client
        pinecone_db = PineconeDB()

        # Get available namespaces
        stats = pinecone_db.get_index_stats()
        namespaces = list(stats.get("namespaces", {}).keys())
        logger.info(f"Available namespaces: {', '.join(namespaces)}")

        if not namespaces:
            logger.warning("No namespaces found, skipping specific namespace test")
            return

        # Test with the first available namespace
        test_namespace = namespaces[0]
        logger.info(f"Testing with namespace: {test_namespace}")

        for vector_id in TEST_VECTOR_IDS:
            # Try to fetch from the specific namespace
            vector_data = pinecone_db.fetch_vector_by_id(
                vector_id, namespace=test_namespace
            )

            if vector_data:
                # Vector found in this namespace
                logger.info(f"✓ Vector {vector_id} found in namespace {test_namespace}")

                # Verify expected fields in the vector data
                assert "id" in vector_data, "Vector data should contain 'id'"
                assert "values" in vector_data, "Vector data should contain 'values'"
                assert (
                    "metadata" in vector_data
                ), "Vector data should contain 'metadata'"

                # Verify id matches requested id
                assert (
                    vector_data["id"] == vector_id
                ), f"Expected ID {vector_id} but got {vector_data['id']}"
            else:
                logger.info(
                    f"Vector {vector_id} not found in namespace {test_namespace} (this is OK)"
                )

    except Exception as e:
        logger.error(
            f"Error in test_fetch_vector_by_id_with_specific_namespace: {e}",
            exc_info=True,
        )
        raise
    finally:
        logger.info("=== Finished test_fetch_vector_by_id_with_specific_namespace ===")


@pytest.mark.integration
def test_fetch_vector_by_id_fallback_behavior() -> None:
    """
    Test the fallback behavior of fetch_vector_by_id.

    This test verifies that:
    1. The method tries other namespaces when a vector isn't found in the specified one
    2. The method can recover and find vectors even with incorrect namespace specifications
    """
    logger.info("=== Testing fetch_vector_by_id fallback behavior ===")

    try:
        # Initialize PineconeDB client
        pinecone_db = PineconeDB()

        # Test fetching with a non-existent namespace
        fake_namespace = "non_existent_namespace_" + str(hash(str(TEST_VECTOR_IDS)))

        for vector_id in TEST_VECTOR_IDS:
            logger.info(
                f"Fetching {vector_id} with non-existent namespace: {fake_namespace}"
            )
            vector_data = pinecone_db.fetch_vector_by_id(
                vector_id, namespace=fake_namespace
            )

            # The fallback behavior should still find the vector
            assert (
                vector_data is not None
            ), f"Failed to retrieve vector {vector_id} with fallback behavior"

            # Verify expected fields and values
            assert (
                vector_data["id"] == vector_id
            ), f"Expected ID {vector_id} but got {vector_data['id']}"
            assert len(vector_data["values"]) == settings.PINECONE_DIMENSIONS
            assert "metadata" in vector_data

            logger.info(f"✓ Successfully retrieved {vector_id} via fallback behavior")

    except Exception as e:
        logger.error(
            f"Error in test_fetch_vector_by_id_fallback_behavior: {e}", exc_info=True
        )
        raise
    finally:
        logger.info("=== Finished test_fetch_vector_by_id_fallback_behavior ===")


@pytest.mark.integration
def test_fetch_vector_by_id_default_namespace() -> None:
    """
    Test the special handling for the __default__ namespace.

    This test verifies that:
    1. The method correctly handles the __default__ namespace case
    2. Vectors can be retrieved from the default namespace despite API limitations
    """
    logger.info("=== Testing fetch_vector_by_id with __default__ namespace ===")

    try:
        # Initialize PineconeDB client
        pinecone_db = PineconeDB()

        for vector_id in TEST_VECTOR_IDS:
            logger.info(f"Fetching {vector_id} from __default__ namespace")
            vector_data = pinecone_db.fetch_vector_by_id(
                vector_id, namespace="__default__"
            )

            if vector_data is not None:
                logger.info(
                    f"✓ Successfully retrieved {vector_id} from default namespace"
                )
                assert vector_data["id"] == vector_id
                assert "values" in vector_data
                assert "metadata" in vector_data
            else:
                logger.info(
                    f"Vector {vector_id} not found in __default__ namespace (this is OK)"
                )

    except Exception as e:
        logger.error(
            f"Error in test_fetch_vector_by_id_default_namespace: {e}", exc_info=True
        )
        raise
    finally:
        logger.info("=== Finished test_fetch_vector_by_id_default_namespace ===")
