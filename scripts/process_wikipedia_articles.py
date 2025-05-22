#!/usr/bin/env python3
"""
Script to process Wikipedia articles for NYC landmarks.

This script:
1. Fetches landmark data from the CoreDataStore API
2. Retrieves Wikipedia articles for each landmark
3. Processes the articles into chunks
4. Generates embeddings for the chunks
5. Stores the vectors in Pinecone


python scripts/process_wikipedia_articles.py --page 2 --limit 5 --verbose
python scripts/process_wikipedia_articles.py --landmark-ids LP-00079 --verbose

"""

import argparse
import concurrent.futures
import datetime
import logging
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from tqdm import tqdm

from nyc_landmarks.db.wikipedia_fetcher import WikipediaFetcher
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.models.metadata_models import SourceType
from nyc_landmarks.models.wikipedia_models import WikipediaContentModel
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
        from nyc_landmarks.db.db_client import get_db_client

        db_client = get_db_client()
        wiki_fetcher = WikipediaFetcher()
        embedding_generator = EmbeddingGenerator()
        pinecone_db = PineconeDB()

        # Step 2: Get Wikipedia articles for the landmark
        articles = db_client.get_wikipedia_articles(landmark_id)

        if not articles:
            logger.info(f"No Wikipedia articles found for landmark: {landmark_id}")
            return False, 0, 0

        logger.info(
            f"Found {len(articles)} Wikipedia articles for landmark: {landmark_id}"
        )
        for article in articles:
            logger.info(f"- Article: {article.title}, URL: {article.url}")

            # Fetch the actual content from Wikipedia
            logger.info(f"Fetching content from Wikipedia for article: {article.title}")
            article_content = wiki_fetcher.fetch_wikipedia_content(article.url)
            if article_content:
                article.content = article_content
                logger.info(
                    f"Successfully fetched content for article: {article.title} ({len(article_content)} chars)"
                )
            else:
                logger.warning(f"Failed to fetch content for article: {article.title}")

        # Step 3: Process the articles
        # Initialize for token-based chunking
        from transformers import GPT2Tokenizer

        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        max_token_limit = 8192
        token_limit_per_chunk = max_token_limit - 500  # Reserve tokens for metadata

        logger.info(f"Using token limit of {token_limit_per_chunk} per chunk")

        # Helper function for token-based chunking
        def split_into_token_chunks(text: Optional[str], max_tokens: int) -> List[str]:
            if text is None:
                return []
            tokens = tokenizer.encode(text)
            chunks = []
            for i in range(0, len(tokens), max_tokens):
                chunks.append(tokenizer.decode(tokens[i : i + max_tokens]))
            return chunks

        # Process each article into WikipediaContentModel objects
        processed_articles = []
        total_chunks = 0

        for article in articles:
            logger.debug(f"Processing article: {article.title}")

            if article.content is None:
                logger.error(f"Content is None for article: {article.title}")
                continue

            # Split the article into token-based chunks
            token_chunks = split_into_token_chunks(
                article.content, token_limit_per_chunk
            )
            logger.info(
                f"Split article '{article.title}' into {len(token_chunks)} token-based chunks"
            )

            # Create dictionary chunks for the WikipediaContentModel
            dict_chunks = []
            for i, chunk_text in enumerate(token_chunks):
                token_count = len(tokenizer.encode(chunk_text))
                logger.info(f"Processing chunk {i} with {token_count} tokens")

                dict_chunks.append(
                    {
                        "text": chunk_text,
                        "chunk_index": i,
                        "metadata": {
                            "chunk_index": i,
                            "article_title": article.title,
                            "article_url": article.url,
                            "source_type": SourceType.WIKIPEDIA.value,
                            "landmark_id": landmark_id,
                        },
                        "total_chunks": len(token_chunks),
                    }
                )

            # Create a WikipediaContentModel with the chunks
            content_model = WikipediaContentModel(
                lpNumber=landmark_id,
                url=article.url,
                title=article.title,
                content=article.content,
                chunks=dict_chunks,
            )

            processed_articles.append(content_model)
            total_chunks += len(dict_chunks)

        if not processed_articles:
            logger.warning(
                f"No Wikipedia articles processed for landmark: {landmark_id}"
            )
            return False, 0, 0

        logger.info(
            f"Processed {len(processed_articles)} Wikipedia articles with {total_chunks} chunks"
        )

        # Step 4: Generate embeddings and store in Pinecone for each article
        total_chunks_embedded = 0

        # Process each article to generate embeddings and store them
        for wiki_article in processed_articles:
            # Skip articles with no chunks
            if not hasattr(wiki_article, "chunks") or not wiki_article.chunks:
                logger.warning(
                    f"No chunks to process for article: {wiki_article.title}"
                )
                continue

            # Generate embeddings for the chunks
            logger.info(
                f"Generating embeddings for {len(wiki_article.chunks)} chunks from article: {wiki_article.title}"
            )
            chunks_with_embeddings = embedding_generator.process_chunks(
                wiki_article.chunks
            )

            # Get current timestamp for processing_date
            current_time = datetime.datetime.now().isoformat()

            # Replace WikipediaMetadata with a dictionary for metadata
            article_metadata = {
                "title": wiki_article.title,
                "url": wiki_article.url,
                "processing_date": current_time,
                "source_type": SourceType.WIKIPEDIA.value,
            }

            def add_metadata_to_chunks(
                chunks_with_embeddings: List[Union[Dict[str, Any], Any]],
                article_metadata: Dict[str, Any],
            ) -> None:
                """Helper function to add metadata to chunks."""
                for chunk in chunks_with_embeddings:
                    if isinstance(chunk, dict):
                        chunk["metadata"]["wikipedia_metadata"] = article_metadata
                    else:
                        if hasattr(chunk, "metadata") and chunk.metadata is not None:
                            chunk.metadata["wikipedia_metadata"] = article_metadata

            # Add metadata to each chunk
            add_metadata_to_chunks(chunks_with_embeddings, article_metadata)

            # Add article title, URL, and processing date to metadata for each chunk
            for chunk in chunks_with_embeddings:
                # Ensure metadata structure is consistent
                if isinstance(chunk, dict):
                    # Add article_metadata field which is used by PineconeDB._create_metadata_for_chunk
                    if "article_metadata" not in chunk:
                        chunk["article_metadata"] = {}
                    chunk["article_metadata"]["title"] = wiki_article.title
                    chunk["article_metadata"]["url"] = wiki_article.url

                    # Add processing_date to be picked up by PineconeDB._create_metadata_for_chunk
                    chunk["processing_date"] = current_time

                    # Also add directly to metadata for backwards compatibility
                    if "metadata" in chunk and chunk["metadata"] is not None:
                        chunk["metadata"]["article_title"] = wiki_article.title
                        chunk["metadata"]["article_url"] = wiki_article.url
                        chunk["metadata"]["processing_date"] = current_time

                    # Debug log to verify metadata is being set
                    logger.info(
                        f"Added article metadata to chunk: article_title={wiki_article.title}, article_url={wiki_article.url}, processing_date={current_time}"
                    )
                else:
                    # Handle object-style chunks
                    # Add article_metadata field
                    if not hasattr(chunk, "article_metadata"):
                        setattr(chunk, "article_metadata", {})
                    chunk.article_metadata["title"] = wiki_article.title
                    chunk.article_metadata["url"] = wiki_article.url

                    # Add processing_date to be picked up by PineconeDB._create_metadata_for_chunk
                    setattr(chunk, "processing_date", current_time)

                    # Also add directly to metadata for backwards compatibility
                    if hasattr(chunk, "metadata") and chunk.metadata is not None:
                        chunk.metadata["article_title"] = wiki_article.title
                        chunk.metadata["article_url"] = wiki_article.url
                        chunk.metadata["processing_date"] = current_time

                    logger.info(
                        f"Added article metadata to object-style chunk: {wiki_article.title} with processing_date={current_time}"
                    )

            # Add additional metadata for Wikipedia articles
            for chunk in chunks_with_embeddings:
                if isinstance(chunk, dict):
                    chunk["metadata"]["article_title"] = wiki_article.title
                    chunk["metadata"]["article_url"] = wiki_article.url
                    chunk["metadata"]["processing_date"] = current_time
                else:
                    if hasattr(chunk, "metadata") and chunk.metadata is not None:
                        chunk.metadata["article_title"] = wiki_article.title
                        chunk.metadata["article_url"] = wiki_article.url
                        chunk.metadata["processing_date"] = current_time

            # Ensure metadata consistency for chunks by adding `source_type` explicitly
            for chunk in chunks_with_embeddings:
                if isinstance(chunk, dict):
                    chunk["metadata"]["source_type"] = SourceType.WIKIPEDIA.value
                else:
                    if hasattr(chunk, "metadata") and chunk.metadata is not None:
                        chunk.metadata["source_type"] = SourceType.WIKIPEDIA.value

            # Store in Pinecone with deterministic IDs
            logger.info(f"Storing {len(chunks_with_embeddings)} vectors in Pinecone")
            vector_ids = pinecone_db.store_chunks(
                chunks=chunks_with_embeddings,
                id_prefix=f"wiki-{wiki_article.title.replace(' ', '_')}-",
                landmark_id=landmark_id,
                use_fixed_ids=True,
                delete_existing=delete_existing
                and total_chunks_embedded == 0,  # Only delete on first article
            )

            total_chunks_embedded += len(vector_ids)
            logger.info(
                f"Stored {len(vector_ids)} vectors for article: {wiki_article.title}"
            )

        logger.info(f"Total chunks embedded: {total_chunks_embedded}")
        return True, len(processed_articles), total_chunks_embedded

    except Exception as e:
        logger.error(f"Error processing Wikipedia for landmark {landmark_id}: {e}")
        return False, 0, 0


