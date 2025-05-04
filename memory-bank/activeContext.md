# NYC Landmarks Vector Database - Active Context

## Current Work Focus
We are now implementing the Wikipedia Article integration for the NYC Landmarks Vector Database project. Significant implementation work has already been completed, with several components already in place. Our current priorities are:

1. **Testing and Validating the Wikipedia Article Integration**: Testing the already implemented components for Wikipedia article integration, including fetching, processing, and storing Wikipedia content in the vector database.
2. **Enhancing Vector Search with Wikipedia Content**: Updating the vector search capabilities to properly handle and distinguish between PDF content and Wikipedia content in search results.
3. **Updating the Chat API**: Enhancing the Chat API to leverage the combined PDF and Wikipedia content for improved responses.
4. **CI/CD Integration**: Adding Wikipedia processing to the GitHub Actions workflow for automated updates.
5. **Documentation and Analytics**: Updating project documentation and implementing tracking for the enhanced data sources.

## Recent Changes
- Created initial project documentation in the memory bank
- Defined the system architecture and core components
- Specified the technical requirements and constraints
- Implemented CoreDataStore API client for landmark data access
- Decided to use CoreDataStore API exclusively as the data source
- Updated API modules to use the database client with CoreDataStore API
- Added MCP server to provide tools for interacting with CoreDataStore API
- Created Pydantic models for data validation of API responses and internal data structures
- Implemented unit and integration tests for the landmark report fetcher
- Set up test infrastructure for pytest in VS Code
- Added integration tests for the CoreDataStore MCP server
- Refactored scripts to use Pydantic for robust data validation
- Updated the `.github/workflows/process_landmarks.yml` GitHub Action for manual triggering, robust batch processing using a matrix strategy, configurable parallelism, and improved dependency installation.
- **Added pip caching to the GitHub Actions workflow to speed up dependency installation and reduce redundant downloads in parallel jobs.**
- **Refactored the CI/CD workflow to build a Docker image with all dependencies in a single job, push it to GitHub Container Registry, and run all parallel jobs using this pre-built image. This ensures all jobs share the same environment and eliminates redundant setup steps.**
- **Created a Dockerfile at the repository root to enable the CI/CD workflow to build and push the Docker image. This resolves the previous job failure due to a missing Dockerfile.**
- **Created a comprehensive Jupyter notebook `pinecone_db_stats.ipynb` for analyzing Pinecone vector database statistics, providing insights into the distribution, metadata, and clustering of landmark vectors.**
- **Created a Jupyter notebook `landmark_query_testing.ipynb` for testing the vector search capabilities, including basic queries, filtering, and performance metrics. This notebook forms the foundation for the Query API Enhancement project.**
- **Cleaned up redundant notebooks by removing duplicates and fixing compatibility issues. Standardized on maintaining only the latest functional versions of notebooks and their executed outputs.**
- **Established a formal practice of executing all notebooks in the terminal with `jupyter nbconvert` to ensure they run correctly in headless environments and to produce output files that can be committed for review.**
- **Enhanced PineconeDB implementation with deterministic vector IDs to prevent duplicate records and maintain metadata consistency when processing the same landmarks multiple times. This resolves issues with growing database size and inconsistent filtering.**
- **Created comprehensive verification tools for Pinecone database validation, including both standalone script (`verify_pinecone_fixed_ids.py`) and integrated test modules (`tests/verification/test_pinecone_fixed_ids.py` and `tests/integration/test_pinecone_validation.py`)**
- **Updated project dependencies in setup.py and requirements.txt to use the latest stable versions. Specifically updated fastapi, uvicorn, openai, pinecone-client, and other key dependencies. Fixed grpcio and grpcio-status to use stable versions rather than release candidates.**
- **Implemented a fully functional Chat API endpoint that uses the existing conversation memory system and includes robust error handling and data validation.**
- **Added unit tests for the Chat API that cover basic conversation, existing conversation, landmark filtering, and error handling scenarios.**
- **Enhanced the implementation to use proper Python type annotations for better code quality and maintainability.**
- **Created a GitHub Actions workflow for deploying to Google Cloud Run (`deploy-gcp.yml`), enabling continuous deployment of the NYC Landmarks Vector DB service with appropriate memory allocation and environment configuration.**
- **Implemented core Wikipedia article integration components:**
  - **Created Pydantic models for Wikipedia article data (`WikipediaArticleModel`, `WikipediaContentModel`, `WikipediaProcessingResult`)**
  - **Enhanced CoreDataStore API client with methods to fetch Wikipedia articles for landmarks**
  - **Developed a Wikipedia content fetcher with rate limiting, error handling, and retries**
  - **Implemented text processing pipeline for Wikipedia content including cleaning and chunking**
  - **Created a processing script to handle Wikipedia article embedding and storage in Pinecone**
  - **Added a notebook for testing Wikipedia integration (`wikipedia_integration_testing.ipynb`)**

