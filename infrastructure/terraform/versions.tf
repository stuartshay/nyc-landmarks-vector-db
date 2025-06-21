terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  cloud {
    organization = "nyc-landmarks"
    workspaces {
      name = "nyc-landmarks-vector-db"
    }
  }
}
