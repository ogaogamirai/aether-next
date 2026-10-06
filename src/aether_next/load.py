"""Load graph IR from file text (format auto-detect)."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from aether_next.adapt.legacy_v3 import parse_legacy_v3_to_graph
from aether_next.engine.core import Graph, parse_dsl

COMPACT_MARKERS = ("[", "group:", "container:", "@layout:")


def detect_format(text: str) -> str:
    """Return 'legacy_v3' | 'compact'."""
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("sticky "):
            return "legacy_v3"
        for m in COMPACT_MARKERS:
            if s.startswith(m) or m in s:
                return "compact"
        if "->" in s and s.startswith("relation "):
            return "legacy_v3"
    return "compact"


def load_graph_from_text(text: str, title: str = "Aether Flow") -> Tuple[Graph, str, List[str]]:
    """
    Returns (graph, format_name, warnings).
    """
    fmt = detect_format(text)
    warnings: List[str] = []
    if fmt == "legacy_v3":
        graph, warnings = parse_legacy_v3_to_graph(text, title=title)
        return graph, fmt, warnings
    graph = parse_dsl(text, title=title)
    if not graph.nodes and "sticky " in text:
        graph, warnings = parse_legacy_v3_to_graph(text, title=title)
        return graph, "legacy_v3", warnings
    return graph, "compact", warnings


def load_graph_from_path(path: str | Path) -> Tuple[Graph, str, List[str]]:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    title = p.stem
    return load_graph_from_text(text, title=title)
