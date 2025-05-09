NYC Landmarks Vector Database - Active Context

## Current Focus

The current focus is on the Wikipedia integration with Pinecone DB, type safety improvements, and tool integration. We have successfully implemented the core functionality to fetch, process, and store Wikipedia content in the vector database alongside existing PDF content, have begun improving type safety across the codebase, and have integrated additional development tools to enhance productivity.

### Recent Implementation

1. **Wikipedia Article Integration**
   - Created Pydantic models for Wikipedia article data (`WikipediaArticleModel`, `WikipediaContentModel`)
   - Implemented fetcher for Wikipedia content with proper error handling and rate limiting
   - Developed text processing pipeline for Wikipedia content
   - Created vector storage mechanism for Wikipedia content with proper metadata
   - Implemented distinct vector ID format for Wikipedia vectors (`wiki-{article_title}-{landmark_id}-chunk-{chunk_num}`)
   - Added verification scripts to validate the integration
   - Created comprehensive API documentation in `memory-bank/api_documentation.md` with Mermaid diagram of process flow
   - Updated API documentation with correct response schemas for CoreDataStore API endpoints
   - Added reference to definitive Swagger JSON schema at `https://api.coredatastore.com/swagger/v1/swagger.json`
   - Updated `LpcReportModel` and `LpcReportResponse` Pydantic models to match actual API schema
   - Created new Pydantic models (`LpcReportDetailResponse`, `MapData`, etc.) for detailed landmark endpoint
   - Fixed Pinecone response handling to properly process different response formats
   - Improved article metadata handling by using a centralized metadata dictionary

2. **Type Safety Improvements**
   - Fixed DbClient implementations to properly use type annotations and avoid mypy errors
   - Enhanced the handling of building data within DbClient to ensure consistent LpcReportModel return values
   - Created proper type stubs for db_client.py to satisfy mypy type checking
   - Improved error handling in DbClient methods to safely convert between dict and Pydantic model responses
   - Updated landmark building retrieval code to safely convert API responses to Pydantic models
   - Refactored `get_landmark_buildings` into smaller helper methods:
     - `_standardize_lp_number`: Ensures consistent landmark ID formatting
     - `_fetch_buildings_from_client`: Retrieves building data from the client API
     - `_fetch_buildings_from_landmark_detail`: Falls back to landmark details when direct building fetch fails
     - `_convert_building_items_to_models`: Converts various data types to consistent model objects
   - Fixed the `get_wikipedia_articles` protocol method to return a valid empty list instead of None
   - Enhanced API documentation to reflect the modular design and improved type handling in DbClient
   - Improved CoreDataStore API handling of non-standard landmark IDs through ID variation detection
   - Added pagination boundary detection to gracefully handle 404 errors at the end of available data

3. **Combined Search Implementation**
   - Created `test_combined_search.py` script to demonstrate search capabilities across both Wikipedia and PDF content
   - Implemented source filtering to allow searching specifically in Wikipedia or PDF content
   - Added proper source attribution in search results
   - Added comparison functionality to see results from different sources for the same query

4. **Development Environment Improvements**
   - Fixed script file permissions by adding proper shebang lines and execute permissions
   - Implemented centralized dependency management via `manage_packages.sh` script
   - Created comprehensive documentation on package management workflow
   - Added missing type stubs for external libraries (types-tabulate) to resolve mypy errors
   - Maintained separation between direct dependencies in setup.py and complete dependency tree in requirements.txt
   - Created log analysis tools to diagnose and fix GitHub Action workflow issues

5. **Vector ID Standardization**
   - Created `scripts/regenerate_pinecone_index.py` to standardize vector IDs
   - Implemented backup functionality to preserve vectors before making changes
   - Developed ID standardization logic for both PDF and Wikipedia content
   - Added verification capabilities to validate ID formatting
   - Added flexible ID handling via the `_standardize_landmark_id` method to handle variant formats

6. **Development Tool Integration**
   - Installed and configured the Context7 MCP server for retrieving up-to-date documentation
   - Set up the MCP configuration to use the npm package `@upstash/context7-mcp`
   - Added the server to `cline_mcp_settings.json` with proper configuration
   - Tested the server functionality by retrieving React hooks documentation
   - Enhanced the development workflow with access to current library documentation
   - Created GitHub Action log analysis tools to identify error patterns

