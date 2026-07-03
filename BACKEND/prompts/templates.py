"""
Prompt Templates — DIA (DataStage Intelligence Assistant)
----------------------------------------------------------
Rebuilt to fix:
  1. Claude thinking it has a JSON file — now clearly told it's a DSX file
  2. Thin context in chat — full stage details, columns, params, transformations injected
  3. Intent-aware routing — SQL, params, lineage, impact get specialised prompts
  4. Raw DSX content referenced where helpful
"""

import json
from typing import Any


# ---------------------------------------------------------------------------
# Master system prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are DIA — DataStage Intelligence Assistant — an expert IBM DataStage ETL analyst with 15+ years of experience.

IMPORTANT: You are analysing a real IBM DataStage DSX job file. The user uploaded a .dsx file which has been parsed and structured for you below. This is NOT a JSON file — it is metadata extracted from a DataStage DSX export file.

Your expertise covers:
- IBM DataStage DSX/XML job definitions (DSRECORD, DSSUBRECORD, CCustomStage, CCustomInput/Output formats)
- DataStage stage types: Oracle Connector, DB2 Connector, Sequential File, Transformer, Join, Aggregator, Sort, Filter, Funnel
- DataStage transformer derivation expressions and their SQL equivalents
- Parameter sets, job parameters (String, Encrypted, Integer, Pathname, ParameterSet types)
- Data lineage tracing from source to target
- Migration to SQL, dbt, Spark, Azure Data Factory, Databricks
- Impact analysis across stage dependencies

