
import re
from typing import Any


# ---------------------------------------------------------------------------
# Low-level tokeniser
# ---------------------------------------------------------------------------

MULTI_LINE_START = re.compile(r'^(\s*)(\w+)\s+=\+=\+=\s*$')
MULTI_LINE_END   = re.compile(r'^=\+=\+=\s*$')
KV_QUOTED        = re.compile(r'^(\s*)(\w+)\s+"(.*)"$')
KV_BARE          = re.compile(r'^(\s*)(\w+)\s*$')
BEGIN_BLOCK      = re.compile(r'^(\s*)BEGIN\s+(\w+)\s*$')
END_BLOCK        = re.compile(r'^(\s*)END\s+(\w+)\s*$')


def _clean(line: str) -> str:
    return line.rstrip('\r\n')


def _tokenise(text: str) -> list[dict]:
    """
    Convert raw DSX text into a flat list of token dicts:
      {type: 'begin'|'end'|'kv'|'multiline', name, value, indent}
    """
    tokens = []
    lines  = text.split('\n')
    i = 0
    while i < len(lines):
        line = _clean(lines[i])

        # Multi-line value block start
        m = MULTI_LINE_START.match(line)
        if m:
            key = m.group(2)
            i += 1
            parts = []
            while i < len(lines):
                l2 = _clean(lines[i])
                if MULTI_LINE_END.match(l2):
                    i += 1
                    break
                parts.append(l2)
                i += 1
            tokens.append({'type': 'kv', 'name': key, 'value': '\n'.join(parts)})
            continue

        # BEGIN block
        m = BEGIN_BLOCK.match(line)
        if m:
            tokens.append({'type': 'begin', 'name': m.group(2)})
            i += 1
            continue

        # END block
        m = END_BLOCK.match(line)
        if m:
            tokens.append({'type': 'end', 'name': m.group(2)})
            i += 1
            continue

        # Key "Value"
        m = KV_QUOTED.match(line)
        if m:
            tokens.append({'type': 'kv', 'name': m.group(2), 'value': m.group(3)})
            i += 1
            continue

        # Bare keyword (flag / no value)
        m = KV_BARE.match(line)
        if m and m.group(2) not in ('', ):
            tokens.append({'type': 'kv', 'name': m.group(2), 'value': True})
            i += 1
            continue

        i += 1

    return tokens


def _build_tree(tokens: list[dict]) -> list[dict]:
    """
    Turn the flat token list into a tree of nested dicts.
    Returns a list of top-level blocks.
    """
    stack: list[dict] = [{'_type': 'ROOT', '_children': [], '_kv': {}}]

    for tok in tokens:
        if tok['type'] == 'begin':
            node = {'_type': tok['name'], '_children': [], '_kv': {}}
            stack[-1]['_children'].append(node)
            stack.append(node)

        elif tok['type'] == 'end':
            if len(stack) > 1:
                stack.pop()

        elif tok['type'] == 'kv':
            key = tok['name']
            val = tok['value']
            cur = stack[-1]['_kv']
            if key in cur:
                # turn into list on collision
                if not isinstance(cur[key], list):
                    cur[key] = [cur[key]]
                cur[key].append(val)
            else:
                cur[key] = val

    return stack[0]['_children']


# ---------------------------------------------------------------------------
# XML property extractor (for XMLProperties / embedded XML blobs)
# ---------------------------------------------------------------------------

