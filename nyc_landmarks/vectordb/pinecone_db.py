"""
Pinecone vector database module for NYC Landmarks Vector Database.

This module handles interactions with the Pinecone vector database service,
including storing and retrieving embeddings.
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

from pinecone import Pinecone, ServerlessSpec

from nyc_landmarks.config.settings import settings
from nyc_landmarks.vectordb.enhanced_metadata import get_metadata_collector

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class PineconeDB:
    """Pinecone vector database operations."""

    def __init__(self):
        """Initialize the Pinecone database with credentials."""
        self.api_key = settings.PINECONE_API_KEY
        self.environment = settings.PINECONE_ENVIRONMENT
        self.index_name = settings.PINECONE_INDEX_NAME
        self.namespace = settings.PINECONE_NAMESPACE
        self.dimensions = settings.PINECONE_DIMENSIONS
        self.metric = settings.PINECONE_METRIC
        self.pinecone_client = None
        self.index = None
        self.metadata_collector = get_metadata_collector()

        # Initialize Pinecone client if API key is provided
        if self.api_key and self.environment:
            try:
                # Initialize Pinecone client with new API
                self.pinecone_client = Pinecone(api_key=self.api_key)
                logger.info(
                    f"Initialized Pinecone client in environment: {self.environment}"
                )

                # Connect to index
                self._connect_to_index()
            except Exception as e:
                logger.error(f"Error initializing Pinecone: {e}")
        else:
            logger.warning("Pinecone API key or environment not provided")

    def _connect_to_index(self):
        """Connect to the Pinecone index, creating it if it doesn't exist."""
        try:
            # Check if index exists
            index_list = self.pinecone_client.list_indexes()
            if self.index_name not in index_list.names():
                logger.info(f"Index '{self.index_name}' does not exist, creating...")

                # Create index with ServerlessSpec
                self.pinecone_client.create_index(
                    name=self.index_name,
                    dimension=self.dimensions,
                    metric=self.metric,
                    spec=ServerlessSpec(cloud="aws", region="us-west-2"),
                )

                # Wait for index to be ready
                logger.info("Waiting for index to initialize...")
                time.sleep(30)

            # Connect to index
            self.index = self.pinecone_client.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
        except Exception as e:
            logger.error(f"Error connecting to Pinecone index: {e}")
            raise

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the index.

        Returns:
            Dictionary containing index statistics
        """
        if not self.index:
            logger.error("Pinecone index not initialized")
            return {"error": "Index not initialized"}

        try:
            stats = self.index.describe_index_stats()
            return stats
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {"error": str(e)}

    def store_vector(
        self, vector_id: str, vector: List[float], metadata: Dict[str, Any]
    ) -> bool:
        """Store a single vector in the index.

        Args:
            vector_id: ID for the vector
            vector: Embedding vector as a list of floats
            metadata: Metadata to store with the vector

        Returns:
            True if successful, False otherwise
        """
        if not self.index:
            logger.error("Pinecone index not initialized")
            return False

        try:
            # Upsert the vector using new API
            self.index.upsert(
                vectors=[{"id": vector_id, "values": vector, "metadata": metadata}],
                namespace=self.namespace,
            )
            logger.debug(f"Stored vector with ID: {vector_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing vector: {e}")
            return False

    def store_vectors_batch(
        self, vectors: List[Tuple[str, List[float], Dict[str, Any]]]
    ) -> bool:
        """Store a batch of vectors in the index.

        Args:
            vectors: List of tuples (id, vector, metadata)

        Returns:
            True if successful, False otherwise
        """
        if not self.index:
            logger.error("Pinecone index not initialized")
            return False

        if not vectors:
            logger.warning("Attempted to store empty vectors list")
            return True

        try:
            # Convert tuples to the format expected by the new API
            formatted_vectors = [
                {"id": id, "values": values, "metadata": metadata}
                for id, values, metadata in vectors
            ]

            # Upsert the vectors using new API
            self.index.upsert(vectors=formatted_vectors, namespace=self.namespace)
            logger.info(f"Stored {len(vectors)} vectors")
            return True
        except Exception as e:
            logger.error(f"Error storing vectors: {e}")
            return False

    def store_chunks(
        self, chunks: List[Dict[str, Any]], id_prefix: str = "", landmark_id: Optional[str] = None
    ) -> List[str]:
        """Store text chunks with embeddings in the index.

        Args:
            chunks: List of chunk dictionaries with text, metadata, and embedding
            id_prefix: Prefix for vector IDs (optional)
            landmark_id: Landmark ID to fetch enhanced metadata (optional)

        Returns:
            List of stored vector IDs
        """
        if not chunks:
            logger.warning("Attempted to store empty chunks list")
            return []

        # Get enhanced metadata if landmark_id is provided
        enhanced_metadata = {}
        if landmark_id:
            enhanced_metadata = self.metadata_collector.collect_landmark_metadata(landmark_id)
            logger.info(f"Retrieved enhanced metadata for landmark: {landmark_id}")

        # Prepare vectors for batch storage
        vectors = []
        vector_ids = []

        for chunk in chunks:
            # Check if chunk has required fields
            if "embedding" not in chunk or "metadata" not in chunk:
                logger.warning(f"Chunk missing required fields: {chunk.keys()}")
                continue

            # Generate a vector ID
            vector_id = f"{id_prefix}{str(uuid.uuid4())}"
            vector_ids.append(vector_id)

            # Get the embedding
            embedding = chunk["embedding"]

            # Get the metadata and add the text for retrieval
            metadata = chunk["metadata"].copy()
            metadata["text"] = chunk["text"]  # Include the text in metadata for retrieval

            # Merge with enhanced metadata if available
            if enhanced_metadata:
                # Keep only metadata fields that won't conflict with chunk-specific metadata
                # and don't exceed Pinecone's metadata size limits
                for key, value in enhanced_metadata.items():
                    if key not in metadata and key != "text":
                        metadata[key] = value

            # Add chunk position information if available
            if "chunk_index" in chunk:
                metadata["chunk_index"] = chunk["chunk_index"]

            # Add to vectors list
            vectors.append((vector_id, embedding, metadata))

        # Store the vectors
        success = self.store_vectors_batch(vectors)

        if success:
            return vector_ids
        else:
            return []

    def query_vectors(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query the index for similar vectors.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter_dict: Filter to apply to the query

        Returns:
            List of matched vectors with metadata
        """
        if not self.index:
            logger.error("Pinecone index not initialized")
            return []

        try:
            # Query the index using new API
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                namespace=self.namespace,
                filter=filter_dict,
            )

            # Process results
            matches = results.matches
            logger.info(f"Query returned {len(matches)} matches")

            return matches
        except Exception as e:
            logger.error(f"Error querying vectors: {e}")
            return []

    def delete_vectors(self, vector_ids: List[str]) -> bool:
        """Delete vectors from the index.

        Args:
            vector_ids: List of vector IDs to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.index:
            logger.error("Pinecone index not initialized")
            return False

        if not vector_ids:
            logger.warning("Attempted to delete empty vector IDs list")
            return True

        try:
            # Delete the vectors
            self.index.delete(ids=vector_ids, namespace=self.namespace)
            logger.info(f"Deleted {len(vector_ids)} vectors")
            return True
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            return False

    def delete_by_metadata(self, filter_dict: Dict[str, Any]) -> bool:
        """Delete vectors matching metadata filter.

        Args:
            filter_dict: Filter to apply for deletion

        Returns:
            True if successful, False otherwise
        """
        if not self.index:
            logger.error("Pinecone index not initialized")
            return False

        try:
            # Delete vectors by metadata filter
            self.index.delete(filter=filter_dict, namespace=self.namespace)
            logger.info(f"Deleted vectors matching filter: {filter_dict}")
            return True
        except Exception as e:
            logger.error(f"Error deleting vectors by metadata: {e}")
            return False
