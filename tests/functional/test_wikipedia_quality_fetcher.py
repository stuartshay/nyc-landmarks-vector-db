"""
Functional tests for Wikipedia Quality Fetcher functionality.

These tests verify the WikipediaQualityFetcher can handle various scenarios
including successful API responses, error conditions, and edge cases.
"""

import logging
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
import requests

from nyc_landmarks.wikipedia.quality_fetcher import WikipediaQualityFetcher

logger = logging.getLogger(__name__)


class TestWikipediaQualityFetcherFunctional:
    """Test WikipediaQualityFetcher functionality with proper isolation."""

    @pytest.fixture
    def quality_fetcher(self) -> WikipediaQualityFetcher:
        """Create a WikipediaQualityFetcher instance for testing."""
        return WikipediaQualityFetcher()

    @pytest.fixture
    def mock_nested_api_response(self) -> Dict[str, Any]:
        """Mock response from Lift Wing API with nested structure."""
        return {
            "enwiki": {
                "scores": {
                    "12345": {
                        "articlequality": {
                            "score": {
                                "prediction": "C",
                                "probability": {
                                    "FA": 0.1,
                                    "GA": 0.15,
                                    "B": 0.2,
                                    "C": 0.35,
                                    "Start": 0.15,
                                    "Stub": 0.05,
                                },
                            }
                        }
                    }
                }
            }
        }

    @pytest.fixture
    def mock_simple_api_response(self) -> Dict[str, Any]:
        """Mock response from Lift Wing API with simple structure."""
        return {
            "score": {
                "prediction": "B",
                "probability": {
                    "FA": 0.05,
                    "GA": 0.1,
                    "B": 0.4,
                    "C": 0.3,
                    "Start": 0.1,
                    "Stub": 0.05,
                },
            }
        }

    @pytest.mark.functional
    def test_quality_fetcher_initialization(
        self, quality_fetcher: WikipediaQualityFetcher
    ) -> None:
        """Test that WikipediaQualityFetcher can be initialized successfully."""
        logger.info("--- Starting test_quality_fetcher_initialization ---")

        assert (
            quality_fetcher is not None
        ), "WikipediaQualityFetcher should initialize successfully"
        assert hasattr(
            quality_fetcher, "api_endpoint"
        ), "Should have api_endpoint attribute"
        assert hasattr(
            quality_fetcher, "user_agent"
        ), "Should have user_agent attribute"
        assert hasattr(quality_fetcher, "headers"), "Should have headers attribute"

        # Check headers are properly configured
        assert "User-Agent" in quality_fetcher.headers
        assert "Content-Type" in quality_fetcher.headers
        assert quality_fetcher.headers["Content-Type"] == "application/json"

        logger.info(
            "✅ WikipediaQualityFetcher initialization test completed successfully"
        )

    @pytest.mark.functional
    @patch("requests.post")
    def test_fetch_article_quality_nested_response(
        self,
        mock_post: Mock,
        quality_fetcher: WikipediaQualityFetcher,
        mock_nested_api_response: Dict[str, Any],
    ) -> None:
        """Test fetching article quality with nested API response structure."""
        logger.info("--- Starting test_fetch_article_quality_nested_response ---")

        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_nested_api_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test the method
        result = quality_fetcher.fetch_article_quality("12345")

        # Verify the result
        assert result is not None, "Should return a result for valid revision ID"
        assert result["prediction"] == "C", "Should extract correct prediction"
        assert result["rev_id"] == "12345", "Should include revision ID"
        assert "probabilities" in result, "Should include probabilities"
        assert isinstance(
            result["probabilities"], dict
        ), "Probabilities should be a dictionary"

        # Verify API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == quality_fetcher.api_endpoint
        assert call_args[1]["json"] == {"rev_id": 12345}
        assert call_args[1]["headers"] == quality_fetcher.headers
        assert call_args[1]["timeout"] == 30

        logger.info("✅ Nested API response test completed successfully")

    @pytest.mark.functional
    @patch("requests.post")
    def test_fetch_article_quality_simple_response(
        self,
        mock_post: Mock,
        quality_fetcher: WikipediaQualityFetcher,
        mock_simple_api_response: Dict[str, Any],
    ) -> None:
        """Test fetching article quality with simple API response structure."""
        logger.info("--- Starting test_fetch_article_quality_simple_response ---")

        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_simple_api_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test the method
        result = quality_fetcher.fetch_article_quality("67890")

        # Verify the result
        assert result is not None, "Should return a result for valid revision ID"
        assert result["prediction"] == "B", "Should extract correct prediction"
        assert result["rev_id"] == "67890", "Should include revision ID"
        assert "probabilities" in result, "Should include probabilities"
        assert (
            result["probabilities"]["B"] == 0.4
        ), "Should include correct probability values"

        logger.info("✅ Simple API response test completed successfully")

    @pytest.mark.functional
    def test_fetch_article_quality_empty_rev_id(
        self, quality_fetcher: WikipediaQualityFetcher
    ) -> None:
        """Test fetching article quality with empty revision ID."""
        logger.info("--- Starting test_fetch_article_quality_empty_rev_id ---")

        # Test with empty string
        result = quality_fetcher.fetch_article_quality("")
        assert result is None, "Should return None for empty revision ID"

        # Test with None (should handle gracefully)
        result = quality_fetcher.fetch_article_quality(None)  # type: ignore
        assert result is None, "Should return None for None revision ID"

        logger.info("✅ Empty revision ID test completed successfully")

    @pytest.mark.functional
    @patch("requests.post")
    def test_fetch_article_quality_connection_error(
        self, mock_post: Mock, quality_fetcher: WikipediaQualityFetcher
    ) -> None:
        """Test handling of connection errors with retry mechanism."""
        logger.info("--- Starting test_fetch_article_quality_connection_error ---")

        # Setup mock to raise connection error
        mock_post.side_effect = requests.ConnectionError("Connection failed")

        # Test the method - should retry and then raise
        with pytest.raises(requests.ConnectionError):
            quality_fetcher.fetch_article_quality("12345")

        # Verify retry attempts were made (should be called 3 times due to retry decorator)
        assert mock_post.call_count == 3, "Should retry 3 times before giving up"

        logger.info("✅ Connection error test completed successfully")

    @pytest.mark.functional
    @patch("requests.post")
    def test_fetch_article_quality_http_error(
        self, mock_post: Mock, quality_fetcher: WikipediaQualityFetcher
    ) -> None:
        """Test handling of HTTP errors."""
        logger.info("--- Starting test_fetch_article_quality_http_error ---")

        # Setup mock response with HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_post.return_value = mock_response

        # Test the method - should retry and then raise
        with pytest.raises(requests.HTTPError):
            quality_fetcher.fetch_article_quality("12345")

        logger.info("✅ HTTP error test completed successfully")

    @pytest.mark.functional
    @patch("requests.post")
    def test_fetch_article_quality_invalid_response_format(
        self, mock_post: Mock, quality_fetcher: WikipediaQualityFetcher
    ) -> None:
        """Test handling of invalid response format."""
        logger.info(
            "--- Starting test_fetch_article_quality_invalid_response_format ---"
        )

        # Setup mock response with invalid format
        mock_response = Mock()
        mock_response.json.return_value = {"invalid": "format"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test the method
        result = quality_fetcher.fetch_article_quality("12345")

        # Should return None for invalid format
        assert result is None, "Should return None for invalid response format"

        logger.info("✅ Invalid response format test completed successfully")

    @pytest.mark.functional
    @patch("requests.post")
    def test_fetch_article_quality_missing_rev_id_in_response(
        self, mock_post: Mock, quality_fetcher: WikipediaQualityFetcher
    ) -> None:
        """Test handling when requested revision ID is not in nested response."""
        logger.info(
            "--- Starting test_fetch_article_quality_missing_rev_id_in_response ---"
        )

        # Setup mock response with different revision ID
        mock_response_data = {
            "enwiki": {
                "scores": {
                    "99999": {  # Different revision ID
                        "articlequality": {
                            "score": {"prediction": "C", "probability": {"C": 0.5}}
                        }
                    }
                }
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test the method with different revision ID
        result = quality_fetcher.fetch_article_quality("12345")

        # Should return None when revision ID not found
        assert (
            result is None
        ), "Should return None when revision ID not found in response"

        logger.info("✅ Missing revision ID test completed successfully")

    @pytest.mark.functional
    @patch("requests.post")
    def test_fetch_article_quality_missing_articlequality_key(
        self, mock_post: Mock, quality_fetcher: WikipediaQualityFetcher
    ) -> None:
        """Test handling when articlequality key is missing from response."""
        logger.info(
            "--- Starting test_fetch_article_quality_missing_articlequality_key ---"
        )

        # Setup mock response missing articlequality key
        mock_response_data = {
            "enwiki": {
                "scores": {
                    "12345": {
                        "other_model": {
                            "score": {"prediction": "C", "probability": {"C": 0.5}}
                        }
                    }
                }
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test the method
        result = quality_fetcher.fetch_article_quality("12345")

        # Should return None when articlequality key is missing
        assert result is None, "Should return None when articlequality key is missing"

        logger.info("✅ Missing articlequality key test completed successfully")

    @pytest.mark.functional
    @patch("requests.post")
    def test_fetch_article_quality_json_decode_error(
        self, mock_post: Mock, quality_fetcher: WikipediaQualityFetcher
    ) -> None:
        """Test handling of JSON decode errors."""
        logger.info("--- Starting test_fetch_article_quality_json_decode_error ---")

        # Setup mock response with JSON decode error
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test the method
        result = quality_fetcher.fetch_article_quality("12345")

        # Should return None for JSON decode error
        assert result is None, "Should return None for JSON decode error"

        logger.info("✅ JSON decode error test completed successfully")

    @pytest.mark.functional
    @patch("requests.post")
    def test_fetch_article_quality_retry_success_after_failure(
        self,
        mock_post: Mock,
        quality_fetcher: WikipediaQualityFetcher,
        mock_simple_api_response: Dict[str, Any],
    ) -> None:
        """Test successful retry after initial failure."""
        logger.info(
            "--- Starting test_fetch_article_quality_retry_success_after_failure ---"
        )

        # Setup mock to fail once then succeed
        mock_response_success = Mock()
        mock_response_success.json.return_value = mock_simple_api_response
        mock_response_success.raise_for_status.return_value = None

        mock_post.side_effect = [
            requests.ConnectionError("First attempt failed"),
            mock_response_success,
        ]

        # Test the method
        result = quality_fetcher.fetch_article_quality("12345")

        # Should succeed on retry
        assert result is not None, "Should succeed on retry"
        assert (
            result["prediction"] == "B"
        ), "Should return correct prediction after retry"
        assert mock_post.call_count == 2, "Should have made 2 attempts"

        logger.info("✅ Retry success test completed successfully")

    @pytest.mark.functional
    def test_fetch_article_quality_methods_exist(
        self, quality_fetcher: WikipediaQualityFetcher
    ) -> None:
        """Test that WikipediaQualityFetcher has expected methods."""
        logger.info("--- Starting test_fetch_article_quality_methods_exist ---")

        # Check that key methods exist
        assert hasattr(
            quality_fetcher, "fetch_article_quality"
        ), "Should have fetch_article_quality method"
        assert callable(
            quality_fetcher.fetch_article_quality
        ), "fetch_article_quality should be callable"

        logger.info("✅ WikipediaQualityFetcher methods test completed successfully")
