"""
Integration tests for the LandmarkReportFetcher using the CoreDataStore API.

These tests validate the interaction with the actual CoreDataStore API
through both direct calls and the MCP server.
"""

import os
import sys
import unittest
from pathlib import Path

# Add the project root to the path so we can import modules
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from nyc_landmarks.models.landmark_models import LpcReportModel, PdfInfo
from scripts.fetch_landmark_reports import LandmarkReportFetcher


class TestLandmarkFetcherIntegration(unittest.TestCase):
    """Integration tests for the LandmarkReportFetcher."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        # Use API key from environment or a default test key
        cls.api_key = os.environ.get("COREDATASTORE_API_KEY", "")
        cls.fetcher = LandmarkReportFetcher(cls.api_key)

    def test_get_lpc_reports_returns_data(self):
        """Test that get_lpc_reports returns actual data from the API."""
        # Fetch a small number of reports
        reports = self.fetcher.get_lpc_reports(page_size=5, page=1)

        # Verify we got some data back
        self.assertIsInstance(reports, list)
        self.assertGreater(len(reports), 0)

        # Verify the data structure
        first_report = reports[0]
        self.assertIn("lpNumber", first_report)
        self.assertIn("name", first_report)

        # Test that we can validate with Pydantic model
        try:
            # This will validate the first report against our model
            LpcReportModel(**first_report)
        except Exception as e:
            self.fail(f"Failed to validate report with Pydantic model: {e}")

    def test_extract_pdf_urls_with_real_data(self):
        """Test that extract_pdf_urls correctly processes real data."""
        # Fetch some reports
        reports = self.fetcher.get_lpc_reports(page_size=5, page=1)

        # Extract PDF URLs
        pdf_info = self.fetcher.extract_pdf_urls(reports)

        # Verify we got some data back
        self.assertIsInstance(pdf_info, list)

        # If we got PDFs, verify structure
        if pdf_info:
            first_pdf = pdf_info[0]
            self.assertIn("id", first_pdf)
            self.assertIn("name", first_pdf)
            self.assertIn("pdf_url", first_pdf)

            # Test that we can validate with Pydantic model
            try:
                # This will validate the first PDF info against our model
                PdfInfo(**first_pdf)
            except Exception as e:
                self.fail(f"Failed to validate PDF info with Pydantic model: {e}")

    def test_full_run_integration(self):
        """Test the full run method with minimal settings."""
        # Run the fetcher with minimal settings
        result = self.fetcher.run(page_size=3, pages=1, download_samples=False)

        # Verify we got a result
        self.assertIsInstance(result, dict)
        self.assertIn("total_reports", result)
        self.assertIn("reports_with_pdfs", result)
        self.assertGreaterEqual(result["total_reports"], 0)
        self.assertGreaterEqual(result["reports_with_pdfs"], 0)


# Skip MCP server tests if run directly, as they need to be run in a specific environment
if __name__ == "__main__":
    unittest.main()
