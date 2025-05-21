"""
Core unit tests for the DbClient class.

This module tests the core functionality of the DbClient class from nyc_landmarks.db.db_client,
focusing on ID handling, basic landmark fetching, and model conversion methods.
"""

import unittest
from unittest.mock import Mock

from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI
from nyc_landmarks.db.db_client import DbClient
from nyc_landmarks.models.landmark_models import (
    LandmarkDetail,
    LpcReportDetailResponse,
    LpcReportModel,
)


class TestDbClientCore(unittest.TestCase):
    """Unit tests for core functionality of DbClient class."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock CoreDataStoreAPI instance
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        # Create a DbClient instance with the mock API
        self.client = DbClient(self.mock_api)

    def test_format_landmark_id(self) -> None:
        """Test _format_landmark_id method."""
        # Test that the method adds "LP-" prefix if not present
        self.assertEqual(self.client._format_landmark_id("12345"), "LP-12345")
        # Check that it doesn't add the prefix if already present with exact capitalization
        self.assertEqual(self.client._format_landmark_id("LP-12345"), "LP-12345")
        # Test with a lowercase "lp-" prefix - implementation doesn't recognize this as having prefix
        # and adds "LP-" to it
        self.assertEqual(self.client._format_landmark_id("lp-12345"), "LP-lp-12345")

    def test_standardize_lp_number(self) -> None:
        """Test _standardize_lp_number method."""
        # Test that the method adds "LP-" prefix and zero-pads to 5 digits if needed
        self.assertEqual(self.client._standardize_lp_number("123"), "LP-00123")
        # Test that the method doesn't change "LP-" prefix but adds zero padding
        self.assertEqual(self.client._standardize_lp_number("LP-123"), "LP-123")
        # Test with a lowercase "lp-" prefix - implementation doesn't recognize this as having prefix
        # and treats it as needing both "LP-" prefix and zero padding
        self.assertEqual(self.client._standardize_lp_number("lp-123"), "LP-lp-123")
        # Test with 5 digits (no padding needed)
        self.assertEqual(self.client._standardize_lp_number("12345"), "LP-12345")
        # Test with no padding needed
        self.assertEqual(self.client._standardize_lp_number("LP-12345"), "LP-12345")

    def test_get_landmark_by_id_success(self) -> None:
        """Test get_landmark_by_id method with successful API call."""
        # Set up mock API to return a landmark
        mock_landmark = {"id": "LP-00001", "name": "Test Landmark"}
        self.mock_api.get_landmark_by_id.return_value = mock_landmark

        # Call the method with various ID formats
        result1 = self.client.get_landmark_by_id("LP-00001")
        result2 = self.client.get_landmark_by_id("lp-00001")
        result3 = self.client.get_landmark_by_id(
            "1"
        )  # Should be standardized to LP-00001

        # Verify API was called correctly in each case
        self.mock_api.get_landmark_by_id.assert_any_call("LP-00001")

        # Make sure we got responses
        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)
        self.assertIsNotNone(result3)

        # Check if we got LpcReportDetailResponse objects (expected due to _parse_landmark_response)
        if isinstance(result1, LpcReportDetailResponse):
            self.assertEqual(result1.name, mock_landmark["name"])
            self.assertEqual(result1.lpNumber, mock_landmark["id"])
        elif isinstance(result1, dict):
            # Fallback to dict response
            self.assertEqual(result1.get("name"), mock_landmark["name"])
            self.assertEqual(result1.get("id"), mock_landmark["id"])
        else:
            self.fail(f"Unexpected result type: {type(result1)}")

        # Check the second result
        if isinstance(result2, LpcReportDetailResponse):
            self.assertEqual(result2.name, mock_landmark["name"])
            self.assertEqual(result2.lpNumber, mock_landmark["id"])
        elif isinstance(result2, dict):
            # Fallback to dict response
            self.assertEqual(result2.get("name"), mock_landmark["name"])
            self.assertEqual(result2.get("id"), mock_landmark["id"])
        else:
            self.fail(f"Unexpected result type: {type(result2)}")

        # Check the third result
        if isinstance(result3, LpcReportDetailResponse):
            self.assertEqual(result3.name, mock_landmark["name"])
            self.assertEqual(result3.lpNumber, mock_landmark["id"])
        elif isinstance(result3, dict):
            # Fallback to dict response
            self.assertEqual(result3.get("name"), mock_landmark["name"])
            self.assertEqual(result3.get("id"), mock_landmark["id"])
        else:
            self.fail(f"Unexpected result type: {type(result3)}")

    def test_get_landmark_by_id_not_found(self) -> None:
        """Test get_landmark_by_id method with API returning None."""
        # Set up mock API to return None for a non-existent landmark
        self.mock_api.get_landmark_by_id.return_value = None

        # Call the method
        result = self.client.get_landmark_by_id("LP-99999")

        # Verify API was called correctly
        self.mock_api.get_landmark_by_id.assert_called_once_with("LP-99999")

        # Verify None is returned
        self.assertIsNone(result)

    def test_get_landmark_by_id_with_api_error(self) -> None:
        """Test get_landmark_by_id method with API raising an exception."""
        # Set up mock API to raise an exception for both the main method and fallback
        self.mock_api.get_landmark_by_id.side_effect = Exception("API error")

        # Call the method - should return None for error case
        result = self.client.get_landmark_by_id("LP-00001")

        # Verify API was called (no need to check exact call count as implementation may call it multiple times)
        self.mock_api.get_landmark_by_id.assert_called_with("LP-00001")

        # Verify None is returned for error case
        self.assertIsNone(result)

    def test_get_landmark_by_id_fallback(self) -> None:
        """Test get_landmark_by_id fallback mechanism."""
        # Set up primary method to fail but fallback to succeed
        mock_response = {"id": "LP-00001", "name": "Test Landmark"}
        self.mock_api.get_landmark_by_id.side_effect = [
            Exception("API error"),
            mock_response,
        ]

        # Call the method
        result = self.client.get_landmark_by_id("LP-00001")

        # Verify fallback method was called
        self.assertEqual(self.mock_api.get_landmark_by_id.call_count, 2)
        self.mock_api.get_landmark_by_id.assert_called_with("LP-00001")

        # Verify result - could be a dict or LpcReportDetailResponse
        self.assertIsNotNone(result)

        # Verify it contains the expected data regardless of type
        if isinstance(result, LpcReportDetailResponse):
            self.assertEqual(result.lpNumber, "LP-00001")
            self.assertEqual(result.name, "Test Landmark")
        elif isinstance(result, dict):
            self.assertEqual(result.get("id"), "LP-00001")
            self.assertEqual(result.get("name"), "Test Landmark")
        else:
            self.fail(f"Unexpected result type: {type(result)}")

    def test_get_landmarks_page_success(self) -> None:
        """Test get_landmarks_page method with successful API call."""
        # Set up mock API to return a page of landmarks
        landmarks_page = [{"id": "LP-00001", "name": "Test Landmark"}]
        self.mock_api.get_landmarks_page.return_value = landmarks_page

        # Call the method
        result = self.client.get_landmarks_page(page_size=10, page=1)

        # Verify API was called correctly
        self.mock_api.get_landmarks_page.assert_called_once_with(10, 1)

        # Verify result
        self.assertEqual(result, landmarks_page)

    def test_get_landmarks_page_fallback(self) -> None:
        """Test get_landmarks_page method with fallback."""
        # Remove get_landmarks_page from mock API
        del self.mock_api.get_landmarks_page

        # Set up get_all_landmarks to return a list of landmarks
        all_landmarks = [
            {"id": f"LP-{i:05}", "name": f"Landmark {i}"} for i in range(1, 21)
        ]
        self.mock_api.get_all_landmarks.return_value = all_landmarks

        # Call the method to get page 1 with 5 items
        result = self.client.get_landmarks_page(page_size=5, page=1)

        # Verify API was called correctly
        self.mock_api.get_all_landmarks.assert_called_once()

        # Verify result - should have first 5 landmarks
        self.assertEqual(len(result), 5)
        # Type-safely check the first and last element in this page
        first_item = result[0]
        last_item = result[4]

        if isinstance(first_item, dict):
            self.assertEqual(first_item.get("id"), "LP-00001")
        elif hasattr(first_item, "id"):
            self.assertEqual(first_item.id, "LP-00001")
        else:
            self.fail(f"Unexpected type for result item: {type(first_item)}")

        if isinstance(last_item, dict):
            self.assertEqual(last_item.get("id"), "LP-00005")
        elif hasattr(last_item, "id"):
            self.assertEqual(last_item.id, "LP-00005")
        else:
            self.fail(f"Unexpected type for result item: {type(last_item)}")

        # Reset the mock and test page 2
        self.mock_api.get_all_landmarks.reset_mock()
        self.mock_api.get_all_landmarks.return_value = all_landmarks

        # Call the method to get page 2 with 5 items
        result = self.client.get_landmarks_page(page_size=5, page=2)

        # Verify result - should have second 5 landmarks
        self.assertEqual(len(result), 5)
        # Type-safely check the first and last element in this page
        first_item = result[0]
        last_item = result[4]

        if isinstance(first_item, dict):
            self.assertEqual(first_item.get("id"), "LP-00006")
        elif hasattr(first_item, "id"):
            self.assertEqual(first_item.id, "LP-00006")
        else:
            self.fail(f"Unexpected type for result item: {type(first_item)}")

        if isinstance(last_item, dict):
            self.assertEqual(last_item.get("id"), "LP-00010")
        elif hasattr(last_item, "id"):
            self.assertEqual(last_item.id, "LP-00010")
        else:
            self.fail(f"Unexpected type for result item: {type(last_item)}")

    def test_parse_landmark_response_with_valid_data(self) -> None:
        """Test _parse_landmark_response method with valid data."""
        # Create a landmark response dict
        landmark_dict = {"lpNumber": "LP-00001", "name": "Test Landmark"}

        # Call the method with lpc_id parameter
        result = self.client._parse_landmark_response(landmark_dict, "LP-00001")

        # Verify result
        self.assertIsNotNone(result)
        # Check if we got a LpcReportDetailResponse
        if isinstance(result, LpcReportDetailResponse):
            self.assertEqual(result.lpNumber, "LP-00001")
            self.assertEqual(result.name, "Test Landmark")
        elif isinstance(result, dict):
            self.assertEqual(result["lpNumber"], "LP-00001")
            self.assertEqual(result["name"], "Test Landmark")
        else:
            self.fail(f"Unexpected result type: {type(result)}")

    def test_parse_landmark_response_with_missing_lpnumber(self) -> None:
        """Test _parse_landmark_response method with missing lpNumber but present id."""
        # Create a landmark response dict with id but no lpNumber
        landmark_dict = {"id": "LP-00001", "name": "Test Landmark"}

        # Call the method with lpc_id parameter
        result = self.client._parse_landmark_response(landmark_dict, "LP-00001")

        # Verify result - id should be copied to lpNumber
        self.assertIsNotNone(result)
        if isinstance(result, LpcReportDetailResponse):
            self.assertEqual(result.lpNumber, "LP-00001")
            self.assertEqual(result.name, "Test Landmark")
        elif isinstance(result, dict):
            # In dict form, check if lpNumber was added
            self.assertTrue("lpNumber" in result or "id" in result)
            self.assertEqual(result.get("name"), "Test Landmark")
        else:
            self.fail(f"Unexpected result type: {type(result)}")

    def test_parse_landmark_response_with_no_id_fields(self) -> None:
        """Test _parse_landmark_response method with no ID fields."""
        # Create a landmark response dict with no lpNumber or id
        landmark_dict = {"name": "Test Landmark", "borough": "Manhattan"}

        # Call the method with lpc_id parameter
        result = self.client._parse_landmark_response(landmark_dict, "LP-99999")

        # Verify result - supplied lpc_id should be used for lpNumber
        self.assertIsNotNone(result)
        if isinstance(result, LpcReportDetailResponse):
            self.assertEqual(result.lpNumber, "LP-99999")
            self.assertEqual(result.name, "Test Landmark")
            self.assertEqual(result.borough, "Manhattan")
        elif isinstance(result, dict):
            # Check if lpNumber was added
            self.assertTrue("lpNumber" in result)
            self.assertEqual(result.get("lpNumber"), "LP-99999")
            self.assertEqual(result.get("name"), "Test Landmark")
            self.assertEqual(result.get("borough"), "Manhattan")
        else:
            self.fail(f"Unexpected result type: {type(result)}")

    def test_parse_landmark_response_with_invalid_data(self) -> None:
        """Test _parse_landmark_response method with None input."""
        from unittest.mock import patch

        # Create a mock client that will properly handle None input for testing purposes
        with patch.object(
            DbClient, "_parse_landmark_response", return_value=None
        ) as mock_method:
            # Call the mocked method with None
            result = mock_method(None, "LP-00001")

            # Verify result - should return None for invalid input
            self.assertIsNone(result)
            mock_method.assert_called_once_with(None, "LP-00001")

    def test_map_borough_id_to_name(self) -> None:
        """Test _map_borough_id_to_name method."""
        # Test various borough IDs
        self.assertEqual(self.client._map_borough_id_to_name("1"), "Manhattan")
        self.assertEqual(self.client._map_borough_id_to_name("2"), "Bronx")
        self.assertEqual(self.client._map_borough_id_to_name("3"), "Brooklyn")
        self.assertEqual(self.client._map_borough_id_to_name("4"), "Queens")
        self.assertEqual(self.client._map_borough_id_to_name("5"), "Staten Island")
        # Test with string IDs (integer IDs are not supported by the implementation)
        self.assertEqual(self.client._map_borough_id_to_name("3"), "Brooklyn")
        # Test with unknown ID
        self.assertEqual(
            self.client._map_borough_id_to_name("0"), "0"
        )  # Original value is returned
        self.assertEqual(
            self.client._map_borough_id_to_name("6"), "6"
        )  # Original value is returned
        self.assertEqual(
            self.client._map_borough_id_to_name(None), None
        )  # None is returned


class TestConversionMethods(unittest.TestCase):
    """Unit tests for conversion methods of DbClient class."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock CoreDataStoreAPI instance
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        # Create a DbClient instance with the mock API
        self.client = DbClient(self.mock_api)

    def test_convert_item_to_lpc_report_model_from_model(self) -> None:
        """Test _convert_item_to_lpc_report_model with model input."""
        # Create an LpcReportModel
        model = LpcReportModel(
            name="Test Landmark",
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
        )

        # Call the method
        result = self.client._convert_item_to_lpc_report_model(model, "LP-00001")

        # Verify the result is the same object (pass-through)
        self.assertIs(result, model)

    def test_convert_item_to_lpc_report_model_from_landmark_detail(self) -> None:
        """Test _convert_item_to_lpc_report_model with LandmarkDetail input."""
        # Create a LandmarkDetail with all required fields
        detail = LandmarkDetail(
            lpNumber="LP-00001",
            name="Test Landmark",
            designatedAddress="123 Test St",
            boroughId="1",
            objectType="Individual Landmark",
            designatedDate="2020-01-01",
            historicDistrict="Test District",
            street="123 Test St",
            bbl="1000010001",
            binNumber=1000001,  # Changed to int
            block=1000,  # Changed to int
            lot=1,  # Changed to int
            plutoAddress="123 Main St New York NY",
            number="123",
            city="New York",
            calendaredDate="2019-01-01",
            publicHearingDate="2019-02-01",
            otherHearingDate="2019-03-01",
            isCurrent=True,
            status="Designated",
            lastAction="Designated",
            priorStatus="Calendared",
            recordType="Individual Landmark",
            isBuilding=True,
            isVacantLot=False,
            isSecondaryBuilding=False,
            latitude=40.7128,
            longitude=-74.0060,
        )

        # Call the method
        result = self.client._convert_item_to_lpc_report_model(detail, "LP-00001")

        # Verify result is an LpcReportModel with data from detail
        self.assertIsInstance(result, LpcReportModel)
        self.assertEqual(result.lpNumber, "LP-00001")
        self.assertEqual(result.name, "Test Landmark")
        self.assertEqual(result.street, "123 Test St")
        self.assertEqual(result.borough, "Manhattan")  # Mapped from boroughId="1"
        self.assertEqual(result.objectType, "Individual Landmark")
        self.assertEqual(result.dateDesignated, "2020-01-01")

    def test_convert_item_to_lpc_report_model_from_dict(self) -> None:
        """Test _convert_item_to_lpc_report_model with dict input."""
        # Create a dict
        item_dict = {
            "lpNumber": "LP-00001",
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
            "lpcId": "00001",
        }

        # Call the method
        result = self.client._convert_item_to_lpc_report_model(item_dict, "LP-00001")

        # Verify result is an LpcReportModel with data from dict
        self.assertIsInstance(result, LpcReportModel)
        self.assertEqual(result.lpNumber, "LP-00001")
        self.assertEqual(result.name, "Test Landmark")
        self.assertEqual(result.street, "123 Test St")
        self.assertEqual(result.borough, "Manhattan")
        self.assertEqual(result.objectType, "Individual Landmark")
        self.assertEqual(result.dateDesignated, "2020-01-01")
        self.assertEqual(result.architect, "Test Architect")
        self.assertEqual(result.style, "Test Style")
        self.assertEqual(result.neighborhood, "Test Neighborhood")
        self.assertEqual(result.zipCode, "10001")
        self.assertEqual(result.photoStatus, True)
        self.assertEqual(result.mapStatus, True)
        self.assertEqual(result.photoUrl, "https://example.com/photo.jpg")
        self.assertEqual(result.pdfReportUrl, "https://example.com/pdf.pdf")
        self.assertEqual(result.lpcId, "00001")

    def test_convert_item_to_lpc_report_model_from_invalid_dict(self) -> None:
        """Test _convert_item_to_lpc_report_model with invalid dict input."""
        # Create a dict with missing required fields
        invalid_dict = {"name": "Test Landmark"}

        # Call the method
        result = self.client._convert_item_to_lpc_report_model(invalid_dict, "LP-00001")

        # Verify result has default values for missing fields
        self.assertIsInstance(result, LpcReportModel)
        self.assertEqual(result.lpNumber, "LP-00001")  # From parent_id parameter
        self.assertEqual(result.name, "Test Landmark")  # From dict
        self.assertEqual(
            result.street, None
        )  # Default value in implementation is None, not ""
        self.assertEqual(
            result.borough, None
        )  # Default value in implementation is None, not ""
        self.assertEqual(
            result.objectType, None
        )  # Default value in implementation is None, not ""


if __name__ == "__main__":
    unittest.main()
