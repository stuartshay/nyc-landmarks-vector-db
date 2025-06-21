{
  "displayName": "NYC Landmarks Vector DB - API Monitoring Dashboard",
  "gridLayout": {
    "columns": "2",
    "widgets": [
      {
        "title": "Service Health Status (Uptime Check)",
        "scorecard": {
          "timeSeriesQuery": {
            "timeSeriesFilter": {
              "filter": "metric.type=\"monitoring.googleapis.com/uptime_check/request_latency\" resource.type=\"uptime_url\"",
              "aggregation": {
                "perSeriesAligner": "ALIGN_MEAN",
                "crossSeriesReducer": "REDUCE_MEAN",
                "alignmentPeriod": "300s"
              }
            },
            "unitOverride": "ms"
          },
          "sparkChartView": {
            "sparkChartType": "SPARK_LINE"
          },
          "thresholds": [
            {
              "value": 5000,
              "color": "RED",
              "direction": "ABOVE"
            }
          ]
        }
      },
      {
        "title": "Service Health Status (via Logs)",
        "scorecard": {
          "timeSeriesQuery": {
            "timeSeriesFilter": {
              "filter": "metric.type=\"logging.googleapis.com/user/${log_name_prefix}.requests\" resource.type=\"cloud_run_revision\"",
              "aggregation": {
                "perSeriesAligner": "ALIGN_RATE",
                "crossSeriesReducer": "REDUCE_SUM",
                "alignmentPeriod": "300s"
              }
            },
            "unitOverride": "1/s"
          },
          "sparkChartView": {
            "sparkChartType": "SPARK_LINE"
          },
          "thresholds": [
            {
              "value": 0.1,
              "color": "RED",
              "direction": "BELOW"
            }
          ]
        }
      },
      {
        "title": "Service Activity (Request Rate)",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"logging.googleapis.com/user/${log_name_prefix}.requests\" resource.type=\"cloud_run_revision\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_RATE",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "alignmentPeriod": "300s"
                  }
                },
                "unitOverride": "1/s"
              },
              "plotType": "LINE"
            }
          ],
          "timeshiftDuration": "0s",
          "yAxis": {
            "label": "Requests/s",
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "Service Uptime (24h)",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"monitoring.googleapis.com/uptime_check/request_latency\" resource.type=\"uptime_url\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_MEAN",
                    "crossSeriesReducer": "REDUCE_MEAN",
                    "alignmentPeriod": "3600s"
                  }
                },
                "unitOverride": "ms"
              },
              "plotType": "LINE"
            }
          ],
          "timeshiftDuration": "0s",
          "yAxis": {
            "label": "Latency (ms)",
            "scale": "LINEAR"
          }
        }
      },
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
      },
      {
        "title": "Vector Database Activity",
        "scorecard": {
          "timeSeriesQuery": {
            "timeSeriesFilter": {
              "filter": "metric.type=\"logging.googleapis.com/user/${log_name_prefix}.vectordb_logs\"",
              "aggregation": {
                "perSeriesAligner": "ALIGN_RATE",
                "crossSeriesReducer": "REDUCE_SUM",
                "alignmentPeriod": "300s"
              }
            },
            "unitOverride": "1/s"
          },
          "sparkChartView": {
            "sparkChartType": "SPARK_LINE"
          },
          "thresholds": [
            {
              "value": 0.01,
              "color": "YELLOW",
              "direction": "BELOW"
            }
          ]
        }
      },
      {
        "title": "Vector Database Log Volume",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"logging.googleapis.com/user/${log_name_prefix}.vectordb_logs\"",
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
            "label": "logs/s",
            "scale": "LINEAR"
          }
        }
      },
      {
        "title": "Vector Database Operations (24h)",
        "xyChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"logging.googleapis.com/user/${log_name_prefix}.vectordb_logs\"",
                  "aggregation": {
                    "perSeriesAligner": "ALIGN_COUNT",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "alignmentPeriod": "3600s"
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
        "title": "Vector Database Log Distribution",
        "pieChart": {
          "dataSets": [
            {
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"logging.googleapis.com/user/${log_name_prefix}.vectordb_logs\"",
                  "aggregation": {
                    "alignmentPeriod": "86400s",
                    "perSeriesAligner": "ALIGN_SUM",
                    "crossSeriesReducer": "REDUCE_SUM",
                    "groupByFields": [
                      "metric.labels.\"severity\""
                    ]
                  }
                }
              }
            }
          ]
        }
      }
    ]
  }
}
