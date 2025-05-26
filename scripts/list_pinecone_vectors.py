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


def query_pinecone_index(pinecone_db: PineconeDB, limit: int) -> Any:
    """
    Query the Pinecone index and retrieve vectors.

    Args:
        pinecone_db: PineconeDB instance
        limit: Maximum number of vectors to return

    Returns:
        Query result with matches structure similar to direct index.query
    """
    # Use PineconeDB.query_vectors instead of direct index access
    logger.info(f"Querying with top_k: {limit}")

    # Get vectors using the centralized query_vectors method
    vectors = pinecone_db.query_vectors(
        query_vector=None,  # None for listing operation (uses zero vector internally)
        top_k=limit,
        include_values=False,
    )

    # Convert to a structure similar to what index.query would return for compatibility
    class QueryResult:
        def __init__(self, matches: List[Any]):
            self.matches = matches

    # Convert dictionary results to match objects for backward compatibility
    class Match:
        def __init__(self, match_dict: Dict[str, Any]):
            self.id = match_dict.get("id")
            self.score = match_dict.get("score")
            self.metadata = match_dict.get("metadata", {})

    matches = [Match(vector) for vector in vectors]
    return QueryResult(matches)


def filter_matches_by_prefix(matches: List[Any], prefix: Optional[str]) -> List[Any]:
    """
    Filter match results by prefix.

    Args:
        matches: List of match objects from Pinecone
        prefix: Optional prefix to filter vector IDs

    Returns:
        Filtered list of matches
    """
    if not prefix:
        return matches

    filtered_matches = []
    for match in matches:
        match_id = getattr(match, "id", None)
        if match_id and match_id.startswith(prefix):
            filtered_matches.append(match)

    return filtered_matches


def convert_matches_to_dicts(matches: List[Any]) -> List[Dict[str, Any]]:
    """
    Convert match objects to dictionaries.

    Args:
        matches: List of match objects from Pinecone

    Returns:
        List of match dictionaries
    """
    matches_data = []
    for match in matches:
        match_dict = {}
        # Extract attributes safely
        match_dict["id"] = getattr(match, "id", None)
        match_dict["score"] = getattr(match, "score", None)
        if hasattr(match, "metadata") and match.metadata:
            match_dict["metadata"] = match.metadata
        matches_data.append(match_dict)

    return matches_data


def list_vectors(
    prefix: Optional[str] = None, limit: int = 10, pretty_print: bool = False
) -> List[Dict[str, Any]]:
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
        logger.info(f"Listing vectors with prefix: {prefix if prefix else 'all'}")

        # Query the Pinecone index
        result = query_pinecone_index(pinecone_db, limit)

        # Handle the result safely
        matches = getattr(result, "matches", None)
        if not matches:
            logger.warning("No vectors found in Pinecone")
            return []

        # Filter results if prefix is provided
        filtered_matches = filter_matches_by_prefix(matches, prefix)
        if not filtered_matches:
            logger.warning(f"No vectors found with prefix: {prefix}")
            return []

        # Convert matches to dictionaries for display
        matches_data = convert_matches_to_dicts(filtered_matches)

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
    parser = argparse.ArgumentParser(description="List vectors in Pinecone")
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
