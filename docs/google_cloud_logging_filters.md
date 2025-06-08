# Google Cloud Logging Filter Examples

## Logger Name Structure

The NYC Landmarks Vector DB uses a hierarchical logger naming structure:

```
{LOG_NAME_PREFIX}.{module_name}
```

Where:

- `LOG_NAME_PREFIX` = `nyc-landmarks-vector-db` (configurable via `.env`)
- `module_name` = Python module name (e.g., `nyc_landmarks.api.query`)

## Common Log Filtering Examples

### 1. All logs from the application

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db"' --project=velvety-byway-327718
```

### 2. API-specific logs only

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db.nyc_landmarks.api"' --project=velvety-byway-327718
```

### 3. Query API logs specifically

```bash
gcloud logging read 'logName="projects/velvety-byway-327718/logs/nyc-landmarks-vector-db.nyc_landmarks.api.query"' --project=velvety-byway-327718
```

### 4. Chat API logs specifically

```bash
gcloud logging read 'logName="projects/velvety-byway-327718/logs/nyc-landmarks-vector-db.nyc_landmarks.api.chat"' --project=velvety-byway-327718
```

### 5. Vector database logs

```bash
gcloud logging read 'logName=~"nyc-landmarks-vector-db.nyc_landmarks.vectordb"' --project=velvety-byway-327718
```

### 6. Main application logs

```bash
gcloud logging read 'logName="projects/velvety-byway-327718/logs/nyc-landmarks-vector-db.nyc_landmarks.main"' --project=velvety-byway-327718
```

## Google Cloud Console Filtering

In the Google Cloud Console, you can filter logs using the following queries:

### Basic filter by logger name prefix:

```
logName=~"nyc-landmarks-vector-db"
```

### Filter by specific module:

```
logName="projects/velvety-byway-327718/logs/nyc-landmarks-vector-db.nyc_landmarks.api.query"
```

### Combine with severity and time:

```
logName=~"nyc-landmarks-vector-db.nyc_landmarks.api" AND severity>=ERROR AND timestamp>="2025-06-08T00:00:00Z"
```

## Logger Name Examples

The following logger names are automatically generated:

| Module               | Logger Name                                                  |
| -------------------- | ------------------------------------------------------------ |
| Main Application     | `nyc-landmarks-vector-db.nyc_landmarks.main`                 |
| Query API            | `nyc-landmarks-vector-db.nyc_landmarks.api.query`            |
| Chat API             | `nyc-landmarks-vector-db.nyc_landmarks.api.chat`             |
| Pinecone Vector DB   | `nyc-landmarks-vector-db.nyc_landmarks.vectordb.pinecone_db` |
| OpenAI Service       | `nyc-landmarks-vector-db.nyc_landmarks.services.openai`      |
| Wikipedia Processing | `nyc-landmarks-vector-db.nyc_landmarks.processing.wikipedia` |

## Configuration

The logger name prefix can be configured via environment variable:

```env
LOG_NAME_PREFIX=nyc-landmarks-vector-db
```

This allows you to customize the logger naming for different environments (dev, staging, prod).
