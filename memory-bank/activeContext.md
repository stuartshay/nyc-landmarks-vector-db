# NYC Landmarks Vector Database - Active Context

## Current Work Focus
We are in the initial setup phase of the NYC Landmarks Vector Database project. Our immediate focus is on:

1. Setting up the project structure and organization
2. Establishing the foundation for the PDF processing pipeline
3. Creating the configuration management system
4. Setting up connections to external services (OpenAI, Pinecone, Azure, CoreDataStore API)
5. Implementing comprehensive testing for scripts and API integrations
6. Integrating Pydantic for data validation throughout the system
7. Enhancing vector search capabilities and implementing query testing

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

## Next Steps
1. Re-run the GitHub Actions workflow to verify that the Docker image is now built and pushed successfully.
2. Implement comprehensive error handling and logging in the API client
3. Optimize MCP server tools for interacting with CoreDataStore API
4. Optimize chunking strategy based on landmark document analysis
5. Implement parallel processing for handling multiple PDFs
6. Add resumable processing to handle interruptions
7. Develop quality assurance tools for embedding evaluation
8. Expand the query testing notebook with more advanced filtering options and visualizations
9. Create API endpoints for vector search based on the notebook's approach
10. Implement conversation memory system
11. Build chat API with context awareness

## Active Decisions and Considerations

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

## Team Collaboration
- Documentation being maintained in the memory bank
- Code will be managed through GitHub with feature branches
- CI/CD pipeline will be implemented using GitHub Actions
- Testing infrastructure is set up for continuous testing
- Jupyter notebooks used for interactive testing and demonstration of complex components
- All notebooks must be tested in the terminal and committed with outputs for review
