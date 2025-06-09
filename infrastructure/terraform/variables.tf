variable "project_id" {
  type        = string
  description = "GCP project ID for NYC landmarks vector database"
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
