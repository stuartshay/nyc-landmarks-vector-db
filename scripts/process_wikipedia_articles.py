#!/usr/bin/env python3
"""
Script to process Wikipedia articles for NYC landmarks and store them in the vector database.

This script retrieves Wikipedia articles for landmarks from the CoreDataStore API,
processes the articles into chunks, generates embeddings using OpenAI,
and stores the embeddings in Pinecone with metadata.
"""

import argparse
import logging
import time
from typing import Optional

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI
from nyc_landmarks.db.wikipedia_fetcher import WikipediaFetcher
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.models.wikipedia_models import WikipediaProcessingResult
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=settings.LOG_LEVEL.value,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def process_landmark_wikipedia(
    landmark_id: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    recreate_index: bool = False,
    delete_existing: bool = True,
) -> Optional[WikipediaProcessingResult]:
    """Process all Wikipedia articles for a landmark and store in vector database.

    Args:
        landmark_id: ID of the landmark to process
        chunk_size: Target size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        recreate_index: Whether to recreate the Pinecone index
        delete_existing: Whether to delete existing vectors for the landmark

    Returns:
        Processing result summary, or None if an error occurs
    """
    try:
        logger.info(f"Processing Wikipedia articles for landmark: {landmark_id}")

        # Initialize components
        api_client = CoreDataStoreAPI()
        wiki_fetcher = WikipediaFetcher()
        embedding_generator = EmbeddingGenerator()
        pinecone_db = PineconeDB()

        # Recreate index if requested
        if recreate_index:
            logger.warning("Recreating Pinecone index. ALL DATA WILL BE LOST!")
            pinecone_db.recreate_index()

        # Get Wikipedia articles for the landmark
        articles = api_client.get_wikipedia_articles(landmark_id)

        if not articles:
            logger.info(f"No Wikipedia articles found for landmark: {landmark_id}")

            # Return empty result
            return WikipediaProcessingResult(
                total_landmarks=1,
                landmarks_with_wikipedia=0,
                total_articles=0,
                articles_processed=0,
                articles_with_errors=0,
                total_chunks=0,
                chunks_embedded=0,
            )

        logger.info(
            f"Found {len(articles)} Wikipedia articles for landmark: {landmark_id}"
        )

        # Process the articles
        processed_articles, result = wiki_fetcher.process_landmark_wikipedia_articles(
            articles, chunk_size, chunk_overlap
        )

        if not processed_articles:
            logger.warning(
                f"No Wikipedia articles processed for landmark: {landmark_id}"
            )
            return result

        # Generate embeddings and store in Pinecone for each article
        total_chunks_embedded = 0

        for article in processed_articles:
            if not article.chunks:
                logger.warning(f"No chunks to process for article: {article.title}")
                continue

            # Generate embeddings for the chunks
            chunks_with_embeddings = embedding_generator.process_chunks(article.chunks)

            # Store in Pinecone with deterministic IDs
            # We'll add "wiki" to the ID prefix to distinguish from PDF chunks
            # Format: wiki-LP-00001-Wyckoff_House-chunk-0
            vector_ids = pinecone_db.store_chunks(
                chunks=chunks_with_embeddings,
                id_prefix=f"wiki-{article.title.replace(' ', '_')}-",
                landmark_id=landmark_id,
                use_fixed_ids=True,
                delete_existing=delete_existing,
            )

            total_chunks_embedded += len(vector_ids)
            logger.info(
                f"Stored {len(vector_ids)} vectors for article: {article.title}"
            )

        # Update the result with the number of chunks embedded
        result.chunks_embedded = total_chunks_embedded

        logger.info(f"Processing complete for landmark {landmark_id}: {str(result)}")
        return result

    except Exception as e:
        logger.error(f"Error processing Wikipedia for landmark {landmark_id}: {e}")
        return None


