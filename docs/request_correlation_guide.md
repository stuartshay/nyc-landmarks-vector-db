# Request Correlation Guide

## Overview

The request body logging middleware now includes **correlation ID tracking** to enable correlating logs across different middleware and services.

## How Correlation Works

### Correlation ID Generation

The middleware automatically:

1. **Checks for existing correlation ID** in request headers:

   - `x-request-id`
   - `x-correlation-id`
   - `request-id`
   - `correlation-id`

1. **Generates a UUID** if no correlation ID is found in headers

1. **Includes correlation ID** in all log entries from the request body middleware

### Log Types with Correlation

#### Request Body Logs (`metric_type: "request_body"`)

```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_body": {"query": "..."},
  "endpoint": "/api/query/search",
  "metric_type": "request_body"
}
```

#### Request Timing Logs (`metric_type: "request_timing"`)

```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "processing_time_ms": 145.23,
  "endpoint": "/api/query/search",
  "metric_type": "request_timing"
}
```

## Correlating with Performance Logs

To correlate request body logs with existing performance logs, you have several options:

### Option 1: Timestamp-based Correlation (Current)

```bash
# Find request body logs around a specific time
jsonPayload.metric_type="request_body" AND
timestamp >= "2025-06-29T01:11:57Z" AND
timestamp <= "2025-06-29T01:11:59Z"

# Find performance logs in the same timeframe
jsonPayload.metric_type="performance" AND
timestamp >= "2025-06-29T01:11:57Z" AND
timestamp <= "2025-06-29T01:11:59Z"
```

### Option 2: Enhanced Performance Middleware (Recommended)

To get true correlation, the performance middleware would need to:

1. **Extract the same correlation ID** from request headers
1. **Include correlation_id** in performance log entries
1. **Use the same correlation ID generation logic**

Example enhanced performance log:

```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "response_time_ms": 2435.34,
  "endpoint": "POST /api/query/search",
  "metric_type": "performance"
}
```

### Option 3: Client-provided Correlation IDs

Clients can provide their own correlation IDs:

```bash
curl -X POST \
  'https://vector-db.coredatastore.com/api/query/search' \
  -H 'X-Request-ID: my-custom-correlation-id-123' \
  -H 'Content-Type: application/json' \
  -d '{"query": "test"}'
```

## Querying Correlated Logs

### Find all logs for a specific request:

```bash
jsonPayload.correlation_id="550e8400-e29b-41d4-a716-446655440000"
```

### Find request body and timing for same correlation ID:

```bash
jsonPayload.correlation_id="550e8400-e29b-41d4-a716-446655440000" AND
(jsonPayload.metric_type="request_body" OR jsonPayload.metric_type="request_timing")
```

### Correlate by endpoint and time window:

```bash
jsonPayload.endpoint="/api/query/search" AND
timestamp >= "2025-06-29T01:11:57Z" AND
timestamp <= "2025-06-29T01:12:02Z" AND
(jsonPayload.metric_type="request_body" OR jsonPayload.metric_type="performance")
```

## Benefits

- **End-to-end request tracking** across middleware
- **Performance debugging** - correlate slow requests with their payloads
- **Error investigation** - trace issues across log types
- **Client request tracking** when clients provide correlation IDs
- **Distributed tracing foundation** for future enhancements

## Next Steps

To achieve full correlation with performance logs, consider:

1. **Updating performance middleware** to use the same correlation ID logic
1. **Adding correlation ID to all log entries** across the application
1. **Implementing distributed tracing** with tools like OpenTelemetry
1. **Standardizing correlation headers** across your API clients
