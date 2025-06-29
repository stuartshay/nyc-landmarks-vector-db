#!/bin/bash

# POST Request Body Logging Query Examples
# This script demonstrates how to query logs for both performance metrics and request bodies

echo "🔍 NYC Landmarks Vector DB - Request Body Logging Queries"
echo "=========================================================="

# Set project ID
PROJECT_ID="velvety-byway-327718"

echo ""
echo "1. Current Performance Logs (Query Endpoints):"
echo "----------------------------------------------"
gcloud logging read \
  'logName=~"nyc-landmarks-vector-db" AND jsonPayload.endpoint_category="query" AND jsonPayload.metric_type="performance"' \
  --limit=3 \
  --format="table(timestamp,jsonPayload.endpoint,jsonPayload.duration_ms,jsonPayload.status_code)" \
  --project=$PROJECT_ID

echo ""
echo "2. Looking for Request Body Logs (Will be available after middleware deployment):"
echo "---------------------------------------------------------------------------------"
gcloud logging read \
  'logName=~"nyc-landmarks-vector-db" AND jsonPayload.endpoint_category="query" AND jsonPayload.metric_type="request_body"' \
  --limit=3 \
  --format="table(timestamp,jsonPayload.endpoint,jsonPayload.body_size_bytes,jsonPayload.client_ip)" \
  --project=$PROJECT_ID

echo ""
echo "3. Combined Query - Performance AND Request Body Logs:"
echo "-----------------------------------------------------"
gcloud logging read \
  'logName=~"nyc-landmarks-vector-db" AND jsonPayload.endpoint_category="query" AND (jsonPayload.metric_type="performance" OR jsonPayload.metric_type="request_body")' \
  --limit=5 \
  --format="table(timestamp,jsonPayload.metric_type,jsonPayload.endpoint,jsonPayload.duration_ms,jsonPayload.body_size_bytes)" \
  --project=$PROJECT_ID

echo ""
echo "4. Recent Query Activity (Last 30 minutes):"
echo "-------------------------------------------"
THIRTY_MIN_AGO=$(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%SZ)
gcloud logging read \
  "logName=~\"nyc-landmarks-vector-db\" AND jsonPayload.endpoint_category=\"query\" AND timestamp>=\"$THIRTY_MIN_AGO\"" \
  --limit=5 \
  --format="table(timestamp,jsonPayload.metric_type,jsonPayload.endpoint)" \
  --project=$PROJECT_ID

echo ""
echo "5. Sample Request Body Query (for when middleware is deployed):"
echo "--------------------------------------------------------------"
echo "Command to find specific queries:"
echo 'gcloud logging read '"'"'jsonPayload.metric_type="request_body" AND jsonPayload.request_body.query:"Lefferts Family"'"'"' --project='$PROJECT_ID

echo ""
echo "6. Performance Analysis - Slow Requests (>2000ms):"
echo "--------------------------------------------------"
gcloud logging read \
  'logName=~"nyc-landmarks-vector-db" AND jsonPayload.metric_type="performance" AND jsonPayload.duration_ms>2000' \
  --limit=5 \
  --format="table(timestamp,jsonPayload.endpoint,jsonPayload.duration_ms,jsonPayload.status_code)" \
  --project=$PROJECT_ID

echo ""
echo "7. Query API Request Information:"
echo "--------------------------------"
gcloud logging read \
  'logName=~"nyc-landmarks-vector-db.nyc_landmarks.api.query" AND message:"search_text request"' \
  --limit=2 \
  --format="table(timestamp,jsonPayload.message)" \
  --project=$PROJECT_ID

echo ""
echo "=========================================================="
echo "📋 Summary of Filtering Options:"
echo ""
echo "Filter by endpoint category:"
echo "  jsonPayload.endpoint_category=\"query\""
echo ""
echo "Filter by metric type:"
echo "  jsonPayload.metric_type=\"performance\""
echo "  jsonPayload.metric_type=\"request_body\""
echo ""
echo "Combined filter (your original request):"
echo "  jsonPayload.endpoint_category=\"query\" AND jsonPayload.metric_type=\"performance\""
echo ""
echo "Find slow requests:"
echo "  jsonPayload.metric_type=\"performance\" AND jsonPayload.duration_ms>5000"
echo ""
echo "Find specific query content (after request body logging is deployed):"
echo "  jsonPayload.metric_type=\"request_body\" AND jsonPayload.request_body.query:\"search term\""
echo ""
echo "Find requests by client:"
echo "  jsonPayload.client_ip=\"specific.ip.address\""
echo "=========================================================="
