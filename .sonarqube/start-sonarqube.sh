#!/bin/bash
# Start SonarQube and PostgreSQL containers

echo "Starting SonarQube containers..."
cd "$(dirname "$0")" && docker compose up -d

echo "Waiting for SonarQube to initialize..."
sleep 5

# Keep checking until SonarQube is available or timeout
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/api/system/status)
  if [ "$STATUS" == "200" ]; then
    echo "✅ SonarQube is up and running at http://localhost:9000"
    echo "🔐 Default credentials: admin/admin"
    echo "🔑 Setting up authentication token..."

    # Set up token for API access - with a small delay to ensure SonarQube is fully initialized
    sleep 5
    "$(dirname "$0")/setup-token.sh"

    echo "🚀 SonarQube setup complete!"
    exit 0
  fi
  ATTEMPT=$((ATTEMPT+1))
  echo "Waiting for SonarQube to start (attempt $ATTEMPT/$MAX_ATTEMPTS)..."
  sleep 2
done

echo "Timed out waiting for SonarQube to start. Check logs with: docker logs nyc-landmarks-vector-db-sonarqube-1"
exit 1
