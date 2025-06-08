# Cloud Run Google Cloud Logging Setup

This document describes how the NYC Landmarks Vector DB Cloud Run instance is configured to use Google Cloud Logging.

## Configuration Overview

The GitHub Actions deployment workflow (`.github/workflows/deploy-gcp.yml`) has been configured to enable Google Cloud Logging for the Cloud Run instance.

### Environment Variables Added

The following environment variables are set in the Cloud Run deployment:

```yaml
env_vars: |
  LOG_PROVIDER=google           # Enables Google Cloud Logging
  LOG_LEVEL=INFO               # Sets log level to INFO
  LOG_NAME_PREFIX=nyc-landmarks-vector-db  # Prefix for logger names
  GCP_PROJECT_ID=${{ secrets.GCP_PROJECT_ID }}  # Required for GCP logging
```

### IAM Permissions

The deployment workflow automatically grants the necessary logging permissions to the Cloud Run service account:

- `roles/logging.logWriter` - Allows writing logs to Google Cloud Logging
- `roles/logging.viewer` - Allows viewing logs in Google Cloud Console

## Logger Name Structure

When deployed to Cloud Run, the application will create logs with hierarchical logger names:

```
nyc-landmarks-vector-db.{module_name}
```

Examples:

- `nyc-landmarks-vector-db.nyc_landmarks.api.query` - Query API logs
- `nyc-landmarks-vector-db.nyc_landmarks.api.chat` - Chat API logs
- `nyc-landmarks-vector-db.nyc_landmarks.utils.validation` - Validation logs

## Viewing Logs

### Google Cloud Console

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
1. Navigate to **Logging** → **Logs Explorer**
1. Use filters to view specific logs:

```
# All application logs
logName=~"nyc-landmarks-vector-db"

# API-specific logs
logName=~"nyc-landmarks-vector-db.nyc_landmarks.api"

# Validation warnings only
logName=~"nyc-landmarks-vector-db.nyc_landmarks.utils.validation" AND severity="WARNING"
```

### Command Line (gcloud CLI)

```bash
# View all application logs
gcloud logging read 'logName=~"nyc-landmarks-vector-db"' --project=YOUR_PROJECT_ID --limit=50

# View production environment logs only
gcloud logging read 'logName=~"nyc-landmarks-vector-db" AND jsonPayload.environment="production"' --project=YOUR_PROJECT_ID --limit=50

# View validation warnings
gcloud logging read 'logName=~"nyc-landmarks-vector-db.nyc_landmarks.utils.validation" AND severity="WARNING"' --project=YOUR_PROJECT_ID --limit=20

# View recent API logs in production
gcloud logging read 'logName=~"nyc-landmarks-vector-db.nyc_landmarks.api" AND jsonPayload.environment="production" AND timestamp>="2025-06-08T00:00:00Z"' --project=YOUR_PROJECT_ID --limit=30
```

## Log Features

### Structured Logging

All logs are automatically formatted as structured JSON with fields including:

- `timestamp` - Log timestamp
- `severity` - Log level (INFO, WARNING, ERROR, etc.)
- `message` - Log message
- `environment` - Application environment (production, staging, development)
- `request_id` - Unique request identifier
- `request_path` - API endpoint path
- `client_ip` - Client IP address
- `user_agent` - Client user agent

### Request Context Tracking

The application automatically tracks request context across all components:

- Unique request IDs for tracing requests through the system
- Client information (IP, User-Agent) for security monitoring
- Request timing and performance metrics

### Validation Logging

API input validation failures are logged as WARNING level messages with detailed information:

- Validation error type
- Client information
- Request details
- Security-relevant patterns (XSS attempts, injection attempts, etc.)

## Monitoring and Alerting

### Recommended Alerts

Set up Cloud Monitoring alerts for:

1. **High validation warning volume** - Multiple validation failures may indicate an attack
1. **Error rate increase** - Sudden increase in ERROR level logs
1. **Performance degradation** - Slow response times in performance logs

### Security Monitoring

Monitor validation logs for patterns indicating:

- XSS attempts (`validation_error="suspicious_content"`)
- Injection attempts (SQL, script injection patterns)
- Unusual client behavior (rapid requests, suspicious user agents)

## Troubleshooting

### Logs Not Appearing

1. Verify environment variables are set correctly in Cloud Run
1. Check IAM permissions for the service account
1. Ensure the application is using `LOG_PROVIDER=google`

### Permission Issues

If logs are not appearing, manually grant permissions:

```bash
# Get the service account email
gcloud run services describe nyc-landmarks-vector-db --region=us-east4 --format="value(spec.template.spec.serviceAccountName)"

# Grant logging permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/logging.logWriter"
```

## Related Documentation

- [Google Cloud Logging Enhancements](google_cloud_logging_enhancements.md)
- [Google Cloud Logging Filters](google_cloud_logging_filters.md)
- [API Validation Logging](api_validation_logging.md)
- [Validation Logging Fix Summary](validation_logging_fix_summary.md)
