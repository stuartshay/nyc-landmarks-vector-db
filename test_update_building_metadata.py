#!/usr/bin/env python3
"""
Simple test to update building metadata for LP-00079
"""

import sys

sys.path.append('.')

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.enhanced_metadata import get_metadata_collector
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

logger = get_logger(__name__)


def main():
    try:
        print("=== Testing Building Metadata Update ===")

        # Initialize clients
        print("Initializing Pinecone client...")
        pinecone_db = PineconeDB()

        print("Initializing metadata collector...")
        collector = get_metadata_collector()

        # Get vectors for LP-00079
        print("Querying vectors for LP-00079...")
        vectors = pinecone_db.query_vectors(
            query_vector=None,
            landmark_id='LP-00079',
            top_k=10,
            namespace_override='landmarks'
        )

        print(f"Found {len(vectors)} vectors for LP-00079")

        if not vectors:
            print("No vectors found - exiting")
            return

        # Get first vector and show current metadata
        vector = vectors[0]
        print(f"Vector ID: {vector['id']}")

        current_metadata = vector.get('metadata', {})
        building_keys = [k for k in current_metadata.keys() if k.startswith('building_')]
        print(f"Current building fields: {len(building_keys)}")

        # Get enhanced metadata
        print("Getting enhanced metadata...")
        enhanced_metadata = collector.collect_landmark_metadata('LP-00079')

        if hasattr(enhanced_metadata, "dict"):
            new_metadata_dict = enhanced_metadata.dict()
        else:
            new_metadata_dict = dict(enhanced_metadata)

        new_building_keys = [k for k in new_metadata_dict.keys() if k.startswith("building_")]
        print(f"Enhanced metadata has {len(new_building_keys)} building fields")

        if new_building_keys:
            print("Building fields that would be added:")
            for key in sorted(new_building_keys)[:5]:
                print(f"  {key}: {new_metadata_dict[key]}")

            # Show what the updated vector would look like
            updated_metadata = current_metadata.copy()
            for key in new_building_keys:
                updated_metadata[key] = new_metadata_dict[key]

            print(f"Updated vector would have {len(updated_metadata)} total metadata fields")

            # Do the actual update
            print("Performing actual update...")
            vector_to_upsert = {
                'id': vector['id'],
                'values': vector.get('values', []),
                'metadata': updated_metadata
            }

            pinecone_db._upsert_vectors_in_batches([vector_to_upsert], batch_size=1)
            print("✅ Vector updated successfully!")

        else:
            print("❌ No building metadata found to add")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
