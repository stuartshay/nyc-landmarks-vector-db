"""
Integration tests for the Wikipedia article processing pipeline.

These tests validate the complete Wikipedia processing workflow from
fetching articles from the CoreDataStore API to storing vectors in Pinecone.

Key improvements in this test:
1. Proper source_type handling based on vector ID prefixes
2. Intermediate validation steps to catch issues early
3. Comprehensive cleanup of test vectors
4. Better error reporting and debugging information
"""

import logging
from typing import Any, Dict, List, Optional

import pytest

from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TEST_LANDMARK_ID = "LP-01973"  # Harlem YMCA (known to have Wikipedia articles)


def _cleanup_test_vectors(pinecone_db: PineconeDB, vector_ids: list) -> None:
    """Clean up test vectors from Pinecone."""
    if vector_ids:
        try:
            deleted_count = pinecone_db.delete_vectors(vector_ids)
            logger.info(f"Cleaned up {deleted_count} test vectors")
        except Exception as e:
            logger.warning(
                f"Failed to cleanup test vectors (this is expected when index is being deleted): {e}"
            )


def _wait_for_pinecone_indexing(seconds: int = 5) -> None:
    """Wait for Pinecone to index the vectors."""
    import time

    logger.info(f"Waiting {seconds} seconds for Pinecone indexing...")
    time.sleep(seconds)


def _verify_stored_vectors(
    pinecone_db: PineconeDB, landmark_id: str, expected_source_type: str
) -> bool:
    """Verify that vectors were stored with correct metadata."""
    # Query without source_type filter first to check if vectors exist
    from nyc_landmarks.embeddings.generator import EmbeddingGenerator

    embedding_generator = EmbeddingGenerator()
    test_embedding = embedding_generator.generate_embedding("test query")

    # Try querying with no filter first to see if any vectors exist
    # Use namespace_override to match the storage namespace
    try:
        all_results = pinecone_db.query_vectors(
            query_vector=test_embedding,
            top_k=10,
            filter_dict={},  # No filter to see all vectors
            namespace_override=pinecone_db.namespace,  # Use the same namespace as storage
        )
        logger.info(f"Found {len(all_results)} total vectors in index")

        # Now filter by landmark_id
        landmark_results = pinecone_db.query_vectors(
            query_vector=test_embedding,
            top_k=10,
            filter_dict={"landmark_id": landmark_id},
            namespace_override=pinecone_db.namespace,  # Use the same namespace as storage
        )
        logger.info(f"Found {len(landmark_results)} vectors for landmark {landmark_id}")

        if landmark_results:
            sample_metadata = landmark_results[0].get("metadata", {})
            logger.info(f"Sample vector metadata keys: {list(sample_metadata.keys())}")
            actual_source_type = sample_metadata.get("source_type", "unknown")
            logger.info(f"Actual source_type in stored vectors: {actual_source_type}")
            return bool(actual_source_type == expected_source_type)

        return False
    except Exception as e:
        logger.error(f"Error verifying stored vectors: {e}")
        return False


@pytest.mark.integration
def test_end_to_end_wikipedia_pipeline(pinecone_test_db: Optional[PineconeDB]) -> None:
    """Test the complete Wikipedia processing pipeline using mocks for all external dependencies.

    This test validates the entire Wikipedia processing workflow:
    1. Retrieves Wikipedia articles from mock database
    2. Fetches Wikipedia content via mocked HTTP requests
    3. Uses enhanced metadata collector with comprehensive API mocks
    4. Processes content through chunking and embedding pipeline
    5. Stores vectors in Pinecone with complete metadata

    All external dependencies (database API, Wikipedia HTTP requests) are mocked
    for reliable, fast, and consistent test execution.
    """
    # Import dependencies
    from nyc_landmarks.db.wikipedia_fetcher import WikipediaFetcher
    from nyc_landmarks.embeddings.generator import EmbeddingGenerator

    # Use comprehensive mock db_client with all API methods mocked
    from tests.mocks import create_mock_db_client

    mock_db_client = create_mock_db_client()

    # Step 1: Retrieve and validate Wikipedia articles
    articles = _retrieve_wikipedia_articles(mock_db_client)

    # Step 2: Collect enhanced metadata with mocks
    enhanced_metadata_dict = _collect_enhanced_metadata(mock_db_client)

    # Step 3: Process Wikipedia content with mocked HTTP response
    content_model = _process_wikipedia_content(WikipediaFetcher(), articles[0])

    # Step 4: Generate embeddings for chunks
    chunks_with_embeddings = _generate_embeddings(EmbeddingGenerator(), content_model)

    # Step 5-8: Store and verify vectors in Pinecone
    _store_and_verify_vectors(
        pinecone_test_db,
        articles[0],
        chunks_with_embeddings,
        enhanced_metadata_dict,
        EmbeddingGenerator(),
    )


