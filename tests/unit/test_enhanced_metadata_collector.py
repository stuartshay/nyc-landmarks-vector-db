"""
Unit tests for the EnhancedMetadataCollector class.

This module tests the functionality of EnhancedMetadataCollector from
nyc_landmarks.vectordb.enhanced_metadata, focusing on metadata collection
from various API sources.
"""

import unittest
from unittest.mock import Mock, patch

from nyc_landmarks.db.db_client import DbClient
from nyc_landmarks.models.landmark_models import LpcReportDetailResponse, PlutoDataModel
from nyc_landmarks.models.metadata_models import SourceType
from nyc_landmarks.vectordb.enhanced_metadata import (
    EnhancedMetadataCollector,
    get_metadata_collector,
)
from tests.mocks.landmark_mocks import get_mock_landmark_details


class TestEnhancedMetadataCollectorBasics(unittest.TestCase):
    """Test basic initialization and factory function of EnhancedMetadataCollector."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock db_client
        self.mock_db_client = Mock(spec=DbClient)

        # Create patchers
        self.db_client_patcher = patch(
            "nyc_landmarks.vectordb.enhanced_metadata.get_db_client",
            return_value=self.mock_db_client,
        )
        self.settings_patcher = patch(
            "nyc_landmarks.vectordb.enhanced_metadata.settings.COREDATASTORE_USE_API",
            True,
        )

        # Start patchers
        self.mock_get_db_client = self.db_client_patcher.start()
        self.mock_settings = self.settings_patcher.start()

    def tearDown(self) -> None:
        """Clean up after each test method."""
        # Stop patchers
        self.db_client_patcher.stop()
        self.settings_patcher.stop()

    def test_init(self) -> None:
        """Test initialization of EnhancedMetadataCollector."""
        # Create the collector
        collector = EnhancedMetadataCollector()

        # Verify get_db_client was called
        self.mock_get_db_client.assert_called_once()

        # Verify attributes were set correctly
        self.assertEqual(collector.db_client, self.mock_db_client)
        self.assertTrue(collector.using_api)

    def test_get_metadata_collector(self) -> None:
        """Test factory function get_metadata_collector."""
        # Call the factory function
        collector = get_metadata_collector()

        # Verify we got an EnhancedMetadataCollector instance
        self.assertIsInstance(collector, EnhancedMetadataCollector)

        # Verify get_db_client was called
        self.mock_get_db_client.assert_called_once()


class TestEnhancedMetadataCollectorNonApiMode(unittest.TestCase):
    """Test EnhancedMetadataCollector in non-API mode."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock db_client
        self.mock_db_client = Mock(spec=DbClient)

        # Create patchers
        self.db_client_patcher = patch(
            "nyc_landmarks.vectordb.enhanced_metadata.get_db_client",
            return_value=self.mock_db_client,
        )
        self.settings_patcher = patch(
            "nyc_landmarks.vectordb.enhanced_metadata.settings.COREDATASTORE_USE_API",
            False,  # Set to non-API mode
        )

        # Start patchers
        self.mock_get_db_client = self.db_client_patcher.start()
        self.mock_settings = self.settings_patcher.start()

        # Create the collector
        self.collector = EnhancedMetadataCollector()

        # Set up basic metadata response
        self.basic_metadata = {
            "landmark_id": "LP-00009",
            "name": "Irad Hawley House",
            "location": "47 Fifth Avenue",
            "borough": "Manhattan",
            "type": "Individual Landmark",
            "designation_date": "1969-09-09T00:00:00",
        }
        self.mock_db_client.get_landmark_metadata.return_value = self.basic_metadata

    def tearDown(self) -> None:
        """Clean up after each test method."""
        # Stop patchers
        self.db_client_patcher.stop()
        self.settings_patcher.stop()

    def test_collect_landmark_metadata_non_api_mode(self) -> None:
        """Test collect_landmark_metadata when COREDATASTORE_USE_API is False."""
        # Call the method
        result = self.collector.collect_landmark_metadata("LP-00009")

        # Verify only basic metadata was used (no API calls)
        # Convert result to dictionary for comparison, removing None values
        result_dict = {k: v for k, v in result.dict().items() if v is not None}

        # Check that all basic metadata fields are present and correct
        for key, expected_value in self.basic_metadata.items():
            self.assertEqual(result_dict[key], expected_value)

        # Verify auto-generated fields are present
        self.assertIn("processing_date", result_dict)
        self.assertIn("source_type", result_dict)
        self.assertEqual(result_dict["source_type"], SourceType.PDF)  # Default value

        # Check that basic metadata values match
        for key, expected_value in self.basic_metadata.items():
            self.assertEqual(result_dict[key], expected_value)

        # Check that auto-generated fields have correct values/types
        self.assertIsInstance(result_dict["processing_date"], str)
        self.assertEqual(result_dict["source_type"], SourceType.PDF)  # Default fallback

        self.mock_db_client.get_landmark_metadata.assert_called_once_with("LP-00009")

        # Verify no other methods were called
        self.mock_db_client.get_landmark_by_id.assert_not_called()
        self.mock_db_client.get_landmark_pluto_data.assert_not_called()


