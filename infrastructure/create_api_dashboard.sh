#!/bin/bash
# DEPRECATED: Use Terraform in infrastructure/terraform instead.

# Create the infrastructure directory if it doesn't exist
mkdir -p infrastructure

# Generate dashboard.json using a here document
cat > infrastructure/dashboard.json <<EOF
{
  "displayName": "API Monitoring Starter Dashboard",
  "gridLayout": {
    "columns": "2",
    "widgets": [
      {
        "title": "Total Request Count",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\\"logging.googleapis.com/user/nyc-landmarks-vector-db.requests\\" resource.type=\\"cloud_run_revision\\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_SUM",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "alignmentPeriod": "60s"
                  }
                },
                "unitOverride": "1"
              },
              "plotType": "STACKED_BAR"
            }
          ],
          "timeshiftDuration": "0s",
          "yAxis": {
            "label": "count",
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "Average Latency",
        "scorecard": {
          "timeSeriesQuery": {
            "timeSeriesFilter": {
              "filter": "metric.type=\\"logging.googleapis.com/user/nyc-landmarks-vector-db.latency\\" resource.type=\\"cloud_run_revision\\"",
              "aggregation": {
                "perSeriesAligner": "ALIGN_MEAN",
                "crossSeriesReducer": "REDUCE_MEAN",
                "alignmentPeriod": "60s"
              }
            },
            "unitOverride": "ms"
          },
          "thresholds": []
        }
      },
      {
        "title": "Request Rate",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\\"logging.googleapis.com/user/nyc-landmarks-vector-db.requests\\" resource.type=\\"cloud_run_revision\\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_RATE",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "alignmentPeriod": "60s"
                  }
                },
                "unitOverride": "1/s"
              },
              "plotType": "LINE"
            }
          ],
          "timeshiftDuration": "0s",
          "yAxis": {
            "label": "requests/s",
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "Error Rate (5xx)",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\\"logging.googleapis.com/user/nyc-landmarks-vector-db.errors\\" resource.type=\\"cloud_run_revision\\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_RATE",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "alignmentPeriod": "60s"
                  }
                },
                "unitOverride": "1/s"
              },
              "plotType": "LINE"
            }
          ],
          "timeshiftDuration": "0s",
          "yAxis": {
            "label": "errors/s",
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "Request Latency (Avg and 95th Percentile)",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\\"logging.googleapis.com/user/nyc-landmarks-vector-db.latency\\" resource.type=\\"cloud_run_revision\\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_PERCENTILE_95",
                    "crossSeriesReducer": "REDUCE_MAX",
                    "alignmentPeriod": "60s"
                  }
                },
                "unitOverride": "ms",
                "plotType": "LINE"
              },
              "targetAxis": "Y1"
            },
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\\"logging.googleapis.com/user/nyc-landmarks-vector-db.latency\\" resource.type=\\"cloud_run_revision\\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_MEAN",
                    "crossSeriesReducer": "REDUCE_MEAN",
                    "alignmentPeriod": "60s"
                  }
                },
                "unitOverride": "ms",
                "plotType": "LINE"
              },
              "targetAxis": "Y1"
            }
          ],
          "timeshiftDuration": "0s",
          "yAxis": {
            "label": "ms",
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "Validation Warning Rate",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\\"logging.googleapis.com/user/nyc-landmarks-vector-db.validation_warnings\\" resource.type=\\"cloud_run_revision\\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_RATE",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "alignmentPeriod": "60s"
                  }
                },
                "unitOverride": "1/s"
              },
              "plotType": "LINE"
            }
          ],
          "timeshiftDuration": "0s",
          "yAxis": {
            "label": "warnings/s",
            "scale": "LINEAR"
          }
        }
      }
    ]
  }
}
EOF

