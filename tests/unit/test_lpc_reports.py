"""
Unit tests for the LPC Report models and API client functionality.

These tests verify that the Pydantic models work correctly and the API client
properly passes data to the models.
"""

import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI
from nyc_landmarks.models.landmark_models import LpcReportModel, LpcReportResponse


class TestLpcReports(unittest.TestCase):
    """Test the LPC Report models and API client functionality."""

    def test_lpc_report_model(self) -> None:
        """Test that LpcReportModel correctly validates and processes data."""
        # Test with minimal required fields
        report = LpcReportModel(
            lpNumber="LP-00001",
            lpcId="00001",
            name="Empire State Building",
            pdfReportUrl=None,
            borough="Manhattan",
            objectType="Individual Landmark",
            street="350 5th Ave",
            dateDesignated="1981-05-19",
            photoStatus=False,
            architect="Shreve, Lamb & Harmon",
            style="Art Deco",
            neighborhood="Midtown",
            zipCode="10118",
            mapStatus=False,
            photoUrl=None,
        )
        self.assertEqual(report.lpNumber, "LP-00001")
        self.assertEqual(report.name, "Empire State Building")
        self.assertIsNone(report.pdfReportUrl)

        # Test with all fields
        report = LpcReportModel(
            lpNumber="LP-00001",
            lpcId="00001",
            name="Empire State Building",
            pdfReportUrl="https://example.com/reports/LP-00001.pdf",
            borough="Manhattan",
            objectType="Individual Landmark",
            street="350 5th Ave",
            dateDesignated="1981-05-19",
            architect="Shreve, Lamb & Harmon",
            style="Art Deco",
            neighborhood="Midtown",
            zipCode="10118",
            mapStatus=True,
            photoStatus=True,
            photoUrl="https://example.com/photos/empire-state.jpg",
        )
        self.assertEqual(report.lpNumber, "LP-00001")
        self.assertEqual(report.borough, "Manhattan")
        self.assertEqual(report.style, "Art Deco")

    def test_lpc_report_response(self) -> None:
        """Test that LpcReportResponse correctly validates and processes data."""
        # Test with valid data
        response = LpcReportResponse(
            results=[
                LpcReportModel(
                    lpNumber="LP-00001",
                    lpcId="00001",
                    name="Empire State Building",
                    pdfReportUrl=None,
                    borough="Manhattan",
                    objectType="Individual Landmark",
                    mapStatus=True,
                    zipCode="10118",
                    photoStatus=False,
                    street="350 5th Ave",
                    dateDesignated="1981-05-19",
                    architect="Shreve, Lamb & Harmon",
                    style="Art Deco",
                    neighborhood="Midtown",
                    photoUrl=None,
                ),
                LpcReportModel(
                    lpNumber="LP-00002",
                    lpcId="00002",
                    name="Chrysler Building",
                    pdfReportUrl=None,
                    borough="Manhattan",
                    photoStatus=False,
                    mapStatus=True,
                    zipCode="10174",
                    objectType="Individual Landmark",
                    street="405 Lexington Ave",
                    dateDesignated="1978-09-12",
                    architect="William Van Alen",
                    style="Art Deco",
                    neighborhood="Midtown",
                    photoUrl=None,
                ),
            ],
            total=2,
            page=1,
            limit=2,
            **{"from": 1},
            to=2,
        )
        self.assertEqual(len(response.results), 2)
        self.assertEqual(response.total, 2)
        self.assertEqual(response.page, 1)
        self.assertEqual(response.results[0].lpNumber, "LP-00001")

    @patch("nyc_landmarks.db.coredatastore_api.CoreDataStoreAPI._make_request")
    def test_get_lpc_reports(self, mock_make_request: MagicMock) -> None:
        """Test that get_lpc_reports correctly processes API responses."""
        # Mock API response
        mock_response: dict[str, Any] = {
            "results": [
                {
                    "lpNumber": "LP-00001",
                    "name": "Empire State Building",
                    "pdfReportUrl": "https://example.com/reports/LP-00001.pdf",
                    "borough": "Manhattan",
                    "objectType": "Individual Landmark",
                },
                {
                    "lpNumber": "LP-00002",
                    "name": "Chrysler Building",
                    "pdfReportUrl": "https://example.com/reports/LP-00002.pdf",
                    "borough": "Manhattan",
                    "objectType": "Individual Landmark",
                },
            ],
            "total": 2,
            "page": 1,
            "limit": 2,
            "from": 1,
            "to": 2,
        }
        mock_make_request.return_value = mock_response

        # Test the API client method
        api = CoreDataStoreAPI()
        response = api.get_lpc_reports(
            page=1, limit=10, borough="Manhattan", object_type="Individual Landmark"
        )

        # Verify that the method correctly called the API
        mock_make_request.assert_called_once()
        args, kwargs = mock_make_request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(
            args[1], "/api/LpcReport/10/1"
        )  # Updated to match actual implementation with /limit/page
        self.assertEqual(kwargs["params"]["Borough"], "Manhattan")
        self.assertEqual(kwargs["params"]["ObjectType"], "Individual Landmark")

        # Verify the response was correctly processed using Pydantic
        self.assertIsInstance(response, LpcReportResponse)
        self.assertEqual(len(response.results), 2)
        self.assertEqual(response.total, 2)
        self.assertEqual(response.results[0].lpNumber, "LP-00001")
        self.assertEqual(response.results[1].name, "Chrysler Building")

    @patch("nyc_landmarks.db.coredatastore_api.CoreDataStoreAPI._make_request")
    def test_get_lpc_reports_with_pagination(
        self, mock_make_request: MagicMock
    ) -> None:
        """Test pagination functionality of get_lpc_reports."""
        # Mock first page response
        mock_response_page1 = {
            "results": [
                {"lpNumber": "LP-00001", "name": "Empire State Building"},
                {"lpNumber": "LP-00002", "name": "Chrysler Building"},
            ],
            "total": 4,
            "page": 1,
            "limit": 2,
            "from": 1,
            "to": 2,
        }

        mock_response_page2 = {
            "results": [
                {"lpNumber": "LP-00003", "name": "Flatiron Building"},
                {"lpNumber": "LP-00004", "name": "Woolworth Building"},
            ],
            "total": 4,
            "page": 2,
            "limit": 2,
            "from": 3,
            "to": 4,
        }

        # Set up mock to return different responses for different requests
        mock_make_request.side_effect = [mock_response_page1, mock_response_page2]

        # Test the API client method for first page
        api = CoreDataStoreAPI()
        response_page1 = api.get_lpc_reports(page=1, limit=2)

        # Test the API client method for second page
        response_page2 = api.get_lpc_reports(page=2, limit=2)

        # Verify the first page response
        self.assertEqual(len(response_page1.results), 2)
        self.assertEqual(response_page1.total, 4)
        self.assertEqual(response_page1.page, 1)
        self.assertEqual(response_page1.results[0].lpNumber, "LP-00001")

        # Verify the second page response
        self.assertEqual(len(response_page2.results), 2)
        self.assertEqual(response_page2.total, 4)
        self.assertEqual(response_page2.page, 2)
        self.assertEqual(response_page2.results[0].lpNumber, "LP-00003")

        # Verify the pages have different content
        self.assertNotEqual(
            response_page1.results[0].lpNumber, response_page2.results[0].lpNumber
        )


if __name__ == "__main__":
    unittest.main()
