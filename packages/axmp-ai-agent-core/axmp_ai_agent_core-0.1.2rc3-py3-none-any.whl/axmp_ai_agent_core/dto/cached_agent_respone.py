"""Cached agent response."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from axmp_ai_agent_core.agent.util.mcp_client_manager import McpServer
from axmp_ai_agent_core.entity.llm_provider import LlmModel


class CachedAgentResponse(BaseModel):
    """Cached agent response."""

    agent_id: str | None = None
    agent_version: int | None = None
    agent_owner: str | None = None
    agent_description: str | None = None
    init_message: str | None = None
    llm_provider_id: str | None = None
    llm_default_model: str | None = None
    llm_models: list[LlmModel] | None = None
    knowledge_base_id: str | None = None
    knowledge_base_name: str | None = None
    mcp_servers: list[McpServer] | None = None


class ConversationState(BaseModel):
    """Conversation state model."""

    messages: list[dict[str, Any]] | None = None
    """The messages of the conversation."""
    created_at: datetime | None = None
    """The created date of the conversation."""
