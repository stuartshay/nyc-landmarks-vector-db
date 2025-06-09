# Health Monitoring Setup for NYC Landmarks Vector DB

This document describes the health monitoring setup for the NYC Landmarks Vector DB service, including the GCP Dashboard widgets and uptime checks.

## Overview

The health monitoring system consists of:

1. **Uptime Check**: A GCP Monitoring uptime check that monitors the `/health` endpoint
1. **Dashboard Widgets**: Two new widgets in the monitoring dashboard showing service health status
1. **Health Endpoint**: The service exposes health information via HTTP endpoint

## Endpoints

### Primary Health Endpoint

- **URL**: `https://vector-db.coredatastore.com/health`
- **Method**: GET
- **Expected Response**:
  ```json
  {
    "status": "healthy",
    "services": {
      "pinecone": {
        "status": "healthy",
        "index": "nyc-landmarks",
        "vector_count": 36301,
        "timestamp": 1749443580.1957765
      }
    }
  }
  ```

### Cloud Run Direct Endpoint

- **URL**: `https://nyc-landmarks-vector-db-1052843754581.us-east4.run.app/health`
- **Method**: GET
- **Same response format as primary endpoint**

## GCP Monitoring Configuration

### Uptime Check Configuration

The Terraform configuration includes an uptime check with the following settings:

```terraform
resource "google_monitoring_uptime_check_config" "health_check" {
  display_name = "NYC Landmarks Vector DB Health Check"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path           = "/health"
    port           = "443"
    use_ssl        = true
    validate_ssl   = true
    request_method = "GET"

    accepted_response_status_codes {
      status_class = "STATUS_CLASS_2XX"
    }
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = local.project_id
      host       = "vector-db.coredatastore.com"
    }
  }

  content_matchers {
    content = "\"status\": \"healthy\""
    matcher = "CONTAINS_STRING"
  }

  checker_type = "STATIC_IP_CHECKERS"
}
```

### Key Features:

- **Frequency**: Checks every 60 seconds
- **Timeout**: 10 seconds per check
- **SSL Validation**: Ensures secure connection
- **Content Validation**: Verifies the response contains `"status": "healthy"`
- **Global Checking**: Uses GCP's global static IP checkers

## Dashboard Widgets

### 1. Service Health Status (Scorecard)

- **Type**: Scorecard with thresholds
- **Metric**: `monitoring.googleapis.com/uptime_check/check_passed`
- **Display**: Current uptime percentage with color-coded status
- **Thresholds**:
  - 🟢 Green: Above 95% uptime
  - 🟡 Yellow: 90-95% uptime
  - 🔴 Red: Below 90% uptime

### 2. Service Uptime (24h) (Line Chart)

- **Type**: Line chart
- **Metric**: `monitoring.googleapis.com/uptime_check/check_passed`
- **Display**: 24-hour trend of service uptime percentage
- **Aggregation**: 5-minute intervals

## Testing

### Manual Testing

Use the provided test script to verify health endpoints:

```bash
cd infrastructure
./test_health_endpoint.sh
```

This script tests both endpoints and validates:

- HTTP response codes (expects 200)
- Response content contains expected health status
- JSON format validation

### Infrastructure Validation

Run the health check script to validate the monitoring setup:

```bash
cd infrastructure
./health_check.sh
```

This validates:

- Terraform configuration includes uptime check resources
- Dashboard template includes health monitoring widgets
- All required files are present and properly configured

## Deployment

### Deploy the Updated Dashboard

```bash
cd infrastructure
./deploy_dashboard.sh apply
```

### Verify Deployment

1. Check that the uptime check is created in GCP Console:

   - Go to Monitoring > Uptime checks
   - Look for "NYC Landmarks Vector DB Health Check"

1. Verify dashboard widgets:

   - Go to Monitoring > Dashboards
   - Open "NYC Landmarks Vector DB - API Monitoring Dashboard"
   - Confirm the first two widgets show service health status

## Monitoring and Alerts

### Available Metrics

- `monitoring.googleapis.com/uptime_check/check_passed`: Boolean metric indicating if the check passed
- `monitoring.googleapis.com/uptime_check/request_latency`: Latency of health check requests

### Recommended Alerts

Consider setting up alerting policies for:

- Uptime drops below 95% over 5 minutes
- Health check fails for 3 consecutive checks
- Response latency exceeds 5 seconds

### Creating Alerts (Optional)

```bash
# Example alert policy can be added to Terraform
resource "google_monitoring_alert_policy" "health_check_failure" {
  display_name = "Service Health Check Failure"
  combiner     = "OR"

  conditions {
    display_name = "Uptime check failure"

    condition_threshold {
      filter          = "resource.type=\"uptime_url\" AND metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\""
      duration        = "300s"
      comparison      = "COMPARISON_EQUAL"
      threshold_value = 0
    }
  }

  notification_channels = [
    # Add your notification channels here
  ]
}
```

## Troubleshooting

### Common Issues

1. **Uptime Check Not Working**

   - Verify the health endpoint is accessible from external networks
   - Check SSL certificate validity
   - Ensure the response contains the expected `"status": "healthy"` string

1. **Dashboard Not Showing Data**

   - Wait 5-10 minutes after deployment for metrics to populate
   - Verify the uptime check is running in GCP Console
   - Check the metric filter in dashboard configuration

1. **Health Endpoint Returns Errors**

   - Check Pinecone connection and authentication
   - Verify service logs for application errors
   - Test endpoint manually with curl

### Debug Commands

```bash
# Test health endpoint manually
curl -X GET "https://vector-db.coredatastore.com/health" -H "accept: application/json"

# Check uptime check status in GCP
gcloud monitoring uptime list

# View recent uptime check results
gcloud logging read "resource.type=uptime_url" --limit=10
```

## Related Documentation

- [GCP Monitoring Setup](gcp_setup.md)
- [Dashboard Configuration](terraform_monitoring_setup.md)
- [API Response Handling](api_response_handling.md)
