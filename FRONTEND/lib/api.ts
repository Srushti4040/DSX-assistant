import type { JobInfo, ChatResponse } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Upload a DSX file
// ---------------------------------------------------------------------------
export async function uploadDSX(file: File): Promise<JobInfo> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${BASE_URL}/api/upload`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail ?? "Upload failed");
  }

  return res.json();
}

// ---------------------------------------------------------------------------
// Send a chat message
// ---------------------------------------------------------------------------
export async function sendMessage(
  sessionId: string,
  message: string
): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Chat failed" }));
    throw new Error(err.detail ?? "Chat failed");
  }

  return res.json();
}

// ---------------------------------------------------------------------------
// Stream a chat message (returns a ReadableStream reader)
// ---------------------------------------------------------------------------
export async function streamMessage(
  sessionId: string,
  message: string
): Promise<ReadableStreamDefaultReader<Uint8Array>> {
  const res = await fetch(`${BASE_URL}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  if (!res.ok || !res.body) {
    throw new Error("Stream failed");
  }

  return res.body.getReader();
}

// ---------------------------------------------------------------------------
// Clear a session
// ---------------------------------------------------------------------------
export async function clearSession(sessionId: string): Promise<void> {
  await fetch(`${BASE_URL}/api/session/${sessionId}`, { method: "DELETE" });
}
