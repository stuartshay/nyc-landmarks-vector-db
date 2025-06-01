#!/usr/bin/env python3
"""
Test script to verify the Wikipedia processing fix.
"""

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.wikipedia import WikipediaProcessor

logger = get_logger(__name__)

def test_landmark_without_wikipedia() -> bool:
    """Test processing a landmark that has no Wikipedia articles."""
    processor = WikipediaProcessor()

    # Test with a landmark that we know has no Wikipedia articles
    landmark_id = "LP-01844"

    print(f"Testing Wikipedia processing for {landmark_id}...")

    success, articles_processed, chunks_embedded = processor.process_landmark_wikipedia(
        landmark_id, chunk_size=1000, chunk_overlap=200, delete_existing=False
    )

    print(f"Results for {landmark_id}:")
    print(f"  Success: {success}")
    print(f"  Articles processed: {articles_processed}")
    print(f"  Chunks embedded: {chunks_embedded}")

    # This should now return True (success) even with 0 articles
    if success and articles_processed == 0 and chunks_embedded == 0:
        print("✅ FIXED: Landmark with no Wikipedia articles correctly returns success=True")
        return True
    else:
        print("❌ NOT FIXED: Still treating no articles as failure")
        return False

def test_multiple_landmarks() -> None:
    """Test multiple landmarks to verify the fix."""
    processor = WikipediaProcessor()

    # Sample of landmarks that failed before
    test_landmarks = ["LP-01844", "LP-01679", "LP-01687", "LP-01790", "LP-01819"]

    success_count = 0
    total_count = len(test_landmarks)

    print(f"\nTesting {total_count} landmarks...")

    for landmark_id in test_landmarks:
        try:
            success, articles_processed, chunks_embedded = processor.process_landmark_wikipedia(
                landmark_id, chunk_size=1000, chunk_overlap=200, delete_existing=False
            )

            if success:
                success_count += 1
                print(f"✅ {landmark_id}: success={success}, articles={articles_processed}, chunks={chunks_embedded}")
            else:
                print(f"❌ {landmark_id}: success={success}, articles={articles_processed}, chunks={chunks_embedded}")

        except Exception as e:
            print(f"❌ {landmark_id}: Exception occurred: {e}")

    success_rate = (success_count / total_count) * 100
    print("\nTest Results:")
    print(f"Success rate: {success_rate:.1f}% ({success_count}/{total_count})")

    if success_rate >= 80:
        print("✅ SUCCESS: Fix appears to be working - success rate is now above 80%")
    else:
        print("❌ NEEDS MORE WORK: Success rate still below 80%")

if __name__ == "__main__":
    print("=" * 80)
    print("TESTING WIKIPEDIA PROCESSING FIX")
    print("=" * 80)

    # Test single landmark
    test_landmark_without_wikipedia()

    # Test multiple landmarks
    test_multiple_landmarks()

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
