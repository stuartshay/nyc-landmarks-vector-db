variable "project_id" {
  type        = string
  description = "GCP project ID"
  default     = ""
}

variable "credentials_file" {
  type        = string
  description = "Path to the GCP service account key file"
  default     = "../../.gcp/service-account-key.json"
}

variable "region" {
  type        = string
  description = "GCP region for resources"
  default     = "us-central1"
}

variable "log_name_prefix" {
  type        = string
  description = "Prefix for application logs"
  default     = "nyc-landmarks-vector-db"
}

variable "notification_channels" {
  type        = list(string)
  description = "List of notification channel IDs for alerts"
  default     = []
}

variable "api_health_check_url" {
  type        = string
  description = "URL to check for API health"
  default     = "https://nyc-landmarks-api.example.com/health"
}

variable "uptime_check_host" {
  type        = string
  description = "Host for uptime check monitoring"
  default     = "nyc-landmarks-api.example.com"
}
