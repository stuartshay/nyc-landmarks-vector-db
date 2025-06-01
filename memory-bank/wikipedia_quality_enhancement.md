# Wikipedia Article Quality Enhancement

## Overview

This document describes the implementation of Wikipedia article quality assessment in the NYC Landmarks Vector Database project. Article quality information is retrieved from the Wikimedia Lift Wing `articlequality` API endpoint and stored as part of the vector metadata, enabling quality-based filtering and ranking in search results.

## Article Quality Ratings

Wikipedia articles are rated according to a quality assessment scale with the following levels (from highest to lowest quality):

| Rating | Description      | Meaning                                                                                                                            |
| ------ | ---------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| FA     | Featured Article | Wikipedia's highest quality designation, awarded to articles that are determined by the community to be among the best on the site |
| GA     | Good Article     | High-quality articles that meet established criteria but fall short of Featured Article status                                     |
| B      | B-Class          | Substantial articles that are reasonably well-written but may need additional work                                                 |
| C      | C-Class          | Articles with moderate content that could benefit from additional development                                                      |
| Start  | Start-Class      | Basic articles that provide some useful information but lack depth                                                                 |
| Stub   | Stub-Class       | Very basic articles with minimal content                                                                                           |

Each assessment includes a confidence score for each level, with the highest confidence score determining the overall rating.

## Implementation Details

### API Integration

The system integrates with the Wikimedia Lift Wing `articlequality` API endpoint:

```
https://api.wikimedia.org/service/lw/inference/v1/models/enwiki-articlequality:predict
```

This API accepts a Wikipedia article revision ID and returns a quality assessment with confidence scores.

Example API response:

```json
{
  "score": {
    "prediction": "B",
    "probability": {
      "FA": 0.04, "GA": 0.23, "B": 0.49,
      "C": 0.18, "Start": 0.05, "Stub": 0.01
    }
  }
}
```

### Code Implementation

The implementation consists of:

1. **WikipediaQualityFetcher** - A dedicated class for interacting with the Lift Wing API
1. **Quality Data Storage** - Integration with the vector metadata system
1. **Metadata Propagation** - Quality data is added to each chunk's metadata

#### Key Components

- `nyc_landmarks/wikipedia/quality_fetcher.py` - Handles API communication and response parsing
- `nyc_landmarks/wikipedia/processor.py` - Integrates quality assessment into article processing
- `nyc_landmarks/vectordb/pinecone_db.py` - Stores quality metadata in vector chunks

### Metadata Fields

The following quality-related fields are added to each vector's metadata:

- `article_quality` - The overall quality rating (FA, GA, B, C, Start, Stub)
- `article_quality_score` - The confidence score for the predicted quality level
- `article_quality_description` - Human-readable description of the quality level

## Usage in Search

### Filtering by Quality

The quality metadata can be used to filter search results based on article quality:

```python
# Example: Filter search to only include Featured and Good articles
filter_dict = {"$or": [{"article_quality": "FA"}, {"article_quality": "GA"}]}

results = db_client.query_vectors(
    query_vector=embedding, filter_dict=filter_dict, top_k=5
)
```

### Ranking by Quality

Quality information can also be used to re-rank search results, giving preference to higher-quality sources:

```python
# Example: Quality-weighted scoring
def quality_weight(quality):
    weights = {"FA": 1.0, "GA": 0.9, "B": 0.7, "C": 0.5, "Start": 0.3, "Stub": 0.1}
    return weights.get(quality, 0.5)


# Rerank results considering both semantic similarity and quality
for result in results:
    quality = result["metadata"].get("article_quality", "C")
    adjusted_score = result["score"] * quality_weight(quality)
    result["adjusted_score"] = adjusted_score

# Sort by adjusted score
results.sort(key=lambda x: x["adjusted_score"], reverse=True)
```

## Future Enhancements

Potential future enhancements include:

1. **Quality Thresholds** - Configure minimum quality levels for inclusion in search results
1. **Quality Boosting** - Dynamically adjust ranking based on quality assessment
1. **Quality Statistics** - Track and report on the distribution of article quality in the database
1. **API Extensions** - Add quality filtering parameters to the Query API
