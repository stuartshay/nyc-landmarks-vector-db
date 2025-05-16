"""
Chat API module for NYC Landmarks Vector Database.

This module provides API endpoints for chatbot functionality with
conversation memory and vector search integration. It enables users
to interact with the NYC Landmarks database using natural language.
"""

from typing import Any, Dict, List, Optional, Protocol, Tuple

import openai
from fastapi import APIRouter, Depends, HTTPException
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field

from nyc_landmarks.chat.conversation import Conversation, conversation_store
from nyc_landmarks.db.db_client import DbClient
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.pinecone_db import PineconeDB


# Define a protocol for QueryMatch to avoid direct import
class QueryMatch(Protocol):
    """Protocol for Pinecone query match object."""

    id: str
    score: float
    metadata: Dict[str, Any]


# Configure logging
logger = get_logger(__name__)

# Create API router
router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
)


# --- Pydantic models for requests and responses ---


class ChatMessage(BaseModel):
    """Chat message model."""

    role: str = Field(
        ..., description="Role of the message sender (user, assistant, system)"
    )
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[float] = Field(None, description="Timestamp of the message")


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str = Field(..., description="User message content")
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for continuing a conversation"
    )
    landmark_id: Optional[str] = Field(
        None, description="Optional landmark ID to focus the chat on"
    )


