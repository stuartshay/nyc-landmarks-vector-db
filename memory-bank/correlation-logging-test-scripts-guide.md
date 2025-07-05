# Correlation ID Logging Test Scripts Guide

This document provides a guide to the correlation ID logging test scripts after cleanup and consolidation.

## Main Correlation ID Testing Scripts (Post-Cleanup)

### 1. `test_correlation_comprehensive.py` ⭐ MAIN SCRIPT

**Purpose**: Comprehensive correlation ID testing suite with multiple test categories
**Features Tested**:

- Local search functionality with correlation tracking
- Header extraction from various formats (X-Correlation-ID, X-Request-ID, etc.)
- Session tracking (multiple operations with same correlation ID)
- Performance analysis with correlation IDs
- Google Cloud Logging query examples

**Usage**:

```bash
cd /workspaces/nyc-landmarks-vector-db

# Run all tests
python scripts/test_correlation_comprehensive.py

# Run specific test suites
python scripts/test_correlation_comprehensive.py --test-suite headers
python scripts/test_correlation_comprehensive.py --test-suite local
python scripts/test_correlation_comprehensive.py --test-suite session
python scripts/test_correlation_comprehensive.py --test-suite performance
```

**Test Suites Available**:

- `headers`: Test correlation ID extraction from HTTP headers
- `local`: Test local search functions with correlation IDs
- `session`: Test session-level correlation across multiple requests
- `performance`: Test performance monitoring with correlation tracking
- `all`: Run all test suites (default)

### 2. `test_api_correlation_logging.py` ⭐ DEMO SCRIPT

**Purpose**: Feature demonstration and API usage examples
**Features Demonstrated**:

- Basic correlation tracking
- Session tracking examples
- Performance analysis capabilities
- HTTP request examples (curl, Python, JavaScript)
- Google Cloud Logging integration examples

**Usage**:

```bash
python scripts/test_api_correlation_logging.py
```

## Scripts Removed During Cleanup

The following duplicate scripts were removed to eliminate redundancy:

- ❌ `test_correlation_logging.py` (root level) - Basic unit test, superseded by comprehensive test
- ❌ `scripts/test_embedding_correlation_logging.py` - Basic functional test, functionality moved to comprehensive test
- ❌ `scripts/test_detailed_correlation_logging.py` - Detailed log analysis, functionality integrated into comprehensive test

## Current Recommended Testing Workflow

### Quick Validation

```bash
# Test header extraction functionality
python scripts/test_correlation_comprehensive.py --test-suite headers
```

### Full Feature Testing

```bash
# Run comprehensive test suite
python scripts/test_correlation_comprehensive.py --test-suite all
```

### Feature Demonstration

```bash
# Show practical usage examples
python scripts/test_api_correlation_logging.py
```

## Related Logging Test Scripts

### 5. `test_development_logging.py`

**Purpose**: Development-focused logging tests
**Features**: General logging functionality testing

### 6. `test_endpoint_logging.py`

**Purpose**: API endpoint specific logging tests
**Features**: Endpoint-level logging validation

### 7. `test_enhanced_logging.py`

**Purpose**: Enhanced logging features testing
**Features**: Advanced logging capabilities

### 8. `test_gcp_logging.py`

**Purpose**: Google Cloud Platform logging integration tests
**Features**: GCP-specific logging functionality

### 9. `test_request_body_logging.py`

**Purpose**: Request body logging tests
**Features**: HTTP request body logging validation

### 10. `test_validation_logging.py`

**Purpose**: Input validation logging tests
**Features**: Validation process logging

## Other Useful Testing Scripts (Non-Correlation Specific)

The following scripts remain available for general logging and API testing:

### General Logging Tests

- `test_development_logging.py` - Development-focused logging tests
- `test_endpoint_logging.py` - API endpoint specific logging tests
- `test_enhanced_logging.py` - Enhanced logging features testing
- `test_gcp_logging.py` - Google Cloud Platform logging integration tests
- `test_request_body_logging.py` - Request body logging tests
- `test_validation_logging.py` - Input validation logging tests

### API Validation Tests

- `test_validation_complete.py` - Complete API validation testing
- `verify_duplicate_logging_fix.py` - Duplicate logging verification

### Specialized Tests

- `test_wikipedia_improvements.py` - Wikipedia processing tests
- `test_landmark_concurrency.py` - Concurrency testing
- `demonstrate_logging.py` - General logging demonstration

## Quick Test Commands

### Correlation ID Testing

