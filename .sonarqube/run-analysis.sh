#!/bin/bash
# Run SonarQube analysis on the project

# Change to the project root directory
cd "$(dirname "$0")/.."

# Check if SonarQube is running
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/api/system/status)
if [ "$STATUS" != "200" ]; then
  echo "ERROR: SonarQube is not running. Start it with: .sonarqube/start-sonarqube.sh"
  exit 1
fi

echo "Running SonarQube analysis..."

# Run sonar-scanner with project properties file
sonar-scanner -Dproject.settings=.sonarqube/sonar-project.properties "$@"

echo "Analysis complete. View results at: http://localhost:9000/dashboard?id=nyc-landmarks-vector-db"
