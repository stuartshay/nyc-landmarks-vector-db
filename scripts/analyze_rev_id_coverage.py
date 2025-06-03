#!/usr/bin/env python3
"""
Utility script to analyze revision ID coverage in existing Wikipedia vectors.

This script checks the current database for revision ID metadata and provides
statistics on coverage and implementation status.
"""

import sys
from typing import Any, Dict

# Add the project root to the path
sys.path.append(".")

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

logger = get_logger(__name__)


def analyze_revision_id_coverage() -> Dict[str, Any]:
    """Analyze revision ID coverage in existing Wikipedia vectors."""
    logger.info("Starting revision ID coverage analysis...")

    try:
        # Initialize database connection
        db = PineconeDB()

        # Fetch Wikipedia vectors
        logger.info("Fetching Wikipedia vectors from database...")
        response = db.list_vectors_by_source("wikipedia", limit=500)

        if not response or not response.get("matches"):
            logger.warning("No Wikipedia vectors found in database")
            return {"total_vectors": 0, "error": "No Wikipedia vectors found"}

        vectors = response.get("matches", [])
        logger.info(f"Found {len(vectors)} Wikipedia vectors")

        # Initialize statistics
        total_vectors = len(vectors)
        vectors_with_rev_id = 0
        vectors_without_rev_id = 0
        unique_revision_ids = set()
        sample_metadata: list[Dict[str, Any]] = []

        # Analyze revision ID coverage
        for vector in vectors:
            metadata = vector.get("metadata", {})

            # Check for revision ID in metadata
            has_rev_id = "article_rev_id" in metadata and metadata["article_rev_id"]

            if has_rev_id:
                vectors_with_rev_id += 1
                unique_revision_ids.add(metadata["article_rev_id"])

                # Collect sample metadata for first 3 vectors with rev_id
                if len(sample_metadata) < 3:
                    sample_metadata.append(
                        {
                            "landmark_id": metadata.get("landmark_id"),
                            "article_title": metadata.get("article_title"),
                            "article_rev_id": metadata.get("article_rev_id"),
                            "article_quality": metadata.get("article_quality"),
                            "processing_date": metadata.get("processing_date"),
                        }
                    )
            else:
                vectors_without_rev_id += 1

        # Calculate coverage percentage
        coverage_percentage = (
            (vectors_with_rev_id / total_vectors * 100) if total_vectors > 0 else 0.0
        )

        return {
            "total_vectors": total_vectors,
            "vectors_with_rev_id": vectors_with_rev_id,
            "vectors_without_rev_id": vectors_without_rev_id,
            "rev_id_coverage_percentage": coverage_percentage,
            "unique_revision_ids": len(unique_revision_ids),
            "sample_metadata": sample_metadata,
        }

    except Exception as e:
        logger.error(f"Error analyzing revision ID coverage: {e}")
        return {"total_vectors": 0, "error": str(e)}


def _get_coverage_status(coverage_percentage: float) -> str:
    """Get coverage status emoji and description based on percentage."""
    if coverage_percentage >= 95:
        return "� Excellent"
    elif coverage_percentage >= 75:
        return "🟡 Good"
    elif coverage_percentage >= 50:
        return "🟠 Partial"
    else:
        return "🔴 Poor"


def _print_overall_statistics(stats: Dict[str, Any]) -> None:
    """Print overall statistics section."""
    print("\n📈 OVERALL STATISTICS")
    print(f"   Total Wikipedia vectors: {stats['total_vectors']:,}")
    print(f"   Vectors with revision IDs: {stats['vectors_with_rev_id']:,}")
    print(f"   Vectors without revision IDs: {stats['vectors_without_rev_id']:,}")
    print(f"   Coverage percentage: {stats['rev_id_coverage_percentage']:.1f}%")
    print(f"   Unique revision IDs: {stats['unique_revision_ids']:,}")

    coverage = stats["rev_id_coverage_percentage"]
    status = _get_coverage_status(coverage)
    print(f"   Status: {status}")


def _analyze_landmark_coverage(landmark_stats: Dict[str, Any]) -> Dict[str, int]:
    """Analyze landmark-level coverage and return counts."""
    full_coverage = 0
    partial_coverage = 0
    no_coverage = 0

    for landmark_id, data in landmark_stats.items():
        total = data["total_vectors"]
        with_rev_id = data["vectors_with_rev_id"]
        coverage_pct = (with_rev_id / total * 100) if total > 0 else 0

        if coverage_pct == 100:
            full_coverage += 1
        elif coverage_pct > 0:
            partial_coverage += 1
        else:
            no_coverage += 1

    return {
        "full_coverage": full_coverage,
        "partial_coverage": partial_coverage,
        "no_coverage": no_coverage,
    }


def _print_landmark_coverage(stats: Dict[str, Any]) -> None:
    """Print landmark-level coverage section."""
    landmark_stats = stats.get("landmark_coverage", {})
    if not landmark_stats:
        return

    print("\n🏛️  LANDMARK-LEVEL COVERAGE")
    coverage_counts = _analyze_landmark_coverage(landmark_stats)

    print(f"   Landmarks with full coverage: {coverage_counts['full_coverage']}")
    print(f"   Landmarks with partial coverage: {coverage_counts['partial_coverage']}")
    print(f"   Landmarks without coverage: {coverage_counts['no_coverage']}")


def _print_sample_metadata(stats: Dict[str, Any]) -> None:
    """Print sample metadata section."""
    if not stats.get("sample_metadata"):
        return

    print("\n📋 SAMPLE METADATA WITH REVISION IDs")
    for i, sample in enumerate(stats["sample_metadata"], 1):
        print(f"   {i}. {sample['article_title']}")
        print(f"      Landmark ID: {sample['landmark_id']}")
        print(f"      Revision ID: {sample['article_rev_id']}")
        print(f"      Quality: {sample.get('article_quality', 'N/A')}")
        print(f"      Processed: {sample.get('processing_date', 'N/A')}")
        print()


def _print_recommendations(coverage_percentage: float) -> None:
    """Print recommendations based on coverage percentage."""
    print("💡 RECOMMENDATIONS")
    if coverage_percentage >= 95:
        print("   ✅ Revision ID tracking is well implemented")
        print("   ✅ Continue monitoring for new articles")
    elif coverage_percentage >= 50:
        print("   🔄 Consider reprocessing articles without revision IDs")
        print("   📊 Monitor coverage as new articles are added")
    else:
        print("   🔄 Reprocess existing Wikipedia articles to add revision IDs")
        print("   🏗️  Ensure revision ID extraction is working in the pipeline")


def print_coverage_report(stats: Dict[str, Any]) -> None:
    """Print a formatted coverage report."""
    print("=" * 70)
    print("📊 WIKIPEDIA REVISION ID COVERAGE ANALYSIS")
    print("=" * 70)

    if "error" in stats:
        print(f"❌ Error: {stats['error']}")
        return

    _print_overall_statistics(stats)
    _print_landmark_coverage(stats)
    _print_sample_metadata(stats)
    _print_recommendations(stats["rev_id_coverage_percentage"])

    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("Analyzing Wikipedia revision ID coverage...")
    stats = analyze_revision_id_coverage()
    print_coverage_report(stats)