## Next Steps
The following steps are needed to complete the Wikipedia article integration:

### Phase 1: Testing and Validation (Current Focus)
1. Test the existing Wikipedia article fetching functionality with a range of landmarks
2. Validate the text processing pipeline for Wikipedia content
3. Verify embedding generation and vector storage with proper metadata
4. Create comprehensive integration tests for the Wikipedia processing pipeline
5. Run performance analyses to optimize the processing pipeline

### Phase 2: Vector Search Enhancement
1. Update vector search queries to handle the combined PDF and Wikipedia sources
2. Implement source filtering options in the query interface
3. Add proper source attribution in search results
4. Enhance metadata filtering to leverage Wikipedia-specific fields
5. Optimize relevance ranking to balance PDF and Wikipedia content

### Phase 3: Chat API Integration
1. Update the Chat API to retrieve context from both PDF and Wikipedia sources
2. Implement source weighting for better response quality
3. Add source attribution in chat responses
4. Enhance conversation memory to track source preferences

### Phase 4: CI/CD Integration
1. Add Wikipedia processing to the GitHub Actions workflow
2. Implement incremental updates for efficiency
3. Create monitoring and alerting for Wikipedia processing
4. Add vector database verification for Wikipedia content

### Phase 5: Documentation and Analytics
1. Update technical documentation with Wikipedia integration details
2. Create user guides for the enhanced search capabilities
3. Implement tracking for sources used in vector searches
4. Develop dashboards for monitoring Wikipedia content statistics

## Active Decisions and Considerations

### Wikipedia Article Integration Strategy
- **Implementation Status:**
  - ✅ Modular pipeline for Wikipedia article processing is implemented
  - ✅ Leveraging existing components (embedding generator, vector storage)
  - ✅ Wikipedia-specific functionality developed (fetcher, chunker)
  - ✅ Source attribution in metadata to distinguish between PDF and Wikipedia content
- **Data Flow (Implemented):**
  - ✅ Fetch landmarks from CoreDataStore API using pagination
  - ✅ Check for associated Wikipedia articles for each landmark
  - ✅ Fetch article content using provided URLs with rate limiting and retries
  - ✅ Process content for embedding (cleaning, chunking)
  - ✅ Generate embeddings for chunks
  - ✅ Store in Pinecone with enhanced metadata
- **Metadata Enhancement (Implemented):**
  - ✅ "source_type" field with value "wikipedia" (vs "pdf" for existing content)
  - ✅ Wikipedia URL as "article_url" in metadata
  - ✅ Article title as "article_title" in metadata
  - ✅ Maintained existing landmark metadata (ID, name, borough, etc.)
- **Technical Solutions (Implemented):**
  - ✅ Rate limiting for Wikipedia requests (1 second between requests)
  - ✅ Retry mechanism with exponential backoff for transient errors
  - ✅ Error handling for missing or inaccessible articles
  - ✅ Deterministic vector IDs for Wikipedia content to prevent duplication
  - ✅ Configured chunking strategy for Wikipedia content (1000 chars with 200 char overlap)

### Vector Database Verification Strategy
- **Created a dual-approach to vector database verification:**
  - Standalone script (`verify_pinecone_fixed_ids.py`) for manual verification and detailed reporting
  - Integrated test modules for automated testing in the CI/CD pipeline
- **Verification covers critical aspects:**
  - Deterministic vector ID format (e.g., `LP-00001-chunk-0`)
  - Metadata consistency across chunks from the same landmark
  - Essential metadata fields present in all vectors
  - Proper handling of deletion and re-insertion with fixed IDs
