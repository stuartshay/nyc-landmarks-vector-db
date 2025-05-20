#!/usr/bin/env python3
"""
Script to fetch a specific vector ID from Pinecone and display its metadata.

This utility allows you to retrieve vector data directly from the Pinecone database
for inspection and debugging purposes. When using the --pretty option, the output
is formatted in a structured way with:
- Clear section headers with separator lines
- Sorted metadata fields for easier reading
- Truncated display of long text fields
- Summary of vector dimensions and sample values

Example usage:
    # Basic usage - prints vector data to console
    python scripts/fetch_pinecone_vector.py "wiki-Wyckoff_House-LP-00001-chunk-0"

    # With pretty-printing for better readability
    python scripts/fetch_pinecone_vector.py "wiki-Wyckoff_House-LP-00001-chunk-0" --pretty
"""

import argparse
from typing import Any, Dict, Optional

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)


def fetch_vector(
    vector_id: str, pretty_print: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Fetch a specific vector from Pinecone by ID.

    Connects to the Pinecone database configured in the application settings,
    retrieves the vector with the specified ID, and returns its complete data
    including embeddings and metadata.

    Args:
        vector_id: The ID of the vector to fetch (e.g., "wiki-Wyckoff_House-LP-00001-chunk-0")
        pretty_print: Whether to format the output with clear sections, sorted metadata fields,
                     and truncated text for better console readability

    Returns:
        The vector data as a dictionary if found, including:
        - id: The vector ID
        - values: The embedding vector values (array of floats)
        - metadata: Dictionary containing all metadata fields like landmark_id, text, etc.
        Returns None if the vector wasn't found or an error occurred.
    """
    try:
        # Initialize Pinecone client
        pinecone_db = PineconeDB()

        # Access the Pinecone index directly
        logger.info(f"Fetching vector with ID: {vector_id}")
        # Get the underlying index object from PineconeDB
        index = pinecone_db.index

        # Use proper type annotations for the fetch operation
        from typing import Any as TypeAny
        from typing import cast

        # Fetch the vector by ID using the fetch method
        # Use cast to help mypy understand the dynamic nature of the Pinecone API
        result = cast(TypeAny, index).fetch(ids=[vector_id])

        # Handle the fetch response properly
        if (
            not result
            or not hasattr(result, "vectors")
            or vector_id not in result.vectors
        ):
            logger.error(f"Vector with ID '{vector_id}' not found in Pinecone")
            return None

        vector_data = result.vectors[vector_id]

        # Format and print the result in a more readable way
        if pretty_print:
            # Format vector data for better readability
            print("=" * 80)
            print(f"VECTOR ID: {vector_id}")
            print("=" * 80)

            # Print metadata in a structured way
            if hasattr(vector_data, "metadata") and vector_data.metadata:
                print("\nMETADATA:")
                print("-" * 80)
                # Sort metadata keys for consistent output
                for key in sorted(vector_data.metadata.keys()):
                    value = vector_data.metadata[key]
                    # Format long text values specially
                    if isinstance(value, str) and len(value) > 80:
                        print(f"{key}:")
                        print(f"  {value[:77]}...")
                        print(f"  [Total length: {len(value)} characters]")
                    else:
                        print(f"{key}: {value}")

            # Print vector values (first few only to avoid cluttering the console)
            if hasattr(vector_data, "values") and vector_data.values:
                values = vector_data.values
                print("\nVECTOR VALUES:")
                print("-" * 80)
                print(f"Dimension: {len(values)}")
                print(f"First 10 values: {values[:10]}")
                print("...")

            print("=" * 80)
        else:
            # For non-pretty mode, use default representation
            print(vector_data)

        # Convert the result to the expected return type
        return_data: Dict[str, Any] = {}

        # Copy all attributes from vector_data to return_data
        for key, value in vector_data.__dict__.items():
            return_data[key] = value

        return return_data

    except Exception as e:
        logger.error(f"Error fetching vector: {e}")
        return None


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Defines the command-line interface for the fetch_pinecone_vector script.
    """
    parser = argparse.ArgumentParser(
        description="Fetch a specific vector from Pinecone by ID and display its metadata",
        epilog=(
            "Example usage:\n"
            "  python scripts/fetch_pinecone_vector.py wiki-Wyckoff_House-LP-00001-chunk-0 --pretty\n"
            "  python scripts/fetch_pinecone_vector.py test-vector-123"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "vector_id",
        type=str,
        help="ID of the vector to fetch (e.g., wiki-Wyckoff_House-LP-00001-chunk-0)",
    )
    parser.add_argument(
        "--pretty",
        "-p",
        action="store_true",
        help="Format output with clear sections, sorted metadata, and truncated text for readability",
    )
    return parser.parse_args()


def main() -> None:
    """
    Main entry point for the script.

    Parses command line arguments and calls the fetch_vector function with the
    provided vector ID and formatting options.

    Example usage from command line:
        python scripts/fetch_pinecone_vector.py "wiki-Wyckoff_House-LP-00001-chunk-0" --pretty
    """
    args = parse_arguments()
    fetch_vector(args.vector_id, args.pretty)


if __name__ == "__main__":
    main()
