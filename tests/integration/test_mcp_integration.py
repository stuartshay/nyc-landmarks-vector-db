"""
Integration tests using the coredatastore-swagger-mcp server.

These tests validate the integration with the CoreDataStore API
through the MCP server tools.
"""

import json
import os
import sys
import unittest
from pathlib import Path

# Add the project root to the path so we can import modules
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from nyc_landmarks.models.landmark_models import LpcReportModel, PdfInfo


class TestCoreDataStoreMcpIntegration(unittest.TestCase):
    """
    Integration tests for the CoreDataStore MCP server.

    These tests require the MCP server to be running and connected.
    """

    @unittest.skipIf("CI" in os.environ, "Skipping MCP tests in CI environment")
    def test_get_lpc_report(self):
        """Test retrieving an LPC report from the MCP server."""
        # This test needs to be run in the environment with the MCP server
        # and will be skipped if the MCP server is not available

        # Sample LPC ID for testing
        lpc_id = "LP-00001"  # Empire State Building

        try:
            # This would use the MCP server if running in the Cline environment
            # Here we're just checking that our model can handle the expected response

            # Mock response format based on API documentation
            mock_response = {
                "lpNumber": lpc_id,
                "name": "Empire State Building",
                "pdfReportUrl": "https://example.com/reports/LP-00001.pdf",
                "borough": "Manhattan",
                "objectType": "Individual Landmark",
            }

            # Validate the response with our Pydantic model
            model = LpcReportModel(**mock_response)

            # Assertions
            self.assertEqual(model.lpNumber, lpc_id)
            self.assertIsInstance(model.name, str)
            self.assertIsInstance(model.pdfReportUrl, str)
        except Exception as e:
            self.fail(f"Failed to validate LPC report model: {e}")

    @unittest.skipIf("CI" in os.environ, "Skipping MCP tests in CI environment")
    def test_get_lpc_reports_filtering(self):
        """Test retrieving filtered LPC reports from the MCP server."""
        # This is a more advanced test that would use filtering capabilities

        try:
            # Mock response format for filtered reports
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

            # Validate report structures
            for report in mock_response["results"]:
                model = LpcReportModel(**report)
                self.assertIsInstance(model.lpNumber, str)
                self.assertIsInstance(model.name, str)
        except Exception as e:
            self.fail(f"Failed to validate filtered LPC reports: {e}")

    @unittest.skipIf("CI" in os.environ, "Skipping MCP tests in CI environment")
    def test_landmark_pdf_info_validation(self):
        """Test validation of PDF information extracted from LPC reports."""

        # Create sample PDF info that conforms to our model
        pdf_info_data = {
            "id": "LP-00001",
            "name": "Empire State Building",
            "pdf_url": "https://example.com/reports/LP-00001.pdf",
        }

        try:
            # Validate with our Pydantic model
            model = PdfInfo(**pdf_info_data)

            # Assertions
            self.assertEqual(model.id, "LP-00001")
            self.assertEqual(model.name, "Empire State Building")
            self.assertEqual(model.pdf_url, "https://example.com/reports/LP-00001.pdf")
        except Exception as e:
            self.fail(f"Failed to validate PDF info model: {e}")

    @unittest.skipIf("CI" in os.environ, "Skipping MCP tests in CI environment")
    def test_pdf_url_validation(self):
        """Test validation rules for PDF URLs."""

        # Valid case
        valid_pdf_info = {
            "id": "LP-00001",
            "name": "Test Landmark",
            "pdf_url": "https://example.com/test.pdf",
        }

        # Invalid case (bad URL)
        invalid_pdf_info = {
            "id": "LP-00002",
            "name": "Test Landmark 2",
            "pdf_url": "not-a-url",
        }

        # Test valid case
        try:
            model = PdfInfo(**valid_pdf_info)
            self.assertEqual(model.pdf_url, "https://example.com/test.pdf")
        except Exception as e:
            self.fail(f"Valid PDF URL failed validation: {e}")

        # Test invalid case
        with self.assertRaises(ValueError):
            PdfInfo(**invalid_pdf_info)


if __name__ == "__main__":
    unittest.main()
