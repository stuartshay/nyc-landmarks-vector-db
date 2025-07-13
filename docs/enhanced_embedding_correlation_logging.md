# Enhanced Embedding Generation Correlation Logging

## Overview

Enhanced the query API to include **correlation ID tracking** during embedding generation, enabling end-to-end request tracing from API request through embedding generation to vector search completion.

## 🎯 Key Enhancements

### ✅ **API Endpoint Correlation Tracking**

**Before:** Basic embedding generation logging

```python
# Generate embedding for the query
query_embedding = embedding_generator.generate_embedding(query.query)
```

**After:** Enhanced correlation tracking

```python
# Get correlation ID for embedding generation tracking
correlation_id = get_correlation_id(request)

# Generate embedding for the query with correlation tracking
logger.info(
    "Generating embedding for query",
    extra={
        "correlation_id": correlation_id,
        "query_text": (
            query.query[:100] + "..." if len(query.query) > 100 else query.query
        ),
        "query_length": len(query.query),
        "landmark_id": query.landmark_id,
        "source_type": query.source_type,
        "operation": "embedding_generation",
        "endpoint": "/api/query/search",
    },
)
query_embedding = embedding_generator.generate_embedding(query.query)
logger.info(
    "Embedding generation completed",
    extra={
        "correlation_id": correlation_id,
        "embedding_dimensions": len(query_embedding) if query_embedding else 0,
        "operation": "embedding_generation_complete",
        "endpoint": "/api/query/search",
    },
)
```

### ✅ **Non-API Function Enhancement**

Enhanced the `_generate_query_embedding` helper function to support correlation logging:

```python
def _generate_query_embedding(
    query_text: str,
    embedding_generator: EmbeddingGenerator,
    correlation_id: Optional[str] = None,
) -> Any:
    """Generate embedding vector with optional correlation tracking."""
    if correlation_id:
        logger.info(
            "Generating embedding for non-API query",
            extra={
                "correlation_id": correlation_id,
                "query_text": (
                    query_text[:100] + "..." if len(query_text) > 100 else query_text
                ),
                "query_length": len(query_text),
                "operation": "embedding_generation",
                "context": "non_api_search",
            },
        )

    embedding = embedding_generator.generate_embedding(query_text)

    if correlation_id:
        logger.info(
            "Embedding generation completed for non-API query",
            extra={
                "correlation_id": correlation_id,
                "embedding_dimensions": len(embedding) if embedding else 0,
                "operation": "embedding_generation_complete",
                "context": "non_api_search",
            },
        )

    return embedding
```

### ✅ **Enhanced Module Functions**

Updated `search_combined_sources()` and `compare_source_results()` to accept and propagate correlation IDs:

```python
from typing import Any, Dict, List, Optional


def search_combined_sources(
    query_text: str,
    landmark_id: Optional[str] = None,
    source_type: Optional[str] = None,
    top_k: int = 5,
    correlation_id: Optional[str] = None,  # 🆕 New parameter
    embedding_generator: Optional["EmbeddingGenerator"] = None,
    vector_db: Optional["PineconeDB"] = None,
    db_client: Optional["DbClient"] = None,
) -> List[Dict[str, Any]]:
    """Search combined sources with correlation tracking."""
    pass
```

## 📊 Logging Structure

### **API Request Flow**

```json
{
  "timestamp": "2025-06-29T18:26:30.123Z",
  "level": "INFO",
  "message": "Generating embedding for query",
  "correlation_id": "priority-test-1751221589",
  "query_text": "What happened at this landmark during the founding of America?",
  "query_length": 62,
  "landmark_id": "LP-00009",
  "source_type": "wikipedia",
  "operation": "embedding_generation",
  "endpoint": "/api/query/search"
}
```

```json
{
  "timestamp": "2025-06-29T18:26:30.456Z",
  "level": "INFO",
  "message": "Embedding generation completed",
  "correlation_id": "priority-test-1751221589",
  "embedding_dimensions": 1536,
  "operation": "embedding_generation_complete",
  "endpoint": "/api/query/search"
}
```

### **Non-API Function Flow**

