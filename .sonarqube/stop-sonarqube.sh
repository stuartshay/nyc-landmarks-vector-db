#!/bin/bash
# Stop SonarQube and PostgreSQL containers

echo "Stopping SonarQube containers..."
cd "$(dirname "$0")" && docker compose down

echo "SonarQube containers stopped."
