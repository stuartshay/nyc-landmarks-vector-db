#!/usr/bin/env python3
"""
Verify Metadata Consistency

This script verifies the consistency between CoreDataStore API metadata and Pinecone DB metadata.
It checks if the landmark_id format and other metadata fields match correctly.
"""

import json
import sys
from pathlib import Path
from pprint import pprint
from typing import Any, Dict

# Add the project root to the path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Import project modules
from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.enhanced_metadata import get_metadata_collector
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logger
logger = get_logger(name="verify_metadata_consistency")


def verify_landmark_metadata(landmark_id: str) -> Dict[str, Any]:
    """
    Verify the consistency between CoreDataStore API and Pinecone metadata for a landmark.

    Args:
        landmark_id: The landmark ID to verify (e.g., 'LP-00009')

    Returns:
        Dict with verification results
    """
    results = {
        "api_metadata": None,
        "enhanced_metadata": None,
        "pinecone_metadata": None,
        "matches_found": 0,
        "matching_fields": [],
        "mismatched_fields": [],
        "missing_fields": [],
        "extra_fields": [],
        "success": False,
        "issues": [],
    }

    try:
        # Step 1: Get metadata from CoreDataStore API
        db_client = get_db_client()
        api_metadata = db_client.get_landmark_metadata(landmark_id)

        if not api_metadata:
            results["issues"].append(
                f"No API metadata found for landmark {landmark_id}"
            )
            return results

        results["api_metadata"] = api_metadata

        # Step 2: Get enhanced metadata
        metadata_collector = get_metadata_collector()
        enhanced_metadata = metadata_collector.collect_landmark_metadata(landmark_id)
        results["enhanced_metadata"] = enhanced_metadata

        # Step 3: Get Pinecone metadata
        pinecone_db = PineconeDB()

        # Generate a query embedding
        embedding_generator = EmbeddingGenerator()
        query_text = api_metadata.get("name", landmark_id)
        query_vector = embedding_generator.generate_embedding(query_text)

        # Use the fixed ID format to directly access the vector
        # This will be more reliable than semantic search since we now use deterministic IDs
        fixed_id = f"{landmark_id}-chunk-0"  # Try to get the first chunk
        logger.info(f"Attempting to find vector with fixed ID pattern: {fixed_id}")

        # First try with the landmark_id filter since that's most reliable
        filter_dict = {"landmark_id": landmark_id}
        logger.info(f"Searching Pinecone with filter: {filter_dict}")
        results_exact = pinecone_db.query_vectors(
            query_vector=query_vector, top_k=5, filter_dict=filter_dict
        )

        if results_exact:
            logger.info(f"Found {len(results_exact)} vectors using exact format")
            results["matches_found"] = len(results_exact)
            pinecone_metadata = results_exact[0].get("metadata", {})
            results["pinecone_metadata"] = pinecone_metadata
        else:
            # Try without LP- prefix
            logger.info("No matches found with exact format, trying without LP- prefix")
            landmark_id_no_prefix = landmark_id.replace("LP-", "")
            filter_dict = {"landmark_id": landmark_id_no_prefix}

            results_no_prefix = pinecone_db.query_vectors(
                query_vector=query_vector, top_k=5, filter_dict=filter_dict
            )

            if results_no_prefix:
                logger.info(
                    f"Found {len(results_no_prefix)} vectors using no-prefix format"
                )
                results["matches_found"] = len(results_no_prefix)
                pinecone_metadata = results_no_prefix[0].get("metadata", {})
                results["pinecone_metadata"] = pinecone_metadata
                results["issues"].append(
                    f"Using no-prefix format: '{landmark_id_no_prefix}' instead of '{landmark_id}'"
                )
            else:
                # Try semantic search without filters
                logger.info(
                    "No matches found with either format, trying semantic search"
                )
                results_semantic = pinecone_db.query_vectors(
                    query_vector=query_vector, top_k=10, filter_dict=None
                )

                if results_semantic:
                    # See if any of the results match our landmark_id
                    for result in results_semantic:
                        if (
                            "metadata" in result
                            and result["metadata"].get("landmark_id") == landmark_id
                        ):
                            logger.info("Found match through semantic search")
                            results["matches_found"] = 1
                            pinecone_metadata = result.get("metadata", {})
                            results["pinecone_metadata"] = pinecone_metadata
                            results["issues"].append(
                                "Metadata filter not working, but found through semantic search"
                            )
                            break

                    if not results["pinecone_metadata"]:
                        logger.warning(
                            "No matching vectors found through semantic search"
                        )
                        results["issues"].append(
                            "No matching vectors found through semantic search"
                        )
                else:
                    logger.warning("No vectors found in index")
                    results["issues"].append("No vectors found in index")

        # Step 4: Compare metadata if we found it
        if results["pinecone_metadata"]:
            # For a fair comparison, only check fields that should be in both
            common_fields = set(enhanced_metadata.keys()).intersection(
                set(results["pinecone_metadata"].keys())
            )

            for field in common_fields:
                enhanced_value = enhanced_metadata[field]
                pinecone_value = results["pinecone_metadata"][field]

                if enhanced_value == pinecone_value:
                    results["matching_fields"].append(field)
                else:
                    results["mismatched_fields"].append(
                        {
                            "field": field,
                            "enhanced": enhanced_value,
                            "pinecone": pinecone_value,
                        }
                    )

            # Check for fields missing from Pinecone
            for field in enhanced_metadata:
                if field not in results["pinecone_metadata"]:
                    results["missing_fields"].append(field)

            # Check for extra fields in Pinecone
            for field in results["pinecone_metadata"]:
                if field not in enhanced_metadata:
                    results["extra_fields"].append(field)

            # Determine overall success
            results["success"] = (
                len(results["mismatched_fields"]) == 0
                and len(results["missing_fields"]) == 0
            )

        return results

    except Exception as e:
        import traceback

        logger.error(f"Error verifying metadata: {e}")
        logger.error(traceback.format_exc())
        results["issues"].append(f"Error: {str(e)}")
        return results


