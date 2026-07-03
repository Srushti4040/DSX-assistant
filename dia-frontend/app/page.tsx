"use client";

import { useState } from "react";
import FileUpload from "@/components/upload/FileUpload";
import JobSummaryCard from "@/components/summary/JobSummaryCard";
import ChatWindow from "@/components/chat/ChatWindow";
import LineageGraph from "@/components/lineage/LineageGraph";
import { clearSession } from "@/lib/api";
import type { JobInfo } from "@/types";

type Tab = "chat" | "lineage";

export default function Home() {
  const [job, setJob] = useState<JobInfo | null>(null);
  const [tab, setTab] = useState<Tab>("chat");

  const reset = async () => {
    if (job) await clearSession(job.session_id).catch(() => {});
    setJob(null);
    setTab("chat");
  };

  if (!job) return <FileUpload onUploadSuccess={setJob} />;

  const TABS = [
    { id: "chat" as Tab,    label: "DIA Chat",     icon: "💬" },
    { id: "lineage" as Tab, label: "Lineage Graph", icon: "🔗" },
  ];

  return (
    <div style={{
      display: "flex", height: "100vh", overflow: "hidden",
      fontFamily: "'Inter', system-ui, sans-serif",
      background: "#f1f5f9",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 99px; }
      `}</style>

      {/* ── Sidebar Column ── */}
      <aside style={{
        width: 272, flexShrink: 0, display: "flex", flexDirection: "column",
        background: "#0f1117", borderRight: "1px solid #1e2130", overflow: "hidden",
      }}>
        {/* Workspace Brand Identifier */}
        <div style={{ padding: "20px 20px 16px", borderBottom: "1px solid #1e2130", flexShrink: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 10, flexShrink: 0,
              background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 12, fontWeight: 700, color: "#fff", letterSpacing: "-0.02em",
            }}>DS</div>
            <div>
              <p style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 600 }}>DataStage DIA</p>
              <p style={{ color: "#3d4466", fontSize: 11, marginTop: 1 }}>Intelligence Assistant</p>
            </div>
          </div>
        </div>

        {/* Modular Metrics Context Target */}
        <div style={{ flex: 1, overflowY: "auto" }}>
          <JobSummaryCard job={job} />
        </div>

        {/* Clear Workspace CTA Anchor */}
        <div style={{ padding: "12px 16px", borderTop: "1px solid #1e2130", flexShrink: 0 }}>
          <button onClick={reset} style={{
            width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
            background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 12, padding: "10px", color: "#94a3b8",
            fontSize: 13, fontWeight: 500, cursor: "pointer", transition: "all 0.15s",
          }}
            onMouseEnter={e => { 
              const btn = e.currentTarget;
              btn.style.background = "rgba(255,255,255,0.1)"; 
              btn.style.color = "#e2e8f0"; 
            }}
            onMouseLeave={e => { 
              const btn = e.currentTarget;
              btn.style.background = "rgba(255,255,255,0.05)"; 
              btn.style.color = "#94a3b8"; 
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
            </svg>
            Upload new file
          </button>
        </div>
      </aside>

      {/* ── Main Panel Control Area ── */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

        {/* View Switch Tab Bar */}
        <div style={{
          background: "#ffffff", borderBottom: "1px solid #e2e8f0",
          padding: "0 24px", display: "flex", alignItems: "flex-end",
          gap: 4, flexShrink: 0,
        }}>
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} style={{
              display: "flex", alignItems: "center", gap: 7,
              padding: "14px 18px 12px",
              border: "none",
              background: "none",
              borderBottomStyle: "solid",
              borderBottomWidth: 2.5,
              borderBottomColor: tab === t.id ? "#6366f1" : "transparent",
              color: tab === t.id ? "#4f46e5" : "#94a3b8",
              fontSize: 13, fontWeight: 600, cursor: "pointer",
              transition: "color 0.15s",
            }}>
              <span style={{ fontSize: 15 }}>{t.icon}</span>
              {t.label}
            </button>
          ))}

          {/* Active Job Marker Pill */}
          <div style={{ marginLeft: "auto", alignSelf: "center", display: "flex", alignItems: "center", gap: 7,
            background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 99,
            padding: "5px 14px",
          }}>
            <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#10b981", flexShrink: 0, boxShadow: "0 0 5px #10b981" }} />
            <span style={{ fontSize: 12, color: "#64748b", fontWeight: 500, maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {job.job_name}
            </span>
          </div>
        </div>

        {/* Dynamic View Container Content */}
        <div style={{ flex: 1, overflow: "hidden" }}>
          {tab === "chat" && <ChatWindow job={job} />}
          {tab === "lineage" && (
            <div style={{ height: "100%", display: "flex", flexDirection: "column", padding: "24px", gap: 16, overflowY: "auto" }}>
              <div>
                <h2 style={{ fontSize: 16, fontWeight: 700, color: "#1e293b", marginBottom: 4 }}>Data lineage graph</h2>
                <p style={{ fontSize: 13, color: "#94a3b8" }}>Drag to pan · scroll to zoom · colours indicate stage role.</p>
              </div>
              <div style={{ flex: 1, minHeight: 480 }}>
                <LineageGraph lineage={job.lineage} />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
