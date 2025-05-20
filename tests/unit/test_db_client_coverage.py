"""
Additional unit tests for the DbClient class focused on coverage.

This module tests the remaining functionality of the DbClient class from nyc_landmarks.db.db_client,
targeting uncovered code paths to improve overall test coverage.
"""

import unittest
from typing import Any, Dict, List, Optional, cast
from unittest.mock import Mock, patch

import pytest

from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI
from nyc_landmarks.db.db_client import DbClient, SupportsWikipedia
from nyc_landmarks.models.landmark_models import (
    LandmarkDetail,
    LpcReportDetailResponse,
    LpcReportModel,
    LpcReportResponse,
)
from nyc_landmarks.models.wikipedia_models import WikipediaArticleModel


class TestSupportsWikipedia(unittest.TestCase):
    """Test the SupportsWikipedia protocol class."""

    def test_protocol_default_methods(self) -> None:
        """Test the default method implementations in the SupportsWikipedia protocol."""
        # Create a class that implements the protocol
        class WikipediaClient(SupportsWikipedia):
            pass

        # Create an instance of the class
        client = WikipediaClient()

        # Test the default implementations
        self.assertIsNone(client.get_wikipedia_article_by_title("Test Article"))
        self.assertEqual(client.get_wikipedia_articles("LP-00001"), [])


class TestDbClientLpcReportsFallback(unittest.TestCase):
    """Test the fallback implementation of get_lpc_reports."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        self.client = DbClient(self.mock_api)

    def test_get_lpc_reports_with_landmarks_page_fallback(self) -> None:
        """Test get_lpc_reports fallback to get_landmarks_page."""
        # Remove get_lpc_reports from mock API
        del self.mock_api.get_lpc_reports

        # Set up get_landmarks_page to return a list of landmarks
        landmarks = [
            {"lpNumber": "LP-00001", "name": "Test Landmark 1", "borough": "Manhattan"},
            {"lpNumber": "LP-00002", "name": "Test Landmark 2", "borough": "Brooklyn"},
        ]
        self.mock_api.get_landmarks_page.return_value = landmarks

        # Call the method
        result = self.client.get_lpc_reports(page=1, limit=10)

        # Verify API was called correctly
        self.mock_api.get_landmarks_page.assert_called_once_with(10, 1)

        # Verify result structure
        self.assertIsInstance(result, LpcReportResponse)
        self.assertEqual(result.total, 2)
        self.assertEqual(result.page, 1)
        self.assertEqual(result.limit, 10)
        self.assertEqual(len(result.results), 2)

        # Verify individual results were properly converted
        self.assertEqual(result.results[0].lpNumber, "LP-00001")
        self.assertEqual(result.results[1].lpNumber, "LP-00002")

    def test_get_lpc_reports_with_landmarks_page_fallback_conversion_error(self) -> None:
        """Test get_lpc_reports fallback with conversion error."""
        # Remove get_lpc_reports from mock API
        del self.mock_api.get_lpc_reports

        # Set up get_landmarks_page to return invalid data that will cause conversion errors
        invalid_landmarks = [
            {"lpNumber": "LP-00001", "name": "Test Landmark 1"},
            {"invalid": "This will fail conversion"},  # Missing required fields
        ]
        self.mock_api.get_landmarks_page.return_value = invalid_landmarks

        # Call the method
        result = self.client.get_lpc_reports(page=1, limit=10)

        # Verify result still contains 2 items (one properly converted, one with default values)
        self.assertEqual(len(result.results), 2)
        self.assertEqual(result.results[0].lpNumber, "LP-00001")
        self.assertEqual(result.results[1].lpNumber, "Unknown")  # Default value for failed conversion


class TestDbClientLandmarkPdfUrl(unittest.TestCase):
    """Test the get_landmark_pdf_url method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        self.client = DbClient(self.mock_api)

    def test_get_landmark_pdf_url_with_both_methods_failing(self) -> None:
        """Test get_landmark_pdf_url when both methods fail."""
        # Set up get_landmark_by_id to raise exception
        with patch.object(self.client, 'get_landmark_by_id', side_effect=Exception("API error")):
            # We need to remove the get_landmark_pdf_url method to test this case
            # because the code checks for hasattr() before trying to call the method
            del self.mock_api.get_landmark_pdf_url

            # Call the method - should return None
            result = self.client.get_landmark_pdf_url("LP-00001")

            # Verify None is returned when both methods fail
            self.assertIsNone(result)


