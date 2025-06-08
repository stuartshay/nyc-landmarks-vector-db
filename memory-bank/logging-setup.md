# Google Cloud Logging Setup

*Updated: 2025-06-08*

This document outlines how application logging can be routed to Google Cloud Logging. The logging layer is provider‑agnostic so that additional providers can be supported in the future.

## Recent Enhancements

Several major enhancements have been implemented to improve the logging system:

1. **Structured Logging**: Added JSON-formatted structured logging with standardized fields
1. **Request Context Tracking**: Implemented request ID and metadata propagation across the application
1. **Performance Monitoring**: Added specialized logging for tracking operation durations and success rates
1. **Error Classification**: Created standardized error categorization for better filtering
1. **FastAPI Middleware**: Implemented automatic request tracking and performance monitoring
1. **Enhanced Documentation**: Created comprehensive documentation in `docs/google_cloud_logging_enhancements.md`

A demonstration script `scripts/demonstrate_logging.py` has been created to showcase these capabilities.

## Enabling Cloud Logging

Set the environment variable `LOG_PROVIDER` to `google` in the deployment configuration. When running locally or when the variable is set to `stdout`, logs are written to the console and optional log files.

The API automatically configures the Google Cloud client when this provider is selected. No code changes are required when deploying to Cloud Run.

## Structured Logging

The logger now supports structured logging with standardized fields. To enable structured logging:

```python
logger = get_logger(__name__, structured=True)
```

When using Google Cloud Logging, structured logging is enabled by default. The structured format includes:

- Standard metadata (timestamp, severity, message, module, line, etc.)
- Request context when available (request_id, path, client_ip, etc.)
- Custom fields via the `extra` parameter

## Request Context Tracking

The application now automatically tracks request context across all components using context variables:

```python
from nyc_landmarks.utils.request_context import get_request_context

# Get the current request information
context = get_request_context()
request_id = context["request_id"]
```

FastAPI middleware has been implemented to automatically propagate this context.

## Enhanced Logging Helpers

Several specialized logging helpers have been added:

```python
# Log with request context
log_with_context(logger, logging.INFO, "Message", extra={"key": "value"})

# Log performance metrics
log_performance(logger, "operation_name", duration_ms=153.4, success=True)

# Log errors with classification
log_error(logger, error, "validation", "Error message")
```

## Extensibility

The `get_logger` helper accepts a `provider` argument and attaches provider‑specific handlers. New providers can be added by implementing additional handlers in `nyc_landmarks.utils.logger`.

## Further Documentation

For more detailed information, usage examples, and query patterns, see `docs/google_cloud_logging_enhancements.md`.
