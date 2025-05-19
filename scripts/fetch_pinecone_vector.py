#!/usr/bin/env python3
"""
Script to fetch a specific vector ID from Pinecone and display its metadata.
"""

import argparse
import json
from typing import Any, Dict, Optional

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)

def fetch_vector(vector_id: str, pretty_print: bool = False) -> Optional[Dict[str, Any]]:
    """
    Fetch a specific vector from Pinecone by ID.

    Args:
        vector_id: The ID of the vector to fetch
        pretty_print: Whether to pretty-print the JSON output

    Returns:
        The vector data if found, None otherwise
    """
    try:
        # Initialize Pinecone client
        pinecone_db = PineconeDB()

        # Access the Pinecone index directly
        logger.info(f"Fetching vector with ID: {vector_id}")
        # Get the underlying index object from PineconeDB
        index = pinecone_db.index
        # Fetch the vector by ID using the fetch method
        result = index.fetch(ids=[vector_id])

        # Handle the fetch response properly
        if not result or not hasattr(result, 'vectors') or vector_id not in result.vectors:
            logger.error(f"Vector with ID '{vector_id}' not found in Pinecone")
            return None

        vector_data = result.vectors[vector_id]

        # Print the result
        if pretty_print:
            print(json.dumps(vector_data, indent=2, default=str))
        else:
            print(vector_data)

        return vector_data

    except Exception as e:
        logger.error(f"Error fetching vector: {e}")
        return None

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch a specific vector from Pinecone by ID"
    )
    parser.add_argument(
        "vector_id",
        type=str,
        help="ID of the vector to fetch",
    )
    parser.add_argument(
        "--pretty",
        "-p",
        action="store_true",
        help="Pretty-print JSON output",
    )
    return parser.parse_args()

def main() -> None:
    """Main entry point for the script."""
    args = parse_arguments()
    fetch_vector(args.vector_id, args.pretty)

if __name__ == "__main__":
    main()
