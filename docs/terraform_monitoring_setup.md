# Terraform Monitoring Setup

This configuration provisions monitoring resources for the NYC Landmarks Vector DB project using the Google Cloud provider.

## Usage

1. Export the target project ID or pass it as a variable:
   ```bash
   export GCP_PROJECT_ID="your-gcp-project"
   ```
   or set `-var project_id=your-gcp-project` when applying.
1. Ensure the service account running Terraform has permissions to manage log-based metrics and dashboards (`roles/logging.configWriter` and `roles/monitoring.editor`).
1. Apply the configuration:
   ```bash
   cd infrastructure/terraform
   terraform init
   terraform apply
   ```

The module creates log-based metrics:

- `nyc-landmarks-vector-db.requests`
- `nyc-landmarks-vector-db.errors`
- `nyc-landmarks-vector-db.latency`
- `nyc-landmarks-vector-db.validation_warnings`

A monitoring dashboard defined in `dashboard.json` will also be deployed.
