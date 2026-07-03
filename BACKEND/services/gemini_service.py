"""
Gemini Service
--------------
Connects to Google Gemini API (gemini-2.5-flash).

Credentials (from .env):
  GEMINI_API_KEY - your Gemini API key

Provides:
  ask()          — single-turn non-streaming call
  chat()         — multi-turn conversation with history
  stream_chat()  — async streaming generator for SSE responses
"""

import os
from typing import AsyncGenerator
from google import genai
from google.genai import types

MAX_TOKENS = 2048

def _get_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in .env")
    return genai.Client(api_key=api_key)

# ---------------------------------------------------------------------------
# Single-turn (used for initial summary on upload)
# ---------------------------------------------------------------------------

def ask(system_prompt: str, user_prompt: str) -> str:
    """Single non-streaming call."""
    client = _get_client()
    response = client.models.generate_content(
        model=_get_model(),
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=MAX_TOKENS,
        ),
    )
    return response.text

# ---------------------------------------------------------------------------
# Multi-turn chat (used for /chat endpoint)
# ---------------------------------------------------------------------------

def _map_history(history: list[dict]) -> list[types.Content]:
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(msg["content"])]))
    return contents

def chat(system_prompt: str, history: list[dict]) -> str:
    """
    Multi-turn chat. `history` is a list of {role, content} dicts.
    Returns the assistant's reply as a string.
    """
    client = _get_client()
    contents = _map_history(history)
    response = client.models.generate_content(
        model=_get_model(),
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=MAX_TOKENS,
        )
    )
    return response.text

# ---------------------------------------------------------------------------
# Streaming chat (used by /chat/stream endpoint)
# ---------------------------------------------------------------------------

async def stream_chat(
    system_prompt: str,
    history: list[dict],
) -> AsyncGenerator[str, None]:
    """
    Async generator that yields text chunks as they stream from Gemini.
    """
    client = _get_client()
    contents = _map_history(history)
    
    response_stream = await client.aio.models.generate_content_stream(
        model=_get_model(),
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=MAX_TOKENS,
        )
    )
    async for chunk in response_stream:
        if chunk.text:
            yield chunk.text
