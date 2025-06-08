# Google Cloud Logging Configuration Summary

## Changes Made to GitHub Actions Workflow

The `.github/workflows/deploy-gcp.yml` file has been updated to configure the Cloud Run instance to use Google Cloud Logging.

### Key Changes

1. **Environment Variables Added:**

   - `LOG_PROVIDER=google` - Enables Google Cloud Logging
   - `LOG_LEVEL=INFO` - Sets appropriate log level for production
   - `LOG_NAME_PREFIX=nyc-landmarks-vector-db` - Sets the logger name prefix for filtering
   - `GCP_PROJECT_ID=${{ secrets.GCP_PROJECT_ID }}` - Required for GCP logging client

1. **IAM Permissions Setup:**

   - Added step to grant `roles/logging.logWriter` to the Cloud Run service account
   - Added step to grant `roles/logging.viewer` to the Cloud Run service account
   - Uses the default compute service account for Cloud Run

1. **Verification Step:**

   - Added step to display logging verification commands after deployment
   - Provides ready-to-use gcloud commands for viewing logs

## How It Works

When the Cloud Run instance starts:

1. **Environment Detection:** The application reads `LOG_PROVIDER=google` and switches to Google Cloud Logging
1. **Logger Setup:** Creates hierarchical logger names with the prefix `nyc-landmarks-vector-db`
1. **Structured Logging:** All logs are formatted as structured JSON for better querying
1. **Request Tracking:** Automatic request context propagation with unique request IDs

## Benefits

### For Development Team

- **Centralized Logging:** All application logs in one place in Google Cloud Console
- **Structured Data:** JSON logs with consistent fields for easy querying
- **Request Tracing:** Follow requests through the entire application flow

### for Operations Team

- **Real-time Monitoring:** Live log streaming in Google Cloud Console
- **Advanced Filtering:** Filter by logger name, severity, timestamp, custom fields
- **Integration:** Easy integration with Cloud Monitoring for alerts

### For Security Team

- **Attack Detection:** Automatic logging of validation failures and suspicious content
- **Audit Trail:** Complete record of all API requests with client information
- **Pattern Analysis:** Structured logs enable detection of attack patterns

## Usage Examples

### View All Application Logs

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db"' --project=YOUR_PROJECT_ID --limit=50
```

### View Validation Warnings (Security Events)

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db.nyc_landmarks.utils.validation" AND severity="WARNING"' --project=YOUR_PROJECT_ID --limit=20
```

### View API Performance Logs

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db.nyc_landmarks.api" AND jsonPayload.duration_ms>500' --project=YOUR_PROJECT_ID --limit=10
```

### Filter by Request ID

```bash
gcloud logging read 'jsonPayload.request_id="req-12345"' --project=YOUR_PROJECT_ID
```

## Related Documentation

- [Cloud Run Logging Setup](cloud_run_logging_setup.md) - Detailed setup documentation
- [Google Cloud Logging Enhancements](google_cloud_logging_enhancements.md) - Feature overview
- [Google Cloud Logging Filters](google_cloud_logging_filters.md) - Query examples
- [API Validation Logging](api_validation_logging.md) - Security logging details

## Next Steps

After the next deployment:

1. **Verify Logs:** Check that logs appear in Google Cloud Console
1. **Test Filtering:** Try the provided gcloud commands to filter logs
1. **Set Up Alerts:** Configure Cloud Monitoring alerts for validation warnings
1. **Security Monitoring:** Monitor validation logs for attack patterns

The Google Cloud Logging integration is now fully configured and will be active on the next deployment to Cloud Run.
