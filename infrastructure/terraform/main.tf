locals {
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
  description    = "Bucket for storing API logs"
}

# Log View for Vector Database Logs
resource "google_logging_log_view" "vectordb_logs_view" {
  name        = "vectordb-logs-view"
  bucket      = google_logging_project_bucket_config.vectordb_logs_bucket.id
  description = "View for all Vector Database logs"
  filter      = ""
}

# Log View for API Logs
resource "google_logging_log_view" "api_logs_view" {
  name        = "api-logs-view"
  bucket      = google_logging_project_bucket_config.api_logs_bucket.id
  description = "View for all API logs"
  filter      = ""
}

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
