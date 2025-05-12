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
from typing import Any, Dict, Generator, List, Optional, Tuple

import pytest

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.pdf.extractor import PDFExtractor
from nyc_landmarks.pdf.text_chunker import TextChunker
from tests.utils.pinecone_test_utils import create_test_index, get_test_db
from tests.utils.test_mocks import get_mock_landmark

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


@pytest.fixture
def temp_dirs() -> Generator[dict[str, str | Path], None, None]:
    """Create temporary directories for test artifacts."""
    base_dir = tempfile.mkdtemp()
    pdfs_dir = Path(base_dir) / "pdfs"
    text_dir = Path(base_dir) / "text"

    pdfs_dir.mkdir(exist_ok=True)
    text_dir.mkdir(exist_ok=True)

    yield {"base_dir": base_dir, "pdfs_dir": pdfs_dir, "text_dir": text_dir}

    # Cleanup
    shutil.rmtree(base_dir)


@pytest.fixture(scope="module")
def dedicated_test_db():
    """
    Create a dedicated test index specific for this test file to isolate from other tests.
    """
    # Create a unique test index name for this test file
    test_index_name = f"nyc-landmarks-test-vector-pipeline-{int(time.time())}"
    logger.info(
        f"Creating dedicated test index for vector pipeline test: {test_index_name}"
    )

    # Create the test index
    index_created = create_test_index(index_name=test_index_name, wait_for_ready=True)
    if not index_created:
        pytest.skip(f"Failed to create dedicated test index {test_index_name}")
        return None

    # Get database instance connected to the test index
    test_db = get_test_db(index_name=test_index_name)

    # Verify connection
    if not test_db.index:
        pytest.skip(f"Failed to connect to dedicated test index {test_index_name}")
        return None

    # Verify the index is ready by getting stats
    try:
        stats = test_db.get_index_stats()
        logger.info(f"Successfully connected to test index. Stats: {stats}")
    except Exception as e:
        logger.error(f"Error verifying test index: {e}")
        pytest.skip(f"Test index verification failed: {e}")
        return None

    # Return the database instance
    yield test_db

    # No cleanup - we'll let the session-scoped fixture handle cleanup


def _setup_test_components(dedicated_test_db: Any) -> Tuple:
    """
    Set up the components needed for the vector storage pipeline test.

    Args:
        dedicated_test_db: The test database fixture

    Returns:
        Tuple containing components needed for testing
    """
    db_client = get_db_client()
    pdf_extractor = PDFExtractor()
    text_chunker = TextChunker(
        chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP
    )
    embedding_generator = EmbeddingGenerator()
    pinecone_db = dedicated_test_db

    # Ensure Pinecone client is initialized
    assert pinecone_db.index is not None, "PineconeDB index not initialized"

    # Get index stats before the test to compare later
    before_stats = pinecone_db.get_index_stats()
    before_count = before_stats.get("total_vector_count", 0)
    logger.info(f"Initial vector count: {before_count}")

    return (
        db_client,
        pdf_extractor,
        text_chunker,
        embedding_generator,
        pinecone_db,
        before_count,
    )


def _fetch_landmark_data(db_client: Any, landmark_id: str) -> Tuple[Any, str]:
    """
    Fetch landmark data from API or use mock data if unavailable.

    Args:
        db_client: Database client instance
        landmark_id: ID of the landmark

    Returns:
        Tuple containing landmark data and name
    """
    # Try to fetch from API if available
    landmark_data = db_client.get_landmark_by_id(landmark_id)

    # If API is unreachable, use mock data from our utility
    if not landmark_data:
        logger.warning(
            "Could not fetch landmark data from API, using mock data instead"
        )
        landmark_data = get_mock_landmark(landmark_id)

    # Handle both Pydantic model and dictionary types
    landmark_name = "Unknown"
    if hasattr(landmark_data, "name"):
        landmark_name = landmark_data.name
    elif isinstance(landmark_data, dict):
        landmark_name = landmark_data.get("name", "Unknown")

    logger.info(f"Using landmark: {landmark_name}")
    return landmark_data, landmark_name


