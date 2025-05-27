"""
Mock data and utilities for testing scripts/vector_utility.py
"""

import argparse
from typing import Any, Dict, List
from unittest.mock import Mock


class MockMatch:
    """Mock class representing a Pinecone match object."""

    def __init__(self, vector_data: Dict[str, Any]) -> None:
        self.id = vector_data["id"]
        self.score = vector_data.get("score", 0.95)
        self.metadata = vector_data["metadata"]
        self.values = vector_data.get("values", [])


def create_mock_pinecone_db() -> Mock:
    """Create a mock PineconeDB instance with standard behavior."""
    mock_db = Mock()

    # Mock successful operations
    mock_db.get_index_stats.return_value = {"total_vector_count": 1000}
    mock_db.fetch_vector_by_id.return_value = get_mock_vector_data()
    mock_db.query_vectors.return_value = create_mock_matches(
        get_mock_landmark_vectors()
    )
    mock_db.list_vectors.return_value = get_mock_vector_batch()

    return mock_db


def create_mock_pinecone_db_empty() -> Mock:
    """Create a mock PineconeDB instance that returns empty results."""
    mock_db = Mock()

    # Mock empty operations
    mock_db.get_index_stats.return_value = {"total_vector_count": 0}
    mock_db.fetch_vector_by_id.return_value = None
    mock_db.query_vectors.return_value = []
    mock_db.list_vectors.return_value = []

    return mock_db


def create_mock_pinecone_db_with_errors() -> Mock:
    """Create a mock PineconeDB instance that raises errors."""
    mock_db = Mock()

    # Mock error operations
    mock_db.get_index_stats.side_effect = Exception("Connection error")
    mock_db.fetch_vector_by_id.side_effect = Exception("Fetch error")
    mock_db.query_vectors.side_effect = Exception("Query error")
    mock_db.list_vectors.side_effect = Exception("List error")

    return mock_db


def get_mock_vector_data(
    vector_id: str = "wiki-Test_Landmark-LP-00001-chunk-0",
) -> Dict[str, Any]:
    """Get mock vector data for a single vector."""
    is_wiki = vector_id.startswith("wiki-")

    base_metadata = {
        "landmark_id": "LP-00001",
        "source_type": "wikipedia" if is_wiki else "pdf",
        "chunk_index": 0,
        "text": "This is a test landmark description for testing purposes.",
        "total_chunks": 5,
        "file_path": "test_file.pdf" if not is_wiki else None,
        "processing_date": "2024-01-15T10:30:00Z",
    }

    if is_wiki:
        # Extract article title from vector_id for consistency
        if "manhattan_municipal_building" in vector_id.lower():
            article_title = "Manhattan Municipal Building"
            article_url = "https://en.wikipedia.org/wiki/Manhattan_Municipal_Building"
        else:
            # Extract from vector ID format wiki-ArticleName-LP-XXXXX-chunk-N
            parts = vector_id.split("-")
            if len(parts) >= 2:
                article_title = parts[1].replace("_", " ")
                article_url = f"https://en.wikipedia.org/wiki/{parts[1]}"
            else:
                article_title = "Test Landmark"
                article_url = "https://en.wikipedia.org/wiki/Test_Landmark"

        base_metadata.update(
            {
                "article_title": article_title,
                "article_url": article_url,
                "section_title": "History",
                "wikipedia_id": "12345",
            }
        )

    return {
        "id": vector_id,
        "values": [0.1] * 1536,  # Standard OpenAI embedding size
        "metadata": base_metadata,
        "score": 0.95,
    }


def get_mock_vector_batch() -> List[Dict[str, Any]]:
    """Get a batch of mock vectors for testing list operations."""
    return [
        get_mock_vector_data("LP-00001-chunk-0"),
        get_mock_vector_data("LP-00001-chunk-1"),
        get_mock_vector_data("wiki-Test_Landmark-LP-00001-chunk-0"),
        get_mock_vector_data("wiki-Test_Landmark-LP-00001-chunk-1"),
        get_mock_vector_data("wiki-Another_Building-LP-00002-chunk-0"),
        get_mock_vector_data("LP-00002-chunk-0"),
    ]


def get_mock_invalid_vector() -> Dict[str, Any]:
    """Get mock vector data with missing required fields."""
    return {
        "id": "invalid-vector-id",
        "values": [0.1] * 1536,
        "metadata": {
            "incomplete": "data",
            # Missing required fields like landmark_id, source_type, etc.
        },
    }


def get_mock_wiki_vector_invalid_title() -> Dict[str, Any]:
    """Get mock Wikipedia vector with mismatched article title."""
    vector = get_mock_vector_data("wiki-Test_Landmark-LP-001-chunk-0")
    vector["metadata"]["article_title"] = "Wrong Title"  # Doesn't match ID
    return vector


