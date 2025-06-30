#!/usr/bin/env python3
"""
Test script to demonstrate enhanced embedding correlation logging.

This script shows how the correlation ID is now tracked through
the embedding generation process for both API and non-API usage.
"""

from nyc_landmarks.api.query import compare_source_results, search_combined_sources
from nyc_landmarks.utils.correlation import generate_correlation_id

# No custom logging configuration - use the project's existing setup
# This prevents duplicate handlers and logging conflicts


def demonstrate_correlation_logging() -> None:
    """Demonstrate enhanced correlation logging for embedding generation."""
    print("🔗 Enhanced Embedding Correlation Logging Demonstration")
    print("=" * 60)

    # Test 1: Non-API search with correlation ID
    print("\n📍 Test 1: Non-API Search with Correlation Tracking")
    correlation_id_1 = generate_correlation_id()
    print(f"   Correlation ID: {correlation_id_1}")
    print("   Query: Federal Hall historical significance")

    try:
        results_1 = search_combined_sources(
            query_text="What is the historical significance of Federal Hall National Memorial?",
            landmark_id="LP-00009",
            source_type="wikipedia",
            top_k=2,
            correlation_id=correlation_id_1,
        )
        print(f"   ✅ Search completed: {len(results_1)} results")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 2: Source comparison with correlation ID
    print("\n📍 Test 2: Source Comparison with Correlation Tracking")
    correlation_id_2 = generate_correlation_id()
    print(f"   Correlation ID: {correlation_id_2}")
    print("   Query: Brooklyn Bridge construction details")

    try:
        comparison_results = compare_source_results(
            query_text="How was the Brooklyn Bridge engineered and constructed?",
            landmark_id=None,
            top_k=2,
            correlation_id=correlation_id_2,
        )
        wiki_count = len(comparison_results["wikipedia_results"])
        pdf_count = len(comparison_results["pdf_results"])
        combined_count = len(comparison_results["combined_results"])
        print(
            f"   ✅ Comparison completed: {wiki_count} wiki, {pdf_count} pdf, {combined_count} combined"
        )
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: Multiple queries with same correlation ID (session simulation)
    print("\n📍 Test 3: Session Simulation (Multiple Queries, Same Correlation ID)")
    session_correlation_id = f"session-{generate_correlation_id()[:8]}"
    print(f"   Session Correlation ID: {session_correlation_id}")

    session_queries = [
        (
            "Wyckoff House",
            "What is the history of the Pieter Claesen Wyckoff House?",
            "LP-00001",
        ),
        (
            "Federal Hall",
            "What happened at Federal Hall during Washington's inauguration?",
            "LP-00009",
        ),
        (
            "Harlem YMCA",
            "What was the role of the Harlem YMCA in the community?",
            "LP-01973",
        ),
    ]

    for i, (name, query, landmark_id) in enumerate(session_queries, 1):
        print(f"\n   📤 Session Query {i}: {name}")
        try:
            session_results = search_combined_sources(
                query_text=query,
                landmark_id=landmark_id,
                top_k=1,
                correlation_id=session_correlation_id,
            )
            print(f"      ✅ Query {i} completed: {len(session_results)} results")
        except Exception as e:
            print(f"      ❌ Query {i} error: {e}")

    print("\n🎯 Correlation Logging Summary")
    print("=" * 60)
    print("📊 Generated Correlation IDs:")
    print(f"   Test 1 (Non-API): {correlation_id_1}")
    print(f"   Test 2 (Comparison): {correlation_id_2}")
    print(f"   Test 3 (Session): {session_correlation_id}")

    print("\n🔍 GCP Logging Queries to View Results:")
    print(
        f"   Test 1: jsonPayload.correlation_id=\"{correlation_id_1}\" AND jsonPayload.operation=\"embedding_generation\""
    )
    print(
        f"   Test 2: jsonPayload.correlation_id=\"{correlation_id_2}\" AND jsonPayload.operation=\"embedding_generation\""
    )
    print(
        f"   Test 3: jsonPayload.correlation_id=\"{session_correlation_id}\" AND jsonPayload.operation=\"embedding_generation\""
    )

    print("\n✅ Enhanced embedding correlation logging demonstration completed!")
    print(
        "   All embedding operations now include correlation IDs for end-to-end tracing."
    )


if __name__ == "__main__":
    demonstrate_correlation_logging()
