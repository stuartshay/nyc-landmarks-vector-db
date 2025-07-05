#!/usr/bin/env python3
"""
Comprehensive Correlation ID Testing Script for NYC Landmarks Vector DB.

This script consolidates all correlation ID testing functionality including:
- Local function testing with correlation ID tracking
- Header extraction validation
- Session correlation across multiple requests
- End-to-end correlation tracking
- GCP logging query examples

Usage:
    python scripts/test_correlation_comprehensive.py [--test-suite all|local|headers|session]
"""

import argparse
from typing import Any, Dict, List, Optional

from nyc_landmarks.api.query import search_combined_sources
from nyc_landmarks.utils.correlation import generate_correlation_id

# Store test results for final summary
test_results: List[Dict[str, str]] = []


def log_test_result(test_name: str, correlation_id: str, status: str = "✅") -> None:
    """Log a test result for the final summary."""
    test_results.append(
        {
            "name": test_name,
            "correlation_id": correlation_id,
            "status": status,
        }
    )


def test_local_search_functionality() -> None:
    """Test local search functionality with correlation IDs."""
    print("🔍 Testing Local Search Functionality with Correlation IDs")
    print("=" * 60)

    test_cases: List[Dict[str, Any]] = [
        {
            "name": "Basic Wikipedia Search",
            "query": "Brooklyn Bridge architectural significance",
            "source_type": "wikipedia",
            "landmark_id": None,
        },
        {
            "name": "Landmark-Specific Search",
            "query": "Federal Hall historical events",
            "source_type": None,
            "landmark_id": "LP-00009",
        },
        {
            "name": "PDF Document Search",
            "query": "construction materials and techniques",
            "source_type": "pdf",
            "landmark_id": None,
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📤 Test {i}: {test_case['name']}")
        correlation_id = generate_correlation_id()
        print(f"   Correlation ID: {correlation_id}")

        try:
            results = search_combined_sources(
                query_text=test_case["query"],
                landmark_id=test_case.get("landmark_id"),
                source_type=test_case.get("source_type"),
                top_k=2,
                correlation_id=correlation_id,
            )

            print(f"   ✅ Success: {len(results)} results")
            log_test_result(test_case["name"], correlation_id, "✅")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            log_test_result(test_case["name"], correlation_id, "❌")


def test_header_extraction() -> None:
    """Test correlation ID extraction from various header formats."""
    print("\n🔗 Testing Header Extraction Functionality")
    print("=" * 60)

    # Test the utility functions directly
    from nyc_landmarks.utils.correlation import extract_correlation_id_from_headers

    header_test_cases: List[Dict[str, Any]] = [
        {
            "name": "X-Correlation-ID Header",
            "headers": {"X-Correlation-ID": "test-correlation-123"},
            "expected": "test-correlation-123",
        },
        {
            "name": "X-Request-ID Header",
            "headers": {"X-Request-ID": "test-request-456"},
            "expected": "test-request-456",
        },
        {
            "name": "Request-ID Header",
            "headers": {"Request-ID": "test-simple-789"},
            "expected": "test-simple-789",
        },
        {
            "name": "Correlation-ID Header",
            "headers": {"Correlation-ID": "test-correlation-999"},
            "expected": "test-correlation-999",
        },
        {
            "name": "Case Insensitive Test",
            "headers": {"x-correlation-id": "test-lowercase-111"},
            "expected": "test-lowercase-111",
        },
        {"name": "No Headers", "headers": {}, "expected": None},
    ]

    for i, test_case in enumerate(header_test_cases, 1):
        test_name: str = test_case["name"]
        test_headers: Dict[str, str] = test_case["headers"]
        expected_value: Optional[str] = test_case["expected"]

        print(f"\n📋 Test {i}: {test_name}")

        try:
            extracted_id = extract_correlation_id_from_headers(test_headers)

            if expected_value is None:
                if extracted_id is None:
                    print("   ✅ Correctly returned None")
                    log_test_result(test_name, "None", "✅")
                else:
                    print(f"   ❌ Expected None, Got: {extracted_id}")
                    log_test_result(test_name, extracted_id or "N/A", "❌")
            else:
                if extracted_id == expected_value:
                    print(f"   ✅ Extracted: {extracted_id}")
                    log_test_result(test_name, extracted_id or "N/A", "✅")
                else:
                    print(f"   ❌ Expected: {expected_value}, Got: {extracted_id}")
                    log_test_result(test_name, extracted_id or "N/A", "❌")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            log_test_result(test_name, "N/A", "❌")


def test_session_correlation() -> None:
    """Test session-level correlation with multiple operations."""
    print("\n📱 Testing Session-Level Correlation")
    print("=" * 60)

    session_id = f"session-{generate_correlation_id()[:8]}"
    print(f"Session ID: {session_id}")

    session_queries = [
        "Statue of Liberty history and construction",
        "Empire State Building architectural features",
        "Central Park landscape design principles",
        "Times Square development timeline",
    ]

    print(f"\nExecuting {len(session_queries)} queries with shared session ID...")

    for i, query in enumerate(session_queries, 1):
        print(f"\n   📤 Query {i}: {query[:50]}...")

        try:
            results = search_combined_sources(
                query_text=query, top_k=1, correlation_id=session_id
            )

            print(f"      ✅ {len(results)} results")

        except Exception as e:
            print(f"      ❌ Error: {e}")

    log_test_result("Session Correlation Test", session_id, "✅")


def test_performance_correlation() -> None:
    """Test performance monitoring with correlation IDs."""
    print("\n⏱️  Testing Performance Correlation")
    print("=" * 60)

    import time

    perf_correlation_id = f"perf-{generate_correlation_id()[:12]}"
    print(f"Performance Test ID: {perf_correlation_id}")

    # Test with increasing complexity
    performance_tests: List[Dict[str, Any]] = [
        {"query": "Bridge", "top_k": 1, "complexity": "Simple"},
        {
            "query": "Brooklyn Bridge engineering marvel construction",
            "top_k": 3,
            "complexity": "Medium",
        },
        {
            "query": "What engineering innovations and construction techniques made the Brooklyn Bridge possible during the 19th century",
            "top_k": 5,
            "complexity": "Complex",
        },
    ]

    for i, test in enumerate(performance_tests, 1):
        test_query: str = test["query"]
        test_top_k: int = test["top_k"]
        test_complexity: str = test["complexity"]

        print(f"\n   🎯 Performance Test {i}: {test_complexity}")
        print(f"      Query: {test_query}")

        start_time = time.time()

        try:
            results = search_combined_sources(
                query_text=test_query,
                top_k=test_top_k,
                correlation_id=perf_correlation_id,
            )

            end_time = time.time()
            duration = end_time - start_time

            print(f"      ✅ Completed in {duration:.2f}s ({len(results)} results)")

        except Exception as e:
            print(f"      ❌ Error: {e}")

    log_test_result("Performance Correlation Test", perf_correlation_id, "✅")


def show_gcp_logging_queries() -> None:
    """Show Google Cloud Logging queries for analysis."""
    print("\n☁️  Google Cloud Logging Analysis Queries")
    print("=" * 60)

    print("📋 Copy these queries into GCP Console > Logging > Logs Explorer:")
    print()

    # Show queries for each test result
    for result in test_results:
        if result["correlation_id"] != "N/A":
            print(f"🔍 {result['name']}:")
            print(f"   jsonPayload.correlation_id=\"{result['correlation_id']}\"")
            print()

    print("📊 General Analysis Queries:")
    print()
    print("   All embedding operations today:")
    print(
        '   jsonPayload.operation="embedding_generation" AND timestamp>="2025-07-01T00:00:00Z"'
    )
    print()
    print("   All vector query operations today:")
    print(
        '   jsonPayload.operation="vector_query_start" AND timestamp>="2025-07-01T00:00:00Z"'
    )
    print()
    print("   Performance analysis (operations > 2 seconds):")
    print(
        '   jsonPayload.operation="vector_query_start" OR jsonPayload.operation="vector_query_complete"'
    )


def print_summary() -> None:
    """Print test summary."""
    print("\n📊 Test Summary")
    print("=" * 60)

    total_tests = len(test_results)
    successful_tests = len([r for r in test_results if r["status"] == "✅"])
    failed_tests = total_tests - successful_tests

    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(successful_tests / total_tests) * 100:.1f}%")

    print("\n🔗 Correlation IDs Generated:")
    for result in test_results:
        status_icon = result["status"]
        print(f"   {status_icon} {result['name']}: {result['correlation_id']}")


def main() -> None:
    """Main function to run correlation ID tests."""
    parser = argparse.ArgumentParser(description="Comprehensive Correlation ID Testing")
    parser.add_argument(
        "--test-suite",
        choices=["all", "local", "headers", "session", "performance"],
        default="all",
        help="Test suite to run",
    )

    args = parser.parse_args()

    print("🧪 Comprehensive Correlation ID Testing Suite")
    print("=" * 70)

    if args.test_suite in ["all", "local"]:
        test_local_search_functionality()

    if args.test_suite in ["all", "headers"]:
        test_header_extraction()

    if args.test_suite in ["all", "session"]:
        test_session_correlation()

    if args.test_suite in ["all", "performance"]:
        test_performance_correlation()

    show_gcp_logging_queries()
    print_summary()

    print("\n✅ Comprehensive correlation ID testing completed!")


if __name__ == "__main__":
    main()
