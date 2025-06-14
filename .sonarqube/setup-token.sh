#!/bin/bash

# SonarQube Token Setup Script
# This script creates a hardcoded token for local development use

TOKEN_FILE=".sonarqube/token"
TOKEN_NAME="local-development"
TOKEN_VALUE="nyc-landmarks-local-dev-token"
SONARQUBE_URL="http://localhost:9000"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin"

echo "🔑 Setting up SonarQube token..."

# Check if SonarQube is running
echo "📡 Checking SonarQube status..."
MAX_ATTEMPTS=10
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    STATUS_RESPONSE=$(curl -s $SONARQUBE_URL/api/system/status)
    if [[ $STATUS_RESPONSE == *"UP"* ]]; then
        echo "✅ SonarQube is running"
        break
    fi
    ATTEMPT=$((ATTEMPT+1))
    echo "⏳ Waiting for SonarQube to be ready (attempt $ATTEMPT/$MAX_ATTEMPTS)..."
    sleep 3

    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo "❌ SonarQube is not running. Please start it with 'make sonar-start'"
        # Create token anyway - it will be used once SonarQube is available
        echo $TOKEN_VALUE > $TOKEN_FILE
        echo "✅ Hardcoded token saved to $TOKEN_FILE"
        exit 0
    fi
done

echo "✅ SonarQube is running"

# Check if token file already exists
if [ -f "$TOKEN_FILE" ]; then
    echo "🔑 Token file already exists. Using existing token."
    exit 0
fi

# Create token through API
echo "🔑 Creating token through API..."
TOKEN_RESPONSE=$(curl -s -X POST "$SONARQUBE_URL/api/user_tokens/generate" \
    -u "$ADMIN_USERNAME:$ADMIN_PASSWORD" \
    -d "name=$TOKEN_NAME" \
    -d "login=admin")

# Check if token was created successfully
if [[ $TOKEN_RESPONSE == *"error"* ]]; then
    echo "❌ Failed to create token. Checking if token already exists..."

    # If token already exists, revoke it and create a new one
    REVOKE_RESPONSE=$(curl -s -X POST "$SONARQUBE_URL/api/user_tokens/revoke" \
        -u "$ADMIN_USERNAME:$ADMIN_PASSWORD" \
        -d "name=$TOKEN_NAME")

    # Try to create token again
    TOKEN_RESPONSE=$(curl -s -X POST "$SONARQUBE_URL/api/user_tokens/generate" \
        -u "$ADMIN_USERNAME:$ADMIN_PASSWORD" \
        -d "name=$TOKEN_NAME" \
        -d "login=admin")

    if [[ $TOKEN_RESPONSE == *"error"* ]]; then
        echo "❌ Failed to create token after revoke attempt."
        echo "⚠️ Using hardcoded token value instead."
        # Save hardcoded token to file
        echo $TOKEN_VALUE > $TOKEN_FILE
        echo "✅ Hardcoded token saved to $TOKEN_FILE"
        exit 0
    fi
fi

# Extract token from response
ACTUAL_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACTUAL_TOKEN" ]; then
    echo "⚠️ Could not extract token from API response. Using hardcoded token value instead."
    # Save hardcoded token to file
    echo $TOKEN_VALUE > $TOKEN_FILE
else
    # Save actual token to file
    echo $ACTUAL_TOKEN > $TOKEN_FILE
fi

echo "✅ Token saved to $TOKEN_FILE"
echo "🔒 This file is excluded from git via .gitignore"
