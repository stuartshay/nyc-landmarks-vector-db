"""
Embedding generation module for NYC Landmarks Vector Database.

This module handles the generation of text embeddings using OpenAI's API.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import openai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from nyc_landmarks.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class EmbeddingGenerator:
    """Text embedding generation using OpenAI API."""

    def __init__(self) -> None:
        """Initialize the embedding generator with OpenAI API credentials."""
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_EMBEDDING_MODEL
        self.dimensions = settings.OPENAI_EMBEDDING_DIMENSIONS

        # Initialize OpenAI client if API key is provided
        if self.api_key:
            openai.api_key = self.api_key

            # Set OpenAI API base if provided
            if settings.OPENAI_API_BASE:
                openai.base_url = settings.OPENAI_API_BASE

            logger.info(f"Initialized OpenAI client with model: {self.model}")
        else:
            logger.warning("OpenAI API key not provided")

    @retry(
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        reraise=True,
    )
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding vector as a list of floats
        """
        if not text:
            logger.warning("Attempted to generate embedding for empty text")
            return [0.0] * self.dimensions

        try:
            # Generate embedding using OpenAI API
            response = openai.embeddings.create(input=text, model=self.model)

            # Extract embedding from response
            embedding = response.data[0].embedding

            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def generate_embeddings_batch(
        self, texts: List[str], batch_size: int = 20
    ) -> List[List[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to generate embeddings for
            batch_size: Maximum number of texts per API call

        Returns:
            List of embedding vectors
        """
        if not texts:
            logger.warning("Attempted to generate embeddings for empty text list")
            return []

        # Initialize list to store embeddings
        embeddings = []

        # Process texts in batches
        for i in range(0, len(texts), batch_size):
            # Get batch of texts
            batch = texts[i : i + batch_size]

            try:
                # Generate embeddings for batch
                response = openai.embeddings.create(input=batch, model=self.model)

                # Extract embeddings from response
                batch_embeddings = [item.embedding for item in response.data]

                # Add batch embeddings to list
                embeddings.extend(batch_embeddings)

                logger.info(
                    f"Generated embeddings for batch {i//batch_size + 1} of {(len(texts) + batch_size - 1) // batch_size}"
                )

                # Sleep to avoid rate limits (if not the last batch)
                if i + batch_size < len(texts):
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error generating embeddings for batch: {e}")
                raise

        return embeddings

    def process_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process text chunks and add embeddings.

        Args:
            chunks: List of chunk dictionaries with text and metadata

        Returns:
            List of chunk dictionaries with embeddings added
        """
        # Extract texts from chunks
        texts = [chunk["text"] for chunk in chunks]

        # Generate embeddings for texts
        embeddings = self.generate_embeddings_batch(texts)

        # Add embeddings to chunks
        processed_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            # Create a copy of the chunk with the embedding added
            processed_chunk = chunk.copy()
            processed_chunk["embedding"] = embedding

            processed_chunks.append(processed_chunk)

        logger.info(f"Processed {len(processed_chunks)} chunks with embeddings")
        return processed_chunks
