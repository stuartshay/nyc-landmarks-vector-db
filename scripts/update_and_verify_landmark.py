#!/usr/bin/env python3
"""
Script to update a specific landmark and verify the results.

This script:
1. Fetches a landmark by ID
2. Processes its enhanced metadata
3. Creates a test vector with the metadata
4. Uploads it to Pinecone
5. Retrieves the vector to verify that the changes were applied correctly

Usage:
    python scripts/update_and_verify_landmark.py LP-00009
"""

import argparse
import json
import time
from typing import Any, Dict, List, Optional

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.enhanced_metadata import EnhancedMetadataCollector
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)


def update_and_verify_landmark(landmark_id: str, verbose: bool = False) -> None:
    """
    Update a landmark in the vector database and verify the results.

    Args:
        landmark_id: ID of the landmark to process
        verbose: Whether to print detailed results
    """
    try:
        logger.info(f"Processing landmark: {landmark_id}")

        # Step 1: Initialize components
        db_client = get_db_client()
        metadata_collector = EnhancedMetadataCollector()
        pinecone_db = PineconeDB()

        # Step 2: Get landmark details
        landmark = db_client.get_landmark_by_id(landmark_id)
        if not landmark:
            logger.error(f"Landmark not found: {landmark_id}")
            return

        if isinstance(landmark, dict):
            landmark_name = landmark.get("name")
        else:
            landmark_name = getattr(landmark, "name", "")

        logger.info(f"Found landmark: {landmark_name}")

        # Step 3: Collect enhanced metadata
        enhanced_metadata = metadata_collector.collect_landmark_metadata(landmark_id)

        # Convert enhanced_metadata to dict for compatibility with _create_metadata_for_chunk
        enhanced_metadata_dict = (
            enhanced_metadata.model_dump()
            if hasattr(enhanced_metadata, "model_dump")
            else enhanced_metadata.model_dump()
        )

        # Step 4: Create a test vector
        test_vector_id = f"test-{landmark_id}-update-{int(time.time())}"
        logger.info(f"Creating test vector with ID: {test_vector_id}")

        mock_chunk = {
            "text": f"Test chunk for {landmark_name}",
            "embedding": [0.1] * settings.OPENAI_EMBEDDING_DIMENSIONS,
        }

        metadata = pinecone_db._create_metadata_for_chunk(
            chunk=mock_chunk,
            source_type="test",
            chunk_index=0,
            landmark_id=landmark_id,
            enhanced_metadata=enhanced_metadata_dict,
        )

        # Step 5: Upload test vector
        # Format the vector as expected by Pinecone SDK
        vectors_to_upsert = [
            {
                "id": test_vector_id,
                "values": mock_chunk["embedding"],
                "metadata": metadata,
            }
        ]

        # Use the namespace if configured
        namespace = pinecone_db.namespace if pinecone_db.namespace else None

        logger.info(f"Upserting test vector to Pinecone with ID: {test_vector_id}")
        if namespace:
            logger.info(f"Using namespace: {namespace}")
            pinecone_db.index.upsert(vectors=vectors_to_upsert, namespace=namespace)
        else:
            pinecone_db.index.upsert(vectors=vectors_to_upsert)

        logger.info("Uploaded test vector to Pinecone")

        # Step 6: Verify the results
        logger.info("Waiting a moment for indexing...")
        # Increase wait time to allow for Pinecone indexing
        wait_time = 10
        logger.info(f"Waiting {wait_time} seconds for indexing to complete...")
        time.sleep(wait_time)

        # Query the vector to verify
        verify_vector(test_vector_id, verbose, namespace)

        logger.info("Update and verification complete")

    except Exception as e:
        logger.error(f"Error updating and verifying landmark: {e}", exc_info=True)


def execute_vector_query(
    pinecone_db: PineconeDB,
    vector: list,
    filter_dict: Optional[Dict[str, Any]] = None,
    top_k: int = 1,
    namespace: Optional[str] = None,
) -> Any:
    """
    Execute a query against the Pinecone index.

    Args:
        pinecone_db: Pinecone DB instance
        vector: Vector to query with
        filter_dict: Optional filter dictionary
        top_k: Number of results to return
        namespace: Optional namespace to query in

    Returns:
        Query response from Pinecone
    """
    # Build query based on available parameters to avoid using **kwargs
    # which is causing type errors
    if namespace and filter_dict:
        return pinecone_db.index.query(
            vector=vector,
            filter=filter_dict,
            top_k=top_k,
            include_metadata=True,
            namespace=namespace,
        )
    elif namespace:
        return pinecone_db.index.query(
            vector=vector, top_k=top_k, include_metadata=True, namespace=namespace
        )
    elif filter_dict:
        return pinecone_db.index.query(
            vector=vector, filter=filter_dict, top_k=top_k, include_metadata=True
        )
    else:
        return pinecone_db.index.query(
            vector=vector, top_k=top_k, include_metadata=True
        )


