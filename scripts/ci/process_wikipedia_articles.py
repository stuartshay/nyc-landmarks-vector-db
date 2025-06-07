#!/usr/bin/env python3
"""
Script to process Wikipedia articles for NYC landmarks.

This script:
1. Fetches landmark data from the CoreDataStore API
2. Retrieves Wikipedia articles for each landmark
3. Processes the articles into chunks
4. Generates embeddings for the chunks
5. Stores the vectors in Pinecone

Examples:
    python scripts/ci/process_wikipedia_articles.py --page 1 --limit 25 --verbose
    python scripts/ci/process_wikipedia_articles.py --landmark-ids LP-00079 --verbose
    python scripts/ci/process_wikipedia_articles.py --all --verbose --parallel
    python scripts/ci/process_wikipedia_articles.py --all --verbose --parallel --workers 8
"""

import argparse
import concurrent.futures
import logging
import sys
import threading
import time
from typing import Any, Dict, List, Set, Tuple

from tqdm import tqdm

from nyc_landmarks.landmarks.landmarks_processing import get_landmarks_to_process
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.utils.results_reporter import print_results
from nyc_landmarks.wikipedia import WikipediaProcessor

# Configure logging
logger = get_logger(__name__)


_thread_local = threading.local()


def _get_processor() -> WikipediaProcessor:
    """Return a thread-local ``WikipediaProcessor`` instance.

    Example
    -------
    Use within a worker function to share a single processor per thread::

        def worker(landmark_id: str) -> None:
            processor = _get_processor()
            processor.process_landmark_wikipedia(landmark_id)
    """

    processor = getattr(_thread_local, "processor", None)
    if processor is None:
        processor = WikipediaProcessor()
        _thread_local.processor = processor
    return processor


def process_landmarks_sequential(
    landmarks: List[str],
    delete_existing: bool,
) -> Dict[str, Any]:
    """
    Process Wikipedia articles for multiple landmarks sequentially.

    Args:
        landmarks: List of landmark IDs to process
        delete_existing: Whether to delete existing vectors for landmarks

    Returns:
        Dictionary mapping landmark IDs to processing results
    """
    processor = WikipediaProcessor()
    results: Dict[str, Any] = {}
    errors: List[str] = []
    skipped_landmarks: Set[str] = set()

    for landmark_id in tqdm(landmarks, desc="Processing landmarks"):
        try:
            success, articles_processed, chunks_embedded = (
                processor.process_landmark_wikipedia(
                    landmark_id, delete_existing=delete_existing
                )
            )
            results[landmark_id] = {
                "success": success,
                "articles_processed": articles_processed,
                "chunks_embedded": chunks_embedded,
            }

            # Track landmarks that failed processing (not just those with no articles)
            # Note: landmarks with no Wikipedia articles now return success=True
            if not success:
                # This is a real processing failure, not just "no articles found"
                logger.warning(
                    f"Failed to process Wikipedia for landmark {landmark_id}"
                )
            elif articles_processed == 0:
                # Success but no articles - this is normal and not a failure
                logger.info(
                    f"No Wikipedia articles found for landmark {landmark_id} (normal case)"
                )
                skipped_landmarks.add(landmark_id)  # Still track for reporting purposes

        except Exception as e:
            error_msg = f"Error processing {landmark_id}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            results[landmark_id] = {
                "success": False,
                "articles_processed": 0,
                "chunks_embedded": 0,
            }

    # Store metadata for results reporting
    results["__metadata__"] = {
        "errors": errors,
        "skipped_landmarks": skipped_landmarks,
    }
    return results


def process_landmarks_parallel(
    landmarks: List[str],
    delete_existing: bool,
    workers: int,
) -> Dict[str, Any]:
    """
    Process Wikipedia articles for multiple landmarks in parallel.

    Args:
        landmarks: List of landmark IDs to process
        delete_existing: Whether to delete existing vectors for landmarks
        workers: Number of parallel workers

    Returns:
        Dictionary mapping landmark IDs to processing results

    Example
    -------
    >>> process_landmarks_parallel(["LP-00079"], False, workers=4)
    """
    results: Dict[str, Any] = {}
    errors: List[str] = []
    skipped_landmarks: Set[str] = set()

    def process_single_landmark(landmark_id: str) -> Tuple[str, bool, int, int]:
        """Process a single landmark and return results."""
        processor = _get_processor()
        success, articles_processed, chunks_embedded = (
            processor.process_landmark_wikipedia(
                landmark_id, delete_existing=delete_existing
            )
        )
        return landmark_id, success, articles_processed, chunks_embedded

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        future_to_landmark = {
            executor.submit(process_single_landmark, landmark_id): landmark_id
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
                returned_id, success, articles_processed, chunks_embedded = (
                    future.result()
                )
                results[landmark_id] = {
                    "success": success,
                    "articles_processed": articles_processed,
                    "chunks_embedded": chunks_embedded,
                }

                # Track landmarks with no articles separately
                if not success and articles_processed == 0:
                    skipped_landmarks.add(landmark_id)

            except Exception as e:
                error_msg = f"Error processing {landmark_id}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                results[landmark_id] = {
                    "success": False,
                    "articles_processed": 0,
                    "chunks_embedded": 0,
                }

    # Store metadata for results reporting
    results["__metadata__"] = {
        "errors": errors,
        "skipped_landmarks": skipped_landmarks,
    }
    return results


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process Wikipedia articles for NYC landmarks"
    )
    parser.add_argument(
        "--landmark-ids",
        type=str,
        help="Comma-separated list of landmark IDs to process",
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
        help="Maximum number of landmarks to process",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Number of landmarks to fetch per API request",
    )

    # Create mutually exclusive group for processing mode
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--all",
        action="store_true",
        help="Process all available landmarks in the database",
    )
    mode_group.add_argument(
        "--page",
        type=int,
        default=1,
        help="Page number to start fetching landmarks from",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Additional validation
    if args.all and args.page != 1:
        parser.error("Cannot use --all with --page (they are mutually exclusive)")

    return args


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level."""
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)


def process_landmarks(
    landmarks: List[str],
    delete_existing: bool,
    use_parallel: bool,
    workers: int,
) -> Dict[str, Any]:
    """Process the landmarks based on configuration."""
    if use_parallel:
        logger.info(
            f"Processing {len(landmarks)} landmarks in parallel with {workers} workers"
        )
        return process_landmarks_parallel(landmarks, delete_existing, workers)
    else:
        logger.info(f"Processing {len(landmarks)} landmarks sequentially")
        return process_landmarks_sequential(landmarks, delete_existing)


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
        args.delete_existing,
        args.parallel,
        args.workers,
    )
    elapsed_time = time.time() - start_time

    # Extract metadata
    metadata = results.pop("__metadata__", {})
    errors = metadata.get("errors", [])
    skipped_landmarks = metadata.get("skipped_landmarks", set())

    # Print results and exit with appropriate code
    exit_code = print_results(
        landmark_results=results,
        total_processing_time=elapsed_time,
        errors=errors,
        skipped_landmarks=skipped_landmarks,
        verbose=args.verbose,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
