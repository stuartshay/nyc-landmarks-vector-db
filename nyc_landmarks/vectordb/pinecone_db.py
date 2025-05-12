"""
PineconeDB class that handles vector operations in Pinecone.
"""

import os
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

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
            self._connect_to_index()
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone index: {e}")
            raise

    def _connect_to_index(self) -> None:
        """
        Internal method to connect to Pinecone index.
        Used for initial connection and reconnection after index recreation.
        """
        # Ensure index_name is not None before connecting
        if not self.index_name:
            raise ValueError("Pinecone index name cannot be None")

        self.index = self.pc.Index(self.index_name)
        logger.info(f"Connected to Pinecone index: {self.index_name}")

    def _get_source_type_from_prefix(self, id_prefix: str) -> str:
        """
        Determine source type based on ID prefix.

        Args:
            id_prefix: The prefix to analyze

        Returns:
            Source type string
        """
        if id_prefix.startswith("wiki-"):
            return "wikipedia"
        elif id_prefix.startswith("test-"):
            return "test"
        else:
            return "pdf"  # Default

    def _get_filter_dict_for_deletion(
        self, landmark_id: str, id_prefix: str
    ) -> Dict[str, str]:
        """
        Create filter dictionary for deleting existing vectors.

        Args:
            landmark_id: ID of the landmark
            id_prefix: Prefix for vector IDs

        Returns:
            Filter dictionary
        """
        filter_dict = {"landmark_id": landmark_id}
        filter_dict["source_type"] = self._get_source_type_from_prefix(id_prefix)
        return filter_dict

    def _get_enhanced_metadata(self, landmark_id: str) -> Dict[str, Any]:
        """
        Get enhanced metadata for a landmark.

        Args:
            landmark_id: ID of the landmark

        Returns:
            Enhanced metadata dictionary
        """
        enhanced_metadata = {}
        try:
            collector = EnhancedMetadataCollector()
            enhanced_metadata = collector.collect_landmark_metadata(landmark_id)
            logger.info(f"Retrieved enhanced metadata for landmark: {landmark_id}")
        except Exception as e:
            logger.warning(f"Could not retrieve enhanced metadata: {e}")
        return enhanced_metadata

    def _generate_vector_id(
        self,
        id_prefix: str,
        landmark_id: Optional[str],
        index: int,
        use_fixed_ids: bool,
    ) -> str:
        """
        Generate vector ID.

        Args:
            id_prefix: Prefix for vector ID
            landmark_id: ID of the landmark
            index: Index of the chunk
            use_fixed_ids: Whether to use fixed IDs

        Returns:
            Generated vector ID
        """
        if use_fixed_ids and landmark_id:
            # Use deterministic ID based on landmark and chunk index
            return f"{id_prefix}{landmark_id}-chunk-{index}"
        else:
            # Generate random UUID for the vector
            return f"{id_prefix}{uuid.uuid4()}"

    def _create_metadata_for_chunk(
        self,
        chunk: Dict[str, Any],
        source_type: str,
        chunk_index: int,
        landmark_id: Optional[str],
        enhanced_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create metadata dictionary for a chunk.

        Args:
            chunk: The chunk dictionary
            source_type: Source type string
            chunk_index: Index of the chunk
            landmark_id: ID of the landmark
            enhanced_metadata: Enhanced metadata dictionary

        Returns:
            Metadata dictionary
        """
        # Basic metadata
        metadata = {
            "text": chunk.get("text", ""),
            "source_type": source_type,
            "chunk_index": chunk_index,
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

        # Filter out null values from enhanced metadata before adding
        filtered_metadata = {
            k: v for k, v in enhanced_metadata.items() if v is not None
        }
        metadata.update(filtered_metadata)

        # Add Wikipedia-specific metadata
        if source_type == "wikipedia" and "article_metadata" in chunk:
            article_meta = chunk.get("article_metadata", {})
            # Filter out null values from article metadata
            article_data = {
                "article_title": article_meta.get("title", ""),
                "article_url": article_meta.get("url", ""),
            }
            metadata.update({k: v for k, v in article_data.items() if v is not None})

        return metadata

    def _upsert_vectors_in_batches(
        self, vectors: List[Dict[str, Any]], batch_size: int = 100
    ) -> None:
        """
        Upsert vectors in batches.

        Args:
            vectors: List of vectors to upsert
            batch_size: Size of each batch
        """
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            try:
                # Convert to the expected type for the Pinecone SDK
                self.index.upsert(vectors=batch)  # pyright: ignore
            except Exception as e:
                logger.error(f"Failed to store chunk batch {i // batch_size}: {e}")

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
            filter_dict = self._get_filter_dict_for_deletion(landmark_id, id_prefix)
            self.delete_vectors_by_filter(filter_dict)

        vectors = []
        vector_ids = []

        # Get enhanced metadata for the landmark if ID is provided
        enhanced_metadata = {}
        if landmark_id:
            enhanced_metadata = self._get_enhanced_metadata(landmark_id)

        # Determine source type based on prefix
        source_type = self._get_source_type_from_prefix(id_prefix)

        # Prepare vectors
        for i, chunk in enumerate(chunks):
            # Generate vector ID
            vector_id = self._generate_vector_id(
                id_prefix, landmark_id, i, use_fixed_ids
            )

            # Extract embedding
            embedding = chunk.get("embedding")

            # Create metadata
            metadata = self._create_metadata_for_chunk(
                chunk, source_type, i, landmark_id, enhanced_metadata
            )

            # Create vector
            vector = {"id": vector_id, "values": embedding, "metadata": metadata}

            vectors.append(vector)
            vector_ids.append(vector_id)

        # Store vectors in batches
        self._upsert_vectors_in_batches(vectors)

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

            # Process the response to extract matches
            result_list: List[Dict[str, Any]] = []

            # Handle response.matches which can be a list or other iterable
            # Cast response to Any to handle different return types from Pinecone SDK
            from typing import Any as TypeAny
            from typing import cast

            response_dict = cast(TypeAny, response)

            # Access matches safely
            matches = getattr(response_dict, "matches", [])
            for match in matches:
                # Handle match objects
                match_dict: Dict[str, Any] = {}

                # Extract ID if available
                if hasattr(match, "id"):
                    match_dict["id"] = match.id

                # Extract score if available
                if hasattr(match, "score"):
                    match_dict["score"] = match.score

                # Extract metadata if available
                if hasattr(match, "metadata"):
                    match_dict["metadata"] = match.metadata

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
            # Delete by filter
            self.index.delete(filter=filter_dict)

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
            filter_dict: Dict[str, Any] = {"source_type": source_type}
            if landmark_id:
                filter_dict["landmark_id"] = landmark_id

            # Query with dummy vector to get metadata
            dimension = self.dimensions
            dummy_vector = [0.0] * dimension
            response = self.index.query(
                vector=dummy_vector,
                top_k=limit,
                filter=filter_dict,
                include_metadata=True,
                include_values=True,  # Explicitly request embedding values
            )

            # Process the response to create a standardized return format
            result: Dict[str, Any] = {"matches": []}

            # Cast response to Any to handle different return types from Pinecone SDK
            from typing import Any as TypeAny
            from typing import cast

            response_dict = cast(TypeAny, response)

            # Extract matches from the response safely
            matches = getattr(response_dict, "matches", [])
            matches_list = []
            for match in matches:
                match_dict = {
                    "id": getattr(match, "id", ""),
                    "score": getattr(match, "score", 0.0),
                    "metadata": getattr(match, "metadata", {}),
                    "values": getattr(
                        match, "values", []
                    ),  # Include the embedding values
                }
                matches_list.append(match_dict)
            result["matches"] = matches_list

            return result

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

            # Create a standardized stats dictionary
            result = {
                "namespaces": {},
                "dimension": 0,
                "index_fullness": 0.0,
                "total_vector_count": 0,
            }

            # Extract values from stats object if available
            if hasattr(stats, "namespaces"):
                result["namespaces"] = stats.namespaces
            if hasattr(stats, "dimension"):
                result["dimension"] = stats.dimension
            if hasattr(stats, "index_fullness"):
                result["index_fullness"] = stats.index_fullness
            if hasattr(stats, "total_vector_count"):
                result["total_vector_count"] = stats.total_vector_count

            return result
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {}

    def recreate_index(self) -> bool:
        """
        Recreate the Pinecone index by deleting and creating it again.

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.index_name:
            logger.error("Index name is not set, cannot recreate index")
            return False

        try:
            # Initialize direct Pinecone client for index operations
            from pinecone import Pinecone, ServerlessSpec

            pc = Pinecone(api_key=self.api_key)

            # Delete the existing index if it exists
            try:
                pc.delete_index(self.index_name)
                logger.info(f"Deleted existing index: {self.index_name}")
            except Exception as e:
                logger.warning(f"Index deletion warning (may not exist yet): {e}")

            # Create the new index
            try:
                # Using standard OpenAI embedding dimensions with ServerlessSpec
                pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric="cosine",
                    spec=ServerlessSpec(cloud="gcp", region="us-central1"),
                )
                logger.info(f"Created new index: {self.index_name}")

                # Wait for the index to be ready and reconnect
                logger.info("Waiting for index to be ready...")
                time.sleep(30)

                # Reinitialize connection to the new index
                self._connect_to_index()

                return True
            except Exception as e:
                logger.error(f"Failed to create index: {e}")
                return False

        except Exception as e:
            logger.error(f"Failed to recreate index: {e}")
            return False

    def store_vectors_batch(
        self, vectors: List[Tuple[str, List[float], Dict[str, Any]]]
    ) -> bool:
        """
        Store a batch of vectors in Pinecone using the low-level API.

        Args:
            vectors: List of tuples containing (id, embedding, metadata)

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.index:
            logger.error("Index not initialized")
            return False

        try:
            # Convert to format expected by upsert
            pinecone_vectors = []
            for vector_id, embedding, metadata in vectors:
                pinecone_vectors.append(
                    {"id": vector_id, "values": embedding, "metadata": metadata}
                )

            # Use batch size of 100 as recommended by Pinecone
            batch_size = 100
            for i in range(0, len(pinecone_vectors), batch_size):
                batch = pinecone_vectors[i : i + batch_size]
                self.index.upsert(vectors=batch)

            logger.info(f"Successfully stored {len(pinecone_vectors)} vectors")
            return True
        except Exception as e:
            logger.error(f"Error storing vectors batch: {e}")
            return False

    def delete_index(self) -> bool:
        """
        Delete the Pinecone index.

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.index_name:
            logger.error("Index name is not set, cannot delete index")
            return False

        try:
            # Initialize direct Pinecone client for index operations
            from pinecone import Pinecone

            pc = Pinecone(api_key=self.api_key)

            # Delete the index
            pc.delete_index(self.index_name)
            logger.info(f"Deleted index: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete index: {e}")
            return False
