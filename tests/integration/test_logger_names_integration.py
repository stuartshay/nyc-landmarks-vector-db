#!/usr/bin/env python3
"""
Integration tests for logger names and Google Cloud Logging filtering.
Tests that different logger names are properly configured for GCP filtering.
"""

import logging
from io import StringIO

import pytest

from nyc_landmarks.config.settings import settings
from nyc_landmarks.utils.logger import get_logger


class TestLoggerNamesIntegration:
    """Test suite for logger name configuration and GCP integration."""

    def test_log_name_prefix_configuration(self) -> None:
        """Test that LOG_NAME_PREFIX is properly configured."""
        assert settings.LOG_NAME_PREFIX is not None
        assert len(settings.LOG_NAME_PREFIX) > 0
        assert isinstance(settings.LOG_NAME_PREFIX, str)

    def test_log_provider_configuration(self) -> None:
        """Test that LOG_PROVIDER is properly configured."""
        assert settings.LOG_PROVIDER is not None
        # LOG_PROVIDER is an enum value, check the actual enum values
        from nyc_landmarks.config.settings import LogProvider

        assert settings.LOG_PROVIDER in [LogProvider.GOOGLE, LogProvider.STDOUT]

    def test_api_query_logger_creation(self) -> None:
        """Test that API query logger is created with correct name."""
        logger = get_logger("nyc_landmarks.api.query")

        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert "nyc_landmarks.api.query" in logger.name

    def test_main_logger_creation(self) -> None:
        """Test that main application logger is created with correct name."""
        logger = get_logger("nyc_landmarks.main")

        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert "nyc_landmarks.main" in logger.name

    def test_chat_logger_creation(self) -> None:
        """Test that chat API logger is created with correct name."""
        logger = get_logger("nyc_landmarks.api.chat")

        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert "nyc_landmarks.api.chat" in logger.name

    @pytest.mark.integration
    def test_logger_names_in_gcp_format(self) -> None:
        """Test that logger names follow GCP filtering format."""
        # Test different logger configurations
        test_loggers = [
            "nyc_landmarks.api.query",
            "nyc_landmarks.main",
            "nyc_landmarks.api.chat",
            "nyc_landmarks.utils.vector",
            "nyc_landmarks.processing.wikipedia",
        ]

        for logger_name in test_loggers:
            logger = get_logger(logger_name)

            # Verify logger name structure
            assert logger_name in logger.name

            # Check that logger name would be compatible with GCP filtering
            expected_gcp_name = f"{settings.LOG_NAME_PREFIX}.{logger_name}"
            assert len(expected_gcp_name) < 256  # GCP logger name limit

    @pytest.mark.integration
    def test_log_messages_contain_proper_metadata(self) -> None:
        """Test that log messages contain proper metadata for GCP filtering."""
        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)

        # Test each logger type
        loggers_to_test = [
            ("nyc_landmarks.api.query", "Test API query log message"),
            ("nyc_landmarks.main", "Test main application log message"),
            ("nyc_landmarks.api.chat", "Test chat API log message"),
        ]

        for logger_name, test_message in loggers_to_test:
            log_capture.truncate(0)
            log_capture.seek(0)

            logger = get_logger(logger_name)
            logger.addHandler(handler)

            # Generate test log message
            logger.info(test_message)

            # Verify log output contains message
            log_output = log_capture.getvalue()
            assert test_message in log_output

            # Clean up
            logger.removeHandler(handler)

    def test_gcp_logger_filtering_patterns(self) -> None:
        """Test that logger names support expected GCP filtering patterns."""
        # Test patterns that should be filterable in GCP
        patterns = [
            f"{settings.LOG_NAME_PREFIX}.*",  # All logs from this app
            f"{settings.LOG_NAME_PREFIX}.nyc_landmarks.api.*",  # All API logs
            f"{settings.LOG_NAME_PREFIX}.nyc_landmarks.api.query",  # Specific query logs
            f"{settings.LOG_NAME_PREFIX}.nyc_landmarks.main",  # Main app logs
        ]

        for pattern in patterns:
            # Verify pattern is valid (no special characters that would break filtering)
            assert not any(char in pattern for char in ['?', '[', ']', '{', '}'])

            # Verify pattern follows expected naming convention
            assert pattern.startswith(settings.LOG_NAME_PREFIX)

    @pytest.mark.integration
    def test_logger_hierarchy_structure(self) -> None:
        """Test that logger hierarchy supports GCP log organization."""
        # Create loggers in hierarchical structure
        parent_logger = get_logger("nyc_landmarks")
        api_logger = get_logger("nyc_landmarks.api")
        query_logger = get_logger("nyc_landmarks.api.query")
        chat_logger = get_logger("nyc_landmarks.api.chat")

        # Verify hierarchy relationships
        assert "nyc_landmarks" in parent_logger.name
        assert "nyc_landmarks.api" in api_logger.name
        assert "nyc_landmarks.api.query" in query_logger.name
        assert "nyc_landmarks.api.chat" in chat_logger.name

        # Verify names support hierarchical filtering
        assert api_logger.name.startswith("nyc_landmarks")
        assert query_logger.name.startswith("nyc_landmarks.api")
        assert chat_logger.name.startswith("nyc_landmarks.api")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
