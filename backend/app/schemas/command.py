"""Pydantic schemas for command and task endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


class CommandCreate(BaseModel):
    """Create a custom command."""

    name: str
    trigger: str
    action: str  # JSON-encoded action descriptor
    description: str = ""


class CommandResponse(BaseModel):
    """A custom command record."""

    id: int
    name: str
    trigger: str
    action: str
    description: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CommandListResponse(BaseModel):
    """List of commands."""

    items: List[CommandResponse]
    total: int


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


class TaskExecuteRequest(BaseModel):
    """Request to execute a task."""

    task_type: str  # "open_app" | "file" | "system_info" | "weather" | "search" | ...
    payload: Dict[str, Any] = {}
    name: str = ""
    description: str = ""
    schedule_at: Optional[datetime] = None


class TaskResponse(BaseModel):
    """A task record."""

    id: int
    name: str
    description: str
    task_type: str
    payload: str
    status: str
    result: str
    scheduled_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """List of tasks."""

    items: List[TaskResponse]
    total: int


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class UserRegister(BaseModel):
    """User registration payload."""

    username: str
    email: str
    password: str
    full_name: str = ""


class UserLogin(BaseModel):
    """User login credentials."""

    username: str
    password: str


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UserPreferences(BaseModel):
    """User preference settings."""

    language: str = "en-US"
    tts_voice: str = "default"
    theme: str = "dark"
    notifications: bool = True
    extra: Dict[str, Any] = {}
