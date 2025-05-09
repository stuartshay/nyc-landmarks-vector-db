#!/usr/bin/env python3
"""
Script to demonstrate the Wikipedia integration functionality.

This script showcases:
1. Fetching Wikipedia articles for a landmark
2. Processing the articles into chunks
3. Generating embeddings for the chunks
4. Storing and querying vectors in Pinecone
5. Comparing search results from Wikipedia and PDF sources
"""

import argparse
import logging
from typing import Any, Dict, Optional

import pandas as pd
from tabulate import tabulate

from nyc_landmarks.api.query import compare_source_results, search_combined_sources
from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI
from nyc_landmarks.db.db_client import DbClient
from nyc_landmarks.db.wikipedia_fetcher import WikipediaFetcher
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)

def fetch_and_display_wikipedia_articles(landmark_id: str) -> None:
    """
    Fetch and display Wikipedia articles for a landmark.

    Args:
        landmark_id: The landmark ID to fetch articles for
    """
    api_client = CoreDataStoreAPI()

    # Get landmark details
    landmark = None
    try:
        # Try different methods to get landmark details
        landmark = api_client.get_landmark_metadata(landmark_id)
    except (AttributeError, Exception):
        try:
            # Fall back to get_landmark_by_id if available
            landmark = api_client.get_landmark_by_id(landmark_id)
        except (AttributeError, Exception):
            pass
    if not landmark:
        print(f"No landmark found with ID: {landmark_id}")
        return

    # Get landmark name
    if isinstance(landmark, dict):
        landmark_name = landmark.get("name", "Unknown")
    else:
        landmark_name = getattr(landmark, "name", "Unknown")

    print(f"\n=== LANDMARK: {landmark_name} (ID: {landmark_id}) ===\n")

    # Get Wikipedia articles
    articles = api_client.get_wikipedia_articles(landmark_id)

    if not articles:
        print("No Wikipedia articles found for this landmark.")
        return

    print(f"Found {len(articles)} Wikipedia articles:\n")

    # Display article details
    for i, article in enumerate(articles, 1):
        print(f"Article {i}: {article.title}")
        print(f"URL: {article.url}")
        # Get article content regardless of what the property is called
        content = ""
        if hasattr(article, "extract"):
            content = article.extract
        elif hasattr(article, "content"):
            content = article.content

        print(f"Extract: {content[:200]}..." if content else "No extract available")
        print()

