"use client";

import ReactMarkdown from "react-markdown";
import type { ChatMessage } from "@/types";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <div style={{
          maxWidth: "72%",
          background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
          color: "#fff", borderRadius: "18px 18px 4px 18px",
          padding: "12px 18px", fontSize: 14, lineHeight: 1.6,
          boxShadow: "0 2px 12px rgba(99,102,241,0.3)",
        }}>
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
      {/* Assistant Avatar */}
      <div style={{
        width: 34, height: 34, borderRadius: 10, flexShrink: 0,
        background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 11, fontWeight: 700, color: "#fff", marginTop: 2,
        boxShadow: "0 2px 8px rgba(99,102,241,0.35)",
      }}>
        DIA
      </div>

      {/* Assistant Bubble Content */}
      <div style={{
        flex: 1, minWidth: 0,
        background: "#ffffff", border: "1px solid #e2e8f0",
        borderRadius: "4px 18px 18px 18px",
        padding: "16px 20px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
        fontSize: 14, lineHeight: 1.7, color: "#334155",
      }}>
        <div className="prose-chat">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
