locals {
  # Test comment for new Terraform workflow system v3 - testing fixed file paths
  project_id = var.project_id != "" ? var.project_id : (
    var.GOOGLE_CREDENTIALS != "" ? jsondecode(var.GOOGLE_CREDENTIALS)["project_id"] : null
  )
  region = var.region
}

provider "google" {
  project     = local.project_id
  region      = local.region
  credentials = var.GOOGLE_CREDENTIALS
}

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

resource "google_logging_project_bucket_config" "vectordb_logs_bucket" {
  project        = local.project_id
  location       = "global"
  bucket_id      = "vectordb-logs"
  retention_days = 30
  description    = "Bucket for storing vector database logs"
}

resource "google_logging_project_bucket_config" "api_logs_bucket" {
  project        = local.project_id
  location       = "global"
  bucket_id      = "api-logs"
  retention_days = 30
  description    = "Bucket for storing general API logs"
}

# Endpoint-specific log buckets
resource "google_logging_project_bucket_config" "api_query_logs_bucket" {
  project        = local.project_id
  location       = "global"
  bucket_id      = "api-query-logs"
  retention_days = 30
  description    = "Bucket for storing /api/query endpoint logs"
}

resource "google_logging_project_bucket_config" "api_chat_logs_bucket" {
  project        = local.project_id
  location       = "global"
  bucket_id      = "api-chat-logs"
  retention_days = 30
  description    = "Bucket for storing /api/chat endpoint logs"
}

resource "google_logging_project_bucket_config" "api_health_logs_bucket" {
  project        = local.project_id
  location       = "global"
  bucket_id      = "api-health-logs"
  retention_days = 30
  description    = "Bucket for storing /health endpoint logs"
}

# Log View for Vector Database Logs
resource "google_logging_log_view" "vectordb_logs_view" {
  name        = "vectordb-logs-view"
  bucket      = google_logging_project_bucket_config.vectordb_logs_bucket.id
  description = "View for all Vector Database logs"
  filter      = ""
}

# Log View for General API Logs
resource "google_logging_log_view" "api_logs_view" {
  name        = "api-logs-view"
  bucket      = google_logging_project_bucket_config.api_logs_bucket.id
  description = "View for general API logs"
  filter      = ""
}

# Endpoint-Specific Log Views (Note: These show all logs in their respective buckets
# since GCP log views cannot filter on JSON payload fields effectively)

resource "google_logging_log_view" "api_query_logs_view" {
  name        = "api-query-logs-view"
  bucket      = google_logging_project_bucket_config.api_query_logs_bucket.id
  description = "View for /api/query endpoint logs"
  filter      = ""
}

resource "google_logging_log_view" "api_chat_logs_view" {
  name        = "api-chat-logs-view"
  bucket      = google_logging_project_bucket_config.api_chat_logs_bucket.id
  description = "View for /api/chat endpoint logs"
  filter      = ""
}

resource "google_logging_log_view" "api_health_logs_view" {
  name        = "api-health-logs-view"
  bucket      = google_logging_project_bucket_config.api_health_logs_bucket.id
  description = "View for /health endpoint logs"
  filter      = ""
}

# Log Sinks for Endpoint-Specific Routing
# Note: Conflicting resources cleaned up - ready for fresh deployment

# Log Sink for Query API Logs
resource "google_logging_project_sink" "api_query_logs_sink" {
  name        = "api-query-logs-sink"
  destination = "logging.googleapis.com/${google_logging_project_bucket_config.api_query_logs_bucket.id}"

  # Filter for query API logs using efficient label-based filtering
  filter = <<-EOT
    resource.type="cloud_run_revision" AND
    resource.labels.service_name="nyc-landmarks-vector-db" AND
    labels.endpoint_category="query"
  EOT

  unique_writer_identity = true
}

# Log Sink for Chat API Logs
resource "google_logging_project_sink" "api_chat_logs_sink" {
  name        = "api-chat-logs-sink"
  destination = "logging.googleapis.com/${google_logging_project_bucket_config.api_chat_logs_bucket.id}"

  # Filter for chat API logs using efficient label-based filtering
  filter = <<-EOT
    resource.type="cloud_run_revision" AND
    resource.labels.service_name="nyc-landmarks-vector-db" AND
    labels.endpoint_category="chat"
  EOT

  unique_writer_identity = true
}

# Log Sink for Health API Logs
resource "google_logging_project_sink" "api_health_logs_sink" {
  name        = "api-health-logs-sink"
  destination = "logging.googleapis.com/${google_logging_project_bucket_config.api_health_logs_bucket.id}"

  # Filter for health API logs using efficient label-based filtering
  filter = <<-EOT
    resource.type="cloud_run_revision" AND
    resource.labels.service_name="nyc-landmarks-vector-db" AND
    labels.endpoint_category="health"
  EOT

  unique_writer_identity = true
}

# Log Sink for General API Logs (fallback for other endpoints)
resource "google_logging_project_sink" "api_logs_sink" {
  name        = "api-logs-sink"
  destination = "logging.googleapis.com/${google_logging_project_bucket_config.api_logs_bucket.id}"

  # Filter for other API-related logs that don't match specific endpoint categories
  filter = <<-EOT
    resource.type="cloud_run_revision" AND
    resource.labels.service_name="nyc-landmarks-vector-db" AND
    (
      logName=~"projects/${local.project_id}/logs/${var.log_name_prefix}.nyc_landmarks.api" OR
      (jsonPayload.metric_type="performance" AND jsonPayload.endpoint_category="other") OR
      jsonPayload.module="middleware"
    )
  EOT

  unique_writer_identity = true
}

