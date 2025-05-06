NYC Landmarks Vector Database - Active Context

## Current Focus

The current focus is on the Wikipedia article integration with Pinecone DB. We have successfully implemented the core functionality to fetch, process, and store Wikipedia content in the vector database alongside existing PDF content.

### Recent Implementation

1. **Wikipedia Article Integration**
   - Created Pydantic models for Wikipedia article data (`WikipediaArticleModel`, `WikipediaContentModel`)
   - Implemented fetcher for Wikipedia content with proper error handling and rate limiting
   - Developed text processing pipeline for Wikipedia content
   - Created vector storage mechanism for Wikipedia content with proper metadata
   - Implemented distinct vector ID format for Wikipedia vectors (`wiki-{article_title}-{landmark_id}-chunk-{chunk_num}`)
   - Added verification scripts to validate the integration
   - Created comprehensive API documentation in `memory-bank/api_documentation.md` with Mermaid diagram of process flow

2. **Combined Search Implementation**
   - Created `test_combined_search.py` script to demonstrate search capabilities across both Wikipedia and PDF content
   - Implemented source filtering to allow searching specifically in Wikipedia or PDF content
   - Added proper source attribution in search results
   - Added comparison functionality to see results from different sources for the same query

3. **Development Environment Improvements**
   - Fixed script file permissions by adding proper shebang lines and execute permissions
   - Implemented centralized dependency management via `manage_packages.sh` script
   - Created comprehensive documentation on package management workflow
   - Added missing type stubs for external libraries (types-tabulate) to resolve mypy errors
   - Maintained separation between direct dependencies in setup.py and complete dependency tree in requirements.txt

4. **Vector ID Standardization**
   - Created `scripts/regenerate_pinecone_index.py` to standardize vector IDs
   - Implemented backup functionality to preserve vectors before making changes
   - Developed ID standardization logic for both PDF and Wikipedia content
   - Added verification capabilities to validate ID formatting

### Recent Testing and Verification

1. **Wikipedia Import Testing**
   - Verified successful import of Wikipedia articles for test landmarks (LP-00001, LP-00003, LP-00004)
   - Confirmed proper vector ID format and metadata for Wikipedia content
   - Validated that Wikipedia content can be retrieved alongside PDF content

2. **Search Functionality Testing**
   - Tested combined search across both Wikipedia and PDF content
   - Verified filtering capabilities to search exclusively in Wikipedia or PDF content
   - Confirmed proper source attribution in search results

3. **Type Checking and Linting**
   - Fixed `test_combined_search.py` mypy errors by adding `types-tabulate` package
   - Ensured all scripts have proper shebang lines and execute permissions

4. **Vector ID Validation Testing**
   - Ran Pinecone validation tests to verify vector ID consistency
   - Identified issues with LP-00001 vectors having inconsistent ID format
   - Confirmed that 3 out of 4 test landmarks have correct ID formats, with only LP-00001 showing issues
   - Verified that all landmarks maintain consistent metadata despite ID format issues

## Active Decisions

1. **Vector ID Format**
   - For Wikipedia content: `wiki-{article_title}-{landmark_id}-chunk-{chunk_num}`
   - For PDF content: `{landmark_id}-chunk-{chunk_num}`
   - This format allows for clear distinction between sources and enables filtering
   - **Note**: Testing has revealed inconsistent ID formats in the index (particularly for LP-00001, which uses `test-LP-00001-LP-00001-chunk-X` instead of the standard format)

2. **Source Type Attribution**
   - Added `source_type` field to all vectors (either "wikipedia" or "pdf")
   - This enables filtering searches by content source

3. **Package Management Strategy**
   - Direct dependencies are listed in `setup.py` with `>=` version format
   - Complete dependency tree is managed in `requirements.txt` with pinned versions
   - `manage_packages.sh` script synchronizes versions between the two files
   - Development dependencies like type stubs are in the `dev` extras_require section

## Next Steps

1. **Execute Vector ID Standardization**
   - Run the `scripts/regenerate_pinecone_index.py` script to fix inconsistent vector IDs
   - Focus on fixing LP-00001 vectors that currently use the non-standard format `test-LP-00001-LP-00001-chunk-X`
   - Use the `--verbose` flag for detailed logging during execution
   - Verify all vectors follow the standardized format after regeneration by running the validation tests

2. **Testing Updates**
   - Update integration tests to remove special handling for LP-00001's non-standard format
   - Modify `tests/integration/test_pinecone_validation.py` to expect standardized ID formats for all landmarks
   - Ensure all tests pass with the standardized vector ID formats

3. **Wikipedia Integration Completion**
   - Add Wikipedia processing to GitHub Actions workflow
   - Implement verification steps in the CI/CD pipeline
   - Create dedicated integration tests for the Wikipedia article pipeline

4. **Query API Enhancement**
   - Update the Query API to leverage both Wikipedia and PDF content
   - Add source attribution in search results
   - Implement combined search with proper filtering capabilities
   - Use the `landmark_query_testing.ipynb` notebook to test enhanced search features

5. **Chat API Enhancement**
   - Update to leverage both Wikipedia and PDF content
   - Add source attribution to responses
   - Test using both content sources in chat generation

## Open Questions

1. **Scale Considerations**
   - How many landmarks have associated Wikipedia articles?
   - What is the performance impact of searching across both sources?
   - Should we prioritize certain sources in search results?

2. **Quality Assurance**
   - How can we verify the quality of Wikipedia content?
   - Should we implement content validation before storage?
   - What metrics should we track for search quality?