def get_mock_vector_zero_embeddings() -> Dict[str, Any]:
    """Get mock vector with zero embeddings."""
    vector = get_mock_vector_data()
    vector["values"] = [0.0] * 1536  # All zeros
    return vector


def get_mock_landmark_vectors() -> List[Dict[str, Any]]:
    """Get mock vectors for a specific landmark."""
    return [
        get_mock_vector_data("LP-00001-chunk-0"),
        get_mock_vector_data("LP-00001-chunk-1"),
        get_mock_vector_data("LP-00001-chunk-2"),
        get_mock_vector_data("wiki-Test_Landmark-LP-00001-chunk-0"),
        get_mock_vector_data("wiki-Test_Landmark-LP-00001-chunk-1"),
    ]


def get_mock_comparison_vectors() -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Get two vectors for comparison testing."""
    vector1 = get_mock_vector_data("test-vector-1")
    vector1["metadata"]["chunk_index"] = 0
    vector1["metadata"]["text"] = "First chunk text"
    vector1["metadata"]["vector1_only"] = "unique_value"

    vector2 = get_mock_vector_data("test-vector-2")
    vector2["metadata"]["chunk_index"] = 1
    vector2["metadata"]["text"] = "Second chunk text"
    vector2["metadata"]["unique_field"] = "different_value"

    return vector1, vector2


def get_mock_verification_vectors() -> List[Dict[str, Any]]:
    """Get vectors for verification testing with various conditions."""
    vectors = []

    # Valid vectors
    for i in range(3):
        vectors.append(get_mock_vector_data(f"valid-LP-00{i + 1}-chunk-0"))

    # Invalid vector (missing metadata)
    invalid_vector = get_mock_invalid_vector()
    vectors.append(invalid_vector)

    # Vector with zero embeddings
    zero_vector = get_mock_vector_zero_embeddings()
    zero_vector["id"] = "zero-embeddings-LP-005-chunk-0"
    vectors.append(zero_vector)

    return vectors


def get_mock_deprecated_metadata() -> Dict[str, Any]:
    """Get metadata with deprecated fields."""
    return {
        "landmark_id": "LP-00001",
        "source_type": "pdf",
        "chunk_index": 0,
        "text": "Test text",
        # Deprecated fields that the function actually checks for
        "bbl": "1000477501",
        "all_bbls": ["1000477501", "1000477502"],
        "old_field": "deprecated_value",
        "legacy_metadata": "should_warn",
        "outdated_format": True,
    }


def create_mock_matches(vector_batch: List[Dict[str, Any]]) -> List[MockMatch]:
    """Create MockMatch objects from vector data."""
    return [MockMatch(vector_data) for vector_data in vector_batch]


# Mock argument classes for command testing


def get_mock_args_fetch() -> argparse.Namespace:
    """Get mock arguments for fetch command."""
    return argparse.Namespace(
        command="fetch",
        vector_id="wiki-Test-LP-001-chunk-0",
        namespace=None,
        verbose=False,
        pretty=True,
    )


def get_mock_args_check_landmark() -> argparse.Namespace:
    """Get mock arguments for check-landmark command."""
    return argparse.Namespace(
        command="check-landmark",
        landmark_id="LP-001",
        namespace=None,
        verbose=False,
        prefix=None,
        limit=10,
    )


def get_mock_args_list_vectors() -> argparse.Namespace:
    """Get mock arguments for list-vectors command."""
    return argparse.Namespace(
        command="list-vectors",
        namespace=None,
        limit=100,
        prefix=None,
        verbose=False,
        pretty=False,
    )


def get_mock_args_validate() -> argparse.Namespace:
    """Get mock arguments for validate command."""
    return argparse.Namespace(
        command="validate",
        vector_id="wiki-Test-LP-001-chunk-0",
        namespace=None,
        verbose=True,
    )


def get_mock_args_compare() -> argparse.Namespace:
    """Get mock arguments for compare-vectors command."""
    return argparse.Namespace(
        command="compare-vectors",
        first_vector_id="test-vector-1",
        second_vector_id="test-vector-2",
        namespace=None,
        format="text",
    )


def get_mock_args_verify() -> argparse.Namespace:
    """Get mock arguments for verify-vectors command."""
    return argparse.Namespace(
        command="verify-vectors",
        namespace=None,
        limit=10,
        verbose=False,
        prefix=None,
        check_embeddings=False,
    )


def get_mock_args_verify_batch() -> argparse.Namespace:
    """Get mock arguments for verify-batch command."""
    return argparse.Namespace(
        command="verify-batch",
        vector_ids=["wiki-Test-LP-001-chunk-0", "wiki-Test-LP-001-chunk-1"],
        file=None,
        namespace=None,
        verbose=False,
        check_embeddings=False,
    )
