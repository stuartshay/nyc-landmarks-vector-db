"""
Additional unit tests for the DbClient class focusing on coverage gaps.

This module tests specific areas in DbClient with low coverage to achieve
at least 80% test coverage across the codebase.
"""

import unittest
from unittest.mock import Mock, patch

from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI
from nyc_landmarks.db.db_client import DbClient, SupportsWikipedia
from nyc_landmarks.models.landmark_models import (
    LpcReportDetailResponse,
    LpcReportResponse,
    PlutoDataModel,
)
from nyc_landmarks.models.wikipedia_models import WikipediaArticleModel


class TestSupportsWikipediaProtocol(unittest.TestCase):
    """Tests for the SupportsWikipedia protocol implementation."""

    def test_protocol_methods(self) -> None:
        """Test the default implementations of the protocol methods."""

        # Create a class that just implements the protocol
        class MinimalWikipediaClient(SupportsWikipedia):
            pass

        # Instantiate the client
        client = MinimalWikipediaClient()

        # Test default implementations
        self.assertIsNone(client.get_wikipedia_article_by_title("Test Article"))
        self.assertEqual(client.get_wikipedia_articles("LP-12345"), [])


class TestGetLpcReportsFallback(unittest.TestCase):
    """Tests for the get_lpc_reports method fallback functionality."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock CoreDataStoreAPI instance without get_lpc_reports
        self.mock_api = Mock(spec=["get_landmarks_page"])
        # Create a DbClient instance with the mock API
        self.client = DbClient(self.mock_api)

    def test_fallback_to_get_landmarks_page(self) -> None:
        """Test fallback to get_landmarks_page when get_lpc_reports is unavailable."""
        # Create a mock LpcReportResponse to return from get_landmarks_page
        from nyc_landmarks.models.landmark_models import LpcReportModel

        mock_results = [
            LpcReportModel(
                lpNumber="LP-12345",
                name="Test Landmark",
                objectType="Individual Landmark",
                borough="Manhattan",
                dateDesignated="2020-01-01",
                lpcId="",  # Required field
                street="",  # Required field
                architect="",  # Required field
                style="",  # Required field
                photoStatus=False,
                mapStatus=False,
                neighborhood="",
                zipCode="",
                photoUrl=None,
                pdfReportUrl=None,
            )
        ]

        mock_response = LpcReportResponse(
            results=mock_results,
            page=1,
            limit=10,
            total=1,
            **{"from": 1},  # Use unpacking for the "from" field
            to=1,
        )

        # Set up mock get_landmarks_page to return our mock response
        self.mock_api.get_landmarks_page.return_value = mock_response

        # Call the method
        result = self.client.get_lpc_reports(page=1, limit=10)

        # Verify API was called correctly
        self.mock_api.get_landmarks_page.assert_called_once_with(10, 1)

        # Verify result is LpcReportResponse
        self.assertIsInstance(result, LpcReportResponse)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0].lpNumber, "LP-12345")
        self.assertEqual(result.results[0].name, "Test Landmark")
        self.assertEqual(result.page, 1)
        self.assertEqual(result.limit, 10)

    def test_fallback_with_invalid_item(self) -> None:
        """Test handling of invalid items during conversion in fallback."""
        # Create a mock get_landmarks_page method that returns a list
        # We need to modify the mock to return a list instead of a LpcReportResponse
        # because we're testing the fallback path specifically
        from nyc_landmarks.models.landmark_models import LpcReportResponse

        # Set up mock get_landmarks_page to return a list with an invalid item
        self.mock_api.get_landmarks_page.return_value = [
            {
                # Missing required fields
                "name": "Invalid Landmark"
            }
        ]

        # Call the method
        result = self.client.get_lpc_reports(page=1, limit=10)

        # Verify result has a valid model with defaults
        self.assertIsInstance(result, LpcReportResponse)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0].name, "Unknown")  # Default value
        self.assertEqual(result.results[0].lpNumber, "Unknown")  # Default value

    def test_fallback_with_exception(self) -> None:
        """Test that get_lpc_reports exception is properly raised."""
        # Set up mock to raise exception
        self.mock_api.get_landmarks_page.side_effect = Exception("API error")

        # We expect an exception to be raised
        with self.assertRaises(Exception):
            self.client.get_lpc_reports(page=1, limit=10)


class TestLandmarkPdfUrl(unittest.TestCase):
    """Tests for the get_landmark_pdf_url method."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock CoreDataStoreAPI instance
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        # Create a DbClient instance with the mock API
        self.client = DbClient(self.mock_api)

    def test_get_landmark_pdf_url_fallback_with_none(self) -> None:
        """Test get_landmark_pdf_url fallback returns None when all methods fail."""
        # Set up mock get_landmark_by_id to raise exception
        with patch.object(
            self.client, "get_landmark_by_id", side_effect=Exception("API error")
        ):
            # Also make get_landmark_pdf_url return None
            self.mock_api.get_landmark_pdf_url.return_value = None

            # Call the method
            result = self.client.get_landmark_pdf_url("LP-12345")

            # Verify result is None
            self.assertIsNone(result)


