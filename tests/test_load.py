from pathlib import Path

from aether_next.load import detect_format, load_graph_from_path, load_graph_from_text

AETHER_DIR = Path(r"G:\マイドライブ\Tools\aether")


def test_detect_legacy_from_sticky():
    text = 'sticky N1 "Title" {\n  pos: 10 20\n}\n'
    assert detect_format(text) == "legacy_v3"


def test_load_succession_navi_smoke():
    path = AETHER_DIR / "aether_dsl_succession_navi.txt"
    if not path.is_file():
        return
    graph, fmt, warnings = load_graph_from_path(path)
    assert fmt == "legacy_v3"
    assert len(graph.nodes) >= 20
    assert len(graph.edges) >= 10
    assert len(graph.nodes) > 0
    # positions preserved
    any_pos = any(n.x is not None and n.y is not None for n in graph.nodes.values())
    assert any_pos


def test_compact_demo():
    dsl = "[A: one | color=cyan]\n[B: two | color=emerald]\n[A] -> [B]\n"
    graph, fmt, _ = load_graph_from_text(dsl)
    assert fmt == "compact"
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
