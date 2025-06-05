#!/usr/bin/env python
"""
Test script for Wikipedia API improvements.

This script tests the performance and reliability improvements made
to the Wikipedia fetcher and metadata collector components.
"""

import argparse
import datetime
import logging
import time
from typing import List, Tuple

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.wikipedia_fetcher import WikipediaFetcher
from nyc_landmarks.vectordb.enhanced_metadata import (
    clear_metadata_cache,
    get_metadata_collector,
)
from nyc_landmarks.wikipedia.processor import WikipediaProcessor

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL.value)
logger = logging.getLogger(__name__)


def test_wikipedia_fetcher(urls: List[str], iterations: int = 3) -> None:
    """
    Test the Wikipedia fetcher with connection pooling.

    Args:
        urls: List of Wikipedia article URLs to fetch
        iterations: Number of times to fetch each URL
    """
    fetcher = WikipediaFetcher()
    logger.info(
        f"Testing Wikipedia fetcher with {len(urls)} URLs, {iterations} iterations each"
    )

    # Track timings
    total_time = 0.0
    fetch_times: List[float] = []

    for i in range(iterations):
        logger.info(f"Iteration {i + 1}/{iterations}")
        for url in urls:
            start_time = time.time()
            content, rev_id = fetcher.fetch_wikipedia_content(url)
            end_time = time.time()

            fetch_time = end_time - start_time
            fetch_times.append(fetch_time)
            total_time += fetch_time

            logger.info(f"Fetched URL: {url}")
            logger.info(f"Content length: {len(content) if content else 0} chars")
            logger.info(f"Revision ID: {rev_id}")
            logger.info(f"Fetch time: {fetch_time:.3f} seconds")

    # Calculate statistics
    avg_time = total_time / (len(urls) * iterations)
    min_time = min(fetch_times)
    max_time = max(fetch_times)

    logger.info(f"Results for {len(urls)} URLs, {iterations} iterations:")
    logger.info(f"Total time: {total_time:.3f} seconds")
    logger.info(f"Average fetch time: {avg_time:.3f} seconds")
    logger.info(f"Min fetch time: {min_time:.3f} seconds")
    logger.info(f"Max fetch time: {max_time:.3f} seconds")


def test_metadata_caching(landmark_ids: List[str], iterations: int = 3) -> None:
    """
    Test metadata caching in the EnhancedMetadataCollector.

    Args:
        landmark_ids: List of landmark IDs to fetch metadata for
        iterations: Number of times to fetch metadata for each landmark
    """
    # Clear cache before starting
    clear_metadata_cache()
    logger.info(
        f"Testing metadata caching with {len(landmark_ids)} landmarks, {iterations} iterations each"
    )

    collector = get_metadata_collector()

    # Track timings
    fetch_times: List[Tuple[str, bool, float]] = []  # (landmark_id, is_cached, time)

    for i in range(iterations):
        logger.info(f"Iteration {i + 1}/{iterations}")
        for landmark_id in landmark_ids:
            start_time = time.time()

            # Check if we should expect a cache hit
            expect_cache_hit = False
            if i > 0 and landmark_id in collector._metadata_cache:
                timestamp, _ = collector._metadata_cache[landmark_id]
                if datetime.datetime.now() - timestamp < collector._cache_ttl:
                    expect_cache_hit = True

            # Fetch metadata
            metadata = collector.collect_landmark_metadata(landmark_id)
            end_time = time.time()

            fetch_time = end_time - start_time
            is_cached = expect_cache_hit
            fetch_times.append((landmark_id, is_cached, fetch_time))

            logger.info(f"Fetched metadata for landmark: {landmark_id}")
            logger.info(
                f"Metadata fields: {len(metadata.dict() if hasattr(metadata, 'dict') else dict(metadata))}"
            )
            logger.info(f"Cache {'hit' if is_cached else 'miss'}")
            logger.info(f"Fetch time: {fetch_time:.3f} seconds")

    # Calculate statistics
    cached_times = [t for _, is_cached, t in fetch_times if is_cached]
    uncached_times = [t for _, is_cached, t in fetch_times if not is_cached]

    logger.info(f"Results for {len(landmark_ids)} landmarks, {iterations} iterations:")

    if uncached_times:
        logger.info(f"Uncached fetches: {len(uncached_times)}")
        logger.info(
            f"Average uncached fetch time: {sum(uncached_times) / len(uncached_times):.3f} seconds"
        )
        logger.info(f"Min uncached fetch time: {min(uncached_times):.3f} seconds")
        logger.info(f"Max uncached fetch time: {max(uncached_times):.3f} seconds")

    if cached_times:
        logger.info(f"Cached fetches: {len(cached_times)}")
        logger.info(
            f"Average cached fetch time: {sum(cached_times) / len(cached_times):.3f} seconds"
        )
        logger.info(f"Min cached fetch time: {min(cached_times):.3f} seconds")
        logger.info(f"Max cached fetch time: {max(cached_times):.3f} seconds")

    if cached_times and uncached_times:
        avg_uncached = sum(uncached_times) / len(uncached_times)
        avg_cached = sum(cached_times) / len(cached_times)
        speedup = avg_uncached / avg_cached
        logger.info(f"Cache speedup factor: {speedup:.2f}x")


