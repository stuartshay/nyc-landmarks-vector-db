"""
Wikipedia content fetcher module for NYC Landmarks Vector Database.

This module handles fetching and processing Wikipedia article content
for landmarks to be embedded and stored in the vector database.
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple, TypedDict

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from nyc_landmarks.config.settings import settings
from nyc_landmarks.models.wikipedia_models import (
    WikipediaArticleModel,
    WikipediaContentModel,
    WikipediaProcessingResult,
)
from nyc_landmarks.utils.logger import configure_basic_logging_safely

# Configure logging
logger = logging.getLogger(__name__)
configure_basic_logging_safely(level=getattr(logging, settings.LOG_LEVEL.value))


# Define chunk type for mypy
class ChunkDict(TypedDict):
    text: str
    chunk_index: int
    metadata: Dict[str, Any]
    total_chunks: int  # Added for type checking


class WikipediaFetcher:
    """Wikipedia content fetcher for landmark articles."""

    def __init__(self) -> None:
        """Initialize the Wikipedia fetcher with a persistent session."""
        # Set up basic configuration
        self.user_agent = (
            "NYCLandmarksVectorDB/1.0 (https://github.com/username/nyc-landmarks-vector-db; "
            "email@example.com) Python-Requests/2.31.0"
        )

        # Create a persistent session with connection pooling
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

        # Configure connection pooling with retry capability
        adapter = HTTPAdapter(
            pool_connections=10,  # Number of connection objects to keep in pool
            pool_maxsize=20,  # Maximum number of connections in the pool
            max_retries=3,  # Default retry configuration
            pool_block=False,  # Whether to block when pool is full
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Configure rate limiting
        self.rate_limit_delay = 1.0  # Seconds between requests to be polite

        logger.info("Initialized Wikipedia content fetcher with connection pooling")

    @retry(  # type: ignore[misc]
        retry=retry_if_exception_type(
            (requests.ConnectionError, requests.Timeout, requests.HTTPError)
        ),
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def fetch_wikipedia_content(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Fetch the content of a Wikipedia article.

        Args:
            url: URL of the Wikipedia article

        Returns:
            Tuple of (article content, revision ID) or (None, None) if an error occurs
        """
        if not self._is_valid_url(url):
            return None, None

        try:
            soup = self._fetch_and_parse_html(url)
            rev_id = self._extract_revision_id(soup, url)
            content = self._extract_content(soup, url, rev_id)

            if content is None:
                return None, str(rev_id) if rev_id is not None else None

            # Add a delay to respect rate limits
            time.sleep(self.rate_limit_delay)

            self._log_success(content, rev_id)
            return content, str(rev_id) if rev_id is not None else None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Wikipedia content from {url}: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error processing Wikipedia content from {url}: {e}"
            )
            return None, None  # Return None for both content and rev_id on error

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid, False otherwise
        """
        if not url.startswith(("http://", "https://")):
            logger.warning(f"Invalid URL format: {url}")
            return False
        return True

    def _fetch_and_parse_html(self, url: str) -> BeautifulSoup:
        """Fetch HTML content and parse it.

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object with parsed HTML
        """
        logger.info(f"Fetching Wikipedia content from: {url}")

        try:
            # Use persistent session with separate connect and read timeouts
            # - connect_timeout: time to establish the connection (3.05s)
            # - read_timeout: time to receive the full response (27s)
            response = self.session.get(
                url,
                timeout=(3.05, 27),  # (connect_timeout, read_timeout)
            )
            response.raise_for_status()

            # Enhance logging for better debugging
            logger.debug(f"HTTP response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            logger.debug(f"Response size: {len(response.text)} bytes")
            logger.debug(f"Response preview: {response.text[:500]}...")

            return BeautifulSoup(response.text, "html.parser")

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error fetching {url}: {e}", exc_info=True)
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error fetching {url}: {e}", exc_info=True)
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"HTTP error fetching {url}: {response.status_code} - {e}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}", exc_info=True)
            raise

    def _extract_revision_id(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract revision ID from the Wikipedia page.

        Args:
            soup: BeautifulSoup object with parsed HTML
            url: Original URL (for extracting from URL if needed)

        Returns:
            Revision ID as string or None if not found
        """
        # Try to find revision ID in the page info
        revision_element = soup.select_one('head > meta[property="mw:pageId"]')
        if revision_element and "content" in revision_element.attrs:
            rev_id = str(revision_element["content"])
            logger.info(f"Found revision ID from meta tag: {rev_id}")
            return rev_id

        # Alternative method - look for it in the page JSON data
        script_rev_id = self._extract_revision_from_scripts(soup)
        if script_rev_id:
            return script_rev_id

        # Another alternative - extract from URL if it contains oldid
        return self._extract_revision_from_url(url)

    def _extract_revision_from_scripts(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract revision ID from script tags.

        Args:
            soup: BeautifulSoup object with parsed HTML

        Returns:
            Revision ID as string or None if not found
        """
        script_tags = soup.find_all("script")
        for script in script_tags:
            if script.string and '"wgRevisionId":' in script.string:
                match = re.search(r'"wgRevisionId":\s*(\d+)', script.string)
                if match:
                    rev_id = str(match.group(1))
                    logger.info(f"Found revision ID from script tag: {rev_id}")
                    return rev_id
        return None

    def _extract_revision_from_url(self, url: str) -> Optional[str]:
        """Extract revision ID from URL if it contains oldid parameter.

        Args:
            url: Wikipedia URL

        Returns:
            Revision ID as string or None if not found
        """
        if "oldid=" in url:
            match = re.search(r"oldid=(\d+)", url)
            if match:
                rev_id = str(match.group(1))
                logger.info(f"Found revision ID from URL: {rev_id}")
                return rev_id
        return None

    def _extract_content(
        self, soup: BeautifulSoup, url: str, rev_id: Optional[str]
    ) -> Optional[str]:
        """Extract main content from Wikipedia page.

        Args:
            soup: BeautifulSoup object with parsed HTML
            url: Original URL for logging
            rev_id: Revision ID for logging

        Returns:
            Cleaned article content or None if extraction fails
        """
        # Extract the main content div
        content_div = soup.find("div", {"id": "mw-content-text"})
        if not content_div:
            logger.warning(f"Could not find main content in Wikipedia page: {url}")
            return None

        # Extract text content
        content = self._extract_text_from_content_div(content_div)

        # Clean up the text
        return self._clean_wikipedia_text(content)

    def _extract_text_from_content_div(self, content_div: Any) -> str:
        """Extract text from content div, handling different element types.

        Args:
            content_div: BeautifulSoup element containing content

        Returns:
            Extracted text content
        """
        from bs4 import NavigableString

        if not isinstance(content_div, NavigableString) and hasattr(
            content_div, "find_all"
        ):
            paragraphs = content_div.find_all("p")
            return "\n\n".join([p.get_text() for p in paragraphs])
        else:
            logger.warning(
                f"Content div doesn't support find_all method: {type(content_div)}"
            )
            return (
                content_div.get_text()
                if hasattr(content_div, "get_text")
                else str(content_div)
            )

    def _log_success(self, content: str, rev_id: Optional[str]) -> None:
        """Log successful content fetch.

        Args:
            content: Fetched content
            rev_id: Revision ID if found
        """
        logger.info(f"Successfully fetched Wikipedia content ({len(content)} chars)")
        logger.debug(f"Content after fetching: {content[:500]}...")

        if rev_id:
            logger.info(f"Fetched Wikipedia content with revision ID: {rev_id}")
        else:
            logger.warning("Could not find revision ID for the Wikipedia page")

    def _clean_wikipedia_text(self, text: str) -> str:
        """Clean Wikipedia article text.

        Args:
            text: Raw Wikipedia text

        Returns:
            Cleaned text
        """
        # Remove citation markers like [1], [2], etc.
        text = re.sub(r"\[\d+\]", "", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Fix newlines
        text = re.sub(r"\n\s*\n", "\n\n", text)

        return text.strip()

    def chunk_wikipedia_text(
        self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[ChunkDict]:
        """Split Wikipedia article text into chunks suitable for embedding.

        Args:
            text: Wikipedia article text
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks

        Returns:
            List of chunk dictionaries with text and metadata
        """
        chunks = []

        # Split text into paragraphs
        paragraphs = text.split("\n\n")

        # Initialize variables
        current_chunk = ""
        current_chunk_size = 0
        chunk_index = 0

        for paragraph in paragraphs:
            # If adding this paragraph would exceed the chunk size and we already have content,
            # save the current chunk and start a new one with overlap
            if current_chunk_size + len(paragraph) > chunk_size and current_chunk:
                # Create chunk metadata
                chunk: ChunkDict = {
                    "text": current_chunk.strip(),
                    "chunk_index": chunk_index,
                    "metadata": {
                        "chunk_index": chunk_index,
                    },
                    "total_chunks": 0,  # Will be updated later
                }
                chunks.append(chunk)
                chunk_index += 1

                # Start a new chunk with overlap
                if current_chunk_size > chunk_overlap:
                    # Try to get approximately chunk_overlap characters from the end
                    words = current_chunk.split()
                    overlap_words = words[
                        -((chunk_overlap // 5) + 1) :
                    ]  # Estimate words by average length
                    current_chunk = " ".join(overlap_words)
                    current_chunk_size = len(current_chunk)
                else:
                    # If current chunk is smaller than desired overlap, keep it all
                    current_chunk_size = len(current_chunk)

            # Add the paragraph to the current chunk
            if current_chunk:
                current_chunk += "\n\n" + paragraph
                current_chunk_size += len(paragraph) + 2  # +2 for the newlines
            else:
                current_chunk = paragraph
                current_chunk_size = len(paragraph)

        # Don't forget the last chunk
        if current_chunk:
            final_chunk: ChunkDict = {
                "text": current_chunk.strip(),
                "chunk_index": chunk_index,
                "metadata": {
                    "chunk_index": chunk_index,
                },
                "total_chunks": 0,  # Will be updated later
            }
            chunks.append(final_chunk)

        # Add total chunks information to each chunk's metadata
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk["metadata"]["total_chunks"] = total_chunks
            chunk["total_chunks"] = (
                total_chunks  # Redundant but matches existing code pattern
            )

        logger.info(f"Split Wikipedia article into {len(chunks)} chunks")
        return chunks

    def process_wikipedia_article(
        self,
        article: WikipediaArticleModel,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> Optional[WikipediaContentModel]:
        """Process a Wikipedia article for embedding.

        Args:
            article: WikipediaArticleModel with URL and metadata
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks

        Returns:
            WikipediaContentModel with content and chunks, or None if an error occurs
        """
        try:
            # Fetch the article content and revision ID
            content, rev_id = self.fetch_wikipedia_content(article.url)
            if not content:
                logger.error(f"Content is None for URL: {article.url}")
                return None
            logger.debug(f"Fetched content preview: {content[:500]}...")

            # Update the article model with the revision ID if found
            if rev_id:
                article.rev_id = rev_id
                logger.info(f"Updated article with revision ID: {rev_id}")

            # Chunk the content
            chunks = self.chunk_wikipedia_text(content, chunk_size, chunk_overlap)

            # Enhance chunks with article metadata
            article_metadata = {
                "article_title": article.title,
                "article_url": article.url,
                "source_type": "wikipedia",
                "landmark_id": article.lpNumber,
                "rev_id": rev_id,  # Add revision ID to metadata
            }

            for chunk in chunks:
                chunk["metadata"].update(article_metadata)

            # Create and return the content model
            # Convert ChunkDict to Dict[str, Any] as expected by WikipediaContentModel
            chunks_as_dicts: List[Dict[str, Any]] = [dict(chunk) for chunk in chunks]
            content_model = WikipediaContentModel(
                lpNumber=article.lpNumber,
                url=article.url,
                title=article.title,
                content=content,
                chunks=chunks_as_dicts,
                rev_id=rev_id,  # Include revision ID
                quality=None,  # Quality assessment will be added later
            )

            return content_model

        except Exception as e:
            logger.error(f"Error processing Wikipedia article {article.title}: {e}")
            return None

    def process_landmark_wikipedia_articles(
        self,
        articles: List[WikipediaArticleModel],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> Tuple[List[WikipediaContentModel], WikipediaProcessingResult]:
        """Process all Wikipedia articles for a landmark.

        Args:
            articles: List of WikipediaArticleModel objects
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks

        Returns:
            Tuple of (list of processed articles, processing result summary)
        """
        processed_articles = []
        total_chunks = 0
        errors = 0

        for article in articles:
            try:
                processed_article = self.process_wikipedia_article(
                    article, chunk_size, chunk_overlap
                )
                if processed_article:
                    processed_articles.append(processed_article)
                    if processed_article.chunks:
                        total_chunks += len(processed_article.chunks)
                else:
                    errors += 1
            except Exception as e:
                logger.error(f"Error processing article {article.title}: {e}")
                errors += 1

        # Create a summary of the processing
        result = WikipediaProcessingResult(
            total_landmarks=1,  # This method processes articles for one landmark
            landmarks_with_wikipedia=1 if articles else 0,
            total_articles=len(articles),
            articles_processed=len(processed_articles),
            articles_with_errors=errors,
            total_chunks=total_chunks,
            chunks_embedded=0,  # Embedding happens in a later step
        )

        return processed_articles, result
