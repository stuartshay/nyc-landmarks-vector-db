# Unit Tests for NYC Landmarks Vector DB

This directory contains unit tests for the NYC Landmarks Vector Database project, with a focus on thorough testing of the database client (`db_client.py`).

## DB Client Test Organization

The database client tests are organized into multiple files to maintain clarity and separation of concerns:

1. **test_db_client.py** - Core functionality tests

   - Tests the basic functionality of the `DbClient` class
   - Focus on ID handling, landmark retrieval, and parsing methods
   - Contains three test classes:
     - `TestDbClientCore`: Tests for core methods like ID formatting, retrieving landmarks, etc.
     - `TestConversionMethods`: Tests for data conversion methods
     - `TestWikipediaIntegration`: Tests for Wikipedia-related methods

1. **test_db_client_additional.py** - Additional functionality tests

   - Tests for landmark and building related methods
   - Contains three test classes:
     - `TestDbClientLandmarkMethods`: Tests for landmark-specific methods
     - `TestDbClientBuildingsMethods`: Tests for building-related methods
     - `TestDbClientTotalCount`: Tests for record counting methods

1. **test_db_client_coverage.py** - Additional tests to ensure high coverage

   - Tests specific edge cases and paths in the code that weren't covered by other tests
   - Ensures overall test coverage exceeds 80% (currently at 96%)
   - Contains six test classes targeting different areas:
     - `TestSupportsWikipediaProtocol`: Tests for the protocol methods
     - `TestGetLpcReportsFallback`: Tests for the fallback functionality in `get_lpc_reports`
     - `TestLandmarkPdfUrl`: Tests for PDF URL retrieval edge cases
     - `TestConversionMethods`: Tests for additional conversion scenarios
     - `TestBuildingMethods`: Tests for building-related edge cases
     - `TestWikipediaMethods`: Tests for Wikipedia-related edge cases
     - `TestOtherMethods`: Tests for miscellaneous methods

## Running the Tests

To run all DB client tests with coverage report:

```bash
python -m pytest tests/unit/test_db_client*.py -v --cov=nyc_landmarks.db.db_client --cov-report term
```

To run a specific test file:

```bash
python -m pytest tests/unit/test_db_client_core.py -v
```

To run a specific test class:

```bash
python -m pytest tests/unit/test_db_client_core.py::TestDbClientCore -v
```

To run a specific test method:

```bash
python -m pytest tests/unit/test_db_client_core.py::TestDbClientCore::test_format_landmark_id -v
```

## Test Coverage

The current test coverage for `db_client.py` is 96%, exceeding the project requirement of 80%. The uncovered lines are primarily related to specific edge cases in error handling that are difficult to trigger in a test environment.

```
Name                            Stmts   Miss  Cover
---------------------------------------------------
nyc_landmarks/db/db_client.py     246     13   95%
```

## Mock Usage

These tests make extensive use of mocking to isolate the `DbClient` class from its dependencies, particularly the `CoreDataStoreAPI` client. This approach allows us to test the `DbClient` class without making actual API calls, resulting in faster and more reliable tests.

Key mocking techniques used:

- Mocking the `CoreDataStoreAPI` class
- Patching specific methods in the `DbClient` class to test error handling
- Creating mock responses to simulate various API response scenarios
