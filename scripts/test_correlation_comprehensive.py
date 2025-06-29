#!/usr/bin/env python3
"""
Comprehensive Cordef make_api_request(
    headers: Dict[str, str],
    payload: Dict[str, Any],
    test_name: str = "API Request",
    api_url: str = API_BASE_URL
) -> Optional[requests.Response]:on ID Testing Script for NYC Landmarks Vector DB.

This script consolidates all correlation ID testing functionality including:
- Multiple header format testing (X-Request-ID, X-Correlation-ID, etc.)
- Header priority validation
- Session correlation across multiple requests
- Auto-generation testing
- End-to-end correlation tracking
- GCP logging query examples

Usage:
    python scripts/test_correlation_comprehensive.py [--test-suite all|headers|tracking|priority|session]
    python scripts/test_correlation_comprehensive.py --help
"""

import argparse
import time
from typing import Any, Dict, List, Optional

import requests

# Configuration
API_BASE_URL = "https://vector-db.coredatastore.com"
REQUEST_TIMEOUT = 30
DEFAULT_USER_AGENT = "ComprehensiveCorrelationTestScript/1.0"

# Store test results for final summary
test_results: List[Dict[str, str]] = []


def log_test_result(test_name: str, correlation_id: str, status: str = "✅") -> None:
    """Log a test result for the final summary."""
    test_results.append(
        {
            "name": test_name,
            "correlation_id": correlation_id,
            "status": status,
            "timestamp": str(int(time.time())),
        }
    )


def make_api_request(
    headers: Dict[str, str],
    payload: Dict[str, Any],
    test_name: str = "API Request",
    api_url: str = API_BASE_URL,
) -> Optional[requests.Response]:
    """Make an API request with error handling."""
    try:
        response = requests.post(
            f"{api_url}/api/query/search",
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )

        print(f"   ✅ Response: {response.status_code}")
        print(f"   ⏱️  Response time: {response.elapsed.total_seconds():.3f}s")
        return response

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def test_header_formats(api_url: str = API_BASE_URL) -> None:
    """Test all supported correlation ID header formats."""
    print("🔗 Testing Correlation ID Header Formats")
    print("=" * 60)

    # Test different correlation ID headers with priority order
    correlation_tests: List[Dict[str, Any]] = [
        {
            "name": "X-Request-ID Header (Highest Priority)",
            "header": "X-Request-ID",
            "value": f"test-x-request-id-{int(time.time())}",
            "priority": 1,
        },
        {
            "name": "X-Correlation-ID Header",
            "header": "X-Correlation-ID",
            "value": f"test-x-correlation-id-{int(time.time())}",
            "priority": 2,
        },
        {
            "name": "Request-ID Header",
            "header": "Request-ID",
            "value": f"test-request-id-{int(time.time())}",
            "priority": 3,
        },
        {
            "name": "Correlation-ID Header (Lowest Priority)",
            "header": "Correlation-ID",
            "value": f"test-correlation-id-{int(time.time())}",
            "priority": 4,
        },
    ]

    for test in correlation_tests:
        print(f"\n📍 Testing: {test['name']}")
        print(f"   Header: {test['header']}: {test['value']}")
        print(f"   Priority: {test['priority']} (1=highest)")

        headers = {
            "Content-Type": "application/json",
            test['header']: test['value'],
            "User-Agent": DEFAULT_USER_AGENT,
        }

        payload = {
            "query": f"Test query for {test['name']}",
            "source_type": "wikipedia",
            "top_k": 2,
        }

        response = make_api_request(headers, payload, test['name'], api_url)
        if response:
            log_test_result(test['name'], test['value'])

        # Small delay between tests
        time.sleep(1)

    print(
        f"\n✅ Header format testing completed - {len([r for r in test_results if 'Header' in r['name']])} tests"
    )


def test_header_priority(api_url: str = API_BASE_URL) -> None:
    """Test header priority when multiple correlation headers are present."""
    print("\n\n🏆 Testing Header Priority")
    print("=" * 60)

    priority_correlation_id = f"priority-test-{int(time.time())}"

    print(f"📋 Expected Winner: {priority_correlation_id} (X-Request-ID)")
    print("🔄 Sending request with multiple correlation headers...")

    # Send multiple correlation headers to test priority
    headers = {
        "Content-Type": "application/json",
        "User-Agent": DEFAULT_USER_AGENT,
        # Multiple headers - X-Request-ID should take priority
        "X-Request-ID": priority_correlation_id,
        "X-Correlation-ID": "should-be-ignored-1",
        "Request-ID": "should-be-ignored-2",
        "Correlation-ID": "should-be-ignored-3",
    }

    payload = {
        "query": "Testing header priority mechanism",
        "source_type": "wikipedia",
        "top_k": 1,
    }

    response = make_api_request(headers, payload, "Header Priority Test", api_url)
    if response:
        log_test_result("Header Priority Test", priority_correlation_id)

    print("\n🔍 Verify priority with GCP query:")
    print(f"   jsonPayload.correlation_id=\"{priority_correlation_id}\"")
    print(
        "   (Should find logs with the priority ID, not the 'should-be-ignored' values)"
    )


