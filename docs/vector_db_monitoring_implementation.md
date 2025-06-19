# Vector Database Monitoring Implementation

This document describes the vector database monitoring implementation that was added to address the requirements in PR #194.

## Overview

The vector database monitoring implementation extends the existing Terraform monitoring configuration with:

1. Specialized log-based metrics for vector database operations
1. Dashboard widgets for visualizing vector database activity and performance
1. Alert policies for detecting issues with vector database operations
1. A dedicated log bucket for better log management
1. Comprehensive documentation on using and interpreting the metrics

## Components Implemented

### Log-Based Metrics

Three log-based metrics were created to capture different aspects of vector database operations:

1. **vectordb_logs**: Captures all vector database logs

   ```hcl
   resource "google_logging_metric" "vectordb_logs" {
     name   = "${var.log_name_prefix}.vectordb_logs"
     filter = "logName=~\"${var.log_name_prefix}.nyc_landmarks.vectordb\""
   }
   ```

1. **vectordb_errors**: Tracks error logs from vector database operations

   ```hcl
   resource "google_logging_metric" "vectordb_errors" {
     name        = "${var.log_name_prefix}.vectordb_errors"
     description = "Count of error logs from vector database operations"
     filter      = "logName=~\"${var.log_name_prefix}.nyc_landmarks.vectordb\" AND severity>=ERROR"
   }
   ```

1. **vectordb_slow_operations**: Monitors operations taking longer than expected

   ```hcl
   resource "google_logging_metric" "vectordb_slow_operations" {
     name        = "${var.log_name_prefix}.vectordb_slow_operations"
     description = "Count of slow vector database operations (>500ms)"
     filter      = "logName=~\"${var.log_name_prefix}.nyc_landmarks.vectordb\" AND jsonPayload.duration_ms>500"
   }
   ```

### Dashboard Widgets

Four specialized widgets were added to the monitoring dashboard to visualize vector database activity:

1. **Vector Database Activity** (Scorecard):

   - Real-time activity measurement
   - Includes a spark line for trend visualization
   - Threshold alert for low activity

1. **Vector Database Log Volume** (Line Chart):

   - Rate of vector database logs over time
   - Helps identify usage patterns and potential issues

1. **Vector Database Operations** (Stacked Bar Chart):

   - Hourly count of operations over a 24-hour period
   - Helps with capacity planning and identifying usage patterns

1. **Vector Database Log Distribution** (Pie Chart):

   - Distribution of logs by severity level
   - Helps quickly identify if errors are occurring

### Alert Policies

Three alert policies were implemented to proactively monitor vector database health:

1. **Vector Database Error Rate Alert**:

   - Triggers when error rate exceeds threshold (5 errors in 5 minutes)
   - Helps identify systemic issues with vector database operations

1. **Vector Database Inactivity Alert**:

   - Triggers when activity drops below expected levels
   - 30-minute window of inactivity before alerting
   - Helps detect service disruptions or integration issues

1. **Vector Database Slow Operations Alert**:

   - Triggers when a high number of slow operations are detected
   - Helps identify performance issues or resource constraints

### Log Management

A dedicated log bucket was created for better management of vector database logs:

```hcl
resource "google_logging_project_bucket_config" "vectordb_logs_bucket" {
  project        = local.project_id
  location       = "global"
  bucket_id      = "vectordb-logs"
  retention_days = 30
  description    = "Bucket for storing vector database logs"
}
```

This provides:

- A 30-day retention policy for vector database logs
- Better organization of logs separate from general application logs
- Centralized storage for all vector database related logs

## Outputs

The monitoring configuration outputs provide direct links to the created resources:

```hcl
output "log_metrics" {
  description = "Created log-based metrics"
  value = {
    # ... existing metrics ...
    vectordb_logs          = google_logging_metric.vectordb_logs.name
    vectordb_errors        = google_logging_metric.vectordb_errors.name
    vectordb_slow_operations = google_logging_metric.vectordb_slow_operations.name
  }
}

output "vectordb_logs_bucket" {
  description = "Log bucket for vector database logs"
  value       = google_logging_project_bucket_config.vectordb_logs_bucket.name
}

output "alert_policies" {
  description = "Created alert policies"
  value = {
    vectordb_error_alert         = google_monitoring_alert_policy.vectordb_error_alert.name
    vectordb_activity_alert      = google_monitoring_alert_policy.vectordb_activity_alert.name
    vectordb_slow_operations_alert = google_monitoring_alert_policy.vectordb_slow_operations_alert.name
  }
}

output "alert_policies_urls" {
  description = "Direct URLs to the alert policies"
  value = {
    vectordb_error_alert         = "https://console.cloud.google.com/monitoring/alerting/policies/${split("/", google_monitoring_alert_policy.vectordb_error_alert.id)[3]}?project=${var.project_id}"
    vectordb_activity_alert      = "https://console.cloud.google.com/monitoring/alerting/policies/${split("/", google_monitoring_alert_policy.vectordb_activity_alert.id)[3]}?project=${var.project_id}"
    vectordb_slow_operations_alert = "https://console.cloud.google.com/monitoring/alerting/policies/${split("/", google_monitoring_alert_policy.vectordb_slow_operations_alert.id)[3]}?project=${var.project_id}"
  }
}
```

## Using the Vector Database Monitoring

### Viewing Vector Database Logs

To view logs captured by the `vectordb_logs` metric, open **Logs Explorer** in the Google Cloud Console and run queries such as:

```text
logName=~"${LOG_NAME_PREFIX}.nyc_landmarks.vectordb"
```

Or filter using the dedicated log bucket:

```text
resource.type="logging_bucket" AND resource.labels.bucket_name="vectordb-logs"
```

### Advanced Query Examples

For targeted analysis, you can use these example queries:

**Query for vector database errors:**

```
logName=~"${LOG_NAME_PREFIX}.nyc_landmarks.vectordb" severity>=ERROR
```

**Query for specific vector operations (like query or upsert):**

```
logName=~"${LOG_NAME_PREFIX}.nyc_landmarks.vectordb" jsonPayload.operation="query"
```

**Query for slow vector operations (taking more than 500ms):**

```
logName=~"${LOG_NAME_PREFIX}.nyc_landmarks.vectordb" jsonPayload.duration_ms>500
```

**Query for operations on a specific namespace:**

```
logName=~"${LOG_NAME_PREFIX}.nyc_landmarks.vectordb" jsonPayload.namespace="wikipedia"
```

### Interpreting Vector Database Metrics

#### Activity Patterns

- **Normal Pattern**: Regular spikes during business hours with lower activity overnight
- **Warning Signs**: Sudden drops in activity or prolonged periods of zero activity
- **Action Items**: Investigate system health if activity drops unexpectedly

#### Log Volume

- **Normal Pattern**: Consistent with application usage patterns
- **Warning Signs**: Sudden spikes in log volume may indicate errors or performance issues
- **Action Items**: Check for error severity distribution and correlate with API performance

#### Error Distribution

- **Normal Ratio**: Primarily INFO logs with minimal WARNING and ERROR logs
- **Warning Signs**: Increasing proportion of WARNING or ERROR logs
- **Action Items**: Review error logs and address underlying issues

## Future Enhancements

Future monitoring enhancements could include:

1. More granular metrics for specific vector operations (query, upsert, delete)
1. Latency tracking for each operation type
1. Vector index size and growth monitoring
1. Integration with third-party monitoring tools
1. Custom notification channels (Slack, PagerDuty)
1. Automated remediation actions for common issues
1. Dedicated logging views when supported by the provider
