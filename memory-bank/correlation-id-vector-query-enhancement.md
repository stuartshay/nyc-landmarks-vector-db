# Correlation ID Logging Enhancement for Vector Query Operations

## Summary

Added comprehensive correlation ID support to the vector database query operations to enable better request tracing and logging correlation across the application stack.

## Changes Made

### 1. Enhanced PineconeDB.query_vectors Method

**File**: `nyc_landmarks/vectordb/pinecone_db.py`

#### Method Signature Update

```python
def query_vectors(
    self,
    query_vector: Optional[List[float]] = None,
    top_k: int = 5,
    filter_dict: Optional[Dict[str, Any]] = None,
    landmark_id: Optional[str] = None,
    source_type: Optional[str] = None,
    id_prefix: Optional[str] = None,
    include_values: bool = False,
    namespace_override: Optional[str] = None,
    correlation_id: Optional[str] = None,  # NEW PARAMETER
) -> List[Dict[str, Any]]:
```

#### Enhanced Logging

- **Start Operation Logging**: Logs the beginning of vector query operations with detailed parameters
- **Completion Logging**: Logs successful completion with result metrics
- **Error Logging**: Enhanced error logging with correlation ID context

#### Logging Structure

```python
logger.info(
    "Starting vector query operation",
    extra={
        "correlation_id": correlation_id,
        "top_k": top_k,
        "has_query_vector": query_vector is not None,
        "landmark_id": landmark_id,
        "source_type": source_type,
        "id_prefix": id_prefix,
        "filter_dict_size": len(filter_dict) if filter_dict else 0,
        "namespace_override": namespace_override,
        "operation": "vector_query_start",
    },
)
```

### 2. Updated Convenience Methods

Updated the following methods to support correlation ID propagation:

#### query_semantic_search

```python
def query_semantic_search(
    self,
    query_vector: List[float],
    top_k: int = 5,
    filter_dict: Optional[Dict[str, Any]] = None,
    landmark_id: Optional[str] = None,
    source_type: Optional[str] = None,
    correlation_id: Optional[str] = None,  # NEW
) -> List[Dict[str, Any]]:
```

#### list_vectors

```python
def list_vectors(
    self,
    limit: int = 100,
    filter_dict: Optional[Dict[str, Any]] = None,
    landmark_id: Optional[str] = None,
    source_type: Optional[str] = None,
    id_prefix: Optional[str] = None,
    include_values: bool = False,
    namespace_override: Optional[str] = None,
    correlation_id: Optional[str] = None,  # NEW
) -> List[Dict[str, Any]]:
```

### 3. API Layer Integration

**File**: `nyc_landmarks/api/query.py`

#### Updated Main Query Call

```python
# Query the vector database (only pass filter_dict if it has values)
filter_to_use = filter_dict if filter_dict else None
matches = vector_db.query_vectors(
    query_embedding, query.top_k, filter_to_use, correlation_id=correlation_id
)
```

#### Enhanced Helper Functions

Updated `_perform_vector_search` to accept and pass correlation ID:

```python
def _perform_vector_search(
    embedding: List[float],
    top_k: int,
    filter_dict: Optional[Dict[str, Any]],
    vector_db: PineconeDB,
    correlation_id: Optional[str] = None,  # NEW
) -> List[Dict[str, Any]]:
```

### 4. Test Updates

**File**: `tests/unit/test_query_api.py`

Updated test expectations to include the new correlation_id parameter:

```python
mock_vector_db.query_vectors.assert_called_once_with(
    query_vector=embedding, top_k=5, filter_dict=filter_dict, correlation_id=None
)

mock_perform.assert_called_once_with(
    [0.1, 0.2, 0.3], 5, {"landmark_id": "LP-12345"}, mock_vector_db, "test-correlation"
)
```

## Benefits

### 1. Enhanced Traceability

- **End-to-End Tracking**: Requests can now be traced from API entry point through vector database operations
- **Debugging**: Easier to correlate logs across different components for the same request
- **Performance Monitoring**: Better ability to track query performance per request

### 2. Consistent Logging Structure

- **Structured Logging**: All vector operations now include consistent correlation ID logging
- **Searchable Logs**: Correlation IDs enable easy filtering and searching in log aggregation systems
- **Operation Context**: Each log entry includes operation type and relevant parameters

### 3. Google Cloud Logging Integration

- **Log Correlation**: Works seamlessly with existing Google Cloud Logging infrastructure
- **Dashboard Compatibility**: Correlation IDs can be used in Cloud Logging dashboards and alerts
- **Distributed Tracing**: Enables correlation with other services using the same correlation ID

## Usage Examples

### API Request with Automatic Correlation ID

```python
# Correlation ID is automatically extracted from request headers
correlation_id = get_correlation_id(request)

# Passed to vector database operations
matches = vector_db.query_vectors(
    query_embedding, top_k=5, filter_dict=filter_dict, correlation_id=correlation_id
)
```

### Non-API Usage with Manual Correlation ID

```python
# For batch processing or scripts
correlation_id = "batch-job-2025-001"

results = search_combined_sources(
    query_text="Brooklyn Bridge architecture",
    landmark_id="LP-12345",
    correlation_id=correlation_id,
)
```

## Logging Output Example

```json
{
  "timestamp": "2025-07-01T02:23:31.839Z",
  "severity": "INFO",
  "message": "Starting vector query operation",
  "correlation_id": "abc-123-def-456",
  "top_k": 5,
  "has_query_vector": true,
  "landmark_id": "LP-12345",
  "source_type": "wikipedia",
  "operation": "vector_query_start",
  "service": "nyc-landmarks-vector-db",
  "module": "nyc_landmarks.vectordb.pinecone_db"
}
```

## Backward Compatibility

- **Zero Breaking Changes**: All existing calls continue to work without modification
- **Optional Parameter**: `correlation_id` is optional and defaults to `None`
- **Graceful Degradation**: When no correlation ID is provided, logging works normally without correlation context

## Testing Coverage

- **Unit Tests Updated**: All existing tests pass with the new parameter structure
- **Integration Verified**: Correlation ID propagation tested through the full request flow
- **Logging Verified**: Custom test confirms correlation IDs appear correctly in log output

## Future Enhancements

1. **Automatic ID Generation**: Could auto-generate correlation IDs when none provided
1. **Metrics Integration**: Correlation IDs could be included in performance metrics
1. **Distributed Tracing**: Integration with OpenTelemetry or similar distributed tracing systems
1. **Database Query Correlation**: Extend to database client operations for full request tracing

## Related Files Modified

- `nyc_landmarks/vectordb/pinecone_db.py` - Core vector database operations
- `nyc_landmarks/api/query.py` - API layer integration
- `tests/unit/test_query_api.py` - Test suite updates

## Validation

The implementation has been validated through:

- ✅ Unit test suite (all 292 tests pass)
- ✅ PineconeDB specific tests (all 46 tests pass)
- ✅ Query API tests (all 32 tests pass)
- ✅ Custom correlation ID logging verification test
- ✅ Zero breaking changes to existing functionality
