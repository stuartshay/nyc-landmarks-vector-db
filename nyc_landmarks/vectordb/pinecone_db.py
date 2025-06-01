"""
PineconeDB class that handles vector operations in Pinecone.
"""

import os
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, cast

from pinecone import Pinecone

from nyc_landmarks.config.settings import settings
from nyc_landmarks.models.metadata_models import LandmarkMetadata
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
        logger.info(f"Using Pinecone namespace: {self.namespace}")

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
        enhanced_metadata_obj: Optional[LandmarkMetadata] = None
        try:
            collector = EnhancedMetadataCollector()
            enhanced_metadata_obj = collector.collect_landmark_metadata(landmark_id)
            logger.info(f"Retrieved enhanced metadata for landmark: {landmark_id}")
        except Exception as e:
            logger.warning(f"Could not retrieve enhanced metadata: {e}")

        # Convert LandmarkMetadata to dictionary or return empty dict if it failed
        return enhanced_metadata_obj.model_dump() if enhanced_metadata_obj else {}

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
        # Build basic metadata
        metadata = self._build_basic_metadata(
            chunk, source_type, chunk_index, landmark_id
        )

        # Add processing date from chunk
        self._add_processing_date(metadata, chunk)

        # Add enhanced metadata (filtered)
        filtered_enhanced = self._filter_enhanced_metadata(enhanced_metadata)
        metadata.update(filtered_enhanced)

        # Add source-specific metadata
        if source_type == "wikipedia":
            self._add_wikipedia_metadata(metadata, chunk)

        return metadata

    def _build_basic_metadata(
        self,
        chunk: Dict[str, Any],
        source_type: str,
        chunk_index: int,
        landmark_id: Optional[str],
    ) -> Dict[str, Any]:
        """Build basic metadata fields for a chunk."""
        metadata = {
            "text": chunk.get("text", ""),
            "source_type": source_type,
            "chunk_index": chunk_index,
        }

        if landmark_id:
            metadata["landmark_id"] = landmark_id

        return metadata

    def _add_processing_date(
        self, metadata: Dict[str, Any], chunk: Dict[str, Any]
    ) -> None:
        """Add processing date to metadata from chunk if available."""
        # Check direct chunk processing_date
        if chunk.get("processing_date"):
            metadata["processing_date"] = chunk.get("processing_date")
        # Check chunk metadata processing_date
        elif chunk.get("metadata", {}).get("processing_date"):
            metadata["processing_date"] = chunk.get("metadata", {}).get(
                "processing_date"
            )

    def _filter_enhanced_metadata(
        self, enhanced_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Filter enhanced metadata to remove unsupported types and null values."""
        filtered_metadata = {}
        try:
            for k, v in enhanced_metadata.items():
                if v is None:
                    continue
                # Skip source_type to preserve the correct source_type from chunk
                if k == "source_type":
                    continue
                # Skip unsupported data types (except buildings list)
                if isinstance(v, (list, dict)) and k != "buildings":
                    logger.warning(f"Skipping unsupported metadata field: {k}")
                    continue
                filtered_metadata[k] = v
        except Exception as e:
            logger.error(f"Error processing enhanced metadata: {e}")

        return filtered_metadata

    def _add_wikipedia_metadata(
        self, metadata: Dict[str, Any], chunk: Dict[str, Any]
    ) -> None:
        """Add Wikipedia-specific metadata to the metadata dictionary."""
        # Extract chunk metadata
        chunk_metadata = chunk.get("metadata", {})

        # Add article quality information if available
        if chunk_metadata.get("article_quality"):
            metadata["article_quality"] = chunk_metadata["article_quality"]
        if chunk_metadata.get("article_quality_score"):
            metadata["article_quality_score"] = chunk_metadata["article_quality_score"]
        if chunk_metadata.get("article_quality_description"):
            metadata["article_quality_description"] = chunk_metadata[
                "article_quality_description"
            ]

        # Handle new metadata format (chunk.metadata) and check for article details.
        if chunk_metadata.get("article_title") or chunk_metadata.get("article_url"):
            article_data = {
                "article_title": chunk_metadata.get("article_title", ""),
                "article_url": chunk_metadata.get("article_url", ""),
            }
            metadata.update({k: v for k, v in article_data.items() if v})
            return

        # Fallback to legacy format (chunk.article_metadata)
        if "article_metadata" in chunk:
            article_meta = chunk.get("article_metadata", {})
            article_data = {
                "article_title": article_meta.get("title", ""),
                "article_url": article_meta.get("url", ""),
            }
            metadata.update({k: v for k, v in article_data.items() if v})

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
            retry_count = 0
            while retry_count < 3:
                try:
                    # Convert to the expected type for the Pinecone SDK
                    self.index.upsert(
                        vectors=cast(List[Any], batch),
                        namespace=self.namespace if self.namespace else None,
                    )
                    break
                except Exception as e:
                    retry_count += 1
                    logger.error(
                        f"Failed to store chunk batch {i // batch_size} on attempt {retry_count}: {e}"
                    )
                    if retry_count == 3:
                        logger.error(
                            f"Giving up on batch {i // batch_size} after 3 attempts"
                        )

    def store_chunks(
        self,
        chunks: List[Dict[str, Any]],
        id_prefix: str = "",
        landmark_id: Optional[str] = None,
        use_fixed_ids: bool = True,
        delete_existing: bool = False,
        enhanced_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Store chunks in Pinecone index.

        Args:
            chunks: List of chunks to store, each with text and embedding
            id_prefix: Prefix for vector IDs (optional)
            landmark_id: ID of the landmark for metadata and filtering
            use_fixed_ids: Create deterministic IDs for vectors based on content and landmark
            delete_existing: Delete existing vectors for the landmark before storing new ones
            enhanced_metadata: Pre-built enhanced metadata dict (optional, will fetch if not provided)

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
        if enhanced_metadata is not None:
            # Use pre-built enhanced metadata
            landmark_enhanced_metadata = enhanced_metadata
        elif landmark_id:
            # Fetch enhanced metadata if not provided
            landmark_enhanced_metadata = self._get_enhanced_metadata(landmark_id)
        else:
            landmark_enhanced_metadata = {}

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
                chunk, source_type, i, landmark_id, landmark_enhanced_metadata
            )

            # Remove _extra_fields from LandmarkMetadata to avoid Pinecone errors
            if "_extra_fields" in metadata:
                del metadata["_extra_fields"]

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

    def _build_combined_filter(
        self,
        filter_dict: Optional[Dict[str, Any]],
        landmark_id: Optional[str],
        source_type: Optional[str],
    ) -> Dict[str, Any]:
        """
        Build a combined filter dictionary from individual filter components.

        Args:
            filter_dict: Base filter dictionary
            landmark_id: Optional landmark ID to filter by
            source_type: Optional source type to filter by

        Returns:
            Combined filter dictionary
        """
        combined_filter: Dict[str, Any] = {}

        if filter_dict:
            combined_filter.update(filter_dict)
        if landmark_id:
            combined_filter["landmark_id"] = landmark_id
        if source_type:
            combined_filter["source_type"] = source_type

        return combined_filter

    def _get_query_vector(self, query_vector: Optional[List[float]]) -> List[float]:
        """
        Get a query vector, creating a dummy one if needed.

        Args:
            query_vector: Optional user-provided query vector

        Returns:
            Query vector to use (provided or dummy)
        """
        if query_vector is None:
            # For listing operations, use zero vector
            dimension = self.dimensions
            vector = [0.0] * dimension
            logger.debug("Using dummy vector for listing operation")
        else:
            vector = query_vector
            logger.debug("Using provided query vector for semantic search")
        return vector

    def _apply_prefix_filter(
        self, matches: List[Any], id_prefix: Optional[str], top_k: int
    ) -> List[Any]:
        """
        Filter matches by ID prefix.

        Args:
            matches: List of match objects
            id_prefix: Prefix to filter by (case-insensitive)
            top_k: Maximum number of results to return

        Returns:
            Filtered list of matches
        """
        if not id_prefix:
            return matches

        prefix_lower = id_prefix.lower()
        filtered_matches = [
            match
            for match in matches
            if hasattr(match, "id")
            and match.id
            and match.id.lower().startswith(prefix_lower)
        ]
        return filtered_matches[:top_k]

    def _standardize_match(self, match: Any, include_values: bool) -> Dict[str, Any]:
        """
        Convert a match object to a standardized dictionary format.

        Args:
            match: Match object from Pinecone response
            include_values: Whether to include embeddings

        Returns:
            Standardized match dictionary
        """
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

        # Extract values if requested and available
        if include_values and hasattr(match, "values"):
            match_dict["values"] = match.values

        return match_dict

    def query_vectors(
        self,
        query_vector: Optional[List[float]] = None,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        landmark_id: Optional[str] = None,
        source_type: Optional[str] = None,
        id_prefix: Optional[str] = None,
        include_values: bool = False,
        namespace_override: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Enhanced query method that consolidates all vector querying functionality.

        This method supports:
        - Semantic similarity search (with query_vector)
        - Metadata filtering (landmark_id, source_type, custom filters)
        - ID prefix filtering
        - Listing operations (when query_vector is None)

        Args:
            query_vector: Embedding vector for semantic search. If None, performs listing operation
            top_k: Number of results to return
            filter_dict: Custom metadata filters (combined with other filters)
            landmark_id: Filter by specific landmark ID
            source_type: Filter by source type ("wikipedia", "pdf", "test")
            id_prefix: Filter vector IDs by prefix (case-insensitive)
            include_values: Whether to include embedding values in results
            namespace_override: Override the instance namespace for this query

        Returns:
            List of matching vectors with metadata and optionally embedding values
        """
        try:
            # Determine the namespace to use
            query_namespace = (
                namespace_override if namespace_override is not None else self.namespace
            )

            # Build filter, get vector, and adjust top_k using helper methods
            combined_filter = self._build_combined_filter(
                filter_dict, landmark_id, source_type
            )
            vector = self._get_query_vector(query_vector)

            # Adjust top_k for prefix filtering
            effective_top_k = top_k
            if id_prefix:
                effective_top_k = max(top_k * 20, 100)
                logger.debug(
                    f"Increased top_k to {effective_top_k} for prefix filtering"
                )

            # Execute the query
            response = self.index.query(
                vector=vector,
                top_k=effective_top_k,
                include_metadata=True,
                include_values=include_values,
                filter=combined_filter if combined_filter else None,
                namespace=query_namespace if query_namespace else None,
            )

            # Handle response.matches which can be a list or other iterable
            from typing import Any as TypeAny
            from typing import cast

            response_dict = cast(TypeAny, response)

            # Access matches safely
            matches = getattr(response_dict, "matches", [])

            # Apply prefix filtering if needed
            if id_prefix:
                matches = self._apply_prefix_filter(matches, id_prefix, top_k)

            # Convert matches to standardized format using helper method
            result_list = [
                self._standardize_match(match, include_values) for match in matches
            ]

            logger.debug(f"Returned {len(result_list)} vectors after processing")
            return result_list

        except Exception as e:
            logger.error(f"Failed to query vectors: {e}")
            return []

    # Convenience methods for common query patterns

    def query_semantic_search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        landmark_id: Optional[str] = None,
        source_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic similarity search with optional metadata filtering.

        Args:
            query_vector: Embedding vector for semantic search
            top_k: Number of results to return
            filter_dict: Custom metadata filters
            landmark_id: Filter by specific landmark ID
            source_type: Filter by source type

        Returns:
            List of semantically similar vectors
        """
        return self.query_vectors(
            query_vector=query_vector,
            top_k=top_k,
            filter_dict=filter_dict,
            landmark_id=landmark_id,
            source_type=source_type,
        )

    def list_vectors(
        self,
        limit: int = 100,
        filter_dict: Optional[Dict[str, Any]] = None,
        landmark_id: Optional[str] = None,
        source_type: Optional[str] = None,
        id_prefix: Optional[str] = None,
        include_values: bool = False,
        namespace_override: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List vectors without semantic search (listing operation).

        Args:
            limit: Maximum number of vectors to return
            filter_dict: Custom metadata filters
            landmark_id: Filter by specific landmark ID
            source_type: Filter by source type
            id_prefix: Filter vector IDs by prefix
            include_values: Whether to include embedding values
            namespace_override: Override namespace for this query

        Returns:
            List of vectors matching the filters
        """
        return self.query_vectors(
            query_vector=None,  # Use None for listing operations
            top_k=limit,
            filter_dict=filter_dict,
            landmark_id=landmark_id,
            source_type=source_type,
            id_prefix=id_prefix,
            include_values=include_values,
            namespace_override=namespace_override,
        )

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

        .. deprecated::
            Use query_vectors() or list_vectors() instead for enhanced functionality.

        Args:
            source_type: Source type to filter by ("wikipedia", "pdf", or "test")
            limit: Maximum number of vectors to return
            landmark_id: Optional landmark ID to filter by

        Returns:
            Dictionary with matches containing vectors and metadata
        """
        import warnings

        warnings.warn(
            "list_vectors_by_source is deprecated. Use query_vectors() or list_vectors() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Delegate to the enhanced query_vectors method
        matches = self.query_vectors(
            query_vector=None,  # Listing operation
            top_k=limit,
            landmark_id=landmark_id,
            source_type=source_type,
            include_values=True,  # Match original behavior
        )

        # Return in the original format for backward compatibility
        return {"matches": matches}

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
            # Use existing Pinecone client for index operations
            from pinecone import ServerlessSpec

            pc = self.pc

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
            vectors: List[Tuple[str, list, dict]]
                List of tuples (id, embedding, metadata). This is NOT the same as the format for upsert, which expects a list of dicts.

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.index:
            logger.error("Index not initialized")
            return False

        try:
            # Convert to format expected by upsert
            pinecone_vectors: list[dict[str, Any]] = []
            for vector_id, embedding, metadata in vectors:
                pinecone_vectors.append(
                    {"id": vector_id, "values": embedding, "metadata": metadata}
                )

            # Use batch size of 100 as recommended by Pinecone
            batch_size = 100
            for i in range(0, len(pinecone_vectors), batch_size):
                batch = pinecone_vectors[i : i + batch_size]
                # upsert expects a list of dicts, not tuples
                self.index.upsert(
                    vectors=cast(List[Any], batch),
                    namespace=self.namespace if self.namespace else None,
                )

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
            # Use existing Pinecone client for index operations
            pc = self.pc

            # Delete the index
            pc.delete_index(self.index_name)
            logger.info(f"Deleted index: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete index: {e}")
            return False

    def _extract_vector_data(
        self, result: Any, vector_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract vector data from fetch result.

        Args:
            result: Fetch result from Pinecone
            vector_id: Vector ID to extract

        Returns:
            Dictionary with vector data or None if not found
        """
        if result and hasattr(result, "vectors") and vector_id in result.vectors:
            return {
                "id": vector_id,
                "values": getattr(result.vectors[vector_id], "values", []),
                "metadata": getattr(result.vectors[vector_id], "metadata", {}),
            }
        return None

    def _fetch_from_namespace(
        self, vector_id: str, namespace: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch vector from a specific namespace.

        Args:
            vector_id: Vector ID to fetch
            namespace: Namespace to fetch from, None for default namespace

        Returns:
            Vector data or None if not found
        """
        try:
            if namespace:
                result = self.index.fetch(ids=[vector_id], namespace=namespace)
            else:
                result = self.index.fetch(ids=[vector_id])
            return self._extract_vector_data(result, vector_id)
        except Exception as e:
            ns_str = f"namespace '{namespace}'" if namespace else "default namespace"
            logger.warning(f"Error fetching vector from {ns_str}: {e}")
            return None

    def _search_all_namespaces(
        self, vector_id: str, skip_namespace: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Search for vector in all namespaces except the one specified.

        Args:
            vector_id: Vector ID to search for
            skip_namespace: Namespace to skip in the search

        Returns:
            Vector data or None if not found
        """
        try:
            stats = self.get_index_stats()
            all_namespaces = list(stats.get("namespaces", {}).keys())

            # Try each namespace until we find the vector
            for ns_name in all_namespaces:
                if ns_name == skip_namespace:
                    continue  # Skip the namespace we already tried

                vector_data = self._fetch_from_namespace(vector_id, ns_name)
                if vector_data:
                    logger.info(
                        f"Found vector in namespace '{ns_name}' instead of requested '{skip_namespace}'"
                    )
                    return vector_data
            return None
        except Exception as e:
            logger.warning(f"Error when trying to search all namespaces: {e}")
            return None

    def fetch_vector_by_id(
        self, vector_id: str, namespace: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific vector from Pinecone by ID using fetch approach.

        Args:
            vector_id: The ID of the vector to fetch
            namespace: Optional Pinecone namespace to search in

        Returns:
            The vector data as a dictionary if found, None otherwise
        """
        try:
            # Use provided namespace or instance default
            fetch_namespace = namespace if namespace is not None else self.namespace
            logger.info(f"Fetching vector with ID: {vector_id}")

            # Try first without specifying namespace parameter (for "__default__" namespace)
            if not fetch_namespace or fetch_namespace == "__default__":
                vector_data = self._fetch_from_namespace(vector_id, None)
                if vector_data:
                    return vector_data

            # If we have a specific namespace or the previous attempt failed, try with namespace
            if fetch_namespace and fetch_namespace != "__default__":
                vector_data = self._fetch_from_namespace(vector_id, fetch_namespace)
                if vector_data:
                    return vector_data

            # If we didn't find it with or without namespace, try all available namespaces
            vector_data = self._search_all_namespaces(vector_id, fetch_namespace)
            if vector_data:
                return vector_data

            logger.error(f"Vector with ID '{vector_id}' not found in any namespace")
            return None

        except Exception as e:
            logger.error(f"Error fetching vector: {e}")
            return None

    def list_vectors_with_filter(
        self,
        prefix: Optional[str] = None,
        limit: int = 10,
        namespace: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List vectors in Pinecone with optional prefix filtering.

        .. deprecated::
            Use query_vectors() or list_vectors() instead for enhanced functionality.

        Args:
            prefix: Optional prefix to filter vector IDs
            limit: Maximum number of vectors to return
            namespace: Optional Pinecone namespace to search in

        Returns:
            List of vector data
        """
        import warnings

        warnings.warn(
            "list_vectors_with_filter is deprecated. Use query_vectors() or list_vectors() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Delegate to the enhanced query_vectors method
        return self.query_vectors(
            query_vector=None,  # Listing operation
            top_k=limit,
            id_prefix=prefix,
            namespace_override=namespace,
            include_values=False,  # Match original behavior
        )

    def query_vectors_by_landmark(
        self, landmark_id: str, namespace: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query Pinecone for vectors related to a landmark.

        .. deprecated::
            Use query_vectors() or list_vectors() instead for enhanced functionality.

        Args:
            landmark_id: The ID of the landmark to check
            namespace: Optional namespace to query

        Returns:
            List of vector matches
        """
        import warnings

        warnings.warn(
            "query_vectors_by_landmark is deprecated. Use query_vectors() or list_vectors() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Delegate to the enhanced query_vectors method
        return self.query_vectors(
            query_vector=None,  # Listing operation
            top_k=100,  # Match original behavior
            landmark_id=landmark_id,
            namespace_override=namespace,
            include_values=False,  # Match original behavior
        )

    def list_indexes(self) -> List[str]:
        """
        List all available Pinecone indexes.

        Returns:
            List of index names
        """
        try:
            indexes = self.pc.list_indexes()
            index_names = (
                [idx.name for idx in indexes]
                if hasattr(indexes, "__iter__")
                else getattr(indexes, "names", [])
            )
            return index_names
        except Exception as e:
            logger.error(f"Failed to list indexes: {e}")
            return []

    def check_index_exists(self, index_name: Optional[str] = None) -> bool:
        """
        Check if a specific index exists.

        Args:
            index_name: Name of index to check (defaults to current index)

        Returns:
            True if index exists, False otherwise
        """
        target_index = index_name or self.index_name
        if not target_index:
            return False

        index_names = self.list_indexes()
        return target_index in index_names

    def test_connection(self) -> bool:
        """
        Test the Pinecone connection and return success status.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            stats = self.get_index_stats()
            return "error" not in stats
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def create_index_if_not_exists(
        self,
        index_name: Optional[str] = None,
        dimensions: Optional[int] = None,
        metric: str = "cosine",
    ) -> bool:
        """
        Create a Pinecone index if it doesn't already exist.

        Args:
            index_name: Name of index to create (defaults to current index)
            dimensions: Vector dimensions (defaults to settings)
            metric: Distance metric to use

        Returns:
            True if index exists or was created successfully, False otherwise
        """
        target_index = index_name or self.index_name
        target_dimensions = dimensions or self.dimensions

        if not target_index:
            logger.error("No index name provided")
            return False

        # Check if index already exists
        if self.check_index_exists(target_index):
            logger.info(f"Index '{target_index}' already exists")
            return True

        try:
            from pinecone import ServerlessSpec

            logger.info(
                f"Creating index '{target_index}' with {target_dimensions} dimensions"
            )

            # Create the index
            self.pc.create_index(
                name=target_index,
                dimension=target_dimensions,
                metric=metric,
                spec=ServerlessSpec(cloud="gcp", region="us-central1"),
            )

            # Wait for index to be ready
            logger.info("Waiting for index to initialize (30 seconds)...")
            time.sleep(30)

            # Verify index was created
            if self.check_index_exists(target_index):
                logger.info(f"Successfully created index: {target_index}")
                return True
            else:
                logger.error(f"Failed to verify index creation: {target_index}")
                return False

        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False
