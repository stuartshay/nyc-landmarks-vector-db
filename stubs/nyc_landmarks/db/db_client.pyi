"""
Type stub file for db_client.py to satisfy mypy.
"""

from typing import Any, Dict, List, Optional, Union

# Import directly from implementation module
from nyc_landmarks.db._coredatastore_api import _CoreDataStoreAPI
from nyc_landmarks.models.landmark_models import (
    LandmarkDetail,
    LpcReportDetailResponse,
    LpcReportModel,
    LpcReportResponse,
)
from nyc_landmarks.models.wikipedia_models import WikipediaArticleModel

class DbClient:
    """Database client interface for CoreDataStore API."""

    client: _CoreDataStoreAPI

    def __init__(self, client: _CoreDataStoreAPI) -> None:
        """Initialize the CoreDataStore API client."""
        ...

    def get_landmark_by_id(
        self, landmark_id: str
    ) -> Optional[Union[Dict[str, Any], LpcReportDetailResponse]]: ...
    def get_all_landmarks(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]: ...
    def get_landmarks_page(
        self, page_size: int = 10, page: int = 1
    ) -> Union[List[Dict[str, Any]], List[LpcReportModel]]: ...
    def search_landmarks(self, search_term: str) -> List[Dict[str, Any]]: ...
    def get_landmark_metadata(self, landmark_id: str) -> Dict[str, Any]: ...
    def get_lpc_reports(
        self,
        page: int = 1,
        limit: int = 10,
        borough: Optional[str] = None,
        object_type: Optional[str] = None,
        neighborhood: Optional[str] = None,
        search_text: Optional[str] = None,
        parent_style_list: Optional[List[str]] = None,
        sort_column: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> LpcReportResponse: ...
    def get_landmark_pdf_url(self, landmark_id: str) -> Optional[str]: ...
    def get_landmark_buildings(
        self, landmark_id: str, limit: int = 50
    ) -> List[LandmarkDetail]: ...
    def get_wikipedia_articles(
        self, landmark_id: str
    ) -> List[WikipediaArticleModel]: ...
    def get_landmark_pluto_data(self, landmark_id: str) -> List[Dict[str, Any]]: ...
    def get_total_record_count(self) -> int: ...
    def _get_count_from_api_metadata(self) -> int: ...

def get_db_client() -> DbClient: ...
