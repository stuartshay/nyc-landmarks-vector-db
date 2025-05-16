# Using Examples in the NYC Landmarks Vector DB

This document explains how to use the example system in the NYC Landmarks Vector DB API.

## Accessing Examples in Swagger UI

The Swagger UI provides a convenient way to test the API endpoints with pre-configured
examples:

1. Open the Swagger UI at http://localhost:8000/docs
1. Navigate to the desired endpoint (e.g. `/api/query/search`)
1. Click on the "Try it out" button
1. Select an example from the dropdown menu
1. The request body will be automatically filled with the example values
1. Click "Execute" to run the query

## Available Example Categories

The system includes several categories of examples:

1. **General Text Queries** - Various queries about NYC landmarks without specific
   filters
1. **Landmark-Specific Queries** - Queries that target a specific landmark using its ID
1. **Source-Type Queries** - Queries that filter by the source type (PDF or Wikipedia)

## Adding New Examples

To add new examples to the system:

1. Open the appropriate file in the `nyc_landmarks/examples/` directory:
   - For search examples, edit `search_examples.py`
1. Add your new example to the appropriate function
1. Restart the API server to see the changes

Example of adding a new search example:

```python
def get_text_query_examples():
    return {
        # Existing examples...
        "chrysler_building": {
            "summary": "Chrysler Building Art Deco Features",
            "description": "Search for information about the Art Deco features of the Chrysler Building",
            "value": {
                "query": "What are the Art Deco features of the Chrysler Building?",
                "landmark_id": None,
                "source_type": "pdf",
                "top_k": 5,
            },
        }
    }
```

## Example Structure

Each example should include:

- **Key** - Unique identifier for the example
- **Summary** - Brief description shown in the dropdown
- **Description** - More detailed explanation
- **Value** - The actual request body used for the example:
  - `query` - The search text
  - `landmark_id` - Optional landmark ID filter
  - `source_type` - Optional source type filter ("pdf", "wikipedia", or null)
  - `top_k` - Number of results to return

## Best Practices

1. Use descriptive keys that indicate the purpose of the example
1. Provide clear summaries that help users understand the example's purpose
1. Create a diverse range of examples that showcase different capabilities
1. Include examples with different filter combinations
1. Test your examples to ensure they return meaningful results

## Creating New Example Types

If you need to create examples for a different API endpoint:

1. Create a new Python file in the `nyc_landmarks/examples/` directory
1. Define functions that return dictionaries of examples
1. Add the functions to `__init__.py`
1. Update the API endpoint to use your new examples