def extract_matches_from_response(
    response: Any, vector_id: Optional[str] = None
) -> List[Any]:
    """
    Extract matches from a Pinecone query response.

    Args:
        response: Pinecone query response
        vector_id: Optional vector ID to filter matches by

    Returns:
        List of matches
    """
    matches = []
    if hasattr(response, "matches"):
        matches = getattr(response, "matches")
    elif isinstance(response, dict) and "matches" in response:
        matches = response["matches"]

    # If vector_id is provided, filter matches for that ID
    if vector_id and matches:
        filtered_matches = []
        for match in matches:
            match_id = (
                getattr(match, "id", "")
                if hasattr(match, "id")
                else match.get("id", "")
            )
            if match_id == vector_id:
                filtered_matches.append(match)
        return filtered_matches

    return matches


def extract_metadata_from_vector(vector: Any) -> Dict[str, Any]:
    """
    Extract metadata from a vector object.

    Args:
        vector: Vector object from Pinecone

    Returns:
        Dictionary of metadata
    """
    metadata = {}
    if hasattr(vector, "metadata"):
        metadata = getattr(vector, "metadata")
    elif isinstance(vector, dict) and "metadata" in vector:
        metadata = vector["metadata"]
    return metadata


def check_bbl_fields(metadata: Dict[str, Any]) -> None:
    """
    Check BBL-related fields in the metadata.

    Args:
        metadata: Vector metadata dictionary
    """
    logger.info("Checking BBL-related fields:")

    # Check if buildings are present in the metadata
    if "buildings" in metadata:
        logger.error(
            "Unexpected 'buildings' field found in metadata - complex objects should be flattened"
        )

    # Check if standalone BBL fields are present
    bbl_fields = ["bbl", "all_bbls"]
    for field in bbl_fields:
        if field in metadata:
            logger.error(
                f"Deprecated standalone field '{field}' found in metadata: {metadata[field]}"
            )


def check_building_fields(metadata: Dict[str, Any]) -> None:
    """
    Check building-related fields in the metadata.

    Args:
        metadata: Vector metadata dictionary
    """
    # Check for building structure
    building_fields = [k for k in metadata.keys() if k.startswith("building_")]
    if building_fields:
        logger.info(f"Found {len(building_fields)} building-related fields")

        # Extract building count
        building_count = metadata.get("building_count", 0)
        logger.info(f"Building count: {building_count}")

        # Extract BBLs from building fields
        bbls = []
        for i in range(
            int(building_count) if isinstance(building_count, (int, float, str)) else 0
        ):
            bbl_field = f"building_{i}_bbl"
            if bbl_field in metadata:
                bbls.append(metadata[bbl_field])

        logger.info(f"BBLs from buildings: {bbls}")
    else:
        logger.info("No building-related fields found in metadata")


def verify_vector(
    vector_id: str, verbose: bool = False, namespace: Optional[str] = None
) -> None:
    """Check metadata for a specific vector ID to verify the update.

    Args:
        vector_id: The ID of the vector to check
        verbose: Whether to print detailed results
        namespace: Optional namespace to use for querying
    """
    pinecone_db = PineconeDB()

    logger.info(f"Verifying vector: {vector_id}")
    if namespace:
        logger.info(f"Using namespace: {namespace}")

    # Get index stats and extract dimension
    dimension = settings.OPENAI_EMBEDDING_DIMENSIONS
    dummy_vector = [0.0] * dimension

    try:
        # First try querying with filter
        logger.info(f"Querying for vector ID: {vector_id}")
        filter_dict = {"id": vector_id}

        # Execute query with filter
        query_response = execute_vector_query(
            pinecone_db, dummy_vector, filter_dict, 1, namespace
        )

        # Extract matches from response
        matches = extract_matches_from_response(query_response)

        # If no matches found, try without filter
        if not matches:
            logger.error(f"Vector not found: {vector_id}")
            logger.info("Trying query without filter...")

            # Execute query without filter
            query_response = execute_vector_query(
                pinecone_db, dummy_vector, None, 100, namespace
            )

            # Look for our specific vector ID in the results
            matches = extract_matches_from_response(query_response, vector_id)

            if not matches:
                logger.error(f"Vector still not found: {vector_id}")
                return

        # We have a match, get the first one
        vector = matches[0]

        # Extract metadata from vector
        metadata = extract_metadata_from_vector(vector)
        if not metadata:
            logger.error("No metadata found in vector")
            return

        # Print basic vector info
        logger.info(f"Vector ID: {vector_id}")

        # Check BBL and building fields
        check_bbl_fields(metadata)
        check_building_fields(metadata)

        # Print full metadata if verbose
        if verbose:
            try:
                logger.info(
                    f"Full metadata:\n{json.dumps(metadata, indent=2, default=str)}"
                )
            except Exception as e:
                logger.error(f"Could not serialize metadata: {e}")
                logger.info(f"Raw metadata: {metadata}")

        logger.info("Verification complete")

    except Exception as e:
        logger.error(f"Error verifying vector {vector_id}: {e}", exc_info=True)
        return


def main() -> None:
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description="Update a landmark and verify the results"
    )
    parser.add_argument(
        "landmark_id", help="ID of the landmark to process (e.g., LP-00009)"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print detailed results"
    )

    args = parser.parse_args()

    # Run the update and verification
    update_and_verify_landmark(args.landmark_id, args.verbose)


if __name__ == "__main__":
    main()