class TestConversionMethods(unittest.TestCase):
    """Tests for data conversion methods."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock CoreDataStoreAPI instance
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        # Create a DbClient instance with the mock API
        self.client = DbClient(self.mock_api)

    def test_convert_item_to_lpc_report_model_with_errors(self) -> None:
        """Test _convert_item_to_lpc_report_model with dict missing many fields."""
        # Create a dict with minimal fields to test fallback path
        minimal_dict = {
            "name": "Test Landmark",
            # Missing all other fields
        }

        # Call the method with a landmark ID context
        result = self.client._convert_item_to_lpc_report_model(minimal_dict, "LP-12345")

        # Verify result has expected values
        self.assertEqual(result.name, "Test Landmark")
        self.assertEqual(result.lpNumber, "LP-12345")  # From context
        # Other fields should be None or have default values
        self.assertIsNone(result.lpcId)
        self.assertIsNone(result.objectType)
        self.assertIsNone(result.street)


class TestBuildingMethods(unittest.TestCase):
    """Tests for building-related methods."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock CoreDataStoreAPI instance
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        # Create a DbClient instance with the mock API
        self.client = DbClient(self.mock_api)

    def test_fetch_buildings_from_client_not_hasattr(self) -> None:
        """Test _fetch_buildings_from_client when client lacks the method."""
        # Create a client with a mock API without get_landmark_buildings
        limited_mock_api = Mock(spec=[])
        limited_client = DbClient(limited_mock_api)

        # Call the method
        result = limited_client._fetch_buildings_from_client("LP-12345", 10)

        # Verify an empty list is returned
        self.assertEqual(result, [])

    def test_fetch_buildings_from_landmark_detail_invalid_response(self) -> None:
        """Test _fetch_buildings_from_landmark_detail with invalid response."""
        # Mock get_landmark_by_id to return a dict instead of LpcReportDetailResponse
        with patch.object(
            self.client, "get_landmark_by_id", return_value={"name": "Test"}
        ):
            # Call the method
            result = self.client._fetch_buildings_from_landmark_detail("LP-12345", 10)

            # Verify an empty list is returned
            self.assertEqual(result, [])

    def test_fetch_buildings_from_landmark_detail_no_landmarks_attr(self) -> None:
        """Test _fetch_buildings_from_landmark_detail with no landmarks attribute."""
        # Create a mock LpcReportDetailResponse without landmarks attribute
        mock_response = Mock(spec=LpcReportDetailResponse)
        # landmarks attribute is missing (hasattr will return False)

        with patch.object(
            self.client, "get_landmark_by_id", return_value=mock_response
        ):
            # Call the method
            result = self.client._fetch_buildings_from_landmark_detail("LP-12345", 10)

            # Verify an empty list is returned
            self.assertEqual(result, [])

    def test_fetch_buildings_from_landmark_detail_invalid_item(self) -> None:
        """Test _fetch_buildings_from_landmark_detail with invalid item in landmarks list."""
        # Create a mock LpcReportDetailResponse with invalid item in landmarks list
        mock_response = Mock(spec=LpcReportDetailResponse)
        # Set landmarks to a list containing an invalid item (not dict or LandmarkDetail)
        mock_response.landmarks = ["not a dict or LandmarkDetail"]

        with patch.object(
            self.client, "get_landmark_by_id", return_value=mock_response
        ):
            # Call the method
            result = self.client._fetch_buildings_from_landmark_detail("LP-12345", 10)

            # Verify an empty list is returned (none of the items could be converted)
            self.assertEqual(result, [])

    def test_convert_building_items_to_models_empty_list(self) -> None:
        """Test _convert_building_items_to_models with empty list."""
        # Call the method with an empty list
        result = self.client._convert_building_items_to_models([], "LP-12345")

        # Verify an empty list is returned
        self.assertEqual(result, [])

    def test_get_landmark_buildings_all_fallbacks_fail(self) -> None:
        """Test get_landmark_buildings when all fallback methods fail."""
        # Mock both fetch methods to return empty lists
        with patch.object(self.client, "_fetch_buildings_from_client", return_value=[]):
            with patch.object(
                self.client, "_fetch_buildings_from_landmark_detail", return_value=[]
            ):
                # Call the method
                result = self.client.get_landmark_buildings("LP-12345")

                # Verify an empty list is returned
                self.assertEqual(result, [])