- **Implemented both detailed and summary reporting:**
  - JSON output files for detailed analysis
  - Console summary reports for quick verification
  - Configurable verbosity for debugging
- **Test integration allows for:**
  - Running verifications after every processing job
  - CI/CD integration to ensure quality in automated workflows
  - Reusable verification components across scripts and tests

### MCP Server Integration

#### CoreDataStore Swagger MCP Server
- MCP server configured for direct access to CoreDataStore API
- Provides multiple tools for retrieving NYC landmarks data:
  - GetLpcReport: Get details for a specific landmark preservation report
  - GetLpcReports: List multiple landmark reports with filtering options
  - GetLandmarks: Retrieve buildings linked to landmarks
  - GetLandmarkStreets: Get street information for landmarks
  - GetLpcPhotoArchive/GetLpcPhotoArchiveCount: Access photo archive
  - GetPlutoRecord: Access PLUTO data
  - GetBoroughs, GetNeighborhoods, GetObjectTypes, GetArchitectureStyles: Reference data
  - GetLpcContent: Access additional content
- Integration is included in project configuration but currently experiencing connection timeouts (confirmed with multiple tool attempts)
- All MCP tool calls result in timeout errors with code -32001, suggesting potential configuration or connectivity issues that need to be resolved
- Integration testing code is implemented to verify functionality when server is available
- Encapsulated in DB client with proper error handling and fallback mechanisms

#### Pinecone Assistant MCP Server
- Identified as a potential enhancement to our current Pinecone implementation
- Provides an MCP server implementation for retrieving information from Pinecone Assistant
- Features include configurable results retrieval and Docker-based deployment
- Requires additional setup: Pinecone API key and Pinecone Assistant API host
- Research needed to understand:
  - Differences between core Pinecone and Pinecone Assistant
  - Migration path for current vector data
  - Feature compatibility with our current metadata filtering needs
  - Integration effort vs. benefits assessment

### Testing Strategy
- Using pytest as the primary testing framework
- Implementing both unit and integration tests
- Utilizing mock objects for unit tests to isolate components
- Leveraging the CoreDataStore MCP server for integration testing
- Adding explicit markers for different test categories (unit, integration, mcp)
- Configuring VS Code for test discovery and execution
- Using Jupyter notebooks for interactive testing of complex components like vector search
- **All Jupyter notebooks MUST be tested using `jupyter nbconvert --to notebook --execute` in the terminal to:**
  - **Verify they run correctly in headless environments (CI/CD pipelines)**
  - **Generate output files that can be committed for review by team members**
  - **Ensure consistent execution across different environments**
  - **Detect and fix errors early in the development process**
- **Vector database verification is now integrated into the testing strategy with:**
  - Reusable verification functions for use in both manual scripts and automated tests
  - Integration tests that verify deterministic ID format and metadata consistency
  - Comprehensive validation across multiple landmarks to ensure system-wide integrity

### Pydantic Integration
- Using Pydantic for data validation across the application
- Created models for API responses and data structures
- Leveraging Pydantic's validation features for robust error handling
- Improving type safety through Pydantic's type annotations
- Utilizing Pydantic for configuration management

### Configuration Management
- Using Google Cloud Secret Store for credential management in production
- Need to implement fallback mechanisms for local development
- Need to determine the specific secrets required and their structure

### PDF Processing Strategy
- Need to evaluate PDF extraction libraries (PyPDF2, PDFPlumber, etc.) for accuracy and performance
- Need to determine the optimal chunking strategy for the landmark PDFs
- Consider how to handle PDF extraction errors and edge cases

### Vector Database Setup
- Need to create appropriate Pinecone index with optimal dimensions and metric
- Define metadata structure for vectors to enable efficient filtering
- Determine batch processing strategy for embedding generation and storage
- **Implemented and verified deterministic vector ID system to prevent duplicate vectors**
- **Added comprehensive metadata validation to ensure data integrity**

### Vector Search Enhancement
- Created foundation for Query API Enhancement with the `landmark_query_testing.ipynb` notebook
- Testing basic vector search capabilities and filtering options
- Measuring query performance metrics to optimize response times
- Exploring filter combinations for improved search relevance
- Planning integration of vector search with the chat API

