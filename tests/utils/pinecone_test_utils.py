"""
Utilities for Pinecone testing with a dedicated test index.

This module provides functions to create, manage, and clean up a dedicated
Pinecone index for testing purposes, keeping test data separate from
production data.
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Optional

# Add the project root to the path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Import needed for serverless spec - with type ignore similar to production code
# Use Pinecone client for index management
from pinecone import Pinecone, ServerlessSpec

from nyc_landmarks.config.settings import settings
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logger
logger = get_logger(name="pinecone_test_utils")

# Constants
DEFAULT_TEST_INDEX_PREFIX = "nyc-landmarks-test"


def generate_session_id() -> str:
    """
    Generate a unique session identifier based on date only for easier debugging.

    Returns:
        str: A date-based session identifier (e.g., "20250524")
    """
    timestamp = time.strftime("%Y%m%d")
    return timestamp


# Generate a unique session ID when this module is imported
SESSION_ID = generate_session_id()


def get_default_test_index_name() -> str:
    """
    Get the default test index name with the current session ID.

    Returns:
        str: The default test index name for this session
    """
    return f"{DEFAULT_TEST_INDEX_PREFIX}-{SESSION_ID}"


def get_custom_test_index_name(custom_suffix: Optional[str] = None) -> str:
    """
    Get a test index name with optional custom suffix.

    Args:
        custom_suffix: Optional custom suffix to append instead of session ID

    Returns:
        str: Test index name with custom suffix or default session ID
    """
    if custom_suffix:
        return f"{DEFAULT_TEST_INDEX_PREFIX}-{custom_suffix}"
    return get_default_test_index_name()


def get_pinecone_client() -> Pinecone:
    """Get a Pinecone client instance for index management."""
    api_key = os.environ.get("PINECONE_API_KEY", settings.PINECONE_API_KEY)
    return Pinecone(api_key=api_key)


def list_test_indexes() -> List[str]:
    """
    List all test indexes that match our prefix.

    Returns:
        List[str]: List of test index names
    """
    pc = get_pinecone_client()
    indexes = pc.list_indexes()

    index_names = (
        [idx.name for idx in indexes]
        if hasattr(indexes, "__iter__")
        else getattr(indexes, "names", [])
    )

    # Filter to only include indexes with our prefix
    return [name for name in index_names if name.startswith(DEFAULT_TEST_INDEX_PREFIX)]


def check_index_exists(pc: Pinecone, index_name: str) -> bool:
    """
    Check if a Pinecone index exists.

    Args:
        pc: Pinecone client
        index_name: Name of the index to check

    Returns:
        bool: True if index exists, False otherwise
    """
    indexes = pc.list_indexes()
    index_names = (
        [idx.name for idx in indexes]
        if hasattr(indexes, "__iter__")
        else getattr(indexes, "names", [])
    )
    return index_name in index_names


def create_serverless_index(pc: Pinecone, index_name: str, dimensions: int) -> bool:
    """
    Create a serverless Pinecone index.

    Args:
        pc: Pinecone client
        index_name: Name of the index to create
        dimensions: Vector dimensions

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(
            f"Creating serverless index '{index_name}' with {dimensions} dimensions"
        )
        pc.create_index(
            name=index_name,
            dimension=dimensions,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        return True
    except Exception as e:
        logger.warning(f"Failed to create serverless index: {e}")
        return False


def create_pod_index(pc: Pinecone, index_name: str, dimensions: int) -> bool:
    """
    Create a pod-based Pinecone index as fallback.

    Args:
        pc: Pinecone client
        index_name: Name of the index to create
        dimensions: Vector dimensions

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Attempting fallback to pod-based index '{index_name}'")
        # In Pinecone v6.0+, PodSpec is available as pinecone.PodSpec
        try:
            # Using pinecone module that's already imported at the top
            import pinecone

            pod_spec = pinecone.PodSpec(environment="us-east-1-aws", pod_type="starter")  # type: ignore

            pc.create_index(  # pyright: ignore
                name=index_name,
                dimension=dimensions,
                metric="cosine",
                spec=pod_spec,
            )
        except (AttributeError, Exception):
            # Fallback - try with minimal parameters (this may fail in newer versions)
            logger.warning(
                "PodSpec not available, attempting simplified index creation"
            )
            pc.create_index(  # pyright: ignore
                name=index_name,
                dimension=dimensions,
                metric="cosine",
            )
        return True
    except Exception as e:
        logger.error(f"Fallback index creation failed: {e}")
        return False


def verify_index_ready(pc: Pinecone, index_name: str) -> None:
    """
    Verify that the index is operational.

    Args:
        pc: Pinecone client
        index_name: Name of the index to verify
    """
    try:
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        logger.info(f"Test index is ready. Stats: {stats}")
    except Exception as e:
        logger.warning(f"Could not verify test index: {e}")


def create_test_index(
    index_name: Optional[str] = None,
    dimensions: Optional[int] = None,
    wait_for_ready: bool = True,
) -> bool:
    """
    Create a dedicated Pinecone index for testing.

    Args:
        index_name: Name for the test index (defaults to nyc-landmarks-test-{session_id})
        dimensions: Vector dimensions (defaults to settings.PINECONE_DIMENSIONS)
        wait_for_ready: Whether to wait for the index to be ready

    Returns:
        bool: True if successful, False otherwise
    """
    # Use provided values or defaults
    test_index = index_name or get_default_test_index_name()
    dims = dimensions or settings.PINECONE_DIMENSIONS

    try:
        # Initialize Pinecone client
        pc = get_pinecone_client()

        # Check if index already exists
        if check_index_exists(pc, test_index):
            logger.info(f"Test index '{test_index}' already exists")
            return True

        # Try creating a serverless index first, then fall back to pod-based if needed
        success = create_serverless_index(pc, test_index, dims)
        if not success:
            success = create_pod_index(pc, test_index, dims)
            if not success:
                return False

        if wait_for_ready:
            logger.info("Waiting for test index to initialize (10 seconds)...")
            time.sleep(10)
            verify_index_ready(pc, test_index)

        return True

    except Exception as e:
        logger.error(f"Error creating test index: {e}")
        return False


def delete_test_index(index_name: Optional[str] = None) -> bool:
    """
    Delete the test Pinecone index.

    Args:
        index_name: Name of the test index to delete (defaults to the current session's index)

    Returns:
        bool: True if successful, False otherwise
    """
    test_index = index_name or get_default_test_index_name()

    try:
        pc = get_pinecone_client()

        # Check if index exists before attempting to delete
        indexes = pc.list_indexes()
        index_names = (
            [idx.name for idx in indexes]
            if hasattr(indexes, "__iter__")
            else getattr(indexes, "names", [])
        )

        if test_index not in index_names:
            logger.info(f"Test index '{test_index}' does not exist, no need to delete")
            return True

        # Delete the index
        logger.info(f"Deleting test index '{test_index}'")
        pc.delete_index(test_index)
        logger.info(f"Successfully deleted test index '{test_index}'")
        return True

    except Exception as e:
        logger.error(f"Error deleting test index: {e}")
        return False


def get_test_db(index_name: Optional[str] = None) -> PineconeDB:
    """
    Get a PineconeDB instance connected to the test index.
    Creates the test index if it doesn't exist.

    Args:
        index_name: Name of the test index (defaults to the current session's index)

    Returns:
        PineconeDB: Instance connected to the test index
    """
    test_index = index_name or get_default_test_index_name()

    # Ensure the test index exists
    create_test_index(test_index)

    # Create and return PineconeDB connected to test index
    return PineconeDB(index_name=test_index)


def cleanup_old_test_indexes(max_age_hours: int = 24) -> List[str]:
    """
    Clean up test indexes that are older than the specified age.

    Args:
        max_age_hours: Maximum age in hours before an index is considered stale

    Returns:
        List[str]: List of deleted index names
    """
    test_indexes = list_test_indexes()
    deleted_indexes: List[str] = []

    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    for index_name in test_indexes:
        # Skip the current session's index
        if index_name == get_default_test_index_name():
            continue

        # Try to parse the timestamp from the index name
        try:
            # Format is nyc-landmarks-test-YYYYMMDD-HHMMSS-random
            parts = index_name.split("-")
            if len(parts) >= 5:
                date_part = parts[3]
                time_part = parts[4]

                if len(date_part) == 8 and len(time_part) == 6:
                    # Parse YYYYMMDD-HHMMSS format
                    timestamp_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                    index_timestamp = time.mktime(
                        time.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    )

                    # Check if index is older than max_age
                    if current_time - index_timestamp > max_age_seconds:
                        logger.info(
                            f"Deleting old test index '{index_name}' (age: {(current_time - index_timestamp) / 3600:.1f} hours)"
                        )
                        if delete_test_index(index_name):
                            deleted_indexes.append(index_name)
        except Exception as e:
            logger.warning(f"Error parsing timestamp for index '{index_name}': {e}")

    return deleted_indexes
