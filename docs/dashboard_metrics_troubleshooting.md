# Dashboard Metrics Troubleshooting Guide

## Issue: Dashboard Showing "0" for Service Health Status

### Current Status

- ✅ Uptime check is created and configured correctly
- ✅ Health endpoints are responding (both return `"status": "healthy"`)
- ✅ Dashboard has been updated with correct filters
- ❓ Dashboard widgets showing "0" instead of actual uptime data

### Root Cause Analysis

The issue appears to be related to metrics data availability and timing:

1. **Metric Generation Delay**: Uptime check metrics typically take 5-15 minutes to appear in monitoring dashboards after creation
1. **Project Scope**: The uptime check is in project `velvety-byway-327718` but dashboard is in project `1052843754581`
1. **Alignment Period**: May need longer periods for initial data aggregation

### Applied Fixes

1. **Updated Dashboard Filters**: Removed project_id filter to allow cross-project metric access
1. **Increased Alignment Period**: Changed from 300s to 600s for better data aggregation
1. **Verified Uptime Check Configuration**: Confirmed it's monitoring the correct endpoint

### Current Configuration

**Uptime Check:**

- Name: "NYC Landmarks Vector DB Health Check"
- Endpoint: `https://vector-db.coredatastore.com/health`
- Frequency: Every 60 seconds
- Content Validation: Checks for `"status": "healthy"`

**Dashboard Widgets:**

1. Service Health Status (Scorecard)
1. Service Uptime (24h) (Line Chart)

**Metric Filter:**

```
metric.type="monitoring.googleapis.com/uptime_check/check_passed"
resource.type="uptime_url"
resource.label.host="vector-db.coredatastore.com"
```

### Next Steps

1. **Wait for Data**: Give the system 10-15 minutes to accumulate metric data
1. **Refresh Dashboard**: Hard refresh the GCP Console dashboard page
1. **Verify in GCP Console**: Check the uptime check status directly in Monitoring console

### Verification Commands

```bash
# Check uptime check status
gcloud monitoring uptime list-configs --project=velvety-byway-327718

# Test health endpoints
./test_health_endpoint.sh

# Verify dashboard deployment
terraform output dashboard_id
```

### Expected Timeline

- **Immediate**: Uptime check starts running
- **2-5 minutes**: First metric data points generated
- **5-15 minutes**: Dashboard widgets start showing data
- **1 hour**: Full historical data available for trends

### Manual Verification

1. Go to GCP Console → Monitoring → Uptime checks
1. Find "NYC Landmarks Vector DB Health Check"
1. Click to view details and recent results
1. Should show successful checks every 60 seconds

### Alternative: Quick Status Check

If dashboard data is delayed, you can manually verify service health:

```bash
# Direct endpoint test
curl -X GET "https://vector-db.coredatastore.com/health" -H "accept: application/json"

# Expected response:
# {"status":"healthy","services":{"pinecone":{"status":"healthy",...}}}
```

______________________________________________________________________

**Last Updated**: June 9, 2025
**Status**: Dashboard updated, waiting for metric data to populate
