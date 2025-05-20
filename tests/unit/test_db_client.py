"""
Unit tests for the DbClient class.

This module tests the functionality of the DbClient class from nyc_landmarks.db.db_client,
focusing on core methods and helper functions.
"""

import unittest
from typing import Any, Dict, cast
from unittest.mock import Mock, patch


from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI
from nyc_landmarks.db.db_client import DbClient
from nyc_landmarks.models.landmark_models import (
    LandmarkDetail,
    LpcReportDetailResponse,
    LpcReportModel,
    LpcReportResponse,
)
from nyc_landmarks.models.wikipedia_models import WikipediaArticleModel


class TestDbClientCore(unittest.TestCase):
    """Unit tests for core methods of DbClient class."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock CoreDataStoreAPI instance
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        # Create a DbClient instance with the mock API
        self.client = DbClient(self.mock_api)

    def test_format_landmark_id(self) -> None:
        """Test _format_landmark_id method with various input formats."""
        # Test with LP prefix already present
        self.assertEqual(
            self.client._format_landmark_id("LP-12345"),
            "LP-12345",
            "Should not modify IDs that already have LP prefix"
        )

        # Test without LP prefix
        self.assertEqual(
            self.client._format_landmark_id("12345"),
            "LP-12345",
            "Should add LP prefix to numeric IDs"
        )

        # Test with short ID - should be zero-padded
        self.assertEqual(
            self.client._format_landmark_id("123"),
            "LP-00123",
            "Should zero-pad short IDs"
        )

        # Test with already zero-padded ID
        self.assertEqual(
            self.client._format_landmark_id("00123"),
            "LP-00123",
            "Should handle already zero-padded IDs correctly"
        )

    def test_parse_landmark_response_with_valid_data(self) -> None:
        """Test _parse_landmark_response with valid data."""
        # Create sample landmark data
        landmark_data = {
            "lpNumber": "LP-12345",
            "name": "Test Landmark",
            "borough": "Manhattan",
            "street": "123 Test St",
            "dateDesignated": "2020-01-01",
            "objectType": "Individual Landmark",
            "architect": "Test Architect",
            "style": "Test Style",
            "neighborhood": "Test Neighborhood",
            "zipCode": "10001",
            "photoStatus": True,
            "mapStatus": True,
            "pdfReportUrl": "https://example.com/pdf.pdf",
            "photoUrl": "https://example.com/photo.jpg"
        }

        # Test parsing with valid data
        result = self.client._parse_landmark_response(landmark_data, "LP-12345")

        # Verify result is a LpcReportDetailResponse
        self.assertIsInstance(
            result,
            LpcReportDetailResponse,
            "Should return LpcReportDetailResponse instance"
        )

        if isinstance(result, LpcReportDetailResponse):
            self.assertEqual(result.lpNumber, "LP-12345")
            self.assertEqual(result.name, "Test Landmark")
            self.assertEqual(result.borough, "Manhattan")

    def test_parse_landmark_response_with_missing_lpnumber(self) -> None:
        """Test _parse_landmark_response with missing lpNumber field."""
        # Create sample landmark data without lpNumber
        landmark_data = {
            "id": "12345",  # Has id but not lpNumber
            "name": "Test Landmark",
            "borough": "Manhattan"
        }

        # Test parsing - should use id field
        result = self.client._parse_landmark_response(landmark_data, "LP-12345")

        # Verify result has correct lpNumber
        self.assertIsInstance(
            result,
            LpcReportDetailResponse,
            "Should return LpcReportDetailResponse instance"
        )

        if isinstance(result, LpcReportDetailResponse):
            self.assertEqual(result.lpNumber, "12345")
            self.assertEqual(result.name, "Test Landmark")

    def test_parse_landmark_response_with_no_id_fields(self) -> None:
        """Test _parse_landmark_response with no id fields."""
        # Create sample landmark data without id or lpNumber
        landmark_data = {
            "name": "Test Landmark",
            "borough": "Manhattan"
        }

        # Test parsing - should use provided lpc_id
        result = self.client._parse_landmark_response(landmark_data, "LP-12345")

        # Verify result has correct lpNumber
        self.assertIsInstance(
            result,
            LpcReportDetailResponse,
            "Should return LpcReportDetailResponse instance"
        )

        if isinstance(result, LpcReportDetailResponse):
            self.assertEqual(result.lpNumber, "LP-12345")
            self.assertEqual(result.name, "Test Landmark")

    def test_parse_landmark_response_with_invalid_data(self) -> None:
        """Test _parse_landmark_response with invalid data."""
        # Test with invalid data type
        result = self.client._parse_landmark_response(cast(Dict[str, Any], None), "LP-12345")
        self.assertIsNone(result, "Should return None for non-dict input")

        # Test with data that would cause validation error
        invalid_data = {
            "lpNumber": "LP-12345",
            # Missing required fields
        }

        result = self.client._parse_landmark_response(invalid_data, "LP-12345")
        # Should return raw dict for validation failure
        self.assertIs(result, invalid_data, "Should return original dict for validation failure")

    @patch("nyc_landmarks.db.db_client.logger")
    def test_get_landmark_fallback(self, mock_logger: Mock) -> None:
        """Test _get_landmark_fallback method."""
        # Set up mock client to return a specific value
        self.mock_api.get_landmark_by_id.return_value = {"id": "LP-12345", "name": "Test"}

        # Test successful fallback
        result = self.client._get_landmark_fallback("LP-12345")
        self.assertEqual(result, {"id": "LP-12345", "name": "Test"})

        # Verify the API was called correctly
        self.mock_api.get_landmark_by_id.assert_called_once_with("LP-12345")

        # Test fallback with exception
        self.mock_api.get_landmark_by_id.reset_mock()
        self.mock_api.get_landmark_by_id.side_effect = Exception("API error")

        result = self.client._get_landmark_fallback("LP-12345")
        self.assertIsNone(result)
        mock_logger.error.assert_called()

    def test_get_landmark_by_id_success(self) -> None:
        """Test get_landmark_by_id with successful API response."""
        # Set up mock API to return a valid landmark
        landmark_data = {
            "lpNumber": "LP-12345",
            "name": "Test Landmark",
            "borough": "Manhattan"
        }
        self.mock_api.get_landmark_by_id.return_value = landmark_data

        # Call the method
        result = self.client.get_landmark_by_id("12345")

        # Verify API was called with properly formatted ID
        self.mock_api.get_landmark_by_id.assert_called_once_with("LP-12345")

        # Verify result is parsed correctly
        self.assertIsInstance(
            result,
            LpcReportDetailResponse,
            "Should return LpcReportDetailResponse instance"
        )

        if isinstance(result, LpcReportDetailResponse):
            self.assertEqual(result.lpNumber, "LP-12345")
            self.assertEqual(result.name, "Test Landmark")

    def test_get_landmark_by_id_not_found(self) -> None:
        """Test get_landmark_by_id when landmark is not found."""
        # Set up mock API to return None (not found)
        self.mock_api.get_landmark_by_id.return_value = None

        # Call the method
        result = self.client.get_landmark_by_id("12345")

        # Verify API was called and result is None
        self.mock_api.get_landmark_by_id.assert_called_once_with("LP-12345")
        self.assertIsNone(result)

    def test_get_landmark_by_id_with_api_error(self) -> None:
        """Test get_landmark_by_id with API error."""
        # Set up mock API to raise exception
        self.mock_api.get_landmark_by_id.side_effect = Exception("API error")

        # Set up mock fallback to return a value
        with patch.object(self.client, '_get_landmark_fallback', return_value={"id": "LP-12345", "name": "Test"}):
            # Call the method
            result = self.client.get_landmark_by_id("12345")

            # Verify fallback was used and returned raw dict
            self.assertEqual(result, {"id": "LP-12345", "name": "Test"})

    def test_get_landmarks_page_success(self) -> None:
        """Test get_landmarks_page with successful response."""
        # Create mock LpcReportResponse
        mock_response = LpcReportResponse(
            results=[
                LpcReportModel(
                    name="Landmark 1",
                    lpNumber="LP-00001",
                    lpcId="00001",
                    objectType="Individual Landmark",
                    architect="Test Architect",
                    style="Test Style",
                    street="123 Test St",
                    borough="Manhattan",
                    dateDesignated="2020-01-01",
                    photoStatus=True,
                    mapStatus=True,
                    neighborhood="Test Neighborhood",
                    zipCode="10001",
                    photoUrl="https://example.com/photo.jpg",
                    pdfReportUrl="https://example.com/pdf.pdf",
                ),
                LpcReportModel(
                    name="Landmark 2",
                    lpNumber="LP-00002",
                    lpcId="00002",
                    objectType="Individual Landmark",
                    architect="Test Architect 2",
                    style="Test Style 2",
                    street="456 Test Ave",
                    borough="Brooklyn",
                    dateDesignated="2020-02-02",
                    photoStatus=True,
                    mapStatus=True,
                    neighborhood="Test Neighborhood 2",
                    zipCode="11201",
                    photoUrl="https://example.com/photo2.jpg",
                    pdfReportUrl="https://example.com/pdf2.pdf",
                ),
            ],
            total=2,
            page=1,
            limit=10,
            from_=1,
            to=2,
        )

        # Mock the get_lpc_reports method to return our response
        with patch.object(self.client, 'get_lpc_reports', return_value=mock_response) as mock_get_lpc_reports:
            # Call the method
            result = self.client.get_landmarks_page(page_size=10, page=1)

            # Verify method was called correctly
            mock_get_lpc_reports.assert_called_once_with(page=1, limit=10)

            # Verify result is correct
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0].lpNumber, "LP-00001")
            self.assertEqual(result[1].lpNumber, "LP-00002")

    def test_get_landmarks_page_fallback(self) -> None:
        """Test get_landmarks_page with fallback to direct API method."""
        # Mock the get_lpc_reports method to raise an exception
        with patch.object(self.client, 'get_lpc_reports', side_effect=Exception("API error")):
            # Set up mock API to return a list of landmarks
            landmark_list = [{"lpNumber": "LP-00001", "name": "Test Landmark"}]
            self.mock_api.get_landmarks_page.return_value = landmark_list

            # Call the method
            result = self.client.get_landmarks_page(page_size=10, page=1)

            # Verify fallback API was called correctly
            self.mock_api.get_landmarks_page.assert_called_once_with(10, 1)

            # Verify result is correct
            self.assertEqual(result, landmark_list)

    def test_map_borough_id_to_name(self) -> None:
        """Test _map_borough_id_to_name with various borough IDs."""
        # Test numeric borough IDs
        self.assertEqual(self.client._map_borough_id_to_name("1"), "Manhattan")
        self.assertEqual(self.client._map_borough_id_to_name("2"), "Bronx")
        self.assertEqual(self.client._map_borough_id_to_name("3"), "Brooklyn")
        self.assertEqual(self.client._map_borough_id_to_name("4"), "Queens")
        self.assertEqual(self.client._map_borough_id_to_name("5"), "Staten Island")

        # Test letter codes
        self.assertEqual(self.client._map_borough_id_to_name("MN"), "Manhattan")
        self.assertEqual(self.client._map_borough_id_to_name("BX"), "Bronx")
        self.assertEqual(self.client._map_borough_id_to_name("BK"), "Brooklyn")
        self.assertEqual(self.client._map_borough_id_to_name("QN"), "Queens")
        self.assertEqual(self.client._map_borough_id_to_name("SI"), "Staten Island")

        # Test case insensitivity
        self.assertEqual(self.client._map_borough_id_to_name("mn"), "Manhattan")

        # Test unknown ID - should return original
        self.assertEqual(self.client._map_borough_id_to_name("unknown"), "unknown")

        # Test None input
        self.assertIsNone(self.client._map_borough_id_to_name(None))

    def test_standardize_lp_number(self) -> None:
        """Test _standardize_lp_number method with various input formats."""
        # Test with LP prefix already present
        self.assertEqual(
            self.client._standardize_lp_number("LP-12345"),
            "LP-12345",
            "Should not modify IDs that already have LP prefix"
        )

        # Test without LP prefix
        self.assertEqual(
            self.client._standardize_lp_number("12345"),
            "LP-12345",
            "Should add LP prefix to numeric IDs"
        )

        # Test with short ID - should be zero-padded
        self.assertEqual(
            self.client._standardize_lp_number("123"),
            "LP-00123",
            "Should zero-pad short IDs"
        )


class TestConversionMethods(unittest.TestCase):
    """Unit tests for data conversion methods in DbClient class."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock CoreDataStoreAPI instance
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        # Create a DbClient instance with the mock API
        self.client = DbClient(self.mock_api)

    def test_convert_item_to_lpc_report_model_from_model(self) -> None:
        """Test _convert_item_to_lpc_report_model with LpcReportModel input."""
        # Create a model instance
        model = LpcReportModel(
            name="Test Landmark",
            lpNumber="LP-12345",
            lpcId="12345",
            objectType="Individual Landmark",
            architect="Test Architect",
            style="Test Style",
            street="123 Test St",
            borough="Manhattan",
            dateDesignated="2020-01-01",
            photoStatus=True,
            mapStatus=True,
            neighborhood="Test Neighborhood",
            zipCode="10001",
            photoUrl="https://example.com/photo.jpg",
            pdfReportUrl="https://example.com/pdf.pdf",
        )

        # Convert - should return the same instance
        result = self.client._convert_item_to_lpc_report_model(model)
        self.assertIs(result, model, "Should return the same model instance")

    def test_convert_item_to_lpc_report_model_from_landmark_detail(self) -> None:
        """Test _convert_item_to_lpc_report_model with LandmarkDetail input."""
        # Create a LandmarkDetail instance
        detail = LandmarkDetail(
            lpNumber="LP-12345",
            name="Test Landmark",
            designatedAddress="123 Test St",
            boroughId="1",
            objectType="Individual Landmark",
            designatedDate="2020-01-01",
            historicDistrict="Test District",
            street="123 Test St",
        )

        # Convert
        result = self.client._convert_item_to_lpc_report_model(detail)

        # Verify conversion
        self.assertIsInstance(result, LpcReportModel)
        self.assertEqual(result.lpNumber, "LP-12345")
        self.assertEqual(result.name, "Test Landmark")
        self.assertEqual(result.street, "123 Test St")
        self.assertEqual(result.borough, "Manhattan")
        self.assertEqual(result.objectType, "Individual Landmark")
        self.assertEqual(result.dateDesignated, "2020-01-01")
        self.assertEqual(result.neighborhood, "Test District")

    def test_convert_item_to_lpc_report_model_from_dict(self) -> None:
        """Test _convert_item_to_lpc_report_model with dict input."""
        # Create a dict
        data = {
            "lpNumber": "LP-12345",
            "name": "Test Landmark",
            "street": "123 Test St",
            "borough": "Manhattan",
            "objectType": "Individual Landmark",
            "dateDesignated": "2020-01-01",
            "architect": "Test Architect",
            "style": "Test Style",
            "neighborhood": "Test Neighborhood",
            "zipCode": "10001",
            "photoStatus": True,
            "mapStatus": True,
            "photoUrl": "https://example.com/photo.jpg",
            "pdfReportUrl": "https://example.com/pdf.pdf",
            "lpcId": "12345",
        }

        # Convert
        result = self.client._convert_item_to_lpc_report_model(data)

        # Verify conversion
        self.assertIsInstance(result, LpcReportModel)
        self.assertEqual(result.lpNumber, "LP-12345")
        self.assertEqual(result.name, "Test Landmark")
        self.assertEqual(result.street, "123 Test St")
        self.assertEqual(result.borough, "Manhattan")
        self.assertEqual(result.objectType, "Individual Landmark")

    @patch("nyc_landmarks.db.db_client.logger")
    def test_convert_item_to_lpc_report_model_from_invalid_dict(self, mock_logger: Mock) -> None:
        """Test _convert_item_to_lpc_report_model with dict missing required fields."""
        # Create an invalid dict (missing required fields)
        invalid_data = {
            "name": "Test Landmark",
            "street": "123 Test St",
            # Missing lpNumber and other required fields
        }

        # Convert with context LP number
        result = self.client._convert_item_to_lpc_report_model(invalid_data, "LP-12345")

        # Verify fallback behavior and logging
        mock_logger.warning.assert_called()  # Check that warning was logged
        self.assertIsInstance(result, LpcReportModel)
        self.assertEqual(result.lpNumber, "LP-12345")  # Should use context LP number
        self.assertEqual(result.name, "Test Landmark")
        self.assertEqual(result.street, "123 Test St")


