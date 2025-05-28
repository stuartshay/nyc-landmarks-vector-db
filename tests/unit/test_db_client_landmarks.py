"""
Additional unit tests for the DbClient class.

This module tests additional functionality of the DbClient class from nyc_landmarks.db.db_client,
focusing on building, landmark, and search methods.
"""

import unittest
from typing import Any, Dict, List, Union
from unittest.mock import Mock, patch

from nyc_landmarks.db._coredatastore_api import _CoreDataStoreAPI as CoreDataStoreAPI
from nyc_landmarks.db.db_client import DbClient
from nyc_landmarks.models.landmark_models import (
    LandmarkDetail,
    LpcReportDetailResponse,
    LpcReportModel,
    LpcReportResponse,
)


class TestDbClientLandmarkMethods(unittest.TestCase):
    """Unit tests for landmark-related methods of DbClient class."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock CoreDataStoreAPI instance
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        # Create a DbClient instance with the mock API
        self.client = DbClient(self.mock_api)

    def test_get_all_landmarks(self) -> None:
        """Test get_all_landmarks method."""
        # Set up mock API to return a list of landmarks
        landmark_list = [{"id": "LP-00001", "name": "Test Landmark"}]
        self.mock_api.get_all_landmarks.return_value = landmark_list

        # Call the method
        result = self.client.get_all_landmarks()

        # Verify API was called correctly
        self.mock_api.get_all_landmarks.assert_called_once_with(None)

        # Verify result
        self.assertEqual(result, landmark_list)

        # Test with limit
        self.mock_api.get_all_landmarks.reset_mock()
        limit = 10
        self.client.get_all_landmarks(limit)
        self.mock_api.get_all_landmarks.assert_called_once_with(limit)

    def test_search_landmarks(self) -> None:
        """Test search_landmarks method."""
        # Set up mock API to return search results
        from nyc_landmarks.models.landmark_models import (
            LpcReportModel,
            LpcReportResponse,
        )

        # Create proper response with Pydantic models
        mock_model = LpcReportModel(
            lpNumber="LP-00001",
            name="Empire State Building",
            lpcId="",
            objectType="",
            architect="",
            style="",
            street="",
            borough="",
            dateDesignated="",
            photoStatus=False,
            mapStatus=False,
            neighborhood="",
            zipCode="",
            photoUrl=None,
            pdfReportUrl=None,
        )

        mock_response = LpcReportResponse(
            results=[mock_model],
            total=1,
            page=1,
            limit=10,
            **{"from": 1},  # Use explicit dict unpacking for reserved keyword
            to=1,
        )

        self.mock_api.search_landmarks.return_value = mock_response

        # Call the method
        result = self.client.search_landmarks("Empire")

        # Verify API was called correctly
        self.mock_api.search_landmarks.assert_called_once_with("Empire")

        # Verify result
        self.assertEqual(result, mock_response)

    def test_get_landmark_metadata(self) -> None:
        """Test get_landmark_metadata method."""
        # Set up mock API to return metadata
        metadata = {
            "landmark_id": "LP-00001",
            "name": "Test Landmark",
            "borough": "Manhattan",
        }
        self.mock_api.get_landmark_metadata.return_value = metadata

        # Call the method
        result = self.client.get_landmark_metadata("LP-00001")

        # Verify API was called correctly
        self.mock_api.get_landmark_metadata.assert_called_once_with("LP-00001")

        # Verify result
        self.assertEqual(result, metadata)

    def _create_test_landmark_models(self, count: int = 20) -> list:
        """Helper method to create test landmark models."""
        from nyc_landmarks.models.landmark_models import LpcReportModel

        return [
            LpcReportModel(
                lpNumber=f"LP-{i:05}",
                name=f"Landmark {i}",
                lpcId="",
                objectType="",
                architect="",
                style="",
                street="",
                borough="",
                dateDesignated="",
                photoStatus=False,
                mapStatus=False,
                neighborhood="",
                zipCode="",
                photoUrl=None,
                pdfReportUrl=None,
            )
            for i in range(1, count + 1)
        ]

    def _assert_landmark_id(self, item: Any, expected_id: str) -> None:
        """Helper method to assert landmark ID regardless of item type."""
        if isinstance(item, dict):
            if "id" in item:
                self.assertEqual(item.get("id"), expected_id)
            elif "lpNumber" in item:
                self.assertEqual(item.get("lpNumber"), expected_id)
            else:
                self.fail(f"Item missing expected keys: {item}")
        elif hasattr(item, "id"):
            self.assertEqual(item.id, expected_id)
        elif hasattr(item, "lpNumber"):
            self.assertEqual(item.lpNumber, expected_id)
        else:
            self.fail(f"Unexpected type for result item: {type(item)}")

    def _setup_fallback_mock_api(self) -> Mock:
        """Helper to setup mock API for fallback testing."""
        from nyc_landmarks.models.landmark_models import LpcReportResponse

        mock_api = Mock(spec=CoreDataStoreAPI)
        result_models = self._create_test_landmark_models(20)
        report_response = LpcReportResponse(
            total=20,
            page=1,
            limit=20,
            **{"from": 1},
            to=20,
            results=result_models,
        )
        mock_api.get_all_landmarks.return_value = report_response
        mock_api.get_lpc_reports.side_effect = Exception("API error")
        return mock_api

    def test_get_landmarks_page_fallback_first_page(self) -> None:
        """Test get_landmarks_page fallback to get_all_landmarks for first page."""
        mock_api = self._setup_fallback_mock_api()
        client = DbClient(mock_api)

        with patch(
            "builtins.hasattr",
            lambda obj, attr: False if attr == "get_landmarks_page" else True,
        ):
            result = client.get_landmarks_page(page_size=5, page=1)

            mock_api.get_all_landmarks.assert_called_once()
            self.assertEqual(len(result), 5)
            self._assert_landmark_id(result[0], "LP-00001")
            self._assert_landmark_id(result[4], "LP-00005")

    def test_get_landmarks_page_fallback_second_page(self) -> None:
        """Test get_landmarks_page fallback to get_all_landmarks for second page."""
        mock_api = self._setup_fallback_mock_api()
        client = DbClient(mock_api)

        with patch(
            "builtins.hasattr",
            lambda obj, attr: False if attr == "get_landmarks_page" else True,
        ):
            result = client.get_landmarks_page(page_size=5, page=2)

            mock_api.get_all_landmarks.assert_called_once()
            self.assertEqual(len(result), 5)
            self._assert_landmark_id(result[0], "LP-00006")
            self._assert_landmark_id(result[4], "LP-00010")

    def test_get_landmarks_page_fallback_api_error(self) -> None:
        """Test get_landmarks_page fallback behavior when API returns error."""
        mock_api = Mock(spec=CoreDataStoreAPI)
        mock_api.get_all_landmarks.side_effect = Exception("API error")
        client = DbClient(mock_api)

        with patch(
            "builtins.hasattr",
            lambda obj, attr: False if attr == "get_landmarks_page" else True,
        ):
            result = client.get_landmarks_page(page_size=5, page=1)
            self.assertEqual(result, [])

    def test_get_lpc_reports_direct_method(self) -> None:
        """Test get_lpc_reports with direct API method."""
        # Create mock response
        mock_response = LpcReportResponse(
            results=[
                LpcReportModel(
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
            ],
            total=1,
            page=1,
            limit=10,
            **{"from": 1},  # Use explicit dict unpacking for reserved keyword
            to=1,
        )

        # Set up mock API to return our response
        self.mock_api.get_lpc_reports.return_value = mock_response

        # Call the method with various parameters
        result = self.client.get_lpc_reports(
            page=2,
            limit=15,
            borough="Manhattan",
            object_type="Individual Landmark",
            neighborhood="Midtown",
            search_text="Empire",
            parent_style_list=["Art Deco"],
            sort_column="name",
            sort_order="asc",
        )

        # Verify API was called correctly with all parameters
        self.mock_api.get_lpc_reports.assert_called_once_with(
            page=2,
            limit=15,
            borough="Manhattan",
            object_type="Individual Landmark",
            neighborhood="Midtown",
            search_text="Empire",
            parent_style_list=["Art Deco"],
            sort_column="name",
            sort_order="asc",
        )

        # Verify result
        self.assertEqual(result, mock_response)

    def test_get_lpc_reports_fallback(self) -> None:
        """Test get_lpc_reports with fallback to get_landmarks_page."""
        # This tests that the client's get_lpc_reports method is called
        # and that an exception is raised when it fails (since there's no real fallback)
        self.mock_api.get_lpc_reports.side_effect = Exception("API error")

        # We expect an exception to be raised because there's no fallback in the implementation
        with self.assertRaises(Exception):
            self.client.get_lpc_reports(page=1, limit=10)

        # Verify API call was made
        self.mock_api.get_lpc_reports.assert_called_once()

    def test_get_lpc_reports_fallback_with_error(self) -> None:
        """Test get_lpc_reports error handling."""
        # Creating a client with no get_lpc_reports method
        limited_mock_api = Mock(spec=[])
        # Ensure the mock doesn't have any methods that would be used in the fallback path
        client = DbClient(limited_mock_api)

        # The implementation will try to access get_lpc_reports method which doesn't exist,
        # then fall back to get_landmarks_page which also doesn't exist
        with self.assertRaises(Exception):
            client.get_lpc_reports(page=1, limit=10)

    def test_get_landmark_pdf_url_from_detail_response(self) -> None:
        """Test get_landmark_pdf_url with LpcReportDetailResponse."""
        # Create a mock LpcReportDetailResponse with PDF URL
        mock_response = Mock(spec=LpcReportDetailResponse)
        mock_response.lpNumber = "LP-00001"
        mock_response.name = "Test Landmark"
        mock_response.borough = "Manhattan"
        mock_response.objectType = "Individual Landmark"
        mock_response.dateDesignated = "2020-01-01"
        mock_response.pdfReportUrl = "https://example.com/pdf.pdf"

        # Set up mock get_landmark_by_id to return our response
        with patch.object(
            self.client, "get_landmark_by_id", return_value=mock_response
        ):
            # Call the method
            result = self.client.get_landmark_pdf_url("LP-00001")

            # Verify result
            self.assertEqual(result, "https://example.com/pdf.pdf")

    @patch("nyc_landmarks.db.db_client.logger")
    def test_get_landmark_pdf_url_with_error(self, mock_logger: Mock) -> None:
        """Test get_landmark_pdf_url with error."""
        # Set up mock get_landmark_by_id to raise exception
        with patch.object(
            self.client, "get_landmark_by_id", side_effect=Exception("API error")
        ):
            # Set up mock API client with get_landmark_pdf_url method
            self.mock_api.get_landmark_pdf_url.return_value = (
                "https://example.com/fallback.pdf"
            )

            # Call the method
            result = self.client.get_landmark_pdf_url("LP-00001")

            # Verify fallback was used
            self.assertEqual(result, "https://example.com/fallback.pdf")
            self.mock_api.get_landmark_pdf_url.assert_called_once_with("LP-00001")
            # Verify error was logged
            mock_logger.warning.assert_called()

    def test_get_landmark_pdf_url_no_url(self) -> None:
        """Test get_landmark_pdf_url when no URL is available."""
        # Create a mock LpcReportDetailResponse without PDF URL
        mock_response = Mock(spec=LpcReportDetailResponse)
        mock_response.lpNumber = "LP-00001"
        mock_response.name = "Test Landmark"
        mock_response.borough = "Manhattan"
        mock_response.objectType = "Individual Landmark"
        mock_response.dateDesignated = "2020-01-01"
        mock_response.pdfReportUrl = None

        # Set up mock get_landmark_by_id to return our response
        with patch.object(
            self.client, "get_landmark_by_id", return_value=mock_response
        ):
            # Also make sure the fallback method returns None too
            self.mock_api.get_landmark_pdf_url.return_value = None

            # Call the method
            result = self.client.get_landmark_pdf_url("LP-00001")

        # Verify None is returned when no URL is available
        self.assertIsNone(result)


class TestDbClientBuildingsMethods(unittest.TestCase):
    """Unit tests for building-related methods of DbClient class."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock CoreDataStoreAPI instance
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        # Create a DbClient instance with the mock API
        self.client = DbClient(self.mock_api)

    def test_fetch_buildings_from_client(self) -> None:
        """Test _fetch_buildings_from_client method."""
        # Set up mock API to return buildings
        buildings = [
            {"lpNumber": "LP-00001", "name": "Building 1"},
            {"lpNumber": "LP-00001", "name": "Building 2"},
        ]
        self.mock_api.get_landmark_buildings.return_value = buildings

        # Call the method
        result = self.client._fetch_buildings_from_client("LP-00001", 10)

        # Verify API was called correctly
        self.mock_api.get_landmark_buildings.assert_called_once_with("LP-00001", 10)

        # Verify result
        self.assertEqual(result, buildings)

    @patch("nyc_landmarks.db.db_client.logger")
    def test_fetch_buildings_from_client_with_error(self, mock_logger: Mock) -> None:
        """Test _fetch_buildings_from_client with error."""
        # Set up mock API to raise exception
        self.mock_api.get_landmark_buildings.side_effect = Exception("API error")

        # Call the method
        result = self.client._fetch_buildings_from_client("LP-00001", 10)

        # Verify empty list is returned and error is logged
        self.assertEqual(result, [])
        mock_logger.error.assert_called()

    def test_fetch_buildings_from_client_no_method(self) -> None:
        """Test _fetch_buildings_from_client when client doesn't have the method."""
        # Set up a mock that doesn't have get_landmark_buildings method
        limited_mock_api = Mock(spec=CoreDataStoreAPI)
        limited_mock_api.get_landmark_buildings = None
        limited_client = DbClient(limited_mock_api)

        # Call the method
        result = limited_client._fetch_buildings_from_client("LP-00001", 10)

        # Verify empty list is returned
        self.assertEqual(result, [])

    def test_fetch_buildings_from_landmark_detail(self) -> None:
        """Test _fetch_buildings_from_landmark_detail method."""
        # Create mock response for testing
        mock_response = Mock(spec=LpcReportDetailResponse)

        # Use the centralized mock function from landmark_mocks.py
        from tests.mocks.landmark_mocks import (
            get_mock_landmarks_for_test_fetch_buildings,
        )

        # Set up mock response landmarks list
        landmarks_list = get_mock_landmarks_for_test_fetch_buildings()
        mock_response.landmarks = landmarks_list

        # Set up mock get_landmark_by_id to return our response
        with patch.object(
            self.client, "get_landmark_by_id", return_value=mock_response
        ):
            # Call the method
            result = self.client._fetch_buildings_from_landmark_detail("LP-00001", 10)

            # Verify result
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0], landmarks_list[0])
            self.assertEqual(result[1], landmarks_list[1])

    @patch("nyc_landmarks.db.db_client.logger")
    def test_fetch_buildings_from_landmark_detail_with_dict_items(
        self, mock_logger: Mock
    ) -> None:
        """Test _fetch_buildings_from_landmark_detail with dict items in landmarks list."""
        # Create a mock LpcReportDetailResponse with landmarks list containing dicts
        landmarks_list = [
            {
                "lpNumber": "LP-00001A",
                "name": "Building 1",
                "designatedAddress": "123 Main St",
                "boroughId": "1",
                "objectType": "Individual Landmark",
                "designatedDate": "2020-01-01",
                "historicDistrict": "Test District",
                "street": "123 Main St",
            },
            {
                "lpNumber": "LP-00001B",
                "name": "Building 2",
                "designatedAddress": "456 Side St",
                "boroughId": "1",
                "objectType": "Individual Landmark",
                "designatedDate": "2020-01-02",
                "historicDistrict": "Test District",
                "street": "456 Side St",
            },
        ]
        mock_response = Mock(spec=LpcReportDetailResponse)
        mock_response.landmarks = landmarks_list

        # Set up mock get_landmark_by_id to return our response
        with patch.object(
            self.client, "get_landmark_by_id", return_value=mock_response
        ):
            # Call the method
            result = self.client._fetch_buildings_from_landmark_detail("LP-00001", 10)

            # Verify result
            self.assertEqual(len(result), 2)

            # Type-safely check first item
            item0 = result[0]
            if isinstance(item0, LandmarkDetail):
                self.assertEqual(item0.lpNumber, "LP-00001A")
            elif isinstance(item0, dict):
                self.assertEqual(item0.get("lpNumber"), "LP-00001A")
            else:
                self.fail(f"Unexpected type for item0: {type(item0)}")

            # Type-safely check second item
            item1 = result[1]
            if isinstance(item1, LandmarkDetail):
                self.assertEqual(item1.lpNumber, "LP-00001B")
            elif isinstance(item1, dict):
                self.assertEqual(item1.get("lpNumber"), "LP-00001B")
            else:
                self.fail(f"Unexpected type for item1: {type(item1)}")

    def test_convert_building_items_to_models(self) -> None:
        """Test _convert_building_items_to_models method."""
        # Create a mixed list of items with explicit typing
        items: List[Union[Dict[str, Any], LandmarkDetail, LpcReportModel]] = [
            LandmarkDetail(
                lpNumber="LP-00001A",
                name="Building 1",
                designatedAddress="123 Main St",
                boroughId="1",
                objectType="Individual Landmark",
                designatedDate="2020-01-01",
                historicDistrict="Test District",
                street="123 Main St",
                bbl="1000010001",
                binNumber=1000001,
                block=1000,
                lot=1,
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
            ),
            {
                "lpNumber": "LP-00001B",
                "name": "Building 2",
                "street": "456 Side St",
                "borough": "Manhattan",
                "objectType": "Individual Landmark",
                "dateDesignated": "2020-01-02",
                "architect": "Test Architect",
                "style": "Test Style",
                "neighborhood": "Test Neighborhood",
                "zipCode": "10001",
                "photoStatus": True,
                "mapStatus": True,
                "photoUrl": "https://example.com/photo.jpg",
                "pdfReportUrl": "https://example.com/pdf.pdf",
                "lpcId": "00001B",
            },
            LpcReportModel(
                name="Building 3",
                lpNumber="LP-00001C",
                lpcId="00001C",
                objectType="Individual Landmark",
                architect="Test Architect",
                style="Test Style",
                street="789 Other St",
                borough="Manhattan",
                dateDesignated="2020-01-03",
                photoStatus=True,
                mapStatus=True,
                neighborhood="Test Neighborhood",
                zipCode="10001",
                photoUrl="https://example.com/photo.jpg",
                pdfReportUrl="https://example.com/pdf.pdf",
            ),
        ]

        # Call the method
        result = self.client._convert_building_items_to_models(items, "LP-00001")

        # Verify result
        self.assertEqual(len(result), 3)
        self.assertIsInstance(result[0], LpcReportModel)
        self.assertIsInstance(result[1], LpcReportModel)
        self.assertIsInstance(result[2], LpcReportModel)
        self.assertEqual(result[0].lpNumber, "LP-00001A")
        self.assertEqual(result[1].lpNumber, "LP-00001B")
        self.assertEqual(result[2].lpNumber, "LP-00001C")

    def test_get_landmark_buildings(self) -> None:
        """Test get_landmark_buildings method."""
        # Set up mock _fetch_buildings_from_client to return buildings
        buildings = [
            {"lpNumber": "LP-00001A", "name": "Building 1"},
            {"lpNumber": "LP-00001B", "name": "Building 2"},
        ]

        with patch.object(
            self.client, "_fetch_buildings_from_client", return_value=buildings
        ) as mock_fetch_client:
            with patch.object(
                self.client, "_convert_building_items_to_models"
            ) as mock_convert:
                # Set up mock _convert_building_items_to_models to return models
                mock_models = [
                    LpcReportModel(
                        name="Building 1",
                        lpNumber="LP-00001A",
                        lpcId="00001A",
                        objectType="Individual Landmark",
                        architect="Test Architect",
                        style="Test Style",
                        street="123 Main St",
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
                        name="Building 2",
                        lpNumber="LP-00001B",
                        lpcId="00001B",
                        objectType="Individual Landmark",
                        architect="Test Architect",
                        style="Test Style",
                        street="456 Side St",
                        borough="Manhattan",
                        dateDesignated="2020-01-02",
                        photoStatus=True,
                        mapStatus=True,
                        neighborhood="Test Neighborhood",
                        zipCode="10001",
                        photoUrl="https://example.com/photo.jpg",
                        pdfReportUrl="https://example.com/pdf.pdf",
                    ),
                ]
                mock_convert.return_value = mock_models

                # Call the method
                result = self.client.get_landmark_buildings("12345", 10)

                # Verify _standardize_lp_number was used implicitly
                mock_fetch_client.assert_called_once_with("LP-12345", 10)

                # Verify _convert_building_items_to_models was called correctly
                mock_convert.assert_called_once_with(buildings, "LP-12345")

                # Verify result
                self.assertEqual(result, mock_models)

    def test_get_landmark_buildings_fallback(self) -> None:
        """Test get_landmark_buildings fallback when primary method returns empty list."""
        # Set up mock _fetch_buildings_from_client to return empty list
        with patch.object(self.client, "_fetch_buildings_from_client", return_value=[]):
            # Set up mock _fetch_buildings_from_landmark_detail to return buildings
            buildings = [
                LandmarkDetail(
                    lpNumber="LP-00001A",
                    name="Building 1",
                    designatedAddress="123 Main St",
                    boroughId="1",
                    objectType="Individual Landmark",
                    designatedDate="2020-01-01",
                    historicDistrict="Test District",
                    street="123 Main St",
                    bbl="1000010001",
                    binNumber=1000001,
                    block=1000,
                    lot=1,
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
            ]

            with patch.object(
                self.client,
                "_fetch_buildings_from_landmark_detail",
                return_value=buildings,
            ) as mock_fetch_detail:
                with patch.object(
                    self.client, "_convert_building_items_to_models"
                ) as mock_convert:
                    # Set up mock _convert_building_items_to_models to return models
                    mock_models = [
                        LpcReportModel(
                            name="Building 1",
                            lpNumber="LP-00001A",
                            lpcId="00001A",
                            objectType="Individual Landmark",
                            architect="Test Architect",
                            style="Test Style",
                            street="123 Main St",
                            borough="Manhattan",
                            dateDesignated="2020-01-01",
                            photoStatus=True,
                            mapStatus=True,
                            neighborhood="Test Neighborhood",
                            zipCode="10001",
                            photoUrl="https://example.com/photo.jpg",
                            pdfReportUrl="https://example.com/pdf.pdf",
                        )
                    ]
                    mock_convert.return_value = mock_models

                    # Call the method
                    result = self.client.get_landmark_buildings("12345", 10)

                    # Verify fallback method was called
                    mock_fetch_detail.assert_called_once_with("LP-12345", 10)

                    # Verify _convert_building_items_to_models was called correctly
                    mock_convert.assert_called_once_with(buildings, "LP-12345")

                    # Verify result
                    self.assertEqual(result, mock_models)


class TestDbClientTotalCount(unittest.TestCase):
    """Unit tests for total count methods of DbClient class."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Create a mock CoreDataStoreAPI instance
        self.mock_api = Mock(spec=CoreDataStoreAPI)
        # Create a DbClient instance with the mock API
        self.client = DbClient(self.mock_api)

    def test_get_total_record_count_from_metadata(self) -> None:
        """Test get_total_record_count using API metadata."""
        # Create a mock response with total field
        # Create mock instead of direct instantiation
        mock_response = Mock(spec=LpcReportResponse)
        mock_response.results = []
        mock_response.total = 1765
        mock_response.page = 1
        mock_response.limit = 1
        mock_response.from_ = 1  # Access the property directly on the mock
        mock_response.to = 1

        # Set up mock get_lpc_reports to return our response
        with patch.object(
            self.client, "get_lpc_reports", return_value=mock_response
        ) as mock_get_lpc_reports:
            # Call the method
            result = self.client.get_total_record_count()

            # Verify get_lpc_reports was called correctly (with minimal records)
            mock_get_lpc_reports.assert_called_once_with(page=1, limit=1)

            # Verify result
            self.assertEqual(result, 1765)

    def test_get_total_record_count_from_pages(self) -> None:
        """Test get_total_record_count by estimating from pages."""
        # Set up mock _get_count_from_api_metadata to return 0 (failure)
        with patch.object(self.client, "_get_count_from_api_metadata", return_value=0):
            # Set up mock get_landmarks_page to return diminishing results
            landmarks = [
                {"id": f"LP-0000{i}", "name": f"Landmark {i}"} for i in range(1, 51)
            ]

            with patch.object(
                self.client,
                "get_landmarks_page",
                side_effect=[
                    landmarks,  # First page (50 items)
                    landmarks[:30],  # Second page (30 items - less than page size)
                    [],  # Third page (empty - end of data)
                ],
            ) as mock_get_page:
                # Call the method
                result = self.client.get_total_record_count()

                # Verify get_landmarks_page was called correctly
                self.assertEqual(
                    mock_get_page.call_count, 2
                )  # Should stop after second page

                # Verify result is sum of items (50 + 30 = 80)
                self.assertEqual(result, 80)

    @patch("nyc_landmarks.db.db_client.logger")
    def test_get_total_record_count_with_error(self, mock_logger: Mock) -> None:
        """Test get_total_record_count with error."""
        # Set up mock methods to raise exceptions
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

                # Verify default value is returned and error is logged
                self.assertEqual(result, 100)
                mock_logger.error.assert_called()


if __name__ == "__main__":
    unittest.main()