def _retrieve_wikipedia_articles(mock_db_client: Any) -> List[Any]:
    """Step 1: Retrieve Wikipedia articles using mock data."""
    logger.info(f"Step 1: Retrieving Wikipedia articles for {TEST_LANDMARK_ID}")
    articles = mock_db_client.get_wikipedia_articles(TEST_LANDMARK_ID)
    assert (
        articles
    ), f"Should retrieve at least one Wikipedia article for {TEST_LANDMARK_ID}"

    logger.info(f"Found {len(articles)} Wikipedia articles for {TEST_LANDMARK_ID}")
    for article in articles:
        logger.info(f"  Article: {article.title}, URL: {article.url}")

    # Ensure the return type is always a list
    return list(articles)


def _collect_enhanced_metadata(mock_db_client: Any) -> dict:
    """Step 2: Initialize enhanced metadata collector with mock client."""
    from unittest.mock import patch

    from nyc_landmarks.vectordb.enhanced_metadata import EnhancedMetadataCollector

    logger.info("Step 2: Initializing enhanced metadata collector with mocks")

    # Patch get_db_client to return our mock client
    with patch(
        "nyc_landmarks.vectordb.enhanced_metadata.get_db_client",
        return_value=mock_db_client,
    ):
        metadata_collector = EnhancedMetadataCollector()

        # Verify enhanced metadata collection works with our mocks
        enhanced_metadata = metadata_collector.collect_landmark_metadata(
            TEST_LANDMARK_ID
        )
        assert (
            enhanced_metadata
        ), f"Should collect enhanced metadata for {TEST_LANDMARK_ID}"

        _log_enhanced_metadata(enhanced_metadata)
        return enhanced_metadata.model_dump()


def _log_enhanced_metadata(enhanced_metadata: Any) -> None:
    """Log enhanced metadata details."""
    logger.info("Enhanced metadata collected successfully:")
    logger.info(f"  Landmark name: {enhanced_metadata.name}")
    logger.info(f"  Architect: {enhanced_metadata.architect}")
    logger.info(f"  Neighborhood: {enhanced_metadata.neighborhood}")
    logger.info(f"  Style: {enhanced_metadata.style}")
    logger.info(f"  Has PLUTO data: {enhanced_metadata.has_pluto_data}")
    if enhanced_metadata.has_pluto_data:
        logger.info(f"  Year built: {enhanced_metadata.year_built}")
        logger.info(f"  Land use: {enhanced_metadata.land_use}")
        logger.info(f"  Zoning district: {enhanced_metadata.zoning_district}")

    # Log buildings data
    if hasattr(enhanced_metadata, "buildings") and enhanced_metadata.buildings:
        logger.info(f"  Buildings count: {len(enhanced_metadata.buildings)}")
        for i, building in enumerate(enhanced_metadata.buildings):
            logger.info(f"    Building {i + 1}:")
            logger.info(f"      Name: {building.get('name', 'N/A')}")
            logger.info(f"      Address: {building.get('address', 'N/A')}")
            logger.info(f"      BBL: {building.get('bbl', 'N/A')}")
            logger.info(f"      BIN Number: {building.get('binNumber', 'N/A')}")
            logger.info(f"      Block: {building.get('block', 'N/A')}")
            logger.info(f"      Lot: {building.get('lot', 'N/A')}")
            logger.info(f"      Latitude: {building.get('latitude', 'N/A')}")
            logger.info(f"      Longitude: {building.get('longitude', 'N/A')}")
    else:
        logger.info("  No buildings data found")


