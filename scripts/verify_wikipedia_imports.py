#!/usr/bin/env python3
"""
Script to verify Wikipedia article integration with Pinecone.

This script:
1. Queries Pinecone DB to check for Wikipedia vectors
2. Validates vector ID format and metadata
3. Reports statistics on Wikipedia content coverage
4. Identifies landmarks with/without Wikipedia content
"""

import argparse
import json
import logging
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
from tabulate import tabulate

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI
from nyc_landmarks.db.db_client import DbClient
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)


def check_wikipedia_coverage() -> Tuple[Dict[str, int], pd.DataFrame]:
    """
    Check Wikipedia article coverage across landmarks.

    Returns:
        Tuple containing:
        - Dictionary with statistics
        - DataFrame with coverage details
    """
    print("Checking Wikipedia coverage in Pinecone DB...")

    # Initialize components
    pinecone_db = PineconeDB()
    db_client = DbClient(CoreDataStoreAPI())

    # Get all landmark IDs
    all_landmarks = db_client.get_all_landmarks()
    landmark_ids = []

    for landmark in all_landmarks:
        if isinstance(landmark, dict):
            landmark_id = landmark.get("id") or landmark.get("lpc_id")
        else:
            landmark_id = getattr(landmark, "id", None) or getattr(
                landmark, "lpc_id", None
            )

        if landmark_id:
            landmark_ids.append(landmark_id)

    print(f"Found {len(landmark_ids)} total landmarks in CoreDataStore API")

    # Query Pinecone for Wikipedia vectors
    query_response = pinecone_db.list_vectors_by_source(source_type="wikipedia")

    if not query_response or not query_response.get("matches"):
        print("No Wikipedia vectors found in Pinecone DB.")
        return {
            "total_landmarks": len(landmark_ids),
            "landmarks_with_wiki": 0,
        }, pd.DataFrame()

    # Extract vector metadata and group by landmark
    vectors = query_response.get("matches", [])
    print(f"Found {len(vectors)} Wikipedia vectors in Pinecone DB")

    # Track statistics
    landmarks_with_wiki = set()
    article_counts = defaultdict(int)
    article_chunks = defaultdict(int)
    article_landmarks = defaultdict(set)
    landmarkid_to_articles = defaultdict(set)

    # Process vectors
    for vector in vectors:
        metadata = vector.get("metadata", {})
        landmark_id = metadata.get("landmark_id")
        article_title = metadata.get("article_title", "Unknown")

        if landmark_id:
            landmarks_with_wiki.add(landmark_id)
            article_counts[article_title] += 1
            article_chunks[article_title] += 1
            article_landmarks[article_title].add(landmark_id)
            landmarkid_to_articles[landmark_id].add(article_title)

    # Calculate statistics
    stats = {
        "total_landmarks": len(landmark_ids),
        "landmarks_with_wiki": len(landmarks_with_wiki),
        "coverage_percentage": round(
            len(landmarks_with_wiki) / len(landmark_ids) * 100, 2
        ),
        "total_wiki_vectors": len(vectors),
        "unique_articles": len(article_counts),
        "avg_chunks_per_article": round(
            sum(article_chunks.values()) / len(article_chunks) if article_chunks else 0,
            2,
        ),
        "max_chunks_per_article": max(article_chunks.values()) if article_chunks else 0,
        "landmarks_without_wiki": len(landmark_ids) - len(landmarks_with_wiki),
    }

    # Create coverage dataframe
    coverage_data = []
    for landmark_id in landmark_ids:
        has_wiki = landmark_id in landmarks_with_wiki
        num_articles = len(landmarkid_to_articles.get(landmark_id, set()))
        article_titles = ", ".join(
            sorted(landmarkid_to_articles.get(landmark_id, set()))
        )
        coverage_data.append(
            {
                "landmark_id": landmark_id,
                "has_wiki": has_wiki,
                "articles_count": num_articles,
                "article_titles": article_titles if has_wiki else "",
            }
        )

    # Convert to DataFrame for better display
    coverage_df = pd.DataFrame(coverage_data)

    return stats, coverage_df


