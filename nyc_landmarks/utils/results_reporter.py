"""Results reporting utilities for processing scripts."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

from nyc_landmarks.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessingStatistics:
    """Statistics for processing operations."""

    total_landmarks: int = 0
    successful_landmarks: int = 0
    failed_landmarks: int = 0
    landmarks_with_articles: int = 0
    landmarks_without_articles: int = 0
    total_articles_processed: int = 0
    total_chunks_embedded: int = 0
    total_processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    landmark_results: Dict[str, Any] = field(default_factory=dict)
    skipped_landmarks: Set[str] = field(default_factory=set)


def calculate_statistics(
    landmark_results: Dict[str, Any],
    total_processing_time: float,
    errors: List[str],
    skipped_landmarks: Set[str],
) -> ProcessingStatistics:
    """Calculate comprehensive processing statistics."""
    stats = ProcessingStatistics(
        total_processing_time=total_processing_time,
        errors=errors,
        landmark_results=landmark_results,
        skipped_landmarks=skipped_landmarks,
    )

    stats.total_landmarks = len(landmark_results)

    for landmark_id, result in landmark_results.items():
        if result.get("success", False):
            stats.successful_landmarks += 1
            articles_processed = result.get("articles_processed", 0)
            chunks_embedded = result.get("chunks_embedded", 0)

            if articles_processed > 0:
                stats.landmarks_with_articles += 1
                stats.total_articles_processed += articles_processed
                stats.total_chunks_embedded += chunks_embedded
            else:
                stats.landmarks_without_articles += 1
        else:
            stats.failed_landmarks += 1

    return stats


def print_statistics(
    stats: ProcessingStatistics,
    verbose: bool = False,
) -> None:
    """Print comprehensive processing statistics."""
    print("\n" + "=" * 80)
    print("PROCESSING STATISTICS")
    print("=" * 80)

    # Basic counts
    print(f"Total landmarks:                 {stats.total_landmarks}")
    print(f"Successful landmarks:            {stats.successful_landmarks}")
    print(f"Failed landmarks:                {stats.failed_landmarks}")
    print(f"Skipped landmarks:               {len(stats.skipped_landmarks)}")
    print()

    # Article-specific statistics
    print(f"Landmarks with Wikipedia:        {stats.landmarks_with_articles}")
    print(f"Landmarks without Wikipedia:     {stats.landmarks_without_articles}")
    print(f"Total articles processed:        {stats.total_articles_processed}")
    print(f"Total chunks embedded:           {stats.total_chunks_embedded}")
    print()

    # Performance metrics
    print(f"Total processing time:           {stats.total_processing_time:.2f} seconds")
    if stats.successful_landmarks > 0:
        avg_time = stats.total_processing_time / stats.successful_landmarks
        print(f"Average time per landmark:       {avg_time:.2f} seconds")
    print()

    # Success rates
    if stats.total_landmarks > 0:
        success_rate = (stats.successful_landmarks / stats.total_landmarks) * 100
        print(f"Success rate:                    {success_rate:.1f}%")

        if stats.landmarks_with_articles > 0:
            wikipedia_rate = (
                stats.landmarks_with_articles / stats.total_landmarks
            ) * 100
            print(f"Wikipedia coverage rate:         {wikipedia_rate:.1f}%")

    # Error summary
    if stats.errors:
        print(f"\nErrors encountered:              {len(stats.errors)}")

    # Verbose details
    if verbose:
        print_list_summary(
            "Skipped landmarks",
            list(stats.skipped_landmarks),
            max_items=10,
        )

        if stats.errors:
            print_list_summary(
                "Errors",
                stats.errors,
                max_items=10,
            )

        # Show landmark details
        successful_with_articles = [
            landmark_id
            for landmark_id, result in stats.landmark_results.items()
            if result.get("success", False) and result.get("articles_processed", 0) > 0
        ]
        print_list_summary(
            "Landmarks with Wikipedia articles",
            successful_with_articles,
            max_items=15,
        )

        successful_without_articles = [
            landmark_id
            for landmark_id, result in stats.landmark_results.items()
            if result.get("success", False) and result.get("articles_processed", 0) == 0
        ]
        print_list_summary(
            "Landmarks without Wikipedia articles",
            successful_without_articles,
            max_items=15,
        )

        failed_landmarks = [
            landmark_id
            for landmark_id, result in stats.landmark_results.items()
            if not result.get("success", False)
        ]
        print_list_summary(
            "Failed landmarks",
            failed_landmarks,
            max_items=15,
        )


def print_list_summary(
    title: str,
    items: List[str],
    max_items: int = 10,
) -> None:
    """Print a summary of a list with optional truncation."""
    if not items:
        return

    print(f"\n{title} ({len(items)} total):")
    displayed_items = items[:max_items]
    for item in displayed_items:
        print(f"  - {item}")

    if len(items) > max_items:
        remaining = len(items) - max_items
        print(f"  ... and {remaining} more")


def determine_exit_status(
    stats: ProcessingStatistics,
    min_success_rate: float = 0.8,
) -> int:
    """Determine appropriate exit status based on processing results."""
    if stats.total_landmarks == 0:
        logger.warning("No landmarks were processed")
        return 1

    success_rate = stats.successful_landmarks / stats.total_landmarks

    if success_rate < min_success_rate:
        logger.warning(
            f"Success rate {success_rate:.1%} is below minimum threshold {min_success_rate:.1%}"
        )
        return 1

    if stats.errors:
        logger.warning(f"Processing completed with {len(stats.errors)} errors")
        return 0  # Still return success if most landmarks processed

    logger.info("Processing completed successfully")
    return 0


def print_results(
    landmark_results: Dict[str, Any],
    total_processing_time: float,
    errors: List[str],
    skipped_landmarks: Set[str],
    verbose: bool = False,
) -> int:
    """
    Print comprehensive processing results and return appropriate exit code.

    Args:
        landmark_results: Dictionary mapping landmark IDs to processing results
        total_processing_time: Total time spent processing
        errors: List of errors encountered during processing
        skipped_landmarks: Set of landmark IDs that were skipped
        verbose: Whether to print detailed verbose output

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Calculate statistics
    stats = calculate_statistics(
        landmark_results,
        total_processing_time,
        errors,
        skipped_landmarks,
    )

    # Print statistics
    print_statistics(stats, verbose)

    # Determine and return exit status
    exit_code = determine_exit_status(stats)

    if exit_code == 0:
        print("\n✅ Processing completed successfully!")
    else:
        print("\n❌ Processing completed with issues.")

    return exit_code
