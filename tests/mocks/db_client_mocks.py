"""
Mock implementations for db_client testing.

This module provides mock objects and fixtures for testing Wikipedia integration
without requiring external API calls to the CoreDataStore API.
"""

from typing import Any, Dict, List
from unittest.mock import Mock

from nyc_landmarks.models.landmark_models import PlutoDataModel
from nyc_landmarks.models.wikipedia_models import WikipediaArticleModel


def get_mock_wikipedia_articles() -> List[WikipediaArticleModel]:
    """
    Get mock Wikipedia article data for testing.

    Returns:
        List of WikipediaArticleModel objects for test landmarks
    """
    return [
        WikipediaArticleModel(
            id=393,
            lpNumber="LP-01973",
            url="https://en.wikipedia.org/wiki/Harlem_YMCA",
            title="Harlem YMCA",
            recordType="Wikipedia",
            content="The Harlem YMCA is a historic building located in Harlem, New York City. Built in 1932, it served as an important community center for the African American community. The building features Art Deco architectural elements and was designed by prominent architects. It provided educational, recreational, and social services to the community for decades.",
        ),
        WikipediaArticleModel(
            id=394,
            lpNumber="LP-00009",
            url="https://en.wikipedia.org/wiki/Federal_Hall",
            title="Federal Hall",
            recordType="Wikipedia",
            content="Federal Hall is a historic building in New York City's Financial District. Originally built as New York's City Hall, it was the site of George Washington's inauguration as the first President of the United States in 1789. The current structure was completed in 1842 and served as a U.S. Custom House. It now operates as a museum and national memorial.",
        ),
    ]


def get_mock_landmark_metadata_lp01973() -> Dict[str, Any]:
    """
    Returns mock basic landmark metadata for LP-01973 (Harlem YMCA).

    This simulates the response from get_landmark_metadata() API call.
    """
    return {
        "landmark_id": "LP-01973",
        "name": "Harlem YMCA",
        "location": "180 West 135th Street",
        "borough": "Manhattan",
        "type": "Individual Landmark",
        "designation_date": "1998-06-23",
    }


def get_mock_landmark_details_lp01973() -> Dict[str, Any]:
    """
    Returns mock detailed landmark information for LP-01973 (Harlem YMCA).

    This simulates the response from get_landmark_by_id() API call,
    providing architect, neighborhood, style information, and indicating
    whether PLUTO data is available for this landmark.
    """
    return {
        "architect": "James C. Mackenzie Jr.",
        "neighborhood": "Harlem",
        "style": "Renaissance Revival",
        "landmark_id": "LP-01973",
        "name": "Harlem YMCA",
        "location": "180 West 135th Street",
        "borough": "Manhattan",
        "type": "Individual Landmark",
        "designation_date": "1998-06-23",
        "plutoStatus": True,  # Matches API field name - indicates that PLUTO data is available for this landmark
    }


def get_mock_landmark_buildings_lp01973() -> List[Dict[str, Any]]:
    """
    Returns mock building data for LP-01973 (Harlem YMCA).

    This simulates the response from get_landmark_buildings() API call,
    providing BBL, BIN, coordinates, and address information.
    """
    return [
        {
            "bbl": "1018510001",
            "bin": "1234567",
            "block": "1851",
            "lot": "1",
            "latitude": 40.8126,
            "longitude": -73.9441,
            "address": "180 West 135th Street",
            "name": "Harlem YMCA",
        }
    ]


def get_mock_landmark_pluto_data_lp01973() -> List[PlutoDataModel]:
    """
    Returns mock PLUTO data for LP-01973 (Harlem YMCA).

    This simulates the response from get_landmark_pluto_data() API call,
    providing property data like year built, land use, and zoning.
    """
    return [
        PlutoDataModel(
            yearBuilt="1932",
            landUse="08",  # Educational/Cultural
            historicDistrict="Central Harlem Historic District",  # Add test data
            zoneDist1="C4-4D",
        )
    ]


def create_mock_db_client() -> Mock:
    """
    Create a comprehensive mock db_client that returns test data for all API methods.

    Returns:
        Mock object configured to return test data for all enhanced metadata collector methods
    """
    mock_client = Mock()

    # Assign all mock methods to the client
    mock_client.get_wikipedia_articles = _create_mock_get_wikipedia_articles()
    mock_client.get_landmark_metadata = _create_mock_get_landmark_metadata()
    mock_client.get_landmark_by_id = _create_mock_get_landmark_by_id()
    mock_client.get_landmark_buildings = _create_mock_get_landmark_buildings()
    mock_client.get_landmark_pluto_data = _create_mock_get_landmark_pluto_data()

    return mock_client


def _create_mock_get_wikipedia_articles():
    """Create mock implementation for get_wikipedia_articles method."""

    def mock_get_wikipedia_articles(landmark_id: str) -> List[WikipediaArticleModel]:
        """Mock implementation that returns articles for specific landmark IDs."""
        mock_articles = get_mock_wikipedia_articles()
        return [article for article in mock_articles if article.lpNumber == landmark_id]

    return mock_get_wikipedia_articles