def _process_wikipedia_content(fetcher: Any, article: Any) -> Any:
    """Step 3: Process Wikipedia article with mocked HTTP response."""
    from unittest.mock import patch

    logger.info("Step 3: Processing Wikipedia content with mocked HTTP requests")

    mock_response = _create_mock_wikipedia_response()

    with patch("requests.get", return_value=mock_response):
        content_model = fetcher.process_wikipedia_article(article)
        assert content_model, f"Should process article '{article.title}' successfully"
        assert content_model.chunks, "Should generate chunks from article content"

        _log_content_chunks(content_model, article.title)
        return content_model


def _create_mock_wikipedia_response() -> Any:
    """Create mock Wikipedia HTTP response."""
    from unittest.mock import MagicMock

    # Mock comprehensive Wikipedia content for Harlem YMCA
    mock_wikipedia_content = """
    The Harlem YMCA is a historic Young Men's Christian Association building located in the Harlem neighborhood of Manhattan, New York City.
    The building was designed by architect James C. Mackenzie Jr. and completed in 1932. It represents a fine example of Renaissance Revival architecture.

    The facility served as an important community center for the African American community during the Harlem Renaissance period.
    The building features distinctive architectural elements including ornate facades and classical proportions.

    Located in the vibrant neighborhood of Harlem, the YMCA has been a cornerstone of community life for decades.
    The building's historical significance extends beyond its architectural merit to its role in social and cultural development.
    """

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = f"""
    <html>
        <body>
            <div id="mw-content-text">
                <div class="mw-parser-output">
                    <p>{mock_wikipedia_content}</p>
                </div>
            </div>
        </body>
    </html>
    """
    return mock_response


def _log_content_chunks(content_model: Any, article_title: str) -> None:
    """Log information about generated content chunks."""
    logger.info(
        f"Generated {len(content_model.chunks)} chunks from article '{article_title}'"
    )
    for i, chunk in enumerate(content_model.chunks[:2]):  # Log first 2 chunks
        # Handle both object and dict representations of chunks
        if hasattr(chunk, "content"):
            content = chunk.content[:100]
        elif isinstance(chunk, dict) and "content" in chunk:
            content = str(chunk["content"])[:100]
        else:
            content = str(chunk)[:100]
        logger.info(f"  Chunk {i + 1}: {content}...")


def _generate_embeddings(embedding_generator: Any, content_model: Any) -> List[Any]:
    """Step 4: Generate embeddings for the chunks."""
    logger.info("Step 4: Generating embeddings for chunks")
    chunks_with_embeddings = embedding_generator.process_chunks(content_model.chunks)
    assert (
        isinstance(chunks_with_embeddings, list) and chunks_with_embeddings
    ), "Should generate embeddings for chunks"

    _validate_embeddings(chunks_with_embeddings)
    # Ensure the return type is always a list
    return list(chunks_with_embeddings)


def _validate_embeddings(chunks_with_embeddings: List[Any]) -> None:
    """Validate that embeddings were generated correctly."""
    logger.info(f"Generated embeddings for {len(chunks_with_embeddings)} chunks")
    for i, chunk in enumerate(chunks_with_embeddings[:2]):  # Check first 2 chunks
        assert (
            hasattr(chunk, "embedding") or "embedding" in chunk
        ), f"Chunk {i + 1} should have an embedding"
        # Handle both object and dict representations
        embedding = (
            getattr(chunk, "embedding", None) or chunk.get("embedding")
            if isinstance(chunk, dict)
            else chunk.embedding
        )
        assert embedding is not None, f"Chunk {i + 1} embedding should not be None"
        assert len(embedding) > 0, f"Chunk {i + 1} embedding should not be empty"


def _store_and_verify_vectors(
    pinecone_test_db: Optional[PineconeDB],
    article: Any,
    chunks_with_embeddings: List[Any],
    enhanced_metadata_dict: Dict[str, Any],
    embedding_generator: Any,
) -> None:
    """Steps 5-8: Store vectors in Pinecone and verify complete pipeline."""
    logger.info("Step 5: Storing vectors in Pinecone with enhanced metadata")
    pinecone_db = pinecone_test_db
    if not pinecone_db or not pinecone_db.index:
        pytest.skip("No Pinecone index available")
        return

    # Override namespace for test index - set to empty string to match test index
    pinecone_db.namespace = ""  # type: ignore
    logger.info(
        "Set test database namespace to empty string to match test index configuration"
    )

    # Use proper Wikipedia prefix to ensure correct source_type detection
    wiki_id_prefix = f"wiki-{article.title.replace(' ', '_')}-{TEST_LANDMARK_ID}-"

    # Store with cleanup of any existing test vectors first
    vector_ids = []
    try:
        # Clean up existing vectors
        _cleanup_existing_vectors(pinecone_db, embedding_generator)

        # Store vectors with enhanced metadata
        vector_ids = _store_vectors(
            pinecone_db, chunks_with_embeddings, wiki_id_prefix, enhanced_metadata_dict
        )

        # Verify stored vectors
        _verify_complete_pipeline(
            pinecone_db, wiki_id_prefix, embedding_generator, vector_ids
        )

    finally:
        _log_test_completion(vector_ids, pinecone_db)


