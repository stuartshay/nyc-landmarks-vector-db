# Scripts Documentation

## Vector Database Utilities

### vector_utility.py

This is a comprehensive tool for working with Pinecone vectors. It combines functionality from multiple
standalone scripts into a single, unified command-line tool.

**Commands:**

- `fetch`: Fetch a specific vector by ID
- `check-landmark`: Check all vectors for a specific landmark ID
- `list-vectors`: List vectors in Pinecone with optional filtering
- `validate`: Validate a specific vector against requirements
- `compare-vectors`: Compare metadata between two vectors
- `verify-vectors`: Verify the integrity of vectors in Pinecone
- `verify-batch`: Verify a batch of specific vectors by their IDs

**Examples:**

```bash
# Fetch a specific vector by ID
python scripts/vector_utility.py fetch wiki-Wyckoff_House-LP-00001-chunk-0 --pretty

# Fetch a vector from a specific namespace
python scripts/vector_utility.py fetch wiki-Manhattan_Municipal_Building-LP-00079-chunk-0 --namespace landmarks

# Check all vectors for a specific landmark
python scripts/vector_utility.py check-landmark LP-00001 --verbose

# List up to 10 vectors starting with a specific prefix
python scripts/vector_utility.py list-vectors --prefix wiki-Wyckoff --limit 10 --pretty

# Validate a specific vector against metadata requirements
python scripts/vector_utility.py validate wiki-Wyckoff_House-LP-00001-chunk-0

# Compare metadata between two vectors
python scripts/vector_utility.py compare-vectors wiki-Wyckoff_House-LP-00001-chunk-0 wiki-Wyckoff_House-LP-00001-chunk-1

# Verify vector integrity in Pinecone
python scripts/vector_utility.py verify-vectors --prefix wiki-Wyckoff --limit 20 --verbose

# Verify a batch of specific vectors
python scripts/vector_utility.py verify-batch wiki-Wyckoff_House-LP-00001-chunk-0 wiki-Wyckoff_House-LP-00001-chunk-1

# Verify vectors from a file
python scripts/vector_utility.py verify-batch --file vector_ids.txt --verbose
```

For detailed help on any command, use the `--help` flag:

```bash
# Show general help
python scripts/vector_utility.py --help

# Show help for a specific command
python scripts/vector_utility.py fetch --help
```

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

> **Note**: Some standalone scripts (`fetch_pinecone_vector.py`, `check_landmark_vectors.py`) have been deprecated in favor of the unified `vector_utility.py` script. Please use the unified script for better functionality and consistency.
