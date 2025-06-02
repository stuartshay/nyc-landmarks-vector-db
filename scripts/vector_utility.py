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
    # Fetch a specific vector by ID (will search across all available namespaces):
    python scripts/vector_utility.py fetch LP-00002-chunk-0 --pretty

    # Fetch a vector from a specific namespace:
    python scripts/vector_utility.py fetch wiki-Manhattan_Municipal_Building-LP-00079-chunk-0 --namespace landmarks --pretty

    # Check all vectors for a specific landmark:
    python scripts/vector_utility.py check-landmark LP-00001 --namespace landmarks --verbose

    # List up to 10 vectors starting with a specific prefix:
    python scripts/vector_utility.py list-vectors --prefix wiki-Manhattan --limit 10 --pretty --namespace landmarks

    # Validate a specific vector against metadata requirements:
    python scripts/vector_utility.py validate wiki-Wyckoff_House-LP-00001-chunk-0

    # Compare metadata between two vectors:
    python scripts/vector_utility.py compare-vectors wiki-Wyckoff_House-LP-00001-chunk-0 wiki-Wyckoff_House-LP-00001-chunk-1 --namespace landmarks

    # Verify vector integrity in Pinecone:
    python scripts/vector_utility.py verify-vectors --prefix wiki-Wyckoff --namespace landmarks --limit 20 --verbose
    python scripts/vector_utility.py verify-vectors --namespace landmarks --limit 20 --verbose

    # Verify a batch of specific vectors:
    python scripts/vector_utility.py verify-batch wiki-Wyckoff_House-LP-00001-chunk-0 wiki-Wyckoff_House-LP-00001-chunk-1