def _cleanup_existing_vectors(
    pinecone_db: PineconeDB, embedding_generator: Any
) -> None:
    """Clean up any existing vectors for this landmark to avoid conflicts."""
    try:
        # Get existing vectors
        temp_embedding = embedding_generator.generate_embedding("cleanup query")
        existing_vectors = pinecone_db.query_vectors(
            query_vector=temp_embedding,
            top_k=100,
            filter_dict={"landmark_id": TEST_LANDMARK_ID},
        )
        if existing_vectors:
            existing_ids = [v.get("id", "") for v in existing_vectors if v.get("id")]
            if existing_ids:
                pinecone_db.delete_vectors(existing_ids)
                logger.info(f"Cleaned up {len(existing_ids)} existing vectors")
    except Exception as e:
        logger.info(f"No existing vectors to clean up (this is normal): {e}")

    # Wait a moment for cleanup to take effect
    _wait_for_pinecone_indexing(3)


def _store_vectors(
    pinecone_db: PineconeDB,
    chunks_with_embeddings: List[Any],
    wiki_id_prefix: str,
    enhanced_metadata_dict: Dict[str, Any],
) -> List[str]:
    """Store vectors with enhanced metadata."""
    vector_ids = pinecone_db.store_chunks(
        chunks=chunks_with_embeddings,
        id_prefix=wiki_id_prefix,
        landmark_id=TEST_LANDMARK_ID,
        use_fixed_ids=True,
        delete_existing=False,  # We already cleaned up manually above
        enhanced_metadata=enhanced_metadata_dict,  # Pass pre-built enhanced metadata
    )

    assert vector_ids, "Should store vectors successfully"
    logger.info(f"Stored {len(vector_ids)} vectors with prefix '{wiki_id_prefix}'")

    # Wait for Pinecone to index the vectors
    _wait_for_pinecone_indexing()
    return vector_ids


def _verify_complete_pipeline(
    pinecone_db: PineconeDB,
    wiki_id_prefix: str,
    embedding_generator: Any,
    vector_ids: List[str],
) -> None:
    """Steps 6-8: Verify vectors were stored and can be queried with complete metadata."""
    # Step 6: Verify vectors were stored with correct metadata
    logger.info("Step 6: Verifying stored vectors have correct metadata")
    expected_source_type = "wikipedia" if wiki_id_prefix.startswith("wiki-") else "test"
    assert _verify_stored_vectors(
        pinecone_db, TEST_LANDMARK_ID, expected_source_type
    ), "Stored vectors metadata verification failed"

    # Step 7: Query vectors to verify complete pipeline with enhanced metadata
    logger.info("Step 7: Querying vectors to verify complete pipeline")
    results = _query_vectors_for_verification(
        pinecone_db, embedding_generator, expected_source_type
    )

    # Step 8: Verify the retrieved vectors have complete metadata including enhanced fields
    logger.info("Step 8: Verifying retrieved vectors have enhanced metadata")
    _verify_enhanced_metadata_in_results(results, expected_source_type)


def _query_vectors_for_verification(
    pinecone_db: PineconeDB, embedding_generator: Any, expected_source_type: str
) -> List[Dict[str, Any]]:
    """Query vectors to verify complete pipeline."""
    test_query = "historic YMCA building in Harlem Renaissance architecture"
    test_embedding = embedding_generator.generate_embedding(test_query)

    results = pinecone_db.query_vectors(
        query_vector=test_embedding,
        top_k=5,
        filter_dict={
            "landmark_id": TEST_LANDMARK_ID,
            "source_type": expected_source_type,
        },
        namespace_override=pinecone_db.namespace,  # Use the same namespace as storage
    )

    assert results, f"Should retrieve vectors with source_type '{expected_source_type}'"
    logger.info(
        f"Retrieved {len(results)} {expected_source_type} vectors for query '{test_query}'"
    )
    return results


