#!/usr/bin/env python3
"""
Test script to verify logger names for Google Cloud Logging filtering.
"""

from nyc_landmarks.config.settings import settings
from nyc_landmarks.utils.logger import get_logger

# Test different logger names to see what gets sent to GCP
print(f"LOG_NAME_PREFIX: {settings.LOG_NAME_PREFIX}")
print(f"LOG_PROVIDER: {settings.LOG_PROVIDER}")

# Create loggers with different names
api_logger = get_logger("nyc_landmarks.api.query")
main_logger = get_logger("nyc_landmarks.main")
chat_logger = get_logger("nyc_landmarks.api.chat")

# Generate test log messages
print("\nGenerating test log messages...")

api_logger.info("Test API query log message - this should appear in GCP with logger name: nyc-landmarks-vector-db.nyc_landmarks.api.query")
main_logger.info("Test main application log message - this should appear in GCP with logger name: nyc-landmarks-vector-db.nyc_landmarks.main")
chat_logger.info("Test chat API log message - this should appear in GCP with logger name: nyc-landmarks-vector-db.nyc_landmarks.api.chat")

print("Test log messages sent to Google Cloud Logging")
print("You should be able to filter logs in GCP by:")
print(f"- Logger name starts with: {settings.LOG_NAME_PREFIX}")
print(f"- Specific loggers like: {settings.LOG_NAME_PREFIX}.nyc_landmarks.api.query")
print(f"- Module-specific: {settings.LOG_NAME_PREFIX}.nyc_landmarks.api.*")
