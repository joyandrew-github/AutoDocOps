"""Core framework: BaseAgent, AgentContext, ConversationMemory."""
from __future__ import annotations
import uuid
import time
from dataclasses import dataclass, field
from typing import Any, Generator
from app.core.logging import get_logger

logger = get_logger(__name__)


# ------------------------------------------------------------------
# AgentContext — shared state passed to every agent invocation
# ------------------------------------------------------------------

@dataclass
class AgentContext:
    """Shared context for an agent invocation."""

    repository_id: int | None = None
    conversation_id: str | None = None
    user_message: str = ""
    selected_entities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def clone(self, **overrides) -> "AgentContext":
        return AgentContext(
            repository_id=overrides.get("repository_id", self.repository_id),
            conversation_id=overrides.get("conversation_id", self.conversation_id),
            user_message=overrides.get("user_message", self.user_message),
            selected_entities=overrides.get("selected_entities", list(self.selected_entities)),
            metadata={**self.metadata, **overrides.get("metadata", {})},
        )


# ------------------------------------------------------------------
# AgentResponse
# ------------------------------------------------------------------

@dataclass
class AgentResponse:
    """Response returned by an agent."""

    agent_name: str = ""
    content: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    tool_calls: list[dict] = field(default_factory=list)
    status: str = "success"
    duration_seconds: float = 0.0
    error: str | None = None


# ------------------------------------------------------------------
# BaseAgent — abstract base class for all agents
# ------------------------------------------------------------------

class BaseAgent:
    """Abstract base agent. Subclasses must implement handle()."""

    name: str = "base"
    description: str = ""
    capabilities: list[str] = []

    def __init__(self, db=None):
        self.db = db

    def handle(self, context: AgentContext) -> AgentResponse:
        raise NotImplementedError

    def stream(self, context: AgentContext) -> Generator[str, None, None]:
        """Streaming response; default implementation yields full response."""
        resp = self.handle(context)
        yield resp.content

    def can_handle(self, message: str) -> float:
        """Return a confidence score 0–1 for whether this agent can handle the message."""
        score = 0.0
        msg_lower = message.lower()
        for cap in self.capabilities:
            if cap in msg_lower:
                score = max(score, 0.6)
        return score

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"


# ------------------------------------------------------------------
# ConversationMemory — maintains conversation history
# ------------------------------------------------------------------

class ConversationMemory:
    """In-memory conversation history per conversation id."""

    def __init__(self):
        self._conversations: dict[str, list[dict]] = {}

    def get_or_create(self, conversation_id: str | None = None) -> str:
        cid = conversation_id or str(uuid.uuid4())
        if cid not in self._conversations:
            self._conversations[cid] = []
        return cid

    def add_user_message(self, conversation_id: str, message: str) -> None:
        self._conversations.setdefault(conversation_id, []).append({
            "role": "user", "content": message, "timestamp": time.time(),
        })

    def add_agent_message(self, conversation_id: str, agent_name: str, content: str) -> None:
        self._conversations.setdefault(conversation_id, []).append({
            "role": "agent", "agent": agent_name, "content": content, "timestamp": time.time(),
        })

    def get_history(self, conversation_id: str, limit: int = 50) -> list[dict]:
        return self._conversations.get(conversation_id, [])[-limit:]

    def get_context_summary(self, conversation_id: str) -> str:
        history = self.get_history(conversation_id, limit=10)
        if not history:
            return ""
        parts = []
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")[:200]
            parts.append(f"[{role}] {content}")
        return "\n".join(parts)

    def clear(self, conversation_id: str) -> None:
        self._conversations.pop(conversation_id, None)

    def list_conversations(self) -> list[str]:
        return list(self._conversations.keys())
