#!/usr/bin/env python3
"""
Test script to verify GCP logging functionality.

This script tests:
1. GCP logging configuration
2. Log level filtering
3. Structured logging format
4. Proper handler cleanup
5. Log verification in GCP console

Usage:
    python scripts/test_gcp_logging.py [--test-type all|quick|verification]
"""

import argparse
import atexit
import logging
import sys
import time
from pathlib import Path
from typing import List

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from nyc_landmarks.config.settings import LogProvider, settings
from nyc_landmarks.utils.logger import get_logger

# Global list to store handlers for cleanup
_cloud_handlers: List[logging.Handler] = []


def cleanup_handlers() -> None:
    """Clean up logging handlers to prevent shutdown warnings."""
    for handler in _cloud_handlers:
        try:
            if hasattr(handler, 'close'):
                handler.close()
        except Exception as e:
            print(f"Warning: Failed to close handler: {e}")


def register_cleanup() -> None:
    """Register cleanup function to run at exit."""
    atexit.register(cleanup_handlers)


def test_basic_logging() -> bool:
    """Test basic logging functionality."""
    print("=== Testing Basic Logging ===")

    # Get logger with GCP provider
    logger = get_logger(
        name="test_gcp_logging",
        log_level=logging.INFO,
        provider=LogProvider.GOOGLE,
        structured=True,
    )

    # Store cloud handlers for cleanup
    for handler in logger.handlers:
        if hasattr(handler, 'transport'):  # CloudLoggingHandler has transport
            _cloud_handlers.append(handler)

    # Test different log levels
    logger.debug("This is a DEBUG message (should not appear in GCP)")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")

    # Test structured logging with extra fields
    logger.info(
        "Testing structured logging",
        extra={
            "test_id": "gcp_logging_test_001",
            "component": "logging_verification",
            "environment": settings.ENV.value,
            "timestamp": time.time(),
        },
    )

    print("Basic logging test completed")
    return True


def test_error_logging() -> bool:
    """Test error logging with exception information."""
    print("=== Testing Error Logging ===")

    logger = get_logger(name="test_gcp_logging_errors")

    try:
        # Intentionally cause an error
        _ = 1 / 0
    except ZeroDivisionError:
        logger.exception(
            "Test exception logging",
            extra={
                "error_type": "division_by_zero",
                "test_scenario": "exception_handling",
            },
        )

    print("Error logging test completed")
    return True


def test_performance_logging() -> bool:
    """Test performance and bulk logging."""
    print("=== Testing Performance Logging ===")

    logger = get_logger(name="test_gcp_logging_performance")

    start_time = time.time()

    # Send multiple log messages quickly
    for i in range(10):
        logger.info(
            f"Performance test message {i + 1}",
            extra={
                "iteration": i + 1,
                "test_type": "performance",
                "batch_id": "perf_test_001",
            },
        )
        time.sleep(0.1)  # Small delay to avoid overwhelming

    elapsed_time = time.time() - start_time
    logger.info(
        f"Performance test completed in {elapsed_time:.2f} seconds",
        extra={
            "total_messages": 10,
            "elapsed_time": elapsed_time,
            "messages_per_second": 10 / elapsed_time,
        },
    )

    print(f"Performance test completed in {elapsed_time:.2f} seconds")
    return True


def verify_gcp_logs() -> None:
    """Provide instructions for verifying logs in GCP Console."""
    print("=== GCP Log Verification Instructions ===")
    print("1. Go to GCP Console: https://console.cloud.google.com/logs")
    print(f"2. Select your project: {settings.GCP_PROJECT_ID}")
    print("3. Use the following filter to find test logs:")
    print("   resource.type=\"global\"")
    print(
        f"   logName=\"projects/{settings.GCP_PROJECT_ID}/logs/{settings.LOG_NAME_PREFIX}.test_gcp_logging\""
    )
    print("4. Look for logs with these components:")
    print("   - test_gcp_logging")
    print("   - test_gcp_logging_errors")
    print("   - test_gcp_logging_performance")
    print(f"5. Verify logs have environment label: {settings.ENV.value}")
    print("6. Check that structured fields are present in the log entries")
    print("\nAlternatively, use gcloud CLI:")
    print(
        f"gcloud logging read 'logName=\"projects/{settings.GCP_PROJECT_ID}/logs/{settings.LOG_NAME_PREFIX}.test_gcp_logging\"' --limit 50"
    )


def test_settings_verification() -> bool:
    """Verify GCP settings are properly configured."""
    print("=== Settings Verification ===")

    logger = get_logger(name="test_settings_verification")

    print(f"GCP Project ID: {settings.GCP_PROJECT_ID}")
    print(f"Log Provider: {settings.LOG_PROVIDER}")
    print(f"Environment: {settings.ENV.value}")
    print(f"Log Name Prefix: {settings.LOG_NAME_PREFIX}")

    # Test that we can create a GCP logging client
    try:
        from google.cloud import logging as gcp_logging

        client = gcp_logging.Client()
        project = client.project
        print(f"GCP Logging Client Created Successfully - Project: {project}")

        logger.info(
            "GCP settings verification completed",
            extra={
                "gcp_project": project,
                "settings_project": settings.GCP_PROJECT_ID,
                "verification_status": "success",
            },
        )
        return True

    except Exception as e:
        print(f"Error: Failed to create GCP logging client: {e}")
        logger.error(
            "GCP settings verification failed",
            extra={"error": str(e), "verification_status": "failed"},
        )
        return False


def main() -> int:
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test GCP logging functionality")
    parser.add_argument(
        "--test-type",
        choices=["all", "quick", "verification"],
        default="all",
        help="Type of test to run",
    )

    args = parser.parse_args()

    # Register cleanup function
    register_cleanup()

    print(f"Starting GCP Logging Tests (type: {args.test_type})")
    print(f"Project: {settings.GCP_PROJECT_ID}")
    print(f"Environment: {settings.ENV.value}")
    print()

    results = []

    if args.test_type in ["all", "quick"]:
        results.append(test_settings_verification())
        results.append(test_basic_logging())

        if args.test_type == "all":
            results.append(test_error_logging())
            results.append(test_performance_logging())

    if args.test_type in ["all", "verification"]:
        verify_gcp_logs()

    # Force flush and cleanup before exit
    print("\n=== Cleaning up logging handlers ===")
    cleanup_handlers()

    # Wait a moment for logs to be sent
    print("Waiting 2 seconds for logs to be sent to GCP...")
    time.sleep(2)

    # Print summary
    if results:
        success_count = sum(results)
        total_count = len(results)
        print("\n=== Test Summary ===")
        print(f"Tests passed: {success_count}/{total_count}")

        if success_count == total_count:
            print("✓ All tests passed!")
            return 0
        else:
            print("✗ Some tests failed")
            return 1
    else:
        print("\n=== Verification Complete ===")
        print("Check GCP Console to verify logs are appearing correctly.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
