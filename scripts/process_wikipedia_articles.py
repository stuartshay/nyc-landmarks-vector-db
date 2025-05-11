#!/usr/bin/env python3
"""
Script to process Wikipedia articles for NYC landmarks.

This script:
1. Fetches landmark data from the CoreDataStore API
2. Retrieves Wikipedia articles for each landmark
3. Processes the articles into chunks
4. Generates embeddings for the chunks
5. Stores the vectors in Pinecone
"""

import argparse
import concurrent.futures
import logging
import sys
import time
from typing import Dict, List, Optional, Tuple

from tqdm import tqdm

from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI
from nyc_landmarks.db.db_client import DbClient
from nyc_landmarks.db.wikipedia_fetcher import WikipediaFetcher
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = get_logger(__name__)


def process_landmark_wikipedia(
    landmark_id: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    delete_existing: bool = False,
) -> Tuple[bool, int, int]:
    """
    Process Wikipedia articles for a landmark and store in vector database.

    Args:
        landmark_id: ID of the landmark to process
        chunk_size: Target size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        delete_existing: Whether to delete existing vectors for the landmark

    Returns:
        Tuple of (success, articles_processed, chunks_embedded)
    """
    try:
        logger.info(f"Processing Wikipedia articles for landmark: {landmark_id}")

        # Step 1: Initialize components
        api_client = CoreDataStoreAPI()
        wiki_fetcher = WikipediaFetcher()
        embedding_generator = EmbeddingGenerator()
        pinecone_db = PineconeDB()

        # Step 2: Get Wikipedia articles for the landmark
        articles = api_client.get_wikipedia_articles(landmark_id)

        if not articles:
            logger.info(f"No Wikipedia articles found for landmark: {landmark_id}")
            return False, 0, 0

        logger.info(
            f"Found {len(articles)} Wikipedia articles for landmark: {landmark_id}"
        )
        for article in articles:
            logger.info(f"- Article: {article.title}, URL: {article.url}")

        # Step 3: Process the articles
        processed_articles, result = wiki_fetcher.process_landmark_wikipedia_articles(
            articles, chunk_size, chunk_overlap
        )

        if not processed_articles:
            logger.warning(
                f"No Wikipedia articles processed for landmark: {landmark_id}"
            )
            return False, 0, 0

        logger.info(
            f"Processed {len(processed_articles)} Wikipedia articles with {result.total_chunks} chunks"
        )

        # Step 4: Generate embeddings and store in Pinecone for each article
        total_chunks_embedded = 0

        for article in processed_articles:
            if not article.chunks:
                logger.warning(f"No chunks to process for article: {article.title}")
                continue

            # Generate embeddings for the chunks
            logger.info(
                f"Generating embeddings for {len(article.chunks)} chunks from article: {article.title}"
            )
            chunks_with_embeddings = embedding_generator.process_chunks(article.chunks)

            # Store in Pinecone with deterministic IDs
            logger.info(f"Storing {len(chunks_with_embeddings)} vectors in Pinecone")
            vector_ids = pinecone_db.store_chunks(
                chunks=chunks_with_embeddings,
                id_prefix=f"wiki-{article.title.replace(' ', '_')}-",
                landmark_id=landmark_id,
                use_fixed_ids=True,
                delete_existing=delete_existing
                and total_chunks_embedded == 0,  # Only delete on first article
            )

            total_chunks_embedded += len(vector_ids)
            logger.info(
                f"Stored {len(vector_ids)} vectors for article: {article.title}"
            )

        logger.info(f"Total chunks embedded: {total_chunks_embedded}")
        return True, len(processed_articles), total_chunks_embedded

    except Exception as e:
        logger.error(f"Error processing Wikipedia for landmark {landmark_id}: {e}")
        return False, 0, 0


def process_landmarks_parallel(
    landmarks: List[str],
    chunk_size: int,
    chunk_overlap: int,
    delete_existing: bool,
    workers: int,
) -> Dict[str, Tuple[bool, int, int]]:
    """
    Process Wikipedia articles for multiple landmarks in parallel.

    Args:
        landmarks: List of landmark IDs to process
        chunk_size: Target size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        delete_existing: Whether to delete existing vectors for landmarks
        workers: Number of parallel workers

    Returns:
        Dictionary mapping landmark IDs to processing results
    """
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        future_to_landmark = {
            executor.submit(
                process_landmark_wikipedia,
                landmark_id,
                chunk_size,
                chunk_overlap,
                delete_existing,
            ): landmark_id
            for landmark_id in landmarks
        }

        # Process results as they complete
        for future in tqdm(
            concurrent.futures.as_completed(future_to_landmark),
            total=len(landmarks),
            desc="Processing landmarks",
        ):
            landmark_id = future_to_landmark[future]
            try:
                success, articles_processed, chunks_embedded = future.result()
                results[landmark_id] = (success, articles_processed, chunks_embedded)
            except Exception as e:
                logger.error(f"Error processing {landmark_id}: {e}")
                results[landmark_id] = (False, 0, 0)

    return results