def process_landmarks_sequential(
    landmarks: List[str],
    chunk_size: int,
    chunk_overlap: int,
    delete_existing: bool,
) -> Dict[str, Union[Tuple[bool, int, int], List[str]]]:
    """
    Process Wikipedia articles for multiple landmarks sequentially.

    Args:
        landmarks: List of landmark IDs to process
        chunk_size: Target size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        delete_existing: Whether to delete existing vectors for landmarks

    Returns:
        Dictionary mapping landmark IDs to processing results, plus a special key for missing articles
    """
    results: Dict[str, Union[Tuple[bool, int, int], List[str]]] = {}
    # Track landmarks with missing articles separately
    missing_articles: List[str] = []

    for landmark_id in tqdm(landmarks, desc="Processing landmarks"):
        success, articles_processed, chunks_embedded = process_landmark_wikipedia(
            landmark_id, chunk_size, chunk_overlap, delete_existing
        )
        results[landmark_id] = (success, articles_processed, chunks_embedded)

        # If not successful and no articles processed, likely missing articles
        if not success and articles_processed == 0:
            missing_articles.append(landmark_id)

    # Store missing articles in the results object for reporting later
    results["__missing_articles__"] = missing_articles
    return results


def process_landmarks_parallel(
    landmarks: List[str],
    chunk_size: int,
    chunk_overlap: int,
    delete_existing: bool,
    workers: int,
) -> Dict[str, Union[Tuple[bool, int, int], List[str]]]:
    """
    Process Wikipedia articles for multiple landmarks in parallel.

    Args:
        landmarks: List of landmark IDs to process
        chunk_size: Target size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        delete_existing: Whether to delete existing vectors for landmarks
        workers: Number of parallel workers

    Returns:
        Dictionary mapping landmark IDs to processing results, plus a special key for missing articles
    """
    results: Dict[str, Union[Tuple[bool, int, int], List[str]]] = {}
    # Track landmarks with missing articles separately
    missing_articles: List[str] = []

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

                # If not successful and no articles processed, likely missing articles
                if not success and articles_processed == 0:
                    missing_articles.append(landmark_id)
            except Exception as e:
                logger.error(f"Error processing {landmark_id}: {e}")
                results[landmark_id] = (False, 0, 0)

    # Store missing articles in the results object for reporting later
    results["__missing_articles__"] = missing_articles
    return results