### API Design
- Need to define API endpoints for vector search and chat functionality
- Consider authentication and rate limiting for the API
- Determine how to handle conversation context in the chat API

### Notebook Management
- **Notebook Execution Workflow:**
  - Consolidated script `run_all_notebooks.py` serves as the primary tool for notebook execution
  - Supports running all notebooks or a single notebook with configurable options:
    ```
    # Run all notebooks in the default directory
    python scripts/run_all_notebooks.py

    # Run a specific notebook
    python scripts/run_all_notebooks.py --notebook notebooks/landmark_query_testing.ipynb

    # Customize output directory
    python scripts/run_all_notebooks.py --output-dir custom_output/notebooks

    # Set cell execution timeout
    python scripts/run_all_notebooks.py --timeout 1200
    ```
  - All executed notebooks are saved with outputs to `test_output/notebooks` with `_executed` suffix
  - Execution results provide summary report of successful/failed notebooks

- **Notebook Standardization:** Maintaining only the latest and most functional versions of notebooks to avoid duplication and confusion
- **Notebook Execution:** All notebooks are executed using the project's script to verify functionality
- **Executed Notebook Storage:** Store executed notebooks in the `test_output/notebooks` directory (excluded from source control) to:
  - Keep the repository clean and minimize unnecessary git diffs
  - Maintain a clear separation between source notebooks and their execution results
  - Provide a structured location for CI/CD pipelines to store execution artifacts
- **Output Clearing:** All notebook cell outputs MUST be cleared before committing via nbstripout pre-commit hook
- **Linting:** All notebooks are linted with nbQA, applying black, isort, and flake8 standards
- **Documentation:** Each notebook must include clear markdown cells explaining purpose and usage
- **Cell Structure:** Logical organization of setup, processing, and visualization cells with proper documentation

### Jupyter Notebook Standards
- **Structure and Organization**
  - Begin with a title and description markdown cell
  - Group related code into logical sections with markdown headers
  - End with a summary/conclusion cell
- **Code Quality**
  - Follow PEP 8 style guide (automatically enforced by nbQA)
  - Use descriptive variable names
  - Include docstrings for functions
  - Keep cell outputs cleared in version control
- **Documentation**
  - Each notebook should start with a clear purpose statement
  - Document data sources and transformations
  - Include explanatory markdown cells between code sections
  - Add comments for complex operations
- **Execution**
  - All notebooks must be tested using `jupyter nbconvert` to confirm functionality
  - All cells should execute in sequential order
  - Notebooks should be designed to run in headless environments
- **Output Management**
  - Cell outputs are never committed to version control (enforced by nbstripout)
  - Execution results are saved in test_output directory for review
  - Visualizations should include clear titles and legends

### Integration Points
- Implemented comprehensive CoreDataStore API client for accessing NYC landmarks data
- Leveraging coredatastore-swagger-mcp server to provide direct access to API functionality
- Extended functionality with methods for accessing landmark data, buildings, photos, PLUTO data, etc.
- Need to determine how to map PDF content to landmark records
- Plan for integration with existing frontend applications

## Current Challenges
1. Determining the optimal text chunking strategy for landmark PDFs
2. Setting up efficient batch processing for embedding generation
3. Designing a scalable conversation memory system
4. Balancing performance, cost, and accuracy in the vector search system
5. Optimizing CoreDataStore API usage for performance and reliability
6. Ensuring proper error handling for all external API calls
7. Managing dependencies and ensuring consistent environment setup
8. Optimizing vector search queries for better relevance and performance
9. **Maintaining metadata consistency when reprocessing landmarks in the vector database**
10. **Integrating Wikipedia content with existing PDF content in the vector database**
11. **Handling potential rate limits when fetching Wikipedia articles**
12. **Ensuring proper attribution and distinction between PDF and Wikipedia content in search results**

## Team Collaboration
- Documentation being maintained in the memory bank
- Code will be managed through GitHub with feature branches
- CI/CD pipeline will be implemented using GitHub Actions
- Testing infrastructure is set up for continuous testing
- Jupyter notebooks used for interactive testing and demonstration of complex components
- All notebooks must be tested in the terminal and committed with outputs for review
- **Vector database verification tools provide confidence in data integrity**
