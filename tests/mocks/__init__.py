"""
Package for mock data used in tests.

This package contains modules with mock data structures and functions
that provide consistent test fixtures across test files.
"""

# Import commonly used mock functions for easy access
from .db_client_mocks import (
    create_mock_db_client,
    create_mock_db_client_empty_responses,
    create_mock_db_client_with_errors,
    get_mock_landmark_buildings_lp01973,
    get_mock_landmark_details_lp01973,
    get_mock_landmark_metadata_lp01973,
    get_mock_landmark_pluto_data_lp01973,
    get_mock_wikipedia_articles,
    mock_db_client_empty_fixture,
    mock_db_client_errors_fixture,
    mock_db_client_fixture,
)
from .landmark_mocks import (
    get_mock_building_model,
    get_mock_buildings_from_landmark_detail,
    get_mock_landmark_details,
    get_mock_landmarks_for_test_fetch_buildings,
)
from .metadata_mocks import (
    get_mock_pdr_report_metadata,
    get_mock_root_metadata,
    get_mock_wikipedia_metadata,
)

__all__ = [
    # db_client mocks
    "create_mock_db_client",
    "create_mock_db_client_with_errors",
    "create_mock_db_client_empty_responses",
    "get_mock_wikipedia_articles",
    "get_mock_landmark_metadata_lp01973",
    "get_mock_landmark_details_lp01973",
    "get_mock_landmark_buildings_lp01973",
    "get_mock_landmark_pluto_data_lp01973",
    "mock_db_client_fixture",
    "mock_db_client_errors_fixture",
    "mock_db_client_empty_fixture",
    # landmark mocks
    "get_mock_landmark_details",
    "get_mock_buildings_from_landmark_detail",
    "get_mock_building_model",
    "get_mock_landmarks_for_test_fetch_buildings",
    # metadata mocks
    "get_mock_root_metadata",
    "get_mock_wikipedia_metadata",
    "get_mock_pdr_report_metadata",
]