def _create_mock_get_landmark_metadata():
    """Create mock implementation for get_landmark_metadata method."""

    def mock_get_landmark_metadata(landmark_id: str) -> Dict[str, Any]:
        """Mock implementation that returns basic landmark metadata."""
        if landmark_id == "LP-01973":
            return get_mock_landmark_metadata_lp01973()
        elif landmark_id == "LP-00009":
            return _get_mock_landmark_metadata_lp00009()
        return {}

    return mock_get_landmark_metadata


def _get_mock_landmark_metadata_lp00009() -> Dict[str, Any]:
    """Get mock landmark metadata for LP-00009."""
    return {
        "landmark_id": "LP-00009",
        "name": "Federal Hall National Memorial",
        "location": "26 Wall Street",
        "borough": "Manhattan",
        "type": "Individual Landmark",
        "designation_date": "1965-12-21",
    }


def _create_mock_get_landmark_by_id():
    """Create mock implementation for get_landmark_by_id method."""

    def mock_get_landmark_by_id(landmark_id: str) -> Dict[str, Any]:
        """Mock implementation that returns detailed landmark information."""
        if landmark_id == "LP-01973":
            return get_mock_landmark_details_lp01973()
        elif landmark_id == "LP-00009":
            return _get_mock_landmark_details_lp00009()
        return {}

    return mock_get_landmark_by_id


def _get_mock_landmark_details_lp00009() -> Dict[str, Any]:
    """Get mock landmark details for LP-00009."""
    return {
        "architect": "Town & Davis",
        "neighborhood": "Financial District",
        "style": "Greek Revival",
        "landmark_id": "LP-00009",
        "name": "Federal Hall National Memorial",
        "location": "26 Wall Street",
        "borough": "Manhattan",
        "type": "Individual Landmark",
        "designation_date": "1965-12-21",
    }


def _create_mock_get_landmark_buildings():
    """Create mock implementation for get_landmark_buildings method."""

    def mock_get_landmark_buildings(landmark_id: str) -> List[Dict[str, Any]]:
        """Mock implementation that returns building data."""
        if landmark_id == "LP-01973":
            return get_mock_landmark_buildings_lp01973()
        elif landmark_id == "LP-00009":
            return _get_mock_landmark_buildings_lp00009()
        return []

    return mock_get_landmark_buildings


def _get_mock_landmark_buildings_lp00009() -> List[Dict[str, Any]]:
    """Get mock landmark buildings for LP-00009."""
    return [
        {
            "bbl": "1000050001",
            "bin": "1000001",
            "block": "5",
            "lot": "1",
            "latitude": 40.7071,
            "longitude": -74.0101,
            "address": "26 Wall Street",
            "name": "Federal Hall National Memorial",
        }
    ]


def _create_mock_get_landmark_pluto_data():
    """Create mock implementation for get_landmark_pluto_data method."""

    def mock_get_landmark_pluto_data(landmark_id: str) -> List[PlutoDataModel]:
        """Mock implementation that returns PLUTO data."""
        if landmark_id == "LP-01973":
            return get_mock_landmark_pluto_data_lp01973()
        elif landmark_id == "LP-00009":
            return _get_mock_landmark_pluto_data_lp00009()
        return []

    return mock_get_landmark_pluto_data


def _get_mock_landmark_pluto_data_lp00009() -> List[PlutoDataModel]:
    """Get mock PLUTO data for LP-00009."""
    return [
        PlutoDataModel(
            yearBuilt="1842",
            landUse="08",  # Educational/Cultural
            historicDistrict="Stone Street Historic District",
            zoneDist1="C5-1",
        )
    ]


def create_mock_db_client_with_errors() -> Mock:
    """
    Create a mock db_client that raises exceptions for testing error handling.

    Returns:
        Mock object that raises exceptions when methods are called
    """
    mock_client = Mock()

    def mock_get_wikipedia_articles_with_error(
        landmark_id: str,
    ) -> List[WikipediaArticleModel]:
        """Mock implementation that raises an exception."""
        raise Exception(f"API error for landmark {landmark_id}")

    mock_client.get_wikipedia_articles = mock_get_wikipedia_articles_with_error
    return mock_client


def create_mock_db_client_empty_responses() -> Mock:
    """
    Create a mock db_client that returns empty responses for testing edge cases.

    Returns:
        Mock object that returns empty lists
    """
    mock_client = Mock()

    def mock_get_wikipedia_articles_empty(
        landmark_id: str,
    ) -> List[WikipediaArticleModel]:
        """Mock implementation that returns empty list."""
        return []

    mock_client.get_wikipedia_articles = mock_get_wikipedia_articles_empty
    return mock_client


# Pytest fixtures for easy use in tests
def mock_db_client_fixture() -> Mock:
    """Pytest fixture that provides a standard mock db_client."""
    return create_mock_db_client()


def mock_db_client_errors_fixture() -> Mock:
    """Pytest fixture that provides a mock db_client that raises errors."""
    return create_mock_db_client_with_errors()


def mock_db_client_empty_fixture() -> Mock:
    """Pytest fixture that provides a mock db_client with empty responses."""
    return create_mock_db_client_empty_responses()
