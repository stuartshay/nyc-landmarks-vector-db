# API Input Validation and Warning Logs

## Overview

The NYC Landmarks Vector DB API now includes comprehensive input validation with warning logs sent to Google Cloud Logging. This ensures that invalid requests are properly logged for security monitoring and debugging purposes.

## Validation Features

### Text Query Validation

- **Empty Query Check**: Rejects empty or whitespace-only queries
- **Length Validation**: Limits queries to 1000 characters
- **Suspicious Content Detection**: Identifies potential XSS attacks, script injection, and malicious content
- **Pattern Matching**: Detects common security threats like:
  - `<script>` tags
  - `javascript:` URLs
  - Event handlers (`onload=`, `onclick=`, etc.)
  - Data URLs with HTML content

### Parameter Validation

- **Landmark ID**: Must be alphanumeric with hyphens/underscores, max 100 characters
- **Session ID**: Must be alphanumeric with hyphens/underscores, max 200 characters
- **Top K**: Must be between 1 and 50 (Pydantic also enforces 1-20 for some endpoints)
- **Source Type**: Must be either "wikipedia" or "pdf"

## Warning Log Structure

All validation warnings are logged to Google Cloud Logging with the following structure:

### Log Metadata

- **Logger Name**: `nyc-landmarks-vector-db.nyc_landmarks.utils.validation`
- **Severity**: `WARNING`
- **Source Location**: Shows the exact file, function, and line number

### Log Fields

Each validation warning includes:

- `validation_error`: Type of validation error (e.g., "empty_query", "suspicious_content")
- `endpoint`: The API endpoint being called
- `client_ip`: Client's IP address (when available)
- `user_agent`: Client's user agent string
- Additional context specific to the validation error

### Validation Error Types

- `empty_query`: Query is empty or contains only whitespace
- `query_too_long`: Query exceeds 1000 character limit
- `suspicious_content`: Potentially malicious content detected
- `invalid_landmark_id_format`: Landmark ID contains invalid characters
- `landmark_id_too_long`: Landmark ID exceeds 100 characters
- `invalid_session_id_format`: Session ID contains invalid characters
- `session_id_too_long`: Session ID exceeds 200 characters
- `invalid_top_k_negative`: top_k parameter is less than 1
- `top_k_too_large`: top_k parameter exceeds 50
- `invalid_source_type`: source_type is not "wikipedia" or "pdf"
- `missing_landmark_id`: Required landmark_id is missing

## Filtering Validation Logs

### Get all validation warnings:

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db.nyc_landmarks.utils.validation" AND severity="WARNING"' --project=velvety-byway-327718
```

### Filter by validation error type:

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.validation_error="suspicious_content"' --project=velvety-byway-327718
```

### Filter by endpoint:

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.endpoint="/api/query/search"' --project=velvety-byway-327718
```

### Filter by client IP:

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.client_ip="192.168.1.100"' --project=velvety-byway-327718
```

## Implementation Details

### ValidationLogger Class

The `ValidationLogger` class in `nyc_landmarks/utils/validation.py` provides static methods for:

- `validate_text_query()`: Validates query text
- `validate_landmark_id()`: Validates landmark identifiers
- `validate_top_k()`: Validates result count parameters
- `validate_source_type()`: Validates source type filters
- `validate_session_id()`: Validates session/conversation identifiers
- `log_validation_success()`: Logs successful validations

### API Integration

Validation is integrated into the following endpoints:

- `POST /api/query/search` - Text search validation
- `POST /api/query/search_by_landmark` - Landmark-specific search validation
- `POST /api/chat/message` - Chat message validation

### Client Information Extraction

The `get_client_info()` function extracts:

- Client IP address from the FastAPI request object
- User-Agent header for identifying the client application

## Security Benefits

1. **Attack Detection**: Identifies potential XSS, injection, and other attacks
1. **Monitoring**: Provides visibility into invalid request patterns
1. **Debugging**: Helps identify client-side issues and integration problems
1. **Compliance**: Maintains audit logs for security and compliance requirements
1. **Rate Limiting**: Can be used to identify clients making excessive invalid requests

## Usage Examples

### Querying Recent Validation Warnings

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db.nyc_landmarks.utils.validation" AND severity="WARNING" AND timestamp>="2025-06-08T00:00:00Z"' --project=velvety-byway-327718
```

### Analyzing Suspicious Activity

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.validation_error="suspicious_content"' --limit=50 --format="table(timestamp,jsonPayload.client_ip,jsonPayload.user_agent,jsonPayload.query_excerpt)" --project=velvety-byway-327718
```

### Monitoring Invalid Source Types

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.validation_error="invalid_source_type"' --format="table(timestamp,jsonPayload.source_type,jsonPayload.endpoint)" --project=velvety-byway-327718
```
