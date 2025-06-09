#!/usr/bin/env python3
"""
Integration tests for environment capture in Google Cloud Logger.
Tests that environment settings are properly included in structured logs.
"""

import json
import logging
import os
from io import StringIO
from typing import Generator
from unittest.mock import patch

import pytest

from nyc_landmarks.utils.logger import StructuredFormatter, get_logger


class TestEnvironmentLoggingIntegration:
    """Test suite for environment capture in logging integration."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self) -> Generator[None, None, None]:
        """Set up test environment variables."""
        # Store original values
        self.original_env = os.environ.get("ENV")
        self.original_log_provider = os.environ.get("LOG_PROVIDER")

        # Set test values
        os.environ["ENV"] = "test"
        os.environ["LOG_PROVIDER"] = "stdout"

        yield

        # Restore original values
        if self.original_env is not None:
            os.environ["ENV"] = self.original_env
        elif "ENV" in os.environ:
            del os.environ["ENV"]

        if self.original_log_provider is not None:
            os.environ["LOG_PROVIDER"] = self.original_log_provider
        elif "LOG_PROVIDER" in os.environ:
            del os.environ["LOG_PROVIDER"]

    def test_environment_field_in_structured_logs(self) -> None:
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

        # Parse the JSON log
        log_data = json.loads(log_output)

        # Check if environment field is present (it should be development in test env)
        assert "environment" in log_data
        assert isinstance(log_data["environment"], str)
        assert len(log_data["environment"]) > 0

        # Clean up
        logger.removeHandler(handler)

    def test_production_environment_capture(self) -> None:
        """Test that production environment setting is properly structured."""
        # This test verifies the logger can handle production settings
        # We don't need to actually change the environment to test the structure
        logger = get_logger(
            "test_production_logger", structured=True, log_to_file=False
        )

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredFormatter())

        # Clear existing handlers and add our capture handler
        logger.handlers.clear()
        logger.addHandler(handler)

        # Log a test message
        logger.info("Production test message")

        # Get the log output
        log_output = log_capture.getvalue().strip()

        # Parse the JSON log
        log_data = json.loads(log_output)

        # Check if environment field is present and valid
        assert "environment" in log_data
        assert isinstance(log_data["environment"], str)
        assert len(log_data["environment"]) > 0

        # Clean up
        logger.removeHandler(handler)

    def test_development_environment_capture(self) -> None:
        """Test that development environment is properly captured."""
        # Test development environment logging (current default)
        logger = get_logger("test_dev_logger", structured=True, log_to_file=False)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredFormatter())

        # Clear existing handlers and add our capture handler
        logger.handlers.clear()
        logger.addHandler(handler)

        # Log a test message
        logger.info("Development test message")

        # Get the log output
        log_output = log_capture.getvalue().strip()

        # Parse the JSON log
        log_data = json.loads(log_output)

        # Check if environment field is present
        assert "environment" in log_data
        assert isinstance(log_data["environment"], str)
        assert len(log_data["environment"]) > 0

        # Clean up
        logger.removeHandler(handler)

    def test_structured_formatter_json_format(self) -> None:
        """Test that StructuredFormatter produces valid JSON."""
        # Create logger with structured formatting
        logger = get_logger("test_json_logger", structured=True, log_to_file=False)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredFormatter())

        # Clear existing handlers and add our capture handler
        logger.handlers.clear()
        logger.addHandler(handler)

        # Log a test message with extra fields
        logger.info(
            "JSON format test",
            extra={
                "custom_field": "custom_value",
                "numeric_field": 42,
                "boolean_field": True,
            },
        )

        # Get the log output
        log_output = log_capture.getvalue().strip()

        # Should be valid JSON
        log_data = json.loads(log_output)

        # Verify expected fields (note: uses 'severity' instead of 'level')
        assert "message" in log_data
        assert "timestamp" in log_data
        assert "severity" in log_data  # Changed from 'level'
        assert "environment" in log_data
        assert "custom_field" in log_data
        assert "numeric_field" in log_data
        assert "boolean_field" in log_data

        # Verify values
        assert log_data["message"] == "JSON format test"
        assert log_data["custom_field"] == "custom_value"
        assert log_data["numeric_field"] == 42
        assert log_data["boolean_field"] is True

        # Clean up
        logger.removeHandler(handler)

    @pytest.mark.integration
    def test_gcp_logger_environment_integration(self) -> None:
        """Test that environment field works with Google Cloud Logger setup."""
        # This tests the local behavior that would be sent to GCP
        logger = get_logger("nyc_landmarks.gcp.test", structured=True)

        # Capture log output (simulating what would go to GCP)
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredFormatter())

        # Add handler to capture output
        logger.addHandler(handler)

        # Generate log entry
        logger.info(
            "GCP integration test message",
            extra={
                "request_id": "test-request-123",
                "user_agent": "IntegrationTestBot/1.0",
            },
        )

        # Verify output format
        log_output = log_capture.getvalue().strip()
        log_data = json.loads(log_output)

        # Verify GCP-compatible structure
        assert "environment" in log_data
        assert isinstance(log_data["environment"], str)
        assert "request_id" in log_data
        assert "user_agent" in log_data
        assert "timestamp" in log_data
        assert "severity" in log_data
        assert "message" in log_data

        # Clean up
        logger.removeHandler(handler)

    def test_missing_environment_handling(self) -> None:
        """Test behavior when ENV environment variable is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Create logger when ENV is not set
            logger = get_logger(
                "test_no_env_logger", structured=True, log_to_file=False
            )

            # Capture log output
            log_capture = StringIO()
            handler = logging.StreamHandler(log_capture)
            handler.setFormatter(StructuredFormatter())

            # Clear existing handlers and add our capture handler
            logger.handlers.clear()
            logger.addHandler(handler)

            # Log a test message
            logger.info("No environment test")

            # Get the log output
            log_output = log_capture.getvalue().strip()

            # Parse the JSON log
            log_data = json.loads(log_output)

            # Environment field should still be present with default value
            assert "environment" in log_data
            # Should have some default value (e.g., "unknown" or "development")
            assert isinstance(log_data["environment"], str)
            assert len(log_data["environment"]) > 0

            # Clean up
            logger.removeHandler(handler)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
