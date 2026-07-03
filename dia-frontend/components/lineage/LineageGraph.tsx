"use client";

import { useMemo } from "react";
import ReactFlow, { Background, Controls, MiniMap, type Node, type Edge } from "reactflow";
import "reactflow/dist/style.css";
import type { Lineage } from "@/types";

const ROLE_STYLE: Record<string, { bg: string; border: string; label: string; accent: string }> = {
  source:      { bg: "#eff6ff", border: "#3b82f6", label: "SOURCE",    accent: "#1d4ed8" },
  target:      { bg: "#f5f3ff", border: "#8b5cf6", label: "TARGET",    accent: "#5b21b6" },
  transformer: { bg: "#fff7ed", border: "#f97316", label: "TRANSFORM", accent: "#c2410c" },
  join:        { bg: "#f0fdfa", border: "#14b8a6", label: "JOIN",      accent: "#0f766e" },
  aggregator:  { bg: "#fdf4ff", border: "#d946ef", label: "AGGREGATE", accent: "#86198f" },
  sort:        { bg: "#f8fafc", border: "#94a3b8", label: "SORT",      accent: "#475569" },
  filter:      { bg: "#fefce8", border: "#eab308", label: "FILTER",    accent: "#854d0e" },
  other:       { bg: "#f8fafc", border: "#cbd5e1", label: "STAGE",     accent: "#64748b" },
};

function autoLayout(nodes: Lineage["nodes"], edges: Lineage["edges"]) {
  const out: Record<string, string[]> = {};
  const inc: Record<string, number> = {};
  
  nodes.forEach((n) => {
    out[n.id] = [];
    inc[n.id] = 0;
  });
  
  edges.forEach((e) => {
    out[e.from]?.push(e.to);
    if (e.to in inc) inc[e.to]++;
  });
  
  const lvl: Record<string, number> = {};
  const q = nodes.filter((n) => inc[n.id] === 0).map((n) => n.id);
  
  q.forEach((id) => {
    lvl[id] = 0;
  });
  
  while (q.length) {
    const cur = q.shift()!;
    for (const nxt of out[cur] ?? []) {
      lvl[nxt] = Math.max(lvl[nxt] ?? 0, (lvl[cur] ?? 0) + 1);
      inc[nxt]--;
      if (inc[nxt] === 0) q.push(nxt);
    }
  }
  
  const colCnt: Record<number, number> = {};
  return nodes.map((n) => {
    const col = lvl[n.id] ?? 0;
    const row = colCnt[col] ?? 0;
    colCnt[col] = row + 1;
    return { ...n, x: col * 250 + 40, y: row * 130 + 40 };
  });
}

export default function LineageGraph({ lineage }: { lineage: Lineage }) {
  const rfNodes: Node[] = useMemo(() => {
    return autoLayout(lineage.nodes, lineage.edges).map((n) => {
      const s = ROLE_STYLE[n.role] ?? ROLE_STYLE.other;
      return {
        id: n.id,
        position: { x: n.x, y: n.y },
        data: {
          label: (
            <div style={{ textAlign: "center", fontFamily: "'Inter',system-ui,sans-serif" }}>
              <div style={{ fontSize: 9, fontWeight: 800, letterSpacing: "0.1em", color: s.accent, opacity: 0.7, marginBottom: 3, textTransform: "uppercase" as const }}>
                {s.label}
              </div>
              <div style={{ fontSize: 12, fontWeight: 700, color: s.accent }}>
                {n.id}
              </div>
            </div>
          ),
        },
        style: {
          background: s.bg,
          border: `2px solid ${s.border}`,
          borderRadius: 14,
          padding: "10px 18px",
          minWidth: 180,
          boxShadow: `0 2px 8px ${s.border}22`,
        },
      };
    });
  }, [lineage]);

  const rfEdges: Edge[] = useMemo(() =>
    lineage.edges.map((e, i) => ({
      id: `e-${i}`,
      source: e.from,
      target: e.to,
      animated: true,
      style: { stroke: "#6366f1", strokeWidth: 2 },
      markerEnd: { type: "arrowclosed" as const, color: "#6366f1", width: 18, height: 18 },
    })),
  [lineage]);

  if (!lineage.nodes.length) {
    return (
      <div style={{ height: 200, display: "flex", alignItems: "center", justifyContent: "center", background: "#fff", borderRadius: 16, border: "1px solid #e2e8f0", color: "#94a3b8", fontSize: 14 }}>
        No lineage data available
      </div>
    );
  }

  const maxY = Math.max(...rfNodes.map((n) => n.position.y)) + 180;

  return (
    <div style={{ height: Math.max(maxY, 420), width: "100%", borderRadius: 16, overflow: "hidden", border: "1px solid #e2e8f0", background: "#fff", boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
      <ReactFlow nodes={rfNodes} edges={rfEdges} fitView fitViewOptions={{ padding: 0.25 }} proOptions={{ hideAttribution: true }}>
        <Background color="#e2e8f0" gap={24} size={1} />
        <Controls />
        <MiniMap nodeStrokeWidth={2} />
      </ReactFlow>
    </div>
  );
}