### Recent Testing and Verification

1. **Wikipedia Import Testing**
   - Verified successful import of Wikipedia articles for test landmarks (LP-00001, LP-00003, LP-00004)
   - Confirmed proper vector ID format and metadata for Wikipedia content
   - Validated that Wikipedia content can be retrieved alongside PDF content
   - Fixed metadata handling to ensure article_title and article_url are properly stored
   - Successfully processed and validated Wikipedia article for LP-00001 (Wyckoff House)

2. **Search Functionality Testing**
   - Tested combined search across both Wikipedia and PDF content
   - Verified filtering capabilities to search exclusively in Wikipedia or PDF content
   - Confirmed proper source attribution in search results

3. **Type Checking and Linting**
   - Fixed `test_combined_search.py` mypy errors by adding `types-tabulate` package
   - Ensured all scripts have proper shebang lines and execute permissions
   - Fixed DbClient type safety issues to ensure consistent return types
   - Added proper type annotations and stubs to reduce mypy errors

4. **Vector ID Validation Testing**
   - Ran Pinecone validation tests to verify vector ID consistency
   - Identified issues with LP-00001 vectors having inconsistent ID format
   - Confirmed that 3 out of 4 test landmarks have correct ID formats, with only LP-00001 showing issues
   - Verified that all landmarks maintain consistent metadata despite ID format issues
   - Created comprehensive GitHub Action log analysis to diagnose vector rebuild issues

## Active Decisions

1. **Vector ID Format**
   - For Wikipedia content: `wiki-{article_title}-{landmark_id}-chunk-{chunk_num}`
   - For PDF content: `{landmark_id}-chunk-{chunk_num}`
   - This format allows for clear distinction between sources and enables filtering
   - **Update**: All vectors now use standardized ID formats after successful index regeneration (confirmed by tests)

2. **Source Type Attribution**
   - Added `source_type` field to all vectors (either "wikipedia" or "pdf")
   - This enables filtering searches by content source

3. **Package Management Strategy**
   - Direct dependencies are listed in `setup.py` with `>=` version format
   - Complete dependency tree is managed in `requirements.txt` with pinned versions
   - `manage_packages.sh` script synchronizes versions between the two files
   - Development dependencies like type stubs are in the `dev` extras_require section

4. **Type Safety and Pydantic Model Usage**
   - Use Pydantic models instead of raw dictionaries for API responses when possible
   - Provide fallback mechanisms when Pydantic model conversion fails
   - Create proper type stubs for key modules to improve static type checking
   - Always provide default values for required model fields when conversion might fail
   - Implement ID format standardization with flexible handling for variant formats

5. **Development Tools Integration**
   - Use Context7 MCP server for up-to-date library documentation during development
   - Maintain MCP server configuration in cline_mcp_settings.json
   - Use standardized server naming convention with GitHub repository URL format
   - Keep MCP servers disabled by default and require explicit approval for operations
   - Perform log analysis on GitHub Action workflows to identify and fix issues

6. **API Error Handling Improvements**
   - Gracefully handle pagination boundary errors (404 on pages beyond available data)
   - Implement flexible landmark ID handling to accommodate various ID formats
   - Return empty but valid response structures instead of raising exceptions
   - Add detailed logging for all API interaction failures
   - Use multiple ID format variations when retrieving landmark data to maximize success

7. **Wikipedia Metadata Handling**
   - Create a single metadata dictionary and update it once rather than individual field assignments
   - Ensure consistent article_title and article_url fields in all Wikipedia vectors
   - Use centralized article_metadata in the wikipedia_fetcher module to ensure consistency
   - Store article metadata alongside chunk metadata for complete information attribution

## Next Steps