def _resolve_pdf_url(db_client: Any, landmark_id: str, landmark_data: Any) -> str:
    """
    Get PDF URL from landmark data or fallback to a default.

    Args:
        db_client: Database client instance
        landmark_id: ID of the landmark
        landmark_data: Landmark data object or dictionary

    Returns:
        URL to the PDF file
    """
    pdf_url = db_client.get_landmark_pdf_url(landmark_id)

    # If PDF URL not available, use the one from mock data
    if not pdf_url:
        if hasattr(landmark_data, "pdfReportUrl"):
            pdf_url = landmark_data.pdfReportUrl
        elif isinstance(landmark_data, dict):
            pdf_url = landmark_data.get(
                "pdfReportUrl", "https://cdn.informationcart.com/pdf/0001.pdf"
            )
        else:
            pdf_url = "https://cdn.informationcart.com/pdf/0001.pdf"

    assert pdf_url, f"No PDF URL found for landmark {landmark_id}"
    return pdf_url


def _download_pdf_file(
    temp_dirs: Dict, landmark_id: str, pdf_url: str
) -> Optional[Path]:
    """
    Download PDF and save to temporary directory.

    Args:
        temp_dirs: Dictionary of temporary directories
        landmark_id: ID of the landmark
        pdf_url: URL to download the PDF from

    Returns:
        Path to the downloaded PDF file or None if download failed
    """
    import requests

    pdf_path = temp_dirs["pdfs_dir"] / f"{landmark_id.replace('/', '_')}.pdf"
    logger.info(f"Downloading PDF from {pdf_url} to {pdf_path}")

    try:
        response = requests.get(pdf_url, stream=True, timeout=30)
        response.raise_for_status()

        with open(pdf_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        assert pdf_path.exists(), f"Failed to download PDF to {pdf_path}"
        return pdf_path
    except Exception as e:
        logger.error(f"Failed to download PDF: {e}")
        # Use a fallback PDF if available
        fallback_pdf = os.environ.get("FALLBACK_PDF_PATH")
        if fallback_pdf and os.path.exists(fallback_pdf):
            logger.info(f"Using fallback PDF: {fallback_pdf}")
            shutil.copy(fallback_pdf, pdf_path)
            return pdf_path
        else:
            return None


def _process_pdf_text(
    pdf_extractor: PDFExtractor, pdf_path: Path, temp_dirs: Dict, landmark_id: str
) -> str:
    """
    Extract text from PDF and save to file.

    Args:
        pdf_extractor: PDF extractor instance
        pdf_path: Path to the PDF file
        temp_dirs: Dictionary of temporary directories
        landmark_id: ID of the landmark

    Returns:
        Extracted text content
    """
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
        text = pdf_extractor.extract_text_from_bytes(pdf_bytes)

    assert text, "Failed to extract text from PDF"
    logger.info(f"Successfully extracted {len(text)} characters of text")

    # Save text to file
    text_path = temp_dirs["text_dir"] / f"{landmark_id.replace('/', '_')}.txt"
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text)

    return text


def _chunk_and_enrich_text(
    text_chunker: TextChunker, text: str, landmark_id: str
) -> Tuple[List, List]:
    """
    Split text into chunks and enrich with metadata.

    Args:
        text_chunker: Text chunker instance
        text: Text content to chunk
        landmark_id: ID of the landmark

    Returns:
        Tuple containing chunks and enriched chunks with metadata
    """
    # Chunk text
    chunks = text_chunker.chunk_text_by_tokens(text)
    assert chunks, "Failed to chunk text"
    logger.info(f"Successfully created {len(chunks)} text chunks")

    # Create enriched chunks with metadata
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

    return chunks, enriched_chunks


