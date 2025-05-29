"""
Mock data for fetch_landmark_reports.py script tests.

This module provides mock data and fixtures for testing the LandmarkReportProcessor
and related functionality without requiring external API calls.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import Mock

from nyc_landmarks.models.landmark_models import (
    LpcReportModel,
    LpcReportResponse,
)


def get_mock_lpc_reports() -> List[LpcReportModel]:
    """
    Get mock LPC report models for testing.

    Returns:
        List of LpcReportModel objects with diverse test data
    """
    return [
        LpcReportModel(
            name="Brooklyn Bridge",
            lpNumber="LP-00001",
            lpcId="00001",
            objectType="Individual Landmark",
            architect="John Augustus Roebling",
            style="Gothic Revival",
            street="Brooklyn Bridge",
            borough="Manhattan",
            dateDesignated="1967-08-24",
            photoStatus=True,
            mapStatus=True,
            neighborhood="Financial District",
            zipCode="10038",
            photoUrl="https://example.com/photos/LP-00001.jpg",
            pdfReportUrl="https://example.com/pdfs/LP-00001.pdf",
        ),
        LpcReportModel(
            name="Central Park",
            lpNumber="LP-00002",
            lpcId="00002",
            objectType="Scenic Landmark",
            architect="Frederick Law Olmsted",
            style="English Landscape",
            street="Central Park",
            borough="Manhattan",
            dateDesignated="1974-05-23",
            photoStatus=True,
            mapStatus=True,
            neighborhood="Upper East Side",
            zipCode="10021",
            photoUrl="https://example.com/photos/LP-00002.jpg",
            pdfReportUrl="https://example.com/pdfs/LP-00002.pdf",
        ),
        LpcReportModel(
            name="Brooklyn Historic District",
            lpNumber="LP-00003",
            lpcId="00003",
            objectType="Historic District",
            architect="Various",
            style="Victorian",
            street="Multiple Streets",
            borough="Brooklyn",
            dateDesignated="1983-11-15",
            photoStatus=False,
            mapStatus=True,
            neighborhood="DUMBO",
            zipCode="11201",
            photoUrl=None,  # No photo URL
            pdfReportUrl="https://example.com/pdfs/LP-00003.pdf",
        ),
        LpcReportModel(
            name="Queens Test Landmark",
            lpNumber="LP-00004",
            lpcId="00004",
            objectType="Individual Landmark",
            architect="Unknown",
            style="Art Deco",
            street="123 Test Street",
            borough="Queens",
            dateDesignated="1995-03-10",
            photoStatus=True,
            mapStatus=False,
            neighborhood="Astoria",
            zipCode="11105",
            photoUrl="https://example.com/photos/LP-00004.jpg",
            pdfReportUrl=None,  # No PDF URL
        ),
        LpcReportModel(
            name="Staten Island Lighthouse",
            lpNumber="LP-00005",
            lpcId="00005",
            objectType="Individual Landmark",
            architect="Unknown",
            style="Colonial",
            street="Lighthouse Avenue",
            borough="Staten Island",
            dateDesignated="2001-07-18",
            photoStatus=True,
            mapStatus=True,
            neighborhood="St. George",
            zipCode="10301",
            photoUrl="https://example.com/photos/LP-00005.jpg",
            pdfReportUrl="https://example.com/pdfs/LP-00005.pdf",
        ),
    ]


def get_mock_lpc_report_response(
    page: int = 1,
    limit: int = 50,
    total: int = 5,
    reports: Optional[List[LpcReportModel]] = None,
) -> LpcReportResponse:
    """
    Get mock LPC report response for pagination testing.

    Args:
        page: Page number
        limit: Items per page
        total: Total items available
        reports: List of reports (defaults to mock reports)

    Returns:
        LpcReportResponse object
    """
    if reports is None:
        reports = get_mock_lpc_reports()

    # Calculate pagination values
    from_index = (page - 1) * limit
    to_index = min(from_index + limit, total)

    return LpcReportResponse(
        total=total,
        page=page,
        limit=limit,
        **{"from": from_index + 1},  # API uses 1-based indexing
        to=to_index,
        results=reports[from_index:to_index],
    )


def get_mock_filtered_reports(filter_type: str) -> List[LpcReportModel]:
    """
    Get mock reports filtered by specific criteria.

    Args:
        filter_type: Type of filter ('manhattan', 'brooklyn', 'individual', 'historic_district')

    Returns:
        Filtered list of LpcReportModel objects
    """
    all_reports = get_mock_lpc_reports()

    if filter_type == "manhattan":
        return [r for r in all_reports if r.borough == "Manhattan"]
    elif filter_type == "brooklyn":
        return [r for r in all_reports if r.borough == "Brooklyn"]
    elif filter_type == "individual":
        return [r for r in all_reports if r.objectType == "Individual Landmark"]
    elif filter_type == "historic_district":
        return [r for r in all_reports if r.objectType == "Historic District"]
    else:
        return all_reports


def get_mock_pdf_info() -> List[Dict[str, str]]:
    """
    Get mock PDF information extracted from reports.

    Returns:
        List of dictionaries with PDF information
    """
    return [
        {
            "id": "LP-00001",
            "name": "Brooklyn Bridge",
            "pdf_url": "https://example.com/pdfs/LP-00001.pdf",
            "borough": "Manhattan",
            "object_type": "Individual Landmark",
        },
        {
            "id": "LP-00002",
            "name": "Central Park",
            "pdf_url": "https://example.com/pdfs/LP-00002.pdf",
            "borough": "Manhattan",
            "object_type": "Scenic Landmark",
        },
        {
            "id": "LP-00003",
            "name": "Brooklyn Historic District",
            "pdf_url": "https://example.com/pdfs/LP-00003.pdf",
            "borough": "Brooklyn",
            "object_type": "Historic District",
        },
        {
            "id": "LP-00005",
            "name": "Staten Island Lighthouse",
            "pdf_url": "https://example.com/pdfs/LP-00005.pdf",
            "borough": "Staten Island",
            "object_type": "Individual Landmark",
        },
    ]


def create_mock_db_client_for_processor() -> Mock:
    """
    Create a mock DbClient specifically for LandmarkReportProcessor testing.

    Returns:
        Mock DbClient with configured methods
    """
    mock_client = Mock()

    # Mock get_total_record_count
    mock_client.get_total_record_count.return_value = 100

    # Mock get_lpc_reports with pagination simulation
    def mock_get_lpc_reports(
        page: int = 1,
        limit: int = 50,
        borough: Optional[str] = None,
        object_type: Optional[str] = None,
        neighborhood: Optional[str] = None,
        search_text: Optional[str] = None,
        parent_style_list: Optional[List[str]] = None,
        sort_column: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> LpcReportResponse:
        """Mock implementation of get_lpc_reports with filtering."""
        all_reports = get_mock_lpc_reports()

        # Apply filters
        filtered_reports = all_reports
        if borough:
            filtered_reports = [r for r in filtered_reports if r.borough == borough]
        if object_type:
            filtered_reports = [
                r for r in filtered_reports if r.objectType == object_type
            ]
        if neighborhood:
            filtered_reports = [
                r for r in filtered_reports if r.neighborhood == neighborhood
            ]
        if search_text:
            filtered_reports = [
                r for r in filtered_reports if search_text.lower() in r.name.lower()
            ]

        # Calculate pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        page_reports = filtered_reports[start_idx:end_idx]

        return LpcReportResponse(
            total=len(filtered_reports),
            page=page,
            limit=limit,
            **{"from": start_idx + 1},
            to=min(end_idx, len(filtered_reports)),
            results=page_reports,
        )

    # Use side_effect for proper mock behavior
    mock_client.get_lpc_reports.side_effect = mock_get_lpc_reports
    return mock_client


def create_mock_db_client_with_errors() -> Mock:
    """
    Create a mock DbClient that raises errors for testing error handling.

    Returns:
        Mock DbClient that raises exceptions
    """
    mock_client = Mock()

    # Mock methods that raise exceptions
    mock_client.get_total_record_count.side_effect = Exception(
        "Database connection error"
    )
    mock_client.get_lpc_reports.side_effect = Exception("API request failed")

    return mock_client


def create_mock_db_client_empty() -> Mock:
    """
    Create a mock DbClient that returns empty results.

    Returns:
        Mock DbClient with empty responses
    """
    mock_client = Mock()

    # Mock empty responses
    mock_client.get_total_record_count.return_value = 0
    mock_client.get_lpc_reports.return_value = LpcReportResponse(
        total=0,
        page=1,
        limit=50,
        **{"from": 0},
        to=0,
        results=[],
    )

    return mock_client


def get_mock_processing_metrics() -> Dict[str, Any]:
    """
    Get mock processing metrics for testing.

    Returns:
        Dictionary with processing metrics
    """
    return {
        "total_records": 100,
        "processed_records": 5,
        "records_with_pdfs": 4,
        "processing_time": 2.5,
        "errors_encountered": [],
        "pages_processed": 1,
    }


def get_mock_output_files() -> Dict[str, str]:
    """
    Get mock output file paths for testing.

    Returns:
        Dictionary mapping file types to paths
    """
    return {
        "landmark_reports": "logs/landmark_reports_20250526_180000.json",
        "pdf_urls": "logs/pdf_urls_20250526_180000.json",
    }


# Helper functions for specific test scenarios


def get_manhattan_only_reports() -> List[LpcReportModel]:
    """Get reports filtered for Manhattan only."""
    return get_mock_filtered_reports("manhattan")


def get_individual_landmarks_only() -> List[LpcReportModel]:
    """Get reports filtered for Individual Landmarks only."""
    return get_mock_filtered_reports("individual")


def get_reports_with_search_bridge() -> List[LpcReportModel]:
    """Get reports that match 'bridge' search term."""
    all_reports = get_mock_lpc_reports()
    return [r for r in all_reports if "bridge" in r.name.lower()]


def create_mock_pinecone_db_for_pdf_index() -> Mock:
    """
    Create a mock PineconeDB instance specifically for PDF index testing.

    Returns:
        Mock PineconeDB with PDF vector query behavior
    """
    mock_db = Mock()

    # Mock list_vectors behavior for different landmarks
    def mock_list_vectors(
        landmark_id: Optional[str] = None,
        source_type: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Mock list_vectors that returns results based on landmark_id."""
        # Return vectors for specific landmarks that should have PDFs
        if landmark_id in ["LP-00001", "LP-00002", "LP-00005"] and source_type == "pdf":
            return [
                {
                    "id": f"pdf-{landmark_id}-chunk-0",
                    "metadata": {
                        "landmark_id": landmark_id,
                        "source_type": "pdf",
                        "chunk_index": 0,
                    },
                }
            ]

        return []  # No matches for other landmarks or source types

    mock_db.list_vectors.side_effect = mock_list_vectors

    # Mock query behavior for different landmarks
    def mock_query_vectors(
        filter_dict: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Mock query that returns results based on landmark_id filter."""
        if filter_dict and "landmark_id" in filter_dict:
            landmark_id = filter_dict["landmark_id"]
            source_type = filter_dict.get("source_type", "pdf")

            # Return vectors for specific landmarks that should have PDFs
            if (
                landmark_id in ["LP-00001", "LP-00002", "LP-00005"]
                and source_type == "pdf"
            ):
                return [
                    {
                        "id": f"pdf-{landmark_id}-chunk-0",
                        "score": 1.0,
                        "metadata": {
                            "landmark_id": landmark_id,
                            "source_type": "pdf",
                            "chunk_index": 0,
                        },
                    }
                ]

        return []  # No matches for other landmarks or source types

    mock_db.query_vectors.side_effect = mock_query_vectors
    return mock_db


def create_mock_pinecone_db_pdf_index_empty() -> Mock:
    """
    Create a mock PineconeDB instance that returns no PDF vectors.

    Returns:
        Mock PineconeDB that always returns empty results
    """
    mock_db = Mock()
    mock_db.query_vectors.return_value = []
    return mock_db


def create_mock_pinecone_db_pdf_index_errors() -> Mock:
    """
    Create a mock PineconeDB instance that raises errors during PDF index queries.

    Returns:
        Mock PineconeDB that raises exceptions
    """
    mock_db = Mock()
    mock_db.list_vectors.side_effect = Exception("PDF index query failed")
    mock_db.query_vectors.side_effect = Exception("PDF index query failed")
    return mock_db
