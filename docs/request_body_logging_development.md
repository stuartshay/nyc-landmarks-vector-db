# Request Body Logging - Development Guide

## Development Mode Features

Since you're in the development stage, the request body logging middleware has been enhanced with several development-friendly features:

### Configuration Options

#### Environment Variables

1. **`DEVELOPMENT_MODE`** (default: `"true"`)

   - Enables development-specific features
   - Includes timing information, additional headers, and debug logging
   - Set to `"false"` for production deployment

1. **`LOG_ALL_POST_REQUESTS`** (default: `"false"`)

   - When `true`, logs ALL POST requests regardless of endpoint
   - Useful for API exploration and discovering new endpoints
   - Only works when `DEVELOPMENT_MODE=true`

### Development Enhancements

#### 1. Increased Limits for Better Debugging

- **Body size limit**: Increased from 2KB to **10KB**
- **String truncation**: Increased from 500 to **1000 characters**
- More complete request bodies in logs for thorough debugging

#### 2. Enhanced Client Information

In development mode, additional headers are logged:

- `accept`
- `accept-encoding`
- `x-request-id`
- `origin`

#### 3. Request Timing Information

Development mode includes timing logs with:

- Processing time in milliseconds
- Response status code
- Queryable via `jsonPayload.metric_type: 'request_timing'`

#### 4. Request Skipping Logs

When POST requests are skipped (not configured for logging), development mode logs:

- Which endpoints were skipped
- Reason for skipping
- Queryable via `jsonPayload.metric_type: 'request_skipped'`

### Usage Examples

#### Basic Development Setup

```bash
# In your .env file or environment
export DEVELOPMENT_MODE=true
export LOG_ALL_POST_REQUESTS=false  # Only log configured endpoints
```

#### Log All POST Requests (Exploration Mode)

```bash
export DEVELOPMENT_MODE=true
export LOG_ALL_POST_REQUESTS=true   # Log ALL POST endpoints
```

#### Google Cloud Logging Queries

```bash
# View all request bodies
jsonPayload.metric_type="request_body"

# View timing information
jsonPayload.metric_type="request_timing"

# View skipped requests
jsonPayload.metric_type="request_skipped"

# View requests with long processing times
jsonPayload.metric_type="request_timing" AND jsonPayload.processing_time_ms > 1000

# View all development logs
jsonPayload.metric_type=("request_body" OR "request_timing" OR "request_skipped")
```

### Testing

Use the provided test script to validate development features:

```bash
python scripts/test_development_logging.py
```

This script:

- Tests all configured endpoints
- Includes development headers
- Demonstrates timing and logging features
- Provides example log queries

### Transitioning to Production

When ready for production:

1. Set environment variables:

   ```bash
   export DEVELOPMENT_MODE=false
   export LOG_ALL_POST_REQUESTS=false
   ```

1. Production optimizations automatically apply:

   - Reduced body size limits (2KB)
   - Shorter string truncation (500 chars)
   - Minimal header logging
   - No timing overhead
   - No debug logging for skipped requests

### Development Benefits

- **Complete visibility**: See exactly what's being sent to your API
- **Performance insights**: Identify slow endpoints early
- **API discovery**: Find all POST endpoints being used
- **Debug assistance**: Rich context for troubleshooting
- **Request correlation**: Track requests with IDs and timing

This setup gives you maximum observability during development while maintaining the ability to optimize for production deployment.
