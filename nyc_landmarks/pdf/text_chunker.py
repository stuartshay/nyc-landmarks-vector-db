"""
Text chunking module for NYC Landmarks Vector Database.

This module handles preprocessing and chunking of text extracted
from landmark PDFs to prepare for embedding generation.
"""

import logging
import re
from typing import Any, Dict, List, Optional

import tiktoken

from nyc_landmarks.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class TextChunker:
    """Text preprocessing and chunking for PDF text."""

    def __init__(
        self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None
    ):
        """Initialize the text chunker with configuration.

        Args:
            chunk_size: Maximum chunk size in tokens (default: from settings)
            chunk_overlap: Overlap between chunks in tokens (default: from settings)
        """
        self.chunk_size = chunk_size if chunk_size is not None else settings.CHUNK_SIZE
        self.chunk_overlap = (
            chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP
        )

        # Initialize tokenizer for counting tokens
        # We use 'cl100k_base' which is used by text-embedding-3-small/large
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        logger.info(
            f"Initialized TextChunker with chunk_size={self.chunk_size}, "
            f"chunk_overlap={self.chunk_overlap}"
        )

    def preprocess_text(self, text: str) -> str:
        """Preprocess text to improve chunking and embedding quality.

        Args:
            text: Raw text extracted from PDF

        Returns:
            Preprocessed text
        """
        if not text:
            return ""

        # Replace multiple newlines with single newline
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Replace multiple spaces with single space
        text = re.sub(r" {2,}", " ", text)

        # Remove any non-printable characters
        text = re.sub(r"[^\x20-\x7E\n]", "", text)

        # Trim whitespace
        text = text.strip()

        return text

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text.

        Args:
            text: Text to count tokens for

        Returns:
            Token count
        """
        tokens = self.tokenizer.encode(text)
        return len(tokens)

    def chunk_text_by_tokens(self, text: str) -> List[str]:
        """Chunk text by token count with overlap.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if not text:
            return []

        # Preprocess the text
        text = self.preprocess_text(text)

        # Tokenize the text
        tokens = self.tokenizer.encode(text)

        # Calculate the chunk size and overlap in tokens
        chunk_size = self.chunk_size
        chunk_overlap = self.chunk_overlap

        # If the text is shorter than the chunk size, return it as a single chunk
        if len(tokens) <= chunk_size:
            return [text]

        # Initialize variables for chunking
        chunks = []
        start_idx = 0

        # Chunk the text by token count
        while start_idx < len(tokens):
            # Calculate the end index for this chunk
            end_idx = min(start_idx + chunk_size, len(tokens))

            # Get the chunk tokens
            chunk_tokens = tokens[start_idx:end_idx]

            # Convert tokens back to text
            chunk = self.tokenizer.decode(chunk_tokens)

            # Add the chunk to the list
            chunks.append(chunk)

            # Update the start index for the next chunk
            # We move forward by chunk_size - chunk_overlap
            start_idx += chunk_size - chunk_overlap

            # If we'd end up with a tiny final chunk, just stop
            if len(tokens) - start_idx < chunk_size / 3:
                break

        # Handle any remaining text if we broke out of the loop early
        if start_idx < len(tokens):
            chunk_tokens = tokens[start_idx:]
            chunk = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk)

        logger.info(f"Chunked text into {len(chunks)} chunks")
        return chunks

    def chunk_with_metadata(
        self, text: str, metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Chunk text and add metadata to each chunk.

        Args:
            text: Text to chunk
            metadata: Metadata to add to each chunk

        Returns:
            List of dictionaries containing chunk text and metadata
        """
        # Chunk the text
        chunks = self.chunk_text_by_tokens(text)

        # Create a list of chunk dictionaries with metadata
        chunk_dicts = []
        for i, chunk in enumerate(chunks):
            # Create a copy of the metadata
            chunk_metadata = metadata.copy()

            # Add chunk-specific metadata
            chunk_metadata["chunk_index"] = i
            chunk_metadata["chunk_count"] = len(chunks)
            chunk_metadata["token_count"] = self.count_tokens(chunk)

            # Create the chunk dictionary
            chunk_dict = {
                "text": chunk,
                "metadata": chunk_metadata,
            }

            chunk_dicts.append(chunk_dict)

        return chunk_dicts

    def process_landmark_text(
        self,
        text: str,
        landmark_id: str,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Process text for a landmark and chunk it with metadata.

        Args:
            text: Text to process and chunk
            landmark_id: ID of the landmark
            additional_metadata: Additional metadata to add to each chunk

        Returns:
            List of dictionaries containing chunk text and metadata
        """
        # Create metadata dictionary
        metadata = {
            "landmark_id": landmark_id,
            "source": "landmark_pdf",
        }

        # Add any additional metadata
        if additional_metadata:
            metadata.update(additional_metadata)

        # Chunk the text with metadata
        return self.chunk_with_metadata(text, metadata)
