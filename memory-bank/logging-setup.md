# Google Cloud Logging Setup

*2025-06-05*

This document outlines how application logging can be routed to Google Cloud Logging. The logging layer is provider‑agnostic so that additional providers can be supported in the future.

## Enabling Cloud Logging

Set the environment variable `LOG_PROVIDER` to `google` in the deployment configuration. When running locally or when the variable is set to `stdout`, logs are written to the console and optional log files.

The API automatically configures the Google Cloud client when this provider is selected. No code changes are required when deploying to Cloud Run.

## Extensibility

The `get_logger` helper accepts a `provider` argument and attaches provider‑specific handlers. New providers can be added by implementing additional handlers in `nyc_landmarks.utils.logger`.
