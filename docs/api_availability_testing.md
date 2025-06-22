# API Availability Testing

## Overview

Tests that require a running local API server now include automatic availability checking. When the API is not available, tests will either skip with clear instructions or show warnings, depending on the test configuration.

## Features

### 1. Automatic API Availability Detection

- Tests automatically check if the local API server is running
- Multiple health check endpoints are tried (health, docs, root)
- Configurable timeout for health checks

### 2. Clear User Guidance

When the API is not available, users get clear instructions:

```
⚠️  Local API at http://localhost:8000 is not available.
Please start the API server before running these tests.
You can start it with: 'uvicorn nyc_landmarks.api.main:app --host 0.0.0.0 --port 8000'
```

### 3. Flexible Testing Strategies

#### Skip Tests (Recommended)

```python
@pytest.fixture(autouse=True)
def check_api_availability(self, base_url: str) -> None:
    """Check if the API is available before running tests."""
    require_api_or_skip(base_url)
```

#### Warn But Continue

```python
def test_something(self):
    warning = require_api_or_warn("http://localhost:8000")
    if warning:
        import warnings

        warnings.warn(warning, UserWarning)
    # ... rest of test
```

#### Manual Checking

```python
def test_something(self):
    if check_api_availability("http://localhost:8000"):
        # Run API-dependent test
        pass
    else:
        # Run alternative test or skip specific parts
        pass
```

## Usage

### For Test Developers

1. **Import the helpers**:

   ```python
   from tests.utils.api_helpers import (
       require_api_or_skip,
       require_api_or_warn,
       check_api_availability,
   )
   ```

1. **Add to test classes that need API**:

   ```python
   @pytest.fixture(autouse=True)
   def check_api_availability(self, base_url: str) -> None:
       require_api_or_skip(base_url)
   ```

### For Test Runners

1. **Start the API server** before running integration tests:

   ```bash
   uvicorn nyc_landmarks.api.main:app --host 0.0.0.0 --port 8000
   ```

1. **Run tests normally**:

   ```bash
   pytest tests/integration/test_api_validation_logging.py -v
   ```

1. **If API not running**, tests will skip with helpful messages

## Implementation

### Files Modified

- `tests/utils/api_helpers.py` - Core helper functions
- `tests/integration/test_api_validation_logging.py` - Added availability checking
- `tests/unit/test_api_helpers.py` - Unit tests with mocking (CI-safe)
- `tests/integration/test_api_helpers_integration.py` - Integration tests with real API calls

### Functions Available

- `check_api_availability(base_url: str, timeout: int = 5) -> bool`
- `require_api_or_skip(base_url: str) -> None`
- `require_api_or_warn(base_url: str) -> Optional[str]`

## Test Strategy

### Unit Tests (CI-Safe)

- **Location**: `tests/unit/test_api_helpers.py`
- **Purpose**: Test helper function logic with mocking
- **CI/CD**: ✅ Safe to run in automated pipelines
- **Mocking**: Uses `unittest.mock` to simulate API responses
- **Coverage**: Tests all code paths without requiring real API servers

### Integration Tests (Manual/Local)

- **Location**: `tests/integration/test_api_helpers_integration.py`
- **Purpose**: Test actual API connectivity behavior
- **CI/CD**: ⚠️ May skip/fail in CI where no API server runs
- **Real Calls**: Makes actual HTTP requests to test endpoints
- **Usage**: For local development and manual testing scenarios

## Benefits

1. **Better Developer Experience**: Clear error messages instead of confusing connection errors
1. **Faster Test Feedback**: No waiting for timeouts on unavailable APIs
1. **Flexible Testing**: Choose between skipping or warning based on test requirements
1. **Consistent Messaging**: Standardized instructions for starting the API server

## Example Output

### When API is Available

```
tests/integration/test_api_validation_logging.py::test_empty_query_validation PASSED
```

### When API is Unavailable

```
tests/integration/test_api_validation_logging.py::test_empty_query_validation SKIPPED
⚠️  Local API at http://localhost:8000 is not available.
Please start the API server before running these tests.
You can start it with: 'uvicorn nyc_landmarks.api.main:app --host 0.0.0.0 --port 8000'
```