def _extract_from_xml(xml_blob: str) -> dict:
    """
    Extract metadata from XMLProperties blobs embedded in DSX files.
    These blobs are often malformed XML (unclosed tags), so we use
    targeted regex patterns instead of a full XML parser.
    """
    result: dict[str, Any] = {}

    # TableName — appears as:
    #   <TableName type='string'><![CDATA[schema.TABLE_NAME]]>
    # or inside WriteStrategyTableName
    for pattern in [
        r'<TableName[^>]*>(?:<!\[CDATA\[)?([^<\]\n\[]+)',
        r'<WriteStrategyTableName[^>]*>(?:<!\[CDATA\[)?([^<\]\n\[]+)',
    ]:
        m = re.search(pattern, xml_blob)
        if m:
            val = m.group(1).strip().rstrip('\\').strip()
            if val and len(val) > 2:
                result['table_name'] = val
                break

    # WriteMode — <WriteMode type='int'><![CDATA[N]]>
    m = re.search(r'<WriteMode[^>]*>(?:<!\[CDATA\[)?(\d+)', xml_blob)
    if m:
        wm_map = {'0': 'insert', '1': 'update', '2': 'upsert',
                  '3': 'delete', '4': 'truncate_insert', '8': 'custom_sql'}
        result['write_mode'] = wm_map.get(m.group(1), m.group(1))

    # Context — <Context type='int'><![CDATA[1|2]]>
    m = re.search(r'<Context[^>]*>(?:<!\[CDATA\[)?(\d+)', xml_blob)
    if m:
        result['context'] = 'source' if m.group(1) == '1' else 'target'

    # Server connection string
    m = re.search(r'<Server[^>]*>(?:<!\[CDATA\[)?([^<\]\n]+)', xml_blob)
    if m:
        result['connection'] = m.group(1).strip()

    # AfterSQL — pushed-down SQL from Balanced Optimization
    m = re.search(r'<AfterSQL[^>]*>(?:<!\[CDATA\[)?([\s\S]+?)(?:]]>|</AfterSQL)', xml_blob)
    if m:
        result['pushed_sql'] = m.group(1).strip()[:3000]

    return result


# ---------------------------------------------------------------------------
# DSX Parser Class
# ---------------------------------------------------------------------------

