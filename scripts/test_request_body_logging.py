#!/usr/bin/env python3
"""
Test script for the request body logging middleware.

This script tests the new middleware by making a POST request and checking
if the request body is properly logged.
"""

import json
import subprocess
import sys
import time

import requests


def test_request_body_logging() -> bool:
    """Test if request body logging is working correctly."""
    print("Testing POST request body logging...")

    # Make a test request to the API
    test_payload = {
        "query": "What is the history of the Lefferts Family?",
        "source_type": "wikipedia",
        "top_k": 5,
    }

    api_url = "https://vector-db.coredatastore.com/api/query/search"

    print(f"Making POST request to: {api_url}")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")

    try:
        response = requests.post(
            api_url,
            json=test_payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "request-body-logging-test/1.0",
            },
            timeout=30,
        )

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()
            print(f"Response received with {response_data.get('count', 0)} results")
        else:
            print(f"Error response: {response.text}")

    except Exception as e:
        print(f"Error making request: {e}")
        return False

    # Wait a moment for logs to be ingested
    print("Waiting 10 seconds for logs to be ingested...")
    time.sleep(10)

    # Query the logs to see if our request body was logged
    print("Checking if request body was logged...")

    # Create a filter to find our specific request
    gcloud_filter = (
        'logName=~"nyc-landmarks-vector-db" AND '
        'jsonPayload.metric_type="request_body" AND '
        'jsonPayload.method="POST" AND '
        'jsonPayload.path="/api/query/search" AND '
        'timestamp>="'
        + time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - 60))
        + '"'
    )

    try:
        result = subprocess.run(  # nosec B607
            [
                "gcloud",
                "logging",
                "read",
                gcloud_filter,
                "--limit",
                "5",
                "--format",
                "json",
                "--project",
                "velvety-byway-327718",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            logs = json.loads(result.stdout) if result.stdout.strip() else []

            if logs:
                print(f"Found {len(logs)} request body log entries!")

                # Display the first log entry
                for i, log in enumerate(logs[:2]):
                    print(f"\n--- Log Entry {i + 1} ---")
                    json_payload = log.get("jsonPayload", {})
                    print(f"Timestamp: {log.get('timestamp')}")
                    print(f"Endpoint: {json_payload.get('endpoint')}")
                    print(f"Body size: {json_payload.get('body_size_bytes')} bytes")

                    request_body = json_payload.get("request_body")
                    if request_body:
                        print(
                            f"Logged request body: {json.dumps(request_body, indent=2)}"
                        )

                    print(
                        f"Client info: IP={json_payload.get('client_ip')}, "
                        f"User-Agent={json_payload.get('user_agent')}"
                    )

                return True
            else:
                print("No request body logs found. This could mean:")
                print("1. The middleware is not yet deployed")
                print("2. Logs haven't been ingested yet (try waiting longer)")
                print("3. There's an issue with the logging configuration")
                return False
        else:
            print(f"Error querying logs: {result.stderr}")
            return False

    except Exception as e:
        print(f"Error querying logs: {e}")
        return False


def check_current_performance_logs() -> None:
    """Check current performance logs to see the pattern."""
    print("\nChecking current performance logs for reference...")

    gcloud_filter = (
        'logName=~"nyc-landmarks-vector-db" AND '
        'jsonPayload.endpoint_category="query" AND '
        'jsonPayload.metric_type="performance" AND '
        'timestamp>="'
        + time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - 300))
        + '"'
    )

    try:
        result = subprocess.run(  # nosec B607
            [
                "gcloud",
                "logging",
                "read",
                gcloud_filter,
                "--limit",
                "2",
                "--format",
                "json",
                "--project",
                "velvety-byway-327718",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            logs = json.loads(result.stdout) if result.stdout.strip() else []

            if logs:
                print(
                    f"Found {len(logs)} recent performance log entries for reference:"
                )
                for i, log in enumerate(logs[:1]):
                    json_payload = log.get("jsonPayload", {})
                    print(
                        f"  Performance log {i + 1}: {json_payload.get('endpoint')} - "
                        f"{json_payload.get('duration_ms'):.1f}ms"
                    )
            else:
                print("No recent performance logs found")
        else:
            print(f"Error querying performance logs: {result.stderr}")

    except Exception as e:
        print(f"Error querying performance logs: {e}")


if __name__ == "__main__":
    print("Request Body Logging Test")
    print("=" * 50)

    # First check current logs for reference
    check_current_performance_logs()

    # Test request body logging
    success = test_request_body_logging()

    print("\n" + "=" * 50)
    if success:
        print("✅ Request body logging test PASSED!")
        print("The middleware is working correctly.")
    else:
        print("❌ Request body logging test FAILED!")
        print("The middleware may need to be deployed or there may be an issue.")

    sys.exit(0 if success else 1)