def validate_vector_id_format() -> Dict[str, Any]:
    """
    Validate Wikipedia vector ID format.

    Returns:
        Dictionary with validation results
    """
    print("Validating Wikipedia vector ID format...")

    pinecone_db = PineconeDB()
    query_response = pinecone_db.list_vectors_by_source(
        source_type="wikipedia", limit=500
    )

    if not query_response or not query_response.get("matches"):
        print("No Wikipedia vectors found in Pinecone DB.")
        return {"vectors_checked": 0, "valid_format": 0, "invalid_format": 0}

    vectors = query_response.get("matches", [])
    valid_ids = 0
    invalid_ids = []

    for vector in vectors:
        vector_id = vector.get("id", "")
        metadata = vector.get("metadata", {})
        landmark_id = metadata.get("landmark_id", "")
        article_title = metadata.get("article_title", "")

        # Expected format: wiki-{article_title}-{landmark_id}-chunk-{chunk_num}
        if (
            vector_id.startswith("wiki-")
            and landmark_id in vector_id
            and "-chunk-" in vector_id
            and (article_title.replace(" ", "_") in vector_id or not article_title)
        ):
            valid_ids += 1
        else:
            invalid_ids.append(vector_id)

    return {
        "vectors_checked": len(vectors),
        "valid_format": valid_ids,
        "valid_percentage": round(valid_ids / len(vectors) * 100, 2) if vectors else 0,
        "invalid_format": len(invalid_ids),
        "invalid_examples": invalid_ids[:5] if invalid_ids else [],
    }


def validate_vector_metadata() -> Dict[str, Any]:
    """
    Validate Wikipedia vector metadata.

    Returns:
        Dictionary with validation results
    """
    print("Validating Wikipedia vector metadata...")

    pinecone_db = PineconeDB()
    query_response = pinecone_db.list_vectors_by_source(
        source_type="wikipedia", limit=500
    )

    if not query_response or not query_response.get("matches"):
        print("No Wikipedia vectors found in Pinecone DB.")
        return {"vectors_checked": 0, "valid_metadata": 0, "invalid_metadata": 0}

    vectors = query_response.get("matches", [])

    # Required metadata fields
    required_fields = [
        "landmark_id",
        "source_type",
        "article_title",
        "article_url",
        "chunk_index",
    ]

    # Check each vector's metadata
    valid_metadata = 0
    missing_fields = Counter()

    for vector in vectors:
        metadata = vector.get("metadata", {})

        # Check for required fields
        missing = [field for field in required_fields if field not in metadata]

        if not missing:
            valid_metadata += 1
        else:
            for field in missing:
                missing_fields[field] += 1

    return {
        "vectors_checked": len(vectors),
        "valid_metadata": valid_metadata,
        "valid_percentage": (
            round(valid_metadata / len(vectors) * 100, 2) if vectors else 0
        ),
        "invalid_metadata": len(vectors) - valid_metadata,
        "most_common_missing": (
            dict(missing_fields.most_common(3)) if missing_fields else {}
        ),
    }


