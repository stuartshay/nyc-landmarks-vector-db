{
  "displayName": "NYC Landmarks Vector DB - API Monitoring Dashboard",
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
                  "filter": "metric.type=\"logging.googleapis.com/user/${log_name_prefix}.requests\" resource.type=\"cloud_run_revision\"",
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
              "filter": "metric.type=\"logging.googleapis.com/user/${log_name_prefix}.latency\" resource.type=\"cloud_run_revision\"",
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
                  "filter": "metric.type=\"logging.googleapis.com/user/${log_name_prefix}.requests\" resource.type=\"cloud_run_revision\"",
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
                  "filter": "metric.type=\"logging.googleapis.com/user/${log_name_prefix}.errors\" resource.type=\"cloud_run_revision\"",
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
                  "filter": "metric.type=\"logging.googleapis.com/user/${log_name_prefix}.latency\" resource.type=\"cloud_run_revision\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_PERCENTILE_95",
                    "crossSeriesReducer": "REDUCE_MAX",
                    "alignmentPeriod": "60s"
                  }
                },
                "unitOverride": "ms"
              },
              "plotType": "LINE",
              "targetAxis": "Y1"
            },
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"logging.googleapis.com/user/${log_name_prefix}.latency\" resource.type=\"cloud_run_revision\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_MEAN",
                    "crossSeriesReducer": "REDUCE_MEAN",
                    "alignmentPeriod": "60s"
                  }
                },
                "unitOverride": "ms"
              },
              "plotType": "LINE",
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
                  "filter": "metric.type=\"logging.googleapis.com/user/${log_name_prefix}.validation_warnings\" resource.type=\"cloud_run_revision\"",
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