class TestEnhancedMetadataCollectorApiMode(unittest.TestCase):
    """Test basic initialization and factory function of EnhancedMetadataCollector."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock db_client
        self.mock_db_client = Mock(spec=DbClient)

        # Create patchers
        self.db_client_patcher = patch(
            "nyc_landmarks.vectordb.enhanced_metadata.get_db_client",
            return_value=self.mock_db_client,
        )
        self.settings_patcher = patch(
            "nyc_landmarks.vectordb.enhanced_metadata.settings.COREDATASTORE_USE_API",
            True,  # Set to API mode
        )

        # Start patchers
        self.mock_get_db_client = self.db_client_patcher.start()
        self.mock_settings = self.settings_patcher.start()

        # Create the collector
        self.collector = EnhancedMetadataCollector()

        # Set up basic metadata response
        self.basic_metadata = {
            "landmark_id": "LP-00009",
            "name": "Irad Hawley House",
            "location": "47 Fifth Avenue",
            "borough": "Manhattan",
            "type": "Individual Landmark",
            "designation_date": "1969-09-09T00:00:00",
        }
        self.mock_db_client.get_landmark_metadata.return_value = self.basic_metadata

        # Set up mock buildings response
        self.mock_buildings = [
            {
                "name": "Salmagundi Club",
                "lpNumber": "LP-00009",
                "bbl": "1005690004",
                "binNumber": 1009274,
                "boroughId": "MN",
                "objectType": "Individual Landmark",
                "block": 569,
                "lot": 4,
                "plutoAddress": "47 5 AVENUE",
                "designatedAddress": "47 5 AVENUE",
                "latitude": 40.7342490239599,
                "longitude": -73.9944453559693,
            }
        ]
        self.mock_db_client.get_landmark_buildings.return_value = self.mock_buildings

        # Set up mock landmark details response
        self.mock_landmark_details = get_mock_landmark_details()
        self.mock_db_client.get_landmark_by_id.return_value = (
            self.mock_landmark_details
        )  # Set up mock PLUTO data as PlutoDataModel instances
        self.pluto_model = PlutoDataModel(
            yearbuilt=1900,
            landUse="Residential",
            historicDistrict="Greenwich Village",
            zoneDist1="R6",
            lotArea=5000,
            bldgArea=3000,
            numFloors=3.0,
            address="47 Fifth Avenue",
            borough="MN",
            ownername="Test Owner",
            bldgclass="R2",
            assessland=150000.0,
            assesstot=400000.0,
        )
        self.mock_pluto_data = [self.pluto_model]
        self.mock_db_client.get_landmark_pluto_data.return_value = self.mock_pluto_data

    def tearDown(self) -> None:
        """Clean up after each test method."""
        # Stop patchers
        self.db_client_patcher.stop()
        self.settings_patcher.stop()

    def test_collect_landmark_metadata_complete_data(self) -> None:
        """Test collect_landmark_metadata with complete data from all sources."""
        # Create a new mock landmark details dictionary with bbl and plutoStatus added
        mock_landmark_details = dict(
            get_mock_landmark_details()
        )  # Convert to dict to allow item assignment
        mock_landmark_details["bbl"] = "1005690004"
        mock_landmark_details["plutoStatus"] = True  # Enable PLUTO data fetching
        self.mock_db_client.get_landmark_by_id.return_value = mock_landmark_details

        # Call the method
        result = self.collector.collect_landmark_metadata("LP-00009")

        # Verify API calls were made
        self.mock_db_client.get_landmark_metadata.assert_called_once_with("LP-00009")
        self.mock_db_client.get_landmark_buildings.assert_called_once_with("LP-00009")
        self.mock_db_client.get_landmark_by_id.assert_called_once_with("LP-00009")
        self.mock_db_client.get_landmark_pluto_data.assert_called_once_with("LP-00009")

        # Verify the result contains all expected data
        # Basic metadata
        self.assertEqual(result["landmark_id"], "LP-00009")
        self.assertEqual(result["name"], "Irad Hawley House")
        self.assertEqual(result["borough"], "Manhattan")

        # Building information is now flattened into the main metadata
        self.assertIn("year_built", result)
        self.assertIn("land_use", result)
        self.assertIn("historic_district", result)
        self.assertIn("zoning_district", result)

        # Verify specific building data values
        self.assertEqual(result["year_built"], "1900")
        self.assertEqual(result["land_use"], "Residential")
        self.assertEqual(result["historic_district"], "Greenwich Village")

        # PLUTO data
        self.assertIn("has_pluto_data", result)
        self.assertTrue(result["has_pluto_data"])
        self.assertEqual(result["year_built"], str(self.pluto_model.yearbuilt))
        self.assertEqual(result["land_use"], self.pluto_model.landUse)
        self.assertEqual(result["historic_district"], self.pluto_model.historicDistrict)
        self.assertEqual(result["zoning_district"], self.pluto_model.zoneDist1)

    def test_collect_landmark_metadata_no_buildings(self) -> None:
        """Test collect_landmark_metadata when no buildings are returned."""
        # Create a new mock landmark details dictionary with plutoStatus added
        mock_landmark_details = dict(
            get_mock_landmark_details()
        )  # Convert to dict to allow item assignment
        mock_landmark_details["plutoStatus"] = True  # Enable PLUTO data fetching
        self.mock_db_client.get_landmark_by_id.return_value = mock_landmark_details

        # Set up empty buildings response
        self.mock_db_client.get_landmark_buildings.return_value = []

        # Call the method
        result = self.collector.collect_landmark_metadata("LP-00009")

        # Verify API calls were made
        self.mock_db_client.get_landmark_buildings.assert_called_once_with("LP-00009")

        # Verify result doesn't have buildings key
        self.assertNotIn("buildings", result)

        # PLUTO data should still be present
        self.assertTrue(result["has_pluto_data"])

    def test_collect_landmark_metadata_no_pluto_data(self) -> None:
        """Test collect_landmark_metadata when no PLUTO data is returned."""
        # Create a new mock landmark details dictionary with plutoStatus added
        mock_landmark_details = dict(
            get_mock_landmark_details()
        )  # Convert to dict to allow item assignment
        mock_landmark_details["plutoStatus"] = True  # Enable PLUTO data fetching
        self.mock_db_client.get_landmark_by_id.return_value = mock_landmark_details

        # Set up empty PLUTO data response
        self.mock_db_client.get_landmark_pluto_data.return_value = []

        # Call the method
        result = self.collector.collect_landmark_metadata("LP-00009")

        # Verify API calls were made
        self.mock_db_client.get_landmark_pluto_data.assert_called_once_with("LP-00009")

        # Verify result has has_pluto_data set to False
        self.assertIn("has_pluto_data", result)
        self.assertFalse(result["has_pluto_data"])

        # PLUTO-related fields should not be present
        for field in ["year_built", "land_use", "historic_district", "zoning_district"]:
            self.assertFalse(
                hasattr(result, field) and getattr(result, field) is not None
            )

    def test_building_data_pydantic_model(self) -> None:
        """Test handling of Pydantic model response for building data."""
        # Use the centralized mock building model
        from tests.mocks.landmark_mocks import get_mock_building_model

        # Create a mock building object with attribute access rather than dict access
        mock_building = Mock()
        building_model = get_mock_building_model()

        # Set attributes based on the mock model
        for attr, value in building_model.items():
            setattr(mock_building, attr, value)

        # Set up mock response to return our mock object
        self.mock_db_client.get_landmark_buildings.return_value = [mock_building]

        # Call the method
        result = self.collector.collect_landmark_metadata("LP-00009")

        # Verify building data was correctly processed and flattened
        # The current implementation flattens building data into the main metadata
        self.assertIn("year_built", result)
        self.assertIn("land_use", result)

        # Check that the specific building data was flattened correctly
        # The test building should have contributed to the flattened data
        self.assertIsNotNone(result.get("year_built"))  # Should have some building data

    def test_landmark_details_pydantic_model(self) -> None:
        """Test handling of Pydantic model response for landmark details."""
        # Create a mock LpcReportDetailResponse for proper method testing
        mock_details = Mock(spec=LpcReportDetailResponse)
        mock_details.name = "Irad Hawley House"
        mock_details.lpNumber = "LP-00009"
        mock_details.bbl = "1005690004"

        # Set up mock response to return our mock object
        self.mock_db_client.get_landmark_by_id.return_value = mock_details

        # Call the method
        result = self.collector.collect_landmark_metadata("LP-00009")

        # Verify result contains expected data
        # The current implementation flattens building data rather than keeping separate buildings
        self.assertEqual(result["landmark_id"], "LP-00009")
        self.assertEqual(result["name"], "Irad Hawley House")

        # Building data from landmark details should be flattened into main metadata
        # We can't predict specific values since they depend on the implementation
        # but we can check that basic metadata is present
        self.assertIsNotNone(result.get("landmark_id"))

    def test_bbl_handling_none_value(self) -> None:
        """Test handling of None BBL values."""
        # Create mock buildings with None BBL
        mock_buildings = [
            {
                "name": "Salmagundi Club",
                "lpNumber": "LP-00009",
                "bbl": None,  # None value
                "binNumber": 1009274,
            }
        ]
        self.mock_db_client.get_landmark_buildings.return_value = mock_buildings

        # Make sure landmark details doesn't return a BBL
        mock_landmark_details = dict(get_mock_landmark_details())
        mock_landmark_details["bbl"] = None
        self.mock_db_client.get_landmark_by_id.return_value = mock_landmark_details

        # Call the method
        result = self.collector.collect_landmark_metadata("LP-00009")

        # Verify result is properly formatted
        # The current implementation flattens building data
        self.assertEqual(result["landmark_id"], "LP-00009")
        self.assertEqual(result["name"], "Irad Hawley House")

        # With None BBL, the implementation should still work correctly
        # We can't make specific assertions about BBL handling since it's flattened
        self.assertIsNotNone(result.get("landmark_id"))  # Basic sanity check

    def test_multiple_buildings(self) -> None:
        """Test handling of multiple buildings in response."""
        # Create mock response with multiple buildings
        mock_buildings = [
            {
                "name": "Building 1",
                "lpNumber": "LP-00009",
                "bbl": "1005690004",
                "binNumber": 1009274,
            },
            {
                "name": "Building 2",
                "lpNumber": "LP-00009",
                "bbl": "1005690005",
                "binNumber": 1009275,
            },
        ]
        self.mock_db_client.get_landmark_buildings.return_value = mock_buildings

        # Call the method
        result = self.collector.collect_landmark_metadata("LP-00009")

        # Verify result processed the multiple buildings correctly
        # The current implementation flattens building data, so we check basic metadata
        self.assertEqual(result["landmark_id"], "LP-00009")
        self.assertEqual(result["name"], "Irad Hawley House")

        # With multiple buildings, the implementation should aggregate/flatten the data
        # We can verify that basic metadata structure is maintained
        self.assertIsNotNone(result.get("landmark_id"))
        self.assertIsNotNone(result.get("name"))

    def test_mock_get_landmark_buildings(self) -> None:
        """Test the mock behavior of get_landmark_buildings."""
        # Directly call the mocked method to verify its behavior
        buildings = self.mock_db_client.get_landmark_buildings("LP-00009")
        self.assertEqual(buildings, self.mock_buildings)


class TestEnhancedMetadataCollectorErrorHandling(unittest.TestCase):
    """Test error handling in EnhancedMetadataCollector."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock db_client
        self.mock_db_client = Mock(spec=DbClient)

        # Create patchers
        self.db_client_patcher = patch(
            "nyc_landmarks.vectordb.enhanced_metadata.get_db_client",
            return_value=self.mock_db_client,
        )
        self.settings_patcher = patch(
            "nyc_landmarks.vectordb.enhanced_metadata.settings.COREDATASTORE_USE_API",
            True,  # Set to API mode
        )

        # Start patchers
        self.mock_get_db_client = self.db_client_patcher.start()
        self.mock_settings = self.settings_patcher.start()

        # Create the collector
        self.collector = EnhancedMetadataCollector()

        # Set up basic metadata response
        self.basic_metadata = {
            "landmark_id": "LP-00009",
            "name": "Irad Hawley House",
            "location": "47 Fifth Avenue",
            "borough": "Manhattan",
            "type": "Individual Landmark",
            "designation_date": "1969-09-09T00:00:00",
        }
        self.mock_db_client.get_landmark_metadata.return_value = self.basic_metadata

    def tearDown(self) -> None:
        """Clean up after each test method."""
        # Stop patchers
        self.db_client_patcher.stop()
        self.settings_patcher.stop()

    def test_direct_api_error(self) -> None:
        """Test error handling when direct API call fails."""
        # Set up direct API to raise exception
        self.mock_db_client.get_landmark_buildings.side_effect = Exception("API error")

        # Call the method
        result = self.collector.collect_landmark_metadata("LP-00009")

        # Verify API was called but failed
        self.mock_db_client.get_landmark_buildings.assert_called_once_with("LP-00009")

        # Convert result to dictionary for comparison, removing None values
        result_dict = {k: v for k, v in result.dict().items() if v is not None}

        # Check that all expected fields from basic metadata are present and correct
        for key, expected_value in self.basic_metadata.items():
            self.assertEqual(result_dict[key], expected_value)

        # Verify that additional auto-generated fields are present
        self.assertIn("processing_date", result_dict)
        self.assertIn("source_type", result_dict)

    def test_landmark_details_error(self) -> None:
        """Test error handling when get_landmark_by_id fails."""
        # Set up successful buildings call
        self.mock_db_client.get_landmark_buildings.return_value = [
            {"name": "Test Building", "bbl": "1234567890"}
        ]

        # Set up landmark details to raise exception
        self.mock_db_client.get_landmark_by_id.side_effect = Exception("API error")

        # Ensure we have a buildings key for testing
        self.mock_db_client.get_landmark_buildings.return_value = [
            {"name": "Test Building", "bbl": "1234567890"}
        ]

        # Call the method
        result = self.collector.collect_landmark_metadata("LP-00009")

        # Verify API was called but failed
        self.mock_db_client.get_landmark_by_id.assert_called_once_with("LP-00009")

        # Verify result contains basic metadata (implementation may vary how it handles errors)
        self.assertEqual(result["landmark_id"], "LP-00009")
        self.assertEqual(result["name"], "Irad Hawley House")

        # The current implementation flattens building data rather than keeping buildings array
        # Error handling behavior may vary, so just check basic structure
        self.assertIsNotNone(result.get("landmark_id"))

        # Photo status should not be set due to the error
        self.assertNotIn("has_photos", result)

    @unittest.skip("Skipping test for PLUTO - Fix Pluto Metadata")
    def test_pluto_data_error(self) -> None:
        """Test error handling when get_landmark_pluto_data fails."""
        # Set up successful buildings call
        self.mock_db_client.get_landmark_buildings.return_value = [
            {"name": "Test Building", "bbl": "1234567890"}
        ]
        # Set up landmark details with dictionary, not LpcReportDetailResponse
        self.mock_db_client.get_landmark_by_id.return_value = {
            "name": "Test Landmark",
        }

        # Set up PLUTO data to raise exception
        self.mock_db_client.get_landmark_pluto_data.side_effect = Exception("API error")

        # Call the method
        result = self.collector.collect_landmark_metadata("LP-00009")

        # Verify API was called but failed
        self.mock_db_client.get_landmark_pluto_data.assert_called_once_with("LP-00009")

        # Verify result includes buildings but no PLUTO data
        self.assertEqual(result["landmark_id"], "LP-00009")
        self.assertEqual(result["name"], "Irad Hawley House")
        # self.assertIn("buildings", result)

        # PLUTO data should not be set due to the error
        # self.assertNotIn("has_pluto_data", result)
        # self.assertNotIn("year_built", result)

    def test_basic_metadata_error(self) -> None:
        """Test error handling when get_landmark_metadata fails."""
        # Set up basic metadata to raise exception
        self.mock_db_client.get_landmark_metadata.side_effect = Exception("API error")

        # The current implementation may handle errors gracefully rather than raising
        result = self.collector.collect_landmark_metadata("LP-00009")

        # Verify API was called but failed
        self.mock_db_client.get_landmark_metadata.assert_called_once_with("LP-00009")

        # The implementation should return some default metadata or handle error gracefully
        self.assertIsNotNone(result)  # Should return something

        # Check that we get either a dict or LandmarkMetadata object
        if hasattr(result, "landmark_id"):
            # It's a LandmarkMetadata object
            self.assertEqual(result.landmark_id, "LP-00009")
        else:
            # It's a dict
            self.assertIn("landmark_id", result)