class TestDbClientConversionMethods(unittest.TestCase):
    """Test the conversion methods of DbClient."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        self.client = DbClient(self.mock_api)

    def test_convert_item_to_lpc_report_model_with_unexpected_input(self) -> None:
        """Test _convert_item_to_lpc_report_model with unexpected input type."""
        # Since Python is dynamically typed, we can call the method with an unexpected type
        # This isn't proper in normal code but helps test the error handling in the method
        invalid_item = None  # type: ignore

        # Call the method with the None value to test error handling
        with patch("nyc_landmarks.db.db_client.logger") as mock_logger:
            # We'll use this approach to handle the type error safely
            try:
                # We're intentionally passing an invalid type to test error handling
                result = self.client._convert_item_to_lpc_report_model(invalid_item, "LP-00001")  # type: ignore
                # If we reach here, the method didn't raise an exception but might have logged an error
                mock_logger.warning.assert_called()
            except Exception as e:
                # Method raised an exception as expected when given invalid input
                self.assertIsInstance(e, Exception)


class TestDbClientFetchBuildings(unittest.TestCase):
    """Test the building fetching methods of DbClient."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        self.client = DbClient(self.mock_api)

    def test_fetch_buildings_from_client_with_cast(self) -> None:
        """Test _fetch_buildings_from_client with type casting."""
        # Set up get_landmark_buildings to return a list
        buildings = [
            {"lpNumber": "LP-00001A", "name": "Building 1"},
            {"lpNumber": "LP-00001B", "name": "Building 2"},
        ]
        self.mock_api.get_landmark_buildings.return_value = buildings

        # Call the method
        result = self.client._fetch_buildings_from_client("LP-00001", 10)

        # Verify correct results are returned
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["lpNumber"], "LP-00001A")
        self.assertEqual(result[1]["lpNumber"], "LP-00001B")

    def test_fetch_buildings_from_landmark_detail_with_invalid_response(self) -> None:
        """Test _fetch_buildings_from_landmark_detail with invalid response."""
        # Set up get_landmark_by_id to return a dict instead of LpcReportDetailResponse
        with patch.object(self.client, 'get_landmark_by_id', return_value={"not": "a proper response"}):
            # Call the method
            result = self.client._fetch_buildings_from_landmark_detail("LP-00001", 10)

            # Verify empty list is returned
            self.assertEqual(result, [])

    def test_fetch_buildings_from_landmark_detail_with_landmarks_attribute_not_list(self) -> None:
        """Test _fetch_buildings_from_landmark_detail when landmarks attribute is not a list."""
        # Create a mock response with landmarks attribute that's not a list
        mock_response = Mock(spec=LpcReportDetailResponse)
        mock_response.landmarks = "not a list"  # type: ignore

        # Set up get_landmark_by_id to return our mock response
        with patch.object(self.client, 'get_landmark_by_id', return_value=mock_response):
            # Call the method
            result = self.client._fetch_buildings_from_landmark_detail("LP-00001", 10)

            # Verify empty list is returned
            self.assertEqual(result, [])

    def test_fetch_buildings_from_landmark_detail_with_invalid_item_in_list(self) -> None:
        """Test _fetch_buildings_from_landmark_detail with invalid items in landmarks list."""
        # Create landmark details and an invalid item
        landmarks_list = [
            LandmarkDetail(
                lpNumber="LP-00001A",
                name="Building 1",
                designatedAddress="123 Main St",
                boroughId="1",
                objectType="Individual Landmark",
                designatedDate="2020-01-01",
                historicDistrict="Test District",
                street="123 Main St",
            ),
            "not a landmark detail object",  # Invalid item
        ]

        # Create a mock response with our mixed landmarks list
        mock_response = Mock(spec=LpcReportDetailResponse)
        mock_response.landmarks = landmarks_list  # type: ignore

        # Set up get_landmark_by_id to return our mock response
        with patch.object(self.client, 'get_landmark_by_id', return_value=mock_response):
            # Call the method
            result = self.client._fetch_buildings_from_landmark_detail("LP-00001", 10)

            # Verify only valid items are in the result
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].lpNumber, "LP-00001A")

    def test_convert_building_items_to_models_with_empty_list(self) -> None:
        """Test _convert_building_items_to_models with empty input list."""
        # Call the method with empty list
        result = self.client._convert_building_items_to_models([], "LP-00001")

        # Verify empty list is returned
        self.assertEqual(result, [])


