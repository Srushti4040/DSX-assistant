"""
Session Store
-------------
In-memory store for parsed DSX metadata and conversation history.
Keyed by session_id (UUID). Suitable for hackathon; swap for Redis in production.
"""

import uuid
from datetime import datetime
from typing import Any


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def create(self, parsed_metadata: dict) -> str:
        """Create a new session with parsed job metadata. Returns session_id."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "session_id":  session_id,
            "created_at":  datetime.utcnow().isoformat(),
            "job_name":    parsed_metadata["job_info"]["name"],
            "metadata":    parsed_metadata,
            "history":     [],              # list of {role, content}
        }
        return session_id

    def get(self, session_id: str) -> dict | None:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def exists(self, session_id: str) -> bool:
        return session_id in self._sessions

    # ------------------------------------------------------------------
    # Conversation history
    # ------------------------------------------------------------------

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Append a message to the session's conversation history."""
        if session_id not in self._sessions:
            raise KeyError(f"Session {session_id} not found.")
        self._sessions[session_id]["history"].append(
            {"role": role, "content": content}
        )

    def get_history(self, session_id: str) -> list[dict]:
        session = self._sessions.get(session_id)
        return session["history"] if session else []

    def get_metadata(self, session_id: str) -> dict | None:
        session = self._sessions.get(session_id)
        return session["metadata"] if session else None


# Singleton — shared across the app via dependency injection
store = SessionStore()