def test_wikipedia_processor(landmark_ids: List[str]) -> None:
    """
    Test the Wikipedia processor with the improved components.

    Args:
        landmark_ids: List of landmark IDs to process
    """
    processor = WikipediaProcessor()
    logger.info(f"Testing Wikipedia processor with {len(landmark_ids)} landmarks")

    for landmark_id in landmark_ids:
        logger.info(f"Processing landmark: {landmark_id}")

        start_time = time.time()
        success, articles_processed, chunks_embedded = (
            processor.process_landmark_wikipedia(
                landmark_id,
                delete_existing=False,
            )
        )
        end_time = time.time()

        processing_time = end_time - start_time

        logger.info(f"Success: {success}")
        logger.info(f"Articles processed: {articles_processed}")
        logger.info(f"Chunks embedded: {chunks_embedded}")
        logger.info(f"Processing time: {processing_time:.3f} seconds")


def get_example_wikipedia_urls() -> List[str]:
    """Get a list of example Wikipedia URLs for testing."""
    return [
        "https://en.wikipedia.org/wiki/Empire_State_Building",
        "https://en.wikipedia.org/wiki/Chrysler_Building",
        "https://en.wikipedia.org/wiki/Flatiron_Building",
        "https://en.wikipedia.org/wiki/Woolworth_Building",
        "https://en.wikipedia.org/wiki/One_World_Trade_Center",
    ]


def get_example_landmark_ids() -> List[str]:
    """Get a list of example landmark IDs for testing."""
    return [
        "LP-00001",
        "LP-00002",
        "LP-00003",
        "LP-00004",
        "LP-00005",
    ]


def main() -> None:
    """Run the test script."""
    parser = argparse.ArgumentParser(description="Test Wikipedia API improvements")
    parser.add_argument(
        "--test-type",
        type=str,
        choices=["fetcher", "metadata", "processor", "all"],
        default="all",
        help="Type of test to run",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Number of iterations for each test",
    )
    parser.add_argument(
        "--landmark-ids",
        type=str,
        nargs="+",
        help="List of landmark IDs to test",
    )
    parser.add_argument(
        "--urls",
        type=str,
        nargs="+",
        help="List of Wikipedia URLs to test",
    )

    args = parser.parse_args()

    urls = args.urls if args.urls else get_example_wikipedia_urls()
    landmark_ids = (
        args.landmark_ids if args.landmark_ids else get_example_landmark_ids()
    )

    if args.test_type in ["fetcher", "all"]:
        logger.info("=== Testing Wikipedia Fetcher ===")
        test_wikipedia_fetcher(urls, args.iterations)

    if args.test_type in ["metadata", "all"]:
        logger.info("=== Testing Metadata Caching ===")
        test_metadata_caching(landmark_ids, args.iterations)

    if args.test_type in ["processor", "all"]:
        logger.info("=== Testing Wikipedia Processor ===")
        test_wikipedia_processor(
            landmark_ids[:2]
        )  # Use fewer landmarks for processor test


if __name__ == "__main__":
    main()
