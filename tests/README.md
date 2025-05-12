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

Example of fallback approach in `test_vector_storage_pipeline_fixed.py`:

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

## Pinecone Testing Strategy

The integration tests that interact with Pinecone use session-specific test indices to avoid polluting the production vector database and support parallel test execution.

### Test Index Architecture

```
┌─────────────────┐     ┌───────────────────────────────────┐
│ Production Index │     │ Session-Specific Test Indices     │
│ (landmarks)      │     │ (nyc-landmarks-test-{session_id}) │
└─────────────────┘     └───────────────────────────────────┘
        │                          │
        ▼                          ▼
┌─────────────────┐     ┌───────────────────────────────────┐
│ Production Data  │     │ Temporary Test Data               │
│ Used by the app  │     │ Each test session gets its own    │
└─────────────────┘     │ isolated index with unique name    │
                        └───────────────────────────────────┘
```

### Test Index Management

We have several utilities to manage the test indices:

1. **Session-Specific Indices**: Each test session automatically gets its own unique index name with timestamp and random identifier (e.g., `nyc-landmarks-test-20250510-221500-a7b3c9`), allowing parallel test execution without conflicts.

2. **Test Fixtures**: `pinecone_test_db` fixture in `tests/integration/conftest.py` automatically creates a session-specific test index at the beginning of a test session and cleans it up at the end.

3. **Management Script**: Use `scripts/manage_test_index.py` to:
   - Create a test index: `python scripts/manage_test_index.py create`
   - Reset the test index: `python scripts/manage_test_index.py reset`
   - Delete the test index: `python scripts/manage_test_index.py delete`
   - Check test index status: `python scripts/manage_test_index.py status`
   - List all test indices: `python scripts/manage_test_index.py list`
   - Clean up old test indices: `python scripts/manage_test_index.py cleanup --age 24`

4. **Utility Module**: For programmatic management of test indices, use the functions in `tests/utils/pinecone_test_utils.py`.

### Benefits of the Session-Specific Test Index Approach

- Complete isolation from production data
- Prevents accidental contamination of the production index
- Clean test environment for each test run
- Support for parallel test execution without conflicts
- Each test session gets a dedicated index with unique naming
- Automatic cleanup of old test indices to prevent resource exhaustion
- Ability to freely modify, delete, or recreate test indices without affecting production or other test sessions