def get_all_landmark_ids(limit: Optional[int] = None) -> List[str]:
    """
    Fetch all landmark IDs using the `get_all_landmarks` method from `db_client`.

    Args:
        limit: Maximum number of landmark IDs to return (optional).

    Returns:
        List of landmark IDs.
    """
    from nyc_landmarks.db.db_client import get_db_client

    db_client = get_db_client()

    try:
        # Fetch landmarks from the database
        landmarks = db_client.get_all_landmarks(limit=limit)

        if not landmarks:
            logger.warning("No landmarks found in the database.")
            return []

        # Extract only the IDs from the landmarks
        landmark_ids = [landmark["id"] for landmark in landmarks if "id" in landmark]

        logger.info(f"Fetched {len(landmark_ids)} landmark IDs.")
        return landmark_ids

    except Exception as e:
        logger.error(f"Error fetching landmark IDs: {e}")
        return []


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed command line arguments
    """
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
        "--page-size",
        type=int,
        default=100,
        help="Number of landmarks to fetch per API request (default: 100)",
    )

    # Create mutually exclusive group for processing mode
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--all",
        action="store_true",
        help="Process all available landmarks in the database (cannot be used with --page)",
    )
    mode_group.add_argument(
        "--page",
        type=int,
        default=1,
        help="Page number to start fetching landmarks from (default: 1, cannot be used with --all)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Additional validation: if someone uses --page with default value and --all
    if args.all and args.page != 1:
        parser.error(
            "Argument --all cannot be used with --page (use either --all or --page N, not both)"
        )

    return args


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbose: Whether to enable verbose (INFO) logging
    """
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)


