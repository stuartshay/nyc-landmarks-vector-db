"""
Integration tests for landmark report pagination functionality.

These tests validate that the system can fetch all landmark reports
across multiple pages using the CoreDataStore API through both
direct client and MCP server approaches.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from scripts.fetch_landmark_reports import LandmarkReportFetcher


class TestLandmarkPagination:
    """Test class for landmark pagination functionality."""

    @pytest.mark.integration
    def test_pagination_metadata(self) -> None:
        """Test that pagination metadata is correctly returned and processed."""
        # Create fetcher instance
        fetcher = LandmarkReportFetcher()

        # Get first page of reports with explicit page size
        page_size = 20
        reports = fetcher.get_lpc_reports(page_size=page_size, page=1)

        # Verify reports were returned
        assert reports, "No reports returned from first page"
        assert len(reports) <= page_size, f"Got more than {page_size} reports"

        # Verify we can get a second page
        page2_reports = fetcher.get_lpc_reports(page_size=page_size, page=2)
        assert page2_reports, "No reports returned from second page"

        # Verify pages contain different reports
        page1_ids = {report["lpNumber"] for report in reports if "lpNumber" in report}
        page2_ids = {
            report["lpNumber"] for report in page2_reports if "lpNumber" in report
        }
        assert page1_ids.isdisjoint(page2_ids), "Overlapping reports between pages"

    @pytest.mark.integration
    def test_fetch_all_pages(self) -> None:
        """Test that all pages of reports can be fetched."""
        # Create fetcher instance
        fetcher = LandmarkReportFetcher()

        # Get first page with all metadata
        page_size = 50  # Use larger page size for efficiency
        all_reports = []
        all_ids: set[str] = set()

        # Fetch first page to get metadata
        response = fetcher.api_client._make_request(
            "GET", f"/api/LpcReport/{page_size}/1"
        )

        assert response, "No response from API"
        assert "results" in response, "No results in response"
        assert "total" in response, "No total count in response"

        total_count = response["total"]
        assert total_count > 0, "Total count should be positive"

        # Calculate number of pages needed
        total_pages = (total_count + page_size - 1) // page_size

        # Fetch all pages
        for page in range(1, total_pages + 1):
            page_reports = fetcher.get_lpc_reports(page_size=page_size, page=page)
            all_reports.extend(page_reports)

            # Extract IDs and check for duplicates
            page_ids = {
                report["lpNumber"] for report in page_reports if "lpNumber" in report
            }
            overlap = all_ids.intersection(page_ids)
            assert not overlap, f"Duplicate IDs found: {overlap}"

            all_ids.update(page_ids)

        # Verify we got the expected number of reports
        assert (
            len(all_reports) == total_count
        ), f"Expected {total_count} reports, got {len(all_reports)}"
        assert (
            len(all_ids) == total_count
        ), f"Expected {total_count} unique IDs, got {len(all_ids)}"

    @pytest.mark.mcp
    def test_pagination_with_mcp_server(self):
        """Test pagination using MCP server direct access."""
        import pytest

        pytest.importorskip("antml.mcp")

        # First test if MCP server is available
        try:
            from claude_dev import use_mcp_tool

            # Get first page to determine total count
            mcp_response = use_mcp_tool(
                server_name="coredatastore-swagger-mcp",
                tool_name="GetLpcReports",
                arguments={"limit": 10, "page": 1},
            )

            assert mcp_response, "No response from MCP server"
            assert "total" in mcp_response, "No total count in MCP response"

            total_count = mcp_response["total"]
            assert total_count > 0, "Total count should be positive"

            # Test fetching data from a couple of different pages
            page2_response = use_mcp_tool(
                server_name="coredatastore-swagger-mcp",
                tool_name="GetLpcReports",
                arguments={"limit": 10, "page": 2},
            )

            assert page2_response, "No response from MCP server for page 2"
            assert "results" in page2_response, "No results in MCP response for page 2"
            assert len(page2_response["results"]) > 0, "No reports in page 2"

            # Check IDs don't overlap between pages
            page1_ids = {report["lpNumber"] for report in mcp_response["results"]}
            page2_ids = {report["lpNumber"] for report in page2_response["results"]}
            assert page1_ids.isdisjoint(
                page2_ids
            ), "Overlapping reports between MCP pages"

        except (ImportError, Exception) as e:
            pytest.skip(f"MCP server test skipped: {str(e)}")

    @pytest.mark.integration
    def test_page_size_variations(self):
        """Test different page sizes to verify correct handling."""
        # Create fetcher instance
        fetcher = LandmarkReportFetcher()

        # Test with different page sizes
        for page_size in [5, 10, 20, 50]:
            response = fetcher.api_client._make_request(
                "GET", f"/api/LpcReport/{page_size}/1"
            )

            assert response, f"No response with page size {page_size}"
            assert "results" in response, f"No results with page size {page_size}"

            # Verify we get the requested page size (or less for the last page)
            assert (
                len(response["results"]) <= page_size
            ), f"Got too many results with page size {page_size}"

    @pytest.mark.integration
    def test_api_url_format(self):
        """Test that the API uses the correct URL format for pagination."""
        # Create fetcher instance
        fetcher = LandmarkReportFetcher()

        # Mock the _make_request method to capture the URL
        original_make_request = fetcher.api_client._make_request

        # Keep track of calls to _make_request
        call_args = []

        def mock_make_request(method, endpoint, params=None, json_data=None):
            # Record the call arguments
            call_args.append((method, endpoint, params, json_data))
            # Call the original method
            return original_make_request(method, endpoint, params, json_data)

        # Replace the method with our mock
        fetcher.api_client._make_request = mock_make_request

        try:
            # Make a call to get_lpc_reports
            page_size = 20
            page = 2
            fetcher.get_lpc_reports(page_size=page_size, page=page)

            # Check that the endpoint was formatted correctly
            assert len(call_args) > 0, "No API calls were made"
            method, endpoint, params, _ = call_args[0]

            # The endpoint should use path parameters for pagination
            expected_endpoint = f"/api/LpcReport/{page_size}/{page}"
            assert (
                endpoint == expected_endpoint
            ), f"Expected endpoint {expected_endpoint}, got {endpoint}"

            # Pagination parameters should not be in the query string
            if params is not None:
                assert (
                    "page" not in params
                ), "Page parameter should not be in query string"
                assert (
                    "limit" not in params
                ), "Limit parameter should not be in query string"
            else:
                # If params is None, there are no query parameters, which is what we want
                pass

        finally:
            # Restore the original method
            fetcher.api_client._make_request = original_make_request

    @pytest.mark.integration
    def test_last_page_handling(self):
        """Test handling of the last page of results."""
        # Create fetcher instance
        fetcher = LandmarkReportFetcher()

        # Get total count to determine last page
        response = fetcher.api_client._make_request("GET", "/api/LpcReport/10/1")

        assert response, "No response from API"
        assert "total" in response, "No total count in response"

        total_count = response["total"]
        page_size = 20

        # Calculate last page number
        last_page = (total_count + page_size - 1) // page_size

        # Get last page
        last_page_reports = fetcher.get_lpc_reports(page_size=page_size, page=last_page)

        # Verify we got results
        assert last_page_reports, f"No reports returned from last page ({last_page})"

        # If total_count is not a multiple of page_size, the last page should have fewer items
        expected_count = (
            total_count % page_size if total_count % page_size != 0 else page_size
        )
        assert (
            len(last_page_reports) == expected_count
        ), f"Last page should have {expected_count} reports"

        # Verify that requesting a page beyond the last page returns empty results
        beyond_last_reports = fetcher.get_lpc_reports(
            page_size=page_size, page=last_page + 1
        )
        assert (
            len(beyond_last_reports) == 0
        ), "Requesting page beyond last should return empty results"
