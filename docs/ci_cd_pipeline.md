# NYC Landmarks Vector Database CI/CD Pipeline

This document describes the Continuous Integration/Continuous Deployment (CI/CD) pipeline for the NYC Landmarks Vector Database project.

## Overview

The CI/CD pipeline automates the process of:

1. Fetching landmark data from the CoreDataStore API
2. Downloading PDF reports for landmarks
3. Processing PDFs to extract text (placeholder)
4. Generating embeddings from text (placeholder)
5. Storing embeddings in a vector database (placeholder)

## Components

### 1. Pipeline Script

The main pipeline script (`scripts/process_landmarks.py`) orchestrates the data processing workflow:

- Connects to the CoreDataStore API
- Retrieves landmark information
- Downloads associated PDF documents
- Creates structured output for further processing
- Includes placeholder functions for text extraction, embedding generation, and vector database integration

### 2. GitHub Actions Workflow

The GitHub Actions workflow (`.github/workflows/update-vector-db.yml`) automates the execution of the pipeline:

- Runs on a schedule (weekly on Sundays)
- Can be triggered manually with custom parameters
- Sets up the necessary environment and dependencies
- Executes the pipeline script
- Uploads logs and statistics as artifacts
- Creates a summary report

## Usage

### Running Locally

To run the pipeline locally:

```bash
# Basic usage - fetch 1 page of landmarks (typically 10 landmarks)
python scripts/process_landmarks.py --pages 1

# Download PDFs for 3 landmarks
python scripts/process_landmarks.py --pages 1 --download --limit 3

# Process all landmarks from 5 pages, download all PDFs
python scripts/process_landmarks.py --pages 5 --download
```

### Manual GitHub Actions Trigger

1. Go to the Actions tab in the GitHub repository
2. Select the "Update NYC Landmarks Vector Database" workflow
3. Click "Run workflow"
4. Enter the desired parameters:
   - Number of pages to fetch
   - Download limit (0 for all)
5. Click "Run workflow"

## Configuration

The pipeline requires the following environment variables or GitHub secrets:

- `COREDATASTORE_API_KEY`: API key for the CoreDataStore API (required)
- `OPENAI_API_KEY`: API key for OpenAI (for future embedding generation)
- `PINECONE_API_KEY`: API key for Pinecone vector database

## Output

The pipeline produces the following outputs:

- `data/landmarks.json`: Raw landmark data from the API
- `data/pdfs/`: Directory containing downloaded PDF files
- `data/pipeline_stats.json`: Statistics about the pipeline run
- `pipeline.log`: Detailed log of the pipeline execution

## Extending the Pipeline

### 1. Implementing Text Extraction

Modify the `extract_text` method in the `LandmarkPipeline` class to:

- Use a PDF extraction library like PyPDF2 or PDFPlumber
- Process each PDF and extract meaningful text
- Save extracted text to `data/text/` directory

### 2. Implementing Embedding Generation

Modify the `generate_embeddings` method to:

- Connect to OpenAI API
- Generate embeddings for each text chunk
- Handle rate limiting and error conditions
- Structure embeddings with appropriate metadata

### 3. Implementing Vector Database Storage

Modify the `store_in_vector_db` method to:

- Connect to Pinecone or another vector database
- Create appropriate index if not exists
- Store vectors with metadata
- Implement upsert logic for incremental updates

## Monitoring and Maintenance

- Check GitHub Actions logs for pipeline run details
- Review pipeline_stats.json for success/failure metrics
- Monitor the vector database size and performance
- Update API keys and credentials as needed

## Troubleshooting

### Common Issues

1. **API Authentication Failures**: Check that the COREDATASTORE_API_KEY is correctly set.
2. **PDF Download Errors**: Some PDFs may be unavailable or require authentication.
3. **Rate Limiting**: Add delays between API calls if encountering rate limits.
4. **Memory Issues**: For large-scale processing, implement batching in the embedding generation step.

### Error Handling

The pipeline includes error handling that:

- Logs errors to the pipeline.log file
- Continues processing on non-critical errors
- Captures statistics on failures
- Creates detailed error reports in the pipeline_stats.json file
