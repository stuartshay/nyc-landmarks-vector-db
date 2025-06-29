# Enhanced Correlation Testing with NYC Landmark Examples

## Overview

Successfully enhanced the `test_correlation_comprehensive.py` script to use **authentic NYC landmark data** from the `nyc_landmarks/examples/search_examples.py` module instead of generic placeholder queries.

## Key Enhancements

### ✅ **Realistic API Request Bodies**

**Before:** Generic test queries

```python
payload = {
    "query": f"Test query for {test['name']}",
    "source_type": "wikipedia",
    "top_k": 2,
}
```

**After:** Authentic NYC landmark queries

```python
payload = {
    "query": "What is the history of the Pieter Claesen Wyckoff House?",
    "source_type": "wikipedia",
    "top_k": 5,
}
```

### ✅ **Context-Specific Payloads**

Different test types now use appropriate NYC landmark examples:

- **Header Testing**: Wyckoff House history (oldest NYC structure)
- **Priority Testing**: Federal Hall queries (Washington's inauguration site)
- **Session Testing**: Brooklyn Bridge engineering questions
- **Tracking Testing**: Architectural style searches
- **Auto-Generation**: Empire State Building architecture queries

### ✅ **Realistic Session Queries**

Session correlation testing now uses actual landmark queries:

```python
session_queries = [
    "What is the history of the Pieter Claesen Wyckoff House?",
    "What is the historical significance of Federal Hall National Memorial?",
    "How was the Brooklyn Bridge engineered and constructed?",
    "What are the Dutch Colonial architectural features of this landmark?",
    "What happened at this landmark during the founding of America?",
]
```

## Implementation Details

### New Helper Functions

1. **`get_realistic_payload(test_type: str)`**

   - Returns contextually appropriate NYC landmark payloads
   - Handles different test scenarios with relevant examples
   - Includes fallback for robustness

1. **`get_session_queries()`**

   - Extracts real queries from search examples
   - Provides diverse NYC landmark questions for session testing
   - Fallback queries if examples unavailable

### Enhanced Import Structure

```python
from nyc_landmarks.examples.search_examples import (
    get_text_query_examples,
    get_landmark_filter_examples,
    get_advanced_query_examples,
)
```

## Benefits

### 🏛️ **Authentic Testing**

- **Real-world scenarios** with actual NYC landmark data
- **Meaningful correlation tracking** with historical queries
- **Production-like request patterns** for better validation

### 📊 **Better Demonstration Value**

- **Showcase actual API capabilities** with landmark searches
- **Realistic load testing** with diverse query types
- **Professional presentation** for stakeholders

### 🔧 **Improved Maintainability**

- **Centralized examples** shared across testing and documentation
- **Type-safe implementation** with proper error handling
- **Modular design** supporting easy updates

## Usage Examples

### Test with Realistic Payloads

```bash
python scripts/test_correlation_comprehensive.py --test-suite headers
```

### Full Correlation Testing Suite

```bash
python scripts/test_correlation_comprehensive.py --test-suite all
```

### Session Testing with NYC Landmarks

```bash
python scripts/test_correlation_comprehensive.py --test-suite session
```

## Quality Assurance

- ✅ **Type Safety**: MyPy validation passes without issues
- ✅ **Error Handling**: Robust fallbacks for any import issues
- ✅ **Realistic Data**: All payloads use authentic NYC landmark content
- ✅ **Backward Compatibility**: Existing functionality preserved
- ✅ **Documentation**: Clear examples and usage patterns

## Impact

### For Development

- **More realistic testing** of correlation ID functionality
- **Better debugging** with meaningful request content
- **Production simulation** with actual query patterns

### For Demonstration

- **Professional showcase** of API capabilities
- **Realistic load scenarios** for performance testing
- **Authentic data flows** for stakeholder presentations

### For Documentation

- **Consistent examples** across testing and API docs
- **Real-world usage patterns** for developer guidance
- **Production-ready demonstrations** for onboarding

## Next Steps

1. **API Testing**: Run enhanced correlation tests against live API
1. **Performance Analysis**: Monitor correlation tracking with realistic loads
1. **Documentation Updates**: Use realistic examples in API documentation
1. **Team Training**: Demonstrate enhanced testing capabilities

The correlation testing script now provides a **professional, realistic testing experience** that accurately reflects how the NYC Landmarks Vector Database will be used in production environments.
