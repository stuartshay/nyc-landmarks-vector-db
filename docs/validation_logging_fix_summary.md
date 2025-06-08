# Validation Logging Fix Summary

## Issue Description

User input validation failures were being logged with ERROR severity instead of WARNING severity in Google Cloud Logging, despite the validation code using `logger.warning()`.

## Root Cause

The issue was in the exception handling within the API endpoints. When `ValidationLogger` methods detected invalid input, they would:

1. Log a warning message using `logger.warning()`
1. Raise an `HTTPException` with status code 400

However, the API endpoints were wrapping the validation calls in try-catch blocks that were catching and re-logging the exceptions, potentially as errors.

## Solution

The exception handling in the API endpoints was corrected to properly handle `HTTPException` instances:

```python
try:
    # Validation code that may raise HTTPException
    ValidationLogger.validate_text_query(...)
    # ... other processing
except HTTPException:
    raise  # Re-raise without logging as error
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

The global exception handler in `main.py` was also updated to let `HTTPException` instances pass through to FastAPI's built-in handler.

## Verification

After implementing the fix, validation failures now correctly appear in Google Cloud Logging with:

- **Severity**: WARNING (not ERROR)
- **Logger**: `nyc-landmarks-vector-db.nyc_landmarks.utils.validation`
- **Structured logging**: Includes validation context and error details

### Test Results

- **Empty query**: ✅ Logged as WARNING
- **Suspicious content**: ✅ Logged as WARNING
- **Invalid characters**: ✅ Logged as WARNING
- **Both query and chat endpoints**: ✅ Working correctly

## Log Filtering

Validation warnings can be filtered in Google Cloud Logging using:

```
logName="projects/PROJECT_ID/logs/nyc-landmarks-vector-db.nyc_landmarks.utils.validation"
AND severity="WARNING"
```

## Files Modified

- `nyc_landmarks/api/query.py` - Exception handling
- `nyc_landmarks/api/chat.py` - Exception handling
- `nyc_landmarks/main.py` - Global exception handler
- `nyc_landmarks/utils/validation.py` - Validation logic and warning logging

## Status

✅ **RESOLVED**: User input validation failures are now correctly logged as warnings (severity=WARNING) in Google Cloud Logging.