```bash
# Main comprehensive correlation test
python scripts/test_correlation_comprehensive.py

# Specific test suites
python scripts/test_correlation_comprehensive.py --test-suite headers
python scripts/test_correlation_comprehensive.py --test-suite local
python scripts/test_correlation_comprehensive.py --test-suite session
python scripts/test_correlation_comprehensive.py --test-suite performance

# Feature demonstration
python scripts/test_api_correlation_logging.py
```

### General Testing

```bash
# GCP logging integration
python scripts/test_gcp_logging.py

# Endpoint logging
python scripts/test_endpoint_logging.py

# Enhanced logging features
python scripts/test_enhanced_logging.py

# API validation
python scripts/test_validation_complete.py
```

## Google Cloud Logging Queries

### Find Correlation ID Logs

```bash
# All logs for a specific correlation ID (replace with actual ID)
jsonPayload.correlation_id="YOUR_CORRELATION_ID_HERE"

# Embedding operations today
jsonPayload.operation="embedding_generation" AND timestamp>="2025-07-01T00:00:00Z"

# Vector query operations today
jsonPayload.operation="vector_query_start" AND timestamp>="2025-07-01T00:00:00Z"

# All operations for a correlation ID
jsonPayload.correlation_id="YOUR_CORRELATION_ID_HERE" AND
(jsonPayload.operation="embedding_generation" OR
 jsonPayload.operation="vector_query_start" OR
 jsonPayload.operation="vector_query_complete")
```

### Performance Analysis Queries

```bash
# Find slow operations (combine with time filters)
jsonPayload.operation="vector_query_start" OR jsonPayload.operation="vector_query_complete"

# Filter by specific module
jsonPayload.module="nyc_landmarks.vectordb.pinecone_db"

# Filter by request source
jsonPayload.context="api_request" OR jsonPayload.context="non_api_search"
```

## Expected Log Structure

### Vector Query Start Log

```json
{
  "timestamp": "2025-07-01T02:30:00.000Z",
  "severity": "INFO",
  "jsonPayload": {
    "message": "Starting vector query operation",
    "correlation_id": "e96017f8-4ecf-4314-b6e0-8283bd2731bd",
    "operation": "vector_query_start",
    "top_k": 3,
    "has_query_vector": true,
    "landmark_id": null,
    "source_type": "wikipedia",
    "module": "nyc_landmarks.vectordb.pinecone_db"
  }
}
```

### Vector Query Complete Log

```json
{
  "timestamp": "2025-07-01T02:30:01.500Z",
  "severity": "INFO",
  "jsonPayload": {
    "message": "Vector query operation completed",
    "correlation_id": "e96017f8-4ecf-4314-b6e0-8283bd2731bd",
    "operation": "vector_query_complete",
    "results_count": 3,
    "effective_top_k": 3,
    "actual_top_k": 3,
    "module": "nyc_landmarks.vectordb.pinecone_db"
  }
}
```

### Embedding Generation Log

```json
{
  "timestamp": "2025-07-01T02:29:59.000Z",
  "severity": "INFO",
  "jsonPayload": {
    "message": "Generating embedding for non-API query",
    "correlation_id": "e96017f8-4ecf-4314-b6e0-8283bd2731bd",
    "operation": "embedding_generation",
    "query_text": "What engineering innovations made the Brooklyn Bridge possible?",
    "query_length": 63,
    "context": "non_api_search",
    "module": "nyc_landmarks.api.query"
  }
}
```

## Key Benefits Demonstrated

1. **End-to-End Tracing**: Follow a request from API entry to database query completion
1. **Performance Analysis**: Measure timing between correlated operations
1. **Debug Support**: Easily find all logs related to a specific request
1. **Operational Insights**: Understand system behavior patterns
1. **Error Correlation**: Link errors to specific request contexts
1. **Session Tracking**: Group multiple operations under a single session ID

## Testing Coverage

- ✅ Unit tests updated and passing (291 passed, 1 skipped)
- ✅ Correlation ID parameter propagation
- ✅ Logging structure validation
- ✅ Backward compatibility verification
- ✅ Performance impact assessment
- ✅ Google Cloud Logging integration ready
- ✅ Header extraction from multiple formats
- ✅ Session-level correlation tracking

## Script Cleanup Summary

**Removed Duplicates**: 3 scripts with overlapping functionality
**Consolidated Into**: 2 primary scripts with clear purposes
**Result**: Cleaner, more maintainable test suite with comprehensive coverage

## Related Documentation

- `/memory-bank/correlation-id-vector-query-enhancement.md` - Complete implementation details
- `/scripts/README.md` - General scripts documentation
- Test output logs demonstrate real-world usage patterns