class TestWikipediaIntegration(unittest.TestCase):
    """Unit tests for Wikipedia-related methods in DbClient class."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock CoreDataStoreAPI instance
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        # Create a DbClient instance with the mock API
        self.client = DbClient(self.mock_api)

    def test_get_wikipedia_articles(self) -> None:
        """Test get_wikipedia_articles method."""
        # Create a mock list of Wikipedia articles
        mock_articles = [
            WikipediaArticleModel(
                title="Test Article",
                url="https://en.wikipedia.org/wiki/Test_Article",
                lpNumber="LP-12345",
                recordType="Wikipedia",
            )
        ]

        # Set up mock API to return articles
        self.mock_api.get_wikipedia_articles.return_value = mock_articles

        # Call the method
        result = self.client.get_wikipedia_articles("LP-12345")

        # Verify API was called correctly
        self.mock_api.get_wikipedia_articles.assert_called_once_with("LP-12345")

        # Verify result
        self.assertEqual(result, mock_articles)

    @patch("nyc_landmarks.db.db_client.logger")
    def test_get_wikipedia_articles_with_error(self, mock_logger: Mock) -> None:
        """Test get_wikipedia_articles when API raises an error."""
        # Set up mock API to raise exception
        self.mock_api.get_wikipedia_articles.side_effect = Exception("API error")

        # Call the method
        result = self.client.get_wikipedia_articles("LP-12345")

        # Verify empty list is returned and error is logged
        self.assertEqual(result, [])
        mock_logger.error.assert_called()

    def test_get_wikipedia_articles_client_lacks_method(self) -> None:
        """Test get_wikipedia_articles when client doesn't have the method."""
        # Set up a mock that doesn't have get_wikipedia_articles method
        limited_mock_api = Mock()
        limited_mock_api.get_wikipedia_articles = None
        limited_client = DbClient(limited_mock_api)

        # Call the method - should return empty list
        result = limited_client.get_wikipedia_articles("LP-12345")
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
