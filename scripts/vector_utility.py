#!/usr/bin/env python3
"""
Vector Utility - A comprehensive tool for working with Pinecone vectors.

This utility provides various operations for inspecting, validating, and managing
vector data in the Pinecone database. It combines functionality from multiple
standalone scripts into a single, unified command-line tool.

Commands:
    fetch           - Fetch a specific vector by ID
    check-landmark  - Check all vectors for a specific landmark ID
    list-vectors    - List vectors in Pinecone with optional filtering
    validate        - Validate a specific vector against requirements
    compare-vectors - Compare metadata between two vectors
    verify-vectors  - Verify the integrity of vectors in Pinecone
    verify-batch    - Verify a batch of specific vectors by their IDs
    verify           - Verify the integrity of vectors

Example usage:
    # Fetch a specific vector by ID:
    python scripts/vector_utility.py fetch wiki-Wyckoff_House-LP-00001-chunk-0 --pretty

    # Fetch a vector from a specific namespace:
    python scripts/vector_utility.py fetch wiki-Manhattan_Municipal_Building-LP-00079-chunk-0 --namespace landmarks --pretty

    # Check all vectors for a specific landmark:
    python scripts/vector_utility.py check-landmark LP-00001 --namespace landmarks --verbose

    # List up to 10 vectors starting with a specific prefix:
    python scripts/vector_utility.py list-vectors --prefix wiki-Manhattan --limit 10 --pretty --namespace landmarks

    # Validate a specific vector against metadata requirements:
    python scripts/vector_utility.py validate wiki-Wyckoff_House-LP-00001-chunk-0 --pretty

    # Compare metadata between two vectors:
    python scripts/vector_utility.py compare-vectors wiki-Wyckoff_House-LP-00001-chunk-0 wiki-Wyckoff_House-LP-00001-chunk-1 --namespace landmarks

    # Verify vector integrity in Pinecone:
    python scripts/vector_utility.py verify-vectors --prefix wiki-Wyckoff --limit 20 --verbose

    # Verify a batch of specific vectors:
    python scripts/vector_utility.py verify-batch wiki-Wyckoff_House-LP-00001-chunk-0 wiki-Wyckoff_House-LP-00001-chunk-1
"""

import argparse
import json
from typing import Any, Dict, List, Optional

from nyc_landmarks.config.settings import settings
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)

# =============== Constants ===============

# Required metadata fields for all vectors
REQUIRED_METADATA = ["landmark_id", "source_type", "chunk_index", "text"]

# Additional required metadata fields for Wikipedia vectors
REQUIRED_WIKI_METADATA = ["article_title", "article_url"]

# Vector ID format patterns for validation
PDF_ID_PATTERN = r"^(LP-\d{5})-chunk-(\d+)$"
WIKI_ID_PATTERN = r"^wiki-(.+)-(LP-\d{5})-chunk-(\d+)$"

# =============== Fetch Vector Command Functions ===============

