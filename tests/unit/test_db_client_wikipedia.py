"""
Wikipedia integration unit tests for the DbClient class.

This module tests the Wikipedia integration functionality of the DbClient class
from nyc_landmarks.db.db_client, focusing on fetching Wikipedia articles for landmarks.
"""

import unittest
from unittest.mock import Mock

from nyc_landmarks.db._coredatastore_api import _CoreDataStoreAPI as CoreDataStoreAPI
from nyc_landmarks.db.db_client import DbClient


class TestWikipediaIntegration(unittest.TestCase):
    """Unit tests for Wikipedia integration in DbClient class."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock CoreDataStoreAPI instance
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        # Create a DbClient instance with the mock API
        self.client = DbClient(self.mock_api)

    def test_get_wikipedia_articles(self) -> None:
        """Test get_wikipedia_articles method."""
        # Set up mock API to return Wikipedia articles
        articles = [{"url": "https://en.wikipedia.org/wiki/Test", "title": "Test"}]
        self.mock_api.get_wikipedia_articles.return_value = articles

        # Call the method
        result = self.client.get_wikipedia_articles("LP-00001")

        # Verify API was called correctly
        self.mock_api.get_wikipedia_articles.assert_called_once_with("LP-00001")

        # Verify result
        self.assertEqual(result, articles)

    def test_get_wikipedia_articles_with_error(self) -> None:
        """Test get_wikipedia_articles method with API raising an error."""
        # Set up mock API to raise an exception
        self.mock_api.get_wikipedia_articles.side_effect = Exception("API error")

        # Call the method - should return empty list for error case
        result = self.client.get_wikipedia_articles("LP-00001")

        # Verify API was called correctly
        self.mock_api.get_wikipedia_articles.assert_called_once_with("LP-00001")

        # Verify empty list is returned for error case
        self.assertEqual(result, [])

    def test_get_wikipedia_articles_client_lacks_method(self) -> None:
        """Test get_wikipedia_articles when client doesn't have the method."""
        # Set up a mock that doesn't have get_wikipedia_articles method
        limited_mock_api = Mock(spec=[])
        limited_client = DbClient(limited_mock_api)

        # Call the method - should return empty list
        result = limited_client.get_wikipedia_articles("LP-00001")

        # Verify empty list is returned
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
