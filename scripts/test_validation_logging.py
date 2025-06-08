#!/usr/bin/env python3
"""
Test script to verify that API input validation and warning logging
are working correctly with Google Cloud Logging.

This script tests all validation scenarios and verifies that warning
logs are properly generated and can be filtered in Google Cloud Logging.
"""

import json
import subprocess
import time

import requests

# API base URL
API_BASE = "http://localhost:8000"

# Test scenarios for validation
TEST_SCENARIOS = [
    {
        "name": "Empty query string",
        "endpoint": "/api/query/search",
        "payload": {"query": "", "top_k": 5},
        "expected_validation_error": "empty_query",
    },
    {
        "name": "Query too long",
        "endpoint": "/api/query/search",
        "payload": {"query": "x" * 1001, "top_k": 5},
        "expected_validation_error": "query_too_long",
    },
    {
        "name": "Suspicious content - script tag",
        "endpoint": "/api/query/search",
        "payload": {"query": "<script>alert('xss')</script>", "top_k": 5},
        "expected_validation_error": "suspicious_content",
    },
    {
        "name": "Suspicious content - javascript URL",
        "endpoint": "/api/query/search",
        "payload": {"query": "javascript:alert('xss')", "top_k": 5},
        "expected_validation_error": "suspicious_content",
    },
    {
        "name": "Invalid landmark ID format",
        "endpoint": "/api/query/search_by_landmark",
        "payload": {"query": "test", "landmark_id": "LP-00001@invalid!", "top_k": 5},
        "expected_validation_error": "invalid_landmark_id_format",
    },
    {
        "name": "Landmark ID too long",
        "endpoint": "/api/query/search_by_landmark",
        "payload": {"query": "test", "landmark_id": "x" * 101, "top_k": 5},
        "expected_validation_error": "landmark_id_too_long",
    },
    {
        "name": "Top K too large",
        "endpoint": "/api/query/search",
        "payload": {"query": "test", "top_k": 51},
        "expected_validation_error": "top_k_too_large",
    },
    {
        "name": "Top K negative",
        "endpoint": "/api/query/search",
        "payload": {"query": "test", "top_k": -1},
        "expected_validation_error": "invalid_top_k_negative",
    },
    {
        "name": "Invalid source type",
        "endpoint": "/api/query/search",
        "payload": {"query": "test", "source_type": "invalid", "top_k": 5},
        "expected_validation_error": "invalid_source_type",
    },
    {
        "name": "Chat - Invalid session ID format",
        "endpoint": "/api/chat/message",
        "payload": {
            "query": "test",
            "session_id": "session@invalid!",
            "landmark_id": "LP-00001",
        },
        "expected_validation_error": "invalid_session_id_format",
    },
    {
        "name": "Chat - Session ID too long",
        "endpoint": "/api/chat/message",
        "payload": {
            "query": "test",
            "session_id": "x" * 201,
            "landmark_id": "LP-00001",
        },
        "expected_validation_error": "session_id_too_long",
    },
]


def test_api_validation() -> list:
    """Test all validation scenarios and generate warning logs."""
    print("🧪 Testing API validation and warning logging...")
    print("=" * 60)

    results = []

    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"\n{i}. Testing: {scenario['name']}")
        print(f"   Endpoint: {scenario['endpoint']}")
        print(f"   Expected error: {scenario['expected_validation_error']}")

        try:
            # Make API request
            url = f"{API_BASE}{scenario['endpoint']}"
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "ValidationTestScript/1.0",
            }

            response = requests.post(
                url, json=scenario["payload"], headers=headers, timeout=30
            )

            result = {
                "scenario": scenario["name"],
                "endpoint": scenario["endpoint"],
                "expected_error": scenario["expected_validation_error"],
                "status_code": response.status_code,
                "success": response.status_code
                == 400,  # Expecting 400 for validation errors
            }

            if response.status_code == 400:
                print("   ✅ Validation failed as expected (HTTP 400)")
                try:
                    error_detail = response.json()
                    print(f"   Response: {json.dumps(error_detail, indent=2)}")
                except Exception:
                    print(f"   Response: {response.text}")
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text}")

            results.append(result)

        except Exception as e:
            print(f"   ❌ Error making request: {e}")
            results.append(
                {
                    "scenario": scenario["name"],
                    "endpoint": scenario["endpoint"],
                    "expected_error": scenario["expected_validation_error"],
                    "status_code": None,
                    "success": False,
                    "error": str(e),
                }
            )

        # Small delay between requests
        time.sleep(0.5)

    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION TEST SUMMARY")
    print("=" * 60)

    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]

    print(f"✅ Successful validations: {len(successful)}/{len(results)}")
    print(f"❌ Failed validations: {len(failed)}/{len(results)}")

    if failed:
        print("\nFailed scenarios:")
        for result in failed:
            print(f"  - {result['scenario']}: HTTP {result.get('status_code', 'N/A')}")

    return results