# Log Sink for Vector Database Logs
resource "google_logging_project_sink" "vectordb_logs_sink" {
  name        = "vectordb-logs-sink"
  destination = "logging.googleapis.com/${google_logging_project_bucket_config.vectordb_logs_bucket.id}"

  # Filter for vector database related logs
  filter = <<-EOT
    resource.type="cloud_run_revision" AND
    resource.labels.service_name="nyc-landmarks-vector-db" AND
    (
      logName=~"projects/${local.project_id}/logs/${var.log_name_prefix}.nyc_landmarks.vectordb" OR
      jsonPayload.module="vectordb" OR
      jsonPayload.module="pinecone_client"
    )
  EOT

  # Use a unique writer identity
  unique_writer_identity = true
}

# Grant the sink service accounts permission to write to the buckets
# Note: Temporarily commented out to allow sinks to be created first
# These will be re-enabled after sinks have proper writer identities

# resource "google_project_iam_member" "api_logs_sink_writer" {
#   project = local.project_id
#   role    = "roles/logging.bucketWriter"
#   member  = google_logging_project_sink.api_logs_sink.writer_identity
# }

# resource "google_project_iam_member" "api_query_logs_sink_writer" {
#   project = local.project_id
#   role    = "roles/logging.bucketWriter"
#   member  = google_logging_project_sink.api_query_logs_sink.writer_identity
# }

# resource "google_project_iam_member" "api_chat_logs_sink_writer" {
#   project = local.project_id
#   role    = "roles/logging.bucketWriter"
#   member  = google_logging_project_sink.api_chat_logs_sink.writer_identity
# }

# resource "google_project_iam_member" "api_health_logs_sink_writer" {
#   project = local.project_id
#   role    = "roles/logging.bucketWriter"
#   member  = google_logging_project_sink.api_health_logs_sink.writer_identity
# }

# resource "google_project_iam_member" "vectordb_logs_sink_writer" {
#   project = local.project_id
#   role    = "roles/logging.bucketWriter"
#   member  = google_logging_project_sink.vectordb_logs_sink.writer_identity
# }

# Alert policy for vector database errors
resource "google_monitoring_alert_policy" "vectordb_error_alert" {
  display_name = "Vector Database Error Rate Alert"
  combiner     = "OR"
  conditions {
    display_name = "High error rate in vector database operations"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.vectordb_errors.name}\" AND resource.type=\"global\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"
  }

  notification_channels = var.notification_channels
  documentation {
    content   = "Vector database is experiencing high error rates. Check logs for details."
    mime_type = "text/markdown"
  }
  depends_on = [google_logging_metric.vectordb_errors]
}

# Alert policy for vector database activity
resource "google_monitoring_alert_policy" "vectordb_activity_alert" {
  display_name = "Vector Database Activity Alert"
  combiner     = "OR"
  conditions {
    display_name = "Low activity in vector database operations"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.vectordb_logs.name}\" AND resource.type=\"global\""
      duration        = "600s"
      comparison      = "COMPARISON_LT"
      threshold_value = 0.01
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"
  }

  notification_channels = var.notification_channels
  documentation {
    content   = "Vector database is showing abnormally low activity. Check if service is functioning correctly."
    mime_type = "text/markdown"
  }
  depends_on = [google_logging_metric.vectordb_logs]
}

# Alert policy for slow vector database operations
resource "google_monitoring_alert_policy" "vectordb_slow_operations_alert" {
  display_name = "Vector Database Slow Operations Alert"
  combiner     = "OR"
  conditions {
    display_name = "High rate of slow operations in vector database"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.vectordb_slow_operations.name}\" AND resource.type=\"global\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"
  }

  notification_channels = var.notification_channels
  documentation {
    content   = "Vector database is experiencing slow operations. Check system resources and vector database logs."
    mime_type = "text/markdown"
  }
  depends_on = [google_logging_metric.vectordb_slow_operations]
}

# Cloud Scheduler job for uptime checks (to keep API warm)
resource "google_cloud_scheduler_job" "scheduler_health_check" {
  name             = "nyc-landmarks-health-check"
  description      = "Scheduled health check for NYC landmarks API"
  schedule         = "*/5 * * * *"
  time_zone        = "America/New_York"
  attempt_deadline = "30s"
  region           = local.region

  retry_config {
    retry_count = 1
  }

  http_target {
    uri         = var.api_health_check_url
    http_method = "GET"
    headers = {
      "User-Agent" = "GCP-Scheduler-HealthCheck/1.0"
    }
  }
}

# Uptime check
resource "google_monitoring_uptime_check_config" "health_check" {
  display_name = "NYC Landmarks Vector DB Health Check"
  timeout      = "10s"
  period       = "300s"

  http_check {
    path           = "/"
    port           = "443"
    use_ssl        = true
    validate_ssl   = true
    request_method = "GET"
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = local.project_id
      host       = var.uptime_check_host
    }
  }
}

# Dashboard for API metrics
resource "google_monitoring_dashboard" "api_dashboard" {
  dashboard_json = templatefile("${path.module}/dashboard.json.tpl", {
    project_id      = local.project_id,
    log_name_prefix = var.log_name_prefix,
    dashboard_name  = "NYC Landmarks Vector DB - API Monitoring Dashboard"
  })
}
