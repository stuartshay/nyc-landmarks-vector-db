"""
Unit tests for VectorMetadataValidator class.
"""

from unittest.mock import patch

from nyc_landmarks.vectordb.vector_metadata_validator import VectorMetadataValidator


class TestVectorMetadataValidator:
    """Test cases for VectorMetadataValidator."""

    def test_validate_valid_vector(self) -> None:
        """Test validation of a valid vector."""
        vector_id = "pdf-landmark123-chunk001"
        vector_data = {
            "metadata": {
                "landmark_id": "landmark123",
                "source_type": "pdf",
                "chunk_index": 1,
                "text": "Some text content",
            },
            "values": [0.1, 0.2, 0.3],
        }

        with (
            patch(
                "nyc_landmarks.vectordb.vector_metadata_validator.VectorIDValidator.validate_format",
                return_value=True,
            ),
            patch(
                "nyc_landmarks.vectordb.vector_metadata_validator.VectorIDValidator.get_source_type",
                return_value="pdf",
            ),
            patch(
                "nyc_landmarks.vectordb.vector_metadata_validator.VectorIDValidator.extract_landmark_info",
                return_value=("landmark123", 1),
            ),
        ):

            is_valid, issues = VectorMetadataValidator.validate(vector_id, vector_data)

            assert is_valid is True
            assert len(issues) == 0

    def test_validate_missing_required_fields(self) -> None:
        """Test validation with missing required fields."""
        vector_id = "pdf-landmark123-chunk001"
        vector_data = {
            "metadata": {
                "landmark_id": "landmark123",
                # Missing source_type, chunk_index, text
            },
            "values": [0.1, 0.2, 0.3],
        }

        with patch(
            "nyc_landmarks.vectordb.vector_metadata_validator.VectorIDValidator.validate_format",
            return_value=True,
        ):
            is_valid, issues = VectorMetadataValidator.validate(vector_id, vector_data)

            assert is_valid is False
            assert len(issues) == 3
            assert "Missing required field: source_type" in issues
            assert "Missing required field: chunk_index" in issues
            assert "Missing required field: text" in issues

    def test_validate_wikipedia_vector(self) -> None:
        """Test validation of a Wikipedia vector."""
        vector_id = "wiki-Empire_State_Building-chunk001"
        vector_data = {
            "metadata": {
                "landmark_id": "empire_state_building",
                "source_type": "wikipedia",
                "chunk_index": 1,
                "text": "Some text content",
                "article_title": "Empire State Building",
                "article_url": "https://en.wikipedia.org/wiki/Empire_State_Building",
            },
            "values": [0.1, 0.2, 0.3],
        }

        with (
            patch(
                "nyc_landmarks.vectordb.vector_metadata_validator.VectorIDValidator.validate_format",
                return_value=True,
            ),
            patch(
                "nyc_landmarks.vectordb.vector_metadata_validator.VectorIDValidator.get_source_type",
                return_value="wikipedia",
            ),
            patch(
                "nyc_landmarks.vectordb.vector_metadata_validator.VectorIDValidator.extract_landmark_info",
                return_value=("empire_state_building", 1),
            ),
        ):

            is_valid, issues = VectorMetadataValidator.validate(vector_id, vector_data)

            assert is_valid is True
            assert len(issues) == 0

    def test_validate_missing_embeddings(self) -> None:
        """Test validation with missing embeddings."""
        vector_id = "pdf-landmark123-chunk001"
        vector_data = {
            "metadata": {
                "landmark_id": "landmark123",
                "source_type": "pdf",
                "chunk_index": 1,
                "text": "Some text content",
            },
            "values": [],
        }

        with (
            patch(
                "nyc_landmarks.vectordb.vector_metadata_validator.VectorIDValidator.validate_format",
                return_value=True,
            ),
            patch(
                "nyc_landmarks.vectordb.vector_metadata_validator.VectorIDValidator.get_source_type",
                return_value="pdf",
            ),
            patch(
                "nyc_landmarks.vectordb.vector_metadata_validator.VectorIDValidator.extract_landmark_info",
                return_value=("landmark123", 1),
            ),
        ):

            is_valid, issues = VectorMetadataValidator.validate(vector_id, vector_data)

            assert is_valid is False
            assert "Missing or empty embeddings" in issues

    def test_validate_metadata_only(self) -> None:
        """Test metadata-only validation."""
        vector_id = "pdf-landmark123-chunk001"
        metadata = {
            "landmark_id": "landmark123",
            "source_type": "pdf",
            "chunk_index": 1,
            "text": "Some text content",
        }

        with (
            patch(
                "nyc_landmarks.vectordb.vector_metadata_validator.VectorIDValidator.validate_format",
                return_value=True,
            ),
            patch(
                "nyc_landmarks.vectordb.vector_metadata_validator.VectorIDValidator.get_source_type",
                return_value="pdf",
            ),
            patch(
                "nyc_landmarks.vectordb.vector_metadata_validator.VectorIDValidator.extract_landmark_info",
                return_value=("landmark123", 1),
            ),
        ):

            is_valid, issues = VectorMetadataValidator.validate_metadata_only(
                vector_id, metadata
            )

            assert is_valid is True
            assert len(issues) == 0

    def test_validate_none_vector_data(self) -> None:
        """Test validation with None vector data."""
        vector_id = "pdf-landmark123-chunk001"
        vector_data = None

        is_valid, issues = VectorMetadataValidator.validate(vector_id, vector_data)

        assert is_valid is False
        assert f"Vector with ID '{vector_id}' not found" in issues