def fetch_vector(
    vector_id: str, pretty_print: bool = False, namespace: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch a specific vector from Pinecone by ID.

    Connects to the Pinecone database configured in the application settings,
    retrieves the vector with the specified ID, and returns its complete data
    including embeddings and metadata.

    Args:
        vector_id: The ID of the vector to fetch
        pretty_print: Whether to format the output with clear sections
        namespace: Optional Pinecone namespace to search in

    Returns:
        The vector data as a dictionary if found
    """
    try:
        # Initialize Pinecone client
        pinecone_db = PineconeDB()

        # Override namespace if provided
        if namespace is not None:
            pinecone_db.namespace = namespace
            logger.info(f"Using custom namespace: {namespace}")
        else:
            logger.info(f"Using default namespace: {pinecone_db.namespace}")

        # Access the Pinecone index directly
        logger.info(f"Fetching vector with ID: {vector_id}")
        index = pinecone_db.index

        # Use proper type annotations for the fetch operation
        from typing import Any as TypeAny
        from typing import cast

        # Fetch the vector by ID using the fetch method with namespace
        result = cast(TypeAny, index).fetch(
            ids=[vector_id],
            namespace=pinecone_db.namespace if pinecone_db.namespace else None
        )

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


# =============== Check Landmark Vectors Command Functions ===============

def query_landmark_vectors(pinecone_db: PineconeDB, landmark_id: str, namespace: Optional[str] = None) -> List[Any]:
    """
    Query Pinecone for vectors related to a landmark.

    Args:
        pinecone_db: PineconeDB instance
        landmark_id: The ID of the landmark to check
        namespace: Optional namespace to query

    Returns:
        List of vector matches
    """
    # Set namespace if provided
    if namespace is not None:
        pinecone_db.namespace = namespace
        logger.info(f"Using custom namespace: {namespace}")
    else:
        logger.info(f"Using default namespace: {pinecone_db.namespace}")

    # Use a dimension of 1536 for OpenAI embeddings
    dimension = settings.OPENAI_EMBEDDING_DIMENSIONS

    # Query all vectors for this landmark
    query_response = pinecone_db.index.query(
        vector=[0.0] * dimension,  # Dummy vector
        filter={"landmark_id": landmark_id},
        top_k=100,  # Increase if needed
        include_metadata=True,
        namespace=pinecone_db.namespace if pinecone_db.namespace else None
    )

    # Access matches safely
    matches = []
    if hasattr(query_response, "matches"):
        matches = getattr(query_response, "matches")
    elif isinstance(query_response, dict) and "matches" in query_response:
        matches = query_response["matches"]

    return matches


def extract_metadata(match: Any) -> Dict[str, Any]:
    """
    Extract metadata from a match object.

    Args:
        match: Match object from Pinecone query

    Returns:
        Metadata dictionary
    """
    metadata = {}
    if hasattr(match, "metadata"):
        metadata = match.metadata
    elif isinstance(match, dict) and "metadata" in match:
        metadata = match["metadata"]
    return metadata


def get_vector_id(match: Any) -> str:
    """
    Extract vector ID from a match object.

    Args:
        match: Match object from Pinecone query

    Returns:
        Vector ID string
    """
    if hasattr(match, "id"):
        return str(match.id)
    elif isinstance(match, dict) and "id" in match:
        return str(match["id"])
    else:
        return "unknown"


def check_deprecated_fields(metadata: Dict[str, Any]) -> None:
    """
    Check for deprecated fields in metadata.

    Args:
        metadata: Vector metadata dictionary
    """
    if "bbl" in metadata:
        print(f"WARNING: Deprecated standalone field 'bbl' found: {metadata['bbl']}")

    if "all_bbls" in metadata:
        print(
            f"WARNING: Deprecated standalone field 'all_bbls' found: {metadata['all_bbls']}"
        )


def process_building_data(metadata: Dict[str, Any]) -> None:
    """
    Process and display building data from metadata.

    Args:
        metadata: Vector metadata dictionary
    """
    building_fields = [k for k in metadata.keys() if k.startswith("building_")]
    if building_fields:
        building_count = metadata.get("building_count", 0)
        print(f"Building count: {building_count}")

        # Find all building BBLs
        building_bbls = []
        for i in range(building_count):
            bbl_field = f"building_{i}_bbl"
            if bbl_field in metadata:
                building_bbls.append(metadata[bbl_field])

        if building_bbls:
            print(f"Building BBLs: {building_bbls}")
        else:
            print("No building BBLs found")
    else:
        print("No building data found")


def display_metadata(metadata: Dict[str, Any], verbose: bool = False) -> None:
    """
    Display metadata, with full details if verbose.

    Args:
        metadata: Vector metadata dictionary
        verbose: Whether to print full metadata details
    """
    if verbose:
        print("\nFull metadata:")
        try:
            print(json.dumps(metadata, indent=2, default=str))
        except Exception as e:
            print(f"Error serializing metadata: {e}")
            print(f"Raw metadata: {metadata}")


def check_landmark_vectors(
    landmark_id: str, verbose: bool = False, namespace: Optional[str] = None
) -> None:
    """
    Check all vectors for a specific landmark.

    Args:
        landmark_id: The ID of the landmark to check
        verbose: Whether to print full metadata details
        namespace: Optional namespace to query
    """
    pinecone_db = PineconeDB()
    print(f"Checking vectors for landmark: {landmark_id}")

    # Get vector matches from Pinecone
    matches = query_landmark_vectors(pinecone_db, landmark_id, namespace)

    print(f"Found {len(matches)} vectors for landmark {landmark_id}")
    if not matches:
        print("No vectors found.")
        return

    # Process each match
    for i, match in enumerate(matches):
        vector_id = get_vector_id(match)
        print(f"\nVector {i + 1}: {vector_id}")

        # Get and process metadata
        metadata = extract_metadata(match)
        check_deprecated_fields(metadata)
        process_building_data(metadata)
        display_metadata(metadata, verbose)


# =============== List Vectors Command Functions ===============

def query_pinecone_index(
    pinecone_db: PineconeDB, limit: int, namespace: Optional[str] = None, prefix: Optional[str] = None
) -> Any:
    """
    Query the Pinecone index and retrieve vectors.

    Args:
        pinecone_db: PineconeDB instance
        limit: Maximum number of vectors to return
        namespace: Optional Pinecone namespace to query in
        prefix: Optional prefix to filter vector IDs (will increase limit internally)

    Returns:
        Query result from Pinecone
    """
    # Use a standard dimension for embeddings
    vector_dimension = 1536  # Common dimension for embeddings
    zero_vector = [0.0] * vector_dimension

    # Set the namespace if provided
    if namespace is not None:
        pinecone_db.namespace = namespace
        logger.info(f"Using custom namespace: {namespace}")
    else:
        logger.info(f"Using default namespace: {pinecone_db.namespace}")

    # If prefix is provided, we'll need to retrieve more vectors to ensure we get matches
    # We'll retrieve a larger number of vectors when filtering by prefix
    effective_limit = limit
    if prefix:
        # For prefix filtering, retrieve a larger number of vectors
        # Minimum 100, but scale with the requested limit
        effective_limit = max(limit * 20, 100)
        logger.info(f"Using effective limit of {effective_limit} to ensure prefix matches for '{prefix}'")

    # Log the query parameters
    logger.info(f"Querying with top_k: {effective_limit}, namespace: {pinecone_db.namespace}")

    # Query the index
    result = pinecone_db.index.query(
        vector=zero_vector,
        top_k=effective_limit,
        include_metadata=True,
        include_values=False,
        namespace=pinecone_db.namespace if pinecone_db.namespace else None
    )

    # Log the total number of matches received
    match_count = len(getattr(result, "matches", []))
    logger.info(f"Retrieved {match_count} vectors from Pinecone")

    return result


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

    total_matches = len(matches)
    logger.info(f"Filtering {total_matches} matches with prefix: '{prefix}'")

    if total_matches == 0:
        print("No vectors retrieved from Pinecone to filter.")
        return []

    # Normalize the prefix for case-insensitive matching
    prefix_lower = prefix.lower()

    # Debug: print first few match IDs to see what we're filtering
    print(f"\nFirst {min(5, total_matches)} matches before filtering:")
    for i, match in enumerate(matches[:5]):
        match_id = getattr(match, "id", "Unknown")
        print(f"  {i+1}. {match_id}")

    # Collect and analyze prefixes to help with debugging
    prefix_distribution = {}
    id_examples = {}

    # Analyze up to 100 vectors to find common prefixes
    sample_size = min(len(matches), 100)
    for match in matches[:sample_size]:
        match_id = getattr(match, "id", "")
        if match_id:
            parts = match_id.split('-')
            if len(parts) > 1:
                # Get the first part or first two parts as common prefixes
                first_part = parts[0]
                if first_part not in prefix_distribution:
                    prefix_distribution[first_part] = 1
                    id_examples[first_part] = match_id
                else:
                    prefix_distribution[first_part] += 1

                # Also track combined prefixes if available
                if len(parts) > 1:
                    combined = f"{parts[0]}-{parts[1]}"
                    if combined not in prefix_distribution:
                        prefix_distribution[combined] = 1
                        id_examples[combined] = match_id
                    else:
                        prefix_distribution[combined] += 1

    # Filter matches by prefix (case insensitive)
    filtered_matches = []
    for match in matches:
        match_id = getattr(match, "id", None)
        if match_id and match_id.lower().startswith(prefix_lower):
            filtered_matches.append(match)

    # Report results
    filtered_count = len(filtered_matches)
    print(f"\nFound {filtered_count} matches out of {total_matches} after filtering with prefix: '{prefix}'")

    # If filtered matches found, show examples
    if filtered_matches:
        print("\nMatched vector IDs (first 5):")
        for i, match in enumerate(filtered_matches[:5]):
            match_id = getattr(match, "id", "Unknown")
            print(f"  {i+1}. {match_id}")
    # If no matches, provide helpful diagnostics
    else:
        print("\nNo matches found with the specified prefix.")

        # Show the most common prefixes found in the data
        if prefix_distribution:
            print("\nCommon prefixes found in the data (with examples):")
            # Sort by frequency, most common first
            sorted_prefixes = sorted(
                prefix_distribution.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Show top 5 common prefixes
            for i, (common_prefix, count) in enumerate(sorted_prefixes[:5]):
                example = id_examples.get(common_prefix, "")
                print(f"  {i+1}. '{common_prefix}' ({count} vectors) - Example: {example}")

            print("\nSuggestions:")
            print("  - Check if your prefix matches exactly how vector IDs are stored")
            print("  - Try using one of the common prefixes shown above")
            print("  - Use a shorter prefix or check for case sensitivity")

            # Check if the prefix is close to any of the common prefixes
            close_matches = [p for p in prefix_distribution.keys() if prefix.lower() in p.lower()]
            if close_matches:
                print("\nSimilar prefixes found that contain your search term:")
                for i, similar in enumerate(close_matches[:3]):
                    print(f"  - '{similar}' (example: {id_examples.get(similar, '')})")

    return filtered_matches


def convert_matches_to_dicts(matches: List[Any]) -> List[Dict[str, Any]]:
    """
    Convert Pinecone match objects to dictionaries.

    Args:
        matches: List of match objects from Pinecone

    Returns:
        List of match dictionaries
    """
    result = []
    for match in matches:
        match_dict = {
            "id": getattr(match, "id", "Unknown"),
            "score": getattr(match, "score", 0.0),
        }

        # Add metadata if available
        metadata = getattr(match, "metadata", None)
        if metadata:
            match_dict["metadata"] = metadata

        result.append(match_dict)

    return result


def list_vectors(
    prefix: Optional[str] = None,
    limit: int = 10,
    pretty_print: bool = False,
    namespace: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List vectors in Pinecone with optional prefix filtering.

    Connects to the Pinecone database and retrieves vectors, optionally filtered
    by a prefix on the vector ID.

    Args:
        prefix: Optional prefix to filter vector IDs
        limit: Maximum number of vectors to return
        pretty_print: Whether to format the output nicely
        namespace: Optional Pinecone namespace to search in

    Returns:
        List of vector data
    """
    try:
        # Initialize Pinecone client
        pinecone_db = PineconeDB()
        logger.info(f"Listing vectors with prefix: '{prefix if prefix else 'all'}'")

        # Display query information
        print("\nQuerying Pinecone database for vectors")
        print(f"  Namespace: {namespace if namespace else pinecone_db.namespace or 'default'}")
        print(f"  Prefix filter: {prefix if prefix else 'None'}")
        print(f"  Result limit: {limit}")

        # Query the Pinecone index with the prefix parameter
        result = query_pinecone_index(pinecone_db, limit, namespace, prefix)

        # Handle the result safely
        matches = getattr(result, "matches", None)
        if not matches:
            logger.warning("No vectors found in Pinecone")
            print("\nNo vectors found in the database.")
            return []

        # Filter results if prefix is provided
        filtered_matches = filter_matches_by_prefix(matches, prefix)
        if not filtered_matches:
            logger.warning(f"No vectors found with prefix: '{prefix}'")
            return []

        # If we have more matches than the limit after filtering, truncate
        if len(filtered_matches) > limit:
            print(f"\nFound {len(filtered_matches)} matches, showing first {limit} as requested")
            filtered_matches = filtered_matches[:limit]
            logger.info(f"Limited results to {limit} matches")
        else:
            print(f"\nFound {len(filtered_matches)} matches")

        # Convert matches to dictionaries for display
        matches_data = convert_matches_to_dicts(filtered_matches)

        # Print the results
        if pretty_print:
            print("\n" + "=" * 80)
            print(f"VECTORS IN PINECONE ({len(matches_data)} found)")
            print("=" * 80)

            # Process each vector individually for better formatting
            for i, match_data in enumerate(matches_data):
                print(f"\nVector {i+1}:")
                print("-" * 40)
                print(f"ID: {match_data.get('id', 'Unknown')}")
                print(f"Score: {match_data.get('score', 0.0)}")

                # Format metadata if present
                metadata = match_data.get('metadata', {})
                if metadata:
                    print("\nMetadata:")
                    # Format each metadata field
                    for key in sorted(metadata.keys()):
                        value = metadata[key]
                        # Format text fields specially
                        if isinstance(value, str) and len(value) > 80:
                            print(f"  {key}:")
                            print(f"    {value[:77]}...")
                            print(f"    [Total length: {len(value)} characters]")
                        else:
                            print(f"  {key}: {value}")
        else:
            for i, match_data in enumerate(matches_data):
                print(f"\nVector {i+1}:")
                print(f"  ID: {match_data.get('id', 'Unknown')}")
                print(f"  Score: {match_data.get('score', 0.0)}")
                # Print a few key metadata fields if available
                metadata = match_data.get('metadata', {})
                if metadata:
                    landmark_id = metadata.get('landmark_id', 'Unknown')
                    source_type = metadata.get('source_type', 'Unknown')
                    chunk_index = metadata.get('chunk_index', 'Unknown')
                    print(f"  Landmark ID: {landmark_id}")
                    print(f"  Source Type: {source_type}")
                    print(f"  Chunk Index: {chunk_index}")

        return matches_data

    except Exception as e:
        logger.error(f"Error listing vectors: {e}")
        import traceback
        traceback.print_exc()
        return []


# =============== Validate Vector Command Functions ===============

def validate_vector_metadata(vector_data: Dict[str, Any], verbose: bool = False) -> bool:
    """
    Validate a vector's metadata against requirements.

    Args:
        vector_data: The vector data to validate
        verbose: Whether to print detailed validation information

    Returns:
        True if valid, False otherwise
    """
    metadata = vector_data.get("metadata", {})
    vector_id = vector_data.get("id", "Unknown")

    if verbose:
        print("\n" + "=" * 80)
        print(f"VALIDATING VECTOR: {vector_id}")
        print("=" * 80)
        print(f"\nMetadata keys: {list(metadata.keys()) if metadata else 'None'}")
        if metadata:
            print(f"\nFull metadata:\n{json.dumps(metadata, indent=2, default=str)}")

    # Check for required fields first
    missing_fields = []
    for field in REQUIRED_METADATA:
        if field not in metadata:
            missing_fields.append(field)

    # Check for Wikipedia-specific fields if this is a Wikipedia vector
    if vector_id.startswith("wiki-"):
        for field in REQUIRED_WIKI_METADATA:
            if field not in metadata:
                missing_fields.append(field)

    # Print validation results
    if missing_fields:
        print(f"\nERROR: Vector {vector_id} is missing required fields: {missing_fields}")
        return False
    else:
        print(f"\nVector {vector_id} has all required metadata fields")

        # Print additional validation checks for important fields
        if verbose:
            source_type = metadata.get("source_type", "Unknown")
            chunk_index = metadata.get("chunk_index", "Unknown")
            landmark_id = metadata.get("landmark_id", "Unknown")
            print("\nVector Details:")
            print(f"  Source Type: {source_type}")
            print(f"  Chunk Index: {chunk_index}")
            print(f"  Landmark ID: {landmark_id}")

            if vector_id.startswith("wiki-"):
                article_title = metadata.get("article_title", "Unknown")
                article_url = metadata.get("article_url", "Unknown")
                print(f"  Article Title: {article_title}")
                print(f"  Article URL: {article_url}")

        return True


def validate_vector_command(args: argparse.Namespace) -> None:
    """Command handler for validating a specific vector."""
    try:
        vector_data = fetch_vector(args.vector_id, namespace=args.namespace)
        if not vector_data:
            print(f"ERROR: Vector with ID '{args.vector_id}' not found")
            return

        validate_vector_metadata(vector_data, verbose=args.verbose)

    except Exception as e:
        logger.error(f"Error validating vector: {e}")
        import traceback
        traceback.print_exc()


# =============== Compare Vectors Command Functions ===============

def compare_vectors(
    first_vector_id: str,
    second_vector_id: str,
    output_format: str = "text",
    namespace: Optional[str] = None
) -> bool:
    """
    Compare metadata and optionally embeddings between two vectors.

    Args:
        first_vector_id: ID of the first vector to compare
        second_vector_id: ID of the second vector to compare
        output_format: Format for displaying the comparison ("text" or "json")
        namespace: Optional Pinecone namespace to search in

    Returns:
        True if successful comparison, False otherwise
    """
    try:
        # Fetch both vectors
        logger.info(f"Fetching first vector: {first_vector_id}")
        first_vector = fetch_vector(first_vector_id, namespace=namespace)
        if not first_vector:
            print(f"ERROR: First vector with ID '{first_vector_id}' not found")
            return False

        logger.info(f"Fetching second vector: {second_vector_id}")
        second_vector = fetch_vector(second_vector_id, namespace=namespace)
        if not second_vector:
            print(f"ERROR: Second vector with ID '{second_vector_id}' not found")
            return False

        # Compare metadata
        first_metadata = first_vector.get("metadata", {})
        second_metadata = second_vector.get("metadata", {})

        # Find all unique keys across both metadata
        all_keys = set(first_metadata.keys()).union(set(second_metadata.keys()))

        # Output header
        print("=" * 80)
        print("COMPARING VECTORS")
        print(f"First:  {first_vector_id}")
        print(f"Second: {second_vector_id}")
        print("=" * 80)

        # Compare and display differences
        print("\nMETADATA COMPARISON:")
        print("-" * 40)

        differences = []
        similarities = []
        unique_to_first = []
        unique_to_second = []

        for key in sorted(all_keys):
            if key not in first_metadata:
                unique_to_second.append(key)
            elif key not in second_metadata:
                unique_to_first.append(key)
            elif first_metadata[key] != second_metadata[key]:
                differences.append(key)
            else:
                similarities.append(key)

        # Print results based on format
        if output_format == "text":
            # Print fields that differ
            if differences:
                print("\nDifferent Values:")
                for key in differences:
                    print(f"  {key}:")
                    print(f"    First:  {first_metadata[key]}")
                    print(f"    Second: {second_metadata[key]}")
                    print()

            # Print fields unique to first vector
            if unique_to_first:
                print("\nUnique to First Vector:")
                for key in unique_to_first:
                    print(f"  {key}: {first_metadata[key]}")

            # Print fields unique to second vector
            if unique_to_second:
                print("\nUnique to Second Vector:")
                for key in unique_to_second:
                    print(f"  {key}: {second_metadata[key]}")

            # Print similar fields if requested
            if similarities:
                print(f"\nIdentical Fields: {len(similarities)} fields match")
                # We don't print all identical fields to avoid cluttering the output

        elif output_format == "json":
            comparison = {
                "vectors": {
                    "first": first_vector_id,
                    "second": second_vector_id
                },
                "differences": {
                    key: {
                        "first": first_metadata.get(key),
                        "second": second_metadata.get(key)
                    } for key in differences
                },
                "unique_to_first": {key: first_metadata[key] for key in unique_to_first},
                "unique_to_second": {key: second_metadata[key] for key in unique_to_second},
                "identical_field_count": len(similarities)
            }
            print(json.dumps(comparison, indent=2, default=str))

        # Provide a summary
        if output_format == "text":
            print("\nSUMMARY:")
            print(f"  Fields with different values: {len(differences)}")
            print(f"  Fields unique to first vector: {len(unique_to_first)}")
            print(f"  Fields unique to second vector: {len(unique_to_second)}")
            print(f"  Fields with identical values: {len(similarities)}")

        return True

    except Exception as e:
        logger.error(f"Error comparing vectors: {e}")
        import traceback
        traceback.print_exc()
        return False


def compare_vectors_command(args: argparse.Namespace) -> None:
    """Command handler for comparing vectors."""
    compare_vectors(
        first_vector_id=args.first_vector_id,
        second_vector_id=args.second_vector_id,
        output_format=args.format,
        namespace=args.namespace
    )


# =============== Verify Vectors Command Functions ===============

def verify_id_format(vector_id: str, source_type: str, landmark_id: str) -> bool:
    """
    Verify that a vector ID follows the correct format.

    Args:
        vector_id: The vector ID to verify
        source_type: The source type (wikipedia or pdf)
        landmark_id: The landmark ID

    Returns:
        True if the ID format is valid, False otherwise
    """
    import re

    if source_type == "wikipedia":
        # Should match pattern: wiki-{article_title}-{landmark_id}-chunk-{chunk_index}
        match = re.match(WIKI_ID_PATTERN, vector_id)
        return match is not None and landmark_id in vector_id
    else:
        # Should match pattern: {landmark_id}-chunk-{chunk_index}
        match = re.match(PDF_ID_PATTERN, vector_id)
        return match is not None and vector_id.startswith(landmark_id)


def check_vector_has_embeddings(vector: Dict[str, Any]) -> bool:
    """
    Check if a vector has valid (non-zero) embeddings.

    Args:
        vector: The vector to check

    Returns:
        True if the vector has valid embeddings, False otherwise
    """
    import numpy as np

    # Get vector ID for logging
    vector_id = vector.get("id", "unknown")
    logger.debug(f"Checking embeddings for vector {vector_id}")

    # Check if the vector has the values field
    if "values" not in vector:
        logger.warning(f"Vector {vector_id} has no embeddings")
        return False

    values = vector.get("values", [])
    if not values:
        logger.warning(f"Vector {vector_id} has empty embeddings array")
        return False

    # Check if embeddings are all zeros
    if np.allclose(np.array(values), 0):
        logger.warning(f"Vector {vector_id} has all-zero embeddings")
        return False

    return True


def verify_article_title(vector_id: str, metadata: Dict[str, Any]) -> bool:
    """
    Verify that the article title in the vector ID matches the metadata.

    Args:
        vector_id: Vector ID
        metadata: Vector metadata

    Returns:
        True if the article title is valid or not applicable, False otherwise
    """
    if not vector_id.startswith("wiki-"):
        return True  # Not applicable for non-wiki vectors

    parts = vector_id.split("-")
    if len(parts) >= 4:
        # Format is wiki-{article_title}-LP-{id}-chunk-{index}
        article_title_from_id = parts[1].replace("_", " ")

        # Check if it matches the metadata
        if "article_title" in metadata:
            matches = metadata["article_title"] == article_title_from_id
            return bool(matches)  # Ensure we return a boolean

    return False


def verify_vectors(
    namespace: Optional[str] = None,
    limit: int = 100,
    prefix: Optional[str] = None,
    check_embeddings: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Verify the integrity of vectors in Pinecone.

    Performs comprehensive validation of vectors including:
    1. Vector ID format
    2. Required metadata fields
    3. Optionally checks embeddings

    Args:
        namespace: Optional Pinecone namespace to check
        limit: Maximum number of vectors to verify
        prefix: Optional prefix to filter vector IDs
        check_embeddings: Whether to check embeddings (requires more bandwidth)
        verbose: Whether to print detailed validation information

    Returns:
        Dictionary with verification results
    """
    try:
        # Initialize Pinecone client
        pinecone_db = PineconeDB()

        # Override namespace if provided
        if namespace is not None:
            pinecone_db.namespace = namespace
            logger.info(f"Using custom namespace: {namespace}")
        else:
            logger.info(f"Using default namespace: {pinecone_db.namespace}")

        # Query vectors
        logger.info(f"Querying up to {limit} vectors for verification")
        vectors = list_vectors(prefix=prefix, limit=limit, namespace=namespace)

        if not vectors:
            logger.warning("No vectors found to verify")
            return {"error": "No vectors found", "total": 0}

        # Print header
        if verbose:
            print("=" * 80)
            print("VERIFYING PINECONE VECTORS")
            print(f"Total vectors to verify: {len(vectors)}")
            print("=" * 80)

        # Track results as dictionaries with integer values
        results: Dict[str, Any] = {
            "total": len(vectors),
            "passed": 0,
            "failed": 0,
            "issues": [],
        }

        # Check each vector
        for vector_data in vectors:
            vector_id = vector_data.get("id", "unknown")
            metadata = vector_data.get("metadata", {})

            if verbose:
                print(f"\nVerifying vector: {vector_id}")

            # Track issues for this vector
            vector_issues = []

            # 1. Check required metadata fields
            missing_fields = []
            for field in REQUIRED_METADATA:
                if field not in metadata:
                    missing_fields.append(field)

            # Check Wiki-specific fields if this is a Wiki vector
            if vector_id.startswith("wiki-"):
                for field in REQUIRED_WIKI_METADATA:
                    if field not in metadata:
                        missing_fields.append(field)

            if missing_fields:
                issue = f"Missing required metadata fields: {missing_fields}"
                vector_issues.append(issue)
                if verbose:
                    print(f"  ✗ {issue}")
            elif verbose:
                print("  ✓ All required metadata fields present")

            # 2. Check ID format
            source_type = metadata.get("source_type", "unknown")
            landmark_id = metadata.get("landmark_id", "unknown")

            if not verify_id_format(vector_id, source_type, landmark_id):
                issue = f"Invalid ID format for {source_type} vector"
                vector_issues.append(issue)
                if verbose:
                    print(f"  ✗ {issue}")
            elif verbose:
                print(f"  ✓ Valid ID format for {source_type} vector")

            # 3. For Wikipedia vectors, check article title
            if vector_id.startswith("wiki-"):
                if not verify_article_title(vector_id, metadata):
                    issue = "Article title in ID does not match metadata"
                    vector_issues.append(issue)
                    if verbose:
                        print(f"  ✗ {issue}")
                elif verbose:
                    print("  ✓ Article title in ID matches metadata")

            # 4. Check embeddings if requested
            if check_embeddings:
                # We need to fetch the full vector with embeddings
                full_vector = fetch_vector(vector_id, namespace=namespace)
                if full_vector and check_vector_has_embeddings(full_vector):
                    if verbose:
                        print("  ✓ Valid embeddings found")
                else:
                    issue = "Missing or invalid embeddings"
                    vector_issues.append(issue)
                    if verbose:
                        print(f"  ✗ {issue}")

            # Update overall results
            if vector_issues:
                results["failed"] += 1
                results["issues"].append({
                    "vector_id": vector_id,
                    "issues": vector_issues
                })
            else:
                results["passed"] += 1

        # Print summary
        if verbose:
            print("\n" + "=" * 80)
            print("VERIFICATION SUMMARY")
            print(f"Total vectors: {results['total']}")
            print(f"Passed: {results['passed']}")
            print(f"Failed: {results['failed']}")
            print("=" * 80)

        return results

    except Exception as e:
        logger.error(f"Error verifying vectors: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "total": 0}


def verify_batch_command(args: argparse.Namespace) -> None:
    """Command handler for batch vector verification."""
    # Read vector IDs from file if provided
    if args.file:
        try:
            with open(args.file, 'r') as f:
                vector_ids = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(vector_ids)} vector IDs from {args.file}")
        except Exception as e:
            logger.error(f"Error reading vector IDs from file: {e}")
            return
    else:
        vector_ids = args.vector_ids

    # Verify the batch
    verify_batch(
        vector_ids=vector_ids,
        namespace=args.namespace,
        check_embeddings=args.check_embeddings,
        verbose=args.verbose
    )


def verify_batch(
    vector_ids: List[str],
    namespace: Optional[str] = None,
    check_embeddings: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Verify a batch of specific vectors by their IDs.

    Args:
        vector_ids: List of vector IDs to verify
        namespace: Optional Pinecone namespace to check
        check_embeddings: Whether to check embeddings (requires more bandwidth)
        verbose: Whether to print detailed validation information

    Returns:
        Dictionary with verification results
    """
    # Print header
    if verbose:
        print("=" * 80)
        print("BATCH VERIFICATION")
        print(f"Verifying {len(vector_ids)} vectors...")
        print("=" * 80)

    results: Dict[str, Any] = {
        "total": len(vector_ids),
        "found": 0,
        "not_found": 0,
        "valid": 0,
        "invalid": 0,
        "details": {}
    }

    for vector_id in vector_ids:
        if verbose:
            print(f"\nChecking vector: {vector_id}")

        # Fetch the vector
        vector = fetch_vector(vector_id, namespace=namespace)
        if not vector:
            results["not_found"] += 1
            results["details"][vector_id] = {"found": False}
            if verbose:
                print("  ✗ Vector not found")
            continue

        results["found"] += 1
        vector_result: Dict[str, Any] = {"found": True, "issues": []}

        # Validate the vector
        metadata = vector.get("metadata", {})
        source_type = metadata.get("source_type", "unknown")
        landmark_id = metadata.get("landmark_id", "unknown")

        # 1. Check required metadata fields
        missing_fields = []
        for field in REQUIRED_METADATA:
            if field not in metadata:
                missing_fields.append(field)

        # Check Wiki-specific fields if this is a Wiki vector
        if vector_id.startswith("wiki-"):
            for field in REQUIRED_WIKI_METADATA:
                if field not in metadata:
                    missing_fields.append(field)

        if missing_fields:
            vector_result["issues"].append(f"Missing fields: {missing_fields}")
            if verbose:
                print(f"  ✗ Missing required metadata fields: {missing_fields}")
        elif verbose:
            print("  ✓ All required metadata fields present")

        # 2. Check ID format
        if not verify_id_format(vector_id, source_type, landmark_id):
            vector_result["issues"].append("Invalid ID format")
            if verbose:
                print(f"  ✗ Invalid ID format for {source_type} vector")
        elif verbose:
            print(f"  ✓ Valid ID format for {source_type} vector")

        # 3. For Wikipedia vectors, check article title
        if vector_id.startswith("wiki-"):
            if not verify_article_title(vector_id, metadata):
                vector_result["issues"].append("Article title mismatch")
                if verbose:
                    print("  ✗ Article title in ID does not match metadata")
            elif verbose:
                print("  ✓ Article title in ID matches metadata")

        # 4. Check embeddings if requested
        if check_embeddings:
            if check_vector_has_embeddings(vector):
                if verbose:
                    print("  ✓ Valid embeddings found")
            else:
                vector_result["issues"].append("Invalid embeddings")
                if verbose:
                    print("  ✗ Missing or invalid embeddings")

        # Update results
        if vector_result["issues"]:
            results["invalid"] += 1
        else:
            results["valid"] += 1

        results["details"][vector_id] = vector_result

    # Print summary
    if verbose:
        print("\n" + "=" * 80)
        print("BATCH VERIFICATION SUMMARY")
        print(f"Total vectors: {results['total']}")
        print(f"Found: {results['found']}")
        print(f"Not found: {results['not_found']}")
        print(f"Valid: {results['valid']}")
        print(f"Invalid: {results['invalid']}")
        print("=" * 80)

    return results


def verify_vectors_command(args: argparse.Namespace) -> None:
    """Command handler for verifying vectors."""
    verify_vectors(
        namespace=args.namespace,
        limit=args.limit,
        prefix=args.prefix,
        check_embeddings=args.check_embeddings,
        verbose=args.verbose
    )


def batch_verify_command(args: argparse.Namespace) -> None:
    """Handle the batch verify command."""
    # Read vector IDs from file if provided
    if args.file:
        try:
            with open(args.file, 'r') as f:
                vector_ids = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(vector_ids)} vector IDs from {args.file}")
        except Exception as e:
            logger.error(f"Error reading vector IDs from file: {e}")
            return
    else:
        vector_ids = args.vector_ids

    # Verify the batch
    verify_batch(
        vector_ids=vector_ids,
        namespace=args.namespace,
        check_embeddings=args.check_embeddings,
        verbose=args.verbose
    )


# =============== Command Line Interface ===============

def fetch_command(args: argparse.Namespace) -> None:
    """Handle the fetch command."""
    fetch_vector(args.vector_id, args.pretty, args.namespace)


def check_landmark_command(args: argparse.Namespace) -> None:
    """Handle the check-landmark command."""
    check_landmark_vectors(args.landmark_id, args.verbose, args.namespace)


def list_vectors_command(args: argparse.Namespace) -> None:
    """Handle the list-vectors command."""
    list_vectors(
        prefix=args.prefix,
        limit=args.limit,
        pretty_print=args.pretty,
        namespace=args.namespace
    )


def setup_fetch_parser(subparsers: Any) -> None:
    """Set up the parser for the fetch command."""
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Fetch a specific vector by ID",
        description="Retrieve and display a specific vector by its ID"
    )
    fetch_parser.add_argument(
        "vector_id",
        type=str,
        help="ID of the vector to fetch (e.g., wiki-Wyckoff_House-LP-00001-chunk-0)",
    )
    fetch_parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        help="Format output with clear sections and truncated text",
    )
    fetch_parser.add_argument(
        "--namespace", "-n",
        type=str,
        help="Pinecone namespace to search in (defaults to configured namespace)",
    )
    fetch_parser.set_defaults(func=fetch_command)


