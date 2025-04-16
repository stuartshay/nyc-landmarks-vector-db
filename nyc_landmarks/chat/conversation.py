"""
Conversation memory module for NYC Landmarks Vector Database.

This module handles the storage and retrieval of conversation history
for the chatbot functionality.
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from nyc_landmarks.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class Conversation:
    """Model for a conversation with the chatbot."""

    def __init__(self, conversation_id: Optional[str] = None):
        """Initialize a conversation.

        Args:
            conversation_id: ID for the conversation (generated if not provided)
        """
        self.conversation_id = conversation_id if conversation_id else str(uuid.uuid4())
        self.messages: List[Dict[str, Any]] = []
        self.created_at = time.time()
        self.updated_at = time.time()

    def add_message(
        self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a message to the conversation.

        Args:
            role: Role of the message sender (user, assistant, system)
            content: Content of the message
            metadata: Additional metadata for the message
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
        }

        if metadata:
            message["metadata"] = metadata

        self.messages.append(message)
        self.updated_at = time.time()

    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get messages from the conversation.

        Args:
            limit: Maximum number of messages to return (most recent first)

        Returns:
            List of messages
        """
        if limit:
            return self.messages[-limit:]
        return self.messages

    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary.

        Returns:
            Dictionary representation of the conversation
        """
        return {
            "conversation_id": self.conversation_id,
            "messages": self.messages,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create a conversation from a dictionary.

        Args:
            data: Dictionary representation of a conversation

        Returns:
            Conversation instance
        """
        conversation = cls(conversation_id=data.get("conversation_id"))
        conversation.messages = data.get("messages", [])
        conversation.created_at = data.get("created_at", time.time())
        conversation.updated_at = data.get("updated_at", time.time())
        return conversation


class ConversationStore:
    """In-memory store for conversation history."""

    def __init__(self):
        """Initialize the conversation store."""
        self.conversations: Dict[str, Conversation] = {}
        self.ttl = settings.CONVERSATION_TTL  # Time to live in seconds

    def create_conversation(self) -> Conversation:
        """Create a new conversation.

        Returns:
            New conversation instance
        """
        conversation = Conversation()
        self.conversations[conversation.conversation_id] = conversation

        logger.info(f"Created conversation: {conversation.conversation_id}")
        return conversation

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID.

        Args:
            conversation_id: ID of the conversation

        Returns:
            Conversation instance, or None if not found
        """
        # Check if conversation exists
        conversation = self.conversations.get(conversation_id)

        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return None

        # Check if conversation has expired
        if time.time() - conversation.updated_at > self.ttl:
            logger.info(f"Conversation expired: {conversation_id}")
            del self.conversations[conversation_id]
            return None

        return conversation

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            True if deleted, False if not found
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Deleted conversation: {conversation_id}")
            return True

        logger.warning(f"Conversation not found for deletion: {conversation_id}")
        return False

    def cleanup_expired(self) -> int:
        """Clean up expired conversations.

        Returns:
            Number of conversations deleted
        """
        current_time = time.time()
        expired_ids = [
            conv_id
            for conv_id, conv in self.conversations.items()
            if current_time - conv.updated_at > self.ttl
        ]

        for conv_id in expired_ids:
            del self.conversations[conv_id]

        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired conversations")

        return len(expired_ids)


# Create a global instance of the conversation store
conversation_store = ConversationStore()