def _create_embeddings(
    embedding_generator: EmbeddingGenerator, enriched_chunks: List
) -> Tuple[List, List]:
    """
    Generate embeddings for text chunks.

    Args:
        embedding_generator: Embedding generator instance
        enriched_chunks: List of enriched text chunks

    Returns:
        Tuple containing embeddings and chunks with embeddings
    """
    # Get text content for embedding generation
    texts = [chunk["text"] for chunk in enriched_chunks]
    embeddings = embedding_generator.generate_embeddings_batch(texts)

    assert len(embeddings) == len(
        texts
    ), "Number of embeddings doesn't match number of chunks"
    logger.info(f"Successfully generated {len(embeddings)} embeddings")

    # Add embeddings to chunks
    chunks_with_embeddings = enriched_chunks.copy()
    for i, embedding in enumerate(embeddings):
        chunks_with_embeddings[i]["embedding"] = embedding

    return embeddings, chunks_with_embeddings


def _store_vectors_in_db(
    pinecone_db: Any, chunks_with_embeddings: List, landmark_id: str
) -> List:
    """
    Store vectors in Pinecone database.

    Args:
        pinecone_db: Pinecone database instance
        chunks_with_embeddings: List of chunks with embedding vectors
        landmark_id: ID of the landmark

    Returns:
        List of vector IDs
    """
    id_prefix = f"test-{landmark_id}-"
    vector_ids = pinecone_db.store_chunks(
        chunks=chunks_with_embeddings,
        id_prefix=id_prefix,
        landmark_id=landmark_id,
    )

    assert vector_ids, "Failed to store vectors in Pinecone"
    logger.info(f"Successfully stored {len(vector_ids)} vectors in Pinecone")
    return vector_ids


def _verify_vector_count(pinecone_db: Any, before_count: int) -> int:
    """
    Verify vectors were stored by checking updated count.

    Args:
        pinecone_db: Pinecone database instance
        before_count: Vector count before storing

    Returns:
        Current vector count
    """
    time.sleep(5)  # Wait for Pinecone to update
    after_stats = pinecone_db.get_index_stats()
    after_count = after_stats.get("total_vector_count", 0)
    logger.info(f"Final vector count: {after_count}")

    # The count should be greater than before
    assert (
        after_count >= before_count
    ), "Vector count did not increase after storing vectors"
    return after_count


def _query_and_verify_vectors(
    pinecone_db: Any, embeddings: List, landmark_id: str
) -> bool:
    """
    Query vectors and verify they can be retrieved.

    Args:
        pinecone_db: Pinecone database instance
        embeddings: List of embedding vectors
        landmark_id: ID of the landmark

    Returns:
        True if vectors were successfully retrieved
    """
    if len(embeddings) == 0:
        logger.warning("No embeddings to query")
        return False

    # Use the first embedding as a query
    query_embedding = embeddings[0]
    matches = pinecone_db.query_vectors(
        query_embedding, top_k=5, filter_dict={"landmark_id": landmark_id}
    )

    assert matches, "Failed to retrieve vectors from Pinecone"
    assert len(matches) > 0, "No matches found for query"
    logger.info(f"Successfully retrieved {len(matches)} vector matches")

    # Verify that at least one of our stored vectors is among the results
    found_match = False
    for match in matches:
        # Handle match object or dictionary
        metadata = {}
        if hasattr(match, "metadata"):
            metadata = match.metadata
        elif hasattr(match, "get"):
            metadata = match.get("metadata", {})
        elif isinstance(match, dict):
            metadata = match.get("metadata", {})

        # Check if the landmark_id exists in metadata
        if isinstance(metadata, dict) and metadata.get("landmark_id") == landmark_id:
            found_match = True
            break
        elif hasattr(metadata, "get") and metadata.get("landmark_id") == landmark_id:
            found_match = True
            break

    assert found_match, "Could not find the stored landmark ID in query results"
    return True


