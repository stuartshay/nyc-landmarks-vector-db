"""
Test utilities for providing mock data for offline testing.

This module provides consistent mock data that can be used when
external services are unavailable during testing.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def get_mock_landmark(landmark_id: str) -> Dict[str, Any]:
    """
    Get mock landmark data for a given landmark ID.

    This function provides consistent mock data for landmarks when the API
    is unavailable during testing.

    Args:
        landmark_id: The landmark ID, e.g., "LP-00001"

    Returns:
        A dictionary containing mock landmark data
    """
    # Common mock data for all landmarks
    mock_data = {
        "id": landmark_id,
        "type": "Individual Landmark",
        "designation_date": "1965-10-14",
        "has_photos": True,
        "has_pluto_data": True,
        "processing_date": datetime.now().strftime("%Y-%m-%d"),
        "source_type": "test",
    }

    # Landmark-specific mock data
    landmark_specific = {
        "LP-00001": {
            "name": "Pieter Claesen Wyckoff House",
            "location": "5816 Clarendon Road",
            "borough": "Brooklyn",
            "architect": "Unknown",
            "style": "Dutch Colonial",
            "neighborhood": "Brownsville",
            "pdfReportUrl": "https://cdn.informationcart.com/pdf/0001.pdf",
        },
        "LP-00009": {
            "name": "Irad Hawley House",
            "location": "47 Fifth Avenue",
            "borough": "Manhattan",
            "architect": "Unknown",
            "style": "Italianate",
            "neighborhood": "Greenwich Village",
            "pdfReportUrl": "https://cdn.informationcart.com/pdf/0009.pdf",
        },
        "LP-00042": {
            "name": "Hanover Bank",
            "location": "1 Hanover Square",
            "borough": "Manhattan",
            "architect": "Unknown",
            "style": "Anglo Italianate",
            "neighborhood": "Financial District",
            "pdfReportUrl": "https://cdn.informationcart.com/pdf/0042.pdf",
        },
        "LP-00066": {
            "name": "4 Fulton Street Building",
            "location": "4 Fulton Street",
            "borough": "Manhattan",
            "architect": "Unknown",
            "style": "Federal",
            "neighborhood": "Financial District",
            "pdfReportUrl": "https://cdn.informationcart.com/pdf/0066.pdf",
        },
    }

    # Use specific data if available, otherwise return generic data
    if landmark_id in landmark_specific:
        mock_data.update(landmark_specific[landmark_id])
    else:
        # Generate generic data for unknown landmark IDs
        mock_data.update(
            {
                "name": f"Mock Landmark {landmark_id}",
                "location": "123 Test Street",
                "borough": "Manhattan",
                "architect": "Unknown",
                "style": "Unknown",
                "neighborhood": "Test Neighborhood",
                "pdfReportUrl": f"https://cdn.informationcart.com/pdf/mock_{landmark_id}.pdf",
            }
        )

    return mock_data


def get_mock_landmark_pdf_text(landmark_id: str) -> str:
    """
    Get mock PDF text for a landmark when PDF download fails.

    Args:
        landmark_id: The landmark ID

    Returns:
        Mock text content that would typically be extracted from a PDF
    """
    landmark_data = get_mock_landmark(landmark_id)
    name = landmark_data.get("name", "Unknown Landmark")

    return f"""
    Landmarks Preservation Commission
    {landmark_id}
    {name}

    This is mock PDF text for testing purposes when the actual PDF
    cannot be accessed. This text is used to simulate the content
    that would normally be extracted from the landmark's PDF report.

    The mock data indicates this is a {landmark_data.get('style', 'Unknown')} style
    building located at {landmark_data.get('location', 'Unknown location')} in
    the borough of {landmark_data.get('borough', 'Unknown borough')}.

    Test chunk for landmark {landmark_id}
    """


def get_mock_lpc_reports(page: int = 1, limit: int = 10) -> Dict[str, Any]:
    """
    Get mock LPC reports for testing.

    Args:
        page: Page number to simulate
        limit: Number of items per page

    Returns:
        A dictionary with paginated mock LPC reports
    """
    # Create a list of available mock landmarks
    available_landmarks = ["LP-00001", "LP-00009", "LP-00042", "LP-00066"]

    # Create mock results based on pagination parameters
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit

    # Get the IDs for the current page
    page_ids = (
        available_landmarks[start_idx:end_idx]
        if start_idx < len(available_landmarks)
        else []
    )

    # Build results for this page
    results = [get_mock_landmark(landmark_id) for landmark_id in page_ids]

    # Build response with pagination metadata
    response = {
        "total": len(available_landmarks),
        "page": page,
        "limit": limit,
        "from": start_idx + 1 if results else 0,
        "to": start_idx + len(results) if results else 0,
        "results": results,
    }

    return response
