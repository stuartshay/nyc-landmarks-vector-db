# Comprehensive Correlation Testing Script

## Overview

The `test_correlation_comprehensive.py` script consolidates all correlation ID testing functionality into a single, powerful tool for testing the NYC Landmarks Vector DB correlation system.

## What Was Consolidated

This script replaces and combines functionality from:

- ❌ `test_correlation_headers.py` (removed - duplicate functionality)
- ❌ `test_correlation_tracking.py` (removed - duplicate functionality)
- ✅ `test_correlation_comprehensive.py` (new comprehensive script)

## Features

### 🔗 Complete Correlation Testing

- **Header Format Testing**: Tests all supported correlation ID headers (X-Request-ID, X-Correlation-ID, Request-ID, Correlation-ID)
- **Priority Validation**: Verifies that X-Request-ID takes precedence over other headers
- **Auto-Generation Testing**: Confirms UUID generation when no correlation headers are provided
- **Session Correlation**: Tests multiple related requests with the same correlation ID
- **Cross-Middleware Tracking**: Validates correlation across request body and performance middleware

### 🎯 Flexible Test Suites

Run specific test suites or all tests:

```bash
# Run all tests (default)
python scripts/test_correlation_comprehensive.py

# Run specific test suite
python scripts/test_correlation_comprehensive.py --test-suite headers
python scripts/test_correlation_comprehensive.py --test-suite priority
python scripts/test_correlation_comprehensive.py --test-suite tracking
python scripts/test_correlation_comprehensive.py --test-suite session
```

### 🔍 Built-in GCP Query Generation

Automatically generates Google Cloud Logging queries for:

- Individual correlation IDs from test runs
- Combined queries for request body + performance logs
- Time-based queries for test sessions
- Pattern-based queries for finding all test-generated logs

## Usage Examples

### Basic Usage

```bash
# Run comprehensive correlation testing
python scripts/test_correlation_comprehensive.py
```

### Test Specific Functionality

```bash
# Test only header formats and priority
python scripts/test_correlation_comprehensive.py --test-suite headers

# Test session correlation tracking
python scripts/test_correlation_comprehensive.py --test-suite session
```

### Custom API URL

```bash
# Test against a different API endpoint
python scripts/test_correlation_comprehensive.py --api-url https://localhost:8000
```

### Get Help

```bash
python scripts/test_correlation_comprehensive.py --help
```

## Test Suites

| Suite      | Description                      | Tests                                                      |
| ---------- | -------------------------------- | ---------------------------------------------------------- |
| `all`      | Complete testing suite (default) | All tests below                                            |
| `headers`  | Header format testing            | X-Request-ID, X-Correlation-ID, Request-ID, Correlation-ID |
| `priority` | Header priority validation       | Multiple headers with X-Request-ID priority                |
| `tracking` | Basic correlation tracking       | Custom IDs and shared correlation groups                   |
| `session`  | Session correlation              | Multiple related requests with same ID                     |

## Generated Correlation IDs

The script generates predictable correlation IDs for easy log querying:

- **Header Tests**: `test-{header-type}-{timestamp}`
- **Priority Test**: `priority-test-{timestamp}`
- **Tracking Tests**: `custom-tracking-{timestamp}`, `shared-tracking-{timestamp}`
- **Session Tests**: `session-{timestamp}`

## Sample Output

```
🧪 Comprehensive Correlation ID Testing
============================================================
🌐 API Base URL: https://vector-db.coredatastore.com
🎯 Test Suite: all
⏰ Started: 2025-06-29 17:27:57 UTC

🔗 Testing Correlation ID Header Formats
============================================================
📍 Testing: X-Request-ID Header (Highest Priority)
   ✅ Response: 200
   ⏱️  Response time: 0.925s

[... additional test output ...]

📊 Test Results: 9/9 successful
🚀 Your correlation system is fully functional and ready for production!
```

## GCP Logging Queries

The script automatically generates Google Cloud Logging queries for correlating logs:

```bash
# Find specific correlation ID
jsonPayload.correlation_id="test-x-request-id-1751218077"

# Find all request body logs with correlation
jsonPayload.metric_type="request_body" AND jsonPayload.correlation_id!="unknown"

# Correlate request body + performance for same ID
jsonPayload.correlation_id="YOUR-CORRELATION-ID" AND
(jsonPayload.metric_type="request_body" OR jsonPayload.metric_type="performance")
```

## Integration with Development Workflow

This script is perfect for:

- **CI/CD Testing**: Validate correlation functionality in automated tests
- **Development Debugging**: Generate specific correlation IDs for log analysis
- **Production Validation**: Verify correlation system health
- **Performance Testing**: Test correlation overhead across multiple requests

## Benefits of Consolidation

✅ **Single Source of Truth**: One script for all correlation testing
✅ **Reduced Maintenance**: No duplicate code to maintain
✅ **Comprehensive Coverage**: All correlation scenarios in one place
✅ **Better Organization**: Structured test suites and clear output
✅ **Enhanced Flexibility**: Configurable test execution
✅ **Integrated Queries**: Built-in GCP logging query generation

## Related Scripts

- `test_gcp_logging.py` - GCP logging configuration testing
- `demonstrate_logging.py` - Enhanced logging demonstration
- `query_request_logs.sh` - GCP log querying utilities

The consolidated script works seamlessly with these related tools to provide a complete correlation testing and debugging experience.
