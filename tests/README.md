# NYC Landmarks Vector DB Testing

This directory contains tests for the NYC Landmarks Vector DB project. The tests are organized into three main categories:

- **Unit Tests**: Fast tests that verify individual components in isolation
- **Functional Tests**: Tests that verify complete workflows and pipelines
- **Integration Tests**: Tests that verify interactions with external services

## Test Categories

### Unit Tests

Unit tests focus on testing individual functions, classes, or methods in isolation. They are fast, reliable, and don't require network access.

Run with:
```bash
python -m pytest tests/unit -v
```

### Functional Tests

Functional tests verify that complete workflows and pipelines function correctly. They may interact with external services but have fallbacks to mock data when those services are unavailable.

Run with:
```bash
python -m pytest tests/functional -v
```

### Integration Tests

Integration tests verify the application's interaction with external dependencies such as APIs, databases, and vector stores. These tests require network connections and credentials.

Run with:
```bash
python -m pytest tests/integration -v
```

## Testing in Offline Environments

Many of our tests interact with external services like the CoreDataStore API and Pinecone.
To ensure tests can run in offline environments or when these services are unavailable,
we've implemented the following strategies:

### Mock Data and Fallbacks

The `tests/utils/test_mocks.py` module provides mock data for:

- Landmark data (`get_mock_landmark()`)
- PDF text content (`get_mock_landmark_pdf_text()`)
- LPC reports API responses (`get_mock_lpc_reports()`)

These mocks are used as fallbacks when external services are unreachable. For example:

```python
try:
    # Try to get real data from API
    landmark_data = db_client.get_landmark_by_id(landmark_id)

    # If API is unreachable, use mock data
    if not landmark_data:
        logger.warning("Could not fetch landmark data from API, using mock data instead")
        landmark_data = get_mock_landmark(landmark_id)
except Exception as e:
    logger.error(f"Error getting landmark by ID: {e}")
    landmark_data = get_mock_landmark(landmark_id)
```

### Handling Network Errors

Tests are designed to handle network errors gracefully by:

1. Using try/except blocks to catch and log exceptions
2. Providing fallback mechanisms when external services are unavailable
3. Skipping certain tests when required services are unavailable

Run with:
```bash
python -m pytest tests/integration -v
```

## Offline Testing Approach

To make tests more robust and runnable in offline environments, we've implemented several strategies:

1. **Fallback Mock Data**: Tests automatically fall back to using mock data when external APIs are unreachable.
   - Example: If the CoreDataStore API can't be reached, the tests use predefined landmark data.

2. **Flexible Metadata Handling**: We've improved metadata extraction to handle different response formats.
   - Tests can work with different versions of the API or when data structures change slightly.

3. **Configurable Timeouts**: Network operations have appropriate timeouts to avoid long waits when services are unreachable.

4. **Conditional Test Skipping**: Tests that absolutely require external services are skipped when those services are unavailable.

Example of fallback approach in `test_vector_storage_pipeline.py`:

```python
# Try to fetch from API if available
landmark_data = db_client.get_landmark_by_id(landmark_id)

# If API is unreachable, use mock data
if not landmark_data:
    logger.warning(
        "Could not fetch landmark data from API, using mock data instead"
    )
    landmark_data = {
        "id": landmark_id,
        "name": "Pieter Claesen Wyckoff House",
        # ... other mock data ...
    }
```

## Running Tests

All tests:
```bash
python -m pytest tests -v
```

Run a specific test file:
```bash
python -m pytest tests/path/to/test_file.py -v
```

Run tests with a specific marker:
```bash
python -m pytest -m "functional" -v
```

Skip tests with a specific marker:
```bash
python -m pytest -k "not mcp" -v
```

## Test Markers

- `unit`: Unit tests
- `functional`: Functional tests
- `integration`: Integration tests
- `mcp`: Tests that use Model Context Protocol (MCP)

Test markers are automatically applied based on the test location in the directory structure.
