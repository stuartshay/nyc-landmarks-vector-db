# Environment Setup Guide

This guide helps you set up the development environment for the NYC Landmarks Vector Database project.

## Quick Start

1. **Copy the environment template:**

   ```bash
   cp .env.sample .env
   ```

1. **Update the environment variables in `.env`:**

   - `OPENAI_API_KEY`: Your OpenAI API key (required for embeddings)
   - `PINECONE_API_KEY`: Your Pinecone API key (required for vector storage)
   - `PINECONE_ENVIRONMENT`: Your Pinecone environment
   - `GOOGLE_CLOUD_PROJECT`: Your GCP project ID (optional)

1. **Start the devcontainer:**

   - Open the project in VS Code
   - Click "Reopen in Container" when prompted
   - Or use Command Palette: "Dev Containers: Rebuild and Reopen in Container"

## Environment Variables

### Required for Core Functionality

- `OPENAI_API_KEY`: OpenAI API key for generating embeddings
- `PINECONE_API_KEY`: Pinecone API key for vector database operations
- `PINECONE_ENVIRONMENT`: Pinecone environment (e.g., "us-west1-gcp")

### Optional for Enhanced Features

- `GOOGLE_CLOUD_PROJECT`: GCP project ID for Cloud Run deployment
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to GCP service account key
- `WIKIPEDIA_USER_AGENT`: User agent for Wikipedia API requests

### Development Configuration

- `ENVIRONMENT`: Set to "development" for local development
- `DEBUG`: Set to "true" for verbose logging
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_FORMAT`: Log format ("json" or "text")

## GCP Authentication (Optional)

If you plan to use Google Cloud features:

1. **Create a service account key:**

   - Go to GCP Console > IAM & Admin > Service Accounts
   - Create or select a service account
   - Create a JSON key and download it

1. **Place the key file:**

   ```bash
   mkdir -p .gcp
   mv path/to/your/key.json .gcp/service-account-key.json
   ```

1. **Run the GCP setup task:**

   - Use VS Code task: "Setup GCP Authentication"
   - Or run: `./scripts/setup_gcp_auth.sh`

## Troubleshooting

### Devcontainer Won't Start

- Ensure `.env` file exists (copy from `.env.sample`)
- Check Docker is running
- Try "Dev Containers: Rebuild Container"

### Missing API Keys

- The application will work with mock data if API keys are not provided
- Set `DEBUG=true` in `.env` to see detailed error messages

### Permission Issues

- Ensure your user has Docker permissions
- On Linux: `sudo usermod -aG docker $USER` (requires logout/login)

## VS Code Tasks

The project includes several pre-configured tasks:

- **Check Development Environment**: Verify all tools are installed
- **Run All Tests**: Execute the full test suite
- **Setup GCP Authentication**: Configure Google Cloud authentication
- **Compare Files/Vectors**: Use the diff tools for debugging

Access these via Command Palette > "Tasks: Run Task"
