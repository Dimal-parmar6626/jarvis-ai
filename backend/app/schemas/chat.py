"""Pydantic schemas for chat endpoints."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ChatMessageRequest(BaseModel):
    """Incoming chat message from client."""

    message: str
    session_id: str = "default"
    language: str = "en-US"


class ChatMessageResponse(BaseModel):
    """Response to a chat message."""

    message: str
    intent: str
    confidence: float
    session_id: str
    timestamp: datetime


class ConversationHistoryItem(BaseModel):
    """A single item in conversation history."""

    id: int
    role: str
    content: str
    intent: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationHistoryResponse(BaseModel):
    """Paginated conversation history."""

    items: List[ConversationHistoryItem]
    total: int
    session_id: Optional[str] = None
