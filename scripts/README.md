# Scripts Documentation

## Vector Database Utilities

### check_specific_vector.py

This script allows you to check the metadata for a specific vector stored in Pinecone. It's particularly useful for debugging and validating that vectors have the correct metadata fields.

**Usage:**

```bash
python scripts/check_specific_vector.py "<vector_id>"
```

**Examples:**

```bash
# Check a Wikipedia vector
python scripts/check_specific_vector.py "wiki-83_and_85_Sullivan_Street-LP-02344-chunk-0"

# Check a landmark report vector
python scripts/check_specific_vector.py "report-LP-00001-chunk-0"
```

**Output:**
The script outputs the full metadata for the vector and, for Wikipedia vectors, validates that required fields are present:

```
Vector ID: wiki-83_and_85_Sullivan_Street-LP-02344-chunk-0
Metadata type: <class 'dict'>
Metadata keys: ['architect', 'borough', 'chunk_index', 'designation_date', ...]
Full metadata: {
  "architect": "Unknown",
  "borough": "Manhattan",
  ...
  "source_type": "wikipedia",
  "text": "83 and 85 Sullivan Street are on Sullivan Street...",
  ...
}

Missing required Wikipedia fields: ['article_title', 'article_url']
```

**Notes:**
- Testing on May 18, 2025 revealed that some Wikipedia vectors were missing `article_title` and `article_url` fields.
- These fields should be added by `process_wikipedia_articles.py`.
