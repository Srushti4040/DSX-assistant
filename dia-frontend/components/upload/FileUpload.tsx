"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { uploadDSX } from "@/lib/api";
import type { JobInfo } from "@/types";

interface FileUploadProps {
  onUploadSuccess: (job: JobInfo) => void;
}

const FEATURES = [
  { icon: "⚡", label: "Job summary",    desc: "Plain-English walkthrough of every stage" },
  { icon: "🔗", label: "Lineage tracing",  desc: "Source-to-target data flow, visualised" },
  { icon: "💬", label: "Intelligent chat", desc: "Ask anything about your pipeline" },
  { icon: "🔄", label: "SQL migration",    desc: "Convert transformer logic to modern SQL" },
];

export default function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState("Parsing DSX structure…");
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(async (accepted: File[]) => {
    const file = accepted[0];
    if (!file) return;
    setError(null);
    setUploading(true);
    setProgress("Parsing DSX structure…");
    
    const t = setTimeout(() => setProgress("Analysing job structure…"), 3500);
    
    try {
      const data = await uploadDSX(file);
      onUploadSuccess(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed. Please try again.");
    } finally {
      clearTimeout(t);
      setUploading(false);
    }
  }, [onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/octet-stream": [".dsx"], "text/xml": [".xml"] },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div style={{
      height: "100vh",
      background: "linear-gradient(135deg, #0d1117 0%, #161b2e 50%, #0d1117 100%)",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "1.25rem 1.5rem",
      fontFamily: "'Inter', system-ui, sans-serif",
      position: "relative",
      overflow: "hidden",
      boxSizing: "border-box",
    }}>

      {/* Ambient glow blobs */}
      <div style={{ position: "absolute", top: "5%", left: "10%", width: 320, height: 320, borderRadius: "50%", background: "radial-gradient(circle, rgba(99,102,241,0.1) 0%, transparent 70%)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", bottom: "5%", right: "8%", width: 280, height: 280, borderRadius: "50%", background: "radial-gradient(circle, rgba(139,92,246,0.08) 0%, transparent 70%)", pointerEvents: "none" }} />

      <div style={{ position: "relative", width: "100%", maxWidth: 980, zIndex: 1, display: "flex", flexDirection: "column", gap: "1rem" }}>

        {/* Hero heading */}
        <div style={{ textAlign: "center" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 10, marginBottom: "0.5rem" }}>
            <div style={{
              width: 34, height: 34, borderRadius: 10,
              background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 11, fontWeight: 800, color: "#fff", letterSpacing: "0.02em", flexShrink: 0,
            }}>DIA</div>
            <h1 style={{
              fontSize: "1.75rem", fontWeight: 700, lineHeight: 1,
              color: "#ffffff", letterSpacing: "-0.03em", margin: 0,
            }}>
              DataStage{" "}
              <span style={{ background: "linear-gradient(135deg, #818cf8, #c084fc)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                Intelligence
              </span>
              {" "}Assistant
            </h1>
          </div>
          <p style={{ color: "#64748b", fontSize: "0.82rem", margin: 0 }}>
            Upload a DSX file for instant intelligent analysis — summaries, lineage, business rules &amp; SQL migration
          </p>
        </div>

        {/* Main card */}
        <div style={{
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.1)",
          borderRadius: 20, padding: "1.5rem",
          backdropFilter: "blur(20px)",
          boxShadow: "0 20px 50px rgba(0,0,0,0.4)",
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "1.5rem",
          alignItems: "stretch",
        }}>

          {/* Drop zone */}
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div
              {...getRootProps()}
              style={{
                border: isDragActive ? "2px dashed #818cf8" : "2px dashed rgba(255,255,255,0.15)",
                borderRadius: 14,
                padding: "1.75rem 1.5rem",
                display: "flex", flexDirection: "column", alignItems: "center",
                justifyContent: "center", gap: "0.75rem", textAlign: "center",
                cursor: uploading ? "default" : "pointer",
                background: isDragActive ? "rgba(99,102,241,0.08)" : "rgba(255,255,255,0.02)",
                transition: "all 0.2s ease",
                flex: 1,
                minHeight: 0,
              }}
            >
              <input {...getInputProps()} />

              {uploading ? (
                <>
                  <div style={{ position: "relative", width: 52, height: 52, flexShrink: 0 }}>
                    <div style={{
                      position: "absolute", inset: 0, borderRadius: "50%",
                      border: "2px solid transparent",
                      borderTopColor: "#818cf8", borderRightColor: "#c084fc",
                      animation: "spin 0.9s linear infinite",
                    }} />
                    <div style={{ position: "absolute", inset: 7, borderRadius: "50%", background: "rgba(99,102,241,0.12)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 800, color: "#818cf8" }}>DIA</div>
                  </div>
                  <div>
                    <p style={{ color: "#e2e8f0", fontWeight: 600, fontSize: "0.95rem", marginBottom: 2 }}>{progress}</p>
                    <p style={{ color: "#64748b", fontSize: "0.78rem" }}>Usually 10–20 seconds</p>
                  </div>
                  <div style={{ display: "flex", gap: 5 }}>
                    {[0, 1, 2].map(i => (
                      <span key={i} style={{ width: 6, height: 6, borderRadius: "50%", background: "#818cf8", animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`, display: "inline-block" }} />
                    ))}
                  </div>
                </>
              ) : (
                <>
                  <div style={{ fontSize: 38, lineHeight: 1, filter: "drop-shadow(0 3px 8px rgba(99,102,241,0.3))", transition: "transform 0.2s", transform: isDragActive ? "scale(1.15) translateY(-3px)" : "translateY(0)" }}>
                    {isDragActive ? "📂" : "📁"}
                  </div>
                  <div>
                    <p style={{ color: "#f1f5f9", fontWeight: 600, fontSize: "1rem", marginBottom: 4 }}>
                      {isDragActive ? "Drop to analyse" : "Drop your DSX file here"}
                    </p>
                    <p style={{ color: "#64748b", fontSize: "0.8rem" }}>or click to browse your files</p>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    {[".dsx", ".xml"].map(ext => (
                      <span key={ext} style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 5, padding: "2px 8px", color: "#94a3b8", fontSize: 11, fontFamily: "monospace" }}>{ext}</span>
                    ))}
                    <span style={{ color: "#475569", fontSize: 11 }}>· max 10 MB</span>
                  </div>
                  <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "0.6rem", width: "100%", textAlign: "center" }}>
                    <span style={{ color: "#475569", fontSize: 11 }}>No file? Use </span>
                    <code style={{ color: "#a5b4fc", fontSize: 10, background: "rgba(99,102,241,0.1)", padding: "2px 7px", borderRadius: 4, fontFamily: "monospace" }}>samples/customer_orders_agg.dsx</code>
                  </div>
                </>
              )}
            </div>

            {error && (
              <div style={{ display: "flex", gap: 8, alignItems: "flex-start", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", borderRadius: 10, padding: "10px 14px" }}>
                <span style={{ color: "#f87171", fontSize: 13 }}>⚠</span>
                <p style={{ color: "#fca5a5", fontSize: 12, lineHeight: 1.4 }}>{error}</p>
              </div>
            )}
          </div>

          {/* Features Column */}
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <p style={{ color: "#475569", fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: 2 }}>What you get</p>
            {FEATURES.map((f) => (
              <div key={f.label} style={{
                display: "flex", alignItems: "center", gap: 12,
                background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: 12, padding: "10px 14px",
                flex: 1,
              }}>
                <span style={{ fontSize: 18, lineHeight: 1, flexShrink: 0 }}>{f.icon}</span>
                <div>
                  <p style={{ color: "#f1f5f9", fontSize: 12, fontWeight: 600, marginBottom: 1 }}>{f.label}</p>
                  <p style={{ color: "#64748b", fontSize: 11, lineHeight: 1.4 }}>{f.desc}</p>
                </div>
              </div>
            ))}
          </div>

        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes bounce { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-5px)} }
        * { box-sizing: border-box; }
      `}</style>
    </div>
  );
}
