"""
Wikipedia content fetcher module for NYC Landmarks Vector Database.

This module handles fetching and processing Wikipedia article content
for landmarks to be embedded and stored in the vector database.
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
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

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class WikipediaFetcher:
    """Wikipedia content fetcher for landmark articles."""

    def __init__(self) -> None:
        """Initialize the Wikipedia fetcher."""
        # Set up basic configuration
        self.user_agent = (
            "NYCLandmarksVectorDB/1.0 (https://github.com/username/nyc-landmarks-vector-db; "
            "email@example.com) Python-Requests/2.31.0"
        )
        self.headers = {"User-Agent": self.user_agent}
        self.rate_limit_delay = 1.0  # Seconds between requests to be polite
        logger.info("Initialized Wikipedia content fetcher")

    @retry(
        retry=retry_if_exception_type(
            (requests.ConnectionError, requests.Timeout, requests.HTTPError)
        ),
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def fetch_wikipedia_content(self, url: str) -> Optional[str]:
        """Fetch the content of a Wikipedia article.

        Args:
            url: URL of the Wikipedia article

        Returns:
            The article content as text, or None if an error occurs
        """
        if not url.startswith(("http://", "https://")):
            logger.warning(f"Invalid URL format: {url}")
            return None

        try:
            logger.info(f"Fetching Wikipedia content from: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            # Parse HTML content
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract the main content div
            content_div = soup.find("div", {"id": "mw-content-text"})
            if not content_div:
                logger.warning(f"Could not find main content in Wikipedia page: {url}")
                return None

            # Find all paragraphs in the content
            paragraphs = content_div.find_all("p")
            content = "\n\n".join([p.get_text() for p in paragraphs])

            # Clean up the text
            content = self._clean_wikipedia_text(content)

            # Add a delay to respect rate limits
            time.sleep(self.rate_limit_delay)

            logger.info(
                f"Successfully fetched Wikipedia content ({len(content)} chars)"
            )
            return content

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Wikipedia content from {url}: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error processing Wikipedia content from {url}: {e}"
            )
            return None

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
    ) -> List[Dict[str, Any]]:
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
                chunk = {
                    "text": current_chunk.strip(),
                    "chunk_index": chunk_index,
                    "metadata": {
                        "chunk_index": chunk_index,
                    },
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
            chunk = {
                "text": current_chunk.strip(),
                "chunk_index": chunk_index,
                "metadata": {
                    "chunk_index": chunk_index,
                },
            }
            chunks.append(chunk)

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
            # Fetch the article content
            content = self.fetch_wikipedia_content(article.url)
            if not content:
                logger.warning(f"No content retrieved for article: {article.title}")
                return None

            # Chunk the content
            chunks = self.chunk_wikipedia_text(content, chunk_size, chunk_overlap)

            # Enhance chunks with article metadata
            for chunk in chunks:
                chunk["metadata"]["article_title"] = article.title
                chunk["metadata"]["article_url"] = article.url
                chunk["metadata"]["source_type"] = "wikipedia"
                chunk["metadata"]["landmark_id"] = article.lpNumber

            # Create and return the content model
            content_model = WikipediaContentModel(
                lpNumber=article.lpNumber,
                url=article.url,
                title=article.title,
                content=content,
                chunks=chunks,
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