class TestWikipediaMethods(unittest.TestCase):
    """Tests for Wikipedia-related methods."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock CoreDataStoreAPI instance with Wikipedia methods
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        self.mock_api.get_wikipedia_article_by_title = Mock()
        self.mock_api.get_wikipedia_articles = Mock()

        # Create a DbClient instance with the mock API
        self.client = DbClient(self.mock_api)

    def test_get_wikipedia_article_by_title_with_dict(self) -> None:
        """Test get_wikipedia_article_by_title with dict response."""
        # Set up mock to return a dict
        article_dict = {
            "title": "Test Article",
            "url": "https://en.wikipedia.org/wiki/Test_Article",
            "lpNumber": "LP-12345",
            "recordType": "Wikipedia",
        }
        self.mock_api.get_wikipedia_article_by_title.return_value = article_dict

        # Call the method
        result = self.client.get_wikipedia_article_by_title("Test Article")

        # Verify result is a WikipediaArticleModel
        self.assertIsNotNone(result)
        self.assertIsInstance(result, WikipediaArticleModel)
        assert (
            result is not None
        )  # Help mypy understand result can't be None after the assertion
        self.assertEqual(result.title, "Test Article")
        self.assertEqual(result.url, "https://en.wikipedia.org/wiki/Test_Article")

    def test_get_wikipedia_article_by_title_with_model(self) -> None:
        """Test get_wikipedia_article_by_title with model response."""
        # Set up mock to return a WikipediaArticleModel
        article_model = WikipediaArticleModel(
            title="Test Article",
            url="https://en.wikipedia.org/wiki/Test_Article",
            lpNumber="LP-12345",
            recordType="Wikipedia",
            id=None,  # Explicitly set id to None as it's an optional field
        )
        self.mock_api.get_wikipedia_article_by_title.return_value = article_model

        # Call the method
        result = self.client.get_wikipedia_article_by_title("Test Article")

        # Verify result is passed through
        self.assertIs(result, article_model)

    def test_get_wikipedia_article_by_title_with_none(self) -> None:
        """Test get_wikipedia_article_by_title with None response."""
        # Set up mock to return None
        self.mock_api.get_wikipedia_article_by_title.return_value = None

        # Call the method
        result = self.client.get_wikipedia_article_by_title("Test Article")

        # Verify result is None
        self.assertIsNone(result)

    def test_get_wikipedia_article_by_title_with_invalid_dict(self) -> None:
        """Test get_wikipedia_article_by_title with invalid dict response."""
        # Set up mock to return an invalid dict (missing required fields)
        self.mock_api.get_wikipedia_article_by_title.return_value = {
            "title": "Test Article"
        }

        # Call the method
        result = self.client.get_wikipedia_article_by_title("Test Article")

        # Verify result is None (conversion failed)
        self.assertIsNone(result)

    def test_get_wikipedia_article_by_title_with_unexpected_type(self) -> None:
        """Test get_wikipedia_article_by_title with unexpected response type."""
        # Set up mock to return a string
        self.mock_api.get_wikipedia_article_by_title.return_value = (
            "Not a model or dict"
        )

        # Call the method
        result = self.client.get_wikipedia_article_by_title("Test Article")

        # Verify result is None
        self.assertIsNone(result)

    def test_get_wikipedia_article_by_title_with_exception(self) -> None:
        """Test get_wikipedia_article_by_title with exception."""
        # Set up mock to raise exception
        self.mock_api.get_wikipedia_article_by_title.side_effect = Exception(
            "API error"
        )

        # Call the method
        result = self.client.get_wikipedia_article_by_title("Test Article")

        # Verify result is None
        self.assertIsNone(result)

    def test_get_wikipedia_article_by_title_client_lacks_method(self) -> None:
        """Test get_wikipedia_article_by_title when client lacks the method."""
        # Create a client with a mock API without get_wikipedia_article_by_title
        limited_mock_api = Mock(spec=[])
        limited_client = DbClient(limited_mock_api)

        # Call the method
        result = limited_client.get_wikipedia_article_by_title("Test Article")

        # Verify result is None
        self.assertIsNone(result)

    def test_get_wikipedia_articles_with_exception(self) -> None:
        """Test get_wikipedia_articles with exception handling."""
        # Set up mock to raise exception
        self.mock_api.get_wikipedia_articles.side_effect = Exception("API error")

        # Call the method
        result = self.client.get_wikipedia_articles("LP-12345")

        # Verify empty list is returned
        self.assertEqual(result, [])


class TestOtherMethods(unittest.TestCase):
    """Tests for other methods with coverage gaps."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock CoreDataStoreAPI instance
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        # Create a DbClient instance with the mock API
        self.client = DbClient(self.mock_api)

    def test_get_landmark_pluto_data(self) -> None:
        """Test get_landmark_pluto_data method."""
        # Set up mock to return pluto data
        pluto_data = [
            {
                "yearBuilt": "1900",
                "landUse": "Residential",
                "historicDistrict": "Greenwich Village",
                "zoneDist1": "R6",
            }
        ]
        self.mock_api.get_landmark_pluto_data.return_value = pluto_data

        # Call the method
        result = self.client.get_landmark_pluto_data("LP-12345")

        # Verify result
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], PlutoDataModel)
        self.assertEqual(result[0].yearBuilt, "1900")
        self.assertEqual(result[0].landUse, "Residential")
        self.assertEqual(result[0].historicDistrict, "Greenwich Village")
        self.assertEqual(result[0].zoneDist1, "R6")
        self.mock_api.get_landmark_pluto_data.assert_called_once_with("LP-12345")

    def test_get_landmark_pluto_data_client_lacks_method(self) -> None:
        """Test get_landmark_pluto_data when client lacks the method."""
        # Create a client with a mock API without get_landmark_pluto_data
        limited_mock_api = Mock(spec=[])
        limited_client = DbClient(limited_mock_api)

        # Call the method
        result = limited_client.get_landmark_pluto_data("LP-12345")

        # Verify empty list is returned
        self.assertEqual(result, [])
        # Ensure the return type is still a list (though empty)
        self.assertIsInstance(result, list)

    def test_get_total_record_count_metadata_success(self) -> None:
        """Test get_total_record_count with successful metadata retrieval."""
        # Mock _get_count_from_api_metadata to return a value
        with patch.object(
            self.client, "_get_count_from_api_metadata", return_value=100
        ):
            # Call the method
            result = self.client.get_total_record_count()

            # Verify result matches the metadata count
            self.assertEqual(result, 100)

    def test_get_total_record_count_both_methods_fail(self) -> None:
        """Test get_total_record_count when both count methods fail."""
        # Mock both methods to raise exceptions
        with patch.object(
            self.client,
            "_get_count_from_api_metadata",
            side_effect=Exception("API error"),
        ):
            with patch.object(
                self.client,
                "_estimate_count_from_pages",
                side_effect=Exception("API error"),
            ):
                # Call the method
                result = self.client.get_total_record_count()

                # Verify default value is returned
                self.assertEqual(result, 100)


if __name__ == "__main__":
    unittest.main()
