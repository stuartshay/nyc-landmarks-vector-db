#!/usr/bin/env python3
"""
Script to regenerate the Pinecone index with standardized vector IDs.

This script exports all existing vectors from the current index,
standardizes their IDs according to the fixed ID format rules,
recreates the index, and then reimports the vectors with the proper IDs.
"""

import argparse
import json
import logging
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Set up logger
logger = get_logger("regenerate_pinecone_index")


def _process_vector(vector: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Process a single vector to extract ID, source type, and landmark ID.

    Args:
        vector: Vector data dictionary

    Returns:
        Tuple of (vector_id, source_type, landmark_id)
    """
    vector_id = vector.get("id", "")
    metadata = vector.get("metadata", {})

    # Extract landmark_id from metadata
    landmark_id = metadata.get("landmark_id", "unknown")

    # Determine source_type
    source_type = metadata.get("source_type", "")

    # Infer source_type if missing
    if not source_type:
        # Try to infer from ID format
        if vector_id.startswith("wiki-"):
            source_type = "wikipedia"
        else:
            source_type = "pdf"
        # Update metadata
        metadata["source_type"] = source_type
        logger.warning(f"Added missing source_type for vector {vector_id}")

    return vector_id, source_type, landmark_id


def _save_vector_files(
    vectors_by_source: Dict[str, List[Dict[str, Any]]],
    landmark_ids: Set[str],
    output_path: Path,
) -> None:
    """
    Save vectors and landmark IDs to output files.

    Args:
        vectors_by_source: Dictionary of vectors grouped by source type
        landmark_ids: Set of unique landmark IDs
        output_path: Directory to save files
    """
    # Save vectors grouped by source type
    for source_type, vectors in vectors_by_source.items():
        source_file = output_path / f"vectors_{source_type}.json"
        with open(source_file, "w") as f:
            json.dump(vectors, f)
        logger.info(f"Saved {len(vectors)} {source_type} vectors to {source_file}")

    # Save landmark IDs for reference
    landmarks_file = output_path / "landmark_ids.json"
    with open(landmarks_file, "w") as f:
        json.dump(list(landmark_ids), f)
    logger.info(f"Saved {len(landmark_ids)} landmark IDs to {landmarks_file}")


def _fetch_vector_batch(
    pinecone_db: PineconeDB, dummy_vector: List[float], batch_size: int
) -> List[Dict[str, Any]]:
    """
    Fetch a batch of vectors from the Pinecone index.

    Args:
        pinecone_db: PineconeDB instance
        dummy_vector: Vector to use for querying
        batch_size: Number of vectors to fetch

    Returns:
        List of vector dictionaries
    """
    return pinecone_db.query_vectors(
        query_vector=dummy_vector, top_k=batch_size, filter_dict=None
    )


def backup_vectors(
    pinecone_db: PineconeDB, output_dir: str, batch_size: int = 100
) -> Tuple[int, Set[str]]:
    """
    Export all vectors from the Pinecone index to a backup directory.

    Args:
        pinecone_db: PineconeDB instance
        output_dir: Directory to save the backup files
        batch_size: Number of vectors to process in each batch

    Returns:
        Tuple containing:
        - Total number of vectors exported
        - Set of unique landmark_ids found
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    # Get index stats to determine total vectors
    stats = pinecone_db.get_index_stats()
    total_vectors = stats.get("total_vector_count", 0)
    logger.info(f"Total vectors to export: {total_vectors}")

    # Use a zero vector for querying
    dummy_vector = [0.0] * pinecone_db.dimensions

    # Track progress
    exported_count = 0
    landmark_ids: Set[str] = set()
    batch_num = 0

    # Dictionary to group vectors by source_type (pdf, wikipedia)
    vectors_by_source: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    # Process vectors in batches
    while True:
        # Query for a batch of vectors
        logger.info(f"Querying batch {batch_num} (size {batch_size})")
        results = _fetch_vector_batch(pinecone_db, dummy_vector, batch_size)

        # Break if no more vectors
        if not results:
            logger.info("No more vectors to export")
            break

        # Track the IDs we've seen in this batch
        batch_ids: Set[str] = set()

        # Process each vector
        for vector in results:
            vector_id, source_type, landmark_id = _process_vector(vector)

            # Skip if no ID (shouldn't happen)
            if not vector_id:
                logger.warning("Vector missing ID, skipping")
                continue

            # Add to batch IDs
            batch_ids.add(vector_id)

            # Track unique landmark IDs
            if landmark_id != "unknown":
                landmark_ids.add(landmark_id)

            # Add to the appropriate source group
            vectors_by_source[source_type].append(vector)

            # Increment counter
            exported_count += 1

            # Log progress periodically
            if exported_count % 1000 == 0:
                logger.info(f"Exported {exported_count} vectors")

        # Delete the vectors we've processed from the index
        if batch_ids:
            pinecone_db.delete_vectors(list(batch_ids))
            logger.info(f"Deleted {len(batch_ids)} processed vectors from index")

        # Increment batch number
        batch_num += 1

    # Save output files
    _save_vector_files(vectors_by_source, landmark_ids, output_path)

    return exported_count, landmark_ids


def is_test_vector(vector_id: str, metadata: Dict[str, Any]) -> bool:
    """
    Determine if a vector is a test vector based on ID patterns or metadata.

    Args:
        vector_id: Vector ID to check
        metadata: Vector metadata

    Returns:
        True if it's a test vector, False otherwise
    """
    # Check if ID contains test patterns
    if "test" in vector_id.lower():
        return True

    # Check if landmark_id has test patterns
    landmark_id = metadata.get("landmark_id", "")
    if "test" in landmark_id.lower():
        return True

    return False


def standardize_ids(
    vectors: List[Dict[str, Any]], source_type: str
) -> List[Dict[str, Any]]:
    """
    Standardize vector IDs based on source type and metadata.

    Args:
        vectors: List of vectors to standardize
        source_type: Source type (pdf, wikipedia)

    Returns:
        List of vectors with standardized IDs
    """
    standardized_vectors: List[Dict[str, Any]] = []

    for vector in vectors:
        vector_id = vector.get("id", "")
        metadata = vector.get("metadata", {})

        # Skip if invalid data
        if not vector_id or not metadata:
            logger.warning(f"Vector {vector_id} missing ID or metadata, skipping")
            continue

        # Get key metadata fields
        landmark_id = metadata.get("landmark_id", "unknown")
        chunk_index = metadata.get("chunk_index", 0)

        # Check if this is a test vector
        if is_test_vector(vector_id, metadata):
            # Use LP-99999 format for test vectors
            test_id = "LP-99999"
            # Update metadata to reflect the new test ID convention
            metadata["landmark_id"] = test_id
            landmark_id = test_id
            metadata["is_test"] = True
            logger.info(f"Identified test vector: {vector_id} -> using {test_id}")

        # Create standardized ID based on source type
        if source_type == "wikipedia":
            article_title = metadata.get("article_title", "Unknown")
            # Clean article title for use in ID (remove spaces and special chars)
            clean_title = article_title.replace(" ", "_").replace(":", "_")
            # Format: wiki-{article_title}-{landmark_id}-chunk-{chunk_index}
            new_id = f"wiki-{clean_title}-{landmark_id}-chunk-{chunk_index}"
        else:
            # Format: {landmark_id}-chunk-{chunk_index}
            new_id = f"{landmark_id}-chunk-{chunk_index}"

        # Update the vector with the new ID
        vector["id"] = new_id

        # Add to results
        standardized_vectors.append(vector)

    return standardized_vectors


def restore_vectors(
    pinecone_db: PineconeDB, backup_dir: str, recreate_index: bool = False
) -> int:
    """
    Restore vectors from backup with standardized IDs.

    Args:
        pinecone_db: PineconeDB instance
        backup_dir: Directory containing the backup files
        recreate_index: Whether to recreate the index before restoring

    Returns:
        Total number of vectors imported
    """
    # Path to backup directory
    backup_path = Path(backup_dir)

    # Recreate index if requested
    if recreate_index:
        logger.info("Recreating Pinecone index")
        success = pinecone_db.recreate_index()
        if not success:
            logger.error("Failed to recreate index")
            return 0

        # Wait for the index to be ready
        logger.info("Waiting for index to be ready...")
        time.sleep(30)

    # Track progress
    imported_count = 0

    # Process each source type file
    for source_file in backup_path.glob("vectors_*.json"):
        source_type = source_file.stem.replace("vectors_", "")
        logger.info(f"Processing {source_type} vectors from {source_file}")

        # Load vectors
        with open(source_file, "r") as f:
            vectors = json.load(f)

        logger.info(f"Loaded {len(vectors)} {source_type} vectors")

        # Standardize IDs
        standardized_vectors = standardize_ids(vectors, source_type)
        logger.info(
            f"Standardized {len(standardized_vectors)} {source_type} vector IDs"
        )

        # Convert to format expected by store_vectors_batch
        batch_size = 100
        for batch_start in range(0, len(standardized_vectors), batch_size):
            batch = standardized_vectors[batch_start : batch_start + batch_size]

            # Prepare vectors for batch storage
            pinecone_vectors: List[Tuple[str, List[float], Dict[str, Any]]] = []
            for v in batch:
                vector_id = v.get("id", "")
                metadata = v.get("metadata", {})

                # Extract embedding from vector if available, or create a dummy
                # In a real implementation, you would need to have the actual embeddings
                # This is just a placeholder for the sample code
                try:
                    embedding = v.get("values", [0.0] * pinecone_db.dimensions)
                    # Ensure the embedding has the correct dimension
                    if len(embedding) != pinecone_db.dimensions:
                        logger.warning(
                            f"Vector {vector_id} has wrong dimension, using dummy embedding"
                        )
                        embedding = [0.0] * pinecone_db.dimensions
                except Exception as e:
                    logger.error(
                        f"Error extracting embedding for vector {vector_id}: {e}"
                    )
                    embedding = [0.0] * pinecone_db.dimensions

                pinecone_vectors.append((vector_id, embedding, metadata))

            # Store the batch
            success = pinecone_db.store_vectors_batch(pinecone_vectors)
            if success:
                imported_count += len(batch)
                logger.info(f"Imported {len(batch)} vectors, total {imported_count}")
            else:
                logger.error(f"Failed to import batch of {len(batch)} vectors")

    return imported_count


def verify_standardized_ids(pinecone_db: PineconeDB) -> Tuple[int, int, int]:
    """
    Verify that all vector IDs in the index follow the standardized format.

    Args:
        pinecone_db: PineconeDB instance

    Returns:
        Tuple containing:
        - Total vectors checked
        - Vectors with correct ID format
        - Vectors with incorrect ID format
    """
    # Get index stats
    stats = pinecone_db.get_index_stats()
    total_vectors = stats.get("total_vector_count", 0)
    logger.info(f"Total vectors to verify: {total_vectors}")

    # Use a zero vector for querying
    dummy_vector = [0.0] * pinecone_db.dimensions

    # Track results
    total_checked = 0
    correct_format = 0
    incorrect_format = 0
    test_vectors = 0

    # Process in batches
    batch_size = 100
    batch_index = 0
    while batch_index * batch_size < total_vectors:
        # Query for a batch of vectors
        results = pinecone_db.query_vectors(
            query_vector=dummy_vector, top_k=batch_size, filter_dict=None
        )

        # Break if no more vectors
        if not results:
            break

        # Check each vector ID
        for vector in results:
            vector_id = vector.get("id", "")
            metadata = vector.get("metadata", {})
            source_type = metadata.get("source_type", "unknown")
            landmark_id = metadata.get("landmark_id", "unknown")

            # Skip if no ID
            if not vector_id:
                continue

            total_checked += 1

            # Check if this is a test vector using LP-99999 format
            if landmark_id == "LP-99999" or metadata.get("is_test", False):
                test_vectors += 1
                logger.info(f"Found test vector with ID: {vector_id}")
                # Test vectors should still follow the standard format
                if (
                    source_type == "wikipedia"
                    and vector_id.startswith("wiki-")
                    and "LP-99999" in vector_id
                    and "-chunk-" in vector_id
                ) or (
                    source_type != "wikipedia"
                    and vector_id.startswith("LP-99999")
                    and "-chunk-" in vector_id
                ):
                    correct_format += 1
                else:
                    incorrect_format += 1
                    logger.warning(f"Incorrect test vector ID format: {vector_id}")
                continue

            # Check format based on source type
            is_valid_format = False
            if source_type == "wikipedia":
                # Should match: wiki-{article_title}-{landmark_id}-chunk-{chunk_index}
                if (
                    vector_id.startswith("wiki-")
                    and landmark_id in vector_id
                    and "-chunk-" in vector_id
                ):
                    is_valid_format = True
                else:
                    incorrect_format += 1
                    logger.warning(f"Incorrect Wikipedia ID format: {vector_id}")
            else:
                # Should match: {landmark_id}-chunk-{chunk_index}
                if vector_id.startswith(landmark_id) and "-chunk-" in vector_id:
                    is_valid_format = True
                else:
                    incorrect_format += 1
                    logger.warning(f"Incorrect PDF ID format: {vector_id}")

            if is_valid_format:
                correct_format += 1

    # Log summary
    logger.info(f"Total vectors checked: {total_checked}")
    logger.info(f"Vectors with correct format: {correct_format}")
    logger.info(f"Vectors with incorrect format: {incorrect_format}")
    logger.info(f"Test vectors found (LP-99999): {test_vectors}")

    return total_checked, correct_format, incorrect_format


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Regenerate Pinecone index with standardized vector IDs"
    )
    parser.add_argument(
        "--backup-dir",
        type=str,
        default="./pinecone_backup",
        help="Directory to store vector backups",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate the index (WARNING: This will delete all vectors)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify ID formats without regenerating",
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip the backup phase (use with caution)",
    )
    parser.add_argument(
        "--skip-restore",
        action="store_true",
        help="Skip the restore phase",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    # Initialize Pinecone client
    pinecone_db = PineconeDB()

    # Verify the index exists and is accessible
    if not pinecone_db.index:
        logger.error("Pinecone index not initialized")
        return

    # Verify only mode
    if args.verify_only:
        logger.info("Running in verify-only mode")
        total_checked, correct_format, incorrect_format = verify_standardized_ids(
            pinecone_db
        )
        if incorrect_format > 0:
            logger.warning(
                f"Found {incorrect_format} vectors with non-standard ID format "
                f"out of {total_checked} total vectors"
            )
        else:
            logger.info(f"All {total_checked} vectors have standardized ID format")
        return

    # Confirm destructive operation
    if not args.skip_backup and not args.skip_restore:
        logger.warning(
            "This operation will export all vectors, standardize IDs, "
            "and reimport them into the index."
        )
        confirm = input("Are you sure you want to proceed? (y/N): ")
        if confirm.lower() != "y":
            logger.info("Operation cancelled")
            return

    # Backup phase
    exported_count = 0
    landmark_ids: Set[str] = set()
    if not args.skip_backup:
        logger.info(f"Backing up vectors to {args.backup_dir}")
        exported_count, landmark_ids = backup_vectors(pinecone_db, args.backup_dir)
        logger.info(
            f"Exported {exported_count} vectors from {len(landmark_ids)} landmarks"
        )

    # Restore phase
    if not args.skip_restore:
        logger.info(f"Restoring vectors from {args.backup_dir} with standardized IDs")
        imported_count = restore_vectors(pinecone_db, args.backup_dir, args.recreate)
        logger.info(f"Imported {imported_count} vectors with standardized IDs")

    # Verify the results
    logger.info("Verifying standardized ID formats")
    total_checked, correct_format, incorrect_format = verify_standardized_ids(
        pinecone_db
    )
    if incorrect_format > 0:
        logger.warning(
            f"Found {incorrect_format} vectors with non-standard ID format "
            f"out of {total_checked} total vectors"
        )
    else:
        logger.info(f"All {total_checked} vectors have standardized ID format")


if __name__ == "__main__":
    main()
