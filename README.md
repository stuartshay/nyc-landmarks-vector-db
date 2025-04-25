# NYC Landmarks Vector Database

[![Python CI](https://github.com/stuartshay/nyc-landmarks-vector-db/actions/workflows/python-ci.yml/badge.svg)](https://github.com/stuartshay/nyc-landmarks-vector-db/actions/workflows/python-ci.yml) [![Dependency Review](https://github.com/stuartshay/nyc-landmarks-vector-db/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/stuartshay/nyc-landmarks-vector-db/actions/workflows/dependency-review.yml)

[![Process NYC Landmarks Data](https://github.com/stuartshay/nyc-landmarks-vector-db/actions/workflows/process_landmarks.yml/badge.svg)](https://github.com/stuartshay/nyc-landmarks-vector-db/actions/workflows/process_landmarks.yml)

[![API Deploy to Google Cloud Run](https://github.com/stuartshay/nyc-landmarks-vector-db/actions/workflows/deploy-gcp.yml/badge.svg)](https://github.com/stuartshay/nyc-landmarks-vector-db/actions/workflows/deploy-gcp.yml)


```
Deployed Application
https://vector-db.coredatastore.com/docs
```

A vector database system for NYC landmarks that extracts metadata and  text from API and PDF reports, converts it to vector embeddings, and enables semantic search and chatbot functionality.

## Project Overview

This project aims to make information about New York City landmarks more accessible and searchable by:

1. Extracting text from PDF reports stored in Azure Blob Storage
2. Processing and chunking the text for optimal embedding
3. Converting text into vector embeddings using OpenAI embedding models
4. Storing embeddings in a Pinecone vector database with comprehensive metadata
5. Providing API endpoints for semantic search and chatbot functionality with conversation memory
6. Enabling filtering by landmark ID and other metadata
7. Integrating exclusively with the CoreDataStore API as the data source

The system makes previously inaccessible information in PDF reports easily searchable through semantic understanding, allowing users to find relevant information about NYC landmarks using natural language queries.

## System Architecture

```mermaid
flowchart TD
    subgraph "Data Sources"
        A[CoreDataStore API\nNYC Landmarks Data]
        B[Azure Blob Storage\nLandmark PDFs]
    end

    subgraph "Database Layer"
        DB[Database Client]
    end

    subgraph "Processing Pipeline"
        C[PDF Text Extractor]
        D[Text Chunker]
        E[OpenAI Embedding Generator]
    end

    subgraph "Storage"
        F[Pinecone Vector Database]
        G[Conversation Memory Store]
    end

    subgraph "API Layer"
        H[Query API]
        I[Chat API]
    end

    A --> DB
    DB --> C
    B --> C
    C --> D
    D --> E
    E --> F
    F --> H
    F --> I
    G --> I
    DB --> H
    DB --> I

    H --> J[Client Applications]
    I --> J
```

## Features

- **PDF Processing Pipeline**: Extract text from PDF reports of NYC landmarks using PyPDF2/PDFPlumber
- **Intelligent Text Chunking**: Process text into optimized chunks (500-1000 tokens) with 10-20% overlap for context preservation
- **High-Quality Embeddings**: Generate embeddings using OpenAI's text-embedding-3-small model (1536 dimensions)
- **Rich Metadata Storage**: Store embeddings in Pinecone with comprehensive metadata including landmark ID, chunk position, source PDF details, and more
- **Semantic Search API**: Provide vector search API for natural language queries with relevant results
- **Conversational AI**: Enable chatbot functionality with conversation memory for contextual follow-up questions
- **Flexible Filtering**: Filter results by landmark ID, borough, neighborhood, and other metadata
- **CoreDataStore Integration**: Access comprehensive NYC landmarks data exclusively through the CoreDataStore API
- **MCP Server Tools**: Leverage coredatastore-swagger-mcp server for direct API interactions with extended functionality
- **Secure Credential Management**: Manage all API keys and credentials through Google Cloud Secret Store

## Tech Stack

- **Python 3.11+**: Primary programming language
- **OpenAI API**: For generating text embeddings using text-embedding-3-small/large models
- **Pinecone**: Vector database for storing and searching embeddings with metadata
- **CoreDataStore API**: Exclusive REST API for accessing NYC landmarks information
- **coredatastore-swagger-mcp**: MCP server providing tools for CoreDataStore API interaction
- **Azure Blob Storage**: Storage location for landmark PDF reports
- **Google Cloud Secret Store**: For secure credential management across environments
- **FastAPI**: For creating API endpoints with automatic documentation
- **PyPDF2/PDFPlumber**: For extracting text from PDFs
- **Pydantic**: For data validation and settings management
- **Requests**: For making HTTP requests to CoreDataStore API
- **Pytest**: For testing framework
- **GitHub Actions**: For CI/CD pipeline

## Getting Started

### Prerequisites

- Python 3.11+
- Access to OpenAI API (API key)
- Access to Pinecone (API key)
- Access to Google Cloud Secret Store
- Access to Azure Blob Storage
- Access to CoreDataStore API (API key)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/nyc-landmarks-vector-db.git
cd nyc-landmarks-vector-db

# Option 1: Using venv (if you have Python 3.11 installed)
python3.11 -m venv venv

# Activate the virtual environment
# On Unix or MacOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Option 2: Using Conda (recommended if Python 3.11 is not installed)
# Create a conda environment
conda create -n nyc-landmarks python=3.11

# Activate the conda environment
conda activate nyc-landmarks

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your preferred editor

# Run the application
python -m nyc_landmarks.main
```

## Development Setup

This project offers two ways to set up your development environment: using VS Code Dev Containers (recommended) or a traditional local setup.

### Option 1: Using VS Code Dev Containers (Recommended)

This project includes a fully configured development container that provides a consistent, isolated environment with all the necessary tools and dependencies pre-installed.

#### Prerequisites
- [VS Code](https://code.visualstudio.com/)
- [Docker](https://www.docker.com/products/docker-desktop)
- [VS Code Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

#### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/nyc-landmarks-vector-db.git
   cd nyc-landmarks-vector-db
   ```

2. Open the project in VS Code:
   ```bash
   code .
   ```

3. When prompted to "Reopen in Container", click "Reopen in Container". Alternatively, you can:
   - Press F1 and select "Remote-Containers: Reopen in Container"
   - Click the green button in the bottom-left corner and select "Reopen in Container"

4. VS Code will build the container and configure the environment (this may take a few minutes the first time).

5. Once inside the container, you're ready to work on the project with all tools and dependencies pre-configured.

6. Copy the sample environment file and edit it:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

7. Set up the MCP server for CoreDataStore API interactions:
   ```bash
   # The coredatastore-swagger-mcp server should be configured
   # as specified in techContext.md
   ```

8. Run the application:
   ```bash
   python -m nyc_landmarks.main
   ```

#### Google Cloud CLI Setup in Dev Container

The development container comes with the Google Cloud CLI pre-installed. To use it for accessing secrets:

1. **Authenticate with Google Cloud:**
   ```bash
   gcloud auth login
   ```
   This will open a browser window where you can log in with your Google account.

2. **Set your Google Cloud project:**
   ```bash
   gcloud config set project your-project-id
   ```
   Replace `your-project-id` with your actual Google Cloud project ID.

3. **Set up Application Default Credentials:**
   ```bash
   gcloud auth application-default login
   ```
   This will set up credentials for your local development environment.

4. **Access Google Cloud Secret Manager:**
   ```bash
   # List available secrets
   gcloud secrets list

   # Access a specific secret
   gcloud secrets versions access latest --secret="your-secret-name"
   ```

5. **Configure service account (if needed):**
   ```bash
   gcloud iam service-accounts keys create key-file.json --iam-account=your-service-account@your-project.iam.gserviceaccount.com
   export GOOGLE_APPLICATION_CREDENTIALS="$PWD/key-file.json"
   ```

The Google Cloud CLI provides many more capabilities. For more details, run `gcloud --help` or visit the [Google Cloud CLI documentation](https://cloud.google.com/sdk/gcloud/reference).

### Option 2: Traditional Local Setup

If you prefer to set up the development environment locally without containers:

#### Prerequisites
- Python 3.11+
- Git

#### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/nyc-landmarks-vector-db.git
   cd nyc-landmarks-vector-db
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3.11 -m venv venv

   # Activate the virtual environment
   # On Unix or MacOS:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   # Install regular dependencies
   pip install -r requirements.txt

   # Install development dependencies
   pip install -e ".[dev]"
   ```

4. **Set up pre-commit hooks:**
   ```bash
   pip install pre-commit
   pre-commit install
   pre-commit run --all-files  # Optional
   ```

5. **Configure environment variables:**
   ```bash
   cp .env.sample .env
   # Edit .env with your credentials
   ```

6. **Configure MCP server for CoreDataStore API:**
   ```bash
   # Set up the coredatastore-swagger-mcp server
   # as detailed in techContext.md
   ```

7. **Run the application:**
   ```bash
   python -m nyc_landmarks.main
   ```

## Code Quality Standards

This project enforces:
- Static type checking with mypy (strict mode)
- Code formatting with Black (88 character line length)
- Import sorting with isort
- Linting with flake8 and pylint
- Minimum 80% test coverage
- Security scanning with bandit

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed information on our development workflow and code standards.

## VS Code Integration

This project includes Visual Studio Code configuration for an optimal development experience:

**Features enabled:**
- Integrated linting and type checking
- Auto-formatting on save
- Debug configurations for various project components
- Test runner integration
- Consistency via EditorConfig

To take full advantage of these features, install the recommended extensions when prompted by VS Code.

## Project Structure

```
nyc-landmarks-vector-db/
├── nyc_landmarks/                # Main package
│   ├── api/                      # API endpoints for vector search and chat
│   │   ├── __init__.py
│   │   ├── chat.py               # Chat API with conversation memory
│   │   └── query.py              # Vector search API endpoints
│   ├── chat/                     # Chat functionality
│   │   ├── __init__.py
│   │   └── conversation.py       # Conversation memory implementation
│   ├── config/                   # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py           # Settings with Google Cloud Secret integration
│   ├── db/                       # Database interactions
│   │   ├── __init__.py
│   │   ├── db_client.py          # Database client interface
│   │   ├── postgres.py           # Low-level database operations
│   │   └── coredatastore_api.py  # CoreDataStore API client implementation
│   ├── embeddings/               # Embedding generation and management
│   │   ├── __init__.py
│   │   └── generator.py          # OpenAI embedding generator
│   ├── pdf/                      # PDF processing modules
│   │   ├── __init__.py
│   │   ├── extractor.py          # PDF text extraction
│   │   └── text_chunker.py       # Text chunking with overlap
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   └── logger.py             # Logging configuration
│   ├── vectordb/                 # Vector database interactions
│   │   ├── __init__.py
│   │   ├── pinecone_db.py        # Pinecone interactions
│   │   └── enhanced_metadata.py  # Enhanced metadata handling
│   ├── __init__.py
│   ├── main.py                   # Application entry point
│   └── py.typed                  # Marker file for type checking
├── tests/                        # Test suite
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
│   ├── fetch_landmark_reports.py # Fetch reports from CoreDataStore API
│   ├── process_landmark_pdfs.py  # Process PDFs into embeddings
│   ├── process_landmarks.py      # Process landmark data
│   └── demo.py                   # Demo script
├── sample_pdfs/                  # Sample PDFs for testing
├── .github/                      # GitHub Actions workflows
├── memory-bank/                  # Project documentation
├── requirements.txt              # Dependencies
├── setup.py                      # Package setup
└── README.md                     # This file
```

## Configuration

The project uses the CoreDataStore API as the exclusive data source for NYC landmarks information. The API provides comprehensive access to landmark data, buildings, photos, PLUTO data, and more. The system is designed with a secure configuration approach:

### Production Environment
- All credentials are stored in Google Cloud Secret Store
- The application retrieves secrets at runtime
- No credentials are stored in code or environment variables

### Development Environment
- Credentials can be stored in a local `.env` file
- The application will fall back to environment variables if Google Cloud is not configured
- Sample configurations are provided in `.env.example`

### Key Configuration Parameters
- `COREDATASTORE_API_KEY`: Your API key for accessing the CoreDataStore API
- `OPENAI_API_KEY`: Your API key for OpenAI's embedding models
- `PINECONE_API_KEY`: Your API key for the Pinecone vector database
- `PINECONE_ENVIRONMENT`: The Pinecone environment to use
- `PINECONE_INDEX_NAME`: The name of your Pinecone index
- `GOOGLE_CLOUD_PROJECT`: Google Cloud project ID for Secret Store
- `TEXT_CHUNK_SIZE`: Size of text chunks for embedding (tokens)
- `TEXT_CHUNK_OVERLAP`: Overlap between chunks (percentage)
- `EMBEDDING_MODEL`: OpenAI embedding model to use
- `EMBEDDING_DIMENSION`: Dimension of the embeddings

## Documentation

Detailed documentation is available in the `memory-bank/` directory:

- `projectbrief.md`: Project overview and requirements
- `productContext.md`: Product context and user experience goals
- `systemPatterns.md`: System architecture and design patterns
- `techContext.md`: Technical context and constraints
- `activeContext.md`: Current work focus and considerations
- `progress.md`: Project progress and status


## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NYC Landmarks Preservation Commission for the data
- CoreDataStore for the API access
- OpenAI for the embedding models
- Pinecone for the vector database
