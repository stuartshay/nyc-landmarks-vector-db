"""
Integration test for metadata consistency.

This test verifies that metadata is consistently maintained between
the CoreDataStore API and Pinecone vectors with our fixed ID implementation.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pytest

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.vectordb.enhanced_metadata import get_metadata_collector
from nyc_landmarks.vectordb.pinecone_db import PineconeDB


@pytest.mark.integration
def test_metadata_consistency_with_fixed_ids():
    """Test that metadata is consistently maintained with fixed IDs."""
    # Skip test if no Pinecone connection
    pinecone_db = PineconeDB()
    if not pinecone_db.index:
        pytest.skip("No Pinecone index available")

    # Initialize clients and tools
    db_client = get_db_client()
    metadata_collector = get_metadata_collector()
    embedding_generator = EmbeddingGenerator()

    # Use a real landmark ID that's likely to be in the database
    landmark_id = "LP-00001"

    # Step 1: Collect metadata from API
    api_metadata = db_client.get_landmark_metadata(landmark_id)
    if not api_metadata:
        pytest.skip(f"No API metadata found for landmark {landmark_id}")

    # Step 2: Create a test chunk with fixed ID
    enhanced_metadata = metadata_collector.collect_landmark_metadata(landmark_id)

    # Create test embedding
    query_text = api_metadata.get("name", landmark_id)
    embedding = embedding_generator.generate_embedding(query_text)

    # Create a chunk
    chunk = {
        "text": f"Test chunk for landmark {landmark_id}",
        "chunk_index": 0,
        "total_chunks": 1,
        "metadata": {
            "landmark_id": landmark_id,  # Use the full LP-XXXXX format
            "chunk_index": 0,
            "total_chunks": 1,
            "source_type": "test",
        },
        "embedding": embedding,
    }

    # Step 3: Store the vector with fixed ID
    vector_ids = pinecone_db.store_chunks(
        chunks=[chunk],
        landmark_id=landmark_id,
        use_fixed_ids=True,
        delete_existing=True,  # This should replace existing vectors
    )

    # Verify that the vector ID follows the expected pattern
    expected_id = f"{landmark_id}-chunk-0"
    assert (
        expected_id in vector_ids
    ), f"Expected ID {expected_id} not found in {vector_ids}"

    # Step 4: Query for the vector to check metadata consistency
    filter_dict = {"landmark_id": landmark_id}
    results = pinecone_db.query_vectors(
        query_vector=embedding, top_k=1, filter_dict=filter_dict
    )

    # Verify that we found a match
    assert results and len(results) > 0, f"No vectors found for landmark {landmark_id}"

    # Get the metadata
    pinecone_metadata = results[0].get("metadata", {})

    # Step 5: Compare enhanced metadata with Pinecone metadata
    # Identify which fields should be checked
    fields_to_check = [
        "landmark_id",
        "name",
        "borough",
        "style",
        "type",
        "designation_date",
    ]

    for field in fields_to_check:
        # Skip fields that might not be in both
        if field not in enhanced_metadata or field not in pinecone_metadata:
            continue

        # Compare values
        enhanced_value = enhanced_metadata[field]
        pinecone_value = pinecone_metadata[field]

        # Handle potential type differences (strings vs numbers, etc.)
        if isinstance(enhanced_value, str) and isinstance(pinecone_value, str):
            assert (
                enhanced_value == pinecone_value
            ), f"Field {field} mismatch: {enhanced_value} != {pinecone_value}"
        else:
            # For non-string values, convert to string for comparison
            assert str(enhanced_value) == str(
                pinecone_value
            ), f"Field {field} mismatch: {enhanced_value} != {pinecone_value}"

    # Verify the landmark_id format is preserved exactly
    assert (
        pinecone_metadata["landmark_id"] == landmark_id
    ), f"Landmark ID mismatch: {pinecone_metadata['landmark_id']} != {landmark_id}"
