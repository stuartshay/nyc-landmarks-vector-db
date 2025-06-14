# NYC Landmarks Vector Database - Technical Context

## Technologies Used

### Core Technologies

1. **Python**: Primary programming language for the project
1. **OpenAI API**: For generating text embeddings using their embedding models
1. **Pinecone**: Vector database for storing and searching text embeddings
1. **CoreDataStore API**: REST API for accessing NYC landmarks data
1. **coredatastore-swagger-mcp**: MCP server providing tools for CoreDataStore API,
   including:
   - GetLpcReport: Get details for a specific landmark report
   - GetLpcReports: List multiple landmark reports with filtering options
   - GetLandmarks: Retrieve buildings linked to landmarks
   - GetLandmarkStreets: Get street information for landmarks
   - GetLpcPhotoArchive/GetLpcPhotoArchiveCount: Access photo archive
   - GetPlutoRecord: Access PLUTO data
   - GetBoroughs, GetNeighborhoods, GetObjectTypes, GetArchitectureStyles: Reference
     data
   - GetLpcContent: Access additional content
1. **Azure Blob Storage**: Current storage location for landmark PDF reports
1. **Google Cloud Secret Store**: For secure credential management

### Python Libraries & Frameworks

1. **FastAPI**: For creating API endpoints
1. **PyPDF2/PDFPlumber**: For extracting text from PDFs
1. **OpenAI Python Client**: For interacting with OpenAI API
1. **Pinecone-client**: For interacting with Pinecone vector database
1. **Requests**: For making HTTP requests to CoreDataStore API
1. **Azure Blob Storage SDK**: For retrieving PDFs from Azure
1. **Google Cloud Secret Manager**: For accessing Google Cloud Secret Store
1. **Pydantic**: For data validation and settings management
1. **Pytest**: For testing
1. **Langchain (Optional)**: May be used for some components as it provides helpful
   abstractions
1. **MCP SDK**: For interacting with the Model Context Protocol server

### Development Tools

1. **GitHub**: Version control and repository hosting
1. **GitHub Actions**: CI/CD platform. Includes:
   - `.github/workflows/process_landmarks.yml`: A manually triggered workflow for
     scalable, batch-based processing of landmark data using a matrix strategy. Requires
     system dependencies like `poppler-utils` and `tesseract-ocr` in its execution
     environment.
   - (Future workflows for automated testing on PRs, deployment, etc.)
1. **SonarQube**: Code quality analysis and security scanning:
   - **Local Setup**: Using Docker Compose with PostgreSQL database
   - **Configuration**: Customized via sonar-project.properties
   - **Features**: Code coverage tracking, code smells detection, vulnerability scanning
   - **Integration**: Local analysis via sonar-scanner CLI tool
1. **Poetry/Pipenv**: Dependency management
1. **Black/Flake8/isort**: Code formatting and linting
1. **Pytest**: Testing framework
1. **Docker**: Containerization (if needed)
1. **System Dependencies (for CI/Processing):** `build-essential`, `libpq-dev`,
   `python3-dev`, `poppler-utils`, `libssl-dev`, `tesseract-ocr`, `libtesseract-dev` are
   required in the GitHub Actions environment for the processing workflow.

## Development Setup

### Local Environment Setup

1. Python 3.9+ installed
1. Poetry or Pipenv for dependency management
1. Local environment variables configuration for development
1. Access to OpenAI API (via key)
1. Access to Pinecone (via key)
1. Access to Google Cloud Secret Store (for production credentials)
1. Access to CoreDataStore API (via API key)
1. Access to Azure Blob Storage (via connection string)
1. Configured coredatastore-swagger-mcp server

### Development Workflow

1. Clone repository from GitHub
1. Install dependencies using Poetry/Pipenv
1. Configure local environment variables
1. Run tests to ensure everything is set up correctly
1. Make changes and commit to feature branches
1. Submit pull requests for review
1. CI/CD pipeline runs tests and deploys changes
1. **Notebook Debugging (Terminal):** Use
   `jupyter nbconvert --to notebook --execute <notebook_path> --output <output_path>` to
   run notebooks from the terminal. This captures output and errors, facilitating
   debugging without a full Jupyter environment. Review the generated output file for
   analysis.

## Technical Constraints

### API Limitations

1. **OpenAI Rate Limits**: OpenAI has rate limits on API calls that need to be managed
1. **OpenAI Token Limits**: Text-embedding models have maximum token limits per request
1. **Pinecone Free Tier Limits**: Limited index size and operation rate on free tier
1. **CoreDataStore API Limits**: May have rate limiting or usage restrictions
1. **Azure Blob Storage Access**: Need to manage efficient access to avoid excessive
   costs

### Performance Considerations

1. **Embedding Generation Time**: OpenAI API calls add latency to processing pipeline
1. **Vector Search Performance**: Need to optimize Pinecone queries for response time
1. **PDF Processing Overhead**: PDF extraction can be resource-intensive for large
   documents
1. **API Response Time**: Need to maintain reasonable response times for user queries
1. **CoreDataStore API Latency**: External API calls can add latency compared to direct
   database access

### Security Constraints

1. **API Key Management**: Must securely handle all API keys and credentials
1. **Data Privacy**: Need to consider any privacy implications of the data being
   processed
1. **Access Control**: Implement appropriate authentication and authorization for the
   API

### Scalability Considerations

1. **Processing Pipeline Scalability**: Need to handle large numbers of PDFs efficiently
1. **Vector Database Scaling**: Plan for growth in the vector database size
1. **Concurrent Users**: Design for multiple simultaneous users of the chat and query
   APIs

## Dependencies and Integration Points

### External Dependencies

1. **OpenAI API**: Essential for generating embeddings
1. **Pinecone Service**: Essential for vector storage and search
1. **Google Cloud Secret Store**: Essential for credential management
1. **Azure Blob Storage**: Essential for PDF access
1. **CoreDataStore API**: Essential source for NYC landmarks data
1. **MCP Server**: For providing CoreDataStore API tools

### Internal Integration Points

1. **Database Client**: Provides interface to CoreDataStore API
1. **CoreDataStore MCP Server**: Provides direct tools for API access
1. **Vector Search API**: Connects vector results with landmark data
1. **Chat API**: Provides conversational interface to vector database
1. **Frontend Applications**: Will consume the vector search and chat APIs

## Monitoring and Maintenance

### Monitoring

1. **API Health Checks**: Regular monitoring of API endpoints
1. **Error Logging**: Comprehensive error logging for troubleshooting
1. **Performance Metrics**: Tracking of response times and system load
1. **Usage Statistics**: Monitoring of API usage patterns

### Maintenance Tasks

1. **Model Updates**: Periodically check for updated embedding models
1. **Database Backups**: Regular backups of the vector database
1. **Dependency Updates**: Keeping all dependencies up to date
1. **Security Audits**: Regular security reviews of the system
