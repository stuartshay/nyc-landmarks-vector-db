# NYC Landmarks Vector Database - Technical Context

## Technologies Used

### Core Technologies
1. **Python**: Primary programming language for the project
2. **OpenAI API**: For generating text embeddings using their embedding models
3. **Pinecone**: Vector database for storing and searching text embeddings
4. **PostgreSQL**: Existing database containing NYC landmarks structured data
5. **Azure Blob Storage**: Current storage location for landmark PDF reports
6. **Google Cloud Secret Store**: For secure credential management

### Python Libraries & Frameworks
1. **FastAPI**: For creating API endpoints
2. **PyPDF2/PDFPlumber**: For extracting text from PDFs
3. **OpenAI Python Client**: For interacting with OpenAI API
4. **Pinecone-client**: For interacting with Pinecone vector database
5. **Psycopg2/SQLAlchemy**: For PostgreSQL database interactions
6. **Azure Blob Storage SDK**: For retrieving PDFs from Azure
7. **Google Cloud Secret Manager**: For accessing Google Cloud Secret Store
8. **Pydantic**: For data validation and settings management
9. **Pytest**: For testing
10. **Langchain (Optional)**: May be used for some components as it provides helpful abstractions

### Development Tools
1. **GitHub**: Version control and repository hosting
2. **GitHub Actions**: CI/CD platform
3. **Poetry/Pipenv**: Dependency management
4. **Black/Flake8/isort**: Code formatting and linting
5. **Pytest**: Testing framework
6. **Docker**: Containerization (if needed)

## Development Setup

### Local Environment Setup
1. Python 3.9+ installed
2. Poetry or Pipenv for dependency management
3. Local environment variables configuration for development
4. Access to OpenAI API (via key)
5. Access to Pinecone (via key)
6. Access to Google Cloud Secret Store (for production credentials)
7. Access to PostgreSQL database (via connection string)
8. Access to Azure Blob Storage (via connection string)

### Development Workflow
1. Clone repository from GitHub
2. Install dependencies using Poetry/Pipenv
3. Configure local environment variables
4. Run tests to ensure everything is set up correctly
5. Make changes and commit to feature branches
6. Submit pull requests for review
7. CI/CD pipeline runs tests and deploys changes

## Technical Constraints

### API Limitations
1. **OpenAI Rate Limits**: OpenAI has rate limits on API calls that need to be managed
2. **OpenAI Token Limits**: Text-embedding models have maximum token limits per request
3. **Pinecone Free Tier Limits**: Limited index size and operation rate on free tier
4. **Azure Blob Storage Access**: Need to manage efficient access to avoid excessive costs

### Performance Considerations
1. **Embedding Generation Time**: OpenAI API calls add latency to processing pipeline
2. **Vector Search Performance**: Need to optimize Pinecone queries for response time
3. **PDF Processing Overhead**: PDF extraction can be resource-intensive for large documents
4. **API Response Time**: Need to maintain reasonable response times for user queries

### Security Constraints
1. **API Key Management**: Must securely handle all API keys and credentials
2. **Data Privacy**: Need to consider any privacy implications of the data being processed
3. **Access Control**: Implement appropriate authentication and authorization for the API

### Scalability Considerations
1. **Processing Pipeline Scalability**: Need to handle large numbers of PDFs efficiently
2. **Vector Database Scaling**: Plan for growth in the vector database size
3. **Concurrent Users**: Design for multiple simultaneous users of the chat and query APIs

## Dependencies and Integration Points

### External Dependencies
1. **OpenAI API**: Essential for generating embeddings
2. **Pinecone Service**: Essential for vector storage and search
3. **Google Cloud Secret Store**: Essential for credential management
4. **Azure Blob Storage**: Essential for PDF access
5. **PostgreSQL Database**: Essential for landmark data

### Internal Integration Points
1. **Existing Postgres Database**: Need to query landmark data
2. **Existing API**: May need to integrate with other NYC landmark services
3. **Frontend Applications**: Will consume the new vector search and chat APIs

## Monitoring and Maintenance

### Monitoring
1. **API Health Checks**: Regular monitoring of API endpoints
2. **Error Logging**: Comprehensive error logging for troubleshooting
3. **Performance Metrics**: Tracking of response times and system load
4. **Usage Statistics**: Monitoring of API usage patterns

### Maintenance Tasks
1. **Model Updates**: Periodically check for updated embedding models
2. **Database Backups**: Regular backups of the vector database
3. **Dependency Updates**: Keeping all dependencies up to date
4. **Security Audits**: Regular security reviews of the system
