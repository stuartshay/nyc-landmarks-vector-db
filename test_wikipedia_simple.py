#!/usr/bin/env python3
"""Simple script to test Wikipedia processing with building metadata."""

import sys

sys.path.append('.')

from dotenv import load_dotenv

load_dotenv()

from nyc_landmarks.wikipedia.processor import WikipediaProcessor


def main():
    """Process LP-00179 Wikipedia articles."""
    try:
        print("🚀 Starting Wikipedia processing for LP-00179...")

        processor = WikipediaProcessor()

        # Process the landmark with delete_existing=True to force recreation
        success, articles_processed, chunks_embedded = processor.process_landmark_wikipedia(
            landmark_id='LP-00179',
            chunk_size=1000,
            chunk_overlap=200,
            delete_existing=True
        )

        print(f"✅ Processing completed!")
        print(f"   Success: {success}")
        print(f"   Articles processed: {articles_processed}")
        print(f"   Chunks embedded: {chunks_embedded}")

        if success and chunks_embedded > 0:
            # Now verify that building metadata was included
            print("\n🔍 Verifying building metadata...")

            from nyc_landmarks.vectordb.pinecone_db import PineconeDB
            pinecone_db = PineconeDB()

            # Query for the vectors we just created
            results = pinecone_db.query_vectors(
                query_vector=None,  # List operation
                landmark_id='LP-00179',
                top_k=1,
                namespace_override='landmarks'
            )

            if results:
                vector = results[0]
                metadata = vector.get('metadata', {})
                building_fields = {k: v for k, v in metadata.items() if k.startswith('building_')}

                print(f"   Found {len(building_fields)} building metadata fields")

                if building_fields:
                    print("   ✅ SUCCESS: Building metadata is included!")
                    print("   Sample fields:")
                    for k, v in list(building_fields.items())[:5]:
                        print(f"     {k}: {v}")
                else:
                    print("   ❌ FAILED: No building metadata found")
            else:
                print("   ❌ No vectors found for LP-00179")

        return success

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
