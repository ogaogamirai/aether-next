"""Marimo cockpit for aether-next (Phase 1). Run: marimo edit apps/cockpit.py"""

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    from pathlib import Path

    from aether_next.load import load_graph_from_path, load_graph_from_text
    from aether_next.engine.core import THEMES

    return load_graph_from_path, load_graph_from_text, mo


@app.cell
def _(mo):
    mo.md("""
    # Aether-next cockpit (Phase 1)
    **閲覧専用** · marimo シェル · エンジンは単一 SVG (`graph_dsl` 系)。
    正本 `Tools/aether` は未変更。計画: `docs/PLAN_v01.md`
    """)
    return


@app.cell
def _(mo):
    board_picker = mo.ui.dropdown(
        options=list(_DEFAULT_BOARDS.keys()),
        value="legacy: aether_dsl_test",
        label="ボード（プリセット）",
    )
    theme_picker = mo.ui.dropdown(
        options=["cool_dark", "academic_light", "paper_warm"],
        value="cool_dark",
        label="テーマ",
    )
    fit_toggle = mo.ui.checkbox(value=True, label="初期 Fit 表示")
    return board_picker, fit_toggle, theme_picker


@app.cell
def _(
    board_picker,
    fit_toggle,
    load_graph_from_path,
    load_graph_from_text,
    theme_picker,
):
    import marimo as mo

    rel_path = _DEFAULT_BOARDS[board_picker.value]
    warnings = []
    fmt = "compact"
    if rel_path:
        graph, fmt, warnings = load_graph_from_path(rel_path)
    else:
        graph, fmt, warnings = load_graph_from_text(_COMPACT_DEMO, title="demo")

    graph.fit_mode = fit_toggle.value
    theme_key = theme_picker.value
    return fmt, graph, mo, theme_key, warnings


@app.cell
def _(graph, theme_key):
    svg_html = graph.to_svg(theme_key=theme_key)
    return (svg_html,)


@app.cell
def _(fmt, graph, mo, warnings):
    stats = mo.md(
        f"""
        | 項目 | 値 |
        |---|---|
        | 形式 | `{fmt}` |
        | ノード | {len(graph.nodes)} |
        | エッジ | {len(graph.edges)} |
        | 警告 | {len(warnings)} |
        """
    )
    warn_block = mo.md("```\n" + "\n".join(warnings[:12]) + "\n```") if warnings else mo.md("_警告なし_")
    return stats, warn_block


@app.cell
def _(stats, svg_html, warn_block):
    import marimo as mo

    mo.vstack([stats, warn_block, mo.Html(svg_html)])
    return (mo,)


if __name__ == "__main__":
    app.run()
