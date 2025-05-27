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
```
