# NYC Landmarks Vector Database - Active Context

## Current Work Focus
We are in the initial setup phase of the NYC Landmarks Vector Database project. Our immediate focus is on:

1. Setting up the project structure and organization
2. Establishing the foundation for the PDF processing pipeline
3. Creating the configuration management system
4. Setting up connections to external services (OpenAI, Pinecone, Azure, PostgreSQL, CoreDataStore API)

## Recent Changes
- Created initial project documentation in the memory bank
- Defined the system architecture and core components
- Specified the technical requirements and constraints
- Implemented CoreDataStore API client as an alternative to direct PostgreSQL database connection
- Created a database client abstraction layer that can switch between PostgreSQL and CoreDataStore API
- Updated API modules to use the new database client abstraction

## Next Steps
1. Set up the basic project structure with appropriate directories
2. Create a configuration management module that works with Google Cloud Secret Store
3. Implement PDF text extraction from Azure Blob Storage
4. Develop text chunking and preprocessing functionality
5. Set up connection to OpenAI API for embedding generation
6. Create Pinecone index and implement vector storage
7. Develop initial API endpoints for vector search

## Active Decisions and Considerations

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
- Implemented connection to both PostgreSQL database and CoreDataStore API with the ability to switch between them
- Added a configuration toggle (COREDATASTORE_USE_API) to choose which data source to use
- Extended functionality with new methods available through the CoreDataStore API (buildings, photos, PLUTO data, etc.)
- Determine how to map PDF content to landmark records
- Plan for integration with existing frontend applications

## Current Challenges
1. Determining the optimal text chunking strategy for landmark PDFs
2. Setting up efficient batch processing for embedding generation
3. Designing a scalable conversation memory system
4. Balancing performance, cost, and accuracy in the vector search system
5. Managing potential differences between PostgreSQL database schema and CoreDataStore API response formats
6. Ensuring proper error handling for both data sources

## Team Collaboration
- Documentation being maintained in the memory bank
- Code will be managed through GitHub with feature branches
- CI/CD pipeline will be implemented using GitHub Actions