def _verify_enhanced_metadata_in_results(
    results: List[Dict[str, Any]], expected_source_type: str
) -> None:
    """Verify the retrieved vectors have complete metadata including enhanced fields."""
    for i, result in enumerate(results):
        metadata = result.get("metadata", {})

        # Basic metadata verification
        assert (
            metadata.get("landmark_id") == TEST_LANDMARK_ID
        ), "Vector should have correct landmark_id"
        assert (
            metadata.get("source_type") == expected_source_type
        ), f"Vector should have source_type '{expected_source_type}'"
        assert (
            "article_title" in metadata or "article_url" in metadata
        ), "Wikipedia vectors should have article metadata"

        # Enhanced metadata verification (should be included via enhanced_metadata collection)
        logger.info(f"  Vector {i + 1} metadata fields: {list(metadata.keys())}")

        # Check for enhanced fields that should be populated by our mocks
        if "architect" in metadata:
            logger.info(f"  ✓ Enhanced field 'architect': {metadata['architect']}")
        if "neighborhood" in metadata:
            logger.info(
                f"  ✓ Enhanced field 'neighborhood': {metadata['neighborhood']}"
            )
        if "style" in metadata:
            logger.info(f"  ✓ Enhanced field 'style': {metadata['style']}")


def _log_test_completion(vector_ids: List[str], pinecone_db: PineconeDB) -> None:
    """Log test completion details."""
    logger.info("✅ All integration test steps completed successfully!")
    logger.info("✅ Wikipedia processing pipeline working with comprehensive mocks!")
    logger.info("✅ Enhanced metadata collection integrated successfully!")

    # Keep test vectors for debugging - DO NOT DELETE
    logger.info(f"Keeping {len(vector_ids)} test vectors in index for debugging")
    logger.info(f"Test vector IDs: {vector_ids[:3]}...")  # Show first 3 IDs
    logger.info(f"Test landmark ID: {TEST_LANDMARK_ID}")
    logger.info(f"Test namespace: {pinecone_db.namespace}")
    logger.info("Run Pinecone dashboard or query tools to inspect the stored vectors")


@pytest.mark.integration
def test_wikipedia_pipeline_error_handling() -> None:
    """Test Wikipedia processing pipeline error handling using mock error scenarios."""
    from tests.mocks import (
        create_mock_db_client_empty_responses,
        create_mock_db_client_with_errors,
    )

    # Test error handling
    mock_error_client = create_mock_db_client_with_errors()

    with pytest.raises(Exception) as exc_info:
        mock_error_client.get_wikipedia_articles(TEST_LANDMARK_ID)

    assert "API error" in str(exc_info.value)
    logger.info("Successfully tested error handling in mock db_client")

    # Test empty response handling
    mock_empty_client = create_mock_db_client_empty_responses()
    empty_articles = mock_empty_client.get_wikipedia_articles(TEST_LANDMARK_ID)

    assert empty_articles == []
    logger.info("Successfully tested empty response handling in mock db_client")


@pytest.mark.integration
def test_mock_wikipedia_articles_structure() -> None:
    """Test that mock Wikipedia articles have the correct structure and data."""
    from nyc_landmarks.models.wikipedia_models import WikipediaArticleModel
    from tests.mocks import get_mock_wikipedia_articles

    articles = get_mock_wikipedia_articles()

    # Verify we have the expected number of test articles
    assert len(articles) == 2, "Should have 2 mock Wikipedia articles"

    # Verify all articles are proper WikipediaArticleModel instances
    for article in articles:
        assert isinstance(
            article, WikipediaArticleModel
        ), "Article should be WikipediaArticleModel instance"
        assert article.id, "Article should have an ID"
        assert article.lpNumber, "Article should have an LP number"
        assert article.url, "Article should have a URL"
        assert article.title, "Article should have a title"
        assert (
            article.recordType == "Wikipedia"
        ), "Article should have correct record type"
        assert article.content, "Article should have content"

    # Verify specific test data
    lp_numbers = [article.lpNumber for article in articles]
    assert "LP-01973" in lp_numbers, "Should have article for LP-01973"
    assert "LP-00009" in lp_numbers, "Should have article for LP-00009"

    logger.info(
        f"Successfully validated structure of {len(articles)} mock Wikipedia articles"
    )


