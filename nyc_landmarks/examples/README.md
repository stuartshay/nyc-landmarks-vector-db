# NYC Landmarks Vector DB Examples

This directory contains example queries and data that can be used for:

1. Populating the Swagger UI documentation with example requests
2. Testing API functionality
3. Demonstrating the capabilities of the system

## Available Example Collections

### Search Examples (`search_examples.py`)

This file contains examples of queries that can be used with the vector search API endpoints.

- **Text Query Examples**: General search queries about NYC landmarks
- **Landmark Filter Examples**: Queries that demonstrate filtering by specific landmark IDs

## How to Maintain and Add Examples

Examples are maintained directly in the Python files in this directory. To add or modify examples:

### Adding a New Search Example

1. Open `search_examples.py`
2. Add your new example to the appropriate function:

```python
def get_text_query_examples():
    return {
        # Existing examples...

        "your_example_key": {
            "summary": "Short Summary",
            "description": "Detailed description of what this example does",
            "value": {
                "query": "Your search query text",
                "landmark_id": None,  # or specific ID if needed
                "source_type": "pdf",  # or "wikipedia" or None
                "top_k": 5
            }
        }
    }
```

3. Save the file and restart the API server
4. Your example will automatically appear in the Swagger UI for the corresponding endpoint

### Creating a New Example Collection

If you want to create examples for a different purpose:

1. Create a new file (e.g., `my_new_examples.py`)
2. Define functions that return dictionaries of example data
3. Import the functions in `__init__.py`
4. Use the examples in your API endpoint definitions

## Example Structure

Each example should follow this structure:

```python
"example_key": {
    "summary": "Brief summary shown in dropdown",
    "description": "More detailed explanation of the example",
    "value": {
        # The actual request body that will be used
    }
}
```

## Best Practices for Examples

1. Use descriptive keys that indicate what the example demonstrates
2. Keep summaries short and focused (they appear in the dropdown menu)
3. Provide detailed descriptions to help users understand when to use each example
4. Include a variety of examples that cover different use cases
5. Test your examples to ensure they return meaningful results
6. Use consistent formatting to make the example collection maintainable
