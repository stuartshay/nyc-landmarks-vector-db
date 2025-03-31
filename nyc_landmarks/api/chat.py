"""
Chat API module for NYC Landmarks Vector Database.

This module provides API endpoints for chatbot functionality with
conversation memory and vector search integration.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import openai
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from nyc_landmarks.chat.conversation import Conversation, conversation_store
from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import DbClient
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)

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


# --- Dependency injection functions ---


def get_embedding_generator():
    """Get an instance of EmbeddingGenerator."""
    return EmbeddingGenerator()


def get_vector_db():
    """Get an instance of PineconeDB."""
    return PineconeDB()


def get_db_client():
    """Get an instance of DbClient."""
    return DbClient()


# --- API endpoints ---


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    embedding_generator: EmbeddingGenerator = Depends(get_embedding_generator),
    vector_db: PineconeDB = Depends(get_vector_db),
    db_client: DbClient = Depends(get_db_client),
):
    """Process a chat message and generate a response.

    Args:
        request: Chat request model
        embedding_generator: EmbeddingGenerator instance
        vector_db: PineconeDB instance
        postgres_db: PostgresDB instance

    Returns:
        ChatResponse with assistant's response and conversation history
    """
    try:
        # Get or create conversation
        conversation = None
        if request.conversation_id:
            conversation = conversation_store.get_conversation(request.conversation_id)

        if not conversation:
            conversation = conversation_store.create_conversation()

            # Add system message to new conversation
            system_message = (
                "You are a knowledgeable assistant that specializes in New York City landmarks. "
                "Your responses should be informative, accurate, and based on the information "
                "provided in the landmark reports and database."
            )
            conversation.add_message("system", system_message)

        # Add user message to conversation
        conversation.add_message("user", request.message)

        # Get relevant context from vector database
        context_text = ""
        sources = []

        # Generate embedding for the query
        query_embedding = embedding_generator.generate_embedding(request.message)

        # Prepare filter if landmark_id is provided
        filter_dict = None
        if request.landmark_id:
            filter_dict = {"landmark_id": request.landmark_id}

        # Query the vector database
        matches = vector_db.query_vectors(
            query_embedding, top_k=3, filter_dict=filter_dict
        )

        # Process matches to create context
        for i, match in enumerate(matches):
            text = match.metadata.get("text", "")
            landmark_id = match.metadata.get("landmark_id", "")
            score = match.score

            # Only use matches with a reasonable similarity score
            if score < 0.7:  # This threshold can be adjusted
                continue

            # Add to context text
            context_text += f"\nContext {i+1}:\n{text}\n"

            # Get landmark name from database if available
            landmark_name = None
            landmark = db_client.get_landmark_by_id(landmark_id)
            if landmark:
                landmark_name = landmark.get("name")

            # Add to sources
            source = {
                "text": text[:200] + "..." if len(text) > 200 else text,
                "landmark_id": landmark_id,
                "landmark_name": landmark_name,
                "score": score,
            }
            sources.append(source)

        # Create message content with context
        messages = []

        # Add system message with context
        if context_text:
            system_context = (
                "You are a knowledgeable assistant that specializes in New York City landmarks. "
                "Use the following information from landmark reports to inform your response. "
                f"{context_text}\n\n"
                "Based on the above context, provide a helpful, accurate response about NYC landmarks. "
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

        # Add conversation history (last 5 messages)
        for msg in conversation.get_messages(limit=10):
            if (
                msg["role"] != "system"
            ):  # Skip system messages, we've handled them above
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Generate response using OpenAI API
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Can be configured in settings
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )

        # Extract response content
        assistant_response = response.choices[0].message.content

        # Add assistant response to conversation
        conversation.add_message("assistant", assistant_response)

        # Convert conversation messages to ChatMessage objects
        chat_messages = []
        for msg in conversation.get_messages():
            if msg["role"] != "system":  # Skip system messages in the response
                chat_message = ChatMessage(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=msg["timestamp"],
                )
                chat_messages.append(chat_message)

        # Create and return response
        return ChatResponse(
            conversation_id=conversation.conversation_id,
            response=assistant_response,
            messages=chat_messages,
            landmark_id=request.landmark_id,
            sources=sources,
        )
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}", response_model=List[ChatMessage])
async def get_conversation_history(conversation_id: str):
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}", response_model=Dict[str, bool])
async def delete_conversation(conversation_id: str):
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

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
