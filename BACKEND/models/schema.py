"""
Pydantic schemas — request and response models for all API endpoints.
"""

from pydantic import BaseModel
from typing import Any


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    session_id: str
    job_name: str
    job_description: str
    summary_stats: dict[str, Any]
    lineage: dict[str, Any]
    parameters: list[dict[str, Any]]
    initial_summary: str          # AI-generated plain-English summary


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatMessage(BaseModel):
    role: str                     # "user" | "assistant"
    content: str


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    history: list[ChatMessage]


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class SessionInfo(BaseModel):
    session_id: str
    job_name: str
    message_count: int
    created_at: str