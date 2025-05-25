import re
from typing import Any, Dict, List, Optional, Tuple


class VectorIDValidator:
    """Validator for vector ID formats for both PDF and Wikipedia sources."""

    # PDF: LP-00029-chunk-0
    PDF_PATTERN = re.compile(r"^(LP-\d{5})-chunk-(\d+)$")
    # Wikipedia: wiki-...-LP-00029-chunk-0
    WIKI_PATTERN = re.compile(r"^wiki-.*-(LP-\d{5})-chunk-(\d+)$")

    @classmethod
    def is_valid(cls, vector_id: str, landmark_id: str, chunk_index: int) -> bool:
        """Check if the vector_id matches either the PDF or Wikipedia format for the given landmark and chunk."""
        expected_pdf = f"{landmark_id}-chunk-{chunk_index}"
        if vector_id == expected_pdf:
            return True
        # Check for Wikipedia format
        match = cls.WIKI_PATTERN.match(vector_id)
        if (
            match
            and match.group(1) == landmark_id
            and match.group(2) == str(chunk_index)
        ):
            return True
        return False

    @classmethod
    def validate_format(cls, vector_id: str) -> bool:
        """
        Validate if vector_id follows any valid format (PDF or Wikipedia).

        Args:
            vector_id: The vector ID to validate

        Returns:
            True if format is valid, False otherwise
        """
        return (
            cls.PDF_PATTERN.match(vector_id) is not None
            or cls.WIKI_PATTERN.match(vector_id) is not None
        )

    @classmethod
    def get_source_type(cls, vector_id: str) -> str:
        """
        Extract source type from vector_id.

        Args:
            vector_id: The vector ID to analyze

        Returns:
            Source type string ('wikipedia', 'pdf', or 'unknown')
        """
        if vector_id.startswith("wiki-"):
            return "wikipedia"
        elif cls.PDF_PATTERN.match(vector_id):
            return "pdf"
        else:
            return "unknown"

    @classmethod
    def extract_landmark_info(cls, vector_id: str) -> Optional[Tuple[str, int]]:
        """
        Extract landmark_id and chunk_index from vector_id.

        Args:
            vector_id: The vector ID to parse

        Returns:
            Tuple of (landmark_id, chunk_index) if valid format, None otherwise
        """
        # Try PDF format first
        pdf_match = cls.PDF_PATTERN.match(vector_id)
        if pdf_match:
            landmark_id = pdf_match.group(1)
            chunk_index = int(pdf_match.group(2))
            return landmark_id, chunk_index

        # Try Wikipedia format
        wiki_match = cls.WIKI_PATTERN.match(vector_id)
        if wiki_match:
            landmark_id = wiki_match.group(1)
            chunk_index = int(wiki_match.group(2))
            return landmark_id, chunk_index

        return None

    @classmethod
    def matches_landmark_and_chunk(
        cls, vector_id: str, landmark_id: str, chunk_index: int
    ) -> bool:
        """
        Check if vector_id matches the expected landmark_id and chunk_index.

        Args:
            vector_id: The vector ID to validate
            landmark_id: Expected landmark ID
            chunk_index: Expected chunk index

        Returns:
            True if vector_id matches the expected values
        """
        extracted_info = cls.extract_landmark_info(vector_id)
        if extracted_info is None:
            return False

        extracted_landmark_id, extracted_chunk_index = extracted_info
        return (
            extracted_landmark_id == landmark_id
            and extracted_chunk_index == chunk_index
        )


def check_vector_formats(results: List[Dict[str, Any]], landmark_id: str) -> bool:
    """Check if all vector IDs follow the expected format (PDF or Wikipedia)."""
    correct_format = True
    for result in results:
        vector_id = result.get("id", "")
        metadata = result.get("metadata", {})
        chunk_index = metadata.get("chunk_index", -1)
        if not VectorIDValidator.is_valid(vector_id, landmark_id, int(chunk_index)):
            # Optionally, raise or collect errors here
            correct_format = False
    return correct_format