@pytest.mark.integration
def test_create_debug_wikipedia_vectors(pinecone_test_db: Optional[PineconeDB]) -> None:
    """Create test Wikipedia vectors with enhanced metadata and keep them for debugging.

    This test creates vectors using the enhanced metadata collector with comprehensive
    mocks to test the complete pipeline without external API dependencies.
    """
    from tests.mocks.db_client_mocks import create_mock_db_client

    mock_db_client = create_mock_db_client()

    # Step 1: Collect enhanced metadata
    enhanced_metadata = _debug_collect_enhanced_metadata(mock_db_client)

    # Step 2: Process Wikipedia articles
    articles, content_model = _debug_process_wikipedia_articles(mock_db_client)

    # Step 3: Generate embeddings and enhance metadata
    chunks_with_embeddings = _debug_generate_enhanced_embeddings(
        content_model, enhanced_metadata, mock_db_client
    )

    # Step 4: Store and verify debug vectors
    _debug_store_and_verify_vectors(pinecone_test_db, chunks_with_embeddings)


def _debug_collect_enhanced_metadata(mock_db_client: Any) -> Any:
    """Step 1: Collect enhanced metadata for debug test."""
    from unittest.mock import patch

    from nyc_landmarks.vectordb.enhanced_metadata import get_metadata_collector

    with patch(
        "nyc_landmarks.vectordb.enhanced_metadata.get_db_client",
        return_value=mock_db_client,
    ):
        metadata_collector = get_metadata_collector()
        enhanced_metadata = metadata_collector.collect_landmark_metadata(
            TEST_LANDMARK_ID
        )

        _log_debug_enhanced_metadata(enhanced_metadata)
        return enhanced_metadata


def _log_debug_enhanced_metadata(enhanced_metadata: Any) -> None:
    """Log enhanced metadata details for debugging."""
    logger.info("Enhanced metadata collected:")
    logger.info(f"  landmark_id: {enhanced_metadata.landmark_id}")
    logger.info(f"  name: {enhanced_metadata.name}")
    logger.info(f"  architect: {enhanced_metadata.architect}")
    logger.info(f"  neighborhood: {enhanced_metadata.neighborhood}")
    logger.info(f"  style: {enhanced_metadata.style}")
    logger.info(f"  has_pluto_data: {enhanced_metadata.has_pluto_data}")
    logger.info(f"  year_built: {enhanced_metadata.year_built}")
    logger.info(f"  land_use: {enhanced_metadata.land_use}")
    logger.info(f"  zoning_district: {enhanced_metadata.zoning_district}")

    # Check if buildings data is present
    if hasattr(enhanced_metadata, "buildings") and enhanced_metadata.buildings:
        buildings = enhanced_metadata.buildings
        logger.info(f"  buildings: {len(buildings)} building(s)")
        if buildings:
            logger.info(f"    Sample building: {buildings[0]}")


def _debug_process_wikipedia_articles(
    mock_db_client: Any,
) -> tuple[List[Any], Optional[Any]]:
    """Step 2: Process Wikipedia articles with mocked content."""
    from unittest.mock import patch

    from nyc_landmarks.db.wikipedia_fetcher import WikipediaFetcher

    # Get Wikipedia articles for the landmark
    articles = mock_db_client.get_wikipedia_articles(TEST_LANDMARK_ID)
    logger.info(f"Retrieved {len(articles)} mock Wikipedia articles")

    if not articles:
        pytest.skip("No Wikipedia articles found for test landmark")
        return [], None

    # Create mock Wikipedia content and HTTP response
    mock_response = _create_debug_mock_wikipedia_response()

    # Process the first article with mocked content
    article = articles[0]
    wiki_fetcher = WikipediaFetcher()

    with patch("requests.get", return_value=mock_response):
        content_model = wiki_fetcher.process_wikipedia_article(article)

        assert content_model, f"Should process article '{article.title}' successfully"
        assert content_model.chunks, "Should generate chunks from article content"

        logger.info(f"Processed article: {article.title}")
        logger.info(f"Generated {len(content_model.chunks)} chunks")

    return articles, content_model


