# Wikipedia Revision ID (rev_id) Tracking Implementation

## Overview

The NYC Landmarks Vector Database now includes comprehensive revision ID tracking for Wikipedia articles. This enhancement provides version control and update tracking capabilities for better citation accuracy and reproducibility.

## Implementation Details

### Storage Locations

Revision IDs are stored in two locations within chunk metadata for maximum compatibility:

1. **`article_metadata['rev_id']`** - Used by PineconeDB for metadata creation
1. **`metadata['article_rev_id']`** - Direct metadata field for backwards compatibility

### Code Components

#### 1. WikipediaFetcher

- **File**: `nyc_landmarks/db/wikipedia_fetcher.py`
- **Methods**:
  - `_extract_revision_id()` - Extracts rev_id from Wikipedia page HTML
  - `_extract_revision_from_scripts()` - Parses revision from script tags
  - `_extract_revision_from_url()` - Extracts from URL parameters
- **Integration**: Automatically captures revision IDs during content fetching

#### 2. WikipediaProcessor

- **File**: `nyc_landmarks/wikipedia/processor.py`
- **Methods**:
  - `_enrich_dict_chunk()` - Adds rev_id to article_metadata
  - `_add_metadata_to_dict()` - Adds rev_id to direct metadata
- **Integration**: Propagates revision IDs through the processing pipeline

#### 3. Data Models

- **File**: `nyc_landmarks/models/wikipedia_models.py`
- **Models**:
  - `WikipediaContentModel.rev_id` - Stores article revision ID
  - `WikipediaQualityModel.rev_id` - Links quality assessment to revision

## Metadata Structure

### Complete Chunk Metadata Example

```json
{
  "text": "Sunnyslope is a neighborhood in the Bronx...",
  "chunk_index": 0,
  "metadata": {
    "article_title": "Sunnyslope (Bronx)",
    "article_url": "https://en.wikipedia.org/wiki/Sunnyslope_(Bronx)",
    "article_rev_id": "1234567890",
    "article_quality": "Stub",
    "article_quality_score": "0.6690722250585311",
    "article_quality_description": "Stub-Class - Very basic information, significant expansion needed",
    "processing_date": "2024-01-01T12:00:00",
    "source_type": "Wikipedia"
  },
  "article_metadata": {
    "title": "Sunnyslope (Bronx)",
    "url": "https://en.wikipedia.org/wiki/Sunnyslope_(Bronx)",
    "rev_id": "1234567890"
  }
}
```

## Usage Examples

### 1. Search by Specific Revision

```python
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

db = PineconeDB()

# Find chunks from a specific article revision
filter_dict = {"article_rev_id": "1234567890"}
results = db.query_vectors(query_vector=embedding, filter_dict=filter_dict, top_k=5)
```

### 2. Filter Articles with Revision Tracking

```python
# Find only articles that have revision IDs
filter_dict = {"article_rev_id": {"$exists": True}}
results = db.query_vectors(query_vector=embedding, filter_dict=filter_dict, top_k=10)
```

### 3. Combine with Quality Filtering

```python
# Find high-quality articles with revision tracking
filter_dict = {
    "$and": [
        {"article_quality": {"$in": ["FA", "GA", "B"]}},
        {"article_rev_id": {"$exists": True}},
    ]
}
results = db.query_vectors(query_vector=embedding, filter_dict=filter_dict, top_k=5)
```

## Benefits

### 1. Version Control

- Track specific Wikipedia article versions
- Identify content changes over time
- Maintain consistency across processing runs

### 2. Citation Accuracy

- Provide precise article version references
- Enable reproducible research citations
- Support academic and documentation needs

### 3. Update Detection

- Compare current vs. stored revision IDs
- Identify when articles need reprocessing
- Implement selective update workflows

### 4. Quality Correlation

- Link quality assessments to specific revisions
- Track quality changes over article versions
- Analyze quality trends over time

### 5. Reproducibility

- Ensure consistent results with specific versions
- Support debugging and validation workflows
- Enable controlled experimentation

## Integration with Existing Features

### Wikipedia Quality Assessment

- Quality assessments are linked to specific revisions
- Quality data includes the revision ID used for assessment
- Enables tracking quality changes across article versions

### Metadata Collection

- Seamlessly integrates with existing metadata pipeline
- Backwards compatible with existing chunk structures
- No changes required to existing query interfaces

### Vector Database Storage

- Revision IDs are automatically indexed for filtering
- Compatible with all existing search and filter operations
- Supports both exact match and existence queries

## Testing

Comprehensive functional tests verify revision ID functionality:

- **File**: `tests/functional/test_wikipedia_rev_id_metadata.py`
- **Coverage**:
  - Metadata storage in multiple locations
  - Handling of missing revision IDs
  - Full chunk enrichment workflow
  - Quality assessment integration

## Future Enhancements

### Update Detection Pipeline

```python
# Pseudocode for future update detection
def check_for_updates(landmark_id: str) -> bool:
    current_vectors = get_vectors_by_landmark(landmark_id)
    stored_rev_id = current_vectors[0]["metadata"]["article_rev_id"]

    latest_rev_id = fetch_latest_revision_id(landmark_id)
    return stored_rev_id != latest_rev_id
```

### Revision History Tracking

```python
# Store revision history for trend analysis
metadata["revision_history"] = [
    {"rev_id": "123", "processed_date": "2024-01-01"},
    {"rev_id": "456", "processed_date": "2024-02-01"},
]
```

### Quality Trend Analysis

```python
# Analyze quality changes across revisions
def analyze_quality_trends(landmark_id: str) -> Dict[str, Any]:
    revisions = get_revision_history(landmark_id)
    return {
        "quality_progression": track_quality_changes(revisions),
        "stability_score": calculate_stability(revisions),
    }
```

## Related Documentation

- [Wikipedia Quality Enhancement](wikipedia_quality_enhancement.md)
- [Building Metadata Integration](building_metadata_integration.md)
- [Unified Vector Utility](unified_vector_utility.md)
- [Vector ID Standardization](vector_id_standardization.md)