class ChatResponse(BaseModel):
    """Chat response model."""

    conversation_id: str = Field(..., description="Conversation ID")
    response: str = Field(..., description="Assistant response")
    messages: List[ChatMessage] = Field([], description="Conversation history")
    landmark_id: Optional[str] = Field(None, description="Landmark ID if specified")
    sources: List[Dict[str, Any]] = Field(
        [], description="Sources of information used in the response"
    )
    source_types: List[str] = Field(
        [], description="Types of sources used (wikipedia, pdf)"
    )


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history endpoint."""

    messages: List[ChatMessage] = Field(
        ..., description="List of messages in the conversation"
    )


class DeleteConversationResponse(BaseModel):
    """Response model for delete conversation endpoint."""

    success: bool = Field(
        ..., description="Whether the conversation was deleted successfully"
    )


# --- Dependency injection functions ---


def get_embedding_generator() -> EmbeddingGenerator:
    """Get an instance of EmbeddingGenerator."""
    return EmbeddingGenerator()


def get_vector_db() -> PineconeDB:
    """Get an instance of PineconeDB."""
    return PineconeDB()


def get_db_client() -> DbClient:
    """Get an instance of DbClient."""
    from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI

    return DbClient(CoreDataStoreAPI())


# --- Helper functions ---


def _get_or_create_conversation(conversation_id: Optional[str] = None) -> Conversation:
    """Get an existing conversation or create a new one.

    Args:
        conversation_id: Optional ID of an existing conversation

    Returns:
        The conversation object
    """
    conversation = None
    if conversation_id:
        conversation = conversation_store.get_conversation(conversation_id)

    if not conversation:
        conversation = conversation_store.create_conversation()

        # Add system message to new conversation
        system_message = (
            "You are a knowledgeable assistant that specializes in New York City landmarks. "
            "Your responses should be informative, accurate, and based on the information "
            "provided in the landmark reports and database."
        )
        conversation.add_message("system", system_message)

    return conversation


def _extract_metadata_and_score(match: Any) -> Tuple[Dict[str, Any], float]:
    """Extract metadata and score from a match result.

    Args:
        match: Match result from vector search

    Returns:
        Tuple of (metadata, score)
    """
    try:
        # Try accessing as an object (Protocol definition)
        metadata = (
            match.metadata if hasattr(match, "metadata") else match.get("metadata", {})
        )
        score = match.score if hasattr(match, "score") else match.get("score", 0)
    except (AttributeError, TypeError):
        # Fall back to dict access (actual Pinecone response)
        metadata = match.get("metadata", {})
        score = match.get("score", 0)

    return metadata, score


def _format_source_info(metadata: Dict[str, Any]) -> str:
    """Format source information based on metadata.

    Args:
        metadata: Vector metadata

    Returns:
        Formatted source information string
    """
    source_type = metadata.get("source_type", "pdf")

    if source_type == "wikipedia":
        article_title = metadata.get("article_title", "Unknown Wikipedia Article")
        return f"[Source: Wikipedia article '{article_title}']"
    else:
        document_name = metadata.get(
            "document_name", metadata.get("file_name", "Unknown Document")
        )
        return f"[Source: LPC Report '{document_name}']"


def _get_landmark_name(landmark_id: str, db_client: DbClient) -> Optional[str]:
    """Get landmark name from database.

    Args:
        landmark_id: Landmark ID
        db_client: Database client

    Returns:
        Landmark name or None if not found
    """
    landmark = db_client.get_landmark_by_id(landmark_id)
    if not landmark:
        return None

    # Handle both dict and Pydantic model objects
    if isinstance(landmark, dict):
        return landmark.get("name")
    else:
        return getattr(landmark, "name", None)


def _create_source_object(
    metadata: Dict[str, Any],
    score: float,
    source_info: str,
    landmark_name: Optional[str],
) -> Dict[str, Any]:
    """Create a source object for response.

    Args:
        metadata: Vector metadata
        score: Match score
        source_info: Formatted source information
        landmark_name: Landmark name

    Returns:
        Source object dictionary
    """
    text = metadata.get("text", "")
    landmark_id = metadata.get("landmark_id", "")
    source_type = metadata.get("source_type", "pdf")

    # Create source URL if available
    source_url = None
    if source_type == "wikipedia":
        source_url = metadata.get("article_url", "")
    else:
        source_url = metadata.get("document_url", "")

    return {
        "text": text[:200] + "..." if len(text) > 200 else text,
        "landmark_id": landmark_id,
        "landmark_name": landmark_name,
        "score": score,
        "source_type": source_type,
        "source": source_info,
        "source_url": source_url,
    }


def _get_context_from_vector_db(
    query: str,
    embedding_generator: EmbeddingGenerator,
    vector_db: PineconeDB,
    db_client: DbClient,
    landmark_id: Optional[str] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Get relevant context from the vector database.

    Args:
        query: User's query
        embedding_generator: EmbeddingGenerator instance
        vector_db: PineconeDB instance
        db_client: Database client instance
        landmark_id: Optional landmark ID to filter results

    Returns:
        Tuple of (context_text, sources)
    """
    context_text = ""
    sources = []

    # Generate embedding for the query
    query_embedding = embedding_generator.generate_embedding(query)

    # Prepare filter dictionary
    filter_dict = {}
    if landmark_id:
        filter_dict["landmark_id"] = landmark_id

    # Only pass filter_dict if it has values
    filter_to_use = filter_dict if filter_dict else None

    # Query the vector database to get combined results from both Wikipedia and PDF sources
    matches = vector_db.query_vectors(
        query_embedding, top_k=5, filter_dict=filter_to_use
    )

    # Process matches to create context
    for i, match in enumerate(matches):
        # Extract metadata and score
        metadata, score = _extract_metadata_and_score(match)

        # Only use matches with a reasonable similarity score
        if score < 0.7:  # This threshold can be adjusted
            continue

        text = metadata.get("text", "")
        landmark_id_from_metadata = metadata.get("landmark_id", "")

        # Format source attribution
        source_info = _format_source_info(metadata)

        # Add to context text
        context_text += f"\nContext {i + 1} {source_info}:\n{text}\n"

        # Get landmark name
        landmark_name = None
        if landmark_id_from_metadata:
            landmark_name = _get_landmark_name(landmark_id_from_metadata, db_client)

        # Create and add source object
        source = _create_source_object(metadata, score, source_info, landmark_name)
        sources.append(source)

    return context_text, sources


