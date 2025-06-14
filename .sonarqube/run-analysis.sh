#!/bin/bash
# Run SonarQube analysis on the project

# Change to the project root directory
cd "$(dirname "$0")/.."

TOKEN_FILE=".sonarqube/token"

# Check if SonarQube is running
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/api/system/status)
if [ "$STATUS" != "200" ]; then
  echo "❌ ERROR: SonarQube is not running. Start it with: .sonarqube/start-sonarqube.sh"
  exit 1
fi

# Check if token file exists and setup if it doesn't
if [ ! -f "$TOKEN_FILE" ]; then
  echo "🔑 No token found. Setting up token..."
  ./.sonarqube/setup-token.sh
  if [ $? -ne 0 ]; then
    echo "❌ Failed to set up token. Please run ./.sonarqube/setup-token.sh manually."
    exit 1
  fi
fi

# Read token from file
TOKEN=$(cat "$TOKEN_FILE")
if [ -z "$TOKEN" ]; then
  echo "❌ Token file is empty. Please run ./.sonarqube/setup-token.sh manually."
  exit 1
fi

echo "🧪 Running unit tests with coverage and generating reports..."
python -m pytest tests/unit --cov=nyc_landmarks --cov-report=xml --junitxml=test-results.xml

if [ $? -ne 0 ]; then
  echo "⚠️ Tests failed, but continuing with analysis..."
fi

echo "🔍 Running SonarQube analysis..."

# Run sonar-scanner with project properties file and token
sonar-scanner \
  -Dproject.settings=.sonarqube/sonar-project.properties \
  -Dsonar.token="$TOKEN" \
  "$@"

echo "✅ Analysis complete. View results at: http://localhost:9000/dashboard?id=nyc-landmarks-vector-db"
