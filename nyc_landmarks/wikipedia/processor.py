"""Wikipedia processing functionality for NYC landmarks."""

import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from transformers.tokenization_utils import PreTrainedTokenizer

from nyc_landmarks.db.wikipedia_fetcher import WikipediaFetcher
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.models.metadata_models import SourceType
from nyc_landmarks.models.wikipedia_models import (
    WikipediaContentModel,
    WikipediaQualityModel,
)
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB
from nyc_landmarks.wikipedia.quality_fetcher import WikipediaQualityFetcher

if TYPE_CHECKING:
    from nyc_landmarks.db.db_client import DbClient

logger = get_logger(__name__)


class WikipediaProcessor:
    """Processes Wikipedia articles for NYC landmarks."""

    def __init__(self) -> None:
        """Initialize the Wikipedia processor components."""
        self.db_client: Optional["DbClient"] = None
        self.wiki_fetcher = WikipediaFetcher()
        self.embedding_generator = EmbeddingGenerator()
        self.pinecone_db = PineconeDB()
        self.quality_fetcher = WikipediaQualityFetcher()

    def _initialize_db_client(self) -> Any:
        """Initialize database client on demand."""
        if self.db_client is None:
            from nyc_landmarks.db.db_client import get_db_client

            self.db_client = get_db_client()
        return self.db_client

    def fetch_wikipedia_articles(self, landmark_id: str) -> List[Any]:
        """
        Fetch Wikipedia articles for the landmark.

        Args:
            landmark_id: ID of the landmark

        Returns:
            List of articles with content
        """
        db_client = self._initialize_db_client()

        # Get Wikipedia articles for the landmark
        articles = db_client.get_wikipedia_articles(landmark_id)

        if not articles:
            logger.info(
                f"No Wikipedia articles found for landmark: {landmark_id} - this is normal and not an error"
            )
            return []

        logger.info(
            f"Found {len(articles)} Wikipedia articles for landmark: {landmark_id}"
        )

        # Fetch content for each article
        for article in articles:
            logger.info(f"- Article: {article.title}, URL: {article.url}")

            # Fetch the actual content from Wikipedia
            logger.info(f"Fetching content from Wikipedia for article: {article.title}")
            article_content, rev_id = self.wiki_fetcher.fetch_wikipedia_content(
                article.url
            )
            if article_content:
                article.content = article_content
                article.rev_id = rev_id  # Store the revision ID
                logger.info(
                    f"Successfully fetched content for article: {article.title} ({len(article_content)} chars)"
                )
                if rev_id:
                    logger.info(f"Article revision ID: {rev_id}")
            else:
                logger.warning(f"Failed to fetch content for article: {article.title}")

        return list(articles)

    def split_into_token_chunks(
        self, text: Optional[str], max_tokens: int, tokenizer: PreTrainedTokenizer
    ) -> List[str]:
        """Split text into chunks based on token count."""
        if text is None:
            return []
        tokens = tokenizer.encode(text)
        chunks = []
        for i in range(0, len(tokens), max_tokens):
            chunks.append(tokenizer.decode(tokens[i : i + max_tokens]))
        return chunks

    def process_articles_into_chunks(
        self, articles: List[Any], landmark_id: str
    ) -> Tuple[List[WikipediaContentModel], int]:
        """
        Process articles into WikipediaContentModel objects with chunks.

        Args:
            articles: List of Wikipedia articles
            landmark_id: ID of the landmark

        Returns:
            Tuple of (processed_articles, total_chunks)
        """
        # Initialize for token-based chunking
        from transformers import GPT2Tokenizer

        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        max_token_limit = 8192
        token_limit_per_chunk = max_token_limit - 500  # Reserve tokens for metadata

        logger.info(f"Using token limit of {token_limit_per_chunk} per chunk")

        processed_articles = []
        total_chunks = 0

        for article in articles:
            logger.debug(f"Processing article: {article.title}")

            if article.content is None:
                logger.error(f"Content is None for article: {article.title}")
                continue

            # Split the article into token-based chunks
            token_chunks = self.split_into_token_chunks(
                article.content, token_limit_per_chunk, tokenizer
            )
            logger.info(
                f"Split article '{article.title}' into {len(token_chunks)} token-based chunks"
            )

            # Create dictionary chunks for the WikipediaContentModel
            dict_chunks: List[Dict[str, Any]] = []
            for i, chunk_text in enumerate(token_chunks):
                token_count = len(tokenizer.encode(chunk_text))
                # Generate the vector ID that will be used for this chunk
                vector_id = (
                    f"wiki-{article.title.replace(' ', '_')}-{landmark_id}-chunk-{i}"
                )
                logger.info(
                    f"Processing chunk {i} with {token_count} tokens (Vector ID: {vector_id})"
                )

                dict_chunks.append(
                    {
                        "text": chunk_text,
                        "chunk_index": i,
                        "metadata": {
                            "chunk_index": i,
                            "article_title": article.title,
                            "article_url": article.url,
                            "source_type": SourceType.WIKIPEDIA.value,
                            "landmark_id": landmark_id,
                            "rev_id": (
                                article.rev_id if hasattr(article, "rev_id") else None
                            ),
                        },
                        "total_chunks": len(token_chunks),
                    }
                )

            # Fetch article quality if revision ID is available
            quality = None
            if hasattr(article, "rev_id") and article.rev_id:
                quality_data = self._fetch_article_quality(article.rev_id)
                if quality_data:
                    quality = quality_data
                    logger.info(
                        f"Added quality assessment for article: {article.title} - {quality.prediction}"
                    )

                    # Add quality info to chunk metadata
                    for chunk in dict_chunks:
                        if "metadata" in chunk:
                            chunk["metadata"]["article_quality"] = quality.prediction
                            chunk["metadata"]["article_quality_score"] = str(
                                quality.probabilities.get(quality.prediction, 0.0)
                            )
                            chunk["metadata"][
                                "article_quality_description"
                            ] = quality.get_quality_description()

            # Create a WikipediaContentModel with the chunks
            content_model = WikipediaContentModel(
                lpNumber=landmark_id,
                url=article.url,
                title=article.title,
                content=article.content,
                chunks=dict_chunks,
                rev_id=article.rev_id,  # Include revision ID
                quality=quality,  # Include quality assessment
            )

            processed_articles.append(content_model)
            total_chunks += len(dict_chunks)

        return processed_articles, total_chunks

    def _fetch_article_quality(self, rev_id: str) -> Optional[WikipediaQualityModel]:
        """
        Fetch quality assessment for a Wikipedia article.

        Args:
            rev_id: Revision ID of the Wikipedia article

        Returns:
            WikipediaQualityModel with quality assessment or None if fetching fails
        """
        if not rev_id:
            logger.warning("Cannot fetch article quality: No revision ID provided")
            return None

        try:
            # Get quality data from the Lift Wing API
            quality_data = self.quality_fetcher.fetch_article_quality(rev_id)

            if not quality_data:
                logger.warning(
                    f"Failed to fetch quality data for revision ID: {rev_id}"
                )
                return None

            # Create a WikipediaQualityModel from the quality data
            quality_model = WikipediaQualityModel(
                prediction=quality_data["prediction"],
                probabilities=quality_data["probabilities"],
                rev_id=quality_data["rev_id"],
            )

            logger.info(
                f"Quality assessment for rev_id {rev_id}: {quality_model.prediction} "
                f"(confidence: {quality_model.probabilities.get(quality_model.prediction, 0.0):.2f})"
            )

            return quality_model

        except Exception as e:
            logger.error(f"Error fetching quality assessment for rev_id {rev_id}: {e}")
            return None

    def add_metadata_to_chunks(
        self,
        chunks_with_embeddings: List[Union[Dict[str, Any], Any]],
        article_metadata: Dict[str, Any],
        enhanced_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Helper function to add metadata to chunks.

        Args:
            chunks_with_embeddings: List of chunks with embeddings
            article_metadata: Article-specific metadata to add
            enhanced_metadata: Optional enhanced metadata with flattened building data
        """
        for chunk in chunks_with_embeddings:
            if isinstance(chunk, dict):
                # Add Wikipedia metadata
                chunk["metadata"]["wikipedia_metadata"] = article_metadata

                # Add flattened building fields from enhanced metadata if available
                if enhanced_metadata:
                    # Only copy fields that start with building_ (these are the flattened fields)
                    building_fields = {
                        k: v
                        for k, v in enhanced_metadata.items()
                        if k.startswith("building_")
                    }
                    if building_fields:
                        chunk["metadata"].update(building_fields)
                        logger.info(
                            f"Added {len(building_fields)} flattened building fields to chunk metadata"
                        )
            else:
                if hasattr(chunk, "metadata") and chunk.metadata is not None:
                    # Add Wikipedia metadata
                    chunk.metadata["wikipedia_metadata"] = article_metadata

                    # Add flattened building fields from enhanced metadata if available
                    if enhanced_metadata:
                        # Only copy fields that start with building_ (these are the flattened fields)
                        building_fields = {
                            k: v
                            for k, v in enhanced_metadata.items()
                            if k.startswith("building_")
                        }
                        if building_fields:
                            for k, v in building_fields.items():
                                chunk.metadata[k] = v
                            logger.info(
                                f"Added {len(building_fields)} flattened building fields to object-style chunk"
                            )

    def enrich_chunks_with_article_metadata(
        self,
        chunks_with_embeddings: List[Union[Dict[str, Any], Any]],
        wiki_article: WikipediaContentModel,
        current_time: str,
        enhanced_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add article metadata to chunks.

        Args:
            chunks_with_embeddings: List of chunks with embeddings
            wiki_article: Wikipedia article model
            current_time: Current timestamp
            enhanced_metadata: Optional enhanced metadata with building data
        """
        for chunk in chunks_with_embeddings:
            if isinstance(chunk, dict):
                self._enrich_dict_chunk(
                    chunk, wiki_article, current_time, enhanced_metadata
                )
            else:
                self._enrich_object_chunk(
                    chunk, wiki_article, current_time, enhanced_metadata
                )

    def _enrich_dict_chunk(
        self,
        chunk: Dict[str, Any],
        wiki_article: WikipediaContentModel,
        current_time: str,
        enhanced_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Enrich a dictionary-style chunk with article metadata."""
        # Add article_metadata field which is used by PineconeDB._create_metadata_for_chunk
        if "article_metadata" not in chunk:
            chunk["article_metadata"] = {}
        chunk["article_metadata"]["title"] = wiki_article.title
        chunk["article_metadata"]["url"] = wiki_article.url

        # Add revision ID for version tracking if available
        if hasattr(wiki_article, "rev_id") and wiki_article.rev_id:
            chunk["article_metadata"]["rev_id"] = wiki_article.rev_id

        # Add processing_date to be picked up by PineconeDB._create_metadata_for_chunk
        chunk["processing_date"] = current_time

        # Also add directly to metadata for backwards compatibility
        if "metadata" in chunk and chunk["metadata"] is not None:
            self._add_metadata_to_dict(chunk["metadata"], wiki_article, current_time)
            self._add_quality_metadata_to_dict(chunk["metadata"], wiki_article)
            self._add_building_fields_to_dict(chunk["metadata"], enhanced_metadata)

        logger.info(
            f"Added article metadata to chunk: article_title={wiki_article.title}, "
            f"article_url={wiki_article.url}, processing_date={current_time}"
            f"{', rev_id=' + wiki_article.rev_id if hasattr(wiki_article, 'rev_id') and wiki_article.rev_id else ''}"
        )

    def _enrich_object_chunk(
        self,
        chunk: Any,
        wiki_article: WikipediaContentModel,
        current_time: str,
        enhanced_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Enrich an object-style chunk with article metadata."""
        # Add article_metadata field
        if not hasattr(chunk, "article_metadata"):
            setattr(chunk, "article_metadata", {})
        chunk.article_metadata["title"] = wiki_article.title
        chunk.article_metadata["url"] = wiki_article.url

        # Add revision ID for version tracking if available
        if hasattr(wiki_article, "rev_id") and wiki_article.rev_id:
            chunk.article_metadata["rev_id"] = wiki_article.rev_id

        # Add processing_date to be picked up by PineconeDB._create_metadata_for_chunk
        setattr(chunk, "processing_date", current_time)

        # Also add directly to metadata for backwards compatibility
        if hasattr(chunk, "metadata") and chunk.metadata is not None:
            self._add_metadata_to_dict(chunk.metadata, wiki_article, current_time)
            self._add_building_fields_to_object(chunk.metadata, enhanced_metadata)

        logger.info(
            f"Added article metadata to object-style chunk: {wiki_article.title} "
            f"with processing_date={current_time}"
            f"{', rev_id=' + wiki_article.rev_id if hasattr(wiki_article, 'rev_id') and wiki_article.rev_id else ''}"
        )

    def _add_metadata_to_dict(
        self,
        metadata: Dict[str, Any],
        wiki_article: WikipediaContentModel,
        current_time: str,
    ) -> None:
        """Add basic metadata fields to a dictionary."""
        metadata["article_title"] = wiki_article.title
        metadata["article_url"] = wiki_article.url
        metadata["processing_date"] = current_time
        metadata["source_type"] = SourceType.WIKIPEDIA.value

        # Add revision ID for version tracking if available
        if hasattr(wiki_article, "rev_id") and wiki_article.rev_id:
            metadata["article_rev_id"] = wiki_article.rev_id

    def _add_quality_metadata_to_dict(
        self, metadata: Dict[str, Any], wiki_article: WikipediaContentModel
    ) -> None:
        """Add quality metadata if available."""
        if hasattr(wiki_article, "quality") and wiki_article.quality:
            metadata["article_quality"] = wiki_article.quality.prediction
            metadata["article_quality_score"] = str(
                wiki_article.quality.probabilities.get(
                    wiki_article.quality.prediction, 0.0
                )
            )
            metadata["article_quality_description"] = (
                wiki_article.quality.get_quality_description()
            )

    def _add_building_fields_to_dict(
        self, metadata: Dict[str, Any], enhanced_metadata: Optional[Dict[str, Any]]
    ) -> None:
        """Add building fields to dictionary metadata."""
        if enhanced_metadata:
            building_fields = self._extract_building_fields(enhanced_metadata)
            if building_fields:
                metadata.update(building_fields)
                logger.info(
                    f"Added {len(building_fields)} flattened building fields to chunk metadata"
                )

    def _add_building_fields_to_object(
        self, metadata: Any, enhanced_metadata: Optional[Dict[str, Any]]
    ) -> None:
        """Add building fields to object metadata."""
        if enhanced_metadata:
            building_fields = self._extract_building_fields(enhanced_metadata)
            if building_fields:
                for k, v in building_fields.items():
                    metadata[k] = v
                logger.info(
                    f"Added {len(building_fields)} flattened building fields to object-style chunk"
                )

    def _extract_building_fields(
        self, enhanced_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract building fields from enhanced metadata."""
        return {k: v for k, v in enhanced_metadata.items() if k.startswith("building_")}

    def generate_embeddings_and_store(
        self,
        processed_articles: List[WikipediaContentModel],
        landmark_id: str,
        delete_existing: bool,
    ) -> int:
        """
        Generate embeddings for chunks and store them in Pinecone.

        Args:
            processed_articles: List of processed Wikipedia articles
            landmark_id: ID of the landmark
            delete_existing: Whether to delete existing vectors for the landmark

        Returns:
            Total chunks embedded
        """
        # Collect enhanced metadata once for this landmark
        from nyc_landmarks.vectordb.enhanced_metadata import EnhancedMetadataCollector

        enhanced_metadata_dict = {}
        try:
            collector = EnhancedMetadataCollector()
            enhanced_metadata_obj = collector.collect_landmark_metadata(landmark_id)
            enhanced_metadata_dict = (
                enhanced_metadata_obj.model_dump(exclude_none=True)
                if enhanced_metadata_obj
                else {}
            )
            logger.info(f"Collected enhanced metadata for landmark {landmark_id}")

            # DEBUG: Log all metadata keys
            logger.info(
                f"DEBUG: Wikipedia processor enhanced metadata keys: {list(enhanced_metadata_dict.keys())}"
            )

            # Log flattened building data information if available
            building_fields = {
                k: v
                for k, v in enhanced_metadata_dict.items()
                if k.startswith("building_")
            }
            logger.info(
                f"DEBUG: Wikipedia processor found {len(building_fields)} building fields"
            )
            if building_fields:
                building_count = len(
                    [
                        k
                        for k in building_fields.keys()
                        if k.startswith("building_") and k.endswith("_name")
                    ]
                )
                logger.info(
                    f"Found {building_count} buildings in flattened metadata format ({len(building_fields)} total fields)"
                )

                # Log building names if building_names array is available
                if "building_names" in enhanced_metadata_dict:
                    names = enhanced_metadata_dict["building_names"]
                    logger.info(f"Building names: {', '.join(names)}")
        except Exception as e:
            logger.warning(
                f"Could not collect enhanced metadata for {landmark_id}: {e}"
            )
            enhanced_metadata_dict = {}

        total_chunks_embedded = 0

        for wiki_article in processed_articles:
            # Skip articles with no chunks
            if not hasattr(wiki_article, "chunks") or not wiki_article.chunks:
                logger.warning(
                    f"No chunks to process for article: {wiki_article.title}"
                )
                continue

            # Generate embeddings for the chunks
            logger.info(
                f"Generating embeddings for {len(wiki_article.chunks)} chunks from article: {wiki_article.title}"
            )
            chunks_with_embeddings = self.embedding_generator.process_chunks(
                wiki_article.chunks
            )

            # Get current timestamp for processing_date
            current_time = datetime.datetime.now().isoformat()

            # Replace WikipediaMetadata with a dictionary for metadata
            article_metadata = {
                "title": wiki_article.title,
                "url": wiki_article.url,
                "processing_date": current_time,
                "source_type": SourceType.WIKIPEDIA.value,
            }

            # Add revision ID to metadata if available
            if hasattr(wiki_article, "rev_id") and wiki_article.rev_id:
                article_metadata["rev_id"] = wiki_article.rev_id
                logger.info(
                    f"Added revision ID {wiki_article.rev_id} to article metadata"
                )

            # Add quality information to article metadata if available
            if hasattr(wiki_article, "quality") and wiki_article.quality:
                article_metadata["article_quality"] = wiki_article.quality.prediction
                article_metadata["article_quality_score"] = str(
                    wiki_article.quality.probabilities.get(
                        wiki_article.quality.prediction, 0.0
                    )
                )
                article_metadata["article_quality_description"] = (
                    wiki_article.quality.get_quality_description()
                )

                logger.info(
                    f"Added quality metadata for article {wiki_article.title}: "
                    f"{wiki_article.quality.prediction} "
                    f"(confidence: {wiki_article.quality.probabilities.get(wiki_article.quality.prediction, 0.0):.2f})"
                )

            # Add metadata to each chunk with enhanced metadata
            self.add_metadata_to_chunks(
                chunks_with_embeddings, article_metadata, enhanced_metadata_dict
            )

            # Add article metadata to chunks with enhanced metadata
            self.enrich_chunks_with_article_metadata(
                chunks_with_embeddings,
                wiki_article,
                current_time,
                enhanced_metadata_dict,
            )

            # Store in Pinecone with deterministic IDs
            logger.info(f"Storing {len(chunks_with_embeddings)} vectors in Pinecone")
            vector_ids = self.pinecone_db.store_chunks(
                chunks=chunks_with_embeddings,
                id_prefix=f"wiki-{wiki_article.title.replace(' ', '_')}-",
                landmark_id=landmark_id,
                use_fixed_ids=True,
                delete_existing=delete_existing
                and total_chunks_embedded == 0,  # Only delete on first article
                enhanced_metadata=enhanced_metadata_dict,
            )

            total_chunks_embedded += len(vector_ids)
            logger.info(
                f"Stored {len(vector_ids)} vectors for article: {wiki_article.title}"
            )

        return total_chunks_embedded

    def process_landmark_wikipedia(
        self,
        landmark_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        delete_existing: bool = False,
    ) -> Tuple[bool, int, int]:
        """
        Process Wikipedia articles for a landmark and store in vector database.

        Args:
            landmark_id: ID of the landmark to process
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            delete_existing: Whether to delete existing vectors for the landmark

        Returns:
            Tuple of (success, articles_processed, chunks_embedded)
        """
        try:
            logger.info(f"Processing Wikipedia articles for landmark: {landmark_id}")

            # Step 1: Get Wikipedia articles for the landmark
            articles = self.fetch_wikipedia_articles(landmark_id)
            if not articles:
                logger.info(
                    f"No Wikipedia articles found for landmark: {landmark_id} - this is not an error"
                )
                return True, 0, 0  # Success with zero articles - not a failure

            # Step 2: Process the articles into chunks
            processed_articles, total_chunks = self.process_articles_into_chunks(
                articles, landmark_id
            )
            if not processed_articles:
                logger.warning(
                    f"No Wikipedia articles could be processed for landmark: {landmark_id} - articles found but content processing failed"
                )
                return (
                    False,
                    0,
                    0,
                )  # This is a real failure - articles exist but couldn't be processed

            logger.info(
                f"Processed {len(processed_articles)} Wikipedia articles with {total_chunks} chunks"
            )

            # Step 3: Generate embeddings and store in Pinecone
            total_chunks_embedded = self.generate_embeddings_and_store(
                processed_articles,
                landmark_id,
                delete_existing,
            )

            logger.info(f"Total chunks embedded: {total_chunks_embedded}")
            return True, len(processed_articles), total_chunks_embedded

        except Exception as e:
            logger.error(f"Error processing Wikipedia for landmark {landmark_id}: {e}")
            return False, 0, 0
