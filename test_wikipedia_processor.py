#!/usr/bin/env python3
"""Quick test of the Wikipedia processor with building metadata."""

import sys

sys.path.append('.')

from nyc_landmarks.wikipedia.processor import WikipediaProcessor

# Test the Wikipedia processor
processor = WikipediaProcessor()

print("Testing Wikipedia processor for LP-00179...")
try:
    success, articles_processed, chunks_embedded = processor.process_landmark_wikipedia(
        'LP-00179',
        chunk_size=1000,
        chunk_overlap=200,
        delete_existing=True
    )

    print(f"Success: {success}")
    print(f"Articles processed: {articles_processed}")
    print(f"Chunks embedded: {chunks_embedded}")

    if success:
        print("✅ Wikipedia processing completed successfully!")
    else:
        print("❌ Wikipedia processing failed")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
