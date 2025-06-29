#!/usr/bin/env python3
"""
Development test script for request body logging middleware.

This script demonstrates the enhanced development features.
"""

import os
import time

import requests

# Set development mode for testing
os.environ["DEVELOPMENT_MODE"] = "true"
os.environ["LOG_ALL_POST_REQUESTS"] = "true"

# API base URL - update as needed
API_BASE_URL = "https://vector-db.coredatastore.com"


def test_request_body_logging() -> None:
    """Test the request body logging with development features."""

    # Test the configured endpoints
    test_endpoints = [
        "/api/query/search",
        "/api/query/search/landmark",
        "/api/chat/message",
    ]

    print("🔧 Testing Request Body Logging Middleware (Development Mode)")
    print("=" * 60)

    for endpoint in test_endpoints:
        print(f"\n📍 Testing endpoint: {endpoint}")

        # Create test payload
        test_payload = {
            "query": "Test query for development",
            "limit": 5,
            "metadata": {
                "test_mode": True,
                "timestamp": time.time(),
                "description": "This is a test request to validate logging middleware",
            },
        }

        try:
            # Add development headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Development-Test-Script/1.0",
                "X-Request-ID": f"dev-test-{int(time.time())}",
                "Accept": "application/json",
            }

            print("  📤 Sending POST request...")
            print(f"  📋 Payload size: {len(str(test_payload))} chars")

            response = requests.post(
                f"{API_BASE_URL}{endpoint}",
                json=test_payload,
                headers=headers,
                timeout=30,
            )

            print(f"  ✅ Response: {response.status_code}")
            print(f"  ⏱️  Response time: {response.elapsed.total_seconds():.3f}s")

            if response.status_code == 200:
                response_data = response.json()
                if isinstance(response_data, dict) and "results" in response_data:
                    print(
                        f"  📊 Results count: {len(response_data.get('results', []))}"
                    )

        except requests.exceptions.RequestException as e:
            print(f"  ❌ Request failed: {e}")
        except Exception as e:
            print(f"  ⚠️  Unexpected error: {e}")

        # Small delay between requests
        time.sleep(1)

    print("\n" + "=" * 60)
    print("🏁 Testing completed!")
    print("\n📝 To view logs, use the following Google Cloud Logging query:")
    print("   jsonPayload.metric_type=\"request_body\" AND")
    print("   jsonPayload.endpoint_category=\"query\"")
    print("\n🕒 For timing logs:")
    print("   jsonPayload.metric_type=\"request_timing\"")
    print("\n🚫 For skipped requests:")
    print("   jsonPayload.metric_type=\"request_skipped\"")


if __name__ == "__main__":
    test_request_body_logging()