Rules:
- Always answer based on the ACTUAL job metadata provided below — never invent stages, columns, or parameters
- When asked for SQL, write complete runnable SQL using the actual table names and column names from the job
- When asked about parameters, list ALL parameters with their exact names, types, and defaults
- When asked about columns, list them with exact names and data types from the parsed metadata
- When the user asks any question about the DSX file, answer it confidently using the provided metadata
- If something is genuinely not present in the metadata, say so clearly — do not guess
- Always refer to this as a "DataStage DSX job" not a "JSON file"
"""


# ---------------------------------------------------------------------------
# Helper — build rich readable context from metadata
# ---------------------------------------------------------------------------

def _build_full_context(metadata: dict[str, Any]) -> str:
    job     = metadata["job_info"]
    stats   = metadata["summary_stats"]
    stages  = metadata["stages"]
    params  = metadata["parameters"]
    lineage = metadata["lineage"]
    links   = metadata["links"]

    lines = []

    # ── Job header ──
    lines.append("=" * 60)
    lines.append("DATASTAGE DSX JOB FILE — PARSED METADATA")
    lines.append("=" * 60)
    lines.append(f"Job Name        : {job['name']}")
    lines.append(f"Job Type        : {job['job_type']}")
    lines.append(f"Category        : {job['category']}")
    lines.append(f"Server          : {job.get('server_name', '')} v{job.get('server_version', '')}")
    lines.append(f"Last Modified   : {job.get('date_modified', '')}")
    lines.append(f"Description     : {job['description'] or '(none)'}")
    lines.append(f"Complexity      : {stats['complexity']} — {stats['total_stages']} stages, "
                 f"{stats['total_links']} links, {stats['total_derivations']} derivations, "
                 f"{stats['total_parameters']} parameters, {stats.get('total_columns', 0)} columns")
    lines.append("")

    # ── Parameters ──
    lines.append("─" * 60)
    lines.append(f"PARAMETERS ({len(params)} total)")
    lines.append("─" * 60)
    if params:
        for p in params:
            lines.append(f"  Name    : {p['name']}")
            lines.append(f"  Type    : {p['type']}")
            lines.append(f"  Default : {p['default'] or '(none)'}")
            lines.append(f"  Prompt  : {p['prompt'] or '(none)'}")
            lines.append(f"  Help    : {p['help'] or '(none)'}")
            lines.append("")
    else:
        lines.append("  (no parameters defined)")
        lines.append("")

    # ── Lineage summary ──
    lines.append("─" * 60)
    lines.append("DATA LINEAGE")
    lines.append("─" * 60)
    lines.append(f"  Source tables : {', '.join(lineage['source_tables']) or '(none identified)'}")
    lines.append(f"  Target tables : {', '.join(lineage['target_tables']) or '(none identified)'}")
    lines.append("")
    if links:
        lines.append("  Data flow (links):")
        for lnk in links:
            lines.append(f"    {lnk['source_name']}  →  {lnk['target_name']}  (link: {lnk['name']})")
    lines.append("")

    # ── Stages (full detail) ──
    lines.append("─" * 60)
    lines.append(f"STAGES ({len(stages)} total)")
    lines.append("─" * 60)
    for s in stages:
        lines.append(f"\n  ┌─ Stage: {s['name']}")
        lines.append(f"  │  ID         : {s['id']}")
        lines.append(f"  │  Role       : {s['role'].upper()}")
        lines.append(f"  │  Type       : {s['type']}")
        if s.get('description'):
            lines.append(f"  │  Description: {s['description']}")
        if s.get('table_name'):
            lines.append(f"  │  Table      : {s['table_name']}")
        if s.get('write_mode'):
            lines.append(f"  │  Write mode : {s['write_mode']}")
        if s.get('connection'):
            lines.append(f"  │  Connection : {s['connection']}")

        # Properties
        props = {k: v for k, v in s.get('properties', {}).items() if v and k != 'XMLProperties'}
        if props:
            lines.append(f"  │  Properties :")
            for k, v in props.items():
                vstr = str(v)[:120]
                lines.append(f"  │    {k}: {vstr}")

        # Input columns
        in_cols = s.get('input_columns', [])
        if in_cols:
            lines.append(f"  │  Input columns ({len(in_cols)}):")
            for c in in_cols:
                nullable = "NULL" if c.get('nullable') else "NOT NULL"
                lines.append(f"  │    {c['name']}  {c.get('type_str') or c.get('sql_type', '')}  {nullable}")

        # Output columns
        out_cols = s.get('output_columns', [])
        if out_cols:
            lines.append(f"  │  Output columns ({len(out_cols)}):")
            for c in out_cols:
                nullable = "NULL" if c.get('nullable') else "NOT NULL"
                lines.append(f"  │    {c['name']}  {c.get('type_str') or c.get('sql_type', '')}  {nullable}")

        # Transformations
        trans = s.get('transformations', [])
        if trans:
            lines.append(f"  │  Transformations/Derivations ({len(trans)}):")
            for t in trans:
                lines.append(f"  │    {t['output_column']} = {t['derivation']}")

        # Aggregations
        agg = s.get('aggregations', {})
        if agg and agg.get('aggregations'):
            lines.append(f"  │  Aggregations:")
            lines.append(f"  │    GROUP BY: {', '.join(agg.get('group_by', []))}")
            for a in agg['aggregations']:
                cond = f" WHERE {a['condition']}" if a.get('condition') else ""
                lines.append(f"  │    {a['output_column']} = {a['function']}({a['input_column']}){cond}")

        lines.append(f"  └{'─' * 50}")

    return "\n".join(lines)





# ---------------------------------------------------------------------------
# Intent detector — routes user question to right prompt style
# ---------------------------------------------------------------------------

def detect_intent(message: str) -> str:
    msg = message.lower()
    if any(k in msg for k in ['sql', 'query', 'select', 'migrate', 'convert', 'rewrite', 'spark', 'dbt']):
        return 'sql'
    if any(k in msg for k in ['parameter', 'param', 'parameter set', 'default value']):
        return 'parameter'
    if any(k in msg for k in ['lineage', 'flow', 'source', 'target', 'trace', 'path']):
        return 'lineage'
    if any(k in msg for k in ['impact', 'change', 'affect', 'break', 'remove', 'modify', 'delete']):
        return 'impact'
    if any(k in msg for k in ['column', 'field', 'schema', 'datatype', 'data type', 'nullable']):
        return 'columns'
    if any(k in msg for k in ['stage', 'connector', 'transformer', 'join', 'aggregat', 'sort', 'filter']):
        return 'stages'
    return 'general'


# ---------------------------------------------------------------------------
# Initial summary prompt (called once on upload)
# ---------------------------------------------------------------------------

def initial_summary_prompt(metadata: dict[str, Any]) -> str:
    context = _build_full_context(metadata)

    return f"""You are DIA — DataStage Intelligence Assistant. A user has uploaded a DataStage DSX job file.
Analyse this job and give a clear, structured summary.

{context}

Provide:
1. **What this job does** — 2-3 sentences describing the business purpose in plain English
2. **Step-by-step walkthrough** — explain each stage in order (use actual stage names)
3. **Key business rules** — list transformation logic, derivations, filters, and calculations
4. **Parameters** — list all job parameters with their purpose
5. **Data flow** — source tables → stages → target tables
6. **Watch points** — potential issues, nulls, encrypted params, migration considerations

Use the actual stage names, table names, column names, and parameter names from the metadata above.
Do NOT say "based on the JSON" — say "based on the DSX job file" or just reference things directly.
"""


# ---------------------------------------------------------------------------
# Chat system prompt — injected as system on every /chat call
# ---------------------------------------------------------------------------

def chat_system_prompt(metadata: dict[str, Any]) -> str:
    context = _build_full_context(metadata)

    return f"""{SYSTEM_PROMPT}

The user has uploaded a DataStage DSX job file. Here is the complete parsed content of that file.
Use this as your ground truth for every question. Answer confidently — you have the full job definition.