```json
{
  "timestamp": "2025-06-29T18:26:30.789Z",
  "level": "INFO",
  "message": "Generating embedding for non-API query",
  "correlation_id": "0af7f2b5-b9f1-4f76-bdb0-bffd3d0b3778",
  "query_text": "What is the history of Federal Hall?",
  "query_length": 35,
  "operation": "embedding_generation",
  "context": "non_api_search"
}
```

## 🔍 GCP Logging Queries

### **Find All Embedding Generation Logs for a Correlation ID**

```
jsonPayload.correlation_id="493d7b93-95a3-48af-b156-ebda3a08f9fc" AND
jsonPayload.operation="embedding_generation"
```

### **Track Complete Embedding Process**

```
jsonPayload.correlation_id="493d7b93-95a3-48af-b156-ebda3a08f9fc" AND
(jsonPayload.operation="embedding_generation" OR
 jsonPayload.operation="embedding_generation_complete")
```

### **Complete 3-Log-Type Query (Query Endpoint + Request Body + Embedding)**

```
jsonPayload.correlation_id="493d7b93-95a3-48af-b156-ebda3a08f9fc" AND
(jsonPayload.endpoint_category="query" OR
 jsonPayload.metric_type="request_body" OR
 jsonPayload.operation="embedding_generation" OR
 jsonPayload.operation="embedding_generation_complete")
```

### **Monitor Embedding Performance**

```
jsonPayload.operation="embedding_generation_complete" AND
jsonPayload.embedding_dimensions > 0
ORDER BY timestamp DESC
```

### **Find Embedding Errors by Correlation**

```
jsonPayload.correlation_id="your-correlation-id" AND
severity >= "ERROR" AND
(jsonPayload.operation="embedding_generation" OR
 textPayload CONTAINS "embedding")
```

## 🚀 Benefits

### **For Development**

- **End-to-End Tracing**: Follow requests from API entry through embedding generation to completion
- **Performance Monitoring**: Track embedding generation time and success rates per correlation ID
- **Debugging Support**: Easily identify issues in specific request flows

### **For Operations**

- **Request Correlation**: Match embedding logs with initial API requests
- **Performance Analysis**: Monitor embedding generation patterns and bottlenecks
- **Error Tracking**: Identify and debug embedding-related issues

### **For Monitoring**

- **Dashboard Integration**: Create metrics based on correlation IDs
- **Alert Configuration**: Set up alerts for embedding generation failures
- **Audit Trails**: Complete request tracing for compliance and debugging

## 📋 Usage Examples

### **API Usage (Automatic)**

```python
# Correlation ID automatically extracted from request headers
# No code changes needed - correlation logging happens automatically
response = requests.post(
    "/api/query/search",
    json={"query": "What is the history of Federal Hall?", "landmark_id": "LP-00009"},
    headers={"X-Request-ID": "user-session-123"},  # This becomes correlation_id
)
```

### **Non-API Usage (Manual)**

```python
from nyc_landmarks.api.query import search_combined_sources
from nyc_landmarks.utils.correlation import generate_correlation_id

# Generate or use existing correlation ID
correlation_id = generate_correlation_id()

# Enhanced search with correlation tracking
results = search_combined_sources(
    query_text="What is the architectural significance of Federal Hall?",
    landmark_id="LP-00009",
    correlation_id=correlation_id,  # Enable correlation logging
)
```

### **Module Integration**

```python
from nyc_landmarks.api.query import compare_source_results

# Compare sources with correlation tracking
comparison = compare_source_results(
    query_text="Federal Hall history",
    landmark_id="LP-00009",
    correlation_id="batch-analysis-456",
)
```

## 🎯 Next Steps

1. **Performance Monitoring**: Set up dashboards to track embedding generation metrics by correlation ID
1. **Error Analysis**: Create alerts for embedding generation failures with correlation context
1. **Optimization**: Use correlation data to identify and optimize slow embedding operations
1. **Testing**: Enhance automated tests to verify correlation ID propagation

The enhanced embedding correlation logging provides **complete request traceability** from API entry through embedding generation, enabling powerful debugging, monitoring, and performance analysis capabilities.
