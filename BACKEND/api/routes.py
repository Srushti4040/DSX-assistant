"""
API Routes — DIA (DataStage Intelligence Assistant)
----------------------------------------------------
  POST /upload          — Upload DSX file → parse → AI summary → session
  POST /chat            — Intent-aware conversational Q&A about the uploaded job
  GET  /session/{id}    — Get session info
  DELETE /session/{id}  — Clear a session
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse

from api.dependencies import get_session_store
from services.session_store import SessionStore
from services import gemini_service
from parser.dsx_parser import parse_dsx_text
from prompts.templates import (
    SYSTEM_PROMPT,
    initial_summary_prompt,
    chat_system_prompt,
    enhance_user_message,
)
from models.schema import (
    UploadResponse,
    ChatRequest,
    ChatResponse,
    ChatMessage,
    SessionInfo,
)

router = APIRouter()

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB

# Max conversation turns to keep (older turns dropped to stay within token limits)
MAX_HISTORY_TURNS = 10


def _trim_history(history: list[dict]) -> list[dict]:
    """
    Keep only the most recent MAX_HISTORY_TURNS pairs.
    Always keep the first assistant message (initial summary) for context.
    """
    if len(history) <= MAX_HISTORY_TURNS * 2:
        return history
    # Keep first message (initial summary) + most recent turns
    first = history[:1]
    rest  = history[1:]
    recent = rest[-(MAX_HISTORY_TURNS * 2 - 1):]
    return first + recent


# ---------------------------------------------------------------------------
# POST /upload
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=UploadResponse)
async def upload_dsx(
    file: UploadFile = File(...),
    store: SessionStore = Depends(get_session_store),
):
    if not file.filename.endswith((".dsx", ".xml")):
        raise HTTPException(status_code=400, detail="Only .dsx or .xml files are supported.")

    contents = await file.read()
    if len(contents) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit.")

    # Parse DSX
    try:
        dsx_text = contents.decode("utf-8", errors="replace")
        metadata = parse_dsx_text(dsx_text)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse DSX file: {str(e)}")

    # Store raw DSX text in metadata so it can be referenced later
    metadata["_raw_filename"] = file.filename

    # Create session
    session_id = store.create(metadata)

    # Generate initial AI summary
    try:
        summary_prompt = initial_summary_prompt(metadata)
        initial_summary = gemini_service.ask(SYSTEM_PROMPT, summary_prompt)
    except Exception as e:
        initial_summary = (
            f"DSX file parsed successfully. Job: **{metadata['job_info']['name']}** "
            f"({metadata['summary_stats']['total_stages']} stages, "
            f"{metadata['summary_stats']['total_parameters']} parameters). "
            f"AI summary unavailable: {str(e)}"
        )

    # Store as first assistant message (kept short — full context is in system prompt)
    store.add_message(session_id, "assistant", initial_summary)

    return UploadResponse(
        session_id=session_id,
        job_name=metadata["job_info"]["name"],
        job_description=metadata["job_info"]["description"],
        summary_stats=metadata["summary_stats"],
        lineage=metadata["lineage"],
        parameters=metadata["parameters"],
        initial_summary=initial_summary,
    )


# ---------------------------------------------------------------------------
# POST /chat
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    store: SessionStore = Depends(get_session_store),
):
    if not store.exists(body.session_id):
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please upload a DSX file first."
        )

    metadata = store.get_metadata(body.session_id)

    # Build system prompt — includes full job context
    system = chat_system_prompt(metadata)

    # Enhance user message with intent-specific context hints
    enhanced_message = enhance_user_message(body.message, metadata)

    # Add enhanced message to history
    store.add_message(body.session_id, "user", enhanced_message)
    history = _trim_history(store.get_history(body.session_id))

    # Call LLM
    try:
        reply = gemini_service.chat(system, history)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM API error: {str(e)}")

    # Store reply
    store.add_message(body.session_id, "assistant", reply)

    # Return original message in history (not enhanced) for clean UI display
    clean_history = []
    for msg in store.get_history(body.session_id):
        role    = msg["role"]
        content = msg["content"]
        # Strip the [CONTEXT] prefix from user messages for display
        if role == "user" and content.startswith("[") and "USER QUESTION: " in content:
            content = content.split("USER QUESTION: ", 1)[-1]
        clean_history.append(ChatMessage(role=role, content=content))

    return ChatResponse(
        reply=reply,
        session_id=body.session_id,
        history=clean_history,
    )


# ---------------------------------------------------------------------------
# POST /chat/stream
# ---------------------------------------------------------------------------

@router.post("/chat/stream")
async def chat_stream(
    body: ChatRequest,
    store: SessionStore = Depends(get_session_store),
):
    if not store.exists(body.session_id):
        raise HTTPException(status_code=404, detail="Session not found.")

    metadata = store.get_metadata(body.session_id)
    system   = chat_system_prompt(metadata)

    enhanced_message = enhance_user_message(body.message, metadata)
    store.add_message(body.session_id, "user", enhanced_message)
    history = _trim_history(store.get_history(body.session_id))

    full_reply: list[str] = []

    async def generate():
        async for chunk in gemini_service.stream_chat(system, history):
            full_reply.append(chunk)
            yield chunk
        store.add_message(body.session_id, "assistant", "".join(full_reply))

    return StreamingResponse(generate(), media_type="text/plain")


# ---------------------------------------------------------------------------
# GET /session/{session_id}
# ---------------------------------------------------------------------------

@router.get("/session/{session_id}", response_model=SessionInfo)
def get_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
):
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    return SessionInfo(
        session_id=session_id,
        job_name=session["job_name"],
        message_count=len(session["history"]),
        created_at=session["created_at"],
    )


# ---------------------------------------------------------------------------
# DELETE /session/{session_id}
# ---------------------------------------------------------------------------

@router.delete("/session/{session_id}")
def delete_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
):
    deleted = store.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"message": f"Session {session_id} deleted."}