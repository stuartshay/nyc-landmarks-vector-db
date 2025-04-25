"""
Tests for the configuration settings module.
"""

import os
from unittest.mock import patch

from nyc_landmarks.config.settings import Environment, LogLevel, Settings


def test_settings_defaults() -> None:
    """Test that Settings has the expected default values."""
    settings = Settings()

    # Check default environment settings
    assert settings.ENV == Environment.DEVELOPMENT
    assert settings.LOG_LEVEL == LogLevel.INFO

    # Check default Google Cloud Secret Manager settings
    assert settings.USE_SECRET_MANAGER is False
    assert settings.GCP_PROJECT_ID is None

    # Check default OpenAI settings
    assert settings.OPENAI_EMBEDDING_MODEL == "text-embedding-3-small"
    assert settings.OPENAI_EMBEDDING_DIMENSIONS == 1536

    # Check default Pinecone settings
    assert settings.PINECONE_INDEX_NAME == "nyc-landmarks"
    assert settings.PINECONE_NAMESPACE == "landmarks"
    assert settings.PINECONE_METRIC == "cosine"
    assert (
        settings.PINECONE_DIMENSIONS == 1536
    )  # Should match OPENAI_EMBEDDING_DIMENSIONS

    # Check default application settings
    assert settings.APP_HOST == "0.0.0.0"
    assert isinstance(settings.APP_PORT, int)

    # Check default PDF processing settings
    assert settings.CHUNK_SIZE == 1000
    assert settings.CHUNK_OVERLAP == 200


def test_pinecone_dimensions_match_embedding_dimensions() -> None:
    """Test that Pinecone dimensions match OpenAI embedding dimensions."""
    test_settings = {
        "OPENAI_EMBEDDING_DIMENSIONS": "3072",  # text-embedding-3-large
    }

    with patch.dict(os.environ, test_settings):
        settings = Settings()
        assert settings.OPENAI_EMBEDDING_DIMENSIONS == 3072
        assert (
            settings.PINECONE_DIMENSIONS == 3072
        )  # Should match OPENAI_EMBEDDING_DIMENSIONS


def test_environment_enum() -> None:
    """Test the Environment enum."""
    assert Environment.DEVELOPMENT.value == "development"
    assert Environment.STAGING.value == "staging"
    assert Environment.PRODUCTION.value == "production"


def test_log_level_enum() -> None:
    """Test the LogLevel enum."""
    assert LogLevel.DEBUG.value == "DEBUG"
    assert LogLevel.INFO.value == "INFO"
    assert LogLevel.WARNING.value == "WARNING"
    assert LogLevel.ERROR.value == "ERROR"
    assert LogLevel.CRITICAL.value == "CRITICAL"