def process_all_landmarks_wikipedia(
    limit: Optional[int] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    recreate_index: bool = False,
    delete_existing: bool = True,
) -> WikipediaProcessingResult:
    """Process Wikipedia articles for all landmarks.

    Args:
        limit: Maximum number of landmarks to process (optional)
        chunk_size: Target size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        recreate_index: Whether to recreate the Pinecone index
        delete_existing: Whether to delete existing vectors for each landmark

    Returns:
        Processing result summary
    """
    try:
        logger.info("Processing Wikipedia articles for all landmarks")

        # Initialize components
        api_client = CoreDataStoreAPI()

        # Get all landmarks
        landmarks = api_client.get_all_landmarks(limit)

        if not landmarks:
            logger.warning("No landmarks found")
            return WikipediaProcessingResult(
                total_landmarks=0,
                landmarks_with_wikipedia=0,
                total_articles=0,
                articles_processed=0,
                articles_with_errors=0,
                total_chunks=0,
                chunks_embedded=0,
            )

        logger.info(f"Found {len(landmarks)} landmarks")

        # Process landmarks
        total_landmarks = len(landmarks)
        landmarks_with_wikipedia = 0
        total_articles = 0
        articles_processed = 0
        articles_with_errors = 0
        total_chunks = 0
        chunks_embedded = 0

        # Recreate index only once if requested
        if recreate_index:
            pinecone_db = PineconeDB()
            logger.warning("Recreating Pinecone index. ALL DATA WILL BE LOST!")
            pinecone_db.recreate_index()

        # Process each landmark
        for i, landmark in enumerate(landmarks):
            landmark_id = landmark.get("id", "")
            if not landmark_id:
                continue

            logger.info(f"Processing landmark {i + 1}/{len(landmarks)}: {landmark_id}")

            # Process the landmark
            result = process_landmark_wikipedia(
                landmark_id=landmark_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                recreate_index=False,  # Already recreated if needed
                delete_existing=delete_existing,
            )

            if result:
                # Update statistics
                landmarks_with_wikipedia += result.landmarks_with_wikipedia
                total_articles += result.total_articles
                articles_processed += result.articles_processed
                articles_with_errors += result.articles_with_errors
                total_chunks += result.total_chunks
                chunks_embedded += result.chunks_embedded

            # Add a delay to avoid rate limiting
            time.sleep(1.0)

        # Create a summary of all processing
        final_result = WikipediaProcessingResult(
            total_landmarks=total_landmarks,
            landmarks_with_wikipedia=landmarks_with_wikipedia,
            total_articles=total_articles,
            articles_processed=articles_processed,
            articles_with_errors=articles_with_errors,
            total_chunks=total_chunks,
            chunks_embedded=chunks_embedded,
        )

        logger.info(f"Processing complete for all landmarks: {str(final_result)}")
        return final_result

    except Exception as e:
        logger.error(f"Error processing all landmarks: {e}")
        return WikipediaProcessingResult(
            total_landmarks=0,
            landmarks_with_wikipedia=0,
            total_articles=0,
            articles_processed=0,
            articles_with_errors=0,
            total_chunks=0,
            chunks_embedded=0,
        )


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Process Wikipedia articles for NYC landmarks and store them in the vector database"
    )
    parser.add_argument(
        "--landmark-id",
        help="Process Wikipedia articles for a specific landmark ID (e.g., LP-00001)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of landmarks to process",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Target size of text chunks in characters",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Number of characters to overlap between chunks",
    )
    parser.add_argument(
        "--recreate-index",
        action="store_true",
        help="Recreate the Pinecone index (WARNING: This will delete all existing vectors)",
    )
    parser.add_argument(
        "--no-delete-existing",
        action="store_true",
        help="Don't delete existing vectors for each landmark before processing",
    )

    args = parser.parse_args()

    # Process based on arguments
    if args.landmark_id:
        result = process_landmark_wikipedia(
            landmark_id=args.landmark_id,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            recreate_index=args.recreate_index,
            delete_existing=not args.no_delete_existing,
        )
        if result:
            print(f"Processing complete: {str(result)}")
    else:
        result = process_all_landmarks_wikipedia(
            limit=args.limit,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            recreate_index=args.recreate_index,
            delete_existing=not args.no_delete_existing,
        )
        print(f"Processing complete: {str(result)}")


if __name__ == "__main__":
    main()
