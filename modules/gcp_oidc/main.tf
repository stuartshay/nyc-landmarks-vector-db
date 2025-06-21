variable "project_id" {
  type = string
}

resource "google_iam_workload_identity_pool" "tfc" {
  project                   = var.project_id
  workload_identity_pool_id = "tfc-pool"
  display_name              = "Terraform Cloud"
  description               = "OIDC pool for Terraform Cloud"
}

resource "google_iam_workload_identity_pool_provider" "tfc" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.tfc.workload_identity_pool_id
  workload_identity_pool_provider_id = "terraform-cloud"
  display_name                       = "Terraform Cloud"
  description                        = "OIDC provider for Terraform Cloud"

  attribute_mapping = {
    "google.subject" = "assertion.sub"
  }

  oidc {
    issuer_uri = "https://app.terraform.io"
  }
}

output "provider_name" {
  value = google_iam_workload_identity_pool_provider.tfc.name
}