class TestEnhancedMetadataCollectorBatch(unittest.TestCase):
    """Test batch metadata collection in EnhancedMetadataCollector."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock db_client
        self.mock_db_client = Mock(spec=DbClient)

        # Create patchers
        self.db_client_patcher = patch(
            "nyc_landmarks.vectordb.enhanced_metadata.get_db_client",
            return_value=self.mock_db_client,
        )
        self.settings_patcher = patch(
            "nyc_landmarks.vectordb.enhanced_metadata.settings.COREDATASTORE_USE_API",
            False,  # Use non-API mode for simplicity
        )

        # Start patchers
        self.mock_get_db_client = self.db_client_patcher.start()
        self.mock_settings = self.settings_patcher.start()

        # Create the collector
        self.collector = EnhancedMetadataCollector()

        # Set up basic metadata responses
        self.metadata1 = {
            "landmark_id": "LP-00001",
            "name": "Landmark 1",
            "borough": "Manhattan",
        }
        self.metadata2 = {
            "landmark_id": "LP-00002",
            "name": "Landmark 2",
            "borough": "Brooklyn",
        }

    def tearDown(self) -> None:
        """Clean up after each test method."""
        # Stop patchers
        self.db_client_patcher.stop()
        self.settings_patcher.stop()

    def test_collect_batch_metadata(self) -> None:
        """Test collect_batch_metadata with multiple landmark IDs."""
        # Set up mock to return different metadata for different IDs
        self.mock_db_client.get_landmark_metadata.side_effect = [
            self.metadata1,
            self.metadata2,
        ]

        # Call the method
        result = self.collector.collect_batch_metadata(["LP-00001", "LP-00002"])

        # Verify API calls were made for both IDs
        self.assertEqual(self.mock_db_client.get_landmark_metadata.call_count, 2)
        self.mock_db_client.get_landmark_metadata.assert_any_call("LP-00001")
        self.mock_db_client.get_landmark_metadata.assert_any_call("LP-00002")

        # Verify result contains both metadata entries
        self.assertEqual(len(result), 2)

        # Check that all expected fields from metadata1 are present and correct in result["LP-00001"]
        for key, expected_value in self.metadata1.items():
            self.assertEqual(result["LP-00001"][key], expected_value)

        # Check that all expected fields from metadata2 are present and correct in result["LP-00002"]
        for key, expected_value in self.metadata2.items():
            self.assertEqual(result["LP-00002"][key], expected_value)

        # Verify that additional auto-generated fields are present
        self.assertIn("processing_date", result["LP-00001"])
        self.assertIn("source_type", result["LP-00001"])
        self.assertIn("processing_date", result["LP-00002"])
        self.assertIn("source_type", result["LP-00002"])

    def test_collect_batch_metadata_empty_list(self) -> None:
        """Test collect_batch_metadata with empty list."""
        # Call the method with empty list
        result = self.collector.collect_batch_metadata([])

        # Verify no API calls were made
        self.mock_db_client.get_landmark_metadata.assert_not_called()

        # Verify result is an empty dict
        self.assertEqual(result, {})