def get_landmarks_to_process(
    landmark_ids: Optional[str],
    limit: Optional[int],
    page: int = 1,
    process_all: bool = False,
    page_size: int = 100,
) -> List[str]:
    """Determine which landmarks to process.

    Args:
        landmark_ids: Comma-separated list of landmark IDs to process
        limit: Maximum number of landmarks to process
        page: Page number to start fetching landmarks from (not used if process_all is True)
        process_all: Whether to process all available landmarks in the database
        page_size: Number of landmarks to fetch per API request

    Returns:
        List of landmark IDs to process
    """
    if landmark_ids:
        # Process specific landmarks
        landmarks_to_process = [lid.strip() for lid in landmark_ids.split(",")]
        logger.info(f"Will process {len(landmarks_to_process)} specified landmarks")
    elif process_all:
        # Process all available landmarks
        from nyc_landmarks.db.db_client import get_db_client

        db_client = get_db_client()
        total_records = db_client.get_total_record_count()
        logger.info(f"Retrieved total record count: {total_records}")

        # If limit is provided, use the smaller of limit or total_records
        effective_limit = (
            min(limit, total_records) if limit is not None else total_records
        )
        logger.info(
            f"Will process up to {effective_limit} landmarks of {total_records} total"
        )

        # When process_all is True, we always start from page 1 (due to mutual exclusivity)
        # Fetch all landmark IDs with the effective limit
        landmarks_to_process = get_all_landmark_ids(effective_limit)
        logger.info(f"Will process {len(landmarks_to_process)} landmarks")
    else:
        # Fetch landmark IDs with the specified limit
        landmarks_to_process = get_all_landmark_ids(limit)
        logger.info(f"Will process {len(landmarks_to_process)} landmarks")

    return landmarks_to_process


def process_landmarks(
    landmarks: List[str],
    chunk_size: int,
    chunk_overlap: int,
    delete_existing: bool,
    use_parallel: bool,
    workers: int,
) -> Dict[str, Union[Tuple[bool, int, int], List[str]]]:
    """Process the landmarks based on configuration.

    Args:
        landmarks: List of landmark IDs to process
        chunk_size: Target size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        delete_existing: Whether to delete existing vectors
        use_parallel: Whether to process landmarks in parallel
        workers: Number of parallel workers

    Returns:
        Results of processing each landmark
    """
    if use_parallel:
        logger.info(
            f"Processing {len(landmarks)} landmarks in parallel with {workers} workers"
        )
        return process_landmarks_parallel(
            landmarks,
            chunk_size,
            chunk_overlap,
            delete_existing,
            workers,
        )
    else:
        logger.info(f"Processing {len(landmarks)} landmarks sequentially")
        return process_landmarks_sequential(
            landmarks,
            chunk_size,
            chunk_overlap,
            delete_existing,
        )


def calculate_statistics(
    results: Dict[str, Union[Tuple[bool, int, int], List[str]]],
    landmarks_count: int,
    elapsed_time: float,
) -> Tuple[int, int, int, List[str], List[str]]:
    """Calculate statistics from processing results.

    Args:
        results: Processing results by landmark ID
        landmarks_count: Total number of landmarks processed
        elapsed_time: Time taken to process landmarks

    Returns:
        Tuple of (successful_landmarks, total_articles, total_chunks,
                 missing_articles, failed_landmarks)
    """
    # Extract special key for missing articles
    missing_articles_data = results.pop("__missing_articles__", [])
    # Convert to list of strings to handle typing
    missing_articles = [str(lid) for lid in missing_articles_data]

    # Calculate statistics
    successful_landmarks = sum(
        1 for success, _, _ in results.values() if isinstance(success, bool) and success
    )
    # Only include tuples, not any special string values like "__missing_articles__"
    total_articles = sum(
        articles for _, articles, _ in results.values() if isinstance(articles, int)
    )
    total_chunks = sum(
        chunks for _, _, chunks in results.values() if isinstance(chunks, int)
    )

    # Calculate true failures (not successful but not in missing_articles)
    failed_landmarks = [
        lid
        for lid, (success, _, _) in results.items()
        if not success and lid not in missing_articles
    ]

    return (
        successful_landmarks,
        total_articles,
        total_chunks,
        missing_articles,
        failed_landmarks,
    )