def setup_check_landmark_parser(subparsers: Any) -> None:
    """Set up the parser for the check-landmark command."""
    check_parser = subparsers.add_parser(
        "check-landmark",
        help="Check all vectors for a specific landmark ID",
        description="Find and validate all vectors for a given landmark ID"
    )
    check_parser.add_argument(
        "landmark_id",
        help="The ID of the landmark to check (e.g., LP-00001)",
    )
    check_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print full metadata details",
    )
    check_parser.add_argument(
        "--namespace", "-n",
        type=str,
        help="Pinecone namespace to search in (defaults to configured namespace)",
    )
    check_parser.set_defaults(func=check_landmark_command)


def setup_list_vectors_parser(subparsers: Any) -> None:
    """Set up the parser for the list-vectors command."""
    list_parser = subparsers.add_parser(
        "list-vectors",
        help="List vectors in Pinecone with optional filtering",
        description="List and filter vectors stored in the Pinecone database"
    )
    list_parser.add_argument(
        "--prefix", "-p",
        type=str,
        help="Prefix to filter vector IDs",
    )
    list_parser.add_argument(
        "--limit", "-l",
        type=int,
        default=10,
        help="Maximum number of vectors to return (default: 10)",
    )
    list_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    list_parser.add_argument(
        "--namespace", "-n",
        type=str,
        help="Pinecone namespace to search in (defaults to configured namespace)",
    )
    list_parser.set_defaults(func=list_vectors_command)


