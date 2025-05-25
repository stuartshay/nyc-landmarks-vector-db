#!/usr/bin/env python3
"""
Demonstration script for the new VectorMetadataValidator class.
"""

from nyc_landmarks.vectordb.vector_metadata_validator import VectorMetadataValidator


def main():
    """Demonstrate the VectorMetadataValidator functionality."""
    print("=== VectorMetadataValidator Demonstration ===\n")

    # Test case 1: Valid PDF vector
    print("1. Testing valid PDF vector:")
    vector_id = "pdf-LP00001-chunk001"
    vector_data = {
        "metadata": {
            "landmark_id": "LP00001",
            "source_type": "pdf",
            "chunk_index": 1,
            "text": "This is some landmark text content.",
        },
        "values": [0.1, 0.2, 0.3, 0.4, 0.5],
    }

    is_valid, issues = VectorMetadataValidator.validate(vector_id, vector_data)
    print(f"Vector ID: {vector_id}")
    print(f"Valid: {is_valid}")
    print(f"Issues: {issues}")
    print()

    # Test case 2: Invalid vector with missing fields
    print("2. Testing invalid vector with missing fields:")
    vector_id = "pdf-LP00002-chunk001"
    vector_data = {
        "metadata": {
            "landmark_id": "LP00002",
            # Missing source_type, chunk_index, text
        },
        "values": [0.1, 0.2, 0.3],
    }

    is_valid, issues = VectorMetadataValidator.validate(vector_id, vector_data)
    print(f"Vector ID: {vector_id}")
    print(f"Valid: {is_valid}")
    print(f"Issues: {issues}")
    print()

    # Test case 3: Wikipedia vector
    print("3. Testing Wikipedia vector:")
    vector_id = "wiki-Empire_State_Building-chunk001"
    vector_data = {
        "metadata": {
            "landmark_id": "empire_state_building",
            "source_type": "wikipedia",
            "chunk_index": 1,
            "text": "The Empire State Building is a famous landmark.",
            "article_title": "Empire State Building",
            "article_url": "https://en.wikipedia.org/wiki/Empire_State_Building",
        },
        "values": [0.1, 0.2, 0.3, 0.4],
    }

    is_valid, issues = VectorMetadataValidator.validate(vector_id, vector_data)
    print(f"Vector ID: {vector_id}")
    print(f"Valid: {is_valid}")
    print(f"Issues: {issues}")
    print()

    # Test case 4: Metadata-only validation
    print("4. Testing metadata-only validation:")
    vector_id = "pdf-LP00003-chunk001"
    metadata = {
        "landmark_id": "LP00003",
        "source_type": "pdf",
        "chunk_index": 1,
        "text": "Some landmark content.",
    }

    is_valid, issues = VectorMetadataValidator.validate_metadata_only(
        vector_id, metadata
    )
    print(f"Vector ID: {vector_id}")
    print(f"Valid: {is_valid}")
    print(f"Issues: {issues}")
    print()

    # Test case 5: None vector data
    print("5. Testing None vector data:")
    vector_id = "pdf-LP00004-chunk001"
    vector_data = None

    is_valid, issues = VectorMetadataValidator.validate(vector_id, vector_data)
    print(f"Vector ID: {vector_id}")
    print(f"Valid: {is_valid}")
    print(f"Issues: {issues}")
    print()

    print("=== Demonstration Complete ===")


if __name__ == "__main__":
    main()
