"""
PineconeDB class that handles vector operations in Pinecone.
"""

import os
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pinecone
from pinecone import Pinecone

from nyc_landmarks.config.settings import settings
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.enhanced_metadata import EnhancedMetadataCollector

logger = get_logger(__name__)


class PineconeDB:
    """
    Class to handle vector operations in Pinecone.
    """

    def __init__(self, index_name: Optional[str] = None):
        """
        Initialize PineconeDB with connection to Pinecone index.

        Args:
            index_name: Name of the index (optional, uses settings if not provided)
        """
        self.api_key = os.environ.get("PINECONE_API_KEY", settings.PINECONE_API_KEY)
        self.environment = os.environ.get(
            "PINECONE_ENVIRONMENT", settings.PINECONE_ENVIRONMENT
        )
        self.index_name = index_name or os.environ.get(
            "PINECONE_INDEX_NAME", settings.PINECONE_INDEX_NAME
        )
        self.namespace = os.environ.get(
            "PINECONE_NAMESPACE", settings.PINECONE_NAMESPACE
        )
        self.dimensions = settings.PINECONE_DIMENSIONS

        # Initialize Pinecone
        logger.info("Initialized Pinecone client")
        self.pc = Pinecone(api_key=self.api_key)

        # Connect to index
        try:
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone index: {e}")
            raise

    def store_chunks(
        self,
        chunks: List[Dict[str, Any]],
        id_prefix: str = "",
        landmark_id: Optional[str] = None,
        use_fixed_ids: bool = True,
        delete_existing: bool = False,
    ) -> List[str]:
        """
        Store chunks in Pinecone index.

        Args:
            chunks: List of chunks to store, each with text and embedding
            id_prefix: Prefix for vector IDs (optional)
            landmark_id: ID of the landmark for metadata and filtering
            use_fixed_ids: Create deterministic IDs for vectors based on content and landmark
            delete_existing: Delete existing vectors for the landmark before storing new ones

        Returns:
            List of vector IDs stored in Pinecone
        """
        if not chunks:
            logger.warning("No chunks to store")
            return []

        # Delete existing vectors if requested
        if delete_existing and landmark_id:
            logger.info(f"Deleting existing vectors for landmark: {landmark_id}")
            filter_dict = {"landmark_id": landmark_id}
            if id_prefix.startswith("wiki-"):
                filter_dict["source_type"] = "wikipedia"
            elif id_prefix.startswith("test-"):
                filter_dict["source_type"] = "test"
            else:
                filter_dict["source_type"] = "pdf"

            self.delete_vectors_by_filter(filter_dict)

        vectors = []
        vector_ids = []

        # Get enhanced metadata for the landmark if ID is provided
        enhanced_metadata = {}
        if landmark_id:
            try:
                collector = EnhancedMetadataCollector()
                enhanced_metadata = collector.collect_landmark_metadata(landmark_id)
                logger.info(f"Retrieved enhanced metadata for landmark: {landmark_id}")
            except Exception as e:
                logger.warning(f"Could not retrieve enhanced metadata: {e}")
                enhanced_metadata = {}

        # Prepare vectors
        for i, chunk in enumerate(chunks):
            # Generate vector ID
            if use_fixed_ids:
                # Use deterministic ID based on landmark and chunk index
                vector_id = f"{id_prefix}{landmark_id}-chunk-{i}"
            else:
                # Generate random UUID for the vector
                vector_id = f"{id_prefix}{uuid.uuid4()}"

            # Extract embedding and metadata
            embedding = chunk.get("embedding")

            # Determine source type based on prefix
            source_type = "pdf"  # Default
            if id_prefix.startswith("wiki-"):
                source_type = "wikipedia"
            elif id_prefix.startswith("test-"):
                source_type = "test"

            # Basic metadata
            metadata = {
                "text": chunk.get("text", ""),
                "source_type": source_type,
                "chunk_index": i,
            }

            # Add landmark ID if provided
            if landmark_id:
                metadata["landmark_id"] = landmark_id

            # Add processing_date if present in chunk
            if chunk.get("processing_date"):
                metadata["processing_date"] = chunk.get("processing_date")

            # Add processing_date from chunk metadata if available
            if chunk.get("metadata", {}).get("processing_date"):
                metadata["processing_date"] = chunk.get("metadata", {}).get(
                    "processing_date"
                )

            # Add enhanced metadata
            metadata.update(enhanced_metadata)

            # Add Wikipedia-specific metadata
            if source_type == "wikipedia" and "article_metadata" in chunk:
                article_meta = chunk.get("article_metadata", {})
                metadata.update(
                    {
                        "article_title": article_meta.get("title", ""),
                        "article_url": article_meta.get("url", ""),
                    }
                )

            # Create vector
            vector = {"id": vector_id, "values": embedding, "metadata": metadata}

            vectors.append(vector)
            vector_ids.append(vector_id)

        # Store in batches of 100
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            try:
                self.index.upsert(vectors=batch)
            except Exception as e:
                logger.error(f"Failed to store chunk batch {i//batch_size}: {e}")

        logger.info(f"Stored {len(vector_ids)} vectors")
        return vector_ids

    def store_chunks_with_fixed_ids(
        self, chunks: List[Dict[str, Any]], landmark_id: str
    ) -> List[str]:
        """
        Store chunks with fixed IDs based on landmark ID and chunk index.
        This is a convenience wrapper around store_chunks.

        Args:
            chunks: List of chunks to store, each with text and embedding
            landmark_id: ID of the landmark for fixed ID generation and metadata

        Returns:
            List of vector IDs stored in Pinecone
        """
        return self.store_chunks(
            chunks=chunks,
            landmark_id=landmark_id,
            id_prefix="",
            use_fixed_ids=True,
            delete_existing=True,
        )

    def query_vectors(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query vectors from Pinecone index.

        Args:
            query_vector: Embedding of the query text
            top_k: Number of results to return
            filter_dict: Dictionary of metadata filters

        Returns:
            List of matching vectors with metadata
        """
        try:
            response = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict,
            )

            # Convert response to dict format
            matches = response.get("matches", [])
            # Ensure matches is a list of dicts
            result_list = []
            for match in matches:
                if isinstance(match, dict):
                    result_list.append(match)
                else:
                    # Convert object to dict if needed
                    match_dict = {
                        "id": match.id if hasattr(match, "id") else "",
                        "score": match.score if hasattr(match, "score") else 0.0,
                        "metadata": (
                            match.metadata if hasattr(match, "metadata") else {}
                        ),
                    }
                    result_list.append(match_dict)

            return result_list

        except Exception as e:
            logger.error(f"Failed to query vectors: {e}")
            return []

    def delete_vectors(self, vector_ids: List[str]) -> int:
        """
        Delete vectors from Pinecone index.

        Args:
            vector_ids: List of vector IDs to delete

        Returns:
            Number of vectors deleted
        """
        if not vector_ids:
            return 0

        try:
            # Delete in batches of 100
            batch_size = 100
            deleted_count = 0

            for i in range(0, len(vector_ids), batch_size):
                batch = vector_ids[i : i + batch_size]
                self.index.delete(ids=batch)
                deleted_count += len(batch)

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            return 0

    def delete_vectors_by_filter(self, filter_dict: Dict[str, Any]) -> int:
        """
        Delete vectors by metadata filter.

        Args:
            filter_dict: Dictionary of metadata filters

        Returns:
            Number of vectors deleted (approximate)
        """
        try:
            # Count vectors matching filter
            stats_response = self.index.query(
                vector=[0.0] * 1536,  # Dummy vector
                top_k=1,
                filter=filter_dict,
                include_metadata=False,
            )

            # Delete by filter
            delete_response = self.index.delete(filter=filter_dict)

            logger.info(f"Deleted vectors matching filter: {filter_dict}")
            return 1  # No way to know exact count from delete response

        except Exception as e:
            logger.error(f"Failed to delete vectors by filter: {e}")
            return 0

    def list_vectors_by_source(
        self, source_type: str, limit: int = 1000, landmark_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List vectors by source type.

        Args:
            source_type: Source type to filter by ("wikipedia", "pdf", or "test")
            limit: Maximum number of vectors to return
            landmark_id: Optional landmark ID to filter by

        Returns:
            Dictionary with matches containing vectors and metadata
        """
        try:
            # Create filter dictionary
            filter_dict = {"source_type": source_type}
            if landmark_id:
                filter_dict["landmark_id"] = landmark_id

            # Query with dummy vector to get metadata
            response = self.index.query(
                vector=[0.0] * 1536,  # Dummy vector
                top_k=limit,
                filter=filter_dict,
                include_metadata=True,
            )

            # Check if response is already a dictionary
            if isinstance(response, dict):
                return response

            # Convert to dict for consistent return type
            try:
                return dict(response)
            except Exception:
                # Handle case where response can't be converted to dict
                if hasattr(response, "matches"):
                    matches = []
                    for match in response.matches:
                        match_dict = {
                            "id": getattr(match, "id", ""),
                            "score": getattr(match, "score", 0.0),
                            "metadata": getattr(match, "metadata", {}),
                        }
                        matches.append(match_dict)
                    return {"matches": matches}
                return {"matches": []}

        except Exception as e:
            logger.error(f"Failed to list vectors by source: {e}")
            return {"matches": []}

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Pinecone index.

        Returns:
            Dictionary with index statistics
        """
        try:
            stats = self.index.describe_index_stats()
            # Convert to dict for consistent return type
            if isinstance(stats, dict):
                return stats
            return {
                "namespaces": {},
                "dimension": 0,
                "index_fullness": 0.0,
                "total_vector_count": 0,
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {}
