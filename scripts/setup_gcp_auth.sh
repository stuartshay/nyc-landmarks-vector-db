#!/bin/bash

# Script to set up Google Cloud CLI authentication using service account key
# This script should be run after the devcontainer starts

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Setting up Google Cloud CLI authentication...${NC}"

# Define paths
WORKSPACE_ROOT="/workspaces/nyc-landmarks-vector-db"
SERVICE_ACCOUNT_KEY_PATH="${WORKSPACE_ROOT}/.gcp/service-account-key.json"
GCLOUD_CONFIG_DIR="${HOME}/.config/gcloud"

# Check if service account key exists
if [ ! -f "$SERVICE_ACCOUNT_KEY_PATH" ]; then
    echo -e "${RED}❌ Service account key not found at: $SERVICE_ACCOUNT_KEY_PATH${NC}"
    echo -e "${YELLOW}Please ensure the service account key is placed in the .gcp directory${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found service account key${NC}"

# Ensure gcloud config directory exists
mkdir -p "$GCLOUD_CONFIG_DIR"

# Authenticate with Google Cloud using the service account key
echo -e "${GREEN}🔐 Authenticating with Google Cloud...${NC}"
gcloud auth activate-service-account --key-file="$SERVICE_ACCOUNT_KEY_PATH"

# Extract project ID from the service account key
PROJECT_ID=$(python3 -c "
import json
with open('$SERVICE_ACCOUNT_KEY_PATH', 'r') as f:
    data = json.load(f)
    print(data['project_id'])
")

# Set the default project
echo -e "${GREEN}🏗️  Setting default project to: $PROJECT_ID${NC}"
gcloud config set project "$PROJECT_ID"

# Verify authentication
echo -e "${GREEN}🔍 Verifying authentication...${NC}"
if [[ -n $(gcloud auth list --filter=status:ACTIVE --format="value(account)") ]]; then
    echo -e "${GREEN}✅ Google Cloud CLI authentication successful!${NC}"
    echo -e "${GREEN}Active account: $(gcloud auth list --filter=status:ACTIVE --format="value(account)")${NC}"
    echo -e "${GREEN}Active project: $(gcloud config get-value project)${NC}"

    # Run comprehensive environment check
    echo -e "${GREEN}🔧 Running comprehensive environment verification...${NC}"
    python3 /workspaces/nyc-landmarks-vector-db/utils/check_dev_env.py
else
    echo -e "${RED}❌ Authentication verification failed${NC}"
    exit 1
fi

# Set up application default credentials for libraries that use them
echo -e "${GREEN}🔧 Setting up Application Default Credentials...${NC}"
export GOOGLE_APPLICATION_CREDENTIALS="$SERVICE_ACCOUNT_KEY_PATH"
echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$SERVICE_ACCOUNT_KEY_PATH\"" >> ~/.zshrc

echo -e "${GREEN}🎉 Google Cloud CLI setup complete!${NC}"
echo -e "${YELLOW}Note: GOOGLE_APPLICATION_CREDENTIALS environment variable has been set for this session and added to ~/.zshrc${NC}"
