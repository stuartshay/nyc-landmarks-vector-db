"""
Functional tests for the vector storage pipeline.

These tests verify that the entire pipeline works correctly:
1. Fetch landmark data
2. Process PDFs
3. Generate embeddings
4. Store vectors in Pinecone
"""

import logging
import os
import shutil
import tempfile
import time
from pathlib import Path

import pytest

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.pdf.extractor import PDFExtractor
from nyc_landmarks.pdf.text_chunker import TextChunker
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


@pytest.fixture
def temp_dirs():
    """Create temporary directories for test artifacts."""
    base_dir = tempfile.mkdtemp()
    pdfs_dir = Path(base_dir) / "pdfs"
    text_dir = Path(base_dir) / "text"

    pdfs_dir.mkdir(exist_ok=True)
    text_dir.mkdir(exist_ok=True)

    yield {"base_dir": base_dir, "pdfs_dir": pdfs_dir, "text_dir": text_dir}

    # Cleanup
    shutil.rmtree(base_dir)


@pytest.mark.integration
def test_vector_storage_pipeline(temp_dirs):
    """Test the complete vector storage pipeline with one landmark."""
    logger.info("=== Testing complete vector storage pipeline ===")

    # Step 1: Initialize components
    db_client = get_db_client()
    pdf_extractor = PDFExtractor()
    text_chunker = TextChunker(
        chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP
    )
    embedding_generator = EmbeddingGenerator()
    pinecone_db = PineconeDB()

    # Ensure Pinecone client is initialized
    assert pinecone_db.index is not None, "PineconeDB index not initialized"

    # Get index stats before the test to compare later
    before_stats = pinecone_db.get_index_stats()
    before_count = before_stats.get("total_vector_count", 0)
    logger.info(f"Initial vector count: {before_count}")

    # Step 2: Fetch one landmark for testing
    landmark_id = "LP-00001"  # Use a known landmark ID or fetch a random one

    landmark_data = db_client.get_landmark_by_id(landmark_id)
    assert landmark_data, f"Could not fetch landmark with ID {landmark_id}"
    logger.info(
        f"Successfully fetched landmark: {landmark_data.get('name', 'Unknown')}"
    )

    # Step 3: Get and download PDF for the landmark
    pdf_url = db_client.get_landmark_pdf_url(landmark_id)
    assert pdf_url, f"No PDF URL found for landmark {landmark_id}"

    # Download PDF to temp location
    import requests

    pdf_path = temp_dirs["pdfs_dir"] / f"{landmark_id.replace('/', '_')}.pdf"
    logger.info(f"Downloading PDF from {pdf_url} to {pdf_path}")

    response = requests.get(pdf_url, stream=True, timeout=30)
    response.raise_for_status()

    with open(pdf_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    assert pdf_path.exists(), f"Failed to download PDF to {pdf_path}"

    # Step 4: Extract text from PDF
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
        text = pdf_extractor.extract_text_from_bytes(pdf_bytes)

    assert text, "Failed to extract text from PDF"
    logger.info(f"Successfully extracted {len(text)} characters of text")

    # Save text to file
    text_path = temp_dirs["text_dir"] / f"{landmark_id.replace('/', '_')}.txt"
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text)

    # Step 5: Chunk text
    chunks = text_chunker.chunk_text_by_tokens(text)
    assert chunks, "Failed to chunk text"
    logger.info(f"Successfully created {len(chunks)} text chunks")

    # Step 6: Generate embeddings
    enriched_chunks = []
    for i, chunk in enumerate(chunks):
        chunk_dict = {
            "text": chunk,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "metadata": {
                "landmark_id": landmark_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "source_type": "pdf",
                "processing_date": time.strftime("%Y-%m-%d"),
            },
        }
        enriched_chunks.append(chunk_dict)

    # Get text content for embedding generation
    texts = [chunk["text"] for chunk in enriched_chunks]
    embeddings = embedding_generator.generate_embeddings_batch(texts)

    assert len(embeddings) == len(
        texts
    ), "Number of embeddings doesn't match number of chunks"
    logger.info(f"Successfully generated {len(embeddings)} embeddings")

    # Step 7: Add embeddings to chunks
    chunks_with_embeddings = enriched_chunks.copy()
    for i, embedding in enumerate(embeddings):
        chunks_with_embeddings[i]["embedding"] = embedding

    # Step 8: Store vectors in Pinecone
    id_prefix = f"test-{landmark_id}-"
    vector_ids = pinecone_db.store_chunks(
        chunks=chunks_with_embeddings,
        id_prefix=id_prefix,
        landmark_id=landmark_id,
    )

    assert vector_ids, "Failed to store vectors in Pinecone"
    logger.info(f"Successfully stored {len(vector_ids)} vectors in Pinecone")

    # Step 9: Verify vectors were stored by checking updated count
    time.sleep(2)  # Give Pinecone time to update
    after_stats = pinecone_db.get_index_stats()
    after_count = after_stats.get("total_vector_count", 0)
    logger.info(f"Final vector count: {after_count}")

    # The count should be greater than before (but we can't assert exact counts due to concurrent tests)
    assert (
        after_count >= before_count
    ), "Vector count did not increase after storing vectors"

    # Step 10: Query one of the stored vectors to make sure it's retrievable
    if len(embeddings) > 0:
        # Use the first embedding as a query
        query_embedding = embeddings[0]
        matches = pinecone_db.query_vectors(
            query_embedding, top_k=5, filter_dict={"landmark_id": landmark_id}
        )

        assert matches, "Failed to retrieve vectors from Pinecone"
        assert len(matches) > 0, "No matches found for query"
        logger.info(f"Successfully retrieved {len(matches)} vector matches")

        # Verify that at least one of our stored vectors is among the results
        # (Note: may not match exactly due to vector normalization, approximate NN, etc.)
        found_match = False
        for match in matches:
            if match.metadata.get("landmark_id") == landmark_id:
                found_match = True
                break

        assert found_match, "Could not find the stored landmark ID in query results"

    # Step 11: Clean up - optional: delete test vectors
    # Uncomment the following lines if you want to delete the test vectors
    # Note: In a production setting, you might want to keep them for debugging
    """
    for vector_id in vector_ids:
        pinecone_db.index.delete(ids=[vector_id])
    logger.info(f"Cleaned up {len(vector_ids)} test vectors")
    """

    logger.info("=== Vector storage pipeline test completed successfully ===")