"""

import argparse
import json
from typing import Any, Dict, List, Optional, Tuple

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB
from nyc_landmarks.vectordb.vector_id_validator import VectorIDValidator

# Configure logging
logger = get_logger(__name__)

# =============== Constants ===============

# Required metadata fields for all vectors
REQUIRED_METADATA = ["landmark_id", "source_type", "chunk_index", "text"]

# Additional required metadata fields for Wikipedia vectors
REQUIRED_WIKI_METADATA = ["article_title", "article_url"]

# =============== Fetch Vector Command Functions ===============


def _print_vector_metadata(vector_data: Any, vector_id: str) -> None:
    """
    Print vector metadata in a structured format.

    Args:
        vector_data: Vector data object
        vector_id: ID of the vector
    """
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


# =============== Check Landmark Vectors Command Functions ===============


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
    # Three possible formats for building data:
    # 1. Primary format: "buildings" array containing building objects
    # 2. Legacy format: Indexed with "building_" prefix (building_0_bbl, building_1_bbl, etc.)
    # 3. Legacy format: Direct top-level fields (bbl, binNumber, latitude, etc.)

    # First check for the primary format - "buildings" array
    if "buildings" in metadata and isinstance(metadata["buildings"], list):
        buildings = metadata["buildings"]

        # If buildings array is empty, report no building data
        if not buildings:
            print("No building data found")
            return

        print(f"\nBuilding count: {len(buildings)}")

        # Process each building in the array
        for idx, building in enumerate(buildings):
            print(f"\nBuilding {idx + 1}:")

            # Handle both string and dictionary formatted buildings
            if isinstance(building, dict):
                # Display key information first
                if building.get("name"):
                    print(f"  Name: {building['name']}")
                if building.get("address"):
                    print(f"  Address: {building['address']}")
                if building.get("bbl"):
                    print(f"  BBL: {building['bbl']}")
                if building.get("binNumber"):
                    print(f"  BIN: {building['binNumber']}")

                # Display block and lot if present
                if building.get("block"):
                    print(f"  Block: {building['block']}")
                if building.get("lot"):
                    print(f"  Lot: {building['lot']}")

                # Display coordinates if available
                if building.get("latitude") and building.get("longitude"):
                    print(
                        f"  Coordinates: ({building['latitude']}, {building['longitude']})"
                    )

                # Display borough information
                if building.get("borough"):
                    print(f"  Borough: {building['borough']}")
                elif building.get("boroughId"):
                    borough_codes = {
                        "MN": "Manhattan",
                        "BK": "Brooklyn",
                        "QN": "Queens",
                        "BX": "Bronx",
                        "SI": "Staten Island",
                    }
                    borough = borough_codes.get(
                        building["boroughId"], building["boroughId"]
                    )
                    print(f"  Borough: {borough}")

                # Display other building characteristics
                if building.get("objectType"):
                    print(f"  Object Type: {building['objectType']}")
                if building.get("designatedDate"):
                    print(f"  Designated Date: {building['designatedDate']}")
                if building.get("historicDistrict"):
                    print(f"  Historic District: {building['historicDistrict']}")

                # Display any other fields not already shown
                other_fields = {
                    k: v
                    for k, v in building.items()
                    if k
                    not in [
                        "name",
                        "address",
                        "bbl",
                        "binNumber",
                        "block",
                        "lot",
                        "latitude",
                        "longitude",
                        "borough",
                        "boroughId",
                        "objectType",
                        "designatedDate",
                        "historicDistrict",
                    ]
                }
                if other_fields:
                    print("  Other fields:")
                    for k, v in sorted(other_fields.items()):
                        if v is not None and v != "":
                            print(f"    {k}: {v}")
            else:
                # Handle case where building might be a string or other simple type
                print(f"  Building data: {building}")
        return

    # Look for legacy prefixed building-related fields in the metadata
    building_fields = [k for k in metadata.keys() if k.startswith("building_")]

    # Check for legacy direct building data format
    building_indicators = ["bbl", "binNumber", "block", "lot", "latitude", "longitude"]
    has_direct_building_data = any(
        indicator in metadata for indicator in building_indicators
    )

    # If no building data in any format, return
    if not building_fields and not has_direct_building_data:
        print("No building data found")
        return

    print("\nWARNING: Using legacy building data format")

    # Process legacy prefixed building fields if present
    if building_fields:
        # Get the building count if available
        building_count = metadata.get("building_count", 0)
        print(f"Building count: {building_count}")

        # Group fields by building index
        building_indices = set()
        for field in building_fields:
            # Skip the building_count field
            if field == "building_count":
                continue

            # Extract building index from field name (e.g., building_0_bbl -> 0)
            parts = field.split("_")
            if len(parts) >= 3 and parts[1].isdigit():
                building_indices.add(int(parts[1]))

        # Process each building
        for idx in sorted(building_indices):
            print(f"\nBuilding {idx + 1}:")

            # Collect all fields for this building
            bldg_fields = {
                k.split("_", 2)[2]: metadata[k]
                for k in building_fields
                if k.startswith(f"building_{idx}_") and len(k.split("_", 2)) >= 3
            }

            # Display key information first if available
            if "address" in bldg_fields:
                print(f"  Address: {bldg_fields['address']}")
            if "bbl" in bldg_fields:
                print(f"  BBL: {bldg_fields['bbl']}")
            if "binNumber" in bldg_fields:
                print(f"  BIN: {bldg_fields['binNumber']}")
            if "name" in bldg_fields and bldg_fields["name"]:
                print(f"  Name: {bldg_fields['name']}")

            # Display coordinates if available
            if "latitude" in bldg_fields and "longitude" in bldg_fields:
                print(
                    f"  Coordinates: ({bldg_fields['latitude']}, {bldg_fields['longitude']})"
                )

            # Display other fields
            other_fields = {
                k: v
                for k, v in bldg_fields.items()
                if k
                not in ["address", "bbl", "binNumber", "name", "latitude", "longitude"]
            }
            if other_fields:
                print("  Other fields:")
                for k, v in sorted(other_fields.items()):
                    if v is not None and v != "":
                        print(f"    {k}: {v}")

    # Process legacy direct building data format if present
    elif has_direct_building_data:
        print("\nBuilding data (direct format):")

        # Display key building information
        if "address" in metadata:
            print(f"  Address: {metadata['address']}")
        elif "location" in metadata:
            print(f"  Location: {metadata['location']}")

        if "name" in metadata and metadata["name"]:
            print(f"  Name: {metadata['name']}")

        if "bbl" in metadata:
            print(f"  BBL: {metadata['bbl']}")
        if "binNumber" in metadata:
            print(f"  BIN: {metadata['binNumber']}")

        # Display block and lot if present
        if "block" in metadata:
            print(f"  Block: {metadata['block']}")
        if "lot" in metadata:
            print(f"  Lot: {metadata['lot']}")

        # Display coordinates if available
        if "latitude" in metadata and "longitude" in metadata:
            print(f"  Coordinates: ({metadata['latitude']}, {metadata['longitude']})")

        # Display borough information
        if "borough" in metadata:
            print(f"  Borough: {metadata['borough']}")
        elif "boroughId" in metadata:
            borough_codes = {
                "MN": "Manhattan",
                "BK": "Brooklyn",
                "QN": "Queens",
                "BX": "Bronx",
                "SI": "Staten Island",
            }
            borough = borough_codes.get(metadata["boroughId"], metadata["boroughId"])
            print(f"  Borough: {borough}")

        # Display building characteristics
        if "objectType" in metadata:
            print(f"  Object Type: {metadata['objectType']}")
        if "designatedDate" in metadata:
            print(f"  Designated Date: {metadata['designatedDate']}")
        if "historicDistrict" in metadata:
            print(f"  Historic District: {metadata['historicDistrict']}")
        if "style" in metadata:
            print(f"  Style: {metadata['style']}")
        if "architect" in metadata:
            print(f"  Architect: {metadata['architect']}")


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


# =============== List Vectors Command Functions ===============


def _analyze_vector_prefixes(
    matches: List[Any], sample_size: int = 100
) -> Tuple[Dict[str, int], Dict[str, str]]:
    """
    Analyze vector IDs to find common prefixes.

    Args:
        matches: List of match objects from Pinecone
        sample_size: Number of vectors to analyze

    Returns:
        Tuple of (prefix_distribution, id_examples)
    """
    prefix_distribution = {}
    id_examples = {}

    # Analyze up to sample_size vectors to find common prefixes
    actual_sample = min(len(matches), sample_size)
    for match in matches[:actual_sample]:
        match_id = getattr(match, "id", "")
        if match_id:
            parts = match_id.split("-")
            if len(parts) > 1:
                # Get the first part as common prefix
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

    return prefix_distribution, id_examples


def _print_filter_diagnostics(
    prefix: str, prefix_distribution: Dict[str, int], id_examples: Dict[str, str]
) -> None:
    """
    Print helpful diagnostics for prefix filtering.

    Args:
        prefix: The prefix that was used for filtering
        prefix_distribution: Dictionary of prefix counts
        id_examples: Dictionary of example IDs for each prefix
    """
    print("\nNo matches found with the specified prefix.")

    # Show the most common prefixes found in the data
    if prefix_distribution:
        print("\nCommon prefixes found in the data (with examples):")
        # Sort by frequency, most common first
        sorted_prefixes = sorted(
            prefix_distribution.items(), key=lambda x: x[1], reverse=True
        )

        # Show top 5 common prefixes
        for i, (common_prefix, count) in enumerate(sorted_prefixes[:5]):
            example = id_examples.get(common_prefix, "")
            print(
                f"  {i + 1}. '{common_prefix}' ({count} vectors) - Example: {example}"
            )

        print("\nSuggestions:")
        print("  - Check if your prefix matches exactly how vector IDs are stored")
        print("  - Try using one of the common prefixes shown above")
        print("  - Use a shorter prefix or check for case sensitivity")

        # Check if the prefix is close to any of the common prefixes
        close_matches = [
            p for p in prefix_distribution.keys() if prefix.lower() in p.lower()
        ]
        if close_matches:
            print("\nSimilar prefixes found that contain your search term:")
            for i, similar in enumerate(close_matches[:3]):
                print(f"  - '{similar}' (example: {id_examples.get(similar, '')})")


def filter_matches_by_prefix(matches: List[Any], prefix: Optional[str]) -> List[Any]:
    """
    Filter match results by prefix.

    Args:
        matches: List of match objects from Pinecone
        prefix: Optional prefix to filter vector IDs

    Returns:
        Filtered list of matches
    """
    # Return all matches if no prefix is specified
    if not prefix:
        return matches

    total_matches = len(matches)
    logger.info(f"Filtering {total_matches} matches with prefix: '{prefix}'")

    if total_matches == 0:
        print("No vectors retrieved from Pinecone to filter.")
        return []

    # Normalize the prefix for case-insensitive matching
    prefix_lower = prefix.lower()

    # Debug: print first few match IDs
    print(f"\nFirst {min(5, total_matches)} matches before filtering:")
    for i, match in enumerate(matches[:5]):
        match_id = getattr(match, "id", "Unknown")
        print(f"  {i + 1}. {match_id}")

    # Analyze prefixes for potential diagnostic information
    prefix_distribution, id_examples = _analyze_vector_prefixes(matches)

    # Filter matches by prefix (case insensitive)
    filtered_matches = [
        match
        for match in matches
        if getattr(match, "id", "")
        and getattr(match, "id", "").lower().startswith(prefix_lower)
    ]

    # Report results
    filtered_count = len(filtered_matches)
    print(
        f"\nFound {filtered_count} matches out of {total_matches} after filtering with prefix: '{prefix}'"
    )

    # Show examples or diagnostics based on results
    if filtered_matches:
        print("\nMatched vector IDs (first 5):")
        for i, match in enumerate(filtered_matches[:5]):
            match_id = getattr(match, "id", "Unknown")
            print(f"  {i + 1}. {match_id}")
    else:
        _print_filter_diagnostics(prefix, prefix_distribution, id_examples)

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


def _print_vector_details_pretty(matches_data: List[Dict[str, Any]]) -> None:
    """
    Print vector details in a pretty format with detailed metadata.

    Args:
        matches_data: List of vector match dictionaries
    """
    print("\n" + "=" * 80)
    print(f"VECTORS IN PINECONE ({len(matches_data)} found)")
    print("=" * 80)

    # Process each vector individually for better formatting
    for i, match_data in enumerate(matches_data):
        print(f"\nVector {i + 1}:")
        print("-" * 40)
        print(f"ID: {match_data.get('id', 'Unknown')}")
        print(f"Score: {match_data.get('score', 0.0)}")

        # Format metadata if present
        metadata = match_data.get("metadata", {})
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


def _print_vector_details_compact(matches_data: List[Dict[str, Any]]) -> None:
    """
    Print vector details in a compact format with key metadata only.

    Args:
        matches_data: List of vector match dictionaries
    """
    for i, match_data in enumerate(matches_data):
        print(f"\nVector {i + 1}:")
        print(f"  ID: {match_data.get('id', 'Unknown')}")
        print(f"  Score: {match_data.get('score', 0.0)}")

        # Print a few key metadata fields if available
        metadata = match_data.get("metadata", {})
        if metadata:
            landmark_id = metadata.get("landmark_id", "Unknown")
            source_type = metadata.get("source_type", "Unknown")
            chunk_index = metadata.get("chunk_index", "Unknown")
            print(f"  Landmark ID: {landmark_id}")
            print(f"  Source Type: {source_type}")
            print(f"  Chunk Index: {chunk_index}")


# =============== Validate Vector Command Functions ===============


def _print_validation_header(
    vector_id: str, metadata: Dict[str, Any], verbose: bool
) -> None:
    """
    Print header information for vector validation.

    Args:
        vector_id: ID of the vector being validated
        metadata: Vector metadata dictionary
        verbose: Whether to print detailed information
    """
    if verbose:
        print("\n" + "=" * 80)
        print(f"VALIDATING VECTOR: {vector_id}")
        print("=" * 80)
        print(f"\nMetadata keys: {list(metadata.keys()) if metadata else 'None'}")
        if metadata:
            print(f"\nFull metadata:\n{json.dumps(metadata, indent=2, default=str)}")


def _check_missing_fields(metadata: Dict[str, Any], vector_id: str) -> List[str]:
    """
    Check for missing required metadata fields.

    Args:
        metadata: Vector metadata dictionary
        vector_id: ID of the vector being validated

    Returns:
        List of missing field names
    """
    missing_fields = []

    # Check for common required fields
    for field in REQUIRED_METADATA:
        if field not in metadata:
            missing_fields.append(field)

    # Check for Wikipedia-specific fields if applicable
    if vector_id.startswith("wiki-"):
        for field in REQUIRED_WIKI_METADATA:
            if field not in metadata:
                missing_fields.append(field)

    return missing_fields


def _print_vector_details(
    metadata: Dict[str, Any], vector_id: str, verbose: bool
) -> None:
    """
    Print additional vector details for verbose output.

    Args:
        metadata: Vector metadata dictionary
        vector_id: ID of the vector
        verbose: Whether to print details
    """
    if not verbose:
        return

    source_type = metadata.get("source_type", "Unknown")
    chunk_index = metadata.get("chunk_index", "Unknown")
    landmark_id = metadata.get("landmark_id", "Unknown")

    print("\nVector Details:")
    print(f"  Source Type: {source_type}")
    print(f"  Chunk Index: {chunk_index}")
    print(f"  Landmark ID: {landmark_id}")

    # Use VectorIDValidator to properly detect Wikipedia vectors
    detected_source = VectorIDValidator.get_source_type(vector_id)
    if detected_source == "wikipedia":
        article_title = metadata.get("article_title", "Unknown")
        article_url = metadata.get("article_url", "Unknown")
        print(f"  Article Title: {article_title}")
        print(f"  Article URL: {article_url}")

        # Additional validation: check if vector ID format matches metadata
        if VectorIDValidator.validate_format(vector_id):
            print("  ✓ Vector ID format is valid")
        else:
            print("  ✗ Vector ID format is invalid")


def validate_vector_metadata(
    vector_data: Dict[str, Any], verbose: bool = False
) -> bool:
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

    # Print header information if verbose
    _print_validation_header(vector_id, metadata, verbose)

    # Validate vector ID format first
    is_valid_format = VectorIDValidator.validate_format(vector_id)
    if not is_valid_format:
        print(f"\nERROR: Vector {vector_id} has invalid ID format")
        return False

    # Check for missing required fields
    missing_fields = _check_missing_fields(metadata, vector_id)

    # Additional validation: Check if source type from ID matches metadata
    detected_source = VectorIDValidator.get_source_type(vector_id)
    metadata_source = metadata.get("source_type", "")

    source_mismatch = False
    if detected_source != "unknown" and metadata_source:
        if detected_source != metadata_source:
            print(
                f"\nWARNING: Source type mismatch - ID suggests '{detected_source}' but metadata says '{metadata_source}'"
            )
            source_mismatch = True

    # Print validation results
    if missing_fields:
        print(
            f"\nERROR: Vector {vector_id} is missing required fields: {missing_fields}"
        )
        return False
    else:
        print(f"\nVector {vector_id} has all required metadata fields")
        if verbose:
            print("  ✓ Vector ID format is valid")
            if not source_mismatch:
                print("  ✓ Source type consistency verified")

        # Print additional details if verbose
        _print_vector_details(metadata, vector_id, verbose)

        return True


def validate_vector_command(args: argparse.Namespace) -> None:
    """Command handler for validating a specific vector."""
    try:
        # Initialize PineconeDB client
        pinecone_db = PineconeDB()

        # Use "__default__" namespace when none is specified
        if args.namespace is None:
            namespace_to_use = "__default__"
            logger.info(f"No namespace specified, using: {namespace_to_use}")
        else:
            namespace_to_use = args.namespace
            logger.info(f"Using specified namespace: {namespace_to_use}")

        # Fetch vector directly using PineconeDB
        vector_data = pinecone_db.fetch_vector_by_id(args.vector_id, namespace_to_use)
        if not vector_data:
            print(f"ERROR: Vector with ID '{args.vector_id}' not found")
            return

        validate_vector_metadata(vector_data, verbose=args.verbose)

    except Exception as e:
        logger.error(f"Error validating vector: {e}")
        import traceback

        traceback.print_exc()


# =============== Compare Vectors Command Functions ===============


def _categorize_metadata_differences(
    all_keys: set, first_metadata: Dict[str, Any], second_metadata: Dict[str, Any]
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """
    Categorize metadata keys into different types of differences.

    Args:
        all_keys: Set of all keys from both metadata dictionaries
        first_metadata: Metadata from first vector
        second_metadata: Metadata from second vector

    Returns:
        Tuple of (differences, similarities, unique_to_first, unique_to_second)
    """
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

    return differences, similarities, unique_to_first, unique_to_second


def _print_text_comparison(
    differences: List[str],
    unique_to_first: List[str],
    unique_to_second: List[str],
    similarities: List[str],
    first_metadata: Dict[str, Any],
    second_metadata: Dict[str, Any],
) -> None:
    """
    Print comparison results in text format.

    Args:
        differences: List of keys with different values
        unique_to_first: List of keys unique to first vector
        unique_to_second: List of keys unique to second vector
        similarities: List of keys with identical values
        first_metadata: Metadata from first vector
        second_metadata: Metadata from second vector
    """
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

    # Print similar fields summary
    if similarities:
        print(f"\nIdentical Fields: {len(similarities)} fields match")


def _print_json_comparison(
    first_vector_id: str,
    second_vector_id: str,
    differences: List[str],
    unique_to_first: List[str],
    unique_to_second: List[str],
    similarities: List[str],
    first_metadata: Dict[str, Any],
    second_metadata: Dict[str, Any],
) -> None:
    """
    Print comparison results in JSON format.

    Args:
        first_vector_id: ID of first vector
        second_vector_id: ID of second vector
        differences: List of keys with different values
        unique_to_first: List of keys unique to first vector
        unique_to_second: List of keys unique to second vector
        similarities: List of keys with identical values
        first_metadata: Metadata from first vector
        second_metadata: Metadata from second vector
    """
    comparison = {
        "vectors": {"first": first_vector_id, "second": second_vector_id},
        "differences": {
            key: {
                "first": first_metadata.get(key),
                "second": second_metadata.get(key),
            }
            for key in differences
        },
        "unique_to_first": {key: first_metadata[key] for key in unique_to_first},
        "unique_to_second": {key: second_metadata[key] for key in unique_to_second},
        "identical_field_count": len(similarities),
    }
    print(json.dumps(comparison, indent=2, default=str))


def compare_vectors(
    first_vector_id: str,
    second_vector_id: str,
    output_format: str = "text",
    namespace: Optional[str] = None,
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
        # Initialize PineconeDB client
        pinecone_db = PineconeDB()

        # Use "__default__" namespace when none is specified
        if namespace is None:
            namespace_to_use = "__default__"
            logger.info(f"No namespace specified, using: {namespace_to_use}")
        else:
            namespace_to_use = namespace
            logger.info(f"Using specified namespace: {namespace_to_use}")

        # Fetch both vectors
        logger.info(f"Fetching first vector: {first_vector_id}")
        first_vector = pinecone_db.fetch_vector_by_id(first_vector_id, namespace_to_use)
        if not first_vector:
            print(f"ERROR: First vector with ID '{first_vector_id}' not found")
            return False

        logger.info(f"Fetching second vector: {second_vector_id}")
        second_vector = pinecone_db.fetch_vector_by_id(
            second_vector_id, namespace_to_use
        )
        if not second_vector:
            print(f"ERROR: Second vector with ID '{second_vector_id}' not found")
            return False

        # Extract metadata
        first_metadata = first_vector.get("metadata", {})
        second_metadata = second_vector.get("metadata", {})
        all_keys = set(first_metadata.keys()).union(set(second_metadata.keys()))

        # Print header
        print("=" * 80)
        print("COMPARING VECTORS")
        print(f"First:  {first_vector_id}")
        print(f"Second: {second_vector_id}")
        print("=" * 80)
        print("\nMETADATA COMPARISON:")
        print("-" * 40)

        # Categorize differences
        differences, similarities, unique_to_first, unique_to_second = (
            _categorize_metadata_differences(all_keys, first_metadata, second_metadata)
        )

        # Print results based on format
        if output_format == "text":
            _print_text_comparison(
                differences,
                unique_to_first,
                unique_to_second,
                similarities,
                first_metadata,
                second_metadata,
            )
            # Print summary
            print("\nSUMMARY:")
            print(f"  Fields with different values: {len(differences)}")
            print(f"  Fields unique to first vector: {len(unique_to_first)}")
            print(f"  Fields unique to second vector: {len(unique_to_second)}")
            print(f"  Fields with identical values: {len(similarities)}")
        elif output_format == "json":
            _print_json_comparison(
                first_vector_id,
                second_vector_id,
                differences,
                unique_to_first,
                unique_to_second,
                similarities,
                first_metadata,
                second_metadata,
            )

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
        namespace=args.namespace,
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
    # Use VectorIDValidator to check format
    if not VectorIDValidator.validate_format(vector_id):
        return False

    # Check if the source type matches what's expected
    detected_source = VectorIDValidator.get_source_type(vector_id)
    if source_type == "wikipedia" and detected_source != "wikipedia":
        return False
    elif source_type == "pdf" and detected_source != "pdf":
        return False

    # Check if landmark_id is present in the vector_id
    return landmark_id in vector_id


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


def _check_required_metadata_fields(
    vector_id: str, metadata: Dict[str, Any]
) -> List[str]:
    """
    Check for missing required metadata fields.

    Args:
        vector_id: Vector ID
        metadata: Vector metadata

    Returns:
        List of missing field names
    """
    missing_fields = []

    # Check basic required fields
    for field in REQUIRED_METADATA:
        if field not in metadata:
            missing_fields.append(field)

    # Check Wiki-specific fields if this is a Wiki vector
    if vector_id.startswith("wiki-"):
        for field in REQUIRED_WIKI_METADATA:
            if field not in metadata:
                missing_fields.append(field)

    return missing_fields


def _check_id_format(
    vector_id: str, metadata: Dict[str, Any], verbose: bool
) -> Optional[str]:
    """Check vector ID format and return error message if invalid."""
    source_type = metadata.get("source_type", "unknown")
    landmark_id = metadata.get("landmark_id", "unknown")

    if not verify_id_format(vector_id, source_type, landmark_id):
        if verbose:
            print(f"  ✗ Invalid ID format for {source_type} vector")
        return f"Invalid ID format for {source_type} vector"
    elif verbose:
        print(f"  ✓ Valid ID format for {source_type} vector")
    return None


def _check_article_title(
    vector_id: str, metadata: Dict[str, Any], verbose: bool
) -> Optional[str]:
    """Check article title for Wikipedia vectors and return error message if invalid."""
    if not vector_id.startswith("wiki-"):
        return None

    if not verify_article_title(vector_id, metadata):
        if verbose:
            print("  ✗ Article title in ID does not match metadata")
        return "Article title in ID does not match metadata"
    elif verbose:
        print("  ✓ Article title in ID matches metadata")
    return None


def _check_embeddings(
    vector_id: str, namespace: Optional[str], verbose: bool
) -> Optional[str]:
    """Check vector embeddings and return error message if invalid."""
    # Initialize PineconeDB client
    pinecone_db = PineconeDB()

    # Use "__default__" namespace when none is specified
    if namespace is None:
        namespace_to_use = "__default__"
        logger.info(f"No namespace specified, using: {namespace_to_use}")
    else:
        namespace_to_use = namespace
        logger.info(f"Using specified namespace: {namespace_to_use}")

    full_vector = pinecone_db.fetch_vector_by_id(vector_id, namespace_to_use)
    if full_vector and check_vector_has_embeddings(full_vector):
        if verbose:
            print("  ✓ Valid embeddings found")
        return None
    else:
        if verbose:
            print("  ✗ Missing or invalid embeddings")
        return "Missing or invalid embeddings"


def _verify_single_vector(
    vector_data: Dict[str, Any],
    check_embeddings: bool,
    namespace: Optional[str],
    verbose: bool,
) -> List[str]:
    """
    Verify a single vector and return list of issues.

    Args:
        vector_data: Vector data to verify
        check_embeddings: Whether to check embeddings
        namespace: Namespace for fetching full vector data
        verbose: Whether to print verbose output

    Returns:
        List of issues found with the vector
    """
    vector_id = vector_data.get("id", "unknown")
    metadata = vector_data.get("metadata", {})
    vector_issues = []

    if verbose:
        print(f"\nVerifying vector: {vector_id}")

    # 1. Check required metadata fields
    missing_fields = _check_required_metadata_fields(vector_id, metadata)
    if missing_fields:
        issue = f"Missing required metadata fields: {missing_fields}"
        vector_issues.append(issue)
        if verbose:
            print(f"  ✗ {issue}")
    elif verbose:
        print("  ✓ All required metadata fields present")

    # 2. Check ID format
    id_issue = _check_id_format(vector_id, metadata, verbose)
    if id_issue:
        vector_issues.append(id_issue)

    # 3. Check article title for Wikipedia vectors
    title_issue = _check_article_title(vector_id, metadata, verbose)
    if title_issue:
        vector_issues.append(title_issue)

    # 4. Check embeddings if requested
    if check_embeddings:
        embedding_issue = _check_embeddings(vector_id, namespace, verbose)
        if embedding_issue:
            vector_issues.append(embedding_issue)

    return vector_issues


def verify_vectors(
    namespace: Optional[str] = None,
    limit: int = 100,
    prefix: Optional[str] = None,
    check_embeddings: bool = False,
    verbose: bool = False,
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

        # Use "__default__" namespace when none is specified
        if namespace is None:
            namespace_to_use = "__default__"
            logger.info(f"No namespace specified, using: {namespace_to_use}")
        else:
            namespace_to_use = namespace
            logger.info(f"Using specified namespace: {namespace_to_use}")

        # Query vectors
        logger.info(f"Querying up to {limit} vectors for verification")
        matches = pinecone_db.list_vectors(
            limit=limit,
            id_prefix=prefix,
            namespace_override=namespace_to_use,
            include_values=False,
        )

        if not matches:
            logger.warning("No vectors found to verify")
            return {"error": "No vectors found", "total": 0}

        # Convert matches to the expected format
        vectors = []
        for match in matches:
            vector_dict = {
                "id": match.get("id", "Unknown"),
                "score": match.get("score", 0.0),
                "metadata": match.get("metadata", {}),
            }
            vectors.append(vector_dict)

        # Print header
        if verbose:
            print("=" * 80)
            print("VERIFYING PINECONE VECTORS")
            print(f"Total vectors to verify: {len(vectors)}")
            print("=" * 80)

        # Initialize results tracking
        results: Dict[str, Any] = {
            "total": len(vectors),
            "passed": 0,
            "failed": 0,
            "issues": [],
        }

        # Check each vector
        for vector_data in vectors:
            vector_id = vector_data.get("id", "unknown")
            vector_issues = _verify_single_vector(
                vector_data, check_embeddings, namespace, verbose
            )

            # Update overall results
            if vector_issues:
                results["failed"] += 1
                results["issues"].append(
                    {"vector_id": vector_id, "issues": vector_issues}
                )
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
            with open(args.file, "r") as f:
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
        verbose=args.verbose,
    )


def _check_batch_metadata_fields(
    vector_id: str, metadata: Dict[str, Any], verbose: bool
) -> Optional[str]:
    """Check metadata fields for batch verification."""
    missing_fields = _check_required_metadata_fields(vector_id, metadata)
    if missing_fields:
        if verbose:
            print(f"  ✗ Missing required metadata fields: {missing_fields}")
        return f"Missing fields: {missing_fields}"
    elif verbose:
        print("  ✓ All required metadata fields present")
    return None


def _check_batch_embeddings(vector: Dict[str, Any], verbose: bool) -> Optional[str]:
    """Check embeddings for batch verification."""
    if check_vector_has_embeddings(vector):
        if verbose:
            print("  ✓ Valid embeddings found")
        return None
    else:
        if verbose:
            print("  ✗ Missing or invalid embeddings")
        return "Invalid embeddings"


def _verify_single_vector_in_batch(
    vector_id: str, namespace: Optional[str], check_embeddings: bool, verbose: bool
) -> Dict[str, Any]:
    """
    Verify a single vector in batch processing.

    Args:
        vector_id: ID of vector to verify
        namespace: Optional namespace
        check_embeddings: Whether to check embeddings
        verbose: Whether to print verbose output

    Returns:
        Dictionary with verification results for the vector
    """
    if verbose:
        print(f"\nChecking vector: {vector_id}")

    # Initialize PineconeDB client
    pinecone_db = PineconeDB()

    # Use "__default__" namespace when none is specified
    if namespace is None:
        namespace_to_use = "__default__"
        logger.info(f"No namespace specified, using: {namespace_to_use}")
    else:
        namespace_to_use = namespace
        logger.info(f"Using specified namespace: {namespace_to_use}")

    # Fetch the vector
    vector = pinecone_db.fetch_vector_by_id(vector_id, namespace_to_use)
    if not vector:
        if verbose:
            print("  ✗ Vector not found")
        return {"found": False}

    # Initialize result tracking
    vector_result: Dict[str, Any] = {"found": True, "issues": []}
    metadata = vector.get("metadata", {})

    # Check required metadata fields
    metadata_issue = _check_batch_metadata_fields(vector_id, metadata, verbose)
    if metadata_issue:
        vector_result["issues"].append(metadata_issue)

    # Check ID format
    id_issue = _check_id_format(vector_id, metadata, verbose)
    if id_issue:
        vector_result["issues"].append("Invalid ID format")

    # Check article title for Wikipedia vectors
    title_issue = _check_article_title(vector_id, metadata, verbose)
    if title_issue:
        vector_result["issues"].append("Article title mismatch")

    # Check embeddings if requested
    if check_embeddings:
        embedding_issue = _check_batch_embeddings(vector, verbose)
        if embedding_issue:
            vector_result["issues"].append(embedding_issue)

    return vector_result


def verify_batch(
    vector_ids: List[str],
    namespace: Optional[str] = None,
    check_embeddings: bool = False,
    verbose: bool = False,
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
    # Use "__default__" namespace when none is specified
    if namespace is None:
        namespace_to_use = "__default__"
        if verbose:
            print(f"No namespace specified, using: {namespace_to_use}")
    else:
        namespace_to_use = namespace
        if verbose:
            print(f"Using specified namespace: {namespace_to_use}")

    # Print header
    if verbose:
        print("=" * 80)
        print("BATCH VERIFICATION")
        print(f"Verifying {len(vector_ids)} vectors...")
        print("=" * 80)

    # Initialize results tracking
    results: Dict[str, Any] = {
        "total": len(vector_ids),
        "found": 0,
        "not_found": 0,
        "valid": 0,
        "invalid": 0,
        "details": {},
    }

    # Process each vector
    for vector_id in vector_ids:
        vector_result = _verify_single_vector_in_batch(
            vector_id, namespace_to_use, check_embeddings, verbose
        )

        # Update aggregate results
        if not vector_result["found"]:
            results["not_found"] += 1
        else:
            results["found"] += 1
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
        verbose=args.verbose,
    )


def batch_verify_command(args: argparse.Namespace) -> None:
    """Handle the batch verify command."""
    # Read vector IDs from file if provided
    if args.file:
        try:
            with open(args.file, "r") as f:
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
        verbose=args.verbose,
    )


# =============== Command Line Interface ===============


def _fetch_from_specific_namespace(
    pinecone_db: PineconeDB, vector_id: str, namespace: str
) -> Optional[Dict[str, Any]]:
    """
    Fetch a vector from a specific namespace.

    Args:
        pinecone_db: The PineconeDB instance
        vector_id: The ID of the vector to fetch
        namespace: The namespace to fetch from

    Returns:
        Vector data dictionary or None if not found
    """
    # Skip "__default__" namespace which causes API errors
    if namespace == "__default__":
        logger.info("Skipping '__default__' namespace due to API limitations")
        return None
    logger.info(f"Trying namespace: {namespace}")
    try:
        temp_vector = pinecone_db.fetch_vector_by_id(vector_id, namespace)
        if temp_vector:
            logger.info(f"Found vector in namespace: {namespace}")
            return temp_vector
        return None
    except Exception as e:
        logger.warning(f"Error fetching from namespace {namespace}: {e}")
        return None


def _search_all_namespaces(
    pinecone_db: PineconeDB, vector_id: str
) -> Optional[Dict[str, Any]]:
    """
    Search for a vector across all available namespaces.

    Args:
        pinecone_db: The PineconeDB instance
        vector_id: The ID of the vector to fetch

    Returns:
        Vector data dictionary or None if not found in any namespace
    """
    # Get index statistics to find available namespaces
    logger.info("No namespace specified, checking all available namespaces")
    stats = pinecone_db.get_index_stats()
    namespaces = stats.get("namespaces", {})

    if not namespaces:
        logger.info("No namespaces found, trying with default namespace")
        return pinecone_db.fetch_vector_by_id(vector_id, None)

    logger.info(f"Found {len(namespaces)} namespaces: {', '.join(namespaces.keys())}")

    # Try each namespace until we find the vector
    for namespace_name in namespaces.keys():
        vector_data = _fetch_from_specific_namespace(
            pinecone_db, vector_id, namespace_name
        )
        if vector_data:
            return vector_data
    return None


class VectorData:
    """Mock vector object for compatibility with existing print functions."""

    def __init__(self, data_dict: Dict[str, Any]):
        """Initialize with data from dictionary."""
        self.id = data_dict.get("id", "")
        self.values = data_dict.get("values", [])
        self.metadata = data_dict.get("metadata", {})


def fetch_command(args: argparse.Namespace) -> None:
    """Handle the fetch command."""
    try:
        # Initialize PineconeDB client
        pinecone_db = PineconeDB()

        # Handle namespace parameter
        if args.namespace is None:
            # Try to find the vector in any available namespace
            vector_data_dict = _search_all_namespaces(pinecone_db, args.vector_id)
        else:
            # Use specified namespace
            logger.info(f"Using specified namespace: {args.namespace}")
            vector_data_dict = pinecone_db.fetch_vector_by_id(
                args.vector_id, args.namespace
            )

        if vector_data_dict is None:
            logger.error(f"Vector with ID '{args.vector_id}' not found in Pinecone")
            return

        # Create a mock vector object and display results
        vector_data = VectorData(vector_data_dict)
        # Print formatted output if requested
        if args.pretty:
            _print_vector_metadata(vector_data, args.vector_id)
        else:
            print(vector_data_dict)

    except Exception as e:
        logger.error(f"Error fetching vector: {e}")
        return


def check_landmark_command(args: argparse.Namespace) -> None:
    """Handle the check-landmark command."""
    try:
        # Initialize PineconeDB client
        pinecone_db = PineconeDB()

        # Use "__default__" namespace when none is specified
        if args.namespace is None:
            namespace_to_use = "__default__"
            logger.info(f"No namespace specified, using: {namespace_to_use}")
        else:
            namespace_to_use = args.namespace
            logger.info(f"Using specified namespace: {namespace_to_use}")

        print(f"Checking vectors for landmark: {args.landmark_id}")

        # Get vector matches from Pinecone using PineconeDB.query_vectors()
        matches = pinecone_db.query_vectors(
            query_vector=None,  # Listing operation
            top_k=100,
            landmark_id=args.landmark_id,
            namespace_override=namespace_to_use,
            include_values=False,
        )

        print(f"Found {len(matches)} vectors for landmark {args.landmark_id}")
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
            display_metadata(metadata, args.verbose)

    except Exception as e:
        logger.error(f"Error checking landmark vectors: {e}")
        import traceback

        traceback.print_exc()


def list_vectors_command(args: argparse.Namespace) -> None:
    """Handle the list-vectors command."""
    try:
        # Initialize Pinecone client
        pinecone_db = PineconeDB()

        # Use "__default__" namespace when none is specified
        if args.namespace is None:
            namespace_to_use = "__default__"
            logger.info(f"No namespace specified, using: {namespace_to_use}")
        else:
            namespace_to_use = args.namespace
            logger.info(f"Using specified namespace: {namespace_to_use}")

        logger.info(
            f"Listing vectors with prefix: '{args.prefix if args.prefix else 'all'}'"
        )

        # Display query information
        print("\nQuerying Pinecone database for vectors")
        print(f"  Namespace: {namespace_to_use}")
        print(f"  Prefix filter: {args.prefix if args.prefix else 'None'}")
        print(f"  Result limit: {args.limit}")

        # Query the Pinecone index using PineconeDB.list_vectors()
        matches = pinecone_db.list_vectors(
            limit=args.limit,
            id_prefix=args.prefix,
            namespace_override=namespace_to_use,
            include_values=False,
        )

        # Handle the result safely
        if not matches:
            logger.warning("No vectors found in Pinecone")
            print("\nNo vectors found in the database.")
            return

        print(f"\nFound {len(matches)} matches")

        # Convert matches to the expected format for display
        matches_data = []
        for match in matches:
            match_dict = {
                "id": match.get("id", "Unknown"),
                "score": match.get("score", 0.0),
                "metadata": match.get("metadata", {}),
            }
            matches_data.append(match_dict)

        # Print the results in the appropriate format
        if args.pretty:
            _print_vector_details_pretty(matches_data)
        else:
            _print_vector_details_compact(matches_data)

    except Exception as e:
        logger.error(f"Error listing vectors: {e}")
        print(f"\nError: Failed to list vectors - {str(e)}")
        import traceback

        traceback.print_exc()


def setup_fetch_parser(subparsers: Any) -> None:
    """Set up the parser for the fetch command."""
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Fetch a specific vector by ID",
        description="Retrieve and display a specific vector by its ID",
    )
    fetch_parser.add_argument(
        "vector_id",
        type=str,
        help="ID of the vector to fetch (e.g., wiki-Wyckoff_House-LP-00001-chunk-0)",
    )
    fetch_parser.add_argument(
        "--pretty",
        "-p",
        action="store_true",
        help="Format output with clear sections and truncated text",
    )
    fetch_parser.add_argument(
        "--namespace",
        "-n",
        type=str,
        help="Pinecone namespace to search in (if not specified, will search all available namespaces)",
    )
    fetch_parser.set_defaults(func=fetch_command)


def setup_check_landmark_parser(subparsers: Any) -> None:
    """Set up the parser for the check-landmark command."""
    check_parser = subparsers.add_parser(
        "check-landmark",
        help="Check all vectors for a specific landmark ID",
        description="Find and validate all vectors for a given landmark ID",
    )
    check_parser.add_argument(
        "landmark_id",
        help="The ID of the landmark to check (e.g., LP-00001)",
    )
    check_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print full metadata details",
    )
    check_parser.add_argument(
        "--namespace",
        "-n",
        type=str,
        help='Pinecone namespace to search in (if not specified, "__default__" will be used)',
    )
    check_parser.set_defaults(func=check_landmark_command)


def setup_list_vectors_parser(subparsers: Any) -> None:
    """Set up the parser for the list-vectors command."""
    list_parser = subparsers.add_parser(
        "list-vectors",
        help="List vectors in Pinecone with optional filtering",
        description="List and filter vectors stored in the Pinecone database",
    )
    list_parser.add_argument(
        "--prefix",
        "-p",
        type=str,
        help="Prefix to filter vector IDs",
    )
    list_parser.add_argument(
        "--limit",
        "-l",
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
        "--namespace",
        "-n",
        type=str,
        help='Pinecone namespace to search in (if not specified, "__default__" will be used)',
    )
    list_parser.set_defaults(func=list_vectors_command)


def setup_validate_parser(subparsers: Any) -> None:
    """Set up the parser for the validate command."""
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a specific vector against requirements",
        description="Check if a vector has all required metadata fields",
    )
    validate_parser.add_argument(
        "vector_id",
        help="The ID of the vector to validate",
    )
    validate_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed validation information",
    )
    validate_parser.add_argument(
        "--namespace",
        "-n",
        type=str,
        help='Pinecone namespace to search in (if not specified, "__default__" will be used)',
    )
    validate_parser.set_defaults(func=validate_vector_command)


def setup_compare_vectors_parser(subparsers: Any) -> None:
    """Set up the parser for the compare-vectors command."""
    compare_parser = subparsers.add_parser(
        "compare-vectors",
        help="Compare metadata between two vectors",
        description="Compare metadata and optionally embeddings between two vectors",
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
        "--format",
        "-f",
        choices=["text", "json"],
        default="text",
        help="Output format for comparison results (default: text)",
    )
    compare_parser.add_argument(
        "--namespace",
        "-n",
        type=str,
        help='Pinecone namespace to search in (if not specified, "__default__" will be used)',
    )
    compare_parser.set_defaults(func=compare_vectors_command)


def setup_verify_vectors_parser(subparsers: Any) -> None:
    """Set up the parser for the verify-vectors command."""
    verify_parser = subparsers.add_parser(
        "verify-vectors",
        help="Verify the integrity of vectors in Pinecone",
        description="Perform comprehensive validation of vectors in Pinecone",
    )
    verify_parser.add_argument(
        "--namespace",
        "-n",
        type=str,
        help='Pinecone namespace to check (if not specified, "__default__" will be used)',
    )
    verify_parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=100,
        help="Maximum number of vectors to verify (default: 100)",
    )
    verify_parser.add_argument(
        "--prefix",
        "-p",
        type=str,
        help="Prefix to filter vector IDs",
    )
    verify_parser.add_argument(
        "--check-embeddings",
        "-e",
        action="store_true",
        help="Check vector embeddings (requires more bandwidth)",
    )
    verify_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed verification information",
    )
    verify_parser.set_defaults(func=verify_vectors_command)


def setup_verify_batch_parser(subparsers: Any) -> None:
    """Set up the parser for the verify-batch command."""
    batch_parser = subparsers.add_parser(
        "verify-batch",
        help="Verify a batch of specific vectors by their IDs",
        description="Verify multiple vectors by providing a list of vector IDs",
    )
    id_group = batch_parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument(
        "vector_ids",
        nargs="*",
        default=[],
        help="List of vector IDs to verify",
    )
    id_group.add_argument(
        "--file",
        "-f",
        type=str,
        help="File containing vector IDs (one per line)",
    )
    batch_parser.add_argument(
        "--namespace",
        "-n",
        type=str,
        help='Pinecone namespace to check (if not specified, "__default__" will be used)',
    )
    batch_parser.add_argument(
        "--check-embeddings",
        "-e",
        action="store_true",
        help="Check vector embeddings (requires more bandwidth)",
    )
    batch_parser.add_argument(
        "--verbose",
        "-v",
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
        title="commands", dest="command", help="Vector operations"
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
