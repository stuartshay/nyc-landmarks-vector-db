"""Wikipedia processing utilities for NYC landmarks."""

from typing import List, Optional

from nyc_landmarks.utils.logger import get_logger

logger = get_logger(__name__)


def get_all_landmark_ids(
    limit: Optional[int] = None,
    page: int = 1,
    page_size: int = 100,
    fetch_all_pages: bool = False,
) -> List[str]:
    """
    Fetch landmark IDs using the `get_lpc_reports` method from `db_client`.

    Args:
        limit: Maximum number of landmark IDs to return (optional).
        page: Page number to fetch (starting from 1) if fetch_all_pages is False.
        page_size: Number of landmarks per page.
        fetch_all_pages: Whether to fetch all pages instead of just the specified page.

    Returns:
        List of landmark IDs.
    """
    from nyc_landmarks.db.db_client import get_db_client

    db_client = get_db_client()

    try:
        all_landmark_ids = []

        if fetch_all_pages:
            # Get total record count to determine how many pages to fetch
            total_records = db_client.get_total_record_count()
            total_pages = (
                total_records + page_size - 1
            ) // page_size  # Ceiling division

            logger.info(
                f"Fetching all {total_records} landmarks across {total_pages} pages with page size {page_size}..."
            )

            # Fetch landmarks page by page
            for current_page in range(1, total_pages + 1):
                response = db_client.get_lpc_reports(page=current_page, limit=page_size)

                if not response or not response.results:
                    logger.warning(
                        f"No landmarks found on page {current_page} with page size {page_size}."
                    )
                    continue

                # Extract only the IDs (lpNumber) from the landmarks on this page
                page_landmark_ids = [
                    report.lpNumber for report in response.results if report.lpNumber
                ]
                all_landmark_ids.extend(page_landmark_ids)

                logger.info(
                    f"Fetched {len(page_landmark_ids)} landmark IDs from page {current_page}/{total_pages}."
                )

                # If we've reached the limit, stop fetching more pages
                if limit is not None and len(all_landmark_ids) >= limit:
                    all_landmark_ids = all_landmark_ids[:limit]
                    logger.info(f"Reached limit of {limit} landmarks. Stopping fetch.")
                    break

            logger.info(f"Total landmarks fetched: {len(all_landmark_ids)}")

        else:
            # Fetch just the specified page
            response = db_client.get_lpc_reports(page=page, limit=page_size)

            if not response or not response.results:
                logger.warning(
                    f"No landmarks found on page {page} with page size {page_size}."
                )
                return []

            # Extract only the IDs (lpNumber) from the landmarks
            all_landmark_ids = [
                report.lpNumber for report in response.results if report.lpNumber
            ]

            # Apply additional limit if specified
            if limit is not None and limit < len(all_landmark_ids):
                all_landmark_ids = all_landmark_ids[:limit]

            logger.info(
                f"Fetched {len(all_landmark_ids)} landmark IDs from page {page}."
            )

        return all_landmark_ids

    except Exception as e:
        logger.error(f"Error fetching landmark IDs: {e}")
        return []


def get_landmarks_to_process(
    landmark_ids: Optional[str],
    limit: Optional[int],
    page: int = 1,
    process_all: bool = False,
    page_size: int = 100,
) -> List[str]:
    """Determine which landmarks to process.

    Args:
        landmark_ids: Comma-separated list of landmark IDs to process
        limit: Maximum number of landmarks to process
        page: Page number to start fetching landmarks from (not used if process_all is True)
        process_all: Whether to process all available landmarks in the database
        page_size: Number of landmarks to fetch per API request

    Returns:
        List of landmark IDs to process
    """
    if landmark_ids:
        # Process specific landmarks
        landmarks_to_process = [lid.strip() for lid in landmark_ids.split(",")]
        logger.info(f"Will process {len(landmarks_to_process)} specified landmarks")
    elif process_all:
        # Process all available landmarks
        from nyc_landmarks.db.db_client import get_db_client

        db_client = get_db_client()
        total_records = db_client.get_total_record_count()
        logger.info(f"Retrieved total record count: {total_records}")

        # If limit is provided, use the smaller of limit or total_records
        effective_limit = (
            min(limit, total_records) if limit is not None else total_records
        )
        logger.info(
            f"Will process up to {effective_limit} landmarks of {total_records} total"
        )

        # When process_all is True, we always start from page 1 (due to mutual exclusivity)
        # Set fetch_all_pages=True to fetch all pages of landmark IDs
        landmarks_to_process = get_all_landmark_ids(
            limit=effective_limit, page=1, page_size=page_size, fetch_all_pages=True
        )
        logger.info(
            f"Will process {len(landmarks_to_process)} landmarks from all available pages"
        )
    else:
        # Fetch landmark IDs with the specified limit, page, and page_size
        landmarks_to_process = get_all_landmark_ids(
            limit=limit, page=page, page_size=page_size
        )
        logger.info(
            f"Will process {len(landmarks_to_process)} landmarks (page {page}, page_size {page_size})"
        )

    return landmarks_to_process