# Print instructions to the user
echo "--------------------------------------------------------------------------------"
echo "API Monitoring Dashboard Script"
echo "--------------------------------------------------------------------------------"
echo "This script has generated a dashboard.json file in the 'infrastructure' directory."
echo ""
echo "Prerequisites:"
echo "  - Google Cloud SDK ('gcloud') installed and configured."
echo "  - Authenticated to GCP with an account that has permissions to create"
echo "    Log-based Metrics and Monitoring Dashboards in the target project."
echo "  - The target Google Cloud Project ID must be correctly set where 'YOUR_PROJECT_ID' is indicated."
echo ""
echo "IMPORTANT: BEFORE YOU PROCEED, YOU MUST:"
echo ""
echo "1. Replace 'YOUR_PROJECT_ID' with your actual Google Cloud Project ID in:"
echo "   - This script (if you plan to re-run it for parameterization in the future)"
echo "   - The Log-based Metric filters below."
echo "   - The gcloud command below."
echo ""
echo "2. Create the following Log-based Metrics in Google Cloud Logging:"
echo "   Go to Logging -> Log-based Metrics -> Create Metric"
echo ""
echo "   Metric 1: Total Requests"
echo "     - Name: nyc-landmarks-vector-db.requests"
echo "     - Description: Counts all successful API requests based on custom logs."
echo "     - Metric Type: Counter"
echo "     - Filter: resource.type=\\"cloud_run_revision\\" AND logName=\\"projects/YOUR_PROJECT_ID/logs/nyc-landmarks-vector-db.nyc_landmarks.api.middleware\\" AND jsonPayload.metric_type=\\"performance\\""
echo "     - Units: 1"
echo ""
echo "   Metric 2: Errors"
echo "     - Name: nyc-landmarks-vector-db.errors"
echo "     - Description: Counts 5xx server errors based on custom logs."
echo "     - Metric Type: Counter"
echo "     - Filter: resource.type=\\"cloud_run_revision\\" AND logName=\\"projects/YOUR_PROJECT_ID/logs/nyc-landmarks-vector-db.nyc_landmarks.api.middleware\\" AND jsonPayload.metric_type=\\"performance\\" AND jsonPayload.status_code>=500"
echo "     - Units: 1"
echo ""
echo "   Metric 3: Latency"
echo "     - Name: nyc-landmarks-vector-db.latency"
echo "     - Description: Tracks API request latency from custom logs."
echo "     - Metric Type: Distribution"
echo "     - Field name: jsonPayload.duration_ms"
echo "     - Filter: resource.type=\\"cloud_run_revision\\" AND logName=\\"projects/YOUR_PROJECT_ID/logs/nyc-landmarks-vector-db.nyc_landmarks.api.middleware\\" AND jsonPayload.metric_type=\\"performance\\" AND jsonPayload.duration_ms>=0"
echo "     - Units: ms"
echo ""
echo "   Metric 4: Validation Warnings"
echo "     - Name: nyc-landmarks-vector-db.validation_warnings"
echo "     - Description: Counts validation warnings from application logs."
echo "     - Metric Type: Counter"
echo "     - Filter: resource.type=\\"cloud_run_revision\\" AND logName=\\"projects/YOUR_PROJECT_ID/logs/nyc-landmarks-vector-db.nyc_landmarks.utils.validation\\" AND severity=\\"WARNING\\""
echo "     - Units: 1"
echo ""
echo "--------------------------------------------------------------------------------"
echo "Once the log-based metrics are created and propagating, run the following command"
echo "to create the dashboard in your Google Cloud project:"
echo ""
echo "gcloud monitoring dashboards create --config-from-file=infrastructure/dashboard.json --project=YOUR_PROJECT_ID"
echo ""
echo "Customization:"
echo "  - You can edit the 'infrastructure/dashboard.json' file to change widget types,"
echo "    add more widgets, or modify MQL queries after it's generated and before running"
echo "    the 'gcloud dashboards create' command."
echo "  - For more advanced visualizations or different metrics, you might need to create"
echo "    additional log-based metrics in GCP."
echo ""
echo "--------------------------------------------------------------------------------"

# Make the script executable
# Note: This chmod command is inside the script itself.
# It ensures that if the script is distributed and then run, it makes itself executable.
# However, for the very first execution after creation by this tool,
# chmod +x infrastructure/create_api_dashboard.sh needs to be run externally.
chmod +x infrastructure/create_api_dashboard.sh

echo "Script infrastructure/create_api_dashboard.sh created and made executable."
echo "File infrastructure/dashboard.json has been generated."
