# Technology Context

This document outlines the technologies used in the NYC Landmarks Vector DB project, the development setup, technical constraints, and dependencies.

## Technologies Used

### Core Technologies

| Category         | Technology            | Purpose                                    |
| ---------------- | --------------------- | ------------------------------------------ |
| Language         | Python 3.9+           | Primary programming language               |
| Vector Database  | Pinecone              | Storage and retrieval of vector embeddings |
| Embedding Models | OpenAI/Azure OpenAI   | Generate text embeddings                   |
| Cloud Platform   | Google Cloud Platform | Cloud infrastructure                       |
| Containerization | Docker                | Application packaging and deployment       |

### Development Tools

| Tool            | Purpose                                             |
| --------------- | --------------------------------------------------- |
| Poetry          | Python dependency management                        |
| Pytest          | Testing framework                                   |
| Pre-commit      | Git hooks for code quality                          |
| Jupyter         | Interactive notebook environment                    |
| mypy            | Static type checking                                |
| Black           | Code formatting                                     |
| Flake8          | Code linting                                        |
| GitHub Actions  | CI/CD pipeline                                      |
| Terraform       | Infrastructure as Code                              |
| Terraform Cloud | Remote state management and collaborative workflows |

### Libraries and Frameworks

| Library        | Purpose                                 |
| -------------- | --------------------------------------- |
| FastAPI        | API framework                           |
| Pydantic       | Data validation and settings management |
| Pandas         | Data manipulation and analysis          |
| numpy          | Numerical operations                    |
| PyPDF2         | PDF parsing                             |
| tiktoken       | Token counting for text chunking        |
| loguru         | Structured logging                      |
| httpx          | HTTP client for API requests            |
| pytest-asyncio | Testing async code                      |

## Development Setup

### Local Environment

1. **Python Environment**:

   - Python 3.9+
   - Poetry for dependency management
   - Virtual environment for isolation

1. **Configuration**:

   - Environment variables for sensitive settings
   - Local config files for development settings
   - Secrets managed outside of version control

1. **Docker**:

   - Dockerfile for containerization
   - docker-compose for local service orchestration
   - Development container for VSCode

### CI/CD Pipeline

1. **GitHub Actions Workflow**:

   - Code validation (linting, formatting)
   - Unit and integration testing
   - Security scanning
   - Container building
   - Deployment to cloud environments

1. **Terraform Workflow**:

   - Infrastructure validation
   - Plan and apply stages
   - Remote state management through Terraform Cloud
   - Workspace-based environment separation

### Cloud Environment

1. **Google Cloud Platform Resources**:

   - Cloud Run for serverless API hosting
   - Cloud Storage for data storage
   - Cloud Logging for centralized logging
   - Cloud Monitoring for observability
   - Cloud Scheduler for periodic tasks

1. **Pinecone**:

   - Managed vector database service
   - Dedicated indexes for production and development
   - Namespace-based organization within indexes

## Technical Constraints

### Performance Considerations

1. **Vector Database Performance**:

   - Query latency target: \<500ms
   - Maximum dimensions: 1536 (OpenAI Ada-002 model)
   - Optimal top-k value: 5-20 for most queries

1. **API Performance**:

   - Request timeout: 30 seconds
   - Rate limiting: 100 requests per minute
   - Maximum payload size: 5MB

### Security Constraints

1. **Authentication**:

   - API key required for production endpoints
   - OAuth 2.0 for administrative actions
   - Service account authentication for GCP resources

1. **Data Protection**:

   - No PII in vector metadata
   - Encryption in transit (TLS)
   - Encryption at rest (GCP default)

### Scalability Limits

1. **Vector Database**:

   - Maximum vectors: 100,000 in current plan
   - Maximum dimensions: 1536
   - Maximum metadata size: 40KB per vector

1. **API**:

   - Serverless scaling based on demand
   - Cold start considerations for infrequent requests
   - Resource allocation adjusted based on load patterns

## Dependencies and Integration Points

### External APIs

1. **OpenAI API**:

   - Used for generating embeddings
   - Rate limited based on plan
   - Fallback to Azure OpenAI if primary API is unavailable

1. **Wikipedia API**:

   - Used for fetching landmark information
   - Subject to rate limiting and fair use policies
   - Response caching to reduce duplicate requests

1. **NYC Open Data APIs**:

   - Additional landmark data sources
   - Varying availability and rate limits
   - Batch processing approach for large datasets

### Infrastructure Dependencies

1. **Google Cloud Platform**:

   - Project-level quota limits
   - Service account permissions
   - Regional resource availability

1. **Pinecone**:

   - Service availability SLA
   - Regional deployment options
   - Plan-based limitations on index size and query rate

## Infrastructure Management

### Terraform Configuration

Terraform is used to manage all infrastructure as code, with resources defined in the `infrastructure/` directory:

```
infrastructure/
├── main.tf                  # Main Terraform configuration
├── variables.tf             # Input variables
├── outputs.tf               # Output values
├── terraform.tfvars         # Variable values
└── terraform/               # Additional Terraform configurations
    ├── dashboard.json.tpl   # Monitoring dashboard template
    └── ...
```

Key resources managed through Terraform:

- Logging metrics and buckets
- Monitoring dashboards
- Alert policies
- Scheduled jobs
- Uptime checks

### Terraform Cloud Integration

Terraform Cloud provides remote state management and collaborative workflows:

1. **Organization and Workspace Structure**:

   - Organization: `nyc-landmarks`
   - Workspace: `nyc-landmarks-vector-db`
   - Working directory: `infrastructure/terraform`

1. **State Management**:

   - Remote state stored in Terraform Cloud
   - State locking to prevent concurrent operations
   - State versioning for tracking changes

1. **Authentication and Authorization**:

   - API tokens for CLI authentication
   - Environment variables for sensitive credentials
   - VCS integration for automatic planning on code changes

1. **Operational Workflow**:

   - Planning in Terraform Cloud environment
   - Apply operations with approval gates
   - Run history and logging for auditability

## Development Workflow

### Code Organization

Code is organized by feature and responsibility:

```
nyc_landmarks/
├── api/           # API endpoints and routing
├── config/        # Configuration management
├── db/            # Database access
├── embeddings/    # Embedding generation
├── landmarks/     # Landmark data processing
├── models/        # Data models and schemas
├── pdf/           # PDF processing
├── utils/         # Utility functions
├── vectordb/      # Vector database operations
└── wikipedia/     # Wikipedia integration
```

### Testing Strategy

1. **Unit Tests**:

   - Test individual components in isolation
   - Mock external dependencies
   - Fast execution for quick feedback

1. **Integration Tests**:

   - Test interactions between components
   - Use test fixtures for consistent setup
   - Run less frequently than unit tests

1. **Functional Tests**:

   - Test complete features end-to-end
   - Run against test environment
   - Cover critical user flows

1. **Load Tests**:

   - Test performance under load
   - Identify bottlenecks
   - Verify scaling behavior

### Documentation

Documentation is maintained in several locations:

1. **Code Documentation**:

   - Docstrings for all functions, classes, and modules
   - Type hints for function signatures
   - README files in major directories

1. **Project Documentation**:

   - Architecture diagrams
   - API specifications
   - Setup and deployment guides
   - Contributing guidelines

1. **Operational Documentation**:

   - Runbooks for common operations
   - Troubleshooting guides
   - Monitoring dashboards
   - Alert response procedures
