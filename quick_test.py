#!/usr/bin/env python3
"""Quick test to see debug output."""

import sys

sys.path.append('.')

from dotenv import load_dotenv

load_dotenv()

from nyc_landmarks.wikipedia.processor import WikipediaProcessor

print("Processing LP-00179...")
processor = WikipediaProcessor()
success, articles, chunks = processor.process_landmark_wikipedia('LP-00179', delete_existing=True)
print(f"Result: success={success}, articles={articles}, chunks={chunks}")
