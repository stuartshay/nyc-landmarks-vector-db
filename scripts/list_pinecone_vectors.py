#!/usr/bin/env python3
"""
Script to list vectors in Pinecone and filter by prefix.
"""

import argparse
import json
from typing import Any, Dict, List, Optional

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)

def list_vectors(prefix: Optional[str] = None, limit: int = 10, pretty_print: bool = False) -> List[Dict[str, Any]]:
    """
    List vectors in Pinecone, optionally filtering by prefix.

    Args:
        prefix: Optional prefix to filter vector IDs
        limit: Maximum number of vectors to return
        pretty_print: Whether to pretty-print the JSON output

    Returns:
        List of vector data
    """
    try:
        # Initialize Pinecone client
        pinecone_db = PineconeDB()

        # Access the Pinecone index directly
        logger.info(f"Listing vectors with prefix: {prefix if prefix else 'all'}")
        # Get the underlying index object from PineconeDB
        index = pinecone_db.index

        # Query parameters
        query_params = {
            "top_k": limit,
            "include_metadata": True,
            "include_values": False,
        }

        # Use a standard dimension for embeddings (most models use 1536 for text)
        # This is just a dummy vector to list vectors
        vector_dimension = 1536  # Common dimension for embeddings
        zero_vector = [0.0] * vector_dimension

        # Query the index without filtering - we'll filter results locally
        logger.info(f"Querying with parameters: {query_params}")
        result = index.query(vector=zero_vector, **query_params)

        if not result or not hasattr(result, 'matches') or not result.matches:
            logger.warning("No vectors found in Pinecone")
            return []

        # Filter results if prefix is provided
        filtered_matches = []
        for match in result.matches:
            match_id = getattr(match, 'id', None)
            if match_id and (not prefix or (prefix and match_id.startswith(prefix))):
                filtered_matches.append(match)

        if not filtered_matches:
            logger.warning(f"No vectors found with prefix: {prefix}")
            return []

        # Convert matches to dictionaries for display
        matches_data = []
        for match in filtered_matches:
            match_dict = {}
            # Extract attributes safely
            match_dict['id'] = getattr(match, 'id', None)
            match_dict['score'] = getattr(match, 'score', None)
            if hasattr(match, 'metadata') and match.metadata:
                match_dict['metadata'] = match.metadata
            matches_data.append(match_dict)

        # Print the results
        if pretty_print:
            print(json.dumps(matches_data, indent=2, default=str))
        else:
            for match_data in matches_data:
                print(match_data)

        return matches_data

    except Exception as e:
        logger.error(f"Error listing vectors: {e}")
        import traceback
        traceback.print_exc()
        return []

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="List vectors in Pinecone"
    )
    parser.add_argument(
        "--prefix",
        "-p",
        type=str,
        help="Prefix to filter vector IDs",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=10,
        help="Maximum number of vectors to return",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    return parser.parse_args()

def main() -> None:
    """Main entry point for the script."""
    args = parse_arguments()
    list_vectors(args.prefix, args.limit, args.pretty)

if __name__ == "__main__":
    main()