1. **Execute Vector ID Standardization (Completed)**
   - ✅ Ran the `scripts/regenerate_pinecone_index.py` script to fix inconsistent vector IDs
   - ✅ Fixed LP-00001 vectors that previously used the non-standard format `test-LP-00001-LP-00001-chunk-X`
   - ✅ Used the `--verbose` flag for detailed logging during execution
   - ✅ Verified all vectors follow the standardized format by running the validation tests
   - 🔍 Issue encountered: zero embeddings in backed-up vectors, requiring full regeneration via GitHub Actions
   - ✅ GitHub Action successfully rebuilt the index with proper standardized IDs (16,136 vectors with consistent format)

2. **Testing Updates (Completed)**
   - ✅ Updated integration tests to remove special handling for LP-00001's non-standard format
   - ✅ Modified `tests/integration/test_pinecone_fixed_ids.py` to expect standardized ID formats for all landmarks
   - ✅ Confirmed all tests pass with the standardized vector ID formats
   - ✅ Enhanced pagination handling with proper path parameter formatting

3. **Fix Remaining Type Safety Issues**
   - Address mypy errors in test files that use older model versions
   - Create proper type stubs for external dependencies where missing
   - Update API interaction code to consistently use the new Pydantic models

4. **Wikipedia Integration Completion (Completed)**
   - ✅ Created Wikipedia processing GitHub Actions workflow in `.github/workflows/process_wikipedia.yml`
   - ✅ Implemented processing script `scripts/process_wikipedia_articles.py` with parallel processing
   - ✅ Added verification capability through `scripts/verify_wikipedia_imports.py`
   - ✅ Developed demonstration script `scripts/demonstrate_wikipedia_integration.py`
   - ✅ Created integration test in `tests/integration/test_wikipedia_integration.py`
   - ✅ Fixed metadata handling in wikipedia_fetcher.py to ensure proper article attribution
   - ✅ Updated PineconeDB response handling to work with different client versions

5. **Query API Enhancement (Completed)**
   - ✅ Enhanced Query API to leverage both Wikipedia and PDF content
   - ✅ Added source attribution in search results with clear identification of Wikipedia vs PDF
   - ✅ Implemented combined search with filtering by source_type
   - ✅ Created comparison functionality to evaluate results from different sources
   - ✅ Used `landmark_query_testing.ipynb` to verify enhanced search capabilities
   - ✅ Added metadata for article titles and URLs in search results

6. **Chat API Enhancement (Completed)**
   - ✅ Updated Chat API to leverage both Wikipedia and PDF content
   - ✅ Added source attribution to responses using [Source: Wikipedia article 'Title'] format
   - ✅ Added source_types field to ChatResponse model to track which sources were used
   - ✅ Improved system prompt to properly incorporate and acknowledge Wikipedia sources
   - ✅ Enhanced vector filtering to support both content types

7. **Process Additional Wikipedia Articles**
   - Execute processing for more landmarks to increase Wikipedia coverage
   - Update verification script to validate proper metadata for all processed landmarks
   - Use the parallel processing feature to efficiently process multiple landmarks

8. **Development Tools Expansion**
   - Leverage Context7 MCP for Pinecone, Pydantic, and other library documentation
   - Explore additional MCP servers for specialized functionality
   - Document library usage patterns based on up-to-date documentation
   - Create library-specific reference guides for the project

9. **API Improvement Implementation**
   - Implement recommendations from vector_rebuild_analysis.md
   - Add robust error recovery for vector storage operations
   - Implement batch validation before storage
   - Add comprehensive error reporting to the GitHub Action workflow
   - Create specific tests for pagination boundary cases and non-standard ID formats

## Open Questions

1. **Scale Considerations**
   - How many landmarks have associated Wikipedia articles?
   - What is the performance impact of searching across both sources?
   - Should we prioritize certain sources in search results?

2. **Quality Assurance**
   - How can we verify the quality of Wikipedia content?
   - Should we implement content validation before storage?
   - What metrics should we track for search quality?

3. **Type Safety Migration**
   - How should we handle test files that rely on the old models?
   - Should we update all tests at once or incrementally?
   - Do we need a comprehensive pass to update all code that uses the models?

4. **API Error Handling Strategy**
   - How should we handle variant landmark ID formats in the production code?
   - What is the best approach for pagination boundary detection?
   - Should we implement automatic retry logic for failed API requests?
