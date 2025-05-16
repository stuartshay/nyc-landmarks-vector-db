# API Response Handling in Tests

## Background

As of May 2025, the database client in this project (`get_landmark_by_id`) has been
updated to return Pydantic models instead of dictionaries. This change improves type
safety but required modifications to our tests.

## The Problem

Tests using the following pattern were failing:

```python
landmark_data = db_client.get_landmark_by_id(landmark_id)
logger.info(f"Using landmark: {landmark_data.get('name', 'Unknown')}")
```

This resulted in an error:

```
AttributeError: 'LpcReportDetailResponse' object has no attribute 'get'
```

The error occurs because Pydantic models use attribute access (e.g., `model.attribute`)
rather than the dictionary-style access (e.g., `dict.get('key')`) that was previously
used.

## The Solution

Tests have been updated to handle both dictionary and Pydantic model responses. The
pattern used is:

```python
# Handle both Pydantic model and dictionary types
landmark_name = "Unknown"
if hasattr(landmark_data, "name"):
    landmark_name = landmark_data.name
elif isinstance(landmark_data, dict):
    landmark_name = landmark_data.get("name", "Unknown")

logger.info(f"Using landmark: {landmark_name}")
```

Similar changes were made for other attributes like `pdfReportUrl`.

## When You Should Use This Pattern

Use this pattern in any code that:

1. Calls `get_landmark_by_id` or other database client methods
1. Needs to handle both legacy (dictionary) responses and new (Pydantic model) responses
1. May run in environments where the API client implementation varies

## Testing

The fix was verified by running functional tests, which now handle both response types
correctly.

## Future Improvements

Consider these improvements to make the code more resilient:

1. Use explicit type checking/casting in the API client
1. Create adapter methods that normalize the response format
1. Update tests to use a consistent response format

## Files Modified

1. `/tests/functional/test_vector_storage_pipeline_fixed.py` - Implemented with model
   and dict handling

> **Note**: The original test file `test_vector_storage_pipeline.py` has been removed,
> and we kept the fixed version with the "\_fixed" suffix to maintain code history and
> make it clear that this file contains fixes for the API response handling issue.

## Date of Change

May 12, 2025
