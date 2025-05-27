# Scripts Documentation

# fetch_landmark_reports.py

This script provides a unified interface for retrieving, filtering, and exporting NYC landmark reports from the CoreDataStore API using the project's `DbClient` abstraction. It is designed for robust, large-scale data extraction and supports a variety of output formats and filtering options.

**Key Features:**

- Fetches all landmark reports with intelligent pagination and progress tracking
- Supports filtering by borough, object type, neighborhood, and text search
- Extracts and exports PDF URLs for landmark reports
- Optionally downloads a sample of PDF reports
- Exports results to JSON and Excel (XLSX) formats
- Allows sorting, custom page sizes, and limiting the number of records
- Provides detailed processing metrics and logging

**Usage Examples:**

```bash
# Fetch all landmark reports with default settings
python scripts/fetch_landmark_reports.py

# Filter by borough and object type
python scripts/fetch_landmark_reports.py --borough Manhattan --object-type "Individual Landmark"

# Export results to Excel
python scripts/fetch_landmark_reports.py --export-excel

# Download sample PDFs (first 5)
python scripts/fetch_landmark_reports.py --download --samples 5
```

**Output Files:**

- JSON: Full landmark data and extracted PDF URLs (with timestamps)
- Excel: XLSX file with all report data (if `--export-excel` is used)
- Sample PDFs: Downloaded to a specified directory (if `--download` is used)

**Main Functions:**

- Fetches all reports with optional filters and pagination
- Extracts PDF URLs from reports
- Downloads a sample of PDF files
- Exports data to JSON and Excel
- Tracks and prints processing metrics

**Dependencies:**

- `nyc_landmarks.db.db_client` (database access)
- `nyc_landmarks.models.landmark_models` (data models)
- `nyc_landmarks.utils.logger` (logging)
- `nyc_landmarks.utils.excel_helper` (Excel export)

See the script's docstring or run with `--help` for a full list of options and arguments.

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
