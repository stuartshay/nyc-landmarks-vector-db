# Wikipedia Vector Metadata Issue Fix

On May 18, 2025, we identified and fixed an issue with Wikipedia vector metadata in the `process_wikipedia_articles.py` script:

## Issue
Wikipedia vectors were missing the required `article_title` and `article_url` metadata fields even though the script was correctly adding these fields to the chunk metadata.

## Root Cause
The issue was due to a mismatch between how metadata was added in `process_wikipedia_articles.py` and how it was read in `PineconeDB._create_metadata_for_chunk()`:

1. In `process_wikipedia_articles.py`, we were adding the article title and URL directly to the `metadata` field of each chunk.
2. However, in `PineconeDB._create_metadata_for_chunk()`, the code was looking for these values in a separate `article_metadata` field, which didn't exist in our chunks.

## Solution
Modified `process_wikipedia_articles.py` to add the information in both locations:

1. Added the article title and URL directly to `metadata` (for backwards compatibility)
2. Added the article information to `article_metadata` as well, which is used by `PineconeDB._create_metadata_for_chunk()`

## Verification
We verified the fix by:
1. Running `process_wikipedia_articles.py` for the Wyckoff House landmark (LP-00001)
2. Using `check_specific_vector.py` to confirm the vector now has the proper metadata fields

## Code Changes
Updated the Wikipedia article processing code to add metadata in both locations:
```python
# Add article_metadata field which is used by PineconeDB._create_metadata_for_chunk
if 'article_metadata' not in chunk:
    chunk['article_metadata'] = {}
chunk['article_metadata']['title'] = wiki_article.title
chunk['article_metadata']['url'] = wiki_article.url

# Also add directly to metadata for backwards compatibility
if 'metadata' in chunk and chunk['metadata'] is not None:
    chunk['metadata']['article_title'] = wiki_article.title
    chunk['metadata']['article_url'] = wiki_article.url
```

This ensures compatibility with both the current database implementation and any code that might be looking for these fields directly in the metadata.
