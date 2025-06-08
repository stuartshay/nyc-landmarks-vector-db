#!/usr/bin/env python3
"""
Test script to verify API validation and warning logs.
"""

import requests

BASE_URL = "http://localhost:8000"


def test_invalid_requests() -> None:
    """Test various invalid API requests to verify warning logs."""

    print("Testing invalid API requests to generate warning logs...")

    # Test 1: Empty query
    print("\n1. Testing empty query...")
    response = requests.post(
        f"{BASE_URL}/api/query/search",
        json={"query": "", "top_k": 5},
        headers={"User-Agent": "ValidationTestBot/1.0"},
        timeout=30
    )
    print(f"Response: {response.status_code} - {response.text}")

    # Test 2: Query too long
    print("\n2. Testing query too long...")
    long_query = "x" * 1001  # Over 1000 character limit
    response = requests.post(
        f"{BASE_URL}/api/query/search",
        json={"query": long_query, "top_k": 5},
        headers={"User-Agent": "ValidationTestBot/1.0"},
        timeout=30
    )
    print(f"Response: {response.status_code} - {response.text}")

    # Test 3: Invalid top_k
    print("\n3. Testing invalid top_k (too large)...")
    response = requests.post(
        f"{BASE_URL}/api/query/search",
        json={"query": "Central Park", "top_k": 100},
        headers={"User-Agent": "ValidationTestBot/1.0"},
        timeout=30
    )
    print(f"Response: {response.status_code} - {response.text}")

    # Test 4: Invalid source_type
    print("\n4. Testing invalid source_type...")
    response = requests.post(
        f"{BASE_URL}/api/query/search",
        json={"query": "Central Park", "source_type": "invalid_source", "top_k": 5},
        headers={"User-Agent": "ValidationTestBot/1.0"},
        timeout=30
    )
    print(f"Response: {response.status_code} - {response.text}")

    # Test 5: Suspicious content (potential XSS)
    print("\n5. Testing suspicious content...")
    response = requests.post(
        f"{BASE_URL}/api/query/search",
        json={"query": "<script>alert('xss')</script>", "top_k": 5},
        headers={"User-Agent": "ValidationTestBot/1.0"},
        timeout=30
    )
    print(f"Response: {response.status_code} - {response.text}")

    # Test 6: Chat API with empty message
    print("\n6. Testing chat API with empty message...")
    response = requests.post(
        f"{BASE_URL}/api/chat/message",
        json={"message": "", "conversation_id": "test-123"},
        headers={"User-Agent": "ValidationTestBot/1.0"},
        timeout=30
    )
    print(f"Response: {response.status_code} - {response.text}")

    # Test 7: Valid request (should work)
    print("\n7. Testing valid request...")
    response = requests.post(
        f"{BASE_URL}/api/query/search",
        json={"query": "Central Park landmarks", "top_k": 3},
        headers={"User-Agent": "ValidationTestBot/1.0"},
        timeout=30
    )
    print(f"Response: {response.status_code} - Success!")

    print("\nAll validation tests completed!")
    print("Check Google Cloud Logging for warning entries with validation_error fields.")


if __name__ == "__main__":
    test_invalid_requests()
