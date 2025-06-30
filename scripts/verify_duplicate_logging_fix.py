#!/usr/bin/env python3
"""
Script to verify that duplicate logging has been fixed by testing the local server
and monitoring log output for duplicates.
"""

import time
from datetime import datetime

import requests


def test_api_endpoint_and_check_logs(base_url: str = "http://127.0.0.1:8000") -> None:
    """Test API endpoints and provide instructions for checking duplicate logs."""

    print("🔍 Testing Duplicate Logging Fix")
    print("=" * 50)

    # Test 1: Basic health check
    print("\n1. Testing health endpoint...")
    correlation_id = f"health-check-{int(time.time())}"

    try:
        response = requests.get(
            f"{base_url}/", headers={"X-Correlation-ID": correlation_id}, timeout=10
        )
        print(
            f"   ✅ Health check: {response.status_code} - {response.json()['message']}"
        )
        print(f"   🔗 Correlation ID: {correlation_id}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return

    # Test 2: Search endpoint (this generates the most logs)
    print("\n2. Testing search endpoint...")
    correlation_id = f"search-test-{int(time.time())}"

    search_payload = {"query": "Brooklyn Bridge", "top_k": 3}

    try:
        response = requests.post(
            f"{base_url}/api/query/search",
            headers={
                "Content-Type": "application/json",
                "X-Correlation-ID": correlation_id,
            },
            json=search_payload,
            timeout=30,
        )
        print(f"   ✅ Search test: {response.status_code}")
        print(f"   🔗 Correlation ID: {correlation_id}")

        if response.status_code == 200:
            results = response.json()
            print(f"   📊 Returned {results.get('count', 0)} results")

    except Exception as e:
        print(f"   ❌ Search test failed: {e}")

    # Test 3: Multiple rapid requests to stress test logging
    print("\n3. Testing multiple rapid requests...")

    for i in range(3):
        correlation_id = f"rapid-test-{int(time.time())}-{i}"
        try:
            response = requests.get(
                f"{base_url}/", headers={"X-Correlation-ID": correlation_id}, timeout=5
            )
            print(
                f"   ✅ Request {i + 1}: {response.status_code} (ID: {correlation_id})"
            )
        except Exception as e:
            print(f"   ❌ Request {i + 1} failed: {e}")

        time.sleep(0.5)  # Small delay between requests

    print("\n" + "=" * 50)
    print("🔍 HOW TO VERIFY NO DUPLICATES:")
    print("=" * 50)

    print("\n📋 Check your server console output for:")
    print("   1. Look for log messages with the correlation IDs above")
    print("   2. Each log message should appear ONLY ONCE")
    print("   3. Before the fix, you would see messages like:")
    print("      INFO:nyc_landmarks.api.query:search_text request...")
    print("      INFO:nyc_landmarks.api.query:search_text request...")  # <- duplicate
    print("      INFO:nyc_landmarks.api.query:search_text request...")  # <- duplicate
    print("   4. After the fix, you should see:")
    print(
        "      INFO:nyc_landmarks.api.query:search_text request..."
    )  # <- single entry

    print("\n✅ SIGNS OF SUCCESS:")
    print("   • Each correlation ID appears in logs only once per operation")
    print("   • No repeated identical log messages")
    print("   • Clean, readable log output")
    print("   • Reduced log volume compared to before")

    print("\n❌ SIGNS OF REMAINING ISSUES:")
    print("   • Same log message appears 2-3 times in a row")
    print("   • Correlation IDs show up multiple times for same operation")
    print("   • Excessive log volume")


def monitor_specific_log_patterns() -> None:
    """Provide guidance on what specific log patterns to look for."""

    print("\n🔍 SPECIFIC PATTERNS TO MONITOR:")
    print("=" * 40)

    patterns_to_check = [
        "INFO:nyc_landmarks.api.query:search_text request",
        "INFO:nyc_landmarks.api.query:Generating embedding",
        "INFO:nyc_landmarks.embeddings.generator:Initialized OpenAI client",
        "INFO:nyc_landmarks.vectordb.pinecone_db:Connected to Pinecone index",
        "INFO:nyc_landmarks.api.middleware:Performance:",
    ]

    print("\n📝 In your server console, watch for these log patterns:")
    for pattern in patterns_to_check:
        print(f"   • {pattern}")

    print("\n✅ EXPECTED BEHAVIOR (FIXED):")
    print("   Each pattern should appear ONCE per API request")

    print("\n❌ PREVIOUS BEHAVIOR (BROKEN):")
    print("   Each pattern would appear 2-3 times per API request")


if __name__ == "__main__":
    print("🚀 Starting duplicate logging verification test")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")

    test_api_endpoint_and_check_logs()
    monitor_specific_log_patterns()

    print("\n" + "=" * 50)
    print("🎯 NEXT STEPS:")
    print("1. Review your server console output")
    print("2. Confirm each log message appears only once")
    print(
        "3. If you see duplicates, check for any remaining logging.basicConfig() calls"
    )
    print("4. If no duplicates, the fix is successful! 🎉")
    print("=" * 50)
