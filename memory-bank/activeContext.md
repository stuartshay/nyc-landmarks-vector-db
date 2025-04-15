# NYC Landmarks Vector Database - Active Context

## Current Work Focus
We are in the initial setup phase of the NYC Landmarks Vector Database project. Our immediate focus is on:

1. Setting up the project structure and organization
2. Establishing the foundation for the PDF processing pipeline
3. Creating the configuration management system
4. Setting up connections to external services (OpenAI, Pinecone, Azure, CoreDataStore API)
5. Implementing comprehensive testing for scripts and API integrations
6. Integrating Pydantic for data validation throughout the system

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
- **Refactored the CI/CD workflow to build a Docker image with all dependencies in a single job, push it to GitHub Container Registry, and run all parallel processing jobs using this pre-built image. This ensures all jobs share the same environment and eliminates redundant setup steps.**
- **Created a Dockerfile at the repository root to enable the CI/CD workflow to build and push the Docker image. This resolves the previous job failure due to a missing Dockerfile.**

## Next Steps
1. Re-run the GitHub Actions workflow to verify that the Docker image is now built and pushed successfully.
2. Implement comprehensive error handling and logging in the API client
3. Optimize MCP server tools for interacting with CoreDataStore API
4. Optimize chunking strategy based on landmark document analysis
5. Implement parallel processing for handling multiple PDFs
6. Add resumable processing to handle interruptions
7. Develop quality assurance tools for embedding evaluation
8. Develop vector search functionality
9. Create API endpoints for vector search
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

### API Design
- Need to define API endpoints for vector search and chat functionality
- Consider authentication and rate limiting for the API
- Determine how to handle conversation context in the chat API

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

## Team Collaboration
- Documentation being maintained in the memory bank
- Code will be managed through GitHub with feature branches
- CI/CD pipeline will be implemented using GitHub Actions
- Testing infrastructure is set up for continuous testing
