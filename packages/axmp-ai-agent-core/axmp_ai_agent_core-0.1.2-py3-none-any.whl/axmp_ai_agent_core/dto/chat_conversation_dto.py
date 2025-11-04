"""Conversation message request model."""

from pydantic import BaseModel, Field


class ConversationMessageRequest(BaseModel):
    """Conversation message request model."""

    message: str | None = Field(None, description="Conversation message")


class ConversationUpdateRequest(BaseModel):
    """Conversation update request model."""

    project_id: str | None = Field(None, description="Conversation project id")
    title: str | None = Field(None, description="Conversation title")
    starred: bool | None = Field(None, description="Conversation starred")
