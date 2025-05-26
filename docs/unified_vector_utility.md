# Unified Vector Utility

## Overview

The `vector_utility.py` script is a comprehensive tool for working with Pinecone vectors. It combines functionality
from multiple standalone scripts into a single, unified command-line tool.

## Unified Scripts

The following standalone scripts have been integrated into `vector_utility.py`:

| Original Script                | Replacement Command                | Description                                      |
| ------------------------------ | ---------------------------------- | ------------------------------------------------ |
| `fetch_pinecone_vector.py`     | `vector_utility.py fetch`          | Fetch a specific vector by ID                    |
| `check_landmark_vectors.py`    | `vector_utility.py check-landmark` | Check all vectors for a specific landmark ID     |
| ~~`list_pinecone_vectors.py`~~ | `vector_utility.py list-vectors`   | List vectors in Pinecone with optional filtering |
| `check_specific_vector.py`     | `vector_utility.py validate`       | Validate a specific vector against requirements  |

Note: Scripts with strikethrough have been completely removed from the codebase.

## Commands

### fetch

Fetch a specific vector by ID from Pinecone.

```bash
python scripts/vector_utility.py fetch <vector_id> [--pretty] [--namespace NAMESPACE]
```

### check-landmark

Check all vectors for a specific landmark ID.

```bash
python scripts/vector_utility.py check-landmark <landmark_id> [--verbose] [--namespace NAMESPACE]
```

### list-vectors

List vectors in Pinecone with optional filtering.

```bash
python scripts/vector_utility.py list-vectors [--prefix PREFIX] [--limit LIMIT] [--pretty] [--namespace NAMESPACE]
```

### validate

Validate a specific vector against metadata requirements.

```bash
python scripts/vector_utility.py validate <vector_id> [--verbose] [--namespace NAMESPACE]
```

### compare-vectors

Compare metadata between two vectors.

```bash
python scripts/vector_utility.py compare-vectors <first_vector_id> <second_vector_id> [--format {text,json}] [--namespace NAMESPACE]
```

### verify-vectors

Verify the integrity of vectors in Pinecone.

```bash
python scripts/vector_utility.py verify-vectors [--namespace NAMESPACE] [--limit LIMIT] [--prefix PREFIX] [--check-embeddings] [--verbose]
```

### verify-batch

Verify a batch of specific vectors by their IDs.

```bash
python scripts/vector_utility.py verify-batch <vector_id1> <vector_id2> ... [--file FILE] [--namespace NAMESPACE] [--check-embeddings] [--verbose]
```

## Examples

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

## Benefits of the Unified Approach

1. **Consistent Interface**: All vector-related operations follow the same command structure and parameter conventions.
1. **Reduced Cognitive Load**: Users only need to remember one script name instead of multiple separate scripts.
1. **Shared Code**: Common functionality like namespace handling and output formatting is shared across all commands.
1. **Easier Maintenance**: Changes to shared functionality automatically apply to all commands.
1. **Extensibility**: New vector-related commands can be easily added to the unified framework.