def setup_validate_parser(subparsers: Any) -> None:
    """Set up the parser for the validate command."""
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a specific vector against requirements",
        description="Check if a vector has all required metadata fields"
    )
    validate_parser.add_argument(
        "vector_id",
        help="The ID of the vector to validate",
    )
    validate_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed validation information",
    )
    validate_parser.add_argument(
        "--namespace", "-n",
        type=str,
        help="Pinecone namespace to search in (defaults to configured namespace)",
    )
    validate_parser.set_defaults(func=validate_vector_command)


def setup_compare_vectors_parser(subparsers: Any) -> None:
    """Set up the parser for the compare-vectors command."""
    compare_parser = subparsers.add_parser(
        "compare-vectors",
        help="Compare metadata between two vectors",
        description="Compare metadata and optionally embeddings between two vectors"
    )
    compare_parser.add_argument(
        "first_vector_id",
        help="The ID of the first vector to compare",
    )
    compare_parser.add_argument(
        "second_vector_id",
        help="The ID of the second vector to compare",
    )
    compare_parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format for comparison results (default: text)",
    )
    compare_parser.add_argument(
        "--namespace", "-n",
        type=str,
        help="Pinecone namespace to search in (defaults to configured namespace)",
    )
    compare_parser.set_defaults(func=compare_vectors_command)


