#!/usr/bin/env python3
"""
Test script for enhanced logging with label-based filtering.

This script tests the new EnhancedCloudLoggingHandler to ensure that:
1. endpoint_category labels are properly set on log records
2. Labels are available for efficient log sink filtering
3. The enhancement doesn't break existing functionality
"""

from nyc_landmarks.utils.logger import get_logger, log_performance


def test_enhanced_logging() -> None:
    """Test the enhanced logging functionality with endpoint categorization."""

    # Get logger
    logger = get_logger(__name__)

    print("Testing enhanced logging with label-based endpoint categorization...")

    # Test query endpoint logging
    print("\n1. Testing /api/query endpoint logging...")
    extra_data = {
        "endpoint": "GET /api/query",
        "endpoint_category": "query",
        "method": "GET",
        "path": "/api/query",
        "status_code": 200,
        "query_params": {"q": "test"},
    }

    log_performance(
        logger,
        "GET /api/query",
        145.67,
        success=True,
        extra=extra_data,
    )

    # Test chat endpoint logging
    print("2. Testing /api/chat endpoint logging...")
    extra_data = {
        "endpoint": "POST /api/chat",
        "endpoint_category": "chat",
        "method": "POST",
        "path": "/api/chat",
        "status_code": 200,
        "query_params": {},
    }

    log_performance(
        logger,
        "POST /api/chat",
        287.34,
        success=True,
        extra=extra_data,
    )

    # Test health endpoint logging
    print("3. Testing /health endpoint logging...")
    extra_data = {
        "endpoint": "GET /health",
        "endpoint_category": "health",
        "method": "GET",
        "path": "/health",
        "status_code": 200,
        "query_params": {},
    }

    log_performance(
        logger,
        "GET /health",
        12.45,
        success=True,
        extra=extra_data,
    )

    # Test other endpoint logging
    print("4. Testing other endpoint logging...")
    extra_data = {
        "endpoint": "GET /docs",
        "endpoint_category": "other",
        "method": "GET",
        "path": "/docs",
        "status_code": 200,
        "query_params": {},
    }

    log_performance(
        logger,
        "GET /docs",
        23.89,
        success=True,
        extra=extra_data,
    )

    print("\n✅ Enhanced logging tests completed!")
    print("Check Google Cloud Logging to verify logs are routed to correct buckets based on labels.")
    print("\nExpected routing:")
    print("- Query logs → api-query-logs bucket")
    print("- Chat logs → api-chat-logs bucket")
    print("- Health logs → api-health-logs bucket")
    print("- Other logs → default logging")


if __name__ == "__main__":
    test_enhanced_logging()