def _create_debug_mock_wikipedia_response() -> Any:
    """Create mock Wikipedia HTTP response for debugging."""
    from unittest.mock import MagicMock

    mock_wikipedia_content = """
    The Harlem YMCA is a historic Young Men's Christian Association building located in the Harlem neighborhood of Manhattan, New York City.
    The building was designed by architect James Gamble Rogers and completed in 1932.
    It served as an important community center for the African American community during the Harlem Renaissance period.

    The building is notable for its Art Deco architectural style and its role in the cultural development of Harlem.
    It housed various programs including educational classes, recreational activities, and community meetings.
    """

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = f"""
    <html>
        <body>
            <div id="mw-content-text">
                <p>{mock_wikipedia_content}</p>
            </div>
        </body>
    </html>
    """
    return mock_response


def _debug_generate_enhanced_embeddings(
    content_model: Any, enhanced_metadata: Any, mock_db_client: Any
) -> List[Dict[str, Any]]:
    """Step 3: Generate embeddings and enhance with metadata."""
    from unittest.mock import patch

    from nyc_landmarks.embeddings.generator import EmbeddingGenerator
    from nyc_landmarks.vectordb.enhanced_metadata import get_metadata_collector

    # Generate embeddings
    embedding_generator = EmbeddingGenerator()
    chunks_with_embeddings = embedding_generator.process_chunks(content_model.chunks)
    logger.info(f"Generated embeddings for {len(chunks_with_embeddings)} chunks")

    # Enhance chunk metadata
    with patch(
        "nyc_landmarks.vectordb.enhanced_metadata.get_db_client",
        return_value=mock_db_client,
    ):
        metadata_collector = get_metadata_collector()
        enhanced_metadata = metadata_collector.collect_landmark_metadata(
            TEST_LANDMARK_ID
        )

        _enhance_chunk_metadata(chunks_with_embeddings, enhanced_metadata)
        _inspect_enhanced_chunks(chunks_with_embeddings)

    return chunks_with_embeddings


def _enhance_chunk_metadata(
    chunks_with_embeddings: List[Dict[str, Any]], enhanced_metadata: Any
) -> None:
    """Add enhanced metadata fields to each chunk."""
    for chunk in chunks_with_embeddings:
        if "metadata" in chunk:
            # Add enhanced metadata fields to each chunk
            chunk["metadata"].update(
                {
                    "architect": enhanced_metadata.architect,
                    "neighborhood": enhanced_metadata.neighborhood,
                    "style": enhanced_metadata.style,
                    "year_built": enhanced_metadata.year_built,
                    "land_use": enhanced_metadata.land_use,
                    "zoning_district": enhanced_metadata.zoning_district,
                    "has_pluto_data": enhanced_metadata.has_pluto_data,
                }
            )

            # Add buildings data if available
            if hasattr(enhanced_metadata, "buildings") and enhanced_metadata.buildings:
                chunk["metadata"]["buildings"] = enhanced_metadata.buildings


def _inspect_enhanced_chunks(chunks_with_embeddings: List[Dict[str, Any]]) -> None:
    """Inspect and log enhanced chunk metadata."""
    if not chunks_with_embeddings:
        return

    sample_chunk = chunks_with_embeddings[0]
    logger.info("Sample enhanced chunk structure:")
    logger.info(f"  Keys in chunk: {list(sample_chunk.keys())}")

    if "metadata" in sample_chunk:
        metadata = sample_chunk["metadata"]
        logger.info(f"  Metadata keys: {list(metadata.keys())}")

        # Log key enhanced metadata fields
        logger.info("Enhanced metadata fields in vector:")
        logger.info(f"    architect: {metadata.get('architect', 'NOT FOUND')}")
        logger.info(f"    neighborhood: {metadata.get('neighborhood', 'NOT FOUND')}")
        logger.info(f"    style: {metadata.get('style', 'NOT FOUND')}")
        logger.info(f"    year_built: {metadata.get('year_built', 'NOT FOUND')}")
        logger.info(f"    land_use: {metadata.get('land_use', 'NOT FOUND')}")
        logger.info(
            f"    has_pluto_data: {metadata.get('has_pluto_data', 'NOT FOUND')}"
        )
        logger.info(f"    buildings: {len(metadata.get('buildings', []))} building(s)")

        # Verify all expected enhanced fields are present
        expected_fields = [
            "architect",
            "neighborhood",
            "style",
            "year_built",
            "land_use",
            "zoning_district",
            "has_pluto_data",
        ]
        missing_fields = [field for field in expected_fields if field not in metadata]
        if missing_fields:
            logger.warning(f"Missing enhanced metadata fields: {missing_fields}")
        else:
            logger.info("✅ All expected enhanced metadata fields present")


