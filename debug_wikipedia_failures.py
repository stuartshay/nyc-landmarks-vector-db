#!/usr/bin/env python3
"""
Debug script to analyze Wikipedia processing failures.
"""

from typing import List

from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.wikipedia import WikipediaProcessor

# Setup logging
logger = get_logger(__name__)

def analyze_landmark_failures(landmark_ids: List[str]) -> None:
    """Analyze specific landmark failures."""
    db_client = get_db_client()
    processor = WikipediaProcessor()
    
    print("=" * 80)
    print("DEBUGGING WIKIPEDIA PROCESSING FAILURES")
    print("=" * 80)
    
    for landmark_id in landmark_ids:
        print(f"\n--- Analyzing {landmark_id} ---")
        
        try:
            # Step 1: Check if landmark exists in the database
            landmark = db_client.get_landmark_by_id(landmark_id)
            if not landmark:
                print(f"❌ Landmark {landmark_id} not found in database")
                continue
            else:
                print(f"✅ Landmark {landmark_id} exists in database")
                if hasattr(landmark, 'buildingName') and landmark.buildingName:
                    print(f"   Building name: {landmark.buildingName}")
                elif hasattr(landmark, 'building_name') and landmark.building_name:
                    print(f"   Building name: {landmark.building_name}")
                
            # Step 2: Check for Wikipedia articles
            articles = db_client.get_wikipedia_articles(landmark_id)
            if not articles:
                print(f"❌ No Wikipedia articles found for {landmark_id}")
                continue
            else:
                print(f"✅ Found {len(articles)} Wikipedia articles for {landmark_id}")
                for i, article in enumerate(articles):
                    print(f"   Article {i+1}: {article.title}")
                    print(f"   URL: {article.url}")
                    
            # Step 3: Try to fetch Wikipedia content
            print("🔍 Attempting to fetch Wikipedia content...")
            for i, article in enumerate(articles):
                try:
                    content, rev_id = processor.wiki_fetcher.fetch_wikipedia_content(article.url)
                    if content:
                        print(f"   ✅ Article {i+1}: Successfully fetched {len(content)} chars (rev: {rev_id})")
                    else:
                        print(f"   ❌ Article {i+1}: Failed to fetch content")
                except Exception as e:
                    print(f"   ❌ Article {i+1}: Error fetching content: {e}")
                    
            # Step 4: Try full processing
            print("🔄 Attempting full Wikipedia processing...")
            try:
                success, articles_processed, chunks_embedded = processor.process_landmark_wikipedia(
                    landmark_id, chunk_size=1000, chunk_overlap=200, delete_existing=False
                )
                if success:
                    print(f"   ✅ Processing successful: {articles_processed} articles, {chunks_embedded} chunks")
                else:
                    print(f"   ❌ Processing failed: {articles_processed} articles, {chunks_embedded} chunks")
            except Exception as e:
                print(f"   ❌ Processing error: {e}")
                
        except Exception as e:
            print(f"❌ Error analyzing {landmark_id}: {e}")

def main() -> None:
    """Main debugging function."""
    # Sample of failed landmark IDs from the log
    failed_landmarks = [
        "LP-01844", "LP-01679", "LP-01687", "LP-01790", "LP-01819",
        "LP-01680", "LP-01682", "LP-01681", "LP-01683", "LP-01684"
    ]
    
    print(f"Analyzing {len(failed_landmarks)} failed landmarks...")
    analyze_landmark_failures(failed_landmarks)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
