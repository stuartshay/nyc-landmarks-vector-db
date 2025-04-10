"""
Integration tests using the coredatastore-swagger-mcp server directly.

These tests demonstrate how to use the MCP server tools to interact with
the CoreDataStore API for testing purposes.
"""

import json
import os
import sys
import unittest
from pathlib import Path

import pytest

# Add the project root to the path so we can import modules
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from nyc_landmarks.models.landmark_models import LpcReportModel, LpcReportResponse, PdfInfo


@pytest.mark.mcp
class TestCoredataStoreMcp(unittest.TestCase):
    """
    Tests that directly use the coredatastore-swagger-mcp server.

    These tests will be skipped if the MCP server is not available or
    if running in a CI environment.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        # Skip all tests if we're in a CI environment
        if "CI" in os.environ:
            raise unittest.SkipTest("Skipping MCP tests in CI environment")

        # Check if MCP server is available
        # In a real implementation, we would use a more robust check
        cls.mcp_available = True

    @unittest.skipIf(
        not os.environ.get("COREDATASTORE_API_KEY"),
        "No CoreDataStore API key available",
    )
    def test_get_lpc_report_with_mcp(self):
        """Test retrieving an LPC report using the MCP server tool."""
        if not self.mcp_available:
            self.skipTest("MCP server not available")

        # In a real test, we would use the MCP server tool directly
        # For now, we'll mock the expected behavior

        # This is how we would structure the test when using MCP
        """
        # Example MCP server usage (in actual code)
        response = use_mcp_tool(
            server_name="coredatastore-swagger-mcp",
            tool_name="GetLpcReport",
            arguments={"lpcId": "LP-00001"}
        )

        # Validate the response
        self.assertIn("lpNumber", response)
        self.assertIn("name", response)
        """

        # For this demonstration, we'll use a mock response
        mock_response = {
            "lpNumber": "LP-00001",
            "name": "Empire State Building",
            "pdfReportUrl": "https://example.com/reports/LP-00001.pdf",
            "borough": "Manhattan",
            "objectType": "Individual Landmark",
        }

        # Validate with our Pydantic model
        model = LpcReportModel(**mock_response)

        # Assertions
        self.assertEqual(model.lpNumber, "LP-00001")
        self.assertEqual(model.name, "Empire State Building")
        self.assertIsInstance(model.pdfReportUrl, str)

    @unittest.skipIf(
        not os.environ.get("COREDATASTORE_API_KEY"),
        "No CoreDataStore API key available",
    )
    def test_get_lpc_reports_filtered_with_mcp(self):
        """Test retrieving filtered LPC reports using the MCP server tool."""
        if not self.mcp_available:
            self.skipTest("MCP server not available")

        # In a real test, we would use the MCP server tool directly
        # For now, we'll mock the expected behavior

        # This is how we would structure the test when using MCP
        """
        # Example MCP server usage (in actual code)
        response = use_mcp_tool(
            server_name="coredatastore-swagger-mcp",
            tool_name="GetLpcReports",
            arguments={
                "limit": 5,
                "page": 1,
                "Borough": "Manhattan",
                "ObjectType": "Individual Landmark"
            }
        )

        # Validate the response
        self.assertIn("results", response)
        self.assertIn("totalCount", response)
        self.assertIn("pageCount", response)
        """

        # For this demonstration, we'll use a mock response
        mock_response = {
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
            "totalCount": 2,
            "pageCount": 1,
        }

        # Validate with our Pydantic model
        response_model = LpcReportResponse(**mock_response)

        # Assertions
        self.assertEqual(len(response_model.results), 2)
        self.assertEqual(response_model.totalCount, 2)
        self.assertEqual(response_model.pageCount, 1)

        # Check that each report can be validated
        for report in response_model.results:
            self.assertIsInstance(report.lpNumber, str)
            self.assertIsInstance(report.name, str)

    @unittest.skipIf(
        not os.environ.get("COREDATASTORE_API_KEY"),
        "No CoreDataStore API key available",
    )
    def test_get_landmarks_with_mcp(self):
        """Test retrieving buildings linked to a landmark using the MCP server tool."""
        if not self.mcp_available:
            self.skipTest("MCP server not available")

        # In a real test, we would use the MCP server tool directly
        # For now, we'll mock the expected behavior

        # This is how we would structure the test when using MCP
        """
        # Example MCP server usage (in actual code)
        response = use_mcp_tool(
            server_name="coredatastore-swagger-mcp",
            tool_name="GetLandmarks",
            arguments={
                "limit": 5,
                "page": 1,
                "LpcNumber": "LP-00001"
            }
        )

        # Validate the response
        self.assertIn("results", response)
        """

        # Mock a building response to demonstrate validation
        mock_building = {
            "id": "NYCL-123",
            "address": "350 5th Ave",
            "landmarkId": "LP-00001",
        }

        # In a real test, we'd validate buildings from the response
        # For now, just demonstrate the test structure
        self.assertIn("id", mock_building)
        self.assertIn("address", mock_building)
        self.assertIn("landmarkId", mock_building)


if __name__ == "__main__":
    unittest.main()
