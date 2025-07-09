#!/usr/bin/env python3
"""
Test script to demonstrate correlation ID logging flow for API query search.

This script makes a POST request to the /api/query/search endpoint and shows
how correlation IDs are used throughout the logging system for request tracing.
"""

import json
import time
import uuid
from typing import Any, Dict, List, Optional

import requests


def make_search_request(
    base_url: str = "http://localhost:8000",
    correlation_id: Optional[str] = None,
    query: str = "What is the history of the Pieter Claesen Wyckoff House?",
    source_type: Optional[str] = "wikipedia",
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Make a POST request to /api/query/search with correlation ID tracking.

    Args:
        base_url: Base URL of the API server
        correlation_id: Optional correlation ID (will generate if not provided)
        query: Search query text
        source_type: Source type filter
        top_k: Number of results to return

    Returns:
        Dictionary with request details and response
    """
    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    # Prepare request
    url = f"{base_url}/api/query/search"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Request-ID": correlation_id,  # Primary correlation header
        "User-Agent": "correlation-test-script/1.0",
    }

    payload = {"query": query, "source_type": source_type, "top_k": top_k}

    print(f"🔍 Making POST request to: {url}")
    print(f"📋 Correlation ID: {correlation_id}")
    print(f"📝 Request payload: {json.dumps(payload, indent=2)}")
    print(f"🏷️  Headers: {json.dumps(headers, indent=2)}")
    print("-" * 80)

    start_time = time.time()

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        result = {
            "correlation_id": correlation_id,
            "request": {
                "url": url,
                "method": "POST",
                "headers": headers,
                "payload": payload,
            },
            "response": {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "duration_ms": round(duration_ms, 2),
            },
            "success": response.status_code == 200,
        }

        if response.status_code == 200:
            try:
                response_data = response.json()
                response_dict = result["response"]
                if isinstance(response_dict, dict):
                    response_dict["data"] = response_data
                result_count = len(response_data.get("results", []))
                print("✅ Request successful!")
                print(f"📊 Status: {response.status_code}")
                print(f"⏱️  Duration: {duration_ms:.2f}ms")
                print(f"📈 Results: {result_count} items")
            except json.JSONDecodeError:
                response_dict = result["response"]
                if isinstance(response_dict, dict):
                    response_dict["text"] = response.text
                print("✅ Request successful but response not JSON")
                print(f"📊 Status: {response.status_code}")
                print(f"⏱️  Duration: {duration_ms:.2f}ms")
        else:
            response_dict = result["response"]
            if isinstance(response_dict, dict):
                response_dict["text"] = response.text
            print("❌ Request failed!")
            print(f"📊 Status: {response.status_code}")
            print(f"⏱️  Duration: {duration_ms:.2f}ms")
            print(f"💬 Response: {response.text}")

    except requests.exceptions.RequestException as e:
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        result = {
            "correlation_id": correlation_id,
            "request": {
                "url": url,
                "method": "POST",
                "headers": headers,
                "payload": payload,
            },
            "response": {"error": str(e), "duration_ms": round(duration_ms, 2)},
            "success": False,
        }

        print("❌ Request failed with exception!")
        print(f"⏱️  Duration: {duration_ms:.2f}ms")
        print(f"💥 Error: {e}")

    return result


def demonstrate_log_aggregation(correlation_id: str) -> None:
    """
    Show how to aggregate logs using the correlation ID.

    Args:
        correlation_id: The correlation ID to search for
    """
    print("\n" + "=" * 80)
    print("📋 LOG AGGREGATION DEMONSTRATION")
    print("=" * 80)

    print(f"🔍 Searching for logs with correlation_id: {correlation_id}")
    print("\n📝 Example log aggregation commands:")

    # Grep command for text logs
    print("\n1. Search text logs:")
    print(f"   grep '{correlation_id}' logs/*.log")

    # JQ command for JSON logs
    print("\n2. Search JSON logs:")
    print(f"   jq '.correlation_id == \"{correlation_id}\"' logs/*.json")

    # Advanced JQ query for structured analysis
    print("\n3. Extract key information:")
    print(f"   jq 'select(.correlation_id == \"{correlation_id}\") | {{")
    print("     timestamp: .timestamp,")
    print("     component: .name,")
    print("     operation: .operation // .message,")
    print("     duration: .duration_ms")
    print("   }' logs/*.json")

    # Show expected log sequence
    print(f"\n📊 Expected log sequence for correlation_id {correlation_id}:")
    expected_logs = [
        "1. Request Body Middleware: POST request body logged",
        "2. Validation Logger: Valid API request processed",
        "3. Query API: Generating embedding for query",
        "4. Query API: Embedding generation completed",
        "5. Vector DB: Starting vector query operation",
        "6. Vector DB: Vector query operation completed",
        "7. Performance Middleware: API request completed",
    ]

    for log_entry in expected_logs:
        print(f"   {log_entry}")


def test_multiple_requests() -> List[Dict[str, Any]]:
    """Test multiple requests with different correlation IDs."""
    print("\n" + "=" * 80)
    print("🔄 TESTING MULTIPLE REQUESTS")
    print("=" * 80)

    test_cases: List[Dict[str, Any]] = [
        {
            "name": "Wikipedia Search",
            "query": "What is the history of the Pieter Claesen Wyckoff House?",
            "source_type": "wikipedia",
            "top_k": 5,
        },
        {
            "name": "PDF Search",
            "query": "architectural details of Brooklyn Bridge",
            "source_type": "pdf",
            "top_k": 3,
        },
        {
            "name": "Combined Search",
            "query": "landmark designation process",
            "source_type": None,  # Will be omitted from request
            "top_k": 10,
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {test_case['name']}")
        print("-" * 40)

        # Create payload, omitting None values
        payload_data = {"query": test_case["query"], "top_k": test_case["top_k"]}
        if test_case["source_type"]:
            payload_data["source_type"] = test_case["source_type"]

        result = make_search_request(
            query=test_case["query"],
            source_type=test_case.get("source_type"),
            top_k=test_case["top_k"],
        )

        results.append(result)

        # Show correlation ID for log aggregation
        print(f"🏷️  Correlation ID for this request: {result['correlation_id']}")

        # Small delay between requests
        time.sleep(1)

    # Summary
    print("\n📊 SUMMARY")
    print("-" * 40)
    successful_requests = sum(1 for r in results if r["success"])
    print(f"✅ Successful requests: {successful_requests}/{len(results)}")

    print("\n🏷️  All correlation IDs generated:")
    for i, result in enumerate(results, 1):
        status = "✅" if result["success"] else "❌"
        print(f"   {i}. {status} {result['correlation_id']}")

    return results


def main() -> List[Dict[str, Any]]:
    """Main function to run the correlation logging demonstration."""
    print("🚀 NYC Landmarks API - Correlation ID Logging Flow Test")
    print("=" * 80)

    print("This script demonstrates how correlation IDs are used throughout")
    print("the logging system for the POST /api/query/search endpoint.")
    print()

    # Test single request
    print("🔍 SINGLE REQUEST TEST")
    print("-" * 40)

    # Generate a specific correlation ID for demonstration
    demo_correlation_id = f"demo-{uuid.uuid4()}"

    make_search_request(
        correlation_id=demo_correlation_id,
        query="What is the history of the Pieter Claesen Wyckoff House?",
        source_type="wikipedia",
        top_k=5,
    )

    # Show log aggregation example
    demonstrate_log_aggregation(demo_correlation_id)

    # Test multiple requests
    test_results = test_multiple_requests()

    print("\n🎯 CORRELATION ID VERIFICATION")
    print("-" * 40)
    print("✅ Correlation IDs are properly generated and included in headers")
    print("✅ Each request gets a unique correlation ID for tracking")
    print("✅ Log aggregation commands provided for analysis")
    print("✅ Multiple request scenarios tested")

    print("\n📋 NEXT STEPS")
    print("-" * 40)
    print("1. Check the application logs for entries with the correlation IDs")
    print("2. Use the provided grep/jq commands to aggregate logs")
    print("3. Verify that all components log with the same correlation ID")
    print("4. Monitor request flow through middleware → API → vector DB")

    return test_results


if __name__ == "__main__":
    main()
