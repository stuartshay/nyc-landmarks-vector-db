#!/usr/bin/env python3
"""
Demonstration script showing how revision ID (rev_id) tracking works in Wikipedia metadata.

This script shows the complete metadata structure including revision IDs for version
tracking and update monitoring.
"""

import json
import sys
from typing import Any, Dict

# Add the project root to the path
sys.path.append(".")

from nyc_landmarks.models.wikipedia_models import (
    WikipediaContentModel,
    WikipediaQualityModel,
)
from nyc_landmarks.wikipedia.processor import WikipediaProcessor


def demonstrate_rev_id_metadata() -> None:
    """Demonstrate how revision ID metadata is stored and used."""
    print("=== Wikipedia Revision ID Metadata Demonstration ===\n")

    # Initialize processor
    processor = WikipediaProcessor()

    # Create a sample Wikipedia article with revision ID and quality assessment
    wiki_article = WikipediaContentModel(
        lpNumber="LP-00001",
        url="https://en.wikipedia.org/wiki/Sunnyslope_(Bronx)",
        title="Sunnyslope (Bronx)",
        content="Sunnyslope is a neighborhood in the Bronx, New York City...",
        chunks=None,
        quality=WikipediaQualityModel(
            prediction="Stub",
            probabilities={
                "FA": 0.01,
                "GA": 0.02,
                "B": 0.05,
                "C": 0.12,
                "Start": 0.20,
                "Stub": 0.60,
            },
            rev_id="1234567890",
        ),
        rev_id="1234567890",
    )

    current_time = "2024-01-01T12:00:00"

    # Create a sample chunk
    test_chunk: Dict[str, Any] = {
        "text": "Sunnyslope is a neighborhood in the Bronx, located in the southeastern part of the borough.",
        "chunk_index": 0,
        "metadata": {},
        "total_chunks": 1,
    }

    # Enrich the chunk with metadata including rev_id
    processor._enrich_dict_chunk(test_chunk, wiki_article, current_time)
    processor._add_quality_metadata_to_dict(test_chunk["metadata"], wiki_article)

    print("1. Complete Chunk Metadata Structure:")
    print("=" * 50)
    print(json.dumps(test_chunk, indent=2, default=str))

    print("\n\n2. Revision ID Storage Locations:")
    print("=" * 50)
    print(
        f"📍 article_metadata['rev_id']: {test_chunk.get('article_metadata', {}).get('rev_id')}"
    )
    print(
        f"📍 metadata['article_rev_id']: {test_chunk.get('metadata', {}).get('article_rev_id')}"
    )

    print("\n\n3. Quality Assessment with Revision ID:")
    print("=" * 50)
    metadata = test_chunk["metadata"]
    print(f"📊 Article Quality: {metadata.get('article_quality')}")
    print(f"📊 Quality Score: {metadata.get('article_quality_score')}")
    print(f"📊 Quality Description: {metadata.get('article_quality_description')}")
    print(f"🔄 Revision ID: {metadata.get('article_rev_id')}")

    print("\n\n4. Benefits of Revision ID Tracking:")
    print("=" * 50)
    print("✅ Version Control: Track specific Wikipedia article versions")
    print("✅ Update Detection: Identify when articles have been updated")
    print("✅ Citation Accuracy: Provide precise article version for citations")
    print("✅ Quality Correlation: Link quality assessments to specific revisions")
    print(
        "✅ Reproducibility: Ensure consistent results with specific article versions"
    )

    print("\n\n5. Usage in Search and Filtering:")
    print("=" * 50)
    print("# Filter by specific revision ID")
    print("filter_dict = {'article_rev_id': '1234567890'}")
    print("")
    print("# Filter by articles with revision tracking")
    print("filter_dict = {'article_rev_id': {'$exists': True}}")
    print("")
    print("# Combine with quality filtering")
    print("filter_dict = {")
    print("    'article_quality': 'Stub',")
    print("    'article_rev_id': {'$exists': True}")
    print("}")


if __name__ == "__main__":
    demonstrate_rev_id_metadata()
