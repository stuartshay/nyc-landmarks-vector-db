# API Query Search Logging Flow Documentation

## Overview

This document provides a comprehensive analysis of the complete logging flow for the POST request to `/api/query/search` endpoint, including correlation ID usage for log aggregation.

## Request Example

```bash
curl -X 'POST' \
  'https://vector-db.coredatastore.com/api/query/search' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "What is the history of the Pieter Claesen Wyckoff House?",
  "source_type": "wikipedia",
  "top_k": 5
}'
```

## Complete Logging Flow

### 1. Request Initiation & Middleware Processing

#### 1.1 Request Context Setup

- **Location**: `nyc_landmarks/utils/request_context.py` (via `setup_request_tracking`)
- **Purpose**: Initialize request tracking context
- **Correlation ID**: Generated or extracted from headers

#### 1.2 Request Body Logging Middleware

- **Location**: `nyc_landmarks/api/request_body_logging_middleware.py`
- **Process**:
  1. Extract correlation ID using `get_correlation_id(request)`
  1. Check if endpoint should be logged (`/api/query/search` is configured)
  1. Read and sanitize request body
  1. Log request body with correlation ID

**Log Entry Example**:

```json
{
  "message": "POST request body logged",
  "endpoint": "/api/query/search",
  "endpoint_category": "query",
  "method": "POST",
  "path": "/api/query/search",
  "request_body": {
    "query": "What is the history of the Pieter Claesen Wyckoff House?",
    "source_type": "wikipedia",
    "top_k": 5
  },
  "body_size_bytes": 98,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_ip": "192.168.1.100",
  "user_agent": "curl/7.68.0"
}
```

#### 1.3 Performance Monitoring Middleware

- **Location**: `nyc_landmarks/api/middleware.py`
- **Process**:
  1. Record start time
  1. Extract correlation ID
  1. Categorize endpoint as "query"
  1. Process request and measure duration

### 2. API Endpoint Processing

#### 2.1 Input Validation

- **Location**: `nyc_landmarks/api/query.py` → `search_text` function
- **Process**:
  1. Extract client information using `get_client_info(request)`
  1. Validate each parameter using `ValidationLogger` methods:
     - `validate_text_query()`
     - `validate_landmark_id()`
     - `validate_top_k()`
     - `validate_source_type()`
  1. Log validation success with correlation ID

**Log Entry Example**:

```json
{
  "message": "Valid API request processed",
  "endpoint": "/api/query/search",
  "client_ip": "192.168.1.100",
  "user_agent": "curl/7.68.0",
  "request_data": {
    "query": "What is the history of the Pieter Claesen Wyckoff House?",
    "landmark_id": null,
    "source_type": "wikipedia",
    "top_k": 5
  },
  "validation_status": "success"
}
```

#### 2.2 Correlation ID Extraction for Processing

- **Location**: `nyc_landmarks/api/query.py` (line ~120)
- **Code**: `correlation_id = get_correlation_id(request)`
- **Purpose**: Ensure correlation ID is available for downstream operations

### 3. Embedding Generation

#### 3.1 Embedding Generation Start

- **Location**: `nyc_landmarks/api/query.py` (lines ~125-140)
- **Process**:
  1. Log embedding generation start with correlation ID
  1. Call `embedding_generator.generate_embedding(query.query)`
  1. Log embedding generation completion

**Log Entry Example**:

```json
{
  "message": "Generating embedding for query",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "query_text": "What is the history of the Pieter Claesen Wyckoff House?",
  "query_length": 54,
  "landmark_id": null,
  "source_type": "wikipedia",
  "operation": "embedding_generation",
  "endpoint": "/api/query/search"
}
```

#### 3.2 OpenAI API Call

- **Location**: `nyc_landmarks/embeddings/generator.py`
- **Process**:
  1. Call OpenAI embeddings API
  1. Handle retries and rate limiting
  1. Return embedding vector

#### 3.3 Embedding Generation Complete

**Log Entry Example**:

```json
{
  "message": "Embedding generation completed",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "embedding_dimensions": 1536,
  "operation": "embedding_generation_complete",
  "endpoint": "/api/query/search"
}
```

### 4. Vector Database Query

#### 4.1 Vector Query Start

- **Location**: `nyc_landmarks/vectordb/pinecone_db.py` → `query_vectors` method
- **Process**:
  1. Log vector query operation start with correlation ID
  1. Build filter dictionary for source_type
  1. Execute Pinecone query

**Log Entry Example**:

