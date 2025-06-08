variable "project_id" {
  type        = string
  description = "GCP project ID"
  default     = ""
}

variable "log_name_prefix" {
  type        = string
  description = "Prefix for application logs"
  default     = "nyc-landmarks-vector-db"
}
