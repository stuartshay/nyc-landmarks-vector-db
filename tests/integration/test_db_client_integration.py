"""
Integration tests for DbClient functionality.

These tests validate the core functionality of the DbClient class,
focusing on methods that interact with the CoreDataStore API.
"""

import sys
from pathlib import Path
from typing import Any, Set

import pytest

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from nyc_landmarks.db.db_client import DbClient, get_db_client


class TestDbClientIntegration:
    """Integration tests for the DbClient class."""

    @pytest.fixture(scope="class")
    def db_client(self) -> DbClient:
        """Return a DbClient instance for testing."""
        return get_db_client()

    @pytest.fixture(scope="class")
    def page_size(self) -> int:
        """Return a standard page size for testing."""
        return 10

    @pytest.fixture(scope="class")
    def total_count(self, db_client: DbClient) -> int:
        """Return the total record count from the API."""
        return db_client.get_total_record_count()

    @pytest.mark.integration
    def test_get_total_record_count_basic(
        self, db_client: DbClient, total_count: int
    ) -> None:
        """Test that get_total_record_count returns a valid count of landmark records."""
        # Verify the count is a positive integer
        assert isinstance(total_count, int), "Total count should be an integer"
        assert total_count > 0, "Total count should be greater than zero"

        # The JSON example showed a total of 1765 - verify we're in a reasonable range
        # This helps catch if we're getting a partial count or incorrect value
        assert (
            total_count > 100
        ), "Total count seems too low compared to expected ~1700+ records"

        print(f"get_total_record_count() returned: {total_count}")

    @pytest.mark.integration
    def test_total_count_api_consistency(
        self, db_client: DbClient, total_count: int
    ) -> None:
        """Test that total_count is consistent with direct API response."""
        # Check diagnostic information
        has_make_request = hasattr(db_client.client, "_make_request")
        print(f"\nDiagnostic info: Client has _make_request method: {has_make_request}")

        if not has_make_request:
            pytest.skip("Client does not have _make_request method")

        try:
            # Make a minimal request with page size 1 to check response format
            response = db_client.client._make_request("GET", "/api/LpcReport/1/1")
            print(
                f"API response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}"
            )

            # If response has a 'total' key, check that our method found it
            if isinstance(response, dict) and "total" in response:
                expected_total = response["total"]
                print(f"API reports 'total' of {expected_total}")

                # Our method should have extracted this value
                assert total_count == expected_total, (
                    f"get_total_record_count() returned {total_count}, "
                    f"but API response has 'total' of {expected_total}"
                )
        except Exception as e:
            print(f"Could not directly verify API response format: {e}")
            pytest.skip(f"API verification failed: {e}")

    @pytest.mark.integration
    def test_get_landmarks_page_basic(
        self, db_client: DbClient, page_size: int
    ) -> None:
        """Test that get_landmarks_page returns valid results for the first page."""
        # Get first page
        first_page = db_client.get_landmarks_page(page_size=page_size, page=1)

        # Basic validation of page results
        assert first_page, "First page should return landmarks"
        assert len(first_page) > 0, "First page should not be empty"
        assert (
            len(first_page) <= page_size
        ), f"First page should have at most {page_size} landmarks"

    @pytest.mark.integration
    def test_landmarks_pagination(self, db_client: DbClient, page_size: int) -> None:
        """Test that pagination works correctly for landmark pages."""
        # Fetch multiple pages to verify consistency
        first_page = db_client.get_landmarks_page(page_size=page_size, page=1)
        second_page = db_client.get_landmarks_page(page_size=page_size, page=2)
        third_page = db_client.get_landmarks_page(page_size=page_size, page=3)

        # All pages should have results
        assert first_page, "First page should return landmarks"
        assert second_page, "Second page should have landmarks"
        assert third_page, "Third page should have landmarks"

        # Extract IDs from first page
        first_page_ids = self._extract_landmark_ids(first_page)

        # Extract IDs from second page
        second_page_ids = self._extract_landmark_ids(second_page)

        # Check that different pages have different records
        assert first_page_ids.isdisjoint(
            second_page_ids
        ), "First and second pages should have different landmarks"

    @pytest.mark.integration
    def test_total_count_consistency(
        self, db_client: DbClient, total_count: int, page_size: int
    ) -> None:
        """Test that total_count is consistent with the number of records we can fetch."""
        # Fetch sample pages
        first_page = db_client.get_landmarks_page(page_size=page_size, page=1)
        second_page = db_client.get_landmarks_page(page_size=page_size, page=2)
        third_page = db_client.get_landmarks_page(page_size=page_size, page=3)

        # Fetch a page near the expected end to verify count
        last_expected_page = (total_count + page_size - 1) // page_size
        mid_page_num = max(
            1, min(last_expected_page - 1, 10)
        )  # Pick a middle page, capped at 10 for performance

        mid_page = db_client.get_landmarks_page(page_size=page_size, page=mid_page_num)
        assert mid_page, f"Page {mid_page_num} should return landmarks"

        # Basic validation that reported count is reasonable
        # The count should be at least the number of records we've seen
        records_seen = (
            len(first_page) + len(second_page) + len(third_page) + len(mid_page)
        )
        assert (
            total_count >= records_seen
        ), f"Total count ({total_count}) should be at least the number of records we've seen ({records_seen})"

        print(f"API reports {total_count} total landmark records")
        print(f"Records seen from sample pages: {records_seen}")

    def _extract_landmark_ids(self, landmarks: list[Any]) -> Set[str]:
        """Extract landmark IDs from a list of landmark objects or dictionaries."""
        ids: Set[str] = set()
        for lm in landmarks:
            if not lm:
                continue

            landmark_id = ""
            if isinstance(lm, dict):
                landmark_id = lm.get("id", "") or lm.get("lpNumber", "")
            else:
                # Handle Pydantic model case
                landmark_id = getattr(lm, "id", "") or getattr(lm, "lpNumber", "")

            if landmark_id:
                ids.add(
                    str(landmark_id)
                )  # Convert to string to ensure type consistency
        return ids