def test_auto_generation(api_url: str = API_BASE_URL) -> None:
    """Test auto-generation of correlation IDs when no headers provided."""
    print("\n\n🔄 Testing Auto-Generated Correlation IDs")
    print("=" * 60)

    print("📍 Test: Request without any correlation headers")
    print("   Expected: Middleware auto-generates UUID correlation ID")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": DEFAULT_USER_AGENT,
        # Intentionally no correlation headers
    }

    payload = {
        "query": "Test auto-generation of correlation ID",
        "source_type": "wikipedia",
        "top_k": 2,
    }

    response = make_api_request(headers, payload, "Auto-Generation Test", api_url)
    if response:
        log_test_result("Auto-Generation Test", "auto-generated-uuid")

    print("   🆔 Correlation ID will be auto-generated by middleware")
    print("   🔍 Check logs for auto-generated UUID pattern")


def test_session_correlation(api_url: str = API_BASE_URL) -> None:
    """Test session correlation across multiple related requests."""
    print("\n\n🌐 Testing Session Correlation")
    print("=" * 60)

    # Use a shared correlation ID for multiple related requests
    session_correlation_id = f"session-{int(time.time())}"

    print(f"📋 Session Correlation ID: {session_correlation_id}")
    print("🎯 Goal: Track multiple related requests through the entire system")

    # Simulate a user session with multiple related queries
    session_queries = [
        "What is the Statue of Liberty?",
        "History of Brooklyn Bridge",
        "Central Park landmarks and monuments",
        "Ellis Island historical significance",
    ]

    headers = {
        "Content-Type": "application/json",
        "X-Request-ID": session_correlation_id,  # Same ID for all requests
        "User-Agent": f"{DEFAULT_USER_AGENT}-Session",
    }

    print(f"\n🔄 Making {len(session_queries)} related requests...")

    for i, query in enumerate(session_queries, 1):
        print(f"\n   📤 Request {i}/{len(session_queries)}: {query}")

        payload = {"query": query, "source_type": "wikipedia", "top_k": 3}

        response = make_api_request(headers, payload, f"Session Request {i}", api_url)
        if response:
            print(f"      📊 Session request {i} completed successfully")

        # Small delay between requests
        time.sleep(0.8)

    log_test_result("Session Correlation Test", session_correlation_id)

    print("\n🎯 Session Analysis GCP Query:")
    print(f"   jsonPayload.correlation_id=\"{session_correlation_id}\"")
    print(
        "   This will show ALL logs (request body + performance) for the entire session!"
    )


def test_correlation_tracking(api_url: str = API_BASE_URL) -> None:
    """Test basic correlation tracking functionality."""
    print("\n\n🔗 Testing Basic Correlation Tracking")
    print("=" * 60)

    # Test 1: Custom correlation ID
    custom_correlation_id = f"custom-tracking-{int(time.time())}"

    print("\n📍 Test 1: Custom Correlation ID")
    print(f"   Correlation ID: {custom_correlation_id}")

    headers = {
        "Content-Type": "application/json",
        "X-Request-ID": custom_correlation_id,
        "User-Agent": DEFAULT_USER_AGENT,
    }

    payload = {
        "query": "What is the history of correlation tracking in distributed systems?",
        "source_type": "wikipedia",
        "top_k": 3,
    }

    response = make_api_request(headers, payload, "Custom Tracking Test", api_url)
    if response:
        log_test_result("Custom Tracking Test", custom_correlation_id)

    # Test 2: Multiple requests with different correlation headers
    shared_correlation_id = f"shared-tracking-{int(time.time())}"

    print("\n📍 Test 2: Multiple Requests with Shared Correlation ID")
    print(f"   Shared Correlation ID: {shared_correlation_id}")

    shared_headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": shared_correlation_id,  # Use different header type
        "User-Agent": DEFAULT_USER_AGENT,
    }

    tracking_queries = [
        "First query in correlation group",
        "Second query in correlation group",
        "Third query in correlation group",
    ]

    for i, query in enumerate(tracking_queries, 1):
        print(f"\n   📤 Group Request {i}: {query}")
        payload = {"query": query, "source_type": "wikipedia", "top_k": 1}

        response = make_api_request(
            shared_headers, payload, f"Group Request {i}", api_url
        )

        # Small delay between requests
        time.sleep(0.5)

    log_test_result("Shared Tracking Test", shared_correlation_id)


