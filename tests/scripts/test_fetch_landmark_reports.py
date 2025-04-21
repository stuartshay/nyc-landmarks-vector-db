"""
Unit tests for the fetch_landmark_reports.py script.

These tests validate the core functionality of the script, including
the API client, report fetching, and PDF URL extraction.
"""

import os

# Add parent directory to path so we can import the script
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from requests.exceptions import RequestException

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from scripts.fetch_landmark_reports import CoreDataStoreClient, LandmarkReportFetcher


class TestCoreDataStoreClient(unittest.TestCase):
    """Test the CoreDataStoreClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.client = CoreDataStoreClient(self.api_key)

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        self.assertEqual(self.client.base_url, "https://api.coredatastore.com")
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertEqual(
            self.client.headers, {"Authorization": f"Bearer {self.api_key}"}
        )

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        client = CoreDataStoreClient()
        self.assertEqual(client.base_url, "https://api.coredatastore.com")
        self.assertIsNone(client.api_key)
        self.assertEqual(client.headers, {})

    @patch("scripts.fetch_landmark_reports.requests.request")
    def test_make_request_success(self, mock_request):
        """Test successful API request."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.content = b'{"key": "value"}'
        mock_response.json.return_value = {"key": "value"}
        mock_request.return_value = mock_response

        # Call method and check result
        result = self.client._make_request("GET", "/test/endpoint", {"param": "value"})
        self.assertEqual(result, {"key": "value"})

        # Verify request was made with correct parameters
        mock_request.assert_called_once_with(
            method="GET",
            url="https://api.coredatastore.com/test/endpoint",
            headers={"Authorization": f"Bearer {self.api_key}"},
            params={"param": "value"},
            json=None,
            timeout=30,
        )

    @patch("scripts.fetch_landmark_reports.requests.request")
    def test_make_request_error(self, mock_request):
        """Test API request with error."""
        # Set up mock to raise an exception
        mock_request.side_effect = RequestException("Test error")

        # Call method and check that exception is raised
        with self.assertRaises(Exception) as context:
            self.client._make_request("GET", "/test/endpoint")

        self.assertIn("Error making API request", str(context.exception))


class TestLandmarkReportFetcher(unittest.TestCase):
    """Test the LandmarkReportFetcher class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.fetcher = LandmarkReportFetcher(self.api_key)

    def test_init(self):
        """Test initialization."""
        self.assertIsInstance(self.fetcher.api_client, CoreDataStoreClient)
        self.assertEqual(self.fetcher.api_client.api_key, self.api_key)

    @patch.object(CoreDataStoreClient, "_make_request")
    def test_get_lpc_reports_success(self, mock_make_request):
        """Test successful retrieval of LPC reports."""
        # Set up mock response
        mock_response = {
            "results": [
                {
                    "lpNumber": "LP-12345",
                    "name": "Test Landmark",
                    "pdfReportUrl": "https://example.com/test.pdf",
                }
            ],
            "totalCount": 1,
            "pageCount": 1,
        }
        mock_make_request.return_value = mock_response

        # Call method and check result
        result = self.fetcher.get_lpc_reports(10, 1)
        self.assertEqual(result, mock_response["results"])

        # Verify request was made with correct parameters
        mock_make_request.assert_called_once_with("GET", "/api/LpcReport/10/1")

    @patch.object(CoreDataStoreClient, "_make_request")
    def test_get_lpc_reports_error(self, mock_make_request):
        """Test error handling when retrieving LPC reports."""
        # Set up mock to raise an exception
        mock_make_request.side_effect = Exception("Test error")

        # Call method and check result
        result = self.fetcher.get_lpc_reports(10, 1)
        self.assertEqual(result, [])

    def test_extract_pdf_urls(self):
        """Test extraction of PDF URLs from reports."""
        # Test data
        reports = [
            {
                "lpNumber": "LP-12345",
                "name": "Test Landmark 1",
                "pdfReportUrl": "https://example.com/test1.pdf",
            },
            {
                "lpNumber": "LP-67890",
                "name": "Test Landmark 2",
                "pdfReportUrl": "https://example.com/test2.pdf",
            },
            {
                "lpNumber": "LP-13579",
                "name": "Test Landmark 3",
                # Missing pdfReportUrl
            },
        ]

        # Call method and check result
        result = self.fetcher.extract_pdf_urls(reports)
        expected = [
            {
                "id": "LP-12345",
                "name": "Test Landmark 1",
                "pdf_url": "https://example.com/test1.pdf",
            },
            {
                "id": "LP-67890",
                "name": "Test Landmark 2",
                "pdf_url": "https://example.com/test2.pdf",
            },
        ]
        self.assertEqual(result, expected)

    @patch("scripts.fetch_landmark_reports.requests.get")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    def test_download_sample_pdf(self, mock_open, mock_get):
        """Test downloading of sample PDFs."""
        # Test data
        pdf_info = [
            {
                "id": "LP-12345",
                "name": "Test Landmark 1",
                "pdf_url": "https://example.com/test1.pdf",
            },
            {
                "id": "LP-67890",
                "name": "Test Landmark 2",
                "pdf_url": "https://example.com/test2.pdf",
            },
        ]

        # Set up mock response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"PDF content"]
        mock_get.return_value = mock_response

        # Create a temporary directory for testing
        output_dir = "test_output_dir"
        os.makedirs(output_dir, exist_ok=True)

        # Call method and check result
        with patch("os.makedirs"):
            result = self.fetcher.download_sample_pdf(pdf_info, output_dir, 1)
            expected = [f"{output_dir}/LP-12345.pdf"]
            self.assertEqual(result, expected)

            # Verify file was opened and written to
            mock_open.assert_called_once_with(f"{output_dir}/LP-12345.pdf", "wb")
            mock_open().write.assert_called_once_with(b"PDF content")

    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch.object(LandmarkReportFetcher, "get_lpc_reports")
    @patch.object(LandmarkReportFetcher, "extract_pdf_urls")
    @patch.object(LandmarkReportFetcher, "download_sample_pdf")
    def test_run(self, mock_download, mock_extract, mock_get, mock_open):
        """Test the main run method."""
        # Set up mock responses
        mock_get.return_value = [
            {
                "lpNumber": "LP-12345",
                "name": "Test Landmark",
                "pdfReportUrl": "https://example.com/test.pdf",
            }
        ]
        mock_extract.return_value = [
            {
                "id": "LP-12345",
                "name": "Test Landmark",
                "pdf_url": "https://example.com/test.pdf",
            }
        ]
        mock_download.return_value = ["sample_pdfs/LP-12345.pdf"]

        # Call method and check result
        result = self.fetcher.run(10, 1, True, 1)
        expected = {"total_reports": 1, "reports_with_pdfs": 1}
        self.assertEqual(result, expected)

        # Verify methods were called with correct parameters
        mock_get.assert_called_once_with(10, 1)
        mock_extract.assert_called_once()
        mock_download.assert_called_once_with(mock_extract.return_value, limit=1)
        self.assertEqual(mock_open.call_count, 2)  # Two files: landmarks and PDF URLs


if __name__ == "__main__":
    unittest.main()