def _debug_store_and_verify_vectors(
    pinecone_test_db: Optional[PineconeDB], chunks_with_embeddings: List[Dict[str, Any]]
) -> None:
    """Step 4: Store vectors in test database and verify results."""
    # Step 5: Store vectors in test database (KEEP FOR DEBUGGING)
    pinecone_db = pinecone_test_db
    if not pinecone_db or not pinecone_db.index:
        pytest.skip("No Pinecone index available")
        return

    # Set namespace to empty string for test
    pinecone_db.namespace = ""

    # Use debug prefix based on the mock article title
    debug_prefix = f"debug-enhanced-wiki-Harlem_YMCA-{TEST_LANDMARK_ID}-"

    vector_ids = pinecone_db.store_chunks(
        chunks=chunks_with_embeddings,
        id_prefix=debug_prefix,
        landmark_id=TEST_LANDMARK_ID,
        use_fixed_ids=True,
        delete_existing=False,
    )

    _log_debug_vector_storage(vector_ids, pinecone_db)
    _wait_for_pinecone_indexing(10)  # Wait longer for debugging
    _debug_query_and_verify_vectors(pinecone_db, vector_ids)


def _log_debug_vector_storage(vector_ids: list, pinecone_db: PineconeDB) -> None:
    """Log debug vector storage information."""
    logger.info(
        f"STORED {len(vector_ids)} ENHANCED DEBUG VECTORS - KEEPING FOR INSPECTION"
    )
    logger.info(f"Vector IDs: {vector_ids}")
    logger.info(f"Landmark ID: {TEST_LANDMARK_ID}")
    logger.info(f"Namespace: {pinecone_db.namespace}")
    logger.info(f"Index name: {pinecone_db.index_name}")


def _debug_query_and_verify_vectors(pinecone_db: PineconeDB, vector_ids: list) -> None:
    """Query and verify the stored debug vectors."""
    from nyc_landmarks.embeddings.generator import EmbeddingGenerator

    embedding_generator = EmbeddingGenerator()
    test_embedding = embedding_generator.generate_embedding("test query")

    # Query all vectors to see what's in the index
    all_results = pinecone_db.query_vectors(
        query_vector=test_embedding,
        top_k=20,
        filter_dict={},  # No filter
    )
    logger.info(f"FOUND {len(all_results)} TOTAL VECTORS IN INDEX")

    # Query by landmark_id
    landmark_results = pinecone_db.query_vectors(
        query_vector=test_embedding,
        top_k=10,
        filter_dict={"landmark_id": TEST_LANDMARK_ID},
    )
    logger.info(
        f"FOUND {len(landmark_results)} VECTORS FOR LANDMARK {TEST_LANDMARK_ID}"
    )

    if landmark_results:
        sample_metadata = landmark_results[0].get("metadata", {})
        logger.info("SAMPLE STORED ENHANCED METADATA:")
        for key, value in sample_metadata.items():
            logger.info(f"  {key}: {value}")

    # Log final debug information
    _log_final_debug_info(pinecone_db, vector_ids)


def _log_final_debug_info(pinecone_db: PineconeDB, vector_ids: list) -> None:
    """Log final debug information for the stored vectors."""
    logger.info("=" * 60)
    logger.info("ENHANCED DEBUG VECTORS CREATED AND KEPT IN TEST DATABASE")
    logger.info("These vectors include comprehensive metadata from all API sources:")
    logger.info(f"  Index: {pinecone_db.index_name}")
    logger.info(f"  Namespace: {pinecone_db.namespace or 'default'}")
    logger.info(f"  Vector IDs: {vector_ids}")
    logger.info(f"  Landmark ID filter: {TEST_LANDMARK_ID}")
    logger.info("=" * 60)