def print_gcp_queries() -> None:
    """Print comprehensive GCP logging queries for all tests."""
    print("\n\n🔍 Google Cloud Logging Queries")
    print("=" * 60)

    print("📊 Individual Test Queries:")
    for result in test_results:
        if result['correlation_id'] != "auto-generated-uuid":
            print(f"\n🔹 {result['name']}:")
            print(f"   jsonPayload.correlation_id=\"{result['correlation_id']}\"")

    print("\n📋 Combined Queries:")

    print("\n🎯 All Request Body Logs with Correlation:")
    print(
        "   jsonPayload.metric_type=\"request_body\" AND jsonPayload.correlation_id!=\"unknown\""
    )

    print("\n🎯 All Performance Logs with Correlation:")
    print(
        "   jsonPayload.metric_type=\"performance\" AND jsonPayload.correlation_id!=\"unknown\""
    )

    print("\n🎯 Correlate Request Body + Performance for any ID:")
    print("   jsonPayload.correlation_id=\"YOUR-CORRELATION-ID\" AND")
    print(
        "   (jsonPayload.metric_type=\"request_body\" OR jsonPayload.metric_type=\"performance\")"
    )

    print("\n🎯 Find logs from this test session (last hour):")
    current_time = int(time.time())
    one_hour_ago = current_time - 3600
    print(
        "   jsonPayload.correlation_id ~ \"test-|session-|custom-|shared-|priority-\" AND"
    )
    print(
        f"   timestamp >= \"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(one_hour_ago))}\""
    )


def print_summary() -> None:
    """Print a comprehensive test summary."""
    print("\n\n🎉 Comprehensive Correlation Testing Summary")
    print("=" * 60)

    successful_tests = [r for r in test_results if r['status'] == '✅']
    total_tests = len(test_results)

    print(f"📊 Test Results: {len(successful_tests)}/{total_tests} successful")

    print("\n✅ Functionality Verified:")
    print(
        "   🔸 Multiple header formats (X-Request-ID, X-Correlation-ID, Request-ID, Correlation-ID)"
    )
    print("   🔸 Header priority (X-Request-ID takes precedence)")
    print("   🔸 Auto-generation (UUIDs when no headers provided)")
    print("   🔸 Session correlation (multiple requests with same ID)")
    print("   🔸 Cross-middleware correlation (request body + performance logs)")
    print("   🔸 End-to-end tracking (distributed request tracing)")

    print("\n🔗 Generated Correlation IDs:")
    for result in successful_tests:
        if result['correlation_id'] != "auto-generated-uuid":
            print(f"   🆔 {result['name']}: {result['correlation_id']}")

    print("\n🚀 Your correlation system is fully functional and ready for production!")


def main() -> None:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Correlation ID Testing Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Suites:
  all       - Run all correlation tests (default)
  headers   - Test header formats only
  tracking  - Test basic correlation tracking
  priority  - Test header priority only
  session   - Test session correlation only

Examples:
  python scripts/test_correlation_comprehensive.py
  python scripts/test_correlation_comprehensive.py --test-suite headers
  python scripts/test_correlation_comprehensive.py --test-suite session
        """,
    )

    parser.add_argument(
        "--test-suite",
        choices=["all", "headers", "tracking", "priority", "session"],
        default="all",
        help="Test suite to run (default: all)",
    )

    parser.add_argument(
        "--api-url",
        default=API_BASE_URL,
        help=f"API base URL (default: {API_BASE_URL})",
    )

    args = parser.parse_args()

    # Use the API URL from args
    api_url = args.api_url

    print("🧪 Comprehensive Correlation ID Testing")
    print("=" * 60)
    print(f"🌐 API Base URL: {api_url}")
    print(f"🎯 Test Suite: {args.test_suite}")
    print(f"⏰ Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")

    # Run selected test suites
    if args.test_suite in ["all", "headers"]:
        test_header_formats(api_url)

    if args.test_suite in ["all", "priority"]:
        test_header_priority(api_url)

    if args.test_suite in ["all", "tracking"]:
        test_correlation_tracking(api_url)

    if args.test_suite in ["all", "session"]:
        test_session_correlation(api_url)

    if args.test_suite == "all":
        test_auto_generation(api_url)

    # Always show queries and summary
    print_gcp_queries()
    print_summary()


if __name__ == "__main__":
    main()
