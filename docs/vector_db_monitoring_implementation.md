# Vector Database and API Monitoring Implementation

This document outlines the implementation of monitoring infrastructure for the NYC Landmarks Vector Database and API, as part of PR #194.

## Overview

The monitoring infrastructure includes:

1. Log buckets for storing logs
1. Log views for easy access to specific log types
1. Log-based metrics for monitoring activity and errors
1. Alert policies for proactive notifications
1. Uptime checks and health monitoring
1. Dashboard for visualizing metrics

## Log Buckets and Views

### Vector Database Logs

```hcl
resource "google_logging_project_bucket_config" "vectordb_logs_bucket" {
  project        = local.project_id
  location       = "global"
  bucket_id      = "vectordb-logs"
  retention_days = 30
  description    = "Bucket for storing vector database logs"
}

resource "google_logging_log_view" "vectordb_logs_view" {
  name        = "vectordb-logs-view"
  bucket      = google_logging_project_bucket_config.vectordb_logs_bucket.id
  description = "View for all Vector Database logs"
  filter      = ""
}
```

**Access URL**: [Vector Database Logs View](https://console.cloud.google.com/logs/storage/projects/velvety-byway-327718/locations/global/buckets/vectordb-logs/views/vectordb-logs-view?project=velvety-byway-327718)

### API Logs

```hcl
resource "google_logging_project_bucket_config" "api_logs_bucket" {
  project        = local.project_id
  location       = "global"
  bucket_id      = "api-logs"
  retention_days = 30
  description    = "Bucket for storing API logs"
}

resource "google_logging_log_view" "api_logs_view" {
  name        = "api-logs-view"
  bucket      = google_logging_project_bucket_config.api_logs_bucket.id
  description = "View for all API logs"
  filter      = ""
}
```

The API logs view captures logs from various API components, including:

- API query logs (e.g., `nyc_landmarks.api.query`)
- API middleware logs
- Request/response information
- Endpoint access patterns

**Sample Log Entry**:

```json
{
  "logName": "projects/velvety-byway-327718/logs/nyc-landmarks-vector-db.nyc_landmarks.api.query",
  "severity": "INFO",
  "jsonPayload": {
    "message": "search_text request: query=What are the architectural features? landmark_id=LP-00001 source_type=None top_k=5",
    "module": "query",
    "function": "search_text",
    "request_path": "/api/query/search/landmark",
    "request_id": "5c8888d0-7e6c-47bd-8c6c-88ca871fbd39",
    "duration_ms": 7.0476531982421875
  }
}
```

**Access URL**: [API Logs View](https://console.cloud.google.com/logs/storage/projects/velvety-byway-327718/locations/global/buckets/api-logs/views/api-logs-view?project=velvety-byway-327718)

## Log-Based Metrics

The following log-based metrics were implemented:

```hcl
resource "google_logging_metric" "requests" {
  name   = "${var.log_name_prefix}.requests"
  filter = "resource.type=\"cloud_run_revision\" AND logName=\"projects/${local.project_id}/logs/${var.log_name_prefix}.nyc_landmarks.api.middleware\" AND jsonPayload.metric_type=\"performance\""
}

resource "google_logging_metric" "errors" {
  name   = "${var.log_name_prefix}.errors"
  filter = "resource.type=\"cloud_run_revision\" AND logName=\"projects/${local.project_id}/logs/${var.log_name_prefix}.nyc_landmarks.api.middleware\" AND jsonPayload.metric_type=\"performance\" AND jsonPayload.status_code>=500"
}

resource "google_logging_metric" "latency" {
  name   = "${var.log_name_prefix}.latency"
  filter = "resource.type=\"cloud_run_revision\" AND logName=\"projects/${local.project_id}/logs/${var.log_name_prefix}.nyc_landmarks.api.middleware\" AND jsonPayload.metric_type=\"performance\" AND jsonPayload.duration_ms>=0"
}

resource "google_logging_metric" "validation_warnings" {
  name   = "${var.log_name_prefix}.validation_warnings"
  filter = "resource.type=\"cloud_run_revision\" AND logName=\"projects/${local.project_id}/logs/${var.log_name_prefix}.nyc_landmarks.utils.validation\" AND severity=\"WARNING\""
}

resource "google_logging_metric" "vectordb_logs" {
  name   = "${var.log_name_prefix}.vectordb_logs"
  filter = "logName=~\"${var.log_name_prefix}.nyc_landmarks.vectordb\""
}

resource "google_logging_metric" "vectordb_errors" {
  name        = "${var.log_name_prefix}.vectordb_errors"
  description = "Counts errors in vector database operations"
  filter      = "logName=~\"${var.log_name_prefix}.nyc_landmarks.vectordb\" AND severity=\"ERROR\""
}

resource "google_logging_metric" "vectordb_slow_operations" {
  name        = "${var.log_name_prefix}.vectordb_slow_operations"
  description = "Tracks slow operations in vector database"
  filter      = "logName=~\"${var.log_name_prefix}.nyc_landmarks.vectordb\" AND jsonPayload.duration_ms>500"
}
```

## Alert Policies

Three alert policies were implemented to monitor vector database operations:

1. **Error Rate Alert**: Triggers when the rate of vector database errors exceeds a threshold.
1. **Activity Alert**: Triggers when vector database activity falls below a certain threshold.
1. **Slow Operations Alert**: Triggers when the rate of slow vector database operations exceeds a threshold.

**Access URLs**:

- [Error Alert](https://console.cloud.google.com/monitoring/alerting/policies/680246190038586123?project=velvety-byway-327718)
- [Activity Alert](https://console.cloud.google.com/monitoring/alerting/policies/15343916069992722197?project=velvety-byway-327718)
- [Slow Operations Alert](https://console.cloud.google.com/monitoring/alerting/policies/16573989850872248382?project=velvety-byway-327718)

## Dashboard

A comprehensive dashboard was created to visualize metrics:

**Access URL**: [NYC Landmarks Vector DB - API Monitoring Dashboard](https://console.cloud.google.com/monitoring/dashboards/custom/cbcd77e4-0a7a-4bdb-8570-d1adfc28658a?project=velvety-byway-327718)

## Implementation Challenges and Solutions

### Log View Filter Syntax

When implementing the log views, we encountered issues with the filter syntax:

- Complex regex patterns in the filter field caused validation errors
- The solution was to use an empty filter string to include all logs in the bucket

### State Locking

During the Terraform apply process, we encountered state locking issues:

- When terraform apply gets interrupted, locks need to be manually cleared
- Used `kill` to terminate hanging processes and remove state lock files

## Usage

### Viewing Logs

1. Vector DB logs: Access the [Vector Database Logs View](https://console.cloud.google.com/logs/storage/projects/velvety-byway-327718/locations/global/buckets/vectordb-logs/views/vectordb-logs-view?project=velvety-byway-327718)
1. API logs: Access the [API Logs View](https://console.cloud.google.com/logs/storage/projects/velvety-byway-327718/locations/global/buckets/api-logs/views/api-logs-view?project=velvety-byway-327718)

### Monitoring Alerts

Set up notification channels in the Google Cloud Console and add them to the `notification_channels` variable in your `terraform.tfvars` file:

```hcl
notification_channels = [
  "projects/velvety-byway-327718/notificationChannels/123456789",
  "projects/velvety-byway-327718/notificationChannels/987654321"
]
```

## Next Steps

1. Implement additional API-specific alert policies
1. Enhance dashboard with more API metrics
1. Set up anomaly detection for API request patterns
1. Create runbooks for responding to specific alerts