def process_wikipedia_article(landmark_id: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> bool:
    """
    Process Wikipedia articles for a landmark.

    Args:
        landmark_id: The landmark ID to process
        chunk_size: Target size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks

    Returns:
        bool: Whether processing was successful
    """
    try:
        print(f"\n=== PROCESSING WIKIPEDIA ARTICLES FOR LANDMARK: {landmark_id} ===\n")

        api_client = CoreDataStoreAPI()
        wiki_fetcher = WikipediaFetcher()
        embedding_generator = EmbeddingGenerator()
        pinecone_db = PineconeDB()

        # Get Wikipedia articles
        articles = api_client.get_wikipedia_articles(landmark_id)

        if not articles:
            print("No Wikipedia articles found for this landmark.")
            return False

        print(f"Processing {len(articles)} Wikipedia articles...\n")

        # Process the articles
        processed_articles, result = wiki_fetcher.process_landmark_wikipedia_articles(
            articles, chunk_size, chunk_overlap
        )

        if not processed_articles:
            print("No Wikipedia articles could be processed.")
            return False

        print(f"Articles processed: {len(processed_articles)}")
        print(f"Total chunks: {result.total_chunks}")
        # Get processing metrics safely using getattr with defaults
        total_tokens = getattr(result, "total_tokens", 0)
        avg_chunk_size = getattr(result, "avg_chunk_size", 0)
        print(f"Total tokens: {total_tokens}")
        print(f"Average chunk size: {avg_chunk_size:.2f} characters")
        print()

        # Process and store chunks for each article
        total_chunks_embedded = 0

        for article in processed_articles:
            if not article.chunks:
                print(f"No chunks to process for article: {article.title}")
                continue

            print(f"Generating embeddings for {len(article.chunks)} chunks from article: {article.title}")
            chunks_with_embeddings = embedding_generator.process_chunks(article.chunks)

            print(f"Storing {len(chunks_with_embeddings)} vectors in Pinecone")
            vector_ids = pinecone_db.store_chunks(
                chunks=chunks_with_embeddings,
                id_prefix=f"wiki-{article.title.replace(' ', '_')}-",
                landmark_id=landmark_id,
                use_fixed_ids=True,
                delete_existing=False,
            )

            total_chunks_embedded += len(vector_ids)
            print(f"Stored {len(vector_ids)} vectors for article: {article.title}\n")

        print(f"Total chunks embedded: {total_chunks_embedded}")
        return True

    except Exception as e:
        print(f"Error processing Wikipedia articles: {e}")
        return False

def search_landmark_content(
    landmark_id: str,
    query: str,
    top_k: int = 5,
    source_type: Optional[str] = None
) -> None:
    """
    Search landmark content from Wikipedia and PDF sources.

    Args:
        landmark_id: The landmark ID to search in
        query: The search query
        top_k: Number of results to return for each source
        source_type: Optional source type filter ('wikipedia' or 'pdf')
    """
    try:
        print(f"\n=== SEARCHING FOR: '{query}' in LANDMARK: {landmark_id} ===\n")

        # Get landmark details
        db_client = DbClient(CoreDataStoreAPI())
        landmark = None
        try:
            # Try different methods to get landmark details
            landmark = db_client.get_landmark_metadata(landmark_id)
        except (AttributeError, Exception):
            try:
                # Fall back to get_landmark_by_id if available
                landmark = db_client.get_landmark_by_id(landmark_id)
            except (AttributeError, Exception):
                pass

        if not landmark:
            print(f"No landmark found with ID: {landmark_id}")
            return

        # Get landmark name
        if isinstance(landmark, dict):
            landmark_name = landmark.get("name", "Unknown")
        else:
            landmark_name = getattr(landmark, "name", "Unknown")

        print(f"Landmark: {landmark_name} (ID: {landmark_id})\n")

        # Execute the search
        if source_type:
            print(f"Searching in {source_type.upper()} content only...\n")

            # Search for content with the specified source type
            results = search_combined_sources(
                query_text=query,
                landmark_id=landmark_id,
                source_type=source_type,
                top_k=top_k
            )

            if not results:
                print(f"No results found in {source_type} content.")
                return

            # Convert results to expected format for display
            display_results = {"matches": results}
            display_search_results(display_results, source_type.upper())

        else:
            print("Comparing search results from both Wikipedia and PDF sources...\n")

            # Get comparison results
            comparison = compare_source_results(
                query_text=query,
                landmark_id=landmark_id,
                top_k=top_k
            )

            # Display Wikipedia results
            wiki_results = comparison.get("wikipedia_results", [])
            if wiki_results:
                display_results = {"matches": wiki_results}
                display_search_results(display_results, "WIKIPEDIA")
            else:
                print("No results found in Wikipedia content.")

            print("\n" + "-" * 80 + "\n")

            # Display PDF results
            pdf_results = comparison.get("pdf_results", [])
            if pdf_results:
                display_results = {"matches": pdf_results}
                display_search_results(display_results, "PDF")
            else:
                print("No results found in PDF content.")

    except Exception as e:
        print(f"Error searching landmark content: {e}")

def display_search_results(results: Dict[str, Any], source_label: str) -> None:
    """
    Display search results in a formatted table.

    Args:
        results: Search results from the QueryAPI
        source_label: Label to display for the source type
    """
    print(f"{source_label} SEARCH RESULTS:\n")

    matches = results.get("matches", [])
    if not matches:
        print("No results found.")
        return

    rows = []
    for i, match in enumerate(matches, 1):
        # Extract metadata
        metadata = match.get("metadata", {})
        text = metadata.get("text", "").strip()
        # Truncate text to a reasonable length for display
        if len(text) > 300:
            text = text[:297] + "..."

        # Source-specific metadata
        source_info = ""
        if metadata.get("source_type") == "wikipedia":
            article_title = metadata.get("article_title", "Unknown Wikipedia Article")
            article_url = metadata.get("article_url", "")
            source_info = f"Article: {article_title}\nURL: {article_url}"
        else:
            report_url = metadata.get("report_url", "")
            source_info = f"PDF URL: {report_url}" if report_url else ""

        # Create row
        row = [
            i,
            match.get("score", 0),
            metadata.get("landmark_id", "Unknown"),
            metadata.get("chunk_index", "?"),
            text,
            source_info
        ]
        rows.append(row)

    # Create a DataFrame for nicer display
    df = pd.DataFrame(
        rows,
        columns=["#", "Score", "Landmark ID", "Chunk", "Text", "Source Info"]
    )

    # Display as a table - convert DataFrame to list for tabulate
    print(tabulate(df.values.tolist(), headers=list(df.columns), tablefmt="psql", showindex=False))

def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Demonstrate Wikipedia integration for NYC landmarks"
    )
    parser.add_argument(
        "--landmark-id",
        type=str,
        required=True,
        help="Landmark ID to demonstrate with",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Search query to demonstrate searching",
    )
    parser.add_argument(
        "--source-type",
        type=str,
        choices=["wikipedia", "pdf"],
        help="Source type to search (omit to search both)",
    )
    parser.add_argument(
        "--process",
        action="store_true",
        help="Process Wikipedia articles (fetch, chunk, embed, store)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of search results to display",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Target size of each chunk in characters",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Number of characters to overlap between chunks",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    # Always display available Wikipedia articles
    fetch_and_display_wikipedia_articles(args.landmark_id)

    # Optionally process the articles
    if args.process:
        success = process_wikipedia_article(
            args.landmark_id,
            args.chunk_size,
            args.chunk_overlap
        )
        if not success:
            print("Failed to process Wikipedia articles. Search results may be incomplete.")

    # Search if a query was provided
    if args.query:
        search_landmark_content(
            args.landmark_id,
            args.query,
            args.top_k,
            args.source_type
        )

if __name__ == "__main__":
    main()
