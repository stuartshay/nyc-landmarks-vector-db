"""Wikipedia processing functionality for NYC landmarks."""

import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from transformers.tokenization_utils import PreTrainedTokenizer

from nyc_landmarks.db.wikipedia_fetcher import WikipediaFetcher
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.models.metadata_models import SourceType
from nyc_landmarks.models.wikipedia_models import WikipediaContentModel
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

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
            dict_chunks = []
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

            # Create a WikipediaContentModel with the chunks
            content_model = WikipediaContentModel(
                lpNumber=landmark_id,
                url=article.url,
                title=article.title,
                content=article.content,
                chunks=dict_chunks,
                rev_id=article.rev_id,  # Include revision ID
            )

            processed_articles.append(content_model)
            total_chunks += len(dict_chunks)

        return processed_articles, total_chunks

    def add_metadata_to_chunks(
        self,
        chunks_with_embeddings: List[Union[Dict[str, Any], Any]],
        article_metadata: Dict[str, Any],
    ) -> None:
        """Helper function to add metadata to chunks."""
        for chunk in chunks_with_embeddings:
            if isinstance(chunk, dict):
                chunk["metadata"]["wikipedia_metadata"] = article_metadata
            else:
                if hasattr(chunk, "metadata") and chunk.metadata is not None:
                    chunk.metadata["wikipedia_metadata"] = article_metadata

    def enrich_chunks_with_article_metadata(
        self,
        chunks_with_embeddings: List[Union[Dict[str, Any], Any]],
        wiki_article: WikipediaContentModel,
        current_time: str,
    ) -> None:
        """Add article metadata to chunks."""
        for chunk in chunks_with_embeddings:
            if isinstance(chunk, dict):
                # Add article_metadata field which is used by PineconeDB._create_metadata_for_chunk
                if "article_metadata" not in chunk:
                    chunk["article_metadata"] = {}
                chunk["article_metadata"]["title"] = wiki_article.title
                chunk["article_metadata"]["url"] = wiki_article.url

                # Add processing_date to be picked up by PineconeDB._create_metadata_for_chunk
                chunk["processing_date"] = current_time

                # Also add directly to metadata for backwards compatibility
                if "metadata" in chunk and chunk["metadata"] is not None:
                    chunk["metadata"]["article_title"] = wiki_article.title
                    chunk["metadata"]["article_url"] = wiki_article.url
                    chunk["metadata"]["processing_date"] = current_time
                    chunk["metadata"]["source_type"] = SourceType.WIKIPEDIA.value

                logger.info(
                    f"Added article metadata to chunk: article_title={wiki_article.title}, "
                    f"article_url={wiki_article.url}, processing_date={current_time}"
                )
            else:
                # Handle object-style chunks
                # Add article_metadata field
                if not hasattr(chunk, "article_metadata"):
                    setattr(chunk, "article_metadata", {})
                chunk.article_metadata["title"] = wiki_article.title
                chunk.article_metadata["url"] = wiki_article.url

                # Add processing_date to be picked up by PineconeDB._create_metadata_for_chunk
                setattr(chunk, "processing_date", current_time)

                # Also add directly to metadata for backwards compatibility
                if hasattr(chunk, "metadata") and chunk.metadata is not None:
                    chunk.metadata["article_title"] = wiki_article.title
                    chunk.metadata["article_url"] = wiki_article.url
                    chunk.metadata["processing_date"] = current_time
                    chunk.metadata["source_type"] = SourceType.WIKIPEDIA.value

                logger.info(
                    f"Added article metadata to object-style chunk: {wiki_article.title} "
                    f"with processing_date={current_time}"
                )

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
                enhanced_metadata_obj.model_dump() if enhanced_metadata_obj else {}
            )
            logger.info(f"Collected enhanced metadata for landmark {landmark_id}")
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

            # Add metadata to each chunk
            self.add_metadata_to_chunks(chunks_with_embeddings, article_metadata)

            # Add article metadata to chunks
            self.enrich_chunks_with_article_metadata(
                chunks_with_embeddings, wiki_article, current_time
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
