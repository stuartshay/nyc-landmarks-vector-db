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

## Active Decisions

1. **Vector ID Format**
   - For Wikipedia content: `wiki-{article_title}-{landmark_id}-chunk-{chunk_num}`
   - For PDF content: `{landmark_id}-{report_name}-{page_num}-{chunk_num}`
   - This format allows for clear distinction between sources and enables filtering

2. **Source Type Attribution**
   - Added `source_type` field to all vectors (either "wikipedia" or "pdf")
   - This enables filtering searches by content source

3. **Package Management Strategy**
   - Direct dependencies are listed in `setup.py` with `>=` version format
   - Complete dependency tree is managed in `requirements.txt` with pinned versions
   - `manage_packages.sh` script synchronizes versions between the two files
   - Development dependencies like type stubs are in the `dev` extras_require section

## Next Steps

1. **CI/CD Integration**
   - Add Wikipedia processing to GitHub Actions workflow
   - Implement verification in the CI/CD pipeline

2. **Chat API Enhancement**
   - Update to leverage both Wikipedia and PDF content
   - Add source attribution to responses

3. **Testing Improvements**
   - Add dedicated integration tests for Wikipedia article pipeline
   - Implement end-to-end tests for complete vector search workflow

## Open Questions

1. **Scale Considerations**
   - How many landmarks have associated Wikipedia articles?
   - What is the performance impact of searching across both sources?
   - Should we prioritize certain sources in search results?

2. **Quality Assurance**
   - How can we verify the quality of Wikipedia content?
   - Should we implement content validation before storage?
   - What metrics should we track for search quality?
