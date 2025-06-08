#!/usr/bin/env python
"""
Demonstration script for the enhanced logging capabilities.

This script showcases the various logging enhancements including:
- Structured logging
- Performance monitoring
- Request context tracking
- Error classification
"""

import argparse
import logging
import random
import time
from typing import Dict

from nyc_landmarks.config.settings import Environment, LogProvider, settings
from nyc_landmarks.utils.logger import (
    get_logger,
    log_error,
    log_performance,
    log_with_context,
)

# Configure logger for this script
logger = get_logger(
    __name__,
    log_level=logging.DEBUG,
    log_to_console=True,
    log_to_file=True,
    structured=True,
)


class DemoOperation:
    """Demo operation to simulate API functionality."""

    def __init__(self, name: str, success_rate: float = 0.9, avg_time: float = 200.0):
        """Initialize with operation parameters."""
        self.name = name
        self.success_rate = success_rate
        self.avg_time = avg_time  # Average time in milliseconds

    def execute(self) -> Dict[str, object]:
        """Execute the operation and return results."""
        # Simulate operation with random duration
        start_time = time.time()

        # Add random jitter to the average time (±30%)
        jitter = random.uniform(0.7, 1.3)  # nosec B311
        duration = self.avg_time * jitter

        # Sleep to simulate processing time
        time.sleep(duration / 1000.0)  # Convert ms to seconds

        # Calculate actual duration
        actual_duration = (time.time() - start_time) * 1000  # Convert to ms

        # Determine if operation succeeds based on success rate
        success = random.random() < self.success_rate  # nosec B311

        # Log performance
        log_performance(
            logger,
            operation_name=self.name,
            duration_ms=actual_duration,
            success=success,
            extra={
                "operation_type": "demo",
                "expected_duration": self.avg_time,
                "jitter_factor": jitter,
            },
        )

        if not success:
            # Simulate an error
            error_type = random.choice(
                ["validation", "timeout", "dependency", "data"]
            )  # nosec B311
            error_msg = f"{error_type.capitalize()} error in {self.name}"

            try:
                # Raise an exception to get a stack trace
                raise RuntimeError(error_msg)
            except RuntimeError as e:
                # Log the error with our enhanced error logging
                log_error(
                    logger,
                    error=e,
                    error_type=error_type,
                    message=f"Error executing {self.name}",
                    extra={
                        "operation": self.name,
                        "duration_ms": actual_duration,
                        "expected_success_rate": self.success_rate,
                    },
                )

                # Return error response
                return {
                    "success": False,
                    "error": error_msg,
                    "duration_ms": actual_duration,
                }

        # Return success response
        return {
            "success": True,
            "operation": self.name,
            "duration_ms": actual_duration,
            "result": f"Completed {self.name} successfully",
        }


def simulate_request_context() -> Dict[str, str]:
    """Simulate a request context for demonstration purposes."""
    # Generate random request information
    request_ids = ["req-123456", "req-789012", "req-345678"]
    paths = ["/api/query/search", "/api/chat/message", "/api/landmarks"]
    client_ips = ["192.168.1.100", "10.0.0.5", "172.16.254.1"]
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    ]

    return {
        "request_id": random.choice(request_ids),  # nosec B311
        "request_path": random.choice(paths),  # nosec B311
        "client_ip": random.choice(client_ips),  # nosec B311
        "user_agent": random.choice(user_agents),  # nosec B311
    }


def run_standard_logging_demo() -> None:
    """Demonstrate standard logging features."""
    logger.info("Starting standard logging demonstration")

    # Basic logging at different levels
    logger.debug("This is a debug message with low-level details")
    logger.info("This is an informational message about normal operation")
    logger.warning("This is a warning that something might be wrong")
    logger.error("This is an error message about something that failed")

    # Logging with extra structured data
    logger.info(
        "User login successful",
        extra={
            "user_id": "user123",
            "login_method": "password",
            "session_id": "sess_abc123",
        },
    )

    # Logging exceptions
    try:
        10 / 0
    except Exception:
        logger.exception("An exception occurred during calculation")

    logger.info("Completed standard logging demonstration")


def run_enhanced_logging_demo(num_operations: int = 5) -> None:
    """Demonstrate enhanced logging features with simulated operations."""
    logger.info(
        "Starting enhanced logging demonstration",
        extra={"demo_type": "enhanced", "operations": num_operations},
    )

    # Define a set of demo operations with varying characteristics
    operations = [
        DemoOperation("vector_search", success_rate=0.95, avg_time=150.0),
        DemoOperation("embedding_generation", success_rate=0.99, avg_time=300.0),
        DemoOperation("database_query", success_rate=0.9, avg_time=80.0),
        DemoOperation("chat_completion", success_rate=0.85, avg_time=500.0),
        DemoOperation("pdf_processing", success_rate=0.8, avg_time=800.0),
    ]

    # Execute operations with simulated request context
    for _ in range(num_operations):
        # Simulate a new request context for each operation
        context = simulate_request_context()
        operation = random.choice(operations)  # nosec B311

        # Log the operation start with context
        log_with_context(
            logger,
            logging.INFO,
            f"Starting operation: {operation.name}",
            extra={
                "operation": operation.name,
                "expected_duration": operation.avg_time,
                **context,
            },
        )

        # Execute the operation
        result = operation.execute()

        # Log the result with context
        log_with_context(
            logger,
            logging.INFO if result["success"] else logging.ERROR,
            f"Operation {operation.name} {'completed' if result['success'] else 'failed'}",
            extra={"result": result, **context},
        )

        # Add a small delay between operations
        time.sleep(0.5)

    logger.info("Completed enhanced logging demonstration")


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Demonstrate enhanced logging capabilities"
    )
    parser.add_argument(
        "--num-operations",
        type=int,
        default=10,
        help="Number of simulated operations to run",
    )
    parser.add_argument(
        "--structured", action="store_true", help="Use structured (JSON) logging format"
    )
    parser.add_argument(
        "--provider",
        choices=["stdout", "google"],
        default=settings.LOG_PROVIDER.value,
        help="Logging provider to use",
    )
    args = parser.parse_args()

    # Configure global settings based on arguments
    settings.ENV = Environment.DEVELOPMENT
    settings.LOG_PROVIDER = LogProvider(args.provider)

    logger.info(
        "Starting logging demonstration script",
        extra={
            "num_operations": args.num_operations,
            "structured": args.structured,
            "log_provider": args.provider,
        },
    )

    # Run demonstrations
    run_standard_logging_demo()
    run_enhanced_logging_demo(args.num_operations)

    logger.info("Logging demonstration completed")


if __name__ == "__main__":
    main()
