"""
Aether DSL v3/v4 export format (sticky / relation / simple arrows).

Mirrors the sticky+relation subset of Tools/aether/aether_parser.js.
Drawings/callouts/paths are parsed for diagnostics but not rendered in v0.1.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from aether_next.engine.core import Graph, Node

# Legacy UI color names → graph_dsl palette keys
_COLOR_MAP = {
    "blue": "blue",
    "cyan": "cyan",
    "green": "emerald",
    "emerald": "emerald",
    "orange": "amber",
    "yellow": "amber",
    "amber": "amber",
    "purple": "purple",
    "rose": "rose",
    "red": "rose",
    "pink": "rose",
    "slate": "slate",
    "gray": "slate",
    "grey": "slate",
}


def _unquote(val: str) -> str:
    val = val.strip()
    if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
        return val[1:-1]
    return val


@dataclass
class LegacySticky:
    id: str
    title: str
    x: float = 120.0
    y: float = 120.0
    color: str = "amber"
    tags: List[str] = field(default_factory=list)
    desc: str = ""
    time: str = ""
    tone: str = ""
    role: str = ""
    confidence: str = ""


@dataclass
class LegacyRelation:
    source: str
    target: str
    label: str = ""
    rel_id: str = ""
    color: Optional[str] = None
    time: str = ""


@dataclass
class LegacyParseResult:
    stickies: List[LegacySticky]
    relations: List[LegacyRelation]
    simple_edges: List[Tuple[str, str]]
    warnings: List[str]


def parse_legacy_v3(text: str) -> LegacyParseResult:
    stickies: List[LegacySticky] = []
    relations: List[LegacyRelation] = []
    simple_edges: List[Tuple[str, str]] = []
    warnings: List[str] = []

    current_sticky: Optional[LegacySticky] = None
    current_relation: Optional[LegacyRelation] = None
    in_drawing = False

    sticky_open = re.compile(r'^sticky\s+(\w+)\s+"([^"]+)"\s*\{')
    relation_open = re.compile(r"^relation\s+(.+?)\s*->\s*(\w+)\s*\{")
    prop_line = re.compile(r"^(\w+):\s*(.+)$")
    simple_conn = re.compile(r"^(\w+)\s*->\s*(\w+)$")

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith(("drawing ", "callout ", "path ")):
            in_drawing = True
            warnings.append(f"unsupported_block: {line.split()[0]} (skipped)")
            continue

        m_st = sticky_open.match(line)
        if m_st:
            current_sticky = LegacySticky(id=m_st.group(1), title=m_st.group(2))
            continue

        m_rel = relation_open.match(line)
        if m_rel:
            left = m_rel.group(1).strip()
            target = m_rel.group(2)
            tokens = left.split()
            if len(tokens) == 1:
                source, rel_id = tokens[0], ""
            else:
                rel_id, source = tokens[0], tokens[-1]
            current_relation = LegacyRelation(
                source=source, target=target, rel_id=rel_id
            )
            continue

        if current_sticky is not None:
            if line == "}":
                stickies.append(current_sticky)
                current_sticky = None
                continue
            pm = prop_line.match(line)
            if pm:
                prop, val = pm.group(1), _unquote(pm.group(2))
                if prop == "pos":
                    parts = val.split()
                    if len(parts) >= 2:
                        try:
                            current_sticky.x = float(parts[0])
                            current_sticky.y = float(parts[1])
                        except ValueError:
                            warnings.append(f"bad_pos:{current_sticky.id}")
                elif prop == "color":
                    current_sticky.color = val
                elif prop == "tags":
                    current_sticky.tags = val.split()
                elif prop == "desc":
                    current_sticky.desc = val.replace("\\n", "\n")
                elif prop == "time":
                    current_sticky.time = val
                elif prop == "tone":
                    current_sticky.tone = val
                elif prop == "role":
                    current_sticky.role = val
                elif prop == "confidence":
                    current_sticky.confidence = val
            continue

        if current_relation is not None:
            if line == "}":
                relations.append(current_relation)
                current_relation = None
                continue
            pm = prop_line.match(line)
            if pm:
                prop, val = pm.group(1), _unquote(pm.group(2))
                if prop == "label":
                    current_relation.label = val
                elif prop == "color":
                    current_relation.color = val
                elif prop == "time":
                    current_relation.time = val
            continue

        if in_drawing:
            if line == "}":
                in_drawing = False
            continue

        m_conn = simple_conn.match(line)
        if m_conn:
            simple_edges.append((m_conn.group(1), m_conn.group(2)))

    return LegacyParseResult(
        stickies=stickies,
        relations=relations,
        simple_edges=simple_edges,
        warnings=warnings,
    )


def legacy_to_graph(
    parsed: LegacyParseResult,
    title: str = "Aether Board",
    *,
    use_layout_positions: bool = True,
) -> Graph:
    g = Graph(title=title)
    g.fit_mode = True

    for s in parsed.stickies:
        pal = _COLOR_MAP.get(s.color.lower(), "slate")
        subtitle_parts = [p for p in [s.role, s.confidence, s.time] if p]
        subtitle = " · ".join(subtitle_parts[:2])
        node = Node(
            id=s.id,
            title=s.title,
            subtitle=subtitle,
            desc=s.desc,
            color=pal,
        )
        if use_layout_positions:
            node.x = s.x
            node.y = s.y
        g.add_node(node)

    for rel in parsed.relations:
        edge_color = None
        if rel.color:
            edge_color = _COLOR_MAP.get(rel.color.lower(), rel.color)
        g.add_edge(
            rel.source,
            rel.target,
            label=rel.label,
            color=edge_color,
        )

    for src, tgt in parsed.simple_edges:
        g.add_edge(src, tgt)

    missing = set()
    for e in g.edges:
        if e.source not in g.nodes:
            missing.add(e.source)
        if e.target not in g.nodes:
            missing.add(e.target)
    if missing:
        parsed.warnings.append(f"dangling_edge_nodes:{','.join(sorted(missing))}")

    return g


def parse_legacy_v3_to_graph(text: str, title: str = "Aether Board") -> Tuple[Graph, List[str]]:
    parsed = parse_legacy_v3(text)
    graph = legacy_to_graph(parsed, title=title)
    return graph, parsed.warnings