def _get_logging_commands(project_id: str) -> list:
    """Get the list of Google Cloud logging commands to execute."""
    return [
        {
            "name": "All validation warnings",
            "cmd": [
                "gcloud",
                "logging",
                "read",
                'logName=~"nyc-landmarks-vector-db.nyc_landmarks.utils.validation" AND severity="WARNING"',
                f"--project={project_id}",
                "--limit=20",
                "--format=json",
            ],
        },
        {
            "name": "Suspicious content warnings",
            "cmd": [
                "gcloud",
                "logging",
                "read",
                'logName=~"nyc-landmarks-vector-db" AND jsonPayload.validation_error="suspicious_content"',
                f"--project={project_id}",
                "--limit=5",
                "--format=json",
            ],
        },
        {
            "name": "Query API warnings",
            "cmd": [
                "gcloud",
                "logging",
                "read",
                'logName=~"nyc-landmarks-vector-db" AND jsonPayload.endpoint="/api/query/search"',
                f"--project={project_id}",
                "--limit=10",
                "--format=json",
            ],
        },
    ]


def _process_log_result(result: subprocess.CompletedProcess) -> None:
    """Process and display the result from a logging command."""
    if result.returncode == 0:
        if result.stdout.strip():
            try:
                logs = json.loads(result.stdout)
                if isinstance(logs, list) and logs:
                    print(f"✅ Found {len(logs)} log entries")

                    # Show first log entry details
                    if logs:
                        first_log = logs[0]
                        print(
                            f"   Latest log timestamp: {first_log.get('timestamp', 'N/A')}"
                        )
                        if 'jsonPayload' in first_log:
                            payload = first_log['jsonPayload']
                            print(
                                f"   Validation error: {payload.get('validation_error', 'N/A')}"
                            )
                            print(f"   Endpoint: {payload.get('endpoint', 'N/A')}")
                            print(f"   Client IP: {payload.get('client_ip', 'N/A')}")
                else:
                    print("ℹ️  No logs found (empty result)")
            except json.JSONDecodeError:
                print(f"✅ Found logs (non-JSON format):\n{result.stdout[:500]}...")
        else:
            print("ℹ️  No logs found")
    else:
        print(f"❌ Command failed (exit code {result.returncode})")
        if result.stderr:
            print(f"   Error: {result.stderr}")


def _execute_logging_command(cmd_info: dict) -> None:
    """Execute a single logging command and process its result."""
    print(f"\n📋 {cmd_info['name']}:")
    print(f"Command: {' '.join(cmd_info['cmd'])}")

    try:
        result = subprocess.run(
            cmd_info["cmd"], capture_output=True, text=True, timeout=30
        )
        _process_log_result(result)

    except subprocess.TimeoutExpired:
        print("⏰ Command timed out")
    except Exception as e:
        print(f"❌ Error running command: {e}")


def verify_logs_in_gcp(project_id: str = "velvety-byway-327718") -> None:
    """Verify that validation warning logs appear in Google Cloud Logging."""
    print("\n🔍 Verifying logs in Google Cloud Logging...")
    print("=" * 60)

    # Wait a moment for logs to be ingested
    print("⏱️  Waiting 10 seconds for log ingestion...")
    time.sleep(10)

    # Check for validation warning logs
    commands = _get_logging_commands(project_id)

    for cmd_info in commands:
        _execute_logging_command(cmd_info)


def main() -> None:
    """Main function to run all validation tests and verify logging."""
    print("🚀 Starting comprehensive validation logging test")
    print("This script will:")
    print("1. Test all API validation scenarios")
    print("2. Verify warning logs are generated")
    print("3. Check logs can be filtered in Google Cloud Logging")
    print()

    # Test API validation
    test_api_validation()

    # Verify logs in GCP
    verify_logs_in_gcp()

    print("\n🎉 Validation logging test completed!")
    print("\nNext steps:")
    print("1. Check the Google Cloud Logging console for detailed log analysis")
    print("2. Use the filtering examples in docs/google_cloud_logging_filters.md")
    print("3. Monitor validation logs for security insights")


if __name__ == "__main__":
    main()
