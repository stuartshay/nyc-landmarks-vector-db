#!/usr/bin/env python3
"""
Script to update existing vectors with building metadata.

This script:
1. Retrieves existing vectors from Pinecone
2. For each vector, collects enhanced metadata including building data
3. Updates the vector metadata in Pinecone with the building information
"""

import argparse
import logging
import sys
from typing import Dict, List, Optional

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.enhanced_metadata import get_metadata_collector
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)


def update_vector_with_building_metadata(
    pinecone_db: PineconeDB,
    vector_data: Dict,
    landmark_id: str,
    dry_run: bool = False
) -> bool:
    """
    Update a single vector with building metadata.

    Args:
        pinecone_db: Pinecone database client
        vector_data: Existing vector data including id, values, and metadata
        landmark_id: Landmark ID to collect metadata for
        dry_run: If True, don't actually update the vector

    Returns:
        True if successful, False otherwise
    """
    try:
        vector_id = vector_data['id']
        logger.info(f"Processing vector {vector_id} for landmark {landmark_id}")

        # Get enhanced metadata including building data
        collector = get_metadata_collector()
        enhanced_metadata = collector.collect_landmark_metadata(landmark_id)

        # Convert to dictionary
        if hasattr(enhanced_metadata, "dict"):
            new_metadata_dict = enhanced_metadata.dict()
        else:
            new_metadata_dict = dict(enhanced_metadata)

        # Check if building metadata exists
        building_keys = [k for k in new_metadata_dict.keys() if k.startswith("building_")]
        if not building_keys:
            logger.warning(f"No building metadata found for landmark {landmark_id}")
            return False

        logger.info(f"Found {len(building_keys)} building metadata fields for {landmark_id}")

        # Get existing metadata and merge with new building metadata
        existing_metadata = vector_data.get('metadata', {})

        # Check if building metadata already exists
        existing_building_keys = [k for k in existing_metadata.keys() if k.startswith("building_")]
        if existing_building_keys:
            logger.info(f"Vector already has {len(existing_building_keys)} building fields - updating")

        # Merge metadata (new building metadata will overwrite existing)
        updated_metadata = existing_metadata.copy()
        for key in building_keys:
            updated_metadata[key] = new_metadata_dict[key]

        if dry_run:
            logger.info(f"DRY RUN: Would update vector {vector_id} with building metadata")
            for key in sorted(building_keys)[:5]:  # Show first 5
                logger.info(f"  {key}: {new_metadata_dict[key]}")
            return True

        # Create vector for upsert (preserving existing values)
        vector_to_upsert = {
            'id': vector_id,
            'values': vector_data.get('values', []),
            'metadata': updated_metadata
        }

        # Use the internal upsert method to update the vector
        pinecone_db._upsert_vectors_in_batches([vector_to_upsert], batch_size=1)

        logger.info(f"Successfully updated vector {vector_id} with building metadata")
        return True

    except Exception as e:
        logger.error(f"Error updating vector {vector_id}: {e}")
        return False


def update_vectors_for_landmarks(
    landmark_ids: List[str],
    namespace: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, bool]:
    """
    Update vectors with building metadata for specified landmarks.

    Args:
        landmark_ids: List of landmark IDs to process
        namespace: Pinecone namespace to use
        dry_run: If True, don't actually update vectors

    Returns:
        Dictionary mapping landmark_id to success status
    """
    results = {}

    try:
        # Initialize Pinecone client
        pinecone_db = PineconeDB()

        for landmark_id in landmark_ids:
            logger.info(f"Processing landmark {landmark_id}")

            # Find vectors for this landmark
            vectors = pinecone_db.query_vectors(
                query_vector=None,  # List operation
                landmark_id=landmark_id,
                top_k=100,  # Get all vectors for this landmark
                namespace_override=namespace
            )

            if not vectors:
                logger.warning(f"No vectors found for landmark {landmark_id}")
                results[landmark_id] = False
                continue

            logger.info(f"Found {len(vectors)} vectors for landmark {landmark_id}")

            # Update each vector
            landmark_success = True
            for vector in vectors:
                success = update_vector_with_building_metadata(
                    pinecone_db, vector, landmark_id, dry_run
                )
                if not success:
                    landmark_success = False

            results[landmark_id] = landmark_success

    except Exception as e:
        logger.error(f"Error in update_vectors_for_landmarks: {e}")
        for landmark_id in landmark_ids:
            if landmark_id not in results:
                results[landmark_id] = False

    return results


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update existing vectors with building metadata"
    )
    parser.add_argument(
        "--landmark-ids",
        type=str,
        required=True,
        help="Comma-separated list of landmark IDs to process"
    )
    parser.add_argument(
        "--namespace",
        type=str,
        default="landmarks",
        help="Pinecone namespace to use"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    # Parse landmark IDs
    landmark_ids = [lid.strip() for lid in args.landmark_ids.split(",")]

    logger.info(f"Processing {len(landmark_ids)} landmarks: {landmark_ids}")
    if args.dry_run:
        logger.info("DRY RUN MODE - No actual updates will be made")

    # Update vectors
    results = update_vectors_for_landmarks(
        landmark_ids,
        namespace=args.namespace,
        dry_run=args.dry_run
    )

    # Report results
    logger.info("=== Results ===")
    success_count = 0
    for landmark_id, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"{landmark_id}: {status}")
        if success:
            success_count += 1

    logger.info(f"Successfully processed {success_count}/{len(landmark_ids)} landmarks")

    # Exit with appropriate code
    if success_count == len(landmark_ids):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
