locals {
  project_id = var.project_id != "" ? var.project_id : env("GCP_PROJECT_ID")
}

provider "google" {
  project = local.project_id
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

resource "google_monitoring_dashboard" "api_dashboard" {
  dashboard_json = file("${path.module}/dashboard.json")
}
