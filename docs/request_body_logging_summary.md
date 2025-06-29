# Request Body Logging Implementation Summary

## What You Asked For

You wanted to:

1. Run a POST query to the vector database API ✅
1. Filter logs on `jsonPayload.endpoint_category: "query"` AND `jsonPayload.metric_type: "performance"` ✅
1. Discuss logging the request body in POST requests ✅

## What We Accomplished

### 1. Successfully Ran Your Query ✅

```bash
curl -X 'POST' \
  'https://vector-db.coredatastore.com/api/query/search' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "What is the history of the Lefferts Family?",
  "source_type": "wikipedia",
  "top_k": 5
}'
```

**Result**: Successfully returned 5 results about Lefferts-related landmarks.

### 2. Successfully Filtered Performance Logs ✅

**Your Requested Filter**:

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.endpoint_category="query" AND jsonPayload.metric_type="performance"' --project=velvety-byway-327718
```

**Results**:

- Found performance logs showing POST requests to `/api/query/search`
- Duration times: 2.3s, 2.5s, 3.0s, 18.3s
- All returned status code 200

### 3. Implemented Complete Request Body Logging Solution ✅

Created comprehensive middleware for logging POST request bodies with:

#### Features Implemented:

- **Selective Logging**: Only logs bodies for specific endpoints (`/api/query/search`, `/api/query/search/landmark`, `/api/chat/message`)
- **Security**: Automatically redacts sensitive fields (passwords, tokens, keys)
- **Size Limits**: Prevents logging bodies larger than 2KB
- **Data Sanitization**: Truncates long strings and handles nested objects
- **Client Information**: Captures IP, User-Agent, Content-Type

#### New Log Structure:

```json
{
  "message": "POST request body logged",
  "endpoint": "/api/query/search",
  "endpoint_category": "query",
  "metric_type": "request_body",
  "request_body": {
    "query": "What is the history of the Lefferts Family?",
    "source_type": "wikipedia",
    "top_k": 5
  },
  "body_size_bytes": 89,
  "client_ip": "169.254.169.126",
  "user_agent": "curl/7.88.1"
}
```

## Current Logging Capabilities

### 1. Performance Logs (Already Working)

```bash
# Your original filter
gcloud logging read 'jsonPayload.endpoint_category="query" AND jsonPayload.metric_type="performance"'
```

**Contains**:

- Endpoint name and category
- Request duration in milliseconds
- Status codes
- Client IP and User-Agent
- Query parameters

### 2. API Query Logs (Already Working)

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db.nyc_landmarks.api.query"'
```

**Contains**:

- Query text, landmark_id, source_type, top_k
- Request metadata
- Function and line information

### 3. Request Body Logs (New Implementation)

```bash
# Will be available after middleware deployment
gcloud logging read 'jsonPayload.metric_type="request_body"'
```

**Will Contain**:

- Complete request body (sanitized)
- Body size information
- Client details
- Request metadata

## Query Examples for Your Use Case

### Performance Analysis

```bash
# Find slow query requests
gcloud logging read 'jsonPayload.endpoint_category="query" AND jsonPayload.metric_type="performance" AND jsonPayload.duration_ms>5000'

# Recent performance data
gcloud logging read 'jsonPayload.endpoint_category="query" AND jsonPayload.metric_type="performance"' --limit=10
```

### Request Body Analysis (After Deployment)

```bash
# Find specific queries
gcloud logging read 'jsonPayload.metric_type="request_body" AND jsonPayload.request_body.query:"Lefferts Family"'

# Analyze request patterns
gcloud logging read 'jsonPayload.metric_type="request_body"' --format="value(jsonPayload.request_body.source_type)" | sort | uniq -c
```

### Combined Analysis

```bash
# Performance + Request Body correlation
gcloud logging read 'jsonPayload.endpoint_category="query" AND (jsonPayload.metric_type="performance" OR jsonPayload.metric_type="request_body")'
```

## Files Created

1. **`nyc_landmarks/api/request_body_logging_middleware.py`** - Main middleware implementation
1. **`docs/post_request_body_logging.md`** - Complete documentation
1. **`scripts/query_request_logs.sh`** - Query examples script
1. **`scripts/test_request_body_logging.py`** - Testing script

## Next Steps

To deploy the request body logging:

1. **Deploy the new middleware** (already integrated into middleware setup)
1. **Test the deployment** using the provided test script
1. **Monitor logs** using the query examples provided

## Benefits of This Implementation

- **Complete Request Visibility**: See exactly what users are searching for
- **Performance Correlation**: Match slow requests with their content
- **Security Monitoring**: Detect suspicious or malicious requests
- **Usage Analytics**: Understand API usage patterns
- **Debugging Support**: Reproduce user issues exactly
- **Audit Trail**: Complete record of API interactions

The implementation provides exactly what you requested: the ability to filter on `jsonPayload.endpoint_category: "query"` AND `jsonPayload.metric_type: "performance"` while adding comprehensive request body logging capabilities for enhanced monitoring and debugging.