{context}

ANSWERING GUIDELINES:
- For SQL questions: write complete, runnable SQL using the exact table names and column names above
- For parameter questions: list all parameters with name, type, default, and purpose
- For lineage questions: trace the exact path using the stage names and link names above
- For column questions: reference the exact column names and data types from the stage definitions
- For "what does this job do" questions: explain using the actual stage names and business context
- Never say you don't have enough information — you have the complete job definition above
- Never refer to this as a JSON file — it is a DataStage DSX job
"""


# ---------------------------------------------------------------------------
# Intent-aware user message enhancer
# Called in routes.py to prepend context hints to user message
# ---------------------------------------------------------------------------

def enhance_user_message(user_message: str, metadata: dict[str, Any]) -> str:
    intent = detect_intent(user_message)
    job    = metadata["job_info"]
    stages = metadata["stages"]
    params = metadata["parameters"]
    lineage = metadata["lineage"]

    prefix = ""

    if intent == 'sql':
        source_cols = []
        target_cols = []
        for s in stages:
            if s['role'] == 'source':
                source_cols.extend([c['name'] for c in s.get('output_columns', [])])
            if s['role'] == 'target':
                target_cols.extend([c['name'] for c in s.get('input_columns', [])])
        trans_summary = []
        for s in stages:
            for t in s.get('transformations', []):
                trans_summary.append(f"{t['output_column']} = {t['derivation']}")
        prefix = f"""[SQL GENERATION CONTEXT]
Job: {job['name']}
Source tables: {', '.join(lineage['source_tables'])}
Target tables: {', '.join(lineage['target_tables'])}
Source columns: {', '.join(source_cols[:30])}
Target columns: {', '.join(target_cols[:30])}
Transformations: {chr(10).join(trans_summary[:20])}

USER QUESTION: """

    elif intent == 'parameter':
        param_detail = "\n".join(
            f"  {p['name']} (type={p['type']}, default={p['default'] or 'none'}, prompt={p['prompt']})"
            for p in params
        )
        prefix = f"""[PARAMETER CONTEXT]
Job has {len(params)} parameters:
{param_detail}

USER QUESTION: """

    elif intent == 'lineage':
        links = metadata.get('links', [])
        flow  = " → ".join(f"{l['source_name']}" for l in links)
        if links:
            flow += f" → {links[-1]['target_name']}"
        prefix = f"""[LINEAGE CONTEXT]
Data flow: {flow}
Sources: {', '.join(lineage['source_tables'])}
Targets: {', '.join(lineage['target_tables'])}

USER QUESTION: """

    elif intent == 'columns':
        col_summary = []
        for s in stages:
            all_cols = s.get('output_columns', []) or s.get('input_columns', [])
            if all_cols:
                col_summary.append(f"Stage {s['name']}: {', '.join(c['name'] for c in all_cols[:10])}")
        prefix = f"""[COLUMN CONTEXT]
{chr(10).join(col_summary)}

USER QUESTION: """

    return prefix + user_message



# ---------------------------------------------------------------------------
# Kept for backward compatibility — used in routes.py for standalone calls
# ---------------------------------------------------------------------------

def lineage_prompt(metadata: dict[str, Any]) -> str:
    context = _build_full_context(metadata)
    lineage = metadata["lineage"]
    links   = metadata.get("links", [])

    edges_text = "\n".join(
        f"  {lnk['source_name']}  →  {lnk['target_name']}  (link: {lnk['name']})"
        for lnk in links
    )

    return f"""Explain the complete data lineage for this DataStage job.

{context}

LINK GRAPH:
{edges_text}

Provide:
1. Source-to-target lineage narrative using actual stage and table names
2. At each stage, what columns are added, removed, or transformed
3. Data quality risks (nulls, type mismatches, filter conditions)
4. Which source columns map to which target columns
"""


def migration_prompt(metadata: dict[str, Any], target_platform: str = "SQL") -> str:
    context = _build_full_context(metadata)

    return f"""Convert this DataStage job to {target_platform}.

{context}

Provide:
1. Complete {target_platform} equivalent using CTEs, with actual table/column names from above
2. Inline comments explaining each transformation's business purpose
3. DataStage-specific functions mapped to {target_platform} equivalents
4. Anything that cannot be directly translated and needs manual review
"""


def impact_prompt(metadata: dict[str, Any], change_description: str) -> str:
    context = _build_full_context(metadata)

    return f"""Perform an impact analysis for the following change in this DataStage job.

PROPOSED CHANGE:
{change_description}

{context}

Provide:
1. Which stages are directly affected (use actual stage names)
2. Which downstream stages/columns are impacted
3. Whether the target table schema is affected
4. Risk level (Low / Medium / High) with justification
5. Recommended steps to safely implement this change
"""