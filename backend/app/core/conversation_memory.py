"""Conversation memory: store and retrieve conversation history with context."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.conversation import Conversation

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manage conversation history with context awareness."""

    def __init__(self, max_in_memory: int = 50):
        self._max_in_memory = max_in_memory
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}

    # ------------------------------------------------------------------
    # In-memory operations
    # ------------------------------------------------------------------

    def add_message(self, session_id: str, role: str, content: str, extra: Optional[Dict] = None) -> Dict[str, Any]:
        """Add a message to the in-memory session history."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        message: Dict[str, Any] = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if extra:
            message.update(extra)

        self._sessions[session_id].append(message)

        # Trim in-memory buffer
        if len(self._sessions[session_id]) > self._max_in_memory:
            self._sessions[session_id] = self._sessions[session_id][-self._max_in_memory:]

        return message

    def get_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent history for a session."""
        messages = self._sessions.get(session_id, [])
        return messages[-limit:]

    def clear_session(self, session_id: str) -> None:
        """Clear in-memory history for a session."""
        self._sessions.pop(session_id, None)

    def get_context_summary(self, session_id: str, limit: int = 5) -> str:
        """Return a short text summary of recent conversation context."""
        messages = self.get_history(session_id, limit=limit)
        if not messages:
            return ""
        lines = [f"{m['role'].capitalize()}: {m['content']}" for m in messages]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Database persistence
    # ------------------------------------------------------------------

    def save_to_db(self, db: Session, user_id: int, session_id: str, role: str, content: str, intent: Optional[str] = None) -> Conversation:
        """Persist a conversation message to the database."""
        record = Conversation(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            intent=intent,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def load_from_db(self, db: Session, user_id: int, session_id: Optional[str] = None, limit: int = 50) -> List[Conversation]:
        """Load conversation history from the database."""
        query = db.query(Conversation).filter(Conversation.user_id == user_id)
        if session_id:
            query = query.filter(Conversation.session_id == session_id)
        return query.order_by(Conversation.created_at.desc()).limit(limit).all()
