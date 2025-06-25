"""Agent context management and data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage


@dataclass
class AgentContext:
    """Context passed between agents during workflow execution.

    This class encapsulates all the context information that agents
    need to process requests and maintain state across handoffs.
    """

    request_id: str
    user_id: str
    guild_id: str | None = None
    conversation_history: list[BaseMessage] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate required fields."""
        if not self.request_id:
            raise ValueError("request_id is required")
        if not self.user_id:
            raise ValueError("user_id is required")


@dataclass
class AgentRequest:
    """Request data structure for agent communication.

    Encapsulates the context and action data needed for agent processing.
    """

    context: AgentContext
    action: str
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate required fields."""
        if not self.context:
            raise ValueError("context is required")
        if not self.action:
            raise ValueError("action is required")


@dataclass
class AgentResponse:
    """Response data structure for agent communication.

    Encapsulates the result of agent processing with metadata.
    """

    success: bool
    result: Any | None = None
    error: str | None = None
    confidence: float = 0.0
    reasoning: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float | None = None

    def __post_init__(self):
        """Validate response data."""
        if self.success and self.result is None:
            raise ValueError("Successful response must have a result")
        if not self.success and not self.error:
            raise ValueError("Failed response must have an error message")


class AgentContextManager:
    """Manager for agent context lifecycle and storage.

    Handles creation, storage, and retrieval of agent contexts
    during workflow execution.
    """

    def __init__(self):
        """Initialize context manager."""
        self._contexts: dict[str, AgentContext] = {}

    def create_context(
        self,
        request_id: str,
        user_id: str,
        guild_id: str | None = None,
        conversation_history: list[BaseMessage] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentContext:
        """Create a new agent context.

        Args:
            request_id: Unique identifier for this request
            user_id: User making the request
            guild_id: Optional Discord guild ID
            conversation_history: Optional conversation history
            metadata: Optional additional metadata

        Returns:
            New AgentContext instance
        """
        return AgentContext(
            request_id=request_id,
            user_id=user_id,
            guild_id=guild_id,
            conversation_history=conversation_history or [],
            metadata=metadata or {},
        )

    def store_context(self, context: AgentContext) -> None:
        """Store a context for later retrieval.

        Args:
            context: AgentContext to store
        """
        self._contexts[context.request_id] = context

    def get_context(self, request_id: str) -> AgentContext | None:
        """Retrieve a stored context.

        Args:
            request_id: Request ID to retrieve context for

        Returns:
            AgentContext if found, None otherwise
        """
        return self._contexts.get(request_id)

    def update_context(self, request_id: str, **updates) -> None:
        """Update a stored context with new data.

        Args:
            request_id: Request ID to update
            **updates: Fields to update
        """
        if request_id in self._contexts:
            context = self._contexts[request_id]
            for key, value in updates.items():
                if hasattr(context, key):
                    setattr(context, key, value)

    def remove_context(self, request_id: str) -> None:
        """Remove a context from storage.

        Args:
            request_id: Request ID to remove
        """
        self._contexts.pop(request_id, None)

    def clear_contexts(self) -> None:
        """Clear all stored contexts."""
        self._contexts.clear()
