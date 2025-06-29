# NYC Landmarks Search Examples Enhancement

## Overview

Enhanced the `nyc_landmarks/examples/search_examples.py` module to use **authentic NYC landmark data** instead of placeholder examples, making it more valuable for API documentation and testing.

## Key Improvements

### ✅ Real Landmark Data Integration

**Before:** Generic placeholder examples

```python
"lefferts_family_history": {
    "query": "What is the history of the Lefferts Family?",
    "landmark_id": None,
    # ...
}
```

**After:** Authentic NYC landmark examples

```python
"wyckoff_house_history": {
    "summary": "Pieter Claesen Wyckoff House History (Wikipedia)",
    "description": "Search for the history of NYC's oldest structure, the Wyckoff House (LP-00001)",
    "value": {
        "query": "What is the history of the Pieter Claesen Wyckoff House?",
        "landmark_id": None,
        "source_type": "wikipedia",
        "top_k": 5,
    },
}
```

### ✅ Valid Landmark IDs

Now using **real LPC numbers** from the NYC Landmarks Preservation Commission database:

- **LP-00001**: Pieter Claesen Wyckoff House (Brooklyn) - NYC's oldest structure
- **LP-00009**: Federal Hall National Memorial (Manhattan) - Site of Washington's inauguration
- **LP-00099**: Brooklyn Heights Historic District
- **LP-01973**: Harlem YMCA Building (Manhattan) - Significant cultural institution

### ✅ Comprehensive Example Categories

1. **Text Queries** (8 examples): General search patterns
1. **Landmark-Specific** (8 examples): Queries filtered by landmark ID
1. **Advanced Patterns** (6 examples): Complex search scenarios
1. **Borough-Focused** (6 examples): Geographic search patterns

### ✅ Enhanced Helper Functions

- `get_all_examples()`: Comprehensive dictionary of all categories
- `get_example_landmark_ids()`: List of all landmark IDs used
- `get_example_queries_by_source_type()`: Filter examples by source
- `validate_query_example()`: Validate example structure
- `get_advanced_query_examples()`: Complex query patterns
- `get_borough_specific_examples()`: Geographic search examples

## Example Distribution

```
📊 Example Categories:
   text_queries: 8 examples
   landmark_specific: 8 examples
   advanced_patterns: 6 examples
   borough_focused: 6 examples

📚 Source Type Distribution:
   PDF sources: 12 examples
   Wikipedia sources: 10 examples
   All sources: 6 examples

🏛️ Real Landmark IDs Used: ['LP-00001', 'LP-00009', 'LP-00099', 'LP-01973']
```

## Quality Assurance

- ✅ **28/28 examples** pass validation
- ✅ All imports successful
- ✅ MyPy type checking passes
- ✅ All unit tests continue to pass
- ✅ Real landmark data verified against API documentation

## Usage Examples

### Basic Text Queries

```python
from nyc_landmarks.examples.search_examples import get_text_query_examples

examples = get_text_query_examples()
wyckoff_example = examples["wyckoff_house_history"]
# Real query about NYC's oldest structure
```

### Landmark-Specific Queries

```python
from nyc_landmarks.examples.search_examples import get_landmark_filter_examples

examples = get_landmark_filter_examples()
federal_hall = examples["federal_hall_specific"]
# Query with landmark_id: "LP-00009"
```

### Advanced Search Patterns

```python
from nyc_landmarks.examples.search_examples import get_advanced_query_examples

examples = get_advanced_query_examples()
multi_source = examples["multi_source_comparison"]
# Complex queries across multiple source types
```

## Impact

1. **API Documentation**: Examples now demonstrate real-world usage patterns
1. **Testing**: More realistic test scenarios with actual landmark data
1. **Developer Experience**: Clear examples of how to query specific NYC landmarks
1. **Data Accuracy**: All landmark IDs verified against the CoreDataStore API
1. **Maintainability**: Well-structured helper functions for easy extension

## Next Steps

The enhanced search examples are ready for:

- Integration into API documentation
- Use in automated testing
- Demo applications and tutorials
- Developer onboarding materials

All examples use authentic NYC landmark data and follow the project's type safety and code quality standards.
