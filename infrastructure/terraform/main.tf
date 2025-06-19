terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

locals {
  project_id = var.project_id != "" ? var.project_id : (
    var.credentials_file != "" ? jsondecode(file(var.credentials_file))["project_id"] : null
  )
  region = var.region
}

provider "google" {
  project     = local.project_id
  region      = local.region
  credentials = var.credentials_file != "" ? file(var.credentials_file) : null
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
  description = "Count of error logs from vector database operations"
  filter      = "logName=~\"${var.log_name_prefix}.nyc_landmarks.vectordb\" AND severity>=ERROR"
}

resource "google_logging_metric" "vectordb_slow_operations" {
  name        = "${var.log_name_prefix}.vectordb_slow_operations"
  description = "Count of slow vector database operations (>500ms)"
  filter      = "logName=~\"${var.log_name_prefix}.nyc_landmarks.vectordb\" AND jsonPayload.duration_ms>500"
}

resource "google_logging_project_bucket_config" "vectordb_logs_bucket" {
  project        = local.project_id
  location       = "global"
  bucket_id      = "vectordb-logs"
  retention_days = 30
  description    = "Bucket for storing vector database logs"
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
      trigger {
        count = 1
      }
    }
  }

  notification_channels = var.notification_channels
  documentation {
    content   = "Vector database operations are experiencing errors at a rate higher than normal. Please investigate logs in the vectordb-logs bucket for more details."
    mime_type = "text/markdown"
  }
  alert_strategy {
    auto_close = "1800s"
  }
}

# Alert policy for vector database inactivity
resource "google_monitoring_alert_policy" "vectordb_activity_alert" {
  display_name = "Vector Database Inactivity Alert"
  combiner     = "OR"
  conditions {
    display_name = "Low or no activity in vector database"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.vectordb_logs.name}\" AND resource.type=\"global\""
      duration        = "1800s"
      comparison      = "COMPARISON_LT"
      threshold_value = 0.01
      aggregations {
        alignment_period   = "900s"
        per_series_aligner = "ALIGN_RATE"
      }
      trigger {
        count = 1
      }
    }
  }

  notification_channels = var.notification_channels
  documentation {
    content   = "Vector database shows little to no activity for an extended period. This might indicate the service is not being utilized or is experiencing issues."
    mime_type = "text/markdown"
  }
  alert_strategy {
    auto_close = "86400s"
  }
}

# Alert policy for slow vector database operations
resource "google_monitoring_alert_policy" "vectordb_slow_operations_alert" {
  display_name = "Vector Database Slow Operations Alert"
  combiner     = "OR"
  conditions {
    display_name = "High number of slow vector database operations"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.vectordb_slow_operations.name}\" AND resource.type=\"global\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
      trigger {
        count = 1
      }
    }
  }

  notification_channels = var.notification_channels
  documentation {
    content   = "Vector database is experiencing a high number of slow operations (>500ms). This may indicate performance issues or resource constraints."
    mime_type = "text/markdown"
  }
  alert_strategy {
    auto_close = "1800s"
  }
}

# Uptime check for the health endpoint
resource "google_monitoring_uptime_check_config" "health_check" {
  display_name = "NYC Landmarks Vector DB Health Check"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path           = "/health"
    port           = "443"
    use_ssl        = true
    validate_ssl   = true
    request_method = "GET"

    accepted_response_status_codes {
      status_class = "STATUS_CLASS_2XX"
    }
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = local.project_id
      host       = "vector-db.coredatastore.com"
    }
  }

  content_matchers {
    content = "\"status\": \"healthy\""
    matcher = "CONTAINS_STRING"
  }

  checker_type = "STATIC_IP_CHECKERS"
}

# Cloud Scheduler job to periodically check health endpoint
resource "google_cloud_scheduler_job" "scheduler_health_check" {
  name        = "nyc-landmarks-health-check"
  description = "Periodic health check for NYC Landmarks Vector DB"
  schedule    = "*/5 * * * *" # Every 5 minutes
  time_zone   = "UTC"
  region      = local.region

  http_target {
    uri         = "https://vector-db.coredatastore.com/health"
    http_method = "GET"

    headers = {
      "User-Agent" = "GCP-Scheduler-HealthCheck/1.0"
    }
  }

  retry_config {
    retry_count          = 3
    max_retry_duration   = "60s"
    min_backoff_duration = "5s"
    max_backoff_duration = "30s"
  }
}

resource "google_monitoring_dashboard" "api_dashboard" {
  dashboard_json = templatefile("${path.module}/dashboard.json.tpl", {
    log_name_prefix = var.log_name_prefix
    project_id      = local.project_id
  })
}
