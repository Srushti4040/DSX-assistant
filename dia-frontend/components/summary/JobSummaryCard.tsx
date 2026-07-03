"use client";

import type { JobInfo } from "@/types";

interface Props {
  job: JobInfo;
}

const COMPLEXITY: Record<string, { color: string; bg: string; border: string }> = {
  Low:    { color: "#34d399", bg: "rgba(52,211,153,0.1)",  border: "rgba(52,211,153,0.2)"  },
  Medium: { color: "#fbbf24", bg: "rgba(251,191,36,0.1)",  border: "rgba(251,191,36,0.2)"  },
  High:   { color: "#f87171", bg: "rgba(248,113,113,0.1)", border: "rgba(248,113,113,0.2)" },
};

const ROLE: Record<string, { color: string; bg: string; icon: string }> = {
  source:      { color: "#60a5fa", bg: "rgba(96,165,250,0.12)",  icon: "↗" },
  target:      { color: "#a78bfa", bg: "rgba(167,139,250,0.12)", icon: "↙" },
  transformer: { color: "#fb923c", bg: "rgba(251,146,60,0.12)",  icon: "⚙" },
  join:        { color: "#2dd4bf", bg: "rgba(45,212,191,0.12)",  icon: "⋈" },
  aggregator:  { color: "#f472b6", bg: "rgba(244,114,182,0.12)", icon: "Σ" },
  sort:        { color: "#94a3b8", bg: "rgba(148,163,184,0.12)", icon: "↕" },
  filter:      { color: "#facc15", bg: "rgba(250,204,21,0.12)",  icon: "▽" },
};

function Label({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "#3d4466", marginBottom: 10, padding: "0 20px" }}>
      {children}
    </p>
  );
}

function Divider() {
  return <div style={{ height: 1, background: "#1e2130", margin: "16px 0" }} />;
}

export default function JobSummaryCard({ job }: Props) {
  const { summary_stats: s, lineage, parameters } = job;
  const cx = COMPLEXITY[s.complexity] ?? COMPLEXITY.Medium;

  return (
    <div style={{ paddingBottom: 24 }}>

      {/* Job Name & Complexity Tag */}
      <div style={{ padding: "18px 20px 0" }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8, marginBottom: 8 }}>
          <h2 style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 600, lineHeight: 1.4 }}>{job.job_name}</h2>
          <span style={{
            flexShrink: 0, fontSize: 10, fontWeight: 700, padding: "3px 9px",
            borderRadius: 99, border: `1px solid ${cx.border}`,
            background: cx.bg, color: cx.color,
          }}>{s.complexity}</span>
        </div>
        {job.job_description && (
          <p style={{ color: "#3d4466", fontSize: 11, lineHeight: 1.6, display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
            {job.job_description}
          </p>
        )}
      </div>

      <Divider />

      {/* Stats Cards Grid */}
      <Label>Overview</Label>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, padding: "0 20px" }}>
        {[
          { v: s.total_stages,      l: "Stages" },
          { v: s.total_links,       l: "Links" },
          { v: s.total_derivations, l: "Derivations" },
          { v: s.total_parameters,  l: "Parameters" },
        ].map(x => (
          <div key={x.l} style={{
            background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: 12, padding: "12px 14px",
          }}>
            <p style={{ color: "#e2e8f0", fontSize: 22, fontWeight: 700, lineHeight: 1, marginBottom: 4 }}>{x.v}</p>
            <p style={{ color: "#3d4466", fontSize: 11 }}>{x.l}</p>
          </div>
        ))}
      </div>

      <Divider />

      {/* Stage Breakdown Pills */}
      <Label>Stage breakdown</Label>
      <div style={{ padding: "0 20px", display: "flex", flexWrap: "wrap", gap: 6 }}>
        {Object.entries(s.stage_role_counts).map(([role, count]) => {
          const r = ROLE[role] ?? { color: "#94a3b8", bg: "rgba(148,163,184,0.1)", icon: "·" };
          return (
            <span key={role} style={{
              display: "inline-flex", alignItems: "center", gap: 5,
              fontSize: 11, fontWeight: 600, padding: "4px 10px",
              borderRadius: 99, background: r.bg, color: r.color,
              border: `1px solid ${r.color}22`,
            }}>
              <span style={{ fontSize: 10 }}>{r.icon}</span>
              {count} {role}
            </span>
          );
        })}
      </div>

      <Divider />

      {/* Source & Target Tables Lineage Stack */}
      <Label>Lineage</Label>
      <div style={{ padding: "0 20px", display: "flex", flexDirection: "column", gap: 6 }}>
        {lineage.source_tables.map(t => (
          <div key={t} style={{
            display: "flex", alignItems: "center", gap: 10,
            background: "rgba(96,165,250,0.06)", border: "1px solid rgba(96,165,250,0.15)",
            borderRadius: 10, padding: "8px 12px",
          }}>
            <span style={{ color: "#60a5fa", fontSize: 10, fontWeight: 800, flexShrink: 0 }}>SRC</span>
            <span style={{ color: "#94a3b8", fontSize: 11, fontFamily: "monospace", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {t.replace(/#/g, "")}
            </span>
          </div>
        ))}
        
        <div style={{ textAlign: "center", color: "#3d4466", fontSize: 12, padding: "2px 0" }}>↓</div>
        
        {lineage.target_tables.map(t => (
          <div key={t} style={{
            display: "flex", alignItems: "center", gap: 10,
            background: "rgba(167,139,250,0.06)", border: "1px solid rgba(167,139,250,0.15)",
            borderRadius: 10, padding: "8px 12px",
          }}>
            <span style={{ color: "#a78bfa", fontSize: 10, fontWeight: 800, flexShrink: 0 }}>TGT</span>
            <span style={{ color: "#94a3b8", fontSize: 11, fontFamily: "monospace", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {t.replace(/#/g, "")}
            </span>
          </div>
        ))}
      </div>

      {/* Runtime Parameters Context */}
      {parameters.length > 0 && (
        <>
          <Divider />
          <Label>Parameters</Label>
          <div style={{ padding: "0 20px", display: "flex", flexDirection: "column", gap: 8 }}>
            {parameters.map(p => (
              <div key={p.name} style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8 }}>
                <span style={{ color: "#94a3b8", fontSize: 11, fontFamily: "monospace", flexShrink: 0 }}>{p.name}</span>
                <span style={{ color: "#3d4466", fontSize: 11, textAlign: "right", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.default}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
