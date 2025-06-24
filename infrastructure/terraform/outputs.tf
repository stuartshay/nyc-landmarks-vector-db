output "project_id" {
  description = "The GCP project ID"
  value       = local.project_id
  sensitive   = true
}

output "region" {
  description = "The GCP region"
  value       = local.region
}

output "log_metrics" {
  description = "Created log-based metrics"
  value = {
    requests                 = google_logging_metric.requests.name
    errors                   = google_logging_metric.errors.name
    latency                  = google_logging_metric.latency.name
    validation_warnings      = google_logging_metric.validation_warnings.name
    vectordb_logs            = google_logging_metric.vectordb_logs.name
    vectordb_errors          = google_logging_metric.vectordb_errors.name
    vectordb_slow_operations = google_logging_metric.vectordb_slow_operations.name
  }
}

output "log_buckets" {
  description = "Created log buckets"
  value = {
    api_logs_bucket      = google_logging_project_bucket_config.api_logs_bucket.id
    vectordb_logs_bucket = google_logging_project_bucket_config.vectordb_logs_bucket.id
  }
}

output "log_sinks" {
  description = "Created log sinks"
  value = {
    api_logs_sink      = google_logging_project_sink.api_logs_sink.id
    vectordb_logs_sink = google_logging_project_sink.vectordb_logs_sink.id
  }
}

output "log_views" {
  description = "Created log views"
  value = {
    api_logs_view      = google_logging_log_view.api_logs_view.name
    vectordb_logs_view = google_logging_log_view.vectordb_logs_view.name
  }
}

output "dashboard_id" {
  description = "The monitoring dashboard ID"
  value       = google_monitoring_dashboard.api_dashboard.id
}

output "dashboard_name" {
  description = "The monitoring dashboard display name"
  value       = jsondecode(google_monitoring_dashboard.api_dashboard.dashboard_json)["displayName"]
  sensitive   = true
}

output "dashboard_url" {
  description = "Direct URL to the monitoring dashboard"
  value       = "https://console.cloud.google.com/monitoring/dashboards/custom/${split("/", google_monitoring_dashboard.api_dashboard.id)[3]}?project=${var.project_id}"
  sensitive   = true
}

output "uptime_check_id" {
  description = "The uptime check ID"
  value       = google_monitoring_uptime_check_config.health_check.uptime_check_id
}

output "uptime_check_name" {
  description = "The uptime check display name"
  value       = google_monitoring_uptime_check_config.health_check.display_name
}

output "vectordb_logs_bucket" {
  description = "Log bucket for vector database logs"
  value       = google_logging_project_bucket_config.vectordb_logs_bucket.name
}

output "api_logs_bucket" {
  description = "Log bucket for API logs"
  value       = google_logging_project_bucket_config.api_logs_bucket.name
}

output "log_views_urls" {
  description = "Direct URLs to the log views"
  value = {
    vectordb_logs_view = "https://console.cloud.google.com/logs/storage/${google_logging_project_bucket_config.vectordb_logs_bucket.name}/views/${google_logging_log_view.vectordb_logs_view.name}?project=${var.project_id}"
    api_logs_view      = "https://console.cloud.google.com/logs/storage/${google_logging_project_bucket_config.api_logs_bucket.name}/views/${google_logging_log_view.api_logs_view.name}?project=${var.project_id}"
  }
  sensitive = true
}

output "alert_policies" {
  description = "Created alert policies"
  value = {
    vectordb_error_alert           = google_monitoring_alert_policy.vectordb_error_alert.name
    vectordb_activity_alert        = google_monitoring_alert_policy.vectordb_activity_alert.name
    vectordb_slow_operations_alert = google_monitoring_alert_policy.vectordb_slow_operations_alert.name
  }
}

output "alert_policies_urls" {
  description = "Direct URLs to the alert policies"
  value = {
    vectordb_error_alert           = "https://console.cloud.google.com/monitoring/alerting/policies/${split("/", google_monitoring_alert_policy.vectordb_error_alert.id)[3]}?project=${var.project_id}"
    vectordb_activity_alert        = "https://console.cloud.google.com/monitoring/alerting/policies/${split("/", google_monitoring_alert_policy.vectordb_activity_alert.id)[3]}?project=${var.project_id}"
    vectordb_slow_operations_alert = "https://console.cloud.google.com/monitoring/alerting/policies/${split("/", google_monitoring_alert_policy.vectordb_slow_operations_alert.id)[3]}?project=${var.project_id}"
  }
  sensitive = true
}
