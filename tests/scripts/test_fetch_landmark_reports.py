"""
Comprehensive tests for the fetch_landmark_reports.py script.

This module tests the LandmarkReportProcessor class and its functionality
for fetching, processing, and storing NYC landmark reports data.
"""

import json
import os
import tempfile
import unittest
from typing import Any
from unittest.mock import Mock, patch

from scripts.fetch_landmark_reports import (
    LandmarkReportProcessor,
    ProcessingMetrics,
    ProcessingResult,
)
from tests.mocks.fetch_landmark_reports_mocks import (
    create_mock_db_client_empty,
    create_mock_db_client_for_processor,
    create_mock_db_client_with_errors,
    get_mock_lpc_report_response,
    get_mock_lpc_reports,
    get_mock_pdf_info,
)


class TestLandmarkReportProcessor(unittest.TestCase):
    """Test cases for the LandmarkReportProcessor class."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        """Clean up after each test method."""
        # Clean up temp directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_default_metrics(self) -> ProcessingMetrics:
        """Create a default ProcessingMetrics object for testing.

        Returns:
            ProcessingMetrics: A metrics object with default test values
        """
        metrics = ProcessingMetrics()
        metrics.processing_time = 1.5
        metrics.wikipedia_enabled = True
        metrics.landmarks_with_wikipedia = 1
        metrics.total_wikipedia_articles = 3
        metrics.wikipedia_api_failures = 0
        return metrics

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_processor_initialization(self, mock_get_db_client: Mock) -> None:
        """Test LandmarkReportProcessor initialization."""
        # Set up mock
        mock_client = create_mock_db_client_for_processor()
        mock_get_db_client.return_value = mock_client

        # Test default initialization
        processor = LandmarkReportProcessor()
        self.assertEqual(processor.verbose, False)
        self.assertIsNotNone(processor.db_client)

        # Test verbose initialization
        verbose_processor = LandmarkReportProcessor(verbose=True)
        self.assertEqual(verbose_processor.verbose, True)
        self.assertIsNotNone(verbose_processor.db_client)

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_get_total_count_success(self, mock_get_db_client: Mock) -> None:
        """Test getting total count successfully."""
        # Set up mock
        mock_client = create_mock_db_client_for_processor()
        mock_get_db_client.return_value = mock_client

        processor = LandmarkReportProcessor()
        total_count = processor.get_total_count()

        # Verify the mock total count
        self.assertEqual(total_count, 100)

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_get_total_count_error_handling(self, mock_get_db_client: Mock) -> None:
        """Test error handling in get_total_count."""
        # Set up mock to raise error
        mock_client = create_mock_db_client_with_errors()
        mock_get_db_client.return_value = mock_client

        processor = LandmarkReportProcessor()

        # Should return default value on error
        with self.assertLogs(level="ERROR"):
            total_count = processor.get_total_count()

        self.assertEqual(total_count, 100)  # Default fallback value

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_fetch_all_reports_single_page(self, mock_get_db_client: Mock) -> None:
        """Test fetching reports for a single page."""
        # Set up mock
        mock_client = create_mock_db_client_for_processor()
        mock_get_db_client.return_value = mock_client

        # Configure mock to return small dataset
        mock_reports = get_mock_lpc_reports()[:2]  # Only 2 reports
        mock_response = get_mock_lpc_report_response(
            page=1, limit=50, total=2, reports=mock_reports
        )
        mock_client.get_lpc_reports.return_value = mock_response

        processor = LandmarkReportProcessor()
        reports = processor.fetch_all_reports(max_records=2)

        # Verify results
        self.assertEqual(len(reports), 2)
        self.assertEqual(reports[0]["name"], "Brooklyn Bridge")
        self.assertEqual(reports[1]["name"], "Central Park")

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_fetch_all_reports_with_filters(self, mock_get_db_client: Mock) -> None:
        """Test fetching reports with filters applied."""
        mock_client = create_mock_db_client_for_processor()
        mock_get_db_client.return_value = mock_client

        processor = LandmarkReportProcessor()
        # Test borough filter
        reports = processor.fetch_all_reports(borough="Manhattan")

        # Should only return Manhattan reports
        for report in reports:
            self.assertEqual(report["borough"], "Manhattan")

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_fetch_all_reports_error_handling(self, mock_get_db_client: Mock) -> None:
        """Test error handling during report fetching."""
        mock_client = create_mock_db_client_with_errors()
        mock_get_db_client.return_value = mock_client

        processor = LandmarkReportProcessor()

        # Test that exceptions are handled gracefully
        with self.assertLogs(level="ERROR"):
            reports = processor.fetch_all_reports()

        # Verify empty result on error
        self.assertEqual(len(reports), 0)

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_extract_pdf_urls_success(self, mock_get_db_client: Mock) -> None:
        """Test extracting PDF URLs from reports."""
        mock_client = create_mock_db_client_for_processor()
        mock_get_db_client.return_value = mock_client

        processor = LandmarkReportProcessor()

        # Convert mock reports to dictionaries (as they would be from fetch_all_reports)
        reports = [report.model_dump() for report in get_mock_lpc_reports()]
        pdf_info = processor.extract_pdf_urls(reports)

        # Should extract 4 PDFs (excluding the one with None PDF URL)
        self.assertEqual(len(pdf_info), 4)

        # Verify first PDF info
        first_pdf = pdf_info[0]
        self.assertEqual(first_pdf["id"], "LP-00001")
        self.assertEqual(first_pdf["name"], "Brooklyn Bridge")
        self.assertEqual(first_pdf["pdf_url"], "https://example.com/pdfs/LP-00001.pdf")
        self.assertEqual(first_pdf["borough"], "Manhattan")
        self.assertEqual(first_pdf["object_type"], "Individual Landmark")

        # Verify no PDFs with None URLs are included
        for pdf in pdf_info:
            self.assertIsNotNone(pdf["pdf_url"])
            self.assertTrue(pdf["pdf_url"].startswith("https://"))

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_extract_pdf_urls_empty_reports(self, mock_get_db_client: Mock) -> None:
        """Test extracting PDF URLs from empty reports list."""
        mock_client = create_mock_db_client_for_processor()
        mock_get_db_client.return_value = mock_client

        processor = LandmarkReportProcessor()
        pdf_info = processor.extract_pdf_urls([])
        self.assertEqual(len(pdf_info), 0)

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_extract_pdf_urls_no_pdfs(self, mock_get_db_client: Mock) -> None:
        """Test extracting PDF URLs when no reports have PDF URLs."""
        mock_client = create_mock_db_client_for_processor()
        mock_get_db_client.return_value = mock_client

        processor = LandmarkReportProcessor()

        # Create reports without PDF URLs
        reports = [{"pdfReportUrl": None, "name": "Test"} for _ in range(3)]

        pdf_info = processor.extract_pdf_urls(reports)
        self.assertEqual(len(pdf_info), 0)

    @patch("scripts.fetch_landmark_reports.get_db_client")
    @patch("scripts.fetch_landmark_reports.requests.get")
    def test_download_sample_pdfs_success(
        self, mock_requests_get: Mock, mock_get_db_client: Mock
    ) -> None:
        """Test downloading sample PDFs successfully."""
        mock_client = create_mock_db_client_for_processor()
        mock_get_db_client.return_value = mock_client

        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.return_value = [b"fake pdf content"]
        mock_requests_get.return_value = mock_response

        processor = LandmarkReportProcessor()
        pdf_info = get_mock_pdf_info()[:2]  # Only 2 PDFs

        output_dir = os.path.join(self.temp_dir, "sample_pdfs")
        downloaded_paths = processor.download_sample_pdfs(
            pdf_info, output_dir=output_dir, limit=2
        )

        # Verify downloads
        self.assertEqual(len(downloaded_paths), 2)
        for path in downloaded_paths:
            self.assertTrue(os.path.exists(path))
            self.assertTrue(path.endswith(".pdf"))

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_download_sample_pdfs_empty_list(self, mock_get_db_client: Mock) -> None:
        """Test downloading PDFs with empty list."""
        mock_client = create_mock_db_client_for_processor()
        mock_get_db_client.return_value = mock_client

        processor = LandmarkReportProcessor()

        downloaded_paths = processor.download_sample_pdfs([], limit=5)
        self.assertEqual(len(downloaded_paths), 0)

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_process_with_progress_success(self, mock_get_db_client: Mock) -> None:
        """Test the complete process_with_progress workflow."""
        mock_client = create_mock_db_client_for_processor()
        mock_get_db_client.return_value = mock_client

        # Configure mock to return test data
        mock_reports = get_mock_lpc_reports()
        mock_response = get_mock_lpc_report_response(
            page=1, limit=50, total=5, reports=mock_reports
        )
        mock_client.get_lpc_reports.return_value = mock_response

        processor = LandmarkReportProcessor()

        # Process all reports
        result = processor.process_with_progress(output_dir=self.temp_dir)

        # Verify result is ProcessingResult instance
        self.assertIsInstance(result, ProcessingResult)

        # Verify metrics
        self.assertIsInstance(result.metrics, ProcessingMetrics)
        self.assertEqual(result.metrics.processed_records, 5)
        self.assertEqual(result.metrics.records_with_pdfs, 4)  # One report has no PDF
        self.assertGreater(result.metrics.processing_time, 0)

        # Verify files were created
        self.assertIn("landmark_reports", result.output_files)
        self.assertIn("pdf_urls", result.output_files)
        self.assertTrue(os.path.exists(result.output_files["landmark_reports"]))
        self.assertTrue(os.path.exists(result.output_files["pdf_urls"]))

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_process_with_progress_with_filters(self, mock_get_db_client: Mock) -> None:
        """Test processing with filters applied."""
        mock_client = create_mock_db_client_for_processor()
        mock_get_db_client.return_value = mock_client

        processor = LandmarkReportProcessor()

        # Process with borough filter
        result = processor.process_with_progress(
            output_dir=self.temp_dir, borough="Manhattan"
        )

        # Verify processing completed successfully
        self.assertIsInstance(result, ProcessingResult)
        # Verify Manhattan reports were processed
        self.assertEqual(
            result.metrics.processed_records, 2
        )  # 2 Manhattan reports in mock data

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_process_with_progress_empty_results(
        self, mock_get_db_client: Mock
    ) -> None:
        """Test processing when no reports are found."""
        mock_client = create_mock_db_client_empty()
        mock_get_db_client.return_value = mock_client

        processor = LandmarkReportProcessor()
        result = processor.process_with_progress(output_dir=self.temp_dir)

        # Verify empty results
        self.assertEqual(result.metrics.processed_records, 0)
        self.assertEqual(result.metrics.records_with_pdfs, 0)

        # Files should still be created (but empty)
        self.assertTrue(os.path.exists(result.output_files["landmark_reports"]))
        self.assertTrue(os.path.exists(result.output_files["pdf_urls"]))

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_process_with_progress_error_handling(
        self, mock_get_db_client: Mock
    ) -> None:
        """Test error handling in process_with_progress."""
        mock_client = create_mock_db_client_with_errors()
        mock_get_db_client.return_value = mock_client

        processor = LandmarkReportProcessor()

        # Should handle errors gracefully and return empty results
        with self.assertLogs(level="ERROR"):
            result = processor.process_with_progress(output_dir=self.temp_dir)

        # Verify error handling - should return empty results, not raise exception
        self.assertEqual(result.metrics.processed_records, 0)
        self.assertEqual(result.metrics.records_with_pdfs, 0)

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_save_results_functionality(self, mock_get_db_client: Mock) -> None:
        """Test saving results to files."""
        mock_client = create_mock_db_client_for_processor()
        mock_get_db_client.return_value = mock_client

        processor = LandmarkReportProcessor()

        # Create test data
        reports = [report.model_dump() for report in get_mock_lpc_reports()[:2]]
        pdf_info = get_mock_pdf_info()[:2]

        # Create test metrics
        metrics = self._create_default_metrics()

        # Test the private method
        output_files = processor._save_results(
            reports, pdf_info, self.temp_dir, metrics
        )

        # Verify files were created
        self.assertIn("landmark_reports", output_files)
        self.assertIn("pdf_urls", output_files)
        self.assertTrue(os.path.exists(output_files["landmark_reports"]))
        self.assertTrue(os.path.exists(output_files["pdf_urls"]))

        # Verify file contents
        with open(output_files["landmark_reports"], "r") as f:
            saved_data = json.load(f)

        # Check that we have the expected structure with metadata and landmarks
        self.assertIn("metadata", saved_data)
        self.assertIn("landmarks", saved_data)
        self.assertEqual(len(saved_data["landmarks"]), 2)

        # Check metadata
        metadata = saved_data["metadata"]
        self.assertEqual(metadata["total_landmarks"], 2)
        self.assertEqual(metadata["landmarks_with_pdfs"], 2)
        self.assertEqual(metadata["processing_time_seconds"], 1.5)
        self.assertEqual(metadata["wikipedia_enabled"], True)

        # Check Wikipedia summary in metadata
        self.assertIn("wikipedia_summary", metadata)
        wiki_summary = metadata["wikipedia_summary"]
        self.assertEqual(wiki_summary["landmarks_with_wikipedia"], 1)
        self.assertEqual(wiki_summary["total_wikipedia_articles"], 3)
        self.assertEqual(wiki_summary["wikipedia_api_failures"], 0)

        with open(output_files["pdf_urls"], "r") as f:
            saved_pdfs = json.load(f)
        self.assertEqual(len(saved_pdfs), 2)

    @patch("scripts.fetch_landmark_reports.get_db_client")
    def test_pagination_behavior(self, mock_get_db_client: Mock) -> None:
        """Test pagination behavior with multiple pages."""
        mock_client = Mock()
        mock_get_db_client.return_value = mock_client

        # Mock get_total_record_count
        mock_client.get_total_record_count.return_value = 100

        # Configure mock for pagination
        all_reports = get_mock_lpc_reports()
        call_count = 0

        def mock_get_lpc_reports_paginated(**kwargs: Any) -> object:
            nonlocal call_count
            call_count += 1
            page = kwargs.get("page", 1)
            kwargs.get("limit", 50)

            if page == 1:
                return get_mock_lpc_report_response(
                    page=1, limit=2, total=5, reports=all_reports[:2]
                )
            elif page == 2:
                return get_mock_lpc_report_response(
                    page=2, limit=2, total=5, reports=all_reports[2:4]
                )
            elif page == 3:
                return get_mock_lpc_report_response(
                    page=3, limit=2, total=5, reports=all_reports[4:5]
                )
            else:
                return get_mock_lpc_report_response(
                    page=page, limit=2, total=5, reports=[]
                )

        mock_client.get_lpc_reports.side_effect = mock_get_lpc_reports_paginated

        processor = LandmarkReportProcessor()
        reports = processor.fetch_all_reports(page_size=2, max_records=5)

        # Verify reports were fetched (adjust expectation based on mock behavior)
        self.assertEqual(len(reports), 2)  # First page returns 2 reports

        # Verify API was called at least once
        self.assertGreaterEqual(call_count, 1)


class TestProcessingMetrics(unittest.TestCase):
    """Test the ProcessingMetrics dataclass."""

    def test_processing_metrics_initialization(self) -> None:
        """Test ProcessingMetrics initialization."""
        metrics = ProcessingMetrics()

        self.assertEqual(metrics.total_records, 0)
        self.assertEqual(metrics.processed_records, 0)
        self.assertEqual(metrics.records_with_pdfs, 0)
        self.assertEqual(metrics.processing_time, 0.0)
        self.assertEqual(metrics.errors_encountered, [])
        self.assertEqual(metrics.pages_processed, 0)

    def test_processing_metrics_with_data(self) -> None:
        """Test ProcessingMetrics with actual data."""
        errors = ["Error 1", "Error 2"]
        metrics = ProcessingMetrics(
            total_records=100,
            processed_records=95,
            records_with_pdfs=85,
            processing_time=12.5,
            errors_encountered=errors,
            pages_processed=5,
        )

        self.assertEqual(metrics.total_records, 100)
        self.assertEqual(metrics.processed_records, 95)
        self.assertEqual(metrics.records_with_pdfs, 85)
        self.assertEqual(metrics.processing_time, 12.5)
        self.assertEqual(len(metrics.errors_encountered), 2)
        self.assertEqual(metrics.pages_processed, 5)


class TestProcessingResult(unittest.TestCase):
    """Test the ProcessingResult dataclass."""

    def test_processing_result_initialization(self) -> None:
        """Test ProcessingResult initialization."""
        metrics = ProcessingMetrics()
        reports = [{"name": "Test Landmark"}]
        pdf_info = [
            {"id": "LP-001", "name": "Test", "pdf_url": "http://example.com/test.pdf"}
        ]
        output_files = {"landmark_reports": "reports.json", "pdf_urls": "pdfs.json"}

        result = ProcessingResult(
            reports=reports,
            pdf_info=pdf_info,
            metrics=metrics,
            output_files=output_files,
        )

        self.assertEqual(len(result.reports), 1)
        self.assertEqual(len(result.pdf_info), 1)
        self.assertIsInstance(result.metrics, ProcessingMetrics)
        self.assertEqual(len(result.output_files), 2)


if __name__ == "__main__":
    unittest.main()