def print_results(results: Dict[str, Any]) -> None:
    """Print verification results in a readable format."""
    print("\n----- METADATA VERIFICATION RESULTS -----\n")

    if results["api_metadata"]:
        print("API METADATA:")
        pprint(results["api_metadata"])
        print()

    if results["enhanced_metadata"]:
        print("ENHANCED METADATA:")
        pprint(results["enhanced_metadata"])
        print()

    if results["pinecone_metadata"]:
        print("PINECONE METADATA:")
        pprint(results["pinecone_metadata"])
        print()

    print(f"MATCHES FOUND: {results['matches_found']}")

    if results["matching_fields"]:
        print("\nMATCHING FIELDS:")
        for field in results["matching_fields"]:
            print(f"  ✓ {field}")

    if results["mismatched_fields"]:
        print("\nMISMATCHED FIELDS:")
        for mismatch in results["mismatched_fields"]:
            print(f"  ✗ {mismatch['field']}:")
            print(f"     Enhanced: {mismatch['enhanced']}")
            print(f"     Pinecone: {mismatch['pinecone']}")

    if results["missing_fields"]:
        print("\nMISSING FROM PINECONE:")
        for field in results["missing_fields"]:
            print(f"  - {field}")

    if results["extra_fields"]:
        print("\nEXTRA FIELDS IN PINECONE:")
        for field in results["extra_fields"]:
            print(f"  + {field}")

    if results["issues"]:
        print("\nISSUES:")
        for issue in results["issues"]:
            print(f"  ! {issue}")

    print("\nOVERALL RESULT:")
    if results["success"]:
        print("✅ SUCCESS: API metadata successfully matches Pinecone data")
    else:
        print("❌ FAILURE: Discrepancies found between API metadata and Pinecone data")


def main():
    """Main function to verify metadata consistency."""
    if len(sys.argv) < 2:
        print("Usage: python verify_metadata_consistency.py <landmark_id>")
        print("Example: python verify_metadata_consistency.py LP-00009")
        return

    landmark_id = sys.argv[1]
    results = verify_landmark_metadata(landmark_id)
    print_results(results)

    # Create output directories if they don't exist
    output_dir = Path("test_output/metadata_verification")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save results to file for reference
    output_file = output_dir / f"{landmark_id.replace('/', '_')}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to: {output_file}")

    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()
