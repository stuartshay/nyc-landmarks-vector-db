"""
VectorMetadataValidator class for validating vector metadata against requirements.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.vector_id_validator import VectorIDValidator

logger = get_logger(__name__)


class VectorMetadataValidator:
    """
    A dedicated class for validating vector metadata against requirements.
    """

    # Required metadata fields for all vectors
    REQUIRED_METADATA = ["landmark_id", "source_type", "chunk_index", "text"]

    # Additional required metadata fields for Wikipedia vectors
    REQUIRED_WIKI_METADATA = ["article_title", "article_url"]

    @classmethod
    def validate(
        cls,
        vector_id: str,
        vector_data: Optional[Dict[str, Any]],
    ) -> Tuple[bool, List[str]]:
        """
        Validate a vector's metadata against requirements.

        Args:
            vector_id: The ID of the vector to validate
            vector_data: The vector data containing metadata and values

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        if not vector_data:
            return False, [f"Vector with ID '{vector_id}' not found"]

        metadata = vector_data.get("metadata", {})
        issues = []

        try:
            # Check for missing required fields
            issues.extend(cls._validate_required_fields(metadata))

            # Check for Wikipedia-specific fields if applicable
            if vector_id.startswith("wiki-"):
                issues.extend(cls._validate_wikipedia_fields(metadata))

            # Validate ID format using VectorIDValidator
            if not VectorIDValidator.validate_format(vector_id):
                issues.append("Invalid vector ID format")

            # Get source type from vector ID and validate against metadata
            issues.extend(cls._validate_source_type_consistency(vector_id, metadata))

            # Validate landmark_id and chunk_index consistency using VectorIDValidator
            issues.extend(cls._validate_landmark_consistency(vector_id, metadata))

            # Check if article title matches for Wikipedia vectors
            if vector_id.startswith("wiki-"):
                issues.extend(
                    cls._validate_wikipedia_title_consistency(vector_id, metadata)
                )

            # Check if vector has valid embeddings
            issues.extend(cls._validate_embeddings(vector_data))

            return len(issues) == 0, issues

        except Exception as e:
            logger.error(f"Error validating vector metadata for {vector_id}: {e}")
            return False, [f"Validation error: {str(e)}"]

    @classmethod
    def _validate_required_fields(cls, metadata: Dict[str, Any]) -> List[str]:
        """Validate that all required metadata fields are present."""
        issues = []
        for field in cls.REQUIRED_METADATA:
            if field not in metadata:
                issues.append(f"Missing required field: {field}")
        return issues

    @classmethod
    def _validate_wikipedia_fields(cls, metadata: Dict[str, Any]) -> List[str]:
        """Validate Wikipedia-specific metadata fields."""
        issues = []
        for field in cls.REQUIRED_WIKI_METADATA:
            if field not in metadata:
                issues.append(f"Missing required Wikipedia field: {field}")
        return issues

    @classmethod
    def _validate_source_type_consistency(
        cls, vector_id: str, metadata: Dict[str, Any]
    ) -> List[str]:
        """Validate that source type in ID matches metadata."""
        issues = []
        id_source_type = VectorIDValidator.get_source_type(vector_id)
        metadata_source_type = metadata.get("source_type", "unknown")

        if id_source_type != "unknown" and metadata_source_type != id_source_type:
            issues.append(
                f"Source type mismatch: ID indicates '{id_source_type}' but metadata has '{metadata_source_type}'"
            )
        return issues

    @classmethod
    def _validate_landmark_consistency(
        cls, vector_id: str, metadata: Dict[str, Any]
    ) -> List[str]:
        """Validate landmark_id and chunk_index consistency between ID and metadata."""
        issues = []
        landmark_info = VectorIDValidator.extract_landmark_info(vector_id)

        if landmark_info:
            id_landmark_id, id_chunk_index = landmark_info
            metadata_landmark_id = metadata.get("landmark_id", "")
            metadata_chunk_index = metadata.get("chunk_index", -1)

            if metadata_landmark_id != id_landmark_id:
                issues.append(
                    f"Landmark ID mismatch: ID has '{id_landmark_id}' but metadata has '{metadata_landmark_id}'"
                )

            if int(metadata_chunk_index) != id_chunk_index:
                issues.append(
                    f"Chunk index mismatch: ID has '{id_chunk_index}' but metadata has '{metadata_chunk_index}'"
                )
        return issues

    @classmethod
    def _validate_wikipedia_title_consistency(
        cls, vector_id: str, metadata: Dict[str, Any]
    ) -> List[str]:
        """Validate Wikipedia article title consistency between ID and metadata."""
        issues = []
        parts = vector_id.split("-")

        if len(parts) >= 4:
            article_title_from_id = parts[1].replace("_", " ")
            if "article_title" in metadata:
                if metadata["article_title"] != article_title_from_id:
                    issues.append("Article title in ID does not match metadata")
        return issues

    @classmethod
    def _validate_embeddings(cls, vector_data: Dict[str, Any]) -> List[str]:
        """Validate that embeddings are present and not all-zero."""
        issues = []
        values = vector_data.get("values", [])

        if not values:
            issues.append("Missing or empty embeddings")
        elif np.allclose(np.array(values), 0):
            issues.append("All-zero embeddings detected")

        return issues

    @classmethod
    def validate_metadata_only(
        cls,
        vector_id: str,
        metadata: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """
        Validate only metadata without embeddings data.

        Args:
            vector_id: The ID of the vector to validate
            metadata: The metadata dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        try:
            # Check for missing required fields
            issues.extend(cls._validate_required_fields(metadata))

            # Check for Wikipedia-specific fields if applicable
            if vector_id.startswith("wiki-"):
                issues.extend(cls._validate_wikipedia_fields(metadata))

            # Validate ID format using VectorIDValidator
            if not VectorIDValidator.validate_format(vector_id):
                issues.append("Invalid vector ID format")

            # Get source type from vector ID and validate against metadata
            issues.extend(cls._validate_source_type_consistency(vector_id, metadata))

            # Validate landmark_id and chunk_index consistency using VectorIDValidator
            issues.extend(cls._validate_landmark_consistency(vector_id, metadata))

            # Check if article title matches for Wikipedia vectors
            if vector_id.startswith("wiki-"):
                issues.extend(
                    cls._validate_wikipedia_title_consistency(vector_id, metadata)
                )

            return len(issues) == 0, issues

        except Exception as e:
            logger.error(f"Error validating vector metadata for {vector_id}: {e}")
            return False, [f"Validation error: {str(e)}"]
