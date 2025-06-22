# Terraform Monitoring Setup

This configuration provisions monitoring resources for the NYC Landmarks Vector DB project using the Google Cloud provider.

## Quick Start

### First-Time Setup

1. **Automated setup** (recommended):

   ```bash
   cd infrastructure
   ./setup_terraform.sh
   ```

1. **Manual setup**:

   ```bash
   cd infrastructure/terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your project details
   terraform init
   terraform plan
   ```

### Deploy Dashboard

1. **Using deployment script**:

   ```bash
   cd infrastructure
   ./deploy_dashboard.sh apply
   ```

1. **Manual deployment**:

   ```bash
   cd infrastructure/terraform
   terraform apply
   ```

## Prerequisites

- Terraform >= 1.0 installed
- Service account key JSON stored at `.gcp/service-account-key.json` with permissions. Load the file contents into the `GOOGLE_CREDENTIALS` variable for Terraform Cloud or CLI:
  - `roles/logging.configWriter`
  - `roles/monitoring.editor`
  - `roles/monitoring.metricWriter`
- GCP project with enabled APIs:
  - Cloud Logging API
  - Cloud Monitoring API
  - Cloud Resource Manager API

## Configuration

The setup automatically detects your GCP project from the service account key file. You can override settings in `terraform.tfvars`:

```hcl
project_id = "your-gcp-project-id"
GOOGLE_CREDENTIALS = file("../../.gcp/service-account-key.json")
region = "us-central1"
log_name_prefix = "nyc-landmarks-vector-db"
```

## Resources Created

The module creates log-based metrics:

- `{log_name_prefix}.requests` - Total API requests
- `{log_name_prefix}.errors` - HTTP 5xx errors
- `{log_name_prefix}.latency` - Request duration
- `{log_name_prefix}.validation_warnings` - Validation warnings
- `{log_name_prefix}.vectordb_logs` - Vector database log count

The configuration also creates a dedicated log bucket and view named
`vectordb-view` to surface vector database logs in the Cloud Console.
You can access it from **Logs Explorer** under the bucket `vectordb-logs`.

A comprehensive monitoring dashboard with widgets for:

- Request count and rate
- Error rate
- Latency (average and 95th percentile)
- Validation warning rate
- Vector database activity and log volume
- Vector database operations (24-hour distribution)
- Vector database log distribution by severity

### Vector Database Monitoring

The dashboard includes several dedicated widgets for monitoring vector database operations:

1. **Vector Database Activity (Scorecard)**:

   - Real-time activity measurement for vector database operations
   - Includes a spark line to show recent trends
   - Yellow threshold alert when activity drops below expected levels

1. **Vector Database Log Volume (Line Chart)**:

   - Rate of vector database logs over time
   - Useful for identifying usage patterns and potential issues
   - Helps correlate vector database activity with API requests

1. **Vector Database Operations (24h)**:

   - Hourly count of vector database operations over a 24-hour period
   - Stacked bar chart format for easy visualization of busy periods
   - Useful for capacity planning and identifying usage patterns

1. **Vector Database Log Distribution (Pie Chart)**:

   - Distribution of logs by severity level (INFO, WARNING, ERROR)
   - Helps quickly identify if errors are occurring in vector database operations
   - Provides insight into the overall health of the vector database system

These widgets help monitor the health, performance, and usage patterns of the vector database system, making it easier to identify issues, plan capacity, and ensure optimal performance.

### Log Explorer Queries for Vector DB Logs

To view logs captured by the `vectordb_logs` metric, open **Logs Explorer** and
run queries such as:

```text
logName=~"${LOG_NAME_PREFIX}.nyc_landmarks.vectordb"
```

Or filter using the dedicated view:

```text
resource.type="logging_bucket" AND resource.labels.bucket_name="vectordb-logs"
```

#### Advanced Vector Database Query Examples

For more targeted analysis, you can use these example queries:

**Query for vector database errors:**

```
logName=~"${LOG_NAME_PREFIX}.nyc_landmarks.vectordb" severity>=ERROR
```

**Query for specific vector operations (like query or upsert):**

```
logName=~"${LOG_NAME_PREFIX}.nyc_landmarks.vectordb" jsonPayload.operation="query"
```

**Query for slow vector operations (taking more than 500ms):**

```
logName=~"${LOG_NAME_PREFIX}.nyc_landmarks.vectordb" jsonPayload.duration_ms>500
```

**Query for operations on a specific namespace:**

```
logName=~"${LOG_NAME_PREFIX}.nyc_landmarks.vectordb" jsonPayload.namespace="wikipedia"
```

These queries can help troubleshoot issues with vector database operations, identify performance bottlenecks, and analyze usage patterns.

## Interpreting Vector Database Metrics

### Activity Patterns

- **Normal Pattern**: Regular spikes during business hours with lower activity overnight
- **Warning Signs**: Sudden drops in activity or prolonged periods of zero activity
- **Action Items**: Investigate system health if activity drops unexpectedly

### Log Volume

- **Normal Pattern**: Consistent with application usage patterns
- **Warning Signs**: Sudden spikes in log volume may indicate errors or performance issues
- **Action Items**: Check for error severity distribution and correlate with API performance

### Error Distribution

- **Normal Ratio**: Primarily INFO logs with minimal WARNING and ERROR logs
- **Warning Signs**: Increasing proportion of WARNING or ERROR logs
- **Action Items**: Review error logs and address underlying issues

## Scripts

- `setup_terraform.sh`: First-time setup with validation
- `deploy_dashboard.sh`: Deploy, plan, destroy, and status commands

## Dashboard Access

After deployment, access your dashboard at:

```
https://console.cloud.google.com/monitoring/dashboards?project=YOUR_PROJECT_ID
```

View resource details:

```bash
cd infrastructure/terraform
terraform output
```

For detailed instructions, see `infrastructure/README.md`.
