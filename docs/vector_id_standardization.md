# Vector ID Standardization

## Overview

This document explains the standardization of vector IDs in the NYC Landmarks Vector
Database project.

## Current Vector ID Format Standards

All vectors in the Pinecone database should follow these ID format conventions:

### For PDF-sourced content:

```
{landmark_id}-chunk-{chunk_index}
```

Example: `LP-00001-chunk-0`

### For Wikipedia-sourced content:

```
wiki-{article_title}-{landmark_id}-chunk-{chunk_index}
```

Example: `wiki-Empire_State_Building-LP-00001-chunk-0`

### For test data:

```
LP-99999-chunk-{chunk_index}
```

## Known Issues

Currently, some vectors (particularly those for landmark LP-00001) have inconsistent ID
formats that don't follow these conventions. These include:

- IDs starting with `test-LP-00001-`
- Wikipedia articles with various ID formats

## Resolution

The script `scripts/regenerate_pinecone_index.py` has been created to standardize all
vector IDs. This script:

1. Exports all vectors from the current Pinecone index
1. Standardizes their IDs according to the format rules
1. Recreates the index (optional)
1. Reimports the vectors with standardized IDs

## Integration Tests

Integration tests in `tests/integration/test_pinecone_validation.py` currently have
special handling for LP-00001 to accommodate the non-standard IDs. Once the
standardization script has been run on the production database, these exceptions should
be removed so that all landmarks are tested with the same strict standards.

## Timeline

- **Current State**: Special handling for non-standard IDs in tests
- **Next Step**: Run the standardization script on production
- **Final State**: Remove special handling in tests, enforce consistent standards

## References

- [Standardization Script](/scripts/regenerate_pinecone_index.py)
- [Integration Tests](/tests/integration/test_pinecone_validation.py)