def process_landmarks_sequential(
    landmarks: List[str],
    chunk_size: int,
    chunk_overlap: int,
    delete_existing: bool,
) -> Dict[str, Tuple[bool, int, int]]:
    """
    Process Wikipedia articles for multiple landmarks sequentially.

    Args:
        landmarks: List of landmark IDs to process
        chunk_size: Target size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        delete_existing: Whether to delete existing vectors for landmarks

    Returns:
        Dictionary mapping landmark IDs to processing results
    """
    results = {}
    for landmark_id in tqdm(landmarks, desc="Processing landmarks"):
        success, articles_processed, chunks_embedded = process_landmark_wikipedia(
            landmark_id, chunk_size, chunk_overlap, delete_existing
        )
        results[landmark_id] = (success, articles_processed, chunks_embedded)
    return results


def get_all_landmark_ids(limit: Optional[int] = None) -> List[str]:
    """
    Get all landmark IDs from the CoreDataStore API.

    Args:
        limit: Maximum number of landmarks to return

    Returns:
        List of landmark IDs
    """
    logger.info("Fetching all landmark IDs from CoreDataStore API")
    db_client = DbClient(CoreDataStoreAPI())

    # Get all landmarks
    landmarks = db_client.get_all_landmarks()

    # Extract IDs
    landmark_ids = []
    for landmark in landmarks:
        if isinstance(landmark, dict):
            landmark_id = landmark.get("id") or landmark.get("lpc_id")
        else:
            landmark_id = getattr(landmark, "id", None) or getattr(
                landmark, "lpc_id", None
            )

        if landmark_id:
            landmark_ids.append(landmark_id)

    logger.info(f"Found {len(landmark_ids)} total landmarks")

    # Apply limit if specified
    if limit is not None and limit > 0:
        landmark_ids = landmark_ids[:limit]
        logger.info(f"Limited to {len(landmark_ids)} landmarks")

    return landmark_ids


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Process Wikipedia articles for NYC landmarks"
    )
    parser.add_argument(
        "--landmark-ids",
        type=str,
        help="Comma-separated list of landmark IDs to process",
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
        "--parallel",
        action="store_true",
        help="Process landmarks in parallel",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (only used with --parallel)",
    )
    parser.add_argument(
        "--delete-existing",
        action="store_true",
        help="Delete existing Wikipedia vectors before processing",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of landmarks to process (only used when no landmark IDs specified)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    # Determine landmarks to process
    landmarks_to_process = []
    if args.landmark_ids:
        # Process specific landmarks
        landmarks_to_process = [lid.strip() for lid in args.landmark_ids.split(",")]
        logger.info(f"Will process {len(landmarks_to_process)} specified landmarks")
    else:
        # Process all landmarks (or limited set)
        landmarks_to_process = get_all_landmark_ids(args.limit)
        logger.info(f"Will process {len(landmarks_to_process)} landmarks")

    if not landmarks_to_process:
        logger.error("No landmarks to process")
        sys.exit(1)

    # Process landmarks
    start_time = time.time()

    if args.parallel:
        logger.info(
            f"Processing {len(landmarks_to_process)} landmarks in parallel with {args.workers} workers"
        )
        results = process_landmarks_parallel(
            landmarks_to_process,
            args.chunk_size,
            args.chunk_overlap,
            args.delete_existing,
            args.workers,
        )
    else:
        logger.info(f"Processing {len(landmarks_to_process)} landmarks sequentially")
        results = process_landmarks_sequential(
            landmarks_to_process,
            args.chunk_size,
            args.chunk_overlap,
            args.delete_existing,
        )

    # Calculate statistics
    elapsed_time = time.time() - start_time
    successful_landmarks = sum(1 for success, _, _ in results.values() if success)
    total_articles = sum(articles for _, articles, _ in results.values())
    total_chunks = sum(chunks for _, _, chunks in results.values())

    # Report results
    print("\n===== WIKIPEDIA PROCESSING RESULTS =====")
    print(f"Total landmarks processed: {len(landmarks_to_process)}")
    print(f"Successful landmarks: {successful_landmarks}")
    print(f"Total Wikipedia articles processed: {total_articles}")
    print(f"Total chunks embedded: {total_chunks}")
    print(f"Processing time: {elapsed_time:.2f} seconds")

    if successful_landmarks < len(landmarks_to_process):
        print(
            f"\nWarning: Failed to process {len(landmarks_to_process) - successful_landmarks} landmarks"
        )
        failed_landmarks = [
            lid for lid, (success, _, _) in results.items() if not success
        ]
        print(f"Failed landmarks: {', '.join(failed_landmarks[:10])}")
        if len(failed_landmarks) > 10:
            print(f"...and {len(failed_landmarks) - 10} more")

    # Set exit code based on success
    if successful_landmarks == 0:
        print("\nError: No landmarks were successfully processed")
        sys.exit(1)
    elif successful_landmarks < len(landmarks_to_process):
        print("\nWarning: Some landmarks failed to process")
        sys.exit(0)  # Still exit with 0 to avoid failing CI jobs
    else:
        print("\nSuccess: All landmarks successfully processed")
        sys.exit(0)


if __name__ == "__main__":
    main()