```json
{
  "message": "Starting vector query operation",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "top_k": 5,
  "has_query_vector": true,
  "landmark_id": null,
  "source_type": "wikipedia",
  "id_prefix": null,
  "filter_dict_size": 1,
  "namespace_override": null,
  "operation": "vector_query_start"
}
```

#### 4.2 Pinecone API Call

- **Process**:
  1. Execute similarity search in Pinecone
  1. Apply filters (source_type: "wikipedia")
  1. Return top 5 results

#### 4.3 Vector Query Complete

**Log Entry Example**:

```json
{
  "message": "Vector query operation completed",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "results_count": 5,
  "effective_top_k": 5,
  "actual_top_k": 5,
  "operation": "vector_query_complete"
}
```

### 5. Response Processing & Performance Logging

#### 5.1 Response Construction

- **Location**: `nyc_landmarks/api/query.py`
- **Process**:
  1. Process vector search results
  1. Enhance with landmark metadata
  1. Build SearchResponse object

#### 5.2 Performance Monitoring Complete

- **Location**: `nyc_landmarks/api/middleware.py`
- **Process**:
  1. Calculate total request duration
  1. Log performance metrics with correlation ID

**Log Entry Example**:

```json
{
  "message": "API request completed",
  "endpoint": "POST /api/query/search",
  "endpoint_category": "query",
  "method": "POST",
  "path": "/api/query/search",
  "status_code": 200,
  "duration_ms": 1250.5,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "query_params": {},
  "success": true
}
```

## Correlation ID Usage Verification

### ✅ Correlation ID Propagation Confirmed

The correlation ID is properly propagated through the entire request lifecycle:

1. **Generated/Extracted**: `get_correlation_id(request)` in middleware
1. **Request Body Logging**: Included in request body logs
1. **Validation Logging**: Available in validation logs
1. **Embedding Generation**: Passed to embedding operations
1. **Vector Database**: Propagated to Pinecone query operations
1. **Performance Monitoring**: Included in timing logs

### Header Priority Order

1. `X-Request-ID` (highest priority)
1. `X-Correlation-ID`
1. `Request-ID`
1. `Correlation-ID` (lowest priority)
1. Generated UUID4 if none found

## Log Aggregation Strategy

### Querying Logs by Correlation ID

```bash
# Example log aggregation query
grep "550e8400-e29b-41d4-a716-446655440000" logs/*.log

# Or using structured logging tools
jq '.correlation_id == "550e8400-e29b-41d4-a716-446655440000"' logs/*.json
```

### Log Categories by Module

1. **Request Body Logs**: `nyc_landmarks.api.request_body_logging_middleware`
1. **Validation Logs**: `nyc_landmarks.utils.validation`
1. **API Endpoint Logs**: `nyc_landmarks.api.query`
1. **Vector DB Logs**: `nyc_landmarks.vectordb.pinecone_db`
1. **Performance Logs**: `nyc_landmarks.api.middleware`
1. **Embedding Logs**: `nyc_landmarks.embeddings.generator`

## Error Handling & Logging

### Validation Errors

- Logged with correlation ID and client information
- Include specific validation failure details
- Return appropriate HTTP status codes

### API Errors

- Global exception handler logs with correlation ID
- Structured error classification
- Client information preserved

### Vector Database Errors

- Retry logic with correlation tracking
- Detailed error context logging
- Graceful degradation

## Monitoring & Observability

### Key Metrics Logged

- Request duration (total and by component)
- Embedding generation time
- Vector database query time
- Request body size
- Result count
- Error rates by correlation ID

### Performance Thresholds

- Total request time: Target < 2000ms
- Embedding generation: Target < 500ms
- Vector database query: Target < 1000ms

## Security Considerations

### Sensitive Data Handling

- Request bodies are sanitized before logging
- Sensitive fields are redacted (`[REDACTED]`)
- Large strings are truncated with `[TRUNCATED]` marker
- Maximum body size limit: 10KB

### Client Information

- IP addresses logged for security monitoring
- User agents tracked for client analysis
- No authentication tokens logged

## Configuration

### Environment Variables

- `DEVELOPMENT_MODE`: Controls logging verbosity
- `LOG_ALL_POST_REQUESTS`: Enables logging for all POST endpoints
- `LOG_LEVEL`: Controls log level (DEBUG, INFO, WARNING, ERROR)

### Logging Endpoints

Currently configured for request body logging:

- `/api/query/search`
- `/api/query/search/landmark`
- `/api/chat/message`
