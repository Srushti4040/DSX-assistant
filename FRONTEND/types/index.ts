export interface JobInfo {
  session_id: string;
  job_name: string;
  job_description: string;
  summary_stats: SummaryStats;
  lineage: Lineage;
  parameters: Parameter[];
  initial_summary: string;
}

export interface SummaryStats {
  total_stages: number;
  total_links: number;
  total_parameters: number;
  stage_role_counts: Record<string, number>;
  total_derivations: number;
  complexity: "Low" | "Medium" | "High";
}

export interface Lineage {
  nodes: LineageNode[];
  edges: LineageEdge[];
  source_tables: string[];
  target_tables: string[];
}

export interface LineageNode {
  id: string;
  type: string;
  role: string;
  label: string;
  x?: number;
  y?: number;
}

export interface LineageEdge {
  from: string;
  to: string;
  label: string;
}

export interface Parameter {
  name: string;
  prompt: string;
  default: string;
  type: string;
  length: string;
  help: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string;
  session_id: string;
  history: ChatMessage[];
}