def print_results(
    landmarks_count: int,
    successful_landmarks: int,
    total_articles: int,
    total_chunks: int,
    elapsed_time: float,
    missing_articles: List[str],
    failed_landmarks: List[str],
    chunk_names: List[str],
) -> int:
    """Print results and determine exit code.

    Args:
        landmarks_count: Total number of landmarks processed
        successful_landmarks: Number of successfully processed landmarks
        total_articles: Total number of articles processed
        total_chunks: Total number of chunks embedded
        elapsed_time: Time taken for processing
        missing_articles: List of landmarks with no Wikipedia articles
        failed_landmarks: List of landmarks that failed processing
        chunk_names: List of chunk names processed

    Returns:
        Exit code (0 for success/partial success, 1 for complete failure)
    """
    # Print main statistics
    print("\n===== WIKIPEDIA PROCESSING RESULTS =====")
    print(f"Total landmarks processed: {landmarks_count}")
    print(f"Successful landmarks: {successful_landmarks}")
    print(f"Total Wikipedia articles processed: {total_articles}")
    print(f"Total chunks embedded: {total_chunks}")
    print(f"Processing time: {elapsed_time:.2f} seconds")

    # Report chunk names
    if chunk_names:
        print("\nProcessed Chunk Names:")
        for chunk_name in chunk_names[:10]:
            print(f"- {chunk_name}")
        if len(chunk_names) > 10:
            print(f"...and {len(chunk_names) - 10} more")

    # Report landmarks with missing articles
    if missing_articles:
        print(f"\nLandmarks with no Wikipedia articles: {len(missing_articles)}")
        print(f"IDs: {', '.join(missing_articles[:10])}")
        if len(missing_articles) > 10:
            print(f"...and {len(missing_articles) - 10} more")

    # Report failed landmarks
    if failed_landmarks:
        print(f"\nLandmarks that failed processing: {len(failed_landmarks)}")
        print(f"Failed landmarks: {', '.join(failed_landmarks[:10])}")
        if len(failed_landmarks) > 10:
            print(f"...and {len(failed_landmarks) - 10} more")

    # Determine exit code and final message
    if successful_landmarks == 0:
        print("\nError: No landmarks were successfully processed")
        return 1
    elif failed_landmarks:
        print(
            "\nWarning: Some landmarks failed to process (not due to missing articles)"
        )
        return 0  # Still exit with 0 to avoid failing CI jobs
    else:
        success_message = "Success: All landmarks successfully processed"
        if missing_articles:
            success_message += f" ({len(missing_articles)} had no Wikipedia articles)"
        print(f"\n{success_message}")
        return 0


def main() -> None:
    """Main entry point for the script."""
    # Parse arguments and set up logging
    args = parse_arguments()
    setup_logging(args.verbose)

    # Get landmarks to process
    landmarks_to_process = get_landmarks_to_process(
        args.landmark_ids, args.limit, args.page, args.all, args.page_size
    )
    if not landmarks_to_process:
        logger.error("No landmarks to process")
        sys.exit(1)

    # Process landmarks and time the execution
    start_time = time.time()
    results = process_landmarks(
        landmarks_to_process,
        args.chunk_size,
        args.chunk_overlap,
        args.delete_existing,
        args.parallel,
        args.workers,
    )
    elapsed_time = time.time() - start_time

    # Calculate statistics and print results
    stats = calculate_statistics(results, len(landmarks_to_process), elapsed_time)
    # Unpack stats in the correct order: successful_landmarks, total_articles, total_chunks, missing_articles, failed_landmarks
    (
        successful_landmarks,
        total_articles,
        total_chunks,
        missing_articles,
        failed_landmarks,
    ) = stats

    # Collect chunk names for reporting
    chunk_names: List[str] = []
    for result in results.values():
        if isinstance(result, tuple) and len(result) == 3:
            success, articles_processed, chunks_embedded = result
            if success and isinstance(chunks_embedded, list):
                for chunk in chunks_embedded:
                    if (
                        isinstance(chunk, dict)
                        and "metadata" in chunk
                        and "article_title" in chunk["metadata"]
                    ):
                        chunk_names.append(chunk["metadata"]["article_title"])

    exit_code = print_results(
        len(landmarks_to_process),
        successful_landmarks,
        total_articles,
        total_chunks,
        elapsed_time,
        missing_articles,
        failed_landmarks,
        chunk_names,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
