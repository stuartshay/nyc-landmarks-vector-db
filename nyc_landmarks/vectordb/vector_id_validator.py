import re
from typing import Any, Dict, List


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
