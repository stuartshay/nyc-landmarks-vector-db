# NYC Landmarks Vector DB - Google Cloud Run Deployment

This document provides instructions for deploying the NYC Landmarks Vector Database to Google Cloud Run using the GitHub Actions workflow.

## Prerequisites

- Google Cloud Platform account
- Project with billing enabled
- Appropriate permissions to create Google Cloud resources

## Setup Process

### 1. Create a Google Cloud Project

If you don't already have a project:

```bash
gcloud projects create PROJECT_ID --name="NYC Landmarks Vector DB"
gcloud config set project PROJECT_ID
```

### 2. Enable Required APIs

```bash
gcloud services enable \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  iam.googleapis.com
```

### 3. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create github-actions-sa \
  --display-name="GitHub Actions Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:github-actions-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:github-actions-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:github-actions-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### 4. Generate Service Account Key

```bash
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions-sa@PROJECT_ID.iam.gserviceaccount.com
```

### 5. Set Up GitHub Secrets

Add the following secrets to your GitHub repository:

- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `GCP_SA_KEY`: The contents of the `key.json` file (service account key)
- `OPENAI_API_KEY`: Your OpenAI API key
- `PINECONE_API_KEY`: Your Pinecone API key
- `PINECONE_ENVIRONMENT`: Your Pinecone environment (e.g., "us-east-1-aws")
- `PINECONE_INDEX_NAME`: The name of your Pinecone index (e.g., "nyc-landmarks")
- `COREDATASTORE_API_KEY`: Your CoreDataStore API key

## Deployment Workflow

The GitHub Actions workflow `.github/workflows/deploy-gcp.yml` will:

1. **Build** a Docker image based on the project's Dockerfile
2. **Publish** the image to Google Artifact Registry
3. **Deploy** the service to Google Cloud Run

The workflow runs:
- Automatically when code is pushed to the `main` or `master` branch
- Manually using the "Run workflow" button in the GitHub Actions tab

## Service Configuration

The Cloud Run service is configured with:

- **Memory**: 2Gi (2 GB)
- **CPU**: 1 CPU
- **Concurrency**: 80 concurrent requests
- **Timeout**: 300 seconds
- **Instances**: Min 1, Max 10 (auto-scaling)
- **Access**: Public (unauthenticated)

## Environment Variables

The service uses the following environment variables:

- `OPENAI_API_KEY`: For generating embeddings and chat completions
- `PINECONE_API_KEY`: For vector database operations
- `PINECONE_ENVIRONMENT`: Specifies Pinecone environment
- `PINECONE_INDEX_NAME`: Specifies which Pinecone index to use
- `COREDATASTORE_API_KEY`: For accessing the CoreDataStore API
- `CONVERSATION_TTL`: Time-to-live for conversation memory (default: 86400 seconds)

## Monitoring and Debugging

After deployment:

1. Access the deployed service URL (shown in GitHub Actions output)
2. Monitor performance in the Google Cloud Console
3. View logs using:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=nyc-landmarks-vector-db"
   ```

## Customizing the Deployment

To modify the deployment configuration:

1. Edit the `.github/workflows/deploy-gcp.yml` file
2. Adjust resource allocations or environment variables as needed
3. Commit and push changes to trigger a new deployment

## Troubleshooting

If the deployment fails:

1. Check GitHub Actions logs for error messages
2. Verify all required secrets are set correctly
3. Ensure the service account has proper permissions
4. Check Google Cloud Run logs for runtime errors
