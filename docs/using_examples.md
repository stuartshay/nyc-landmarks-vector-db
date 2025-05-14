# Using Examples in the NYC Landmarks Vector DB

This document explains how to use the example system in the NYC Landmarks Vector DB API.

## Accessing Examples in Swagger UI

The Swagger UI provides a convenient way to test the API endpoints with pre-configured examples:

1. Open the Swagger UI at http://localhost:8000/docs
2. Navigate to the desired endpoint (e.g. `/api/query/search`)
3. Click on the "Try it out" button
4. Select an example from the dropdown menu
5. The request body will be automatically filled with the example values
6. Click "Execute" to run the query

## Available Example Categories

The system includes several categories of examples:

1. **General Text Queries** - Various queries about NYC landmarks without specific filters
2. **Landmark-Specific Queries** - Queries that target a specific landmark using its ID
3. **Source-Type Queries** - Queries that filter by the source type (PDF or Wikipedia)

## Adding New Examples

To add new examples to the system:

1. Open the appropriate file in the `nyc_landmarks/examples/` directory:
   - For search examples, edit `search_examples.py`
2. Add your new example to the appropriate function
3. Restart the API server to see the changes

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
                "top_k": 5
            }
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
2. Provide clear summaries that help users understand the example's purpose
3. Create a diverse range of examples that showcase different capabilities
4. Include examples with different filter combinations
5. Test your examples to ensure they return meaningful results

## Creating New Example Types

If you need to create examples for a different API endpoint:

1. Create a new Python file in the `nyc_landmarks/examples/` directory
2. Define functions that return dictionaries of examples
3. Add the functions to `__init__.py`
4. Update the API endpoint to use your new examples
