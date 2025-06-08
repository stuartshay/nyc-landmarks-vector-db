#!/bin/bash

# Test script to simulate devcontainer startup process
# This validates that the GCP setup will work correctly when a new container is created

set -e

echo "🧪 Testing devcontainer GCP setup simulation..."
echo "================================================"

# Save current authentication state
echo "💾 Saving current authentication state..."
CURRENT_ACCOUNT=$(gcloud auth list --format="value(account)" --filter="status:ACTIVE" 2>/dev/null || echo "none")
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "none")

# Clear authentication to simulate fresh container
echo "🧹 Clearing authentication to simulate fresh container..."
gcloud auth revoke --all 2>/dev/null || true
gcloud config unset project 2>/dev/null || true

# Test the setup script
echo "🔧 Running setup script..."
if /workspaces/nyc-landmarks-vector-db/scripts/setup_gcp_auth.sh; then
    echo "✅ Setup script completed successfully"
else
    echo "❌ Setup script failed"
    exit 1
fi

# Test the verification script
echo "🔍 Running verification script..."
if python /workspaces/nyc-landmarks-vector-db/utils/check_dev_env.py; then
    echo "✅ Verification script completed successfully"
else
    echo "❌ Verification script failed"
    exit 1
fi

echo "================================================"
echo "🎉 Devcontainer GCP setup simulation successful!"
echo "The setup will work correctly when the container starts."
