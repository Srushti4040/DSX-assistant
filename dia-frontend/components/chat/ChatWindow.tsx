"use client";

import { useState, useRef, useEffect } from "react";
import { sendMessage } from "@/lib/api";
import MessageBubble from "./MessageBubble";
import type { ChatMessage, JobInfo } from "@/types";

const SUGGESTED = [
  { icon: "📋", text: "Explain this job step by step" },
  { icon: "🔗", text: "Trace the data lineage" },
  { icon: "⚙️", text: "List all business rules" },
  { icon: "🔄", text: "Convert this pipeline to SQL" },
  { icon: "⚠️", text: "What are the pipeline risks?" },
  { icon: "💡", text: "Impact of changing DISCOUNT_PCT?" },
];

export default function ChatWindow({ job }: { job: JobInfo }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  // Initialize messages safely when job changes
  useEffect(() => {
    if (job?.initial_summary) {
      setMessages([{ role: "assistant", content: job.initial_summary }]);
    }
  }, [job]);

  // Smooth scroll to bottom on new messages or loading states
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;

    setMessages((p) => [...p, { role: "user", content: text }]);
    setInput("");
    setError(null);
    setLoading(true);

    if (taRef.current) taRef.current.style.height = "auto";

    try {
      const r = await sendMessage(job.session_id, text);
      setMessages((p) => [...p, { role: "assistant", content: r.reply }]);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const onKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  };

  const onInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + "px";
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#f8fafc" }}>
      {/* Messages Stream */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px", display: "flex", flexDirection: "column", gap: 20 }}>
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}

        {/* Loading / Typing Indicator */}
        {loading && (
          <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
            <div style={{
              width: 34, height: 34, borderRadius: 10, flexShrink: 0,
              background: "linear-gradient(135deg,#6366f1,#8b5cf6)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 11, fontWeight: 700, color: "#fff",
            }}>DIA</div>
            <div style={{
              background: "#fff", border: "1px solid #e2e8f0", borderRadius: "4px 18px 18px 18px",
              padding: "14px 20px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
              display: "flex", alignItems: "center", gap: 6,
            }}>
              {[0, 0.2, 0.4].map((delay, i) => (
                <span key={i} style={{
                  width: 7, height: 7, borderRadius: "50%", background: "#cbd5e1", display: "inline-block",
                  animation: `bounce 1.2s ease-in-out ${delay}s infinite`,
                }} />
              ))}
            </div>
          </div>
        )}

        {/* Error Notification */}
        {error && (
          <div style={{
            background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 12,
            padding: "12px 16px", color: "#dc2626", fontSize: 13, display: "flex", gap: 8,
          }}>
            <span>⚠️</span> {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggested Prompts (Only visible at start) */}
      {messages.length === 1 && (
        <div style={{ padding: "0 24px 16px", flexShrink: 0 }}>
          <p style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "#94a3b8", marginBottom: 10 }}>
            ✨ Try asking
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {SUGGESTED.map((s) => (
              <button
                key={s.text}
                onClick={() => send(s.text)}
                style={{
                  display: "flex", alignItems: "flex-start", gap: 10,
                  background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12,
                  padding: "10px 14px", textAlign: "left", cursor: "pointer",
                  fontSize: 12, color: "#475569", lineHeight: 1.4, fontFamily: "inherit",
                  transition: "all 0.15s",
                }}
                onMouseEnter={(e) => {
                  const b = e.currentTarget;
                  b.style.borderColor = "#6366f1";
                  b.style.color = "#4f46e5";
                  b.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.1)";
                }}
                onMouseLeave={(e) => {
                  const b = e.currentTarget;
                  b.style.borderColor = "#e2e8f0";
                  b.style.color = "#475569";
                  b.style.boxShadow = "none";
                }}
              >
                <span style={{ fontSize: 15, flexShrink: 0, marginTop: 1 }}>{s.icon}</span>
                <span>{s.text}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form Controls */}
      <div style={{ padding: "12px 24px 20px", flexShrink: 0 }}>
        <div style={{
          background: "#fff", border: "1px solid #e2e8f0", borderRadius: 18,
          boxShadow: "0 4px 16px rgba(0,0,0,0.07)",
          transition: "border-color 0.15s, box-shadow 0.15s",
        }}
          onFocusCapture={(e) => {
            e.currentTarget.style.borderColor = "#6366f1";
            e.currentTarget.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.12), 0 4px 16px rgba(0,0,0,0.07)";
          }}
          onBlurCapture={(e) => {
            e.currentTarget.style.borderColor = "#e2e8f0";
            e.currentTarget.style.boxShadow = "0 4px 16px rgba(0,0,0,0.07)";
          }}
        >
          <div style={{ display: "flex", alignItems: "flex-end", gap: 10, padding: "14px 16px 10px" }}>
            <textarea
              ref={taRef}
              value={input}
              onChange={onInput}
              onKeyDown={onKey}
              placeholder="Ask DIA anything about this DataStage job…"
              rows={1}
              style={{
                flex: 1, background: "transparent", border: "none", outline: "none", resize: "none",
                fontSize: 14, color: "#1e293b", lineHeight: 1.6,
                fontFamily: "'Inter', system-ui, sans-serif",
                minHeight: 28, maxHeight: 160,
              }}
            />
            <button
              onClick={() => send(input)}
              disabled={!input.trim() || loading}
              style={{
                flexShrink: 0, width: 38, height: 38, borderRadius: 12,
                background: input.trim() && !loading ? "linear-gradient(135deg,#6366f1,#8b5cf6)" : "#f1f5f9",
                border: "none", cursor: input.trim() && !loading ? "pointer" : "default",
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "all 0.2s",
                boxShadow: input.trim() && !loading ? "0 2px 8px rgba(99,102,241,0.4)" : "none",
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                stroke={input.trim() && !loading ? "#fff" : "#94a3b8"}
                strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z" />
              </svg>
            </button>
          </div>
          <div style={{ padding: "0 16px 10px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 11, color: "#cbd5e1" }}>Enter to send · Shift+Enter for new line</span>
            {loading && <span style={{ fontSize: 11, color: "#6366f1", fontWeight: 500 }}>DIA is thinking…</span>}
          </div>
        </div>
      </div>

      <style>{`@keyframes bounce { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-5px)} }`}</style>
    </div>
  );
}
