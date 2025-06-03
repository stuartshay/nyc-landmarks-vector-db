"""
Module for fetching Wikipedia article quality assessments using the Lift Wing API.

This module provides functionality to assess the quality of Wikipedia articles
by querying the Wikimedia Lift Wing API's articlequality model.
"""

from typing import Any, Dict, Optional

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from nyc_landmarks.config.settings import Settings
from nyc_landmarks.utils.logger import get_logger

logger = get_logger(__name__)


class WikipediaQualityFetcher:
    """Fetches quality assessments for Wikipedia articles using the Lift Wing API."""

    def __init__(self) -> None:
        """Initialize the Wikipedia quality fetcher."""
        settings = Settings()
        self.api_endpoint = settings.WIKIPEDIA_API_ENDPOINT
        self.user_agent = settings.WIKIPEDIA_USER_AGENT
        self.headers = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
        }
        logger.info("Initialized Wikipedia quality fetcher")

    @retry(  # type: ignore[misc]
        retry=retry_if_exception_type(
            (requests.ConnectionError, requests.Timeout, requests.HTTPError)
        ),
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def fetch_article_quality(self, rev_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch article quality assessment from Lift Wing API.

        Args:
            rev_id: Wikipedia revision ID

        Returns:
            Dictionary containing quality prediction and probabilities, or None if failed
        """
        if not rev_id:
            logger.warning("Cannot fetch article quality: No revision ID provided")
            return None

        try:
            logger.info(f"Fetching quality assessment for Wikipedia revision: {rev_id}")

            # Prepare the request payload
            payload = {"rev_id": int(rev_id)}

            # Make the API request
            response = requests.post(
                self.api_endpoint, headers=self.headers, json=payload, timeout=30
            )
            response.raise_for_status()

            # Parse the response
            result = response.json()

            # Handle the nested structure in the actual API response
            if "enwiki" in result and "scores" in result["enwiki"]:
                # Extract from nested structure
                rev_id_str = str(rev_id)
                if rev_id_str in result["enwiki"]["scores"]:
                    article_scores = result["enwiki"]["scores"][rev_id_str]
                    if (
                        "articlequality" in article_scores
                        and "score" in article_scores["articlequality"]
                    ):
                        score = article_scores["articlequality"]["score"]
                        logger.info("Successfully parsed nested Lift Wing API response")
                    else:
                        logger.warning(
                            f"Missing articlequality or score in API response: {result}"
                        )
                        return None
                else:
                    logger.warning(
                        f"Rev ID {rev_id} not found in API response: {result}"
                    )
                    return None
            elif "score" in result:
                # Handle the simple structure we initially expected
                score = result["score"]
            else:
                logger.warning(f"Invalid response format from Lift Wing API: {result}")
                return None
            logger.info(
                f"Quality assessment for rev_id {rev_id}: {score.get('prediction', 'Unknown')}"
            )

            return {
                "prediction": score.get("prediction"),
                "probabilities": score.get("probability", {}),
                "rev_id": rev_id,
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching quality assessment for rev_id {rev_id}: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error processing quality assessment for rev_id {rev_id}: {e}"
            )
            return None
