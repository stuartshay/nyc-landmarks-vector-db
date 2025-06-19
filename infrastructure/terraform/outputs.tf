output "project_id" {
  description = "The GCP project ID"
  value       = local.project_id
}

output "region" {
  description = "The GCP region"
  value       = local.region
}

output "log_metrics" {
  description = "Created log-based metrics"
  value = {
    requests            = google_logging_metric.requests.name
    errors              = google_logging_metric.errors.name
    latency             = google_logging_metric.latency.name
    validation_warnings = google_logging_metric.validation_warnings.name
    vectordb_logs       = google_logging_metric.vectordb_logs.name
  }
}

output "dashboard_id" {
  description = "The monitoring dashboard ID"
  value       = google_monitoring_dashboard.api_dashboard.id
}

output "dashboard_name" {
  description = "The monitoring dashboard display name"
  value       = jsondecode(google_monitoring_dashboard.api_dashboard.dashboard_json)["displayName"]
}

output "dashboard_url" {
  description = "Direct URL to the monitoring dashboard"
  value       = "https://console.cloud.google.com/monitoring/dashboards/custom/${split("/", google_monitoring_dashboard.api_dashboard.id)[3]}?project=${var.project_id}"
}

output "uptime_check_id" {
  description = "The uptime check ID"
  value       = google_monitoring_uptime_check_config.health_check.uptime_check_id
}

output "uptime_check_name" {
  description = "The uptime check display name"
  value       = google_monitoring_uptime_check_config.health_check.display_name
}

output "vectordb_view_name" {
  description = "Logging view for vectordb logs"
  value       = google_logging_view.vectordb_logs_view.name
}