class DSXParser:
    def __init__(self, text: str):
        self.text = text
        self.tokens = _tokenise(text)
        tree = _build_tree(self.tokens)
        
        # Flatten the root children into a accessible records map
        self._records = {'ROOT': {'_type': 'ROOT', '_children': tree, '_kv': {}}}
        for node in tree:
            # Safely use identifier fields or type names as unique keys
            ident = node['_kv'].get('Identifier', node['_kv'].get('Name', node['_type']))
            self._records[ident] = node
            
        self._job_meta = self._records['ROOT']['_kv']

    # Placeholder helper methods to ensure the code executes cleanly
    def _extract_pin_columns(self, pin_id: str) -> list:
        return []

    def _extract_transformations(self, rec: dict) -> list:
        return []

    def _classify_role(self, stage_type: str, kv: dict, xml_info: dict, input_pins: list, output_pins: list) -> str:
        return xml_info.get('context', 'transformer')

    def parse(self) -> dict:
        job_info = self._extract_job_info("DSJob_Default")
        params = self._extract_parameters()
        stages = self._extract_stages()
        links = self._extract_links(stages)
        lineage = self._build_lineage(stages, links)
        stats = self._build_stats(stages, links, params)
        
        return {
            'job_info': job_info,
            'parameters': params,
            'stages': stages,
            'links': links,
            'lineage': lineage,
            'summary_stats': stats
        }

    # ------------------------------------------------------------------
    # Job info
    # ------------------------------------------------------------------

    def _extract_job_info(self, job_ident: str) -> dict:
        root_rec = self._records.get('ROOT', {})
        kv = root_rec.get('_kv', {})

        # Header info
        header_kv: dict = {}
        tokens = _tokenise(self.text)
        in_header = False
        for tok in tokens:
            if tok['type'] == 'begin' and tok['name'] == 'HEADER':
                in_header = True
            elif tok['type'] == 'end' and tok['name'] == 'HEADER':
                in_header = False
            elif in_header and tok['type'] == 'kv':
                header_kv[tok['name']] = tok['value']

        # Job type: 1=server, 3=parallel, 2=mainframe
        job_type_map = {'1': 'Server', '2': 'Mainframe', '3': 'Parallel'}
        raw_type = kv.get('JobType', '3')
        job_type = job_type_map.get(str(raw_type), f'Type {raw_type}')

        return {
            'name':           job_ident,
            'description':    kv.get('FullDescription', ''),
            'job_type':       job_type,
            'category':       kv.get('Category', '').replace('\\\\', '/').replace('\\', '/'),
            'date_modified':  self._job_meta.get('DateModified', ''),
            'server_version': header_kv.get('ServerVersion', ''),
            'server_name':    header_kv.get('ServerName', ''),
            'tool_version':   header_kv.get('ToolVersion', ''),
            'export_date':    header_kv.get('Date', ''),
        }

    # ------------------------------------------------------------------
    # Parameters
    # ------------------------------------------------------------------

    def _extract_parameters(self) -> list[dict]:
        root_rec = self._records.get('ROOT', {})
        params   = []

        param_type_map = {
            '0': 'String', '1': 'Encrypted', '2': 'Integer', '3': 'Float',
            '4': 'Pathname', '5': 'List', '6': 'Date', '7': 'Time',
            '8': 'Timestamp', '9': 'Boolean', '13': 'ParameterSet',
        }

        for sub in root_rec.get('_children', []):
            if sub['_type'] != 'DSSUBRECORD':
                continue
            skv = sub['_kv']
            if 'Name' not in skv:
                continue
            # Only include proper parameters (have Prompt or ParamType)
            if 'Prompt' not in skv and 'ParamType' not in skv:
                continue

            raw_type = str(skv.get('ParamType', '0'))
            params.append({
                'name':    skv.get('Name', ''),
                'prompt':  skv.get('Prompt', ''),
                'default': skv.get('Default', ''),
                'type':    param_type_map.get(raw_type, f'Type{raw_type}'),
                'help':    skv.get('HelpTxt', ''),
            })

        return params

    # ------------------------------------------------------------------
    # Stages
    # ------------------------------------------------------------------

    def _extract_stages(self) -> list[dict]:
        stages = []

        for ident, rec in self._records.items():
            kv      = rec.get('_kv', {})
            ole     = kv.get('OLEType', '')

            # Only process actual stage records
            if ole not in ('CCustomStage', 'CTransformerStage',
                           'CHashFileStage', 'CSeqFileStage',
                           'CSortStage', 'CFilterStage', 'CFunnelStage'):
                # Also catch stages where OLEType is not set but StageType is
                if 'StageType' not in kv:
                    continue

            name       = kv.get('Name', ident)
            stage_type = kv.get('StageType', ole)

            # Properties from DSSUBRECORD children
            props = {}
            for sub in rec.get('_children', []):
                if sub['_type'] == 'DSSUBRECORD':
                    skv = sub['_kv']
                    pname = skv.get('Name', '')
                    pval  = skv.get('Value', '')
                    if pname:
                        props[pname] = pval

            # Extract table info from XMLProperties
            xml_info: dict = {}
            xml_blob = props.get('XMLProperties', '')
            if xml_blob:
                xml_info = _extract_from_xml(xml_blob)

            # Find input/output pin identifiers
            input_pins  = [p.strip() for p in kv.get('InputPins', '').split('|') if p.strip()]
            output_pins = [p.strip() for p in kv.get('OutputPins', '').split('|') if p.strip()]

            # Collect columns from all pins
            input_cols  = []
            output_cols = []
            for pin_id in input_pins:
                input_cols.extend(self._extract_pin_columns(pin_id))
            for pin_id in output_pins:
                output_cols.extend(self._extract_pin_columns(pin_id))

            # Transformations (for transformer stages)
            transformations = self._extract_transformations(rec)

            # Determine role
            role = self._classify_role(stage_type, kv, xml_info, input_pins, output_pins)

            # Table name resolution
            table_name = (
                xml_info.get('table_name') or
                props.get('TableName') or
                props.get('tableName') or
                ''
            )
            
            stages.append({
                'id': ident,
                'name': name,
                'type': stage_type,
                'role': role,
                'table_name': table_name,
                'input_pins': input_pins,
                'output_pins': output_pins,
                'input_columns': input_cols,
                'output_columns': output_cols,
                'transformations': transformations
            })
            
        return stages

    def _extract_links(self, stages: list[dict]) -> list[dict]:
        links = []
        seen  = set()

        # Build stage-id → stage-name lookup
        id_to_name = {s['id']: s['name'] for s in stages}

        for ident, rec in self._records.items():
            kv  = rec.get('_kv', {})
            ole = kv.get('OLEType', '')

            # Only process pin records
            if ole not in ('CCustomOutput', 'CCustomInput'):
                continue

            partner_raw = kv.get('Partner', '')
            if not partner_raw:
                continue

            # Partner format: "StageID|PinID"
            parts = partner_raw.split('|')
            if len(parts) < 1:
                continue
            partner_stage_id = parts[0].strip()

            # Find which stage owns this pin
            my_stage_id = None
            for s in stages:
                if ident in s['input_pins'] or ident in s['output_pins']:
                    my_stage_id = s['id']
                    break

            if not my_stage_id or not partner_stage_id:
                continue

            link_name = kv.get('Name', ident)

            if ole == 'CCustomOutput':
                # This pin OUTPUTS from my_stage to partner_stage
                key = (my_stage_id, partner_stage_id)
                if key not in seen:
                    seen.add(key)
                    links.append({
                        'id':           f'LNK_{ident}',
                        'name':         link_name,
                        'source_stage': my_stage_id,
                        'source_name':  id_to_name.get(my_stage_id, my_stage_id),
                        'target_stage': partner_stage_id,
                        'target_name':  id_to_name.get(partner_stage_id, partner_stage_id),
                        'source_pin':   ident,
                        'target_pin':   parts[1] if len(parts) > 1 else '',
                    })

        return links

    # ------------------------------------------------------------------
    # Lineage
    # ------------------------------------------------------------------

    def _build_lineage(self, stages: list[dict], links: list[dict]) -> dict:
        nodes = [
            {'id': s['id'], 'name': s['name'], 'type': s['type'],
             'role': s['role'], 'label': s['name']}
            for s in stages
        ]
        edges = [
            {'from': lnk['source_stage'], 'to': lnk['target_stage'],
             'from_name': lnk['source_name'], 'to_name': lnk['target_name'],
             'label': lnk['name']}
            for lnk in links
        ]

        source_tables = []
        target_tables = []
        for s in stages:
            tbl = s.get('table_name', '').strip()
            if not tbl:
                continue
            if s['role'] == 'source':
                source_tables.append(tbl)
            elif s['role'] == 'target':
                target_tables.append(tbl)

        return {
            'nodes':         nodes,
            'edges':         edges,
            'source_tables': list(dict.fromkeys(source_tables)),
            'target_tables': list(dict.fromkeys(target_tables)),
        }

    # ------------------------------------------------------------------
    # Summary stats
    # ------------------------------------------------------------------

    def _build_stats(self, stages: list, links: list, params: list) -> dict:
        role_counts: dict[str, int] = {}
        for s in stages:
            r = s['role']
            role_counts[r] = role_counts.get(r, 0) + 1

        total_derivations = sum(len(s.get('transformations', [])) for s in stages)
        total_cols = sum(
            len(s.get('input_columns', [])) + len(s.get('output_columns', []))
            for s in stages
        )

        n = len(stages)
        d = total_derivations
        complexity = 'High' if n > 10 or d > 15 else 'Medium' if n > 4 or d > 4 else 'Low'

        return {
            'total_stages':      n,
            'total_links':       len(links),
            'total_parameters':  len(params),
            'total_columns':     total_cols,
            'total_derivations': total_derivations,
            'stage_role_counts': role_counts,
            'complexity':        complexity,
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_dsx_file(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    return DSXParser(text).parse()


def parse_dsx_text(text: Any) -> dict:
    # Handle CP1252 / Latin-1 encoded bytes passed as string
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='replace')
    return DSXParser(text).parse()