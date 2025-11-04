"""This module contains the list model for the alert."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from axmp_ai_agent_core.entity.user_rbac import Group, Role, User
from axmp_ai_agent_core.util.list_utils import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)


class BaseListModel(BaseModel):
    """Base list model for alert."""

    current_page: int = Field(DEFAULT_PAGE_NUMBER, ge=DEFAULT_PAGE_NUMBER)
    page_size: int = Field(DEFAULT_PAGE_SIZE, le=MAX_PAGE_SIZE)
    total: int = Field(0, ge=0)

    model_config = ConfigDict(exclude_none=True)


class GroupList(BaseListModel):
    """Group list model."""

    data: list[Group]


class RoleList(BaseListModel):
    """Role list model."""

    data: list[Role]


class UserList(BaseListModel):
    """User list model."""

    data: list[User]
