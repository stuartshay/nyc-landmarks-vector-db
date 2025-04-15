#!/usr/bin/env python3
"""
Pinecone DB Stats Test Script
This script tests the Pinecone connection and fetches index statistics
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from nyc_landmarks.config.settings import settings
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

def test_pinecone_stats():
    """Test the Pinecone connection and get index statistics"""
    print("\n=== NYC Landmarks Vector Database Statistics ===\n")

    # Initialize the Pinecone database client
    pinecone_db = PineconeDB()

    # Check if the connection was successful
    if pinecone_db.index:
        print(f"✅ Successfully connected to Pinecone index: {pinecone_db.index_name}")
        print(f"Namespace: {pinecone_db.namespace}")
        print(f"Dimensions: {pinecone_db.dimensions}")
        print(f"Metric: {pinecone_db.metric}")
    else:
        print("❌ Failed to connect to Pinecone. Check your credentials and network connection.")
        return

    print("\n== Index Statistics ==\n")

    try:
        # Get index statistics
        stats = pinecone_db.get_index_stats()

        # Display the stats
        print("📊 Index Statistics:")
        print(f"Dimension: {stats.get('dimension')}")
        print(f"Index Fullness: {stats.get('index_fullness')}")

        # Extract namespace information
        namespaces = stats.get('namespaces', {})
        total_vector_count = stats.get('total_vector_count', 0)

        print(f"\n🔢 Total Vector Count: {total_vector_count:,}")
        print("\n📁 Namespace Statistics:")

        # Print namespace info
        for ns_name, ns_data in namespaces.items():
            print(f"  - {ns_name}: {ns_data}")

    except Exception as e:
        print(f"❌ Error getting Pinecone stats: {e}")

    print("\n== Vector Query Test ==\n")

    try:
        # Test querying for vectors
        import numpy as np

        # Generate a random query vector with the right dimensions
        random_vector = np.random.rand(pinecone_db.dimensions).tolist()

        # Query for similar vectors
        results = pinecone_db.query_vectors(
            query_vector=random_vector,
            top_k=5
        )

        print(f"✅ Query successful, found {len(results)} results")

        # Display a sample result if available
        if results:
            print("\nSample result:")
            sample = results[0]
            print(f"ID: {sample.get('id')}")
            print(f"Score: {sample.get('score')}")
            metadata = sample.get('metadata', {})
            print(f"Metadata keys: {list(metadata.keys())}")

    except Exception as e:
        print(f"❌ Error querying vectors: {e}")

    print("\n=== Test completed ===")

if __name__ == "__main__":
    test_pinecone_stats()