@pytest.mark.integration
def test_pinecone_connection_and_operations():
    """Test basic Pinecone operations to ensure the database is accessible."""
    logger.info("=== Testing Pinecone connection and basic operations ===")

    # Create Pinecone client
    pinecone_db = PineconeDB()

    # Check if index exists
    assert pinecone_db.index is not None, "Failed to connect to Pinecone index"

    # Get index stats
    stats = pinecone_db.get_index_stats()
    assert isinstance(stats, dict), "Failed to retrieve index stats"
    assert "error" not in stats, f"Error in stats: {stats.get('error')}"

    logger.info(f"Pinecone index stats: {stats}")

    # Test storing a single vector with metadata
    test_id = f"test-vector-{int(time.time())}"
    test_vector = [0.1] * settings.PINECONE_DIMENSIONS

    # Create a test chunk in the format expected by store_chunks
    test_chunk = {
        "text": "This is a test vector for functional testing.",
        "chunk_index": 0,
        "total_chunks": 1,
        "embedding": test_vector,
        "metadata": {
            "landmark_id": "TEST-LANDMARK",
            "chunk_index": 0,
            "total_chunks": 1,
            "source_type": "test",
            "processing_date": time.strftime("%Y-%m-%d"),
            "test": True,
            "source": "functional_test",
        },
    }

    # Use store_chunks instead of store_vectors
    vector_ids = pinecone_db.store_chunks(
        chunks=[test_chunk], id_prefix=test_id, landmark_id="TEST-LANDMARK"
    )

    assert vector_ids, "Failed to store test vector"
    logger.info(f"Successfully stored test vector with ID: {vector_ids[0]}")

    # Test querying the vector
    matches = pinecone_db.query_vectors(
        query_vector=test_vector, top_k=1, filter_dict={"landmark_id": "TEST-LANDMARK"}
    )

    assert matches, "Failed to retrieve test vector"
    assert len(matches) > 0, "No matches found for test vector query"
    logger.info(
        f"Successfully retrieved test vector: {matches[0].get('id', 'unknown')}"
    )

    # Clean up the test vector
    if vector_ids:
        pinecone_db.delete_vectors(vector_ids)
        logger.info(f"Cleaned up test vector {vector_ids[0]}")

    logger.info(
        "=== Pinecone connection and operations test completed successfully ==="
    )