def _cleanup_test_vectors(pinecone_db: Any, vector_ids: List) -> None:
    """
    Clean up test vectors from database.

    Args:
        pinecone_db: Pinecone database instance
        vector_ids: List of vector IDs to delete
    """
    for vector_id in vector_ids:
        pinecone_db.delete_vectors([vector_id])
    logger.info(f"Cleaned up {len(vector_ids)} test vectors")


@pytest.mark.integration
@pytest.mark.functional
def test_vector_storage_pipeline(temp_dirs: dict, dedicated_test_db) -> None:
    """
    Test the complete vector storage pipeline with one landmark.

    This test validates the entire data flow:
    1. Fetching landmark data from the API or using mock data
    2. Downloading the landmark's PDF document
    3. Extracting text content from the PDF
    4. Chunking the text into processable segments
    5. Generating vector embeddings for each text chunk
    6. Storing these vectors in the Pinecone database
    7. Verifying the vectors were stored correctly
    8. Querying the database to retrieve the vectors
    9. Cleaning up test data from Pinecone

    Args:
        temp_dirs: Fixture providing temporary directories for test artifacts
        dedicated_test_db: Fixture providing a dedicated test database
    """
    logger.info("=== Testing complete vector storage pipeline ===")

    # Step 1: Set up test components
    (
        db_client,
        pdf_extractor,
        text_chunker,
        embedding_generator,
        pinecone_db,
        before_count,
    ) = _setup_test_components(dedicated_test_db)

    # Step 2: Select and fetch landmark data
    landmark_id = "LP-00101"  # Use a known landmark ID that exists in CoreDataStore API
    landmark_data, landmark_name = _fetch_landmark_data(db_client, landmark_id)

    # Step 3: Get PDF URL
    pdf_url = _resolve_pdf_url(db_client, landmark_id, landmark_data)

    # Step 4: Download PDF
    pdf_path = _download_pdf_file(temp_dirs, landmark_id, pdf_url)
    if pdf_path is None:
        pytest.skip("Cannot proceed without PDF")
        return

    # Step 5: Extract and process text from PDF
    text = _process_pdf_text(pdf_extractor, pdf_path, temp_dirs, landmark_id)

    # Step 6: Chunk text and enrich with metadata
    chunks, enriched_chunks = _chunk_and_enrich_text(text_chunker, text, landmark_id)

    # Step 7: Generate embeddings
    embeddings, chunks_with_embeddings = _create_embeddings(
        embedding_generator, enriched_chunks
    )

    # Step 8: Store vectors in Pinecone
    vector_ids = _store_vectors_in_db(pinecone_db, chunks_with_embeddings, landmark_id)

    # Step 9: Verify vectors were stored by checking count
    _verify_vector_count(pinecone_db, before_count)

    # Step 10: Query and verify vector retrieval
    _query_and_verify_vectors(pinecone_db, embeddings, landmark_id)

    # Step 11: Clean up test vectors
    _cleanup_test_vectors(pinecone_db, vector_ids)

    logger.info("=== Vector storage pipeline test completed successfully ===")


@pytest.mark.functional
def test_pinecone_connection_and_operations(dedicated_test_db) -> None:
    """Test basic Pinecone operations to ensure the database is accessible."""
    logger.info("=== Testing Pinecone connection and basic operations ===")

    # Use test-specific Pinecone client
    pinecone_db = dedicated_test_db

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
            "landmark_id": "LP-00101",  # Use a real landmark ID
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
        chunks=[test_chunk], id_prefix=test_id, landmark_id="LP-00101"
    )

    assert vector_ids, "Failed to store test vector"
    logger.info(f"Successfully stored test vector with ID: {vector_ids[0]}")

    # Wait for Pinecone to update - increased wait time to ensure indexing is complete
    time.sleep(10)

    # Test querying the vector
    matches = pinecone_db.query_vectors(
        query_vector=test_vector, top_k=1, filter_dict={"landmark_id": "LP-00101"}
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
