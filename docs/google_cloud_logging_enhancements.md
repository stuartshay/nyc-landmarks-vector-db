# Google Cloud Logging Enhancements

This document describes the enhanced logging capabilities implemented in the NYC Landmarks Vector DB project, focusing on the Google Cloud Logging integration.

## Overview

We've enhanced the logging system with several capabilities:

1. **Structured Logging**: All logs can now be formatted as structured JSON for better querying and analysis
1. **Request Context Tracking**: Request IDs and metadata are automatically propagated throughout the application
1. **Performance Monitoring**: Specialized logging for tracking operation performance
1. **Error Classification**: Standardized error categorization and logging
1. **Middleware Integration**: FastAPI middleware for automatic context propagation and performance tracking

## Core Components

### Request Context Tracking

The `nyc_landmarks/utils/request_context.py` module provides context variable management for tracking request information throughout the application lifecycle:

```python
# Get context information in any part of the application
from nyc_landmarks.utils.request_context import get_request_context

# Access request context
context = get_request_context()
request_id = context["request_id"]
```

The context variables include:

- `request_id`: Unique identifier for each request
- `request_path`: URL path of the request
- `client_ip`: Client IP address
- `user_agent`: User agent string
- `duration_ms`: Request processing duration (when available)

### Enhanced Logger

The `nyc_landmarks/utils/logger.py` module has been extended with:

1. **Structured Logging Formatter**: Outputs logs as JSON with standardized fields
1. **Context-Aware Logging**: Automatically includes request context in logs
1. **Specialized Logging Functions**:
   - `log_with_context`: Log with request context included
   - `log_performance`: Log operation performance metrics
   - `log_error`: Log errors with standardized classification

```python
# Example: Performance logging
from nyc_landmarks.utils.logger import get_logger, log_performance

logger = get_logger(__name__)

# Log operation performance
log_performance(
    logger,
    operation_name="vector_search",
    duration_ms=153.4,
    success=True,
    extra={"query_size": 512, "vector_count": 10000},
)
```

### API Middleware

The `nyc_landmarks/api/middleware.py` module provides:

1. **RequestContextMiddleware**: Automatically tracks request context
1. **PerformanceMonitoringMiddleware**: Logs performance metrics for all API endpoints

```python
# In main.py - already integrated
from nyc_landmarks.api.middleware import setup_api_middleware

# Configure all middleware
setup_api_middleware(app)
```

## Querying Logs in Google Cloud Console

### By Request ID

Track a specific request through the system:

```
jsonPayload.request_id="req-123456"
```

### By Performance Metrics

Find slow operations:

```
jsonPayload.metric_type="performance" AND jsonPayload.duration_ms>500
```

### By Error Type

Find specific categories of errors:

```
jsonPayload.error_type="validation"
```

### By Endpoint

View logs for a specific API endpoint:

```
jsonPayload.request_path="/api/query/search"
```

## Log Structure

All structured logs include these standard fields:

```json
{
  "timestamp": "2023-06-08T03:45:12.123Z",
  "severity": "INFO",
  "message": "Operation completed",
  "module": "query",
  "function": "search_text",
  "line": 42,
  "request_id": "req-123456",
  "request_path": "/api/query/search",
  "client_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "duration_ms": 153.4
}
```

Performance logs add:

```json
{
  "operation": "vector_search",
  "success": true,
  "metric_type": "performance"
}
```

Error logs add:

```json
{
  "error_type": "validation",
  "error_class": "ValueError",
  "error_message": "Invalid input parameter",
  "exception": {
    "type": "ValueError",
    "message": "Invalid input parameter",
    "traceback": ["Traceback (most recent call last):", "..."]
  }
}
```

## Usage Examples

### Basic Logging with Context

```python
from nyc_landmarks.utils.logger import get_logger, log_with_context
import logging

logger = get_logger(__name__)

log_with_context(
    logger,
    logging.INFO,
    "Processing landmark data",
    extra={"landmark_id": "LP-12345", "operation": "pdf_extraction"},
)
```

### Error Logging with Classification

```python
from nyc_landmarks.utils.logger import get_logger, log_error

logger = get_logger(__name__)

try:
    # Operation that might fail
    result = process_landmark(landmark_id)
except ValueError as e:
    log_error(
        logger,
        error=e,
        error_type="validation",
        message="Invalid landmark data",
        extra={"landmark_id": landmark_id},
    )
```

### Performance Tracking

```python
from nyc_landmarks.utils.logger import get_logger, log_performance
import time

logger = get_logger(__name__)

start_time = time.time()
try:
    # Operation to measure
    result = search_vectors(query, top_k=10)
    success = True
except Exception:
    success = False
    raise
finally:
    duration_ms = (time.time() - start_time) * 1000
    log_performance(
        logger,
        operation_name="vector_search",
        duration_ms=duration_ms,
        success=success,
        extra={"query_size": len(query), "top_k": 10},
    )
```

## Demonstration Script

A demonstration script is available at `scripts/demonstrate_logging.py` that shows how to use all of these features. Run it with:

```bash
python -m scripts.demonstrate_logging --structured --num-operations 5
```

For Google Cloud Logging output:

```bash
python -m scripts.demonstrate_logging --provider google --num-operations 5
```
