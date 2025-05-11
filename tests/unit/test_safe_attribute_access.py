"""
Unit tests for the safe_get_attribute function in process_all_landmarks.py.
"""

import unittest
from typing import Any, Dict, NamedTuple

from scripts.process_all_landmarks import safe_get_attribute


class MockPydanticModel:
    """A mock Pydantic model with predefined attributes."""

    def __init__(self, name: str, borough: str, pdf_url: str) -> None:
        self.name = name
        self.borough = borough
        self.pdfReportUrl = pdf_url


class LpcReportDetailResponse(NamedTuple):
    """A mock LpcReportDetailResponse using NamedTuple."""

    name: str
    borough: str
    pdfReportUrl: str


class TestSafeAttributeAccess(unittest.TestCase):
    """Test cases for the safe_get_attribute function."""

    def setUp(self) -> None:
        """Set up test data."""
        # Dictionary
        self.dict_obj: Dict[str, Any] = {
            "name": "Empire State Building",
            "borough": "Manhattan",
            "pdfReportUrl": "https://example.com/empire-state.pdf",
        }

        # Pydantic-like model
        self.model_obj = MockPydanticModel(
            name="Brooklyn Bridge",
            borough="Brooklyn",
            pdf_url="https://example.com/brooklyn-bridge.pdf",
        )

        # NamedTuple (similar to actual LpcReportDetailResponse)
        self.named_tuple_obj = LpcReportDetailResponse(
            name="Statue of Liberty",
            borough="Manhattan",
            pdfReportUrl="https://example.com/statue-of-liberty.pdf",
        )

    def test_safe_get_from_dict(self) -> None:
        """Test safe_get_attribute with dictionary objects."""
        # Get existing attribute
        self.assertEqual(
            safe_get_attribute(self.dict_obj, "name"), "Empire State Building"
        )

        # Get with default
        self.assertEqual(
            safe_get_attribute(self.dict_obj, "non_existent", "default"), "default"
        )

        # Get non-existent attribute without default
        self.assertIsNone(safe_get_attribute(self.dict_obj, "non_existent"))

    def test_safe_get_from_model(self) -> None:
        """Test safe_get_attribute with Pydantic-like model objects."""
        # Get existing attribute
        self.assertEqual(safe_get_attribute(self.model_obj, "name"), "Brooklyn Bridge")

        # Get with default
        self.assertEqual(
            safe_get_attribute(self.model_obj, "non_existent", "default"), "default"
        )

        # Get non-existent attribute without default
        self.assertIsNone(safe_get_attribute(self.model_obj, "non_existent"))

    def test_safe_get_from_named_tuple(self) -> None:
        """Test safe_get_attribute with NamedTuple objects (LpcReportDetailResponse)."""
        # Get existing attribute
        self.assertEqual(
            safe_get_attribute(self.named_tuple_obj, "name"), "Statue of Liberty"
        )

        # Get with default
        self.assertEqual(
            safe_get_attribute(self.named_tuple_obj, "non_existent", "default"),
            "default",
        )

        # Get non-existent attribute without default
        self.assertIsNone(safe_get_attribute(self.named_tuple_obj, "non_existent"))

    def test_safe_get_camelcase_pdf_url(self) -> None:
        """Test safe_get_attribute with camelCase attribute names."""
        # From dict
        self.assertEqual(
            safe_get_attribute(self.dict_obj, "pdfReportUrl"),
            "https://example.com/empire-state.pdf",
        )

        # From model
        self.assertEqual(
            safe_get_attribute(self.model_obj, "pdfReportUrl"),
            "https://example.com/brooklyn-bridge.pdf",
        )

        # From named tuple
        self.assertEqual(
            safe_get_attribute(self.named_tuple_obj, "pdfReportUrl"),
            "https://example.com/statue-of-liberty.pdf",
        )

    def test_safe_get_with_none_object(self) -> None:
        """Test safe_get_attribute with None object."""
        # Should return default for None object
        self.assertEqual(safe_get_attribute(None, "anything", "default"), "default")
        self.assertIsNone(safe_get_attribute(None, "anything"))


if __name__ == "__main__":
    unittest.main()