def _prepare_chat_messages(
    conversation: Conversation, context_text: str
) -> List[ChatCompletionMessageParam]:
    """Prepare the list of messages for the chat completion API.

    Args:
        conversation: Conversation object
        context_text: Context text from vector search

    Returns:
        List of messages for the chat completion API
    """
    messages: List[ChatCompletionMessageParam] = []

    # Add system message with context
    if context_text:
        system_context = (
            "You are a knowledgeable assistant that specializes in New York City landmarks. "
            "Use the following information from landmark reports and Wikipedia articles to inform your response. "
            f"{context_text}\n\n"
            "Based on the above context, provide a helpful, accurate response about NYC landmarks. "
            "When using information from Wikipedia, acknowledge it appropriately. "
            "If the context doesn't contain relevant information to answer the question, "
            "say that you don't have specific information about that and provide general "
            "information about NYC landmarks if possible."
        )
        messages.append({"role": "system", "content": system_context})
    else:
        messages.append(
            {
                "role": "system",
                "content": "You are a knowledgeable assistant that specializes in New York City landmarks.",
            }
        )

    # Add conversation history (last 10 messages)
    for msg in conversation.get_messages(limit=10):
        if msg["role"] != "system":  # Skip system messages, we've handled them above
            messages.append({"role": msg["role"], "content": msg["content"]})

    return messages


def _convert_to_chat_messages(conversation: Conversation) -> List[ChatMessage]:
    """Convert conversation messages to ChatMessage objects.

    Args:
        conversation: Conversation object

    Returns:
        List of ChatMessage objects
    """
    chat_messages = []
    for msg in conversation.get_messages():
        if msg["role"] != "system":  # Skip system messages in the response
            chat_message = ChatMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"],
            )
            chat_messages.append(chat_message)
    return chat_messages


# --- API endpoints ---


@router.post("/message", response_model=ChatResponse)  # type: ignore[misc]
async def chat_message(
    request: ChatRequest,
    embedding_generator: EmbeddingGenerator = Depends(get_embedding_generator),
    vector_db: PineconeDB = Depends(get_vector_db),
    db_client: DbClient = Depends(get_db_client),
) -> ChatResponse:
    """Process a chat message and generate a response.

    Args:
        request: Chat request model
        embedding_generator: EmbeddingGenerator instance
        vector_db: PineconeDB instance
        db_client: Database client instance

    Returns:
        ChatResponse with assistant's response and conversation history
    """
    try:
        # Get or create conversation
        conversation = _get_or_create_conversation(request.conversation_id)

        # Add user message to conversation
        conversation.add_message("user", request.message)

        # Get relevant context from vector database
        context_text, sources = _get_context_from_vector_db(
            request.message,
            embedding_generator,
            vector_db,
            db_client,
            request.landmark_id,
        )

        # Prepare messages for chat completion API
        messages = _prepare_chat_messages(conversation, context_text)

        # Generate response using OpenAI API
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Can be configured in settings
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )

        # Extract response content
        assistant_response = response.choices[0].message.content or ""

        # Add assistant response to conversation
        conversation.add_message("assistant", assistant_response)

        # Convert conversation messages to ChatMessage objects
        chat_messages = _convert_to_chat_messages(conversation)

        # Extract source types for the response
        source_types = list({source.get("source_type", "pdf") for source in sources})

        # Create and return response
        return ChatResponse(
            conversation_id=conversation.conversation_id,
            response=assistant_response,
            messages=chat_messages,
            landmark_id=request.landmark_id,
            sources=sources,
            source_types=source_types,
        )
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}", response_model=ConversationHistoryResponse)  # type: ignore[misc]
async def get_conversation_history(conversation_id: str) -> ConversationHistoryResponse:
    """Get conversation history.

    Args:
        conversation_id: ID of the conversation

    Returns:
        List of chat messages
    """
    try:
        # Get conversation
        conversation = conversation_store.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=404, detail=f"Conversation not found: {conversation_id}"
            )

        # Convert conversation messages to ChatMessage objects
        messages = _convert_to_chat_messages(conversation)

        # Return response model
        return ConversationHistoryResponse(messages=messages)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}", response_model=DeleteConversationResponse)  # type: ignore[misc]
async def delete_conversation(conversation_id: str) -> DeleteConversationResponse:
    """Delete a conversation.

    Args:
        conversation_id: ID of the conversation

    Returns:
        Dictionary with success status
    """
    try:
        # Delete conversation
        success = conversation_store.delete_conversation(conversation_id)

        if not success:
            raise HTTPException(
                status_code=404, detail=f"Conversation not found: {conversation_id}"
            )

        return DeleteConversationResponse(success=True)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
