# Active Context

## Current Focus

The current focus is on refactoring and consolidating code duplication between `scripts/vector_utility.py` and `nyc_landmarks/vectordb/pinecone_db.py` to improve maintainability and reduce redundancy.

## Recent Changes

### PineconeDB Enhancement - Phase 1 Complete (2025-05-25)

Successfully enhanced the `PineconeDB` class with four new methods to consolidate functionality from `scripts/vector_utility.py`:

1. **`fetch_vector_by_id()`** - Consolidated vector fetching logic

   - Replaces manual Pinecone index operations from utility script
   - Supports optional namespace parameter
   - Returns standardized dictionary format
   - Includes proper error handling and logging

1. **`list_vectors_with_filter()`** - Enhanced vector listing with prefix filtering

   - Supports optional prefix filtering for vector IDs
   - Implements smart limit adjustment for prefix searches
   - Returns standardized list of vector dictionaries
   - Case-insensitive prefix matching

1. **`query_vectors_by_landmark()`** - Landmark-specific vector queries

   - Filters vectors by landmark_id metadata
   - Uses dummy vector approach for metadata-only queries
   - Supports optional namespace parameter
   - Returns standardized match format

1. **`validate_vector_metadata()`** - Comprehensive vector validation

   - Validates required metadata fields for all vectors
   - Checks Wikipedia-specific fields for wiki vectors
   - Validates vector ID format patterns
   - Checks for valid embeddings (non-zero, non-empty)
   - Returns tuple of (is_valid, list_of_issues)

### Technical Implementation Details

- Added necessary imports: `re` for regex patterns, `numpy` for embedding validation
- All methods support optional namespace parameters with fallback to instance default
- Consistent error handling and logging throughout
- Methods return standardized data formats for easy consumption
- Proper type annotations and documentation

## Active Decisions and Considerations

1. **Code Consolidation Strategy**: Move from duplicated Pinecone operations in scripts to centralized methods in `PineconeDB` class, making the utility script a thin CLI wrapper.

1. **Namespace Flexibility**: All new methods accept optional namespace parameters while falling back to instance defaults, providing maximum flexibility for different use cases.

1. **Standardized Return Formats**: All methods return consistent dictionary formats to ensure compatibility across the codebase.

1. **Validation Patterns**: Comprehensive validation includes both metadata structure and content validation (embeddings), following established patterns from the utility script.

## Next Steps

### Phase 2: Refactor Vector Utility Script

1. **Replace duplicated functions** in `scripts/vector_utility.py`:

   - Replace `_setup_pinecone_client()` with direct `PineconeDB` instantiation
   - Replace `fetch_vector()` with `PineconeDB.fetch_vector_by_id()`
   - Replace `query_landmark_vectors()` with `PineconeDB.query_vectors_by_landmark()`
   - Replace `list_vectors()` logic with `PineconeDB.list_vectors_with_filter()`
   - Replace validation functions with `PineconeDB.validate_vector_metadata()`

1. **Simplify script architecture**:

   - Focus on CLI interface and output formatting
   - Remove ~400 lines of duplicated Pinecone operations
   - Preserve specialized command-line handling and pretty-printing logic

1. **Test enhanced functionality**:

   - Verify all utility script commands work with new PineconeDB methods
   - Ensure output formatting remains consistent
   - Test error handling and edge cases

### Expected Benefits

- **Reduced Code Duplication**: Eliminate ~30% of code in vector_utility.py
- **Single Source of Truth**: All Pinecone operations centralized in PineconeDB class
- **Improved Maintainability**: Changes to Pinecone logic only need to happen once
- **Better Reusability**: Other parts of codebase can use enhanced PineconeDB methods
- **Consistent Error Handling**: Unified approach to Pinecone error management
