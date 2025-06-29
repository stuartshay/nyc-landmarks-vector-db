# POST Request Body Logging Implementation

## Overview

The NYC Landmarks Vector Database API now includes comprehensive request body logging for POST endpoints. This feature captures and logs the request payloads sent to specific API endpoints for debugging, monitoring, and analytics purposes.

## Implementation Details

### New Middleware: RequestBodyLoggingMiddleware

The request body logging is implemented as FastAPI middleware (`RequestBodyLoggingMiddleware`) that:

1. **Captures POST request bodies** for specific endpoints
1. **Sanitizes sensitive data** before logging
1. **Limits log size** to prevent excessive logging
1. **Preserves request body** for normal API processing

### Configuration

#### Enabled Endpoints

Request body logging is enabled for these endpoints:

- `/api/query/search` - Vector search queries
- `/api/query/search/landmark` - Landmark-specific searches
- `/api/chat/message` - Chat API requests

#### Security Features

- **Field Redaction**: Sensitive fields (password, token, secret, key, authorization) are redacted
- **Size Limits**: Request bodies larger than 2KB are not logged (only size is recorded)
- **String Truncation**: Very long string values (>500 chars) are truncated
- **Nested Sanitization**: Recursively sanitizes nested JSON objects

#### Log Structure

Request body logs include these fields:

```json
{
  "message": "POST request body logged",
  "endpoint": "/api/query/search",
  "endpoint_category": "query",
  "method": "POST",
  "path": "/api/query/search",
  "request_body": {
    "query": "What is the history of the Lefferts Family?",
    "source_type": "wikipedia",
    "top_k": 5
  },
  "body_size_bytes": 89,
  "metric_type": "request_body",
  "client_ip": "169.254.169.126",
  "user_agent": "curl/7.88.1",
  "content_type": "application/json"
}
```

## Querying Request Body Logs

### Filter for Request Body Logs

To query request body logs specifically:

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.metric_type="request_body"' \
  --project=velvety-byway-327718 \
  --limit=10 \
  --format=json
```

### Filter by Endpoint

To see request bodies for specific endpoints:

```bash
# Query endpoint logs
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.endpoint_category="query" AND jsonPayload.metric_type="request_body"' \
  --project=velvety-byway-327718 \
  --limit=5

# Chat endpoint logs
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.endpoint_category="chat" AND jsonPayload.metric_type="request_body"' \
  --project=velvety-byway-327718 \
  --limit=5
```

### Combined Performance + Request Body Query

To see both performance and request body logs for the same requests:

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.endpoint_category="query" AND (jsonPayload.metric_type="performance" OR jsonPayload.metric_type="request_body")' \
  --project=velvety-byway-327718 \
  --limit=10 \
  --format="table(timestamp,jsonPayload.metric_type,jsonPayload.endpoint,jsonPayload.duration_ms,jsonPayload.body_size_bytes)"
```

### Filter by Request Content

To find requests containing specific query terms:

```bash
# Find requests about "Empire State Building"
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.metric_type="request_body" AND jsonPayload.request_body.query:"Empire State Building"' \
  --project=velvety-byway-327718

# Find requests with specific source_type
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.metric_type="request_body" AND jsonPayload.request_body.source_type="wikipedia"' \
  --project=velvety-byway-327718
```

### Recent Activity Analysis

To analyze recent API usage patterns:

```bash
# Last hour's requests with bodies
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.metric_type="request_body" AND timestamp>="'$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)'"' \
  --project=velvety-byway-327718 \
  --format="table(timestamp,jsonPayload.client_ip,jsonPayload.request_body.query,jsonPayload.body_size_bytes)"
```

## Use Cases

### 1. Debugging API Issues

When users report problems, you can examine their exact request:

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.metric_type="request_body" AND jsonPayload.client_ip="CLIENT_IP"' \
  --project=velvety-byway-327718
```

### 2. Query Analysis

Understand what users are searching for:

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.metric_type="request_body"' \
  --project=velvety-byway-327718 \
  --format="value(jsonPayload.request_body.query)" \
  --limit=20
```

### 3. Performance Correlation

Correlate slow requests with their content:

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.endpoint_category="query" AND jsonPayload.metric_type="performance" AND jsonPayload.duration_ms>5000' \
  --project=velvety-byway-327718 \
  --format="table(timestamp,jsonPayload.duration_ms,jsonPayload.endpoint)"
```

### 4. Usage Analytics

Track API usage patterns:

```bash
# Count requests by source type
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.metric_type="request_body"' \
  --project=velvety-byway-327718 \
  --format="value(jsonPayload.request_body.source_type)" | sort | uniq -c
```

## Security and Privacy

### Data Protection

- Sensitive fields are automatically redacted
- Large payloads are not logged to prevent log spam
- Logs are stored in Google Cloud Logging with appropriate access controls

### Compliance

- Request body logging helps with audit trails
- Logs can be used for security monitoring
- Retention policies follow Google Cloud Logging settings

## Integration with Existing Logging

The request body logging integrates seamlessly with existing logging:

1. **Performance Logs**: Still available with `metric_type="performance"`
1. **Validation Logs**: Validation warnings continue as before
1. **Error Logs**: Application errors are still logged normally
1. **Request Body Logs**: New logs with `metric_type="request_body"`

## Deployment

The middleware is automatically included when the application starts. No configuration changes are needed beyond deploying the updated code.

## Example Usage Session

```bash
# 1. Make a request
curl -X POST https://vector-db.coredatastore.com/api/query/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Brooklyn Bridge", "source_type": "wikipedia", "top_k": 3}'

# 2. Wait a moment for log ingestion
sleep 10

# 3. Check performance logs
gcloud logging read 'jsonPayload.endpoint_category="query" AND jsonPayload.metric_type="performance"' --limit=1

# 4. Check request body logs
gcloud logging read 'jsonPayload.endpoint_category="query" AND jsonPayload.metric_type="request_body"' --limit=1

# 5. Find your specific request
gcloud logging read 'jsonPayload.request_body.query:"Brooklyn Bridge"' --limit=1
```
