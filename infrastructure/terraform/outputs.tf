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
