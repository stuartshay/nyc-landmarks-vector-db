"""
Unit tests for CoreDataStoreAPI methods.

This module tests the CoreDataStoreAPI class from nyc_landmarks.db.coredatastore_api,
with particular focus on the standardization of landmark IDs.
"""

import unittest
from unittest.mock import Mock, patch

from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI


class TestCoreDataStoreAPI(unittest.TestCase):
    """Tests for the CoreDataStoreAPI class."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a CoreDataStoreAPI instance
        self.api = CoreDataStoreAPI()

    def test_standardize_landmark_id_with_lp_prefix(self) -> None:
        """Test _standardize_landmark_id method with LP-prefixed IDs."""
        # Test with standard LP prefix format
        variations = self.api._standardize_landmark_id("LP-12345")
        self.assertEqual(variations, ["LP-12345"])

        # Test with LP prefix and leading zeros
        variations = self.api._standardize_landmark_id("LP-01234")
        self.assertEqual(variations, ["LP-01234"])

        # Test with LP prefix and suffix
        variations = self.api._standardize_landmark_id("LP-01234A")
        self.assertIn("LP-01234A", variations)
        self.assertIn("LP-01234", variations)  # Should include version without suffix
        # In most cases, only 2 unique variations exist after deduplication
        self.assertGreaterEqual(len(variations), 2)  # Should have at least 2 variations

    def test_standardize_landmark_id_without_lp_prefix(self) -> None:
        """Test _standardize_landmark_id method with IDs missing LP prefix."""
        # Test with numeric ID without LP prefix
        variations = self.api._standardize_landmark_id("12345")
        self.assertEqual(
            variations[0], "LP-12345"
        )  # First variation should have LP prefix

        # Test with numeric ID with leading zeros
        variations = self.api._standardize_landmark_id("01234")
        self.assertEqual(variations[0], "LP-01234")  # Should preserve format

        # Test with numeric ID without leading zeros
        variations = self.api._standardize_landmark_id("1234")
        self.assertEqual(variations[0], "LP-01234")  # Should add leading zeros

        # Test with numeric ID and suffix
        variations = self.api._standardize_landmark_id("1234A")
        self.assertEqual(
            variations[0], "LP-1234A"
        )  # First variation should preserve suffix
        self.assertIn(
            "LP-01234", variations
        )  # Should include zerofilled version without suffix

    def test_standardize_landmark_id_with_complex_formats(self) -> None:
        """Test _standardize_landmark_id method with complex ID formats."""
        # Test with complex LP prefix format with suffix
        variations = self.api._standardize_landmark_id("LP-02118A")
        self.assertEqual(variations[0], "LP-02118A")  # Should preserve original
        self.assertIn("LP-02118", variations)  # Should include version without suffix
        # The third variation is often removed due to deduplication

        # Test with numeric only version of the same
        variations = self.api._standardize_landmark_id("2118A")
        self.assertEqual(variations[0], "LP-2118A")  # Should add LP prefix
        self.assertIn(
            "LP-02118", variations
        )  # Should include zerofilled version without suffix

    def test_standardize_landmark_id_with_edge_cases(self) -> None:
        """Test _standardize_landmark_id method with edge cases."""
        # Test with empty ID (should not happen in practice, but handle it gracefully)
        variations = self.api._standardize_landmark_id("")
        self.assertEqual(variations[0], "LP-00000")  # Should return a valid format

        # Test with very short ID
        variations = self.api._standardize_landmark_id("1")
        self.assertEqual(variations[0], "LP-00001")  # Should pad with zeros

        # Test with very long ID (should be handled reasonably)
        variations = self.api._standardize_landmark_id("123456789")
        self.assertEqual(variations[0], "LP-123456789")  # Should preserve digits

    def test_standardize_landmark_id_uniqueness(self) -> None:
        """Test that _standardize_landmark_id returns unique variations."""
        # Test that duplicates are removed
        variations = self.api._standardize_landmark_id("LP-00001")
        # Should be a unique list (no duplicates)
        self.assertEqual(len(variations), len(set(variations)))

        # Test with an ID that might generate the same variation multiple ways
        variations = self.api._standardize_landmark_id("LP-00001A")
        # Should be a unique list (no duplicates)
        self.assertEqual(len(variations), len(set(variations)))


if __name__ == "__main__":
    unittest.main()
