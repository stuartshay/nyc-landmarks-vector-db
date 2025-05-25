"""
Utilities for Pinecone testing with a dedicated test index.

This module provides functions to create, manage, and clean up a dedicated
Pinecone index for testing purposes, keeping test data separate from
production data.
"""

import sys
import time
from pathlib import Path
from typing import List, Optional

# Add the project root to the path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

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


def list_test_indexes() -> List[str]:
    """
    List all test indexes that match our prefix.

    Returns:
        List[str]: List of test index names
    """
    try:
        # Use PineconeDB to list indexes
        pinecone_db = PineconeDB()
        index_names = pinecone_db.list_indexes()

        # Filter to only include indexes with our prefix
        return [
            name for name in index_names if name.startswith(DEFAULT_TEST_INDEX_PREFIX)
        ]
    except Exception as e:
        logger.error(f"Failed to list test indexes: {e}")
        return []


def check_index_exists(index_name: str) -> bool:
    """
    Check if a Pinecone index exists.

    Args:
        index_name: Name of the index to check

    Returns:
        bool: True if index exists, False otherwise
    """
    try:
        # Use PineconeDB to check if index exists
        pinecone_db = PineconeDB()
        return pinecone_db.check_index_exists(index_name)
    except Exception as e:
        logger.error(f"Failed to check if index exists: {e}")
        return False


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
        # Use PineconeDB to create index if it doesn't exist
        pinecone_db = PineconeDB()
        success = pinecone_db.create_index_if_not_exists(
            index_name=test_index, dimensions=dims, metric="cosine"
        )

        if success and wait_for_ready:
            logger.info("Waiting for test index to initialize (10 seconds)...")
            time.sleep(10)
            # Verify readiness by creating a new PineconeDB instance connected to the test index
            try:
                test_db = PineconeDB(index_name=test_index)
                if test_db.index:
                    logger.info(f"Test index '{test_index}' is ready")
                else:
                    logger.warning(
                        f"Test index '{test_index}' may not be fully ready yet"
                    )
            except Exception as e:
                logger.warning(f"Could not verify test index readiness: {e}")

        return success

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
        # Use PineconeDB to check if index exists and delete it
        pinecone_db = PineconeDB()

        if not pinecone_db.check_index_exists(test_index):
            logger.info(f"Test index '{test_index}' does not exist, no need to delete")
            return True

        # Delete the index using a temporary PineconeDB instance
        temp_db = PineconeDB(index_name=test_index)
        success = temp_db.delete_index()

        if success:
            logger.info(f"Successfully deleted test index '{test_index}'")
        else:
            logger.error(f"Failed to delete test index '{test_index}'")

        return success

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