def report_article_distribution() -> Dict[str, Any]:
    """
    Report article distribution across landmarks.

    Returns:
        Dictionary with article distribution statistics
    """
    print("Analyzing article distribution across landmarks...")

    pinecone_db = PineconeDB()
    query_response = pinecone_db.list_vectors_by_source(source_type="wikipedia")

    if not query_response or not query_response.get("matches"):
        print("No Wikipedia vectors found in Pinecone DB.")
        return {"articles_analyzed": 0}

    vectors = query_response.get("matches", [])

    # Group by articles
    articles = defaultdict(lambda: {"landmarks": set(), "chunks": 0})

    for vector in vectors:
        metadata = vector.get("metadata", {})
        landmark_id = metadata.get("landmark_id")
        article_title = metadata.get("article_title", "Unknown")

        if landmark_id and article_title != "Unknown":
            articles[article_title]["landmarks"].add(landmark_id)
            articles[article_title]["chunks"] += 1

    # Analyze distribution
    article_counts = sorted(
        [
            (title, len(data["landmarks"]), data["chunks"])
            for title, data in articles.items()
        ],
        key=lambda x: x[1],
        reverse=True,
    )

    # Categorize articles
    single_landmark = [a for a in article_counts if a[1] == 1]
    multi_landmark = [a for a in article_counts if a[1] > 1]

    # Top articles by landmark coverage
    top_articles = article_counts[:10] if article_counts else []

    return {
        "articles_analyzed": len(articles),
        "single_landmark_articles": len(single_landmark),
        "multi_landmark_articles": len(multi_landmark),
        "max_landmarks_per_article": (
            max([a[1] for a in article_counts]) if article_counts else 0
        ),
        "avg_landmarks_per_article": (
            round(sum([a[1] for a in article_counts]) / len(article_counts), 2)
            if article_counts
            else 0
        ),
        "top_articles": top_articles,
    }


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Verify Wikipedia integration with Pinecone DB"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output with detailed statistics",
    )
    parser.add_argument(
        "--coverage-report",
        action="store_true",
        help="Generate a detailed coverage report CSV",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./",
        help="Directory to save reports (default: current directory)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of landmarks to check",
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    # Check Wikipedia coverage
    print("\n===== WIKIPEDIA COVERAGE CHECK =====")
    coverage_stats, coverage_df = check_wikipedia_coverage()

    # Report coverage statistics
    print("\nWikipedia Coverage Statistics:")
    print(f"Total landmarks: {coverage_stats['total_landmarks']}")
    print(f"Landmarks with Wikipedia content: {coverage_stats['landmarks_with_wiki']}")
    print(f"Coverage percentage: {coverage_stats['coverage_percentage']}%")
    print(
        f"Landmarks without Wikipedia content: {coverage_stats['landmarks_without_wiki']}"
    )
    print(f"Total Wikipedia vectors: {coverage_stats.get('total_wiki_vectors', 0)}")
    print(f"Unique Wikipedia articles: {coverage_stats.get('unique_articles', 0)}")
    print(
        f"Average chunks per article: {coverage_stats.get('avg_chunks_per_article', 0)}"
    )

    # Validate vector ID format
    print("\n===== VECTOR ID FORMAT VALIDATION =====")
    id_validation = validate_vector_id_format()

    print(
        f"\nVector ID Format Results (checked {id_validation['vectors_checked']} vectors):"
    )
    print(
        f"Valid format: {id_validation['valid_format']} ({id_validation['valid_percentage']}%)"
    )
    print(f"Invalid format: {id_validation['invalid_format']}")

    if id_validation["invalid_format"] > 0:
        print("\nInvalid ID examples:")
        for example in id_validation["invalid_examples"]:
            print(f"- {example}")

    # Validate vector metadata
    print("\n===== METADATA VALIDATION =====")
    metadata_validation = validate_vector_metadata()

    print(
        f"\nMetadata Validation Results (checked {metadata_validation['vectors_checked']} vectors):"
    )
    print(
        f"Valid metadata: {metadata_validation['valid_metadata']} ({metadata_validation['valid_percentage']}%)"
    )
    print(f"Invalid metadata: {metadata_validation['invalid_metadata']}")

    if metadata_validation["invalid_metadata"] > 0:
        print("\nMost common missing fields:")
        for field, count in metadata_validation["most_common_missing"].items():
            print(f"- {field}: missing in {count} vectors")

    # Report article distribution
    print("\n===== ARTICLE DISTRIBUTION =====")
    distribution = report_article_distribution()

    print(
        f"\nArticle Distribution (analyzed {distribution['articles_analyzed']} articles):"
    )
    print(f"Single-landmark articles: {distribution['single_landmark_articles']}")
    print(f"Multi-landmark articles: {distribution['multi_landmark_articles']}")
    print(f"Max landmarks per article: {distribution['max_landmarks_per_article']}")
    print(f"Avg landmarks per article: {distribution['avg_landmarks_per_article']}")

    if distribution.get("top_articles"):
        print("\nTop articles by landmark coverage:")
        article_rows = []
        for i, (title, landmark_count, chunk_count) in enumerate(
            distribution["top_articles"], 1
        ):
            article_rows.append([i, title, landmark_count, chunk_count])

        df = pd.DataFrame(
            article_rows, columns=["#", "Article Title", "Landmarks", "Chunks"]
        )
        print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))

    # Generate coverage report if requested
    if args.coverage_report and not coverage_df.empty:
        report_path = f"{args.output_dir.rstrip('/')}/wikipedia_coverage_report.csv"
        coverage_df.to_csv(report_path, index=False)
        print(f"\nCoverage report saved to: {report_path}")

    # Set exit code based on validation results
    if (
        id_validation.get("valid_percentage", 0) < 95
        or metadata_validation.get("valid_percentage", 0) < 95
    ):
        print(
            "\nValidation WARNING: Some vectors have incorrect format or missing metadata!"
        )
        sys.exit(1)
    else:
        print(
            "\nValidation SUCCESS: Wikipedia integration appears to be working correctly."
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
