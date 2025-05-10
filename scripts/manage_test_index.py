#!/usr/bin/env python3
"""
Manage Pinecone Test Index

This script provides commands to create, reset, or delete the Pinecone test index
used for integration testing. It helps isolate test data from production data.

Usage:
    python manage_test_index.py create    # Create the test index if it doesn't exist
    python manage_test_index.py reset     # Delete and recreate the test index
    python manage_test_index.py delete    # Delete the test index
    python manage_test_index.py status    # Check the status of the test index
"""

import argparse
import sys
import time
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from nyc_landmarks.utils.logger import get_logger
from tests.utils.pinecone_test_utils import (
    cleanup_old_test_indexes,
    create_test_index,
    delete_test_index,
    get_default_test_index_name,
    get_pinecone_client,
    list_test_indexes,
)

# Configure logger
logger = get_logger(name="manage_test_index")


def create_index() -> None:
    """Create the test index if it doesn't exist."""
    test_index_name = get_default_test_index_name()
    logger.info(f"Creating test index '{test_index_name}'...")
    success = create_test_index(wait_for_ready=True)
    if success:
        logger.info(f"✅ Test index '{test_index_name}' is ready for use")
    else:
        logger.error(f"❌ Failed to create test index '{test_index_name}'")
        sys.exit(1)


def reset_index() -> None:
    """Delete and recreate the test index."""
    test_index_name = get_default_test_index_name()
    logger.info(f"Resetting test index '{test_index_name}'...")

    # First delete the test index
    delete_success = delete_test_index()
    if not delete_success:
        logger.warning(
            f"⚠️ Failed to delete test index '{test_index_name}', attempting to create anyway"
        )

    # Wait briefly after deletion
    time.sleep(2)

    # Create the test index
    create_success = create_test_index(wait_for_ready=True)
    if create_success:
        logger.info(
            f"✅ Test index '{test_index_name}' has been reset and is ready for use"
        )
    else:
        logger.error(f"❌ Failed to recreate test index '{test_index_name}'")
        sys.exit(1)


def delete_index() -> None:
    """Delete the test index."""
    test_index_name = get_default_test_index_name()
    logger.info(f"Deleting test index '{test_index_name}'...")
    success = delete_test_index()
    if success:
        logger.info(f"✅ Test index '{test_index_name}' has been deleted")
    else:
        logger.error(f"❌ Failed to delete test index '{test_index_name}'")
        sys.exit(1)


def check_status() -> None:
    """Check the status of the test index."""
    test_index_name = get_default_test_index_name()
    logger.info(f"Checking status of test index '{test_index_name}'...")
    pc = get_pinecone_client()

    # Get list of indexes
    indexes = pc.list_indexes()
    index_names = (
        [idx.name for idx in indexes]
        if hasattr(indexes, "__iter__")
        else getattr(indexes, "names", [])
    )

    if test_index_name in index_names:
        # Index exists, get stats
        try:
            index = pc.Index(test_index_name)
            stats = index.describe_index_stats()

            # Extract and display key information
            vector_count = getattr(stats, "total_vector_count", 0)
            dimension = getattr(stats, "dimension", "unknown")
            fullness = getattr(stats, "index_fullness", 0)

            logger.info(f"✅ Test index '{test_index_name}' exists")
            logger.info(f"   - Vector count: {vector_count}")
            logger.info(f"   - Dimension: {dimension}")
            logger.info(f"   - Index fullness: {fullness}")
        except Exception as e:
            logger.warning(f"⚠️ Index exists but could not get stats: {e}")
    else:
        logger.info(f"❌ Test index '{test_index_name}' does not exist")


def list_indexes() -> None:
    """List all test indexes."""
    logger.info("Listing all test indexes...")
    test_indexes = list_test_indexes()

    if test_indexes:
        logger.info(f"Found {len(test_indexes)} test indexes:")
        for idx, name in enumerate(test_indexes, 1):
            current = (
                " (current session)" if name == get_default_test_index_name() else ""
            )
            logger.info(f"  {idx}. {name}{current}")
    else:
        logger.info("No test indexes found")


def cleanup_indexes(age_hours: int = 24) -> None:
    """Clean up old test indexes."""
    logger.info(f"Cleaning up test indexes older than {age_hours} hours...")
    deleted = cleanup_old_test_indexes(max_age_hours=age_hours)

    if deleted:
        logger.info(f"Cleaned up {len(deleted)} old test indexes:")
        for idx, name in enumerate(deleted, 1):
            logger.info(f"  {idx}. {name}")
    else:
        logger.info("No old test indexes to clean up")


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Manage the Pinecone test index for integration testing"
    )
    parser.add_argument(
        "action",
        choices=["create", "reset", "delete", "status", "list", "cleanup"],
        help="Action to perform on the test index",
    )
    parser.add_argument(
        "--age",
        type=int,
        default=24,
        help="Maximum age in hours for cleanup action (default: 24)",
    )

    args = parser.parse_args()

    # Execute the requested action
    if args.action == "create":
        create_index()
    elif args.action == "reset":
        reset_index()
    elif args.action == "delete":
        delete_index()
    elif args.action == "status":
        check_status()
    elif args.action == "list":
        list_indexes()
    elif args.action == "cleanup":
        cleanup_indexes(args.age)


if __name__ == "__main__":
    main()
