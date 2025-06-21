#!/bin/bash

# Script to validate the API and VectorDB log views
# This script assumes you have authenticated with GCP using gcloud auth login

echo "Validating API Log View..."
gcloud logging read "logName=projects/velvety-byway-327718/logs/nyc-landmarks-vector-db.nyc_landmarks.api.query" \
  --bucket=api-logs \
  --view=api-logs-view \
  --location=global \
  --project=velvety-byway-327718 \
  --limit=5 \
  --format=json

echo "Validating VectorDB Log View..."
gcloud logging read "logName=projects/velvety-byway-327718/logs/nyc-landmarks-vector-db.nyc_landmarks.vectordb" \
  --bucket=vectordb-logs \
  --view=vectordb-logs-view \
  --location=global \
  --project=velvety-byway-327718 \
  --limit=5 \
  --format=json

# Alternative method using REST API
# This can be run if you have a valid access token
echo "Alternative validation method using REST API:"
echo "To validate API Log View using REST API, run:"
echo "curl -H \"Authorization: Bearer \$(gcloud auth print-access-token)\" \
  \"https://logging.googleapis.com/v2/projects/velvety-byway-327718/locations/global/buckets/api-logs/views/api-logs-view/logs\""

echo "To validate VectorDB Log View using REST API, run:"
echo "curl -H \"Authorization: Bearer \$(gcloud auth print-access-token)\" \
  \"https://logging.googleapis.com/v2/projects/velvety-byway-327718/locations/global/buckets/vectordb-logs/views/vectordb-logs-view/logs\""
