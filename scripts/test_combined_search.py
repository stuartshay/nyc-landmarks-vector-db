#!/usr/bin/env python3
"""
Script to test combined Wikipedia and PDF content search in Pinecone.

This script demonstrates how to search across both Wikipedia and PDF vectors,
and how to filter results based on source type.
"""

import argparse
import logging
from typing import Any, Dict, List, Optional

from tabulate import tabulate

from nyc_landmarks.config.settings import settings
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL.value,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def search_vectors(
    query_text: str,
    landmark_id: Optional[str] = None,
    source_type: Optional[str] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search for vectors matching the query text with optional filtering.

    Args:
        query_text: The text to search for
        landmark_id: Optional landmark ID to filter results
        source_type: Optional source type to filter results (e.g., "wikipedia" or "pdf")
        top_k: Maximum number of results to return

    Returns:
        List of matching vectors with metadata
    """
    # Initialize components
    embedding_generator = EmbeddingGenerator()
    pinecone_db = PineconeDB()

    # Generate embedding for the query text
    embedding = embedding_generator.generate_embedding(query_text)

    # Build filter dictionary
    filter_dict = {}
    if landmark_id:
        filter_dict["landmark_id"] = landmark_id
    if source_type:
        filter_dict["source_type"] = source_type

    # Query the vector database
    logger.info(f"Querying Pinecone with text: '{query_text}'")
    logger.info(f"Using filters: {filter_dict}")

    results = pinecone_db.query_vectors(
        query_vector=embedding, top_k=top_k, filter_dict=filter_dict
    )

    return results


def display_results(results: List[Dict[str, Any]]) -> None:
    """
    Display search results in a readable format.

    Args:
        results: List of vector matches from Pinecone
    """
    if not results:
        print("No matching results found.")
        return

    # Prepare results for tabular display
    table_data = []
    for r in results:
        metadata = r.get("metadata", {})
        source_type = metadata.get("source_type", "unknown")

        # Format text snippet
        text = metadata.get("text", "")
        snippet = text[:100] + "..." if len(text) > 100 else text

        # Get source-specific information
        if source_type == "wikipedia":
            source_info = metadata.get("article_title", "Unknown Wikipedia Article")
        else:
            source_info = metadata.get(
                "document_name", metadata.get("file_name", "Unknown Document")
            )

        table_data.append(
            [
                r.get("id", "unknown"),
                metadata.get("landmark_id", ""),
                metadata.get("landmark_name", ""),
                source_type,
                source_info,
                round(r.get("score", 0.0), 3),
                snippet,
            ]
        )

    # Display table of results
    headers = [
        "Vector ID",
        "Landmark ID",
        "Landmark Name",
        "Source Type",
        "Source Info",
        "Score",
        "Text Snippet",
    ]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def compare_sources(
    query_text: str, landmark_id: Optional[str] = None, top_k: int = 3
) -> None:
    """
    Compare search results from different sources for the same query.

    Args:
        query_text: The text to search for
        landmark_id: Optional landmark ID to filter results
        top_k: Maximum number of results to return per source
    """
    print(f"\n===== SEARCHING FOR: '{query_text}' =====")

    # Get results from Wikipedia sources
    wiki_results = search_vectors(
        query_text=query_text,
        landmark_id=landmark_id,
        source_type="wikipedia",
        top_k=top_k,
    )

    print("\n===== WIKIPEDIA RESULTS =====")
    display_results(wiki_results)

    # Get results from PDF sources
    pdf_results = search_vectors(
        query_text=query_text, landmark_id=landmark_id, source_type="pdf", top_k=top_k
    )

    print("\n===== PDF RESULTS =====")
    display_results(pdf_results)

    # Get combined results (no source filter)
    combined_results = search_vectors(
        query_text=query_text,
        landmark_id=landmark_id,
        source_type=None,
        top_k=top_k * 2,
    )

    print("\n===== COMBINED RESULTS (NO SOURCE FILTER) =====")
    display_results(combined_results)


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Test combined Wikipedia and PDF content search in Pinecone"
    )
    parser.add_argument(
        "--query",
        default="historic landmark in Brooklyn",
        help="Text query to search for",
    )
    parser.add_argument(
        "--landmark-id", help="Filter results by landmark ID (e.g., LP-00001)"
    )
    parser.add_argument(
        "--source",
        choices=["wikipedia", "pdf", "combined"],
        default="combined",
        help="Source type to search from (wikipedia, pdf, or combined)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Maximum number of results to return per source",
    )

    args = parser.parse_args()

    if args.source == "combined":
        # Run comparison search
        compare_sources(
            query_text=args.query, landmark_id=args.landmark_id, top_k=args.top_k
        )
    else:
        # Run specific source search
        results = search_vectors(
            query_text=args.query,
            landmark_id=args.landmark_id,
            source_type=args.source,
            top_k=args.top_k,
        )

        print(f"\n===== {args.source.upper()} SEARCH RESULTS =====")
        display_results(results)


if __name__ == "__main__":
    main()
