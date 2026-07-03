"""
Embeddings Service
------------------
Generates text embeddings via Google Gemini API (text-embedding-004).

Credentials (from .env):
  GEMINI_API_KEY - API key

Currently used for:
  - Semantic similarity search across job stage chunks (future enhancement)
  - Ranking context chunks before injecting into LLM prompt

For the hackathon, embeddings are optional — the context builder falls back
to keyword matching if this service is unavailable.
"""

import os
from google import genai

def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)

def _get_deployment() -> str:
    return os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def embed(text: str) -> list[float]:
    """
    Embed a single string. Returns a list of floats (the embedding vector).
    Raises RuntimeError if credentials are missing.
    """
    client = _get_client()
    response = client.models.embed_content(
        model=_get_deployment(),
        contents=text,
    )
    return response.embeddings[0].values

def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of strings in one API call.
    Returns a list of embedding vectors in the same order as input.
    """
    if not texts:
        return []

    client = _get_client()
    response = client.models.embed_content(
        model=_get_deployment(),
        contents=texts,
    )
    return [item.values for item in response.embeddings]

def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x * x for x in a) ** 0.5
    mag_b = sum(x * x for x in b) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)

def rank_chunks_by_query(
    query: str,
    chunks: list[str],
    top_k: int = 5,
) -> list[str]:
    """
    Given a user query and a list of text chunks, return the top_k most
    semantically relevant chunks (ranked by cosine similarity).

    Falls back gracefully — returns all chunks if embedding fails.
    """
    try:
        query_vec  = embed(query)
        chunk_vecs = embed_batch(chunks)
        scored = [
            (cosine_similarity(query_vec, vec), chunk)
            for vec, chunk in zip(chunk_vecs, chunks)
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]
    except Exception:
        # Graceful fallback — return first top_k chunks without ranking
        return chunks[:top_k]