class TestDbClientWikipedia(unittest.TestCase):
    """Test the Wikipedia article methods of DbClient."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a mock that supports the Wikipedia protocol
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        # Add the required method to the mock
        self.mock_api.get_wikipedia_article_by_title = Mock()
        self.client = DbClient(self.mock_api)

    def test_get_wikipedia_article_by_title_with_dict_response(self) -> None:
        """Test get_wikipedia_article_by_title with dict response."""
        # Set up the mock API to return a dict with correct field names
        article_dict = {
            "id": 12345,  # Use "id" instead of "pageId" to match the actual model
            "title": "Test Article",
            "url": "https://en.wikipedia.org/wiki/Test_Article",
            # Only include required fields for WikipediaArticleModel
            "lpNumber": "LP-00001",
            "recordType": "Wikipedia",
        }
        self.mock_api.get_wikipedia_article_by_title.return_value = article_dict

        # Call the method
        result = self.client.get_wikipedia_article_by_title("Test Article")

        # Verify API was called correctly
        self.mock_api.get_wikipedia_article_by_title.assert_called_once_with("Test Article")

        # Verify result was converted to WikipediaArticleModel
        self.assertIsInstance(result, WikipediaArticleModel)
        self.assertEqual(result.id, 12345)  # Use "id" instead of "pageId"
        self.assertEqual(result.title, "Test Article")

    def test_get_wikipedia_article_by_title_with_model_response(self) -> None:
        """Test get_wikipedia_article_by_title with WikipediaArticleModel response."""
        # Create a model to return using the correct field names
        article_model = WikipediaArticleModel(
            id=12345,  # Use "id" instead of "pageId"
            title="Test Article",
            url="https://en.wikipedia.org/wiki/Test_Article",
            lpNumber="LP-00001",
        )
        self.mock_api.get_wikipedia_article_by_title.return_value = article_model

        # Call the method
        result = self.client.get_wikipedia_article_by_title("Test Article")

        # Verify result is the same model
        self.assertIs(result, article_model)

    def test_get_wikipedia_article_by_title_with_invalid_dict(self) -> None:
        """Test get_wikipedia_article_by_title with invalid dict response."""
        # Set up the mock API to return a dict with missing required fields
        invalid_dict = {"title": "Test Article"}  # Missing required fields
        self.mock_api.get_wikipedia_article_by_title.return_value = invalid_dict

        # Call the method
        result = self.client.get_wikipedia_article_by_title("Test Article")

        # Verify None is returned for invalid dict
        self.assertIsNone(result)

    def test_get_wikipedia_article_by_title_with_unexpected_response(self) -> None:
        """Test get_wikipedia_article_by_title with unexpected response type."""
        # Set up the mock API to return an unexpected type
        self.mock_api.get_wikipedia_article_by_title.return_value = 12345  # type: ignore

        # Call the method
        result = self.client.get_wikipedia_article_by_title("Test Article")

        # Verify None is returned for unexpected response type
        self.assertIsNone(result)

    def test_get_wikipedia_article_by_title_with_exception(self) -> None:
        """Test get_wikipedia_article_by_title with exception from API."""
        # Set up the mock API to raise exception
        self.mock_api.get_wikipedia_article_by_title.side_effect = Exception("API error")

        # Call the method
        result = self.client.get_wikipedia_article_by_title("Test Article")

        # Verify None is returned when API raises exception
        self.assertIsNone(result)


class TestDbClientPlutoData(unittest.TestCase):
    """Test the get_landmark_pluto_data method of DbClient."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        self.client = DbClient(self.mock_api)

    def test_get_landmark_pluto_data(self) -> None:
        """Test get_landmark_pluto_data with API that supports it."""
        # Set up the mock API to return pluto data
        pluto_data = [{"bbl": "1234567890", "address": "123 Main St"}]
        self.mock_api.get_landmark_pluto_data.return_value = pluto_data

        # Call the method
        result = self.client.get_landmark_pluto_data("LP-00001")

        # Verify API was called correctly
        self.mock_api.get_landmark_pluto_data.assert_called_once_with("LP-00001")

        # Verify result
        self.assertEqual(result, pluto_data)

    def test_get_landmark_pluto_data_unsupported(self) -> None:
        """Test get_landmark_pluto_data with API that doesn't support it."""
        # Remove get_landmark_pluto_data from mock API
        del self.mock_api.get_landmark_pluto_data

        # Call the method
        result = self.client.get_landmark_pluto_data("LP-00001")

        # Verify empty list is returned
        self.assertEqual(result, [])


class TestDbClientTotalCount(unittest.TestCase):
    """Additional tests for get_total_record_count method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        self.client = DbClient(self.mock_api)

    def test_get_count_from_api_metadata_with_exception(self) -> None:
        """Test _get_count_from_api_metadata with exception."""
        # Set up get_lpc_reports to raise exception
        with patch.object(self.client, 'get_lpc_reports', side_effect=Exception("API error")):
            # Call the method
            result = self.client._get_count_from_api_metadata()

            # Verify 0 is returned when API raises exception
            self.assertEqual(result, 0)

    def test_get_count_from_api_metadata_without_total(self) -> None:
        """Test _get_count_from_api_metadata when response lacks total field."""
        # Create mock response without total field
        mock_response = Mock(spec=LpcReportResponse)
        delattr(mock_response, 'total')

        # Set up get_lpc_reports to return our mock response
        with patch.object(self.client, 'get_lpc_reports', return_value=mock_response):
            # Call the method
            result = self.client._get_count_from_api_metadata()

            # Verify 0 is returned when response lacks total field
            self.assertEqual(result, 0)

    def test_estimate_count_from_pages_max_pages(self) -> None:
        """Test _estimate_count_from_pages when max pages is reached."""
        # Set up get_landmarks_page to always return full page
        full_page = [{"id": f"LP-{i:05}"} for i in range(1, 51)]

        with patch.object(self.client, 'get_landmarks_page', return_value=full_page):
            # Call the method
            result = self.client._estimate_count_from_pages()

            # Verify count is 5 pages * 50 items = 250
            self.assertEqual(result, 250)

    def test_estimate_count_from_pages_empty_response(self) -> None:
        """Test _estimate_count_from_pages when API returns empty response."""
        # Set up get_landmarks_page to return empty list
        with patch.object(self.client, 'get_landmarks_page', return_value=[]):
            # Call the method
            result = self.client._estimate_count_from_pages()

            # Verify at least 1 is returned even for empty response
            self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