def setup_verify_vectors_parser(subparsers: Any) -> None:
    """Set up the parser for the verify-vectors command."""
    verify_parser = subparsers.add_parser(
        "verify-vectors",
        help="Verify the integrity of vectors in Pinecone",
        description="Perform comprehensive validation of vectors in Pinecone"
    )
    verify_parser.add_argument(
        "--namespace", "-n",
        type=str,
        help="Pinecone namespace to check (defaults to configured namespace)",
    )
    verify_parser.add_argument(
        "--limit", "-l",
        type=int,
        default=100,
        help="Maximum number of vectors to verify (default: 100)",
    )
    verify_parser.add_argument(
        "--prefix", "-p",
        type=str,
        help="Prefix to filter vector IDs",
    )
    verify_parser.add_argument(
        "--check-embeddings", "-e",
        action="store_true",
        help="Check vector embeddings (requires more bandwidth)",
    )
    verify_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed verification information",
    )
    verify_parser.set_defaults(func=verify_vectors_command)


def setup_verify_batch_parser(subparsers: Any) -> None:
    """Set up the parser for the verify-batch command."""
    batch_parser = subparsers.add_parser(
        "verify-batch",
        help="Verify a batch of specific vectors by their IDs",
        description="Verify multiple vectors by providing a list of vector IDs"
    )
    id_group = batch_parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument(
        "vector_ids",
        nargs="*",
        default=[],
        help="List of vector IDs to verify",
    )
    id_group.add_argument(
        "--file", "-f",
        type=str,
        help="File containing vector IDs (one per line)",
    )
    batch_parser.add_argument(
        "--namespace", "-n",
        type=str,
        help="Pinecone namespace to check (defaults to configured namespace)",
    )
    batch_parser.add_argument(
        "--check-embeddings", "-e",
        action="store_true",
        help="Check vector embeddings (requires more bandwidth)",
    )
    batch_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed verification information",
    )
    batch_parser.set_defaults(func=verify_batch_command)


def main() -> None:
    """
    Main entry point for the script.

    Parses command line arguments and dispatches to the appropriate function.
    """
    parser = argparse.ArgumentParser(
        description="Vector Utility - A comprehensive tool for working with Pinecone vectors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="Vector operations"
    )
    subparsers.required = True

    # Set up the individual command parsers
    setup_fetch_parser(subparsers)
    setup_check_landmark_parser(subparsers)
    setup_list_vectors_parser(subparsers)
    setup_validate_parser(subparsers)
    setup_compare_vectors_parser(subparsers)
    setup_verify_vectors_parser(subparsers)
    setup_verify_batch_parser(subparsers)

    # Parse arguments and call the appropriate function
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
