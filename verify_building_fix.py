#!/usr/bin/env python3
"""Quick script to verify building metadata in vectors"""

import sys

sys.path.append('.')

try:
    from nyc_landmarks.vectordb.pinecone_db import PineconeDB

    print("Creating PineconeDB client...")
    client = PineconeDB()

    print("Querying for LP-00079 vectors...")
    results = client.query_vectors(
        query_vector=None,  # List operation
        landmark_id='LP-00079',
        top_k=1,
        namespace_override='landmarks'
    )

    print(f"Found {len(results)} vectors for LP-00079")

    if results:
        vector = results[0]
        print(f"Vector ID: {vector['id']}")

        metadata = vector.get('metadata', {})
        building_keys = [k for k in metadata.keys() if k.startswith('building_')]
        print(f"Building fields found: {len(building_keys)}")

        if building_keys:
            print("Building fields:", sorted(building_keys)[:10])  # Show first 10

            # Show key building data
            key_fields = [
                'building_0_bbl', 'building_0_binNumber',
                'building_0_latitude', 'building_0_longitude',
                'building_0_address', 'building_0_name'
            ]

            print("\nKey building metadata:")
            for field in key_fields:
                if field in metadata:
                    print(f"  {field}: {metadata[field]}")

            print(f"\n✅ SUCCESS: Found {len(building_keys)} building metadata fields!")
        else:
            print("❌ No building fields found in metadata")
    else:
        print("❌ No vectors found for LP-00079")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
