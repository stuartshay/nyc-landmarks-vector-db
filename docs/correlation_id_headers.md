# Sending Correlation IDs in Headers

## Overview

Yes! You can absolutely send correlation IDs in request headers. The system supports multiple header formats and will use them to correlate logs across both **Request Body Logging** and **Performance Monitoring** middleware.

## Supported Header Formats

The middleware checks for correlation IDs in this priority order:

1. **`X-Request-ID`** (highest priority)
1. **`X-Correlation-ID`**
1. **`Request-ID`**
1. **`Correlation-ID`** (lowest priority)

If none are provided, a UUID is automatically generated.

## Examples

### Basic Correlation ID

```bash
curl -X POST 'https://vector-db.coredatastore.com/api/query/search' \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: my-custom-correlation-123' \
  -d '{
    "query": "What is the history of the Lefferts Family?",
    "source_type": "wikipedia",
    "top_k": 5
  }'
```

### Alternative Header Formats

```bash
# Using X-Correlation-ID
curl -X POST 'https://vector-db.coredatastore.com/api/query/search' \
  -H 'X-Correlation-ID: session-abc-123' \
  -H 'Content-Type: application/json' \
  -d '{"query": "test"}'

# Using Request-ID
curl -X POST 'https://vector-db.coredatastore.com/api/query/search' \
  -H 'Request-ID: trace-xyz-789' \
  -H 'Content-Type: application/json' \
  -d '{"query": "test"}'

# Using Correlation-ID
curl -X POST 'https://vector-db.coredatastore.com/api/query/search' \
  -H 'Correlation-ID: user-session-456' \
  -H 'Content-Type: application/json' \
  -d '{"query": "test"}'
```

### Session Tracking

```bash
# Use the same correlation ID for related requests
SESSION_ID="user-session-$(date +%s)"

# First request
curl -X POST 'https://vector-db.coredatastore.com/api/query/search' \
  -H "X-Request-ID: $SESSION_ID" \
  -H 'Content-Type: application/json' \
  -d '{"query": "Brooklyn Bridge history"}'

# Related request with same correlation ID
curl -X POST 'https://vector-db.coredatastore.com/api/query/search' \
  -H "X-Request-ID: $SESSION_ID" \
  -H 'Content-Type: application/json' \
  -d '{"query": "Central Park landmarks"}'
```

## What Gets Correlated

When you send a correlation ID in headers, it will appear in **both log types**:

### Request Body Logs (`metric_type: "request_body"`)

```json
{
  "correlation_id": "my-custom-correlation-123",
  "request_body": {"query": "..."},
  "endpoint": "/api/query/search",
  "metric_type": "request_body",
  "body_size_bytes": 104
}
```

### Performance Logs (`metric_type: "performance"`)

```json
{
  "correlation_id": "my-custom-correlation-123",
  "endpoint": "POST /api/query/search",
  "metric_type": "performance",
  "response_time_ms": 2435.34,
  "status_code": 200
}
```

## Querying Correlated Logs

### Find All Logs for a Specific Request

```bash
# Replace with your actual correlation ID
jsonPayload.correlation_id="my-custom-correlation-123"
```

### Find Request Body + Performance for Same Request

```bash
jsonPayload.correlation_id="my-custom-correlation-123" AND
(jsonPayload.metric_type="request_body" OR jsonPayload.metric_type="performance")
```

### Find All Requests with Custom Correlation IDs

```bash
# Exclude auto-generated UUIDs, show only client-provided IDs
jsonPayload.correlation_id!="unknown" AND
NOT jsonPayload.correlation_id ~ "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
```

### Session Analysis

```bash
# Find all activity for a user session
jsonPayload.correlation_id="user-session-1672531200" AND
timestamp >= "2025-06-29T00:00:00Z" AND
timestamp <= "2025-06-29T23:59:59Z"
```

## Header Priority Testing

If you send multiple correlation headers, the system uses priority:

```bash
curl -X POST 'https://vector-db.coredatastore.com/api/query/search' \
  -H 'X-Request-ID: priority-winner' \
  -H 'X-Correlation-ID: ignored' \
  -H 'Request-ID: also-ignored' \
  -H 'Content-Type: application/json' \
  -d '{"query": "test"}'

# Result: correlation_id will be "priority-winner"
```

## Best Practices

### 1. Use Meaningful IDs

```bash
# Good: Descriptive and traceable
X-Request-ID: user-12345-session-20250629-query-001

# Avoid: Generic or unclear
X-Request-ID: abc123
```

### 2. Session Correlation

```bash
# Use the same ID for related requests in a user session
SESSION="user-789-$(date +%Y%m%d-%H%M%S)"

# All related requests use the same session ID
X-Request-ID: $SESSION
```

### 3. Microservice Propagation

```bash
# Pass correlation IDs between services
curl -X POST 'https://external-service.com/api' \
  -H "X-Request-ID: $CORRELATION_ID" \
  -H 'Content-Type: application/json' \
  -d '{"data": "from-vector-db"}'
```

## Testing

Use the provided test script to validate correlation functionality:

```bash
python scripts/test_correlation_headers.py
```

This script tests:

- ✅ All supported header formats
- ✅ Header priority order
- ✅ Session correlation across multiple requests
- ✅ End-to-end log correlation

## Implementation Details

Both middleware components now support correlation IDs:

- **RequestBodyLoggingMiddleware**: Logs request bodies with correlation IDs
- **PerformanceMonitoringMiddleware**: Logs performance metrics with correlation IDs

This provides complete request traceability across your entire API pipeline! 🎯
