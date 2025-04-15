"""
Pinecone vector database module for NYC Landmarks Vector Database.

This module handles interactions with the Pinecone vector database service,
including storing and retrieving embeddings.
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

# Import pinecone-client (using updated API)
from pinecone import Pinecone  # type: ignore

from nyc_landmarks.config.settings import settings
from nyc_landmarks.vectordb.enhanced_metadata import get_metadata_collector

# Configure logging the
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class PineconeDB:
    """
    Pinecone vector database operations.

    This class provides methods to interact with Pinecone vector database,
    including initializing connections, storing vectors, querying for similar vectors,
    and managing indexes.

    Attributes:
        api_key (str): Pinecone API key from settings
        index_name (str): Name of the Pinecone index to use
        namespace (str): Namespace within the index for vector storage
        dimensions (int): Dimensionality of vectors to store
        metric (str): Distance metric for vector similarity (e.g., "cosine")
        pc: Pinecone client instance
        index: Pinecone index instance for operations
        metadata_collector: Collector for enhanced metadata
    """

    def __init__(self) -> None:
        """
        Initialize the Pinecone database with credentials.

        Sets up the Pinecone client using API key from the application configuration.
        If credentials are available, it will attempt to connect to the specified index.

        Raises:
            Various exceptions from the Pinecone library may be caught and logged.
        """
        self.api_key = settings.PINECONE_API_KEY
        self.index_name = settings.PINECONE_INDEX_NAME
        self.namespace = settings.PINECONE_NAMESPACE
        self.dimensions = settings.PINECONE_DIMENSIONS
        self.metric = settings.PINECONE_METRIC
        self.pc = None
        self.index = None
        self.metadata_collector = get_metadata_collector()

        # Initialize Pinecone client if API key is provided
        if self.api_key:
            try:
                # Initialize Pinecone with new API
                self.pc = Pinecone(api_key=self.api_key)
                logger.info("Initialized Pinecone client")

                # Connect to index
                self._connect_to_index()
            except Exception as e:
                logger.error(f"Error initializing Pinecone: {e}")
        else:
            logger.warning("Pinecone API key not provided")

    def _connect_to_index(self) -> None:
        """
        Connect to the Pinecone index without recreating it.

        Attempts to establish a connection to the pre-existing Pinecone index specified
        in the initialization parameters. Will try to connect even if the index appears
        to not exist in case of temporary API inconsistencies.

        Raises:
            Exception: If connection to the index fails, the exception is logged and re-raised.
        """
        try:
            # Check if index exists
            indexes = self.pc.list_indexes()
            if self.index_name not in indexes.names():
                logger.warning(
                    f"Index '{self.index_name}' does not exist. "
                    f"This should be pre-created in the Pinecone dashboard."
                )
                logger.info(
                    "Attempting to connect anyway in case of list_indexes inconsistency..."
                )

            # Connect to existing index
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
        except Exception as e:
            logger.error(f"Error connecting to Pinecone index: {e}")
            raise

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index.

        Retrieves information about the current state of the Pinecone index,
        including vector count, namespaces, and dimension information.

        Returns:
            Dict[str, Any]: Dictionary containing index statistics or an error message
                            if the operation fails
        """
        if not self.index:
            logger.error("Pinecone index not initialized")
            return {"error": "Index not initialized"}

        try:
            # Call describe_index_stats on the index object instance
            stats_response = self.index.describe_index_stats()

            # Check if the response is None *before* trying to convert it
            if stats_response is None:
                logger.error(
                    f"Received None response from self.index.describe_index_stats for index '{self.index_name}'"
                )
                return {"error": "Received no stats from Pinecone (None response)"}

            # Proceed if the response is not None
            logger.debug(
                f"describe_index_stats response type: {type(stats_response)}, value: {stats_response}"
            )

            # Build dictionary from the response
            try:
                stats_dict = {}

                # Extract dimension if available
                if hasattr(stats_response, "dimension"):
                    stats_dict["dimension"] = stats_response.dimension

                # Extract index_fullness if available
                if hasattr(stats_response, "index_fullness"):
                    stats_dict["index_fullness"] = stats_response.index_fullness

                # Extract namespaces if available
                if hasattr(stats_response, "namespaces"):
                    namespaces_dict = {}
                    for ns_name, ns_data in stats_response.namespaces.items():
                        namespaces_dict[ns_name] = dict(ns_data)
                    stats_dict["namespaces"] = namespaces_dict
                else:
                    stats_dict["namespaces"] = {}

                # Extract total_vector_count if available
                if hasattr(stats_response, "total_vector_count"):
                    stats_dict["total_vector_count"] = stats_response.total_vector_count
                else:
                    stats_dict["total_vector_count"] = 0

                logger.debug(
                    f"Successfully retrieved and built index stats dict: {stats_dict}"
                )
                return stats_dict
            except Exception as build_e:
                logger.exception(
                    f"Error building dictionary from stats_response: {build_e}",
                    exc_info=True,
                )
                return {"error": f"Error processing stats response: {str(build_e)}"}

        except Exception as e:
            error_message = "Unknown error"
            try:
                # Try to get a string representation safely
                error_message = str(e)
            except Exception as str_e:
                logger.error(f"Could not convert exception to string: {str_e}")

            logger.exception(
                f"Unexpected error getting index stats: {error_message}", exc_info=True
            )  # Log full traceback
            return {"error": f"Unexpected error getting stats: {error_message}"}

    def store_vector(
        self, vector_id: str, vector: List[float], metadata: Dict[str, Any]
    ) -> bool:
        """
        Store a single vector in the index.

        Adds or updates a single vector with associated metadata in the Pinecone index.

        Args:
            vector_id (str): Unique identifier for the vector
            vector (List[float]): Embedding vector as a list of floats
            metadata (Dict[str, Any]): Metadata to store with the vector

        Returns:
            bool: True if successful, False otherwise
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
        """
        Store a batch of vectors in the index.

        Efficiently uploads multiple vectors with their metadata in a single operation
        to minimize API calls and improve performance.

        Args:
            vectors (List[Tuple[str, List[float], Dict[str, Any]]]): List of tuples
                containing (vector_id, vector_values, metadata) for each vector to store

        Returns:
            bool: True if successful, False otherwise
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
        self,
        chunks: List[Dict[str, Any]],
        id_prefix: str = "",
        landmark_id: Optional[str] = None,
    ) -> List[str]:
        """
        Store text chunks with embeddings in the index.

        Processes a list of text chunks with their embeddings and metadata,
        optionally enhances the metadata with landmark-specific information,
        and stores them in the Pinecone index.

        Args:
            chunks (List[Dict[str, Any]]): List of chunk dictionaries, each containing
                'text', 'metadata', and 'embedding' keys
            id_prefix (str, optional): Prefix for generated vector IDs. Defaults to "".
            landmark_id (Optional[str], optional): Landmark ID to fetch enhanced metadata.
                Defaults to None.

        Returns:
            List[str]: List of stored vector IDs, empty if operation failed
        """
        if not chunks:
            logger.warning("Attempted to store empty chunks list")
            return []

        # Get enhanced metadata if landmark_id is provided
        enhanced_metadata = {}
        if landmark_id:
            enhanced_metadata = self.metadata_collector.collect_landmark_metadata(
                landmark_id
            )
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
            # Include the text in metadata for retrieval
            metadata["text"] = chunk["text"]

            # Merge with enhanced metadata if available
            if enhanced_metadata:
                # Keep only metadata fields that won't conflict with chunk-specific metadata
                # and don't exceed Pinecone's metadata size limits
                for key, value in enhanced_metadata.items():
                    # Skip keys that already exist or text fields
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
        return []

    def query_vectors(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query the index for similar vectors.

        Searches the Pinecone index for vectors similar to the provided query vector,
        optionally filtering results based on metadata values.

        Args:
            query_vector (List[float]): Query embedding vector to find similar vectors for
            top_k (int, optional): Number of results to return. Defaults to 5.
            filter_dict (Optional[Dict[str, Any]], optional): Metadata filter to apply to the query.
                Defaults to None.

        Returns:
            List[Dict[str, Any]]: List of matched vectors with their metadata and similarity scores
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

            # Convert pinecone match objects to dictionaries
            return [dict(match) for match in matches]
        except Exception as e:
            logger.error(f"Error querying vectors: {e}")
            return []

    def delete_vectors(self, vector_ids: List[str]) -> bool:
        """
        Delete vectors from the index.

        Removes vectors with the specified IDs from the Pinecone index.

        Args:
            vector_ids (List[str]): List of vector IDs to delete

        Returns:
            bool: True if successful, False otherwise
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
        """
        Delete vectors matching metadata filter.

        Removes vectors that match the specified metadata filter criteria from the Pinecone index.
        This is useful for batch deletion of vectors based on their metadata attributes.

        Args:
            filter_dict (Dict[str, Any]): Metadata filter criteria to match vectors for deletion

        Returns:
            bool: True if successful, False otherwise
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

    def delete_index(self) -> bool:
        """
        Delete the entire Pinecone index.

        Removes the entire Pinecone index, which deletes all vectors and
        associated metadata. Use with caution as this operation cannot be undone.

        Returns:
            bool: True if successful or if index didn't exist, False on error
        """
        if not self.pc:
            logger.error("Pinecone client not initialized")
            return False

        try:
            # Check if index exists using new API
            indexes = self.pc.list_indexes()
            if self.index_name in indexes.names():
                # Delete the index using new API
                self.pc.delete_index(self.index_name)
                logger.info(f"Successfully deleted index: {self.index_name}")

                # Reset the index reference
                self.index = None
                return True

            logger.warning(f"Index {self.index_name} does not exist, nothing to delete")
            return True
        except Exception as e:
            logger.error(f"Error deleting index: {e}")
            return False

    def recreate_index(self) -> bool:
        """
        Delete and recreate the Pinecone index.

        Completely rebuilds the Pinecone index by first deleting the existing one
        and then creating a new one with the configured dimensions and metric.
        This operation is destructive and will result in the loss of all vectors
        and metadata stored in the index.

        Note:
            This operation may be restricted by Pinecone service tier limitations.
            The method includes a waiting period to allow the new index to initialize.

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.pc:
            logger.error("Pinecone client not initialized")
            return False

        # Delete existing index if it exists
        deleted = self.delete_index()
        if not deleted:
            return False

        # Create new index
        try:
            # Create index with new API
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimensions,
                metric=self.metric
            )
            logger.warning(
                "Note: GCP starter tier may not allow creating new indexes. "
                "If this fails, try using AWS region."
            )

            # Wait for index to be ready
            logger.info("Waiting for index to initialize...")
            time.sleep(30)

            # Connect to the new index
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Successfully recreated index: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Error recreating index: {e}")
            return False
