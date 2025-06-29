#!/usr/bin/env python3
"""
Test script to verify endpoint categorization and logging.
"""

from nyc_landmarks.api.middleware import _categorize_endpoint
from nyc_landmarks.utils.logger import get_logger, log_performance


def test_endpoint_categorization() -> None:
    """Test that endpoints are categorized correctly."""
    test_cases = [
        ("/api/query/search", "query"),
        ("/api/query/search_by_landmark", "query"),
        ("/api/chat/message", "chat"),
        ("/health", "health"),
        ("/", "other"),
        ("/api/unknown", "other"),
        ("/docs", "other"),
    ]

    print("Testing endpoint categorization:")
    print("=" * 50)

    for path, expected in test_cases:
        actual = _categorize_endpoint(path)
        status = "✓" if actual == expected else "✗"
        print(f"{status} {path:<30} -> {actual} (expected: {expected})")
    print()


def test_performance_logging() -> None:
    """Test that performance logging includes endpoint_category."""
    print("Testing performance logging with endpoint categories:")
    print("=" * 50)

    # Get logger with structured logging to see JSON output
    logger = get_logger("test_middleware", structured=True, log_to_file=False)

    # Test cases with different endpoint categories
    test_cases = [
        ("GET /api/query/search", "query"),
        ("POST /api/chat/message", "chat"),
        ("GET /health", "health"),
        ("GET /", "other"),
    ]

    for endpoint, category in test_cases:
        extra_data = {
            "endpoint": endpoint,
            "endpoint_category": category,
            "method": endpoint.split()[0],
            "path": endpoint.split()[1],
            "status_code": 200,
        }

        log_performance(
            logger,
            endpoint,
            123.45,
            success=True,
            extra=extra_data,
        )
        print(f"✓ Logged performance for {endpoint} (category: {category})")
    print()


if __name__ == "__main__":
    test_endpoint_categorization()
    test_performance_logging()
    print(
        "All tests completed! Check the log output above to verify the endpoint_category field is included."
    )
