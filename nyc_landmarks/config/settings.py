"""
Configuration settings for the NYC Landmarks Vector Database.

This module manages configuration and credentials for the application,
with support for retrieving secrets from Google Cloud Secret Manager
and fallback to environment variables for local development.
"""

import json
from enum import Enum
from typing import Any, Optional

from dotenv import load_dotenv

# Add error handling for Google Cloud Secret Manager import
try:
    from google.cloud import secretmanager

    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    print(
        "Warning: google.cloud.secretmanager not available - will use environment variables only"
    )
from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file if it exists
load_dotenv()


class Environment(str, Enum):
    """Application environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogProvider(str, Enum):
    """Available logging providers."""

    STDOUT = "stdout"
    GOOGLE = "google"


class Settings(BaseSettings):
    """Application settings and configuration."""

    # Environment settings
    ENV: Environment = Field(default=Environment.DEVELOPMENT)
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO)
    LOG_PROVIDER: LogProvider = Field(default=LogProvider.STDOUT)
    LOG_NAME_PREFIX: str = Field(default="nyc-landmarks-vector-db")

    def __init__(self, **kwargs: Any) -> None:
        """Initialize settings with environment-specific defaults."""
        super().__init__(**kwargs)

        # Automatically use Google Cloud Logging in production to prevent stdout duplication
        if (
            self.ENV == Environment.PRODUCTION
            and self.LOG_PROVIDER == LogProvider.STDOUT
        ):
            self.LOG_PROVIDER = LogProvider.GOOGLE

    # Google Cloud Secret Manager settings
    GCP_PROJECT_ID: Optional[str] = Field(default=None)
    USE_SECRET_MANAGER: bool = Field(default=False)

    # OpenAI API settings
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small")
    OPENAI_EMBEDDING_DIMENSIONS: int = Field(default=1536)  # For text-embedding-3-small
    OPENAI_API_BASE: Optional[str] = Field(default=None)

    # Pinecone settings
    PINECONE_API_KEY: str = Field(default="")
    PINECONE_ENVIRONMENT: str = Field(default="")
    PINECONE_INDEX_NAME: str = Field(default="nyc-landmarks")
    PINECONE_NAMESPACE: str = Field(default="landmarks")
    PINECONE_METRIC: str = Field(default="cosine")
    PINECONE_DIMENSIONS: int = Field(
        default=1536
    )  # Should match OPENAI_EMBEDDING_DIMENSIONS

    # Azure Blob Storage settings
    AZURE_STORAGE_CONNECTION_STRING: str = Field(default="")
    AZURE_STORAGE_CONTAINER_NAME: str = Field(default="")

    # CoreDataStore API settings
    COREDATASTORE_API_KEY: str = Field(default="")
    COREDATASTORE_USE_API: bool = Field(
        default=True
    )  # Set API as the default data source

    # Application settings
    APP_HOST: str = Field(default="0.0.0.0")  # nosec
    APP_PORT: int = Field(default=8000)
    # URL for production/deployed environment (optional)
    DEPLOYMENT_URL: Optional[str] = Field(default="https://vector-db.coredatastore.com")
    # Whether to show production URL in development swagger UI
    SHOW_PROD_URL_IN_DEV: bool = Field(default=True)

    # PDF processing settings
    CHUNK_SIZE: int = Field(default=1000)  # Token size for text chunks
    CHUNK_OVERLAP: int = Field(default=200)  # Token overlap between chunks

    # Chat settings
    CONVERSATION_TTL: int = Field(
        default=3600
    )  # Time to live for conversation history in seconds

    # Wikipedia API settings
    WIKIPEDIA_USER_AGENT: str = Field(
        default="NYCLandmarksVectorDB/1.0 (https://github.com/username/nyc-landmarks-vector-db; "
        "email@example.com) Python-Requests/2.31.0"
    )
    WIKIPEDIA_API_ENDPOINT: str = Field(
        default="https://api.wikimedia.org/service/lw/inference/v1/models/enwiki-articlequality:predict"
    )

    @field_validator("PINECONE_DIMENSIONS", mode="before")  # type: ignore[misc]
    @classmethod
    def match_embedding_dimensions(cls, v: int, info: ValidationInfo) -> int:
        """Ensure Pinecone dimensions match OpenAI embedding dimensions."""
        values = info.data
        embedding_dimensions = values.get("OPENAI_EMBEDDING_DIMENSIONS")
        if embedding_dimensions is not None:
            return int(embedding_dimensions)  # Ensure an integer is returned
        return v

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"  # Allow extra fields
    )


class SecretManager:
    """Google Cloud Secret Manager client for retrieving secrets."""

    def __init__(self, project_id: str):
        """Initialize the Google Cloud Secret Manager client.

        Args:
            project_id: GCP project ID
        """
        if not GOOGLE_CLOUD_AVAILABLE:
            raise ImportError("Google Cloud Secret Manager is not available")

        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id

    def get_secret(self, secret_id: str, version_id: str = "latest") -> str:
        """Retrieve a secret from Google Cloud Secret Manager.

        Args:
            secret_id: ID of the secret to retrieve
            version_id: Version of the secret (default: "latest")

        Returns:
            The secret value as a string
        """
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version_id}"
        response = self.client.access_secret_version(request={"name": name})
        return str(response.payload.data.decode("UTF-8"))


def load_settings_from_secrets(settings: Settings) -> Settings:
    """Load settings from Google Cloud Secret Manager.

    Args:
        settings: Existing settings object with GCP_PROJECT_ID set

    Returns:
        Updated settings object with values from Secret Manager
    """
    if not settings.USE_SECRET_MANAGER or not settings.GCP_PROJECT_ID:
        return settings

    try:
        secret_manager = SecretManager(settings.GCP_PROJECT_ID)

        # Define secrets to retrieve
        secrets_map = {
            "openai": {
                "OPENAI_API_KEY": "api_key",
                "OPENAI_EMBEDDING_MODEL": "embedding_model",
                "OPENAI_API_BASE": "api_base",
            },
            "pinecone": {
                "PINECONE_API_KEY": "api_key",
                "PINECONE_ENVIRONMENT": "environment",
                "PINECONE_INDEX_NAME": "index_name",
            },
            "azure_storage": {
                "AZURE_STORAGE_CONNECTION_STRING": "connection_string",
                "AZURE_STORAGE_CONTAINER_NAME": "container_name",
            },
            "coredatastore": {
                "COREDATASTORE_API_KEY": "api_key",
            },
        }

        # Retrieve secrets and update settings
        for secret_group, secret_keys in secrets_map.items():
            try:
                secret_value = secret_manager.get_secret(secret_group)
                secret_data = json.loads(secret_value)

                for setting_key, secret_key in secret_keys.items():
                    if secret_key in secret_data:
                        setattr(settings, setting_key, secret_data[secret_key])
            except Exception as e:
                # Log error and continue with environment variables
                # in a production environment, we would want better error handling
                print(f"Error retrieving secret {secret_group}: {e}")

    except Exception as e:
        # Log error and continue with environment variables
        print(f"Error initializing Secret Manager: {e}")

    return settings


# Load settings
settings = Settings()

# Try to load from Google Cloud Secret Manager if enabled and available
if settings.USE_SECRET_MANAGER and settings.GCP_PROJECT_ID and GOOGLE_CLOUD_AVAILABLE:
    try:
        settings = load_settings_from_secrets(settings)
    except Exception as e:
        print(f"Failed to load settings from Secret Manager: {e}")
        print("Using environment variables instead.")
elif settings.USE_SECRET_MANAGER and not GOOGLE_CLOUD_AVAILABLE:
    print("Secret Manager is enabled but google.cloud package is not available.")
    print("Using environment variables instead.")
