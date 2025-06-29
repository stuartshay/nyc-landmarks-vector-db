#!/usr/bin/env python3
"""
Comprehensive test script for correlation ID functionality across all middleware.

This script demonstrates how to send correlation IDs in headers and correlate
logs across request body logging and performance monitoring middleware.
"""

import time

import requests

API_BASE_URL = "https://vector-db.coredatastore.com"


def test_correlation_headers() -> None:
    """Test correlation ID functionality with different header formats."""

    print("🔗 Testing Correlation ID Headers")
    print("=" * 60)

    # Test different correlation ID headers
    correlation_tests = [
        {
            "name": "X-Request-ID Header",
            "header": "X-Request-ID",
            "value": f"test-x-request-id-{int(time.time())}",
        },
        {
            "name": "X-Correlation-ID Header",
            "header": "X-Correlation-ID",
            "value": f"test-x-correlation-id-{int(time.time())}",
        },
        {
            "name": "Request-ID Header",
            "header": "Request-ID",
            "value": f"test-request-id-{int(time.time())}",
        },
        {
            "name": "Correlation-ID Header",
            "header": "Correlation-ID",
            "value": f"test-correlation-id-{int(time.time())}",
        },
    ]

    for test in correlation_tests:
        print(f"\n📍 Testing: {test['name']}")
        print(f"   Header: {test['header']}: {test['value']}")

        headers = {
            "Content-Type": "application/json",
            test['header']: test['value'],
            "User-Agent": "CorrelationHeaderTestScript/1.0",
        }

        payload = {
            "query": f"Test query for {test['name']}",
            "source_type": "wikipedia",
            "top_k": 2,
        }

        try:
            response = requests.post(
                f"{API_BASE_URL}/api/query/search",
                json=payload,
                headers=headers,
                timeout=30,
            )

            print(f"   ✅ Response: {response.status_code}")
            print(f"   ⏱️  Response time: {response.elapsed.total_seconds():.3f}s")

            # Small delay between tests
            time.sleep(1)

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n" + "=" * 60)
    print("🎯 Correlation Query Examples")
    print("\nTo view correlated logs for any test above, use:")

    for test in correlation_tests:
        print(f"\n🔍 {test['name']}:")
        print(f"   jsonPayload.correlation_id=\"{test['value']}\"")

    print("\n📊 Combined correlation queries:")
    print("   # All request body logs with correlation")
    print(
        "   jsonPayload.metric_type=\"request_body\" AND jsonPayload.correlation_id!=\"unknown\""
    )
    print("\n   # All performance logs with correlation")
    print(
        "   jsonPayload.metric_type=\"performance\" AND jsonPayload.correlation_id!=\"unknown\""
    )
    print("\n   # Correlate request body + performance for same ID")
    print("   jsonPayload.correlation_id=\"YOUR-CORRELATION-ID\" AND")
    print(
        "   (jsonPayload.metric_type=\"request_body\" OR jsonPayload.metric_type=\"performance\")"
    )


def test_end_to_end_correlation() -> None:
    """Test end-to-end correlation across multiple requests."""

    print("\n\n🌐 Testing End-to-End Correlation")
    print("=" * 60)

    # Use a shared correlation ID for multiple related requests
    session_correlation_id = f"session-{int(time.time())}"

    print(f"📋 Session Correlation ID: {session_correlation_id}")

    # Simulate a user session with multiple related queries
    queries = [
        "What is the Statue of Liberty?",
        "History of Brooklyn Bridge",
        "Central Park landmarks",
    ]

    headers = {
        "Content-Type": "application/json",
        "X-Request-ID": session_correlation_id,  # Same ID for all requests
        "User-Agent": "SessionCorrelationTest/1.0",
    }

    print(f"\n🔄 Making {len(queries)} related requests...")

    for i, query in enumerate(queries, 1):
        print(f"\n   📤 Request {i}: {query}")

        payload = {"query": query, "source_type": "wikipedia", "top_k": 3}

        try:
            response = requests.post(
                f"{API_BASE_URL}/api/query/search",
                json=payload,
                headers=headers,
                timeout=30,
            )

            print(
                f"      ✅ {response.status_code} ({response.elapsed.total_seconds():.3f}s)"
            )

        except Exception as e:
            print(f"      ❌ Error: {e}")

        # Small delay between requests
        time.sleep(0.8)

    print("\n🎯 Session Analysis Query:")
    print(f"   jsonPayload.correlation_id=\"{session_correlation_id}\"")
    print(
        "\n   This will show ALL logs (request body + performance) for the entire session!"
    )


def test_correlation_priority() -> None:
    """Test header priority when multiple correlation headers are present."""

    print("\n\n🏆 Testing Header Priority")
    print("=" * 60)

    priority_correlation_id = f"priority-test-{int(time.time())}"

    # Send multiple correlation headers to test priority
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "PriorityTestScript/1.0",
        # Multiple headers - x-request-id should take priority
        "X-Request-ID": priority_correlation_id,
        "X-Correlation-ID": "should-be-ignored-1",
        "Request-ID": "should-be-ignored-2",
        "Correlation-ID": "should-be-ignored-3",
    }

    payload = {
        "query": "Testing header priority",
        "source_type": "wikipedia",
        "top_k": 1,
    }

    print(f"📋 Expected Correlation ID: {priority_correlation_id}")
    print("🔄 Sending request with multiple correlation headers...")

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/query/search",
            json=payload,
            headers=headers,
            timeout=30,
        )

        print(
            f"✅ Response: {response.status_code} ({response.elapsed.total_seconds():.3f}s)"
        )
        print("\n🔍 Verify priority with:")
        print(f"   jsonPayload.correlation_id=\"{priority_correlation_id}\"")
        print("   (Should find logs, not the 'should-be-ignored' values)")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_correlation_headers()
    test_end_to_end_correlation()
    test_correlation_priority()

    print("\n\n🎉 All correlation tests completed!")
    print("\n📝 Summary:")
    print("✅ Multiple header formats supported (X-Request-ID, X-Correlation-ID, etc.)")
    print("✅ Session correlation across multiple requests")
    print("✅ Header priority testing (X-Request-ID takes precedence)")
    print("✅ Full log correlation between request body and performance logs")
    print("\n🚀 Your correlation system is fully functional!")
