#!/usr/bin/env python3
"""
Test script to verify that the Google Cloud Logger captures the environment setting.
"""

import json
import os
from io import StringIO

# Set environment for testing
os.environ["ENV"] = "production"
os.environ["LOG_PROVIDER"] = "stdout"  # Use stdout for testing

import logging

from nyc_landmarks.utils.logger import StructuredFormatter, get_logger


def test_environment_in_logs() -> None:
    """Test that environment is included in structured logs."""

    # Create a logger with structured formatting
    logger = get_logger("test_logger", structured=True, log_to_file=False)

    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(StructuredFormatter())

    # Clear existing handlers and add our capture handler
    logger.handlers.clear()
    logger.addHandler(handler)

    # Log a test message
    logger.info("Test message for environment capture")

    # Get the log output
    log_output = log_capture.getvalue().strip()

    print("Raw log output:")
    print(log_output)

    # Parse the JSON log
    try:
        log_data = json.loads(log_output)
        print("\nParsed log data:")
        print(json.dumps(log_data, indent=2))

        # Check if environment field is present
        if "environment" in log_data:
            print(f"\n✅ Environment field found: {log_data['environment']}")
            if log_data["environment"] == "production":
                print("✅ Environment correctly set to 'production'")
            else:
                print(f"❌ Environment is '{log_data['environment']}', expected 'production'")
        else:
            print("❌ Environment field not found in log data")

    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse log output as JSON: {e}")


if __name__ == "__main__":
    print("Testing environment capture in Google Cloud Logger...")
    test_environment_in_logs()
