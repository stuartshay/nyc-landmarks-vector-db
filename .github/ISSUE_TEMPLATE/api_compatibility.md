# API Compatibility Issue

## Problem

When developing tests or code that interacts with the database client, I'm getting an error similar to:

```
AttributeError: 'LpcReportDetailResponse' object has no attribute 'get'
```

## Solution

The database client returns either a dictionary or a Pydantic model. Use this pattern to handle both:

```python
# Handle both Pydantic model and dictionary types
if hasattr(object, "attribute_name"):
    # Pydantic model approach
    value = object.attribute_name
elif isinstance(object, dict):
    # Dictionary approach
    value = object.get('attribute_name', default_value)
```

## Reference

See the [API Response Handling Documentation](../../docs/api_response_handling.md) for more details on how to handle this.

## Examples

For common patterns and examples, see:
- `test_vector_storage_pipeline_fixed.py`
