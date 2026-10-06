"""
Aether Graph DSL Core Engine (Lightweight Python + SVG)
外部重厚ライブラリ不要。極小で動作するNode/Edgeオブジェクト、
コンパクトDSLパーサー、3大自動配置（LR水平 / TB垂直 / Radial放射）、
4方向動的ポート自動接続、マルチカラーテーマ対応、
カード内動的ウィジェット（マウラーのバラ、白うさぎ、猫、波形）、
さらに「クリック詳細パネル（Inspector）」＆「矢印キー（↑↓←→）フォーカス移動」を完全統合。
"""

import json
import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

# ==========================================
# カラーテーマ定義
# ==========================================
THEMES = {
    "academic_light": {
        "name": "🏛️ Academic Light (知的・明るいホワイト)",
        "bg": "#f8fafc",
        "grid": "rgba(15, 23, 42, 0.05)",
        "wrapper_bg": "#ffffff",
        "wrapper_border": "#cbd5e1",
        "card_bg": "#ffffff",
        "card_shadow": "0 4px 14px rgba(15, 23, 42, 0.08)",
        "text_title": "#0f172a",
        "text_sub": "#475569",
        "text_desc": "#64748b",
        "edge_default": "#64748b",
        "arrow_color": "#64748b",
        "panel_bg": "rgba(255, 255, 255, 0.95)",
        "panel_border": "#cbd5e1",
        "palette": {
            "cyan": {"border": "#0e7490", "header": "#0e7490", "badge": "rgba(14, 116, 144, 0.1)"},
            "emerald": {"border": "#2d6a4f", "header": "#2d6a4f", "badge": "rgba(45, 106, 79, 0.1)"},
            "amber": {"border": "#b45309", "header": "#b45309", "badge": "rgba(180, 83, 9, 0.1)"},
            "purple": {"border": "#6d597a", "header": "#6d597a", "badge": "rgba(109, 89, 122, 0.1)"},
            "rose": {"border": "#9e2a2b", "header": "#9e2a2b", "badge": "rgba(158, 42, 43, 0.1)"},
            "blue": {"border": "#2b4c7e", "header": "#2b4c7e", "badge": "rgba(43, 76, 126, 0.1)"},
            "slate": {"border": "#4a5568", "header": "#4a5568", "badge": "rgba(74, 85, 104, 0.1)"},
        }
    },
    "cool_dark": {
        "name": "🪐 Aether Slate (クール・宇宙ダーク)",
        "bg": "#0b0f19",
        "grid": "rgba(255, 255, 255, 0.06)",
        "wrapper_bg": "#0f172a",
        "wrapper_border": "#334155",
        "card_bg": "#1e293b",
        "card_shadow": "0 12px 30px rgba(0, 0, 0, 0.5)",
        "text_title": "#f8fafc",
        "text_sub": "#94a3b8",
        "text_desc": "#64748b",
        "edge_default": "#475569",
        "arrow_color": "#64748b",
        "panel_bg": "rgba(15, 23, 42, 0.95)",
        "panel_border": "#334155",
        "palette": {
            "cyan": {"border": "#38bdf8", "header": "#38bdf8", "badge": "rgba(56, 189, 248, 0.15)"},
            "emerald": {"border": "#34d399", "header": "#34d399", "badge": "rgba(52, 211, 153, 0.15)"},
            "amber": {"border": "#fbbf24", "header": "#fbbf24", "badge": "rgba(251, 191, 36, 0.15)"},
            "purple": {"border": "#c084fc", "header": "#c084fc", "badge": "rgba(192, 132, 252, 0.15)"},
            "rose": {"border": "#fb7185", "header": "#fb7185", "badge": "rgba(251, 113, 133, 0.15)"},
            "blue": {"border": "#60a5fa", "header": "#60a5fa", "badge": "rgba(96, 165, 250, 0.15)"},
            "slate": {"border": "#94a3b8", "header": "#94a3b8", "badge": "rgba(148, 163, 184, 0.15)"},
        }
    },
    "paper_warm": {
        "name": "📜 Paper Warm (書籍・アイボリー暖色)",
        "bg": "#f5f0e8",
        "grid": "rgba(68, 54, 42, 0.06)",
        "wrapper_bg": "#faf7f2",
        "wrapper_border": "#ded5c7",
        "card_bg": "#ffffff",
        "card_shadow": "0 4px 14px rgba(68, 54, 42, 0.08)",
        "text_title": "#292524",
        "text_sub": "#57534e",
        "text_desc": "#78716c",
        "edge_default": "#78716c",
        "arrow_color": "#78716c",
        "panel_bg": "rgba(250, 247, 242, 0.95)",
        "panel_border": "#ded5c7",
        "palette": {
            "cyan": {"border": "#466975", "header": "#466975", "badge": "rgba(70, 105, 117, 0.1)"},
            "emerald": {"border": "#588157", "header": "#588157", "badge": "rgba(88, 129, 87, 0.1)"},
            "amber": {"border": "#a36a39", "header": "#a36a39", "badge": "rgba(163, 106, 57, 0.1)"},
            "purple": {"border": "#6a4c6e", "header": "#6a4c6e", "badge": "rgba(106, 76, 110, 0.1)"},
            "rose": {"border": "#a24936", "header": "#a24936", "badge": "rgba(162, 73, 54, 0.1)"},
            "blue": {"border": "#3d5a80", "header": "#3d5a80", "badge": "rgba(61, 90, 128, 0.1)"},
            "slate": {"border": "#5c5549", "header": "#5c5549", "badge": "rgba(92, 85, 73, 0.1)"},
        }
    }
}

COLOR_PALETTE = THEMES["cool_dark"]["palette"]


# ==========================================
# 動的ウィジェット描画
# ==========================================
def generate_widget_svg(widget_name: str, x: float, y: float, size: float = 52.0, pal: dict = None) -> str:
    """カード内に埋め込むミニチュア動的ベクターウィジェット"""
    color = pal.get("header", "#38bdf8") if pal else "#38bdf8"
    border = pal.get("border", "#38bdf8") if pal else "#38bdf8"
    cx, cy = x + size / 2.0, y + size / 2.0

    if widget_name == "rose":
        r = size * 0.44
        pts = []
        for k in range(0, 361, 3):
            th_rad = (k * 71.0) * math.pi / 180.0
            rad = r * math.sin(6.0 * th_rad)
            px = cx + rad * math.cos(th_rad)
            py = cy + rad * math.sin(th_rad)
            pts.append(f"{px:.1f},{py:.1f}")
        points_str = " ".join(pts)
        return f'''<g class="widget-rose" style="transform-origin:{cx:.1f}px {cy:.1f}px;">
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{size/2.0:.1f}" fill="rgba(0,0,0,0.04)" stroke="{color}" stroke-width="1" stroke-dasharray="3,2" opacity="0.6" />
  <polyline points="{points_str}" fill="none" stroke="{color}" stroke-width="1.3" opacity="0.85" />
</g>'''

    elif widget_name == "rabbit":
        return f'''<g class="widget-rabbit">
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{size/2.0:.1f}" fill="rgba(244, 63, 94, 0.08)" stroke="{border}" stroke-width="1" stroke-dasharray="3,2" opacity="0.7" />
  <g transform="translate({cx:.1f}, {cy + 3.0:.1f})">
    <circle cx="0" cy="0" r="14" fill="#ffffff" stroke="#94a3b8" stroke-width="0.8" />
    <ellipse cx="-4.5" cy="-18" rx="3" ry="8.5" fill="#ffffff" stroke="#94a3b8" stroke-width="0.8" />
    <ellipse cx="-4.5" cy="-18" rx="1.6" ry="6" fill="#fda4af" opacity="0.75" />
    <ellipse cx="4.5" cy="-18" rx="3" ry="8.5" fill="#ffffff" stroke="#94a3b8" stroke-width="0.8" />
    <ellipse cx="4.5" cy="-18" rx="1.6" ry="6" fill="#fda4af" opacity="0.75" />
    <circle cx="-7.5" cy="3.5" r="2.6" fill="#f43f5e" opacity="0.4" />
    <circle cx="7.5" cy="3.5" r="2.6" fill="#f43f5e" opacity="0.4" />
    <ellipse cx="-4.5" cy="-1" rx="1.7" ry="2.2" fill="#be123c" />
    <circle cx="-3.8" cy="-1.8" r="0.6" fill="#ffffff" />
    <ellipse cx="4.5" cy="-1" rx="1.7" ry="2.2" fill="#be123c" />
    <circle cx="3.8" cy="-1.8" r="0.6" fill="#ffffff" />
    <ellipse cx="0" cy="2.8" rx="1.3" ry="1" fill="#f43f5e" />
    <path d="M -1.8 4.5 Q 0 6 1.8 4.5" fill="none" stroke="#475569" stroke-width="0.8" />
  </g>
</g>'''

    elif widget_name == "cat":
        return f'''<g class="widget-cat">
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{size/2.0:.1f}" fill="rgba(217, 119, 6, 0.08)" stroke="{border}" stroke-width="1" stroke-dasharray="3,2" opacity="0.7" />
  <g transform="translate({cx:.1f}, {cy + 2.0:.1f})">
    <ellipse cx="0" cy="0" rx="14" ry="12.5" fill="#ffffff" stroke="#94a3b8" stroke-width="0.8" />
    <polygon points="-10,-6 -15,-16 -3,-10" fill="#27272a" stroke="#18181b" stroke-width="0.8" />
    <polygon points="-9,-7 -12,-14 -4,-10" fill="#fda4af" opacity="0.65" />
    <polygon points="10,-6 15,-16 3,-10" fill="#27272a" stroke="#18181b" stroke-width="0.8" />
    <polygon points="9,-7 12,-14 4,-10" fill="#fda4af" opacity="0.65" />
    <path d="M 0 -11 Q -5 -5 -11 0 Q -13 -6 -6 -11 Z" fill="#27272a" />
    <path d="M 0 -11 Q 5 -5 11 0 Q 13 -6 6 -11 Z" fill="#27272a" />
    <ellipse cx="-5" cy="0" rx="2.6" ry="3" fill="#d97706" />
    <ellipse cx="-5" cy="0" rx="1" ry="2.6" fill="#18181b" />
    <circle cx="-4.3" cy="-1" r="0.6" fill="#ffffff" />
    <ellipse cx="5" cy="0" rx="2.6" ry="3" fill="#d97706" />
    <ellipse cx="5" cy="0" rx="1" ry="2.6" fill="#18181b" />
    <circle cx="4.3" cy="-1" r="0.6" fill="#ffffff" />
    <polygon points="0,2.3 -1,1.1 1,1.1" fill="#f43f5e" />
    <line x1="-6" y1="2.3" x2="-13" y2="1.3" stroke="#64748b" stroke-width="0.6" />
    <line x1="-6" y1="4.3" x2="-13" y2="5.3" stroke="#64748b" stroke-width="0.6" />
    <line x1="6" y1="2.3" x2="13" y2="1.3" stroke="#64748b" stroke-width="0.6" />
    <line x1="6" y1="4.3" x2="13" y2="5.3" stroke="#64748b" stroke-width="0.6" />
  </g>
</g>'''

    elif widget_name == "sine":
        cx_s, cy_s = x + 4.0, y + size / 2.0
        pts = []
        for i in range(45):
            px = cx_s + i * (size - 8.0) / 44.0
            py = cy_s - 14.0 * math.sin(i * 0.28)
            pts.append(f"{px:.1f},{py:.1f}")
        return f'''<g class="widget-sine">
  <line x1="{cx_s:.1f}" y1="{cy_s:.1f}" x2="{cx_s+size-8.0:.1f}" y2="{cy_s:.1f}" stroke="{color}" stroke-width="0.6" stroke-dasharray="2,2" opacity="0.4" />
  <polyline points="{' '.join(pts)}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" />
</g>'''

    return ""


# ==========================================
# データ構造
# ==========================================
@dataclass
class Node:
    id: str
    title: str
    subtitle: str = ""
    desc: str = ""
    color: str = "cyan"
    icon: str = ""
    widget: str = ""
    x: Optional[float] = None
    y: Optional[float] = None
    w: float = 190.0
    h: float = 90.0


@dataclass
class Edge:
    source: str
    target: str
    label: str = ""
    style: str = "bezier"
    dashed: bool = False
    color: Optional[str] = None


@dataclass
class Container:
    id: str
    title: str
    node_ids: List[str] = field(default_factory=list)
    color: str = "slate"
    dashed: bool = True


# ==========================================
# グラフ描画ヘルパー（HTML / SVG コンポーネント生成）
# ==========================================
def _build_css(th: dict) -> str:
    """グラフ全体のCSSスタイルシート"""
    return '''<style>
  @keyframes spin { 100% { transform: rotate(360deg); } }
  .widget-rose { animation: spin 24s linear infinite; }
  .sticky-card.focused > rect:first-child {
    stroke: #38bdf8 !important;
    stroke-width: 3.5px !important;
    filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.6));
  }
  .aether-inspector.open {
    transform: translateX(0) !important;
    opacity: 1 !important;
    pointer-events: auto !important;
  }
  /* 手書き風スケッチモード */
  .sketch-mode .sticky-card > rect,
  .sketch-mode .edge-path,
  .sketch-mode .aether-container > rect {
    filter: url(#sketch-filter);
    stroke-linecap: round;
    stroke-linejoin: round;
  }
  .aether-container > rect {
    transition: all 0.25s cubic-bezier(0.2, 0, 0, 1);
  }
</style>'''


def _build_toolbar(th: dict, sketch_active: bool, fit_active: bool = False) -> str:
    """操作ツールバーHTML"""
    btn_sketch_style = 'background:rgba(0,0,0,0.08);' if sketch_active else 'background:transparent;'
    btn_fit_style = 'background:rgba(0,0,0,0.08);' if fit_active else 'background:transparent;'
    fit_label = '📐 1:1' if fit_active else '🔍 全体 (Fit)'
    return f'''<div style="position:absolute; top:12px; left:12px; z-index:10; display:flex; gap:6px; background:rgba(255,255,255,0.75); backdrop-filter:blur(8px); padding:4px 6px; border-radius:10px; border:1px solid {th['wrapper_border']}; box-shadow:0 2px 6px rgba(0,0,0,0.05);">
  <button onclick="window.__realignAether('LR')" style="background:transparent; border:none; padding:4px 8px; font-size:11px; font-weight:600; color:{th['text_sub']}; cursor:pointer; border-radius:6px;" title="水平フロー整列">↔️ 水平(LR)</button>
  <button onclick="window.__realignAether('TB')" style="background:transparent; border:none; padding:4px 8px; font-size:11px; font-weight:600; color:{th['text_sub']}; cursor:pointer; border-radius:6px;" title="垂直ツリー整列">↕️ 垂直(TB)</button>
  <button onclick="window.__realignAether('radial')" style="background:transparent; border:none; padding:4px 8px; font-size:11px; font-weight:600; color:{th['text_sub']}; cursor:pointer; border-radius:6px;" title="放射ハブ整列">🕸️ 放射</button>
  <span style="border-left:1px solid {th['wrapper_border']}; margin:2px 2px;"></span>
  <button id="btn-toggle-fit" onclick="window.__toggleFitView()" style="{btn_fit_style} border:none; padding:4px 8px; font-size:11px; font-weight:600; color:{th['text_sub']}; cursor:pointer; border-radius:6px;" title="キャンバス全体表示 (Fit) と等倍 (1:1) の切り替え">{fit_label}</button>
  <button id="btn-toggle-sketch" onclick="window.__toggleSketchMode()" style="{btn_sketch_style} border:none; padding:4px 8px; font-size:11px; font-weight:600; color:{th['text_sub']}; cursor:pointer; border-radius:6px;" title="手書き風スケッチ描画の切り替え">✏️ スケッチ</button>
  <span style="border-left:1px solid {th['wrapper_border']}; margin:2px 2px;"></span>
  <button onclick="window.__exportCurrentLayoutHTML()" style="background:transparent; border:none; padding:4px 8px; font-size:11px; font-weight:600; color:{th['text_sub']}; cursor:pointer; border-radius:6px;" title="現在のノード配置をデフォルトにして単体HTMLを保存">💾 配置を保存</button>
  <span style="border-left:1px solid {th['wrapper_border']}; margin:2px 2px;"></span>
  <span style="font-size:10px; color:{th['text_desc']}; align-self:center; padding:0 4px;">⌨️ 矢印キーで移動</span>
</div>'''


def _build_defs(th: dict) -> str:
    """SVG <defs> 定義（矢印マーカーおよび手書きフィルタ）"""
    return f'''  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="{th['arrow_color']}" />
    </marker>
    <filter id="sketch-filter" x="-10%" y="-10%" width="120%" height="120%">
      <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="3" result="noise" />
      <feDisplacementMap in="SourceGraphic" in2="noise" scale="2.5" xChannelSelector="R" yChannelSelector="G" />
    </filter>
  </defs>'''


def _build_containers_svg(containers: Dict[str, Container], nodes: Dict[str, Node], palette: dict) -> str:
    """最背面コンテナ（グループ領域）レイヤー"""
    lines = ['  <g id="containers-layer">']
    for c in containers.values():
        c_nodes = [nodes[nid] for nid in c.node_ids if nid in nodes]
        if not c_nodes:
            continue
        min_x = min(n.x for n in c_nodes) - 20.0
        min_y = min(n.y for n in c_nodes) - 32.0
        max_x = max(n.x + n.w for n in c_nodes) + 20.0
        max_y = max(n.y + n.h for n in c_nodes) + 20.0
        cw = max_x - min_x
        ch = max_y - min_y
        cpal = palette.get(c.color, palette["slate"])
        dash_attr = 'stroke-dasharray="6,4" ' if c.dashed else ''
        nids_str = ",".join(c.node_ids)

        lines.append(f'    <g id="container_{c.id}" class="aether-container" data-nodes="{nids_str}">')
        lines.append(f'      <rect x="{min_x:.1f}" y="{min_y:.1f}" width="{cw:.1f}" height="{ch:.1f}" rx="14" fill="{cpal["badge"]}" stroke="{cpal["border"]}" stroke-width="1.6" {dash_attr}opacity="0.85" />')
        lines.append(f'      <text x="{min_x + 14:.1f}" y="{min_y + 20:.1f}" font-size="11" font-weight="700" fill="{cpal["header"]}" letter-spacing="0.05em">{c.title}</text>')
        lines.append('    </g>')
    lines.append('  </g>')
    return "\n".join(lines)


def _build_edges_svg(edges: List[Edge], nodes: Dict[str, Node], th: dict) -> str:
    """エッジ（接続線・ラベル）レイヤー"""
    lines = ['  <g id="edges-layer">']
    for i, edge in enumerate(edges):
        u = nodes.get(edge.source)
        v = nodes.get(edge.target)
        if not u or not v:
            continue
        
        d, mx, my = Graph.calc_dynamic_ports(u.x, u.y, u.w, u.h, v.x, v.y, v.w, v.h)
        dash_attr = 'stroke-dasharray="6,4" ' if edge.dashed else ''
        edge_color = edge.color or th["edge_default"]
        edge_id = f"edge_{u.id}_{v.id}_{i}"
        
        lines.append(f'    <g class="edge-group" id="group_{edge_id}">')
        lines.append(f'      <path id="{edge_id}" class="edge-path" data-u="{u.id}" data-v="{v.id}" d="{d}" fill="none" stroke="{edge_color}" stroke-width="2.5" stroke-linecap="round" {dash_attr}marker-end="url(#arrow)" />')
        if edge.label:
            lines.append(f'      <text id="lbl_{edge_id}" x="{mx:.1f}" y="{my:.1f}" font-size="11" font-weight="600" fill="{th["text_sub"]}" text-anchor="middle">{edge.label}</text>')
        lines.append('    </g>')
    lines.append('  </g>')
    return "\n".join(lines)


def _build_nodes_svg(nodes: Dict[str, Node], palette: dict, th: dict, interactive: bool) -> str:
    """ノード（カード、ウィジェット、ポート）レイヤー"""
    lines = ['  <g id="cards-layer">']
    for node in nodes.values():
        pal = palette.get(node.color, palette["cyan"])
        cursor = 'style="cursor:grab; transition: transform 0.25s cubic-bezier(0.2, 0, 0, 1);"' if interactive else ''
        lines.append(f'    <g id="{node.id}" class="sticky-card" transform="translate({node.x:.1f}, {node.y:.1f})" data-x="{node.x:.1f}" data-y="{node.y:.1f}" data-w="{node.w:.1f}" data-h="{node.h:.1f}" {cursor}>')
        lines.append(f'      <rect x="0" y="0" width="{node.w:.1f}" height="{node.h:.1f}" rx="10" fill="{th["card_bg"]}" stroke="{pal["border"]}" stroke-width="2" />')
        lines.append(f'      <rect x="0" y="0" width="{node.w:.1f}" height="6" rx="3" fill="{pal["header"]}" />')
        
        lines.append(f'      <text x="12" y="24" font-size="10" font-weight="700" fill="{pal["header"]}" letter-spacing="0.05em">{node.id.upper()}</text>')
        lines.append(f'      <text x="12" y="44" font-size="13" font-weight="600" fill="{th["text_title"]}">{node.title}</text>')
        if node.subtitle:
            lines.append(f'      <text x="12" y="64" font-size="11" fill="{th["text_sub"]}">{node.subtitle}</text>')
        if node.desc:
            lines.append(f'      <text x="12" y="78" font-size="10" fill="{th["text_desc"]}">{node.desc}</text>')
        
        if node.widget:
            wx = node.w - 58.0
            wy = (node.h - 52.0) / 2.0 + 3.0
            widget_svg = generate_widget_svg(node.widget, wx, wy, size=52.0, pal=pal)
            lines.append(f'      {widget_svg}')

        # 4方向接続ポート（目印）
        lines.append(f'      <circle cx="{node.w/2:.1f}" cy="0" r="3" fill="{pal["header"]}" opacity="0.6" />')
        lines.append(f'      <circle cx="{node.w:.1f}" cy="{node.h/2:.1f}" r="3" fill="{pal["header"]}" opacity="0.6" />')
        lines.append(f'      <circle cx="{node.w/2:.1f}" cy="{node.h:.1f}" r="3" fill="{pal["header"]}" opacity="0.6" />')
        lines.append(f'      <circle cx="0" cy="{node.h/2:.1f}" r="3" fill="{pal["header"]}" opacity="0.6" />')
        lines.append('    </g>')
    lines.append('  </g>')
    return "\n".join(lines)


def _build_inspector_html(th: dict) -> str:
    """右サイド詳細インスペクターパネルHTML"""
    return f'''<!-- 右サイド詳細インスペクターパネル -->
<div id="aether-inspector" class="aether-inspector" onpointerdown="event.stopPropagation()" onclick="event.stopPropagation()" style="position:absolute; top:12px; right:12px; width:280px; max-height:calc(100% - 24px); background:{th.get('panel_bg', 'rgba(255,255,255,0.95)')}; backdrop-filter:blur(12px); border:1px solid {th.get('panel_border', '#cbd5e1')}; border-radius:14px; padding:16px; box-shadow:0 12px 30px rgba(0,0,0,0.18); box-sizing:border-box; transform:translateX(320px); transition:transform 0.25s cubic-bezier(0.2,0,0,1), opacity 0.25s ease; opacity:0; pointer-events:none; z-index:9999; overflow-y:auto; font-family:system-ui,sans-serif;">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
    <span id="insp-badge" style="font-size:10px; font-weight:700; padding:2px 8px; border-radius:999px; letter-spacing:0.05em; background:rgba(2,132,199,0.12); color:#0284c7;">ID</span>
    <button onclick="window.__closeInspector()" style="background:none; border:none; color:{th['text_desc']}; font-size:16px; font-weight:700; cursor:pointer; line-height:1; padding:2px 6px;">✕</button>
  </div>
  <div id="insp-title" style="font-size:15px; font-weight:700; color:{th['text_title']}; margin-bottom:4px; line-height:1.4;">タイトル</div>
  <div id="insp-sub" style="font-size:12px; color:{th['text_sub']}; margin-bottom:12px; font-weight:500;">サブタイトル</div>
  <div id="insp-desc" style="font-size:12px; color:{th['text_desc']}; line-height:1.6; margin-bottom:14px; background:rgba(0,0,0,0.03); padding:8px 10px; border-radius:8px; border-left:3px solid {th['arrow_color']};">説明</div>
  
  <div style="font-size:11px; font-weight:700; color:{th['text_sub']}; margin-bottom:6px;">🔗 接続エッジ</div>
  <div id="insp-edges" style="font-size:11px; color:{th['text_desc']}; display:flex; flex-direction:column; gap:4px;"></div>
</div>'''


def _build_client_script(node_ids: list, node_meta_dict: dict, edges_list: list, th: dict, theme_key: str, init_view_w: int = 980, init_view_h: int = 480, fit_active: bool = False) -> str:
    """ネイティブJavaScript（インタラクション・幾何計算・整列・全体Fit・HTML保存）"""
    node_ids_json = json.dumps(node_ids, ensure_ascii=False)
    node_meta_json = json.dumps(node_meta_dict, ensure_ascii=False)
    edges_json = json.dumps(edges_list, ensure_ascii=False)
    fit_active_str = "true" if fit_active else "false"

    return f'''<script>
(function() {{
  const svg = document.getElementById('aether-svg');
  if (!svg) return;
  const inspector = document.getElementById('aether-inspector');
  let target = null;
  let offset = {{ x: 0, y: 0 }};
  let pointerStart = {{ x: 0, y: 0 }};
  let currentFocusId = null;

  const initViewW = {init_view_w};
  const initViewH = {init_view_h};
  let isFitMode = {fit_active_str};

  const nodeIds = {node_ids_json};
  const nodeMeta = {node_meta_json};
  const edgesList = {edges_json};

  function applyCardPos(card, x, y) {{
    card.setAttribute('data-x', x);
    card.setAttribute('data-y', y);
    card.setAttribute('transform', `translate(${{x}},${{y}})`);
  }}

  function calcDynamicPorts(ux, uy, uw, uh, vx, vy, vw, vh) {{
    const cx_u = ux + uw / 2.0;
    const cy_u = uy + uh / 2.0;
    const cx_v = vx + vw / 2.0;
    const cy_v = vy + vh / 2.0;

    const dx = cx_v - cx_u;
    const dy = cy_v - cy_u;

    let p1, p2, c1, c2;
    if (Math.abs(dx) >= Math.abs(dy)) {{
      if (dx >= 0) {{
        p1 = [ux + uw, cy_u];
        p2 = [vx, cy_v];
        const dist = Math.max(40.0, Math.abs(dx) * 0.45);
        c1 = [p1[0] + dist, p1[1]];
        c2 = [p2[0] - dist, p2[1]];
      }} else {{
        p1 = [ux, cy_u];
        p2 = [vx + vw, cy_v];
        const dist = Math.max(40.0, Math.abs(dx) * 0.45);
        c1 = [p1[0] - dist, p1[1]];
        c2 = [p2[0] + dist, p2[1]];
      }}
    }} else {{
      if (dy >= 0) {{
        p1 = [cx_u, uy + uh];
        p2 = [cx_v, vy];
        const dist = Math.max(40.0, Math.abs(dy) * 0.45);
        c1 = [p1[0], p1[1] + dist];
        c2 = [p2[0], p2[1] - dist];
      }} else {{
        p1 = [cx_u, uy];
        p2 = [cx_v, vy + vh];
        const dist = Math.max(40.0, Math.abs(dy) * 0.45);
        c1 = [p1[0], p1[1] - dist];
        c2 = [p2[0], p2[1] + dist];
      }}
    }}
    const d = `M ${{p1[0].toFixed(1)}} ${{p1[1].toFixed(1)}} C ${{c1[0].toFixed(1)}} ${{c1[1].toFixed(1)}}, ${{c2[0].toFixed(1)}} ${{c2[1].toFixed(1)}}, ${{p2[0].toFixed(1)}} ${{p2[1].toFixed(1)}}`;
    const mx = (p1[0] + p2[0]) / 2.0;
    const my = (p1[1] + p2[1]) / 2.0 - 8.0;
    return {{ d, mx, my }};
  }}

  function updateEdges() {{
    svg.querySelectorAll('.edge-path').forEach(edge => {{
      const uId = edge.getAttribute('data-u');
      const vId = edge.getAttribute('data-v');
      const u = svg.querySelector('#' + uId);
      const v = svg.querySelector('#' + vId);
      if (!u || !v) return;

      const ux = parseFloat(u.getAttribute('data-x'));
      const uy = parseFloat(u.getAttribute('data-y'));
      const uw = parseFloat(u.getAttribute('data-w'));
      const uh = parseFloat(u.getAttribute('data-h'));

      const vx = parseFloat(v.getAttribute('data-x'));
      const vy = parseFloat(v.getAttribute('data-y'));
      const vw = parseFloat(v.getAttribute('data-w'));
      const vh = parseFloat(v.getAttribute('data-h'));

      const res = calcDynamicPorts(ux, uy, uw, uh, vx, vy, vw, vh);
      edge.setAttribute('d', res.d);

      const lbl = svg.querySelector('#lbl_' + edge.id);
      if (lbl) {{
        lbl.setAttribute('x', res.mx);
        lbl.setAttribute('y', res.my);
      }}
    }});
  }}

  function updateContainers() {{
    svg.querySelectorAll('.aether-container').forEach(cGroup => {{
      const nids = (cGroup.getAttribute('data-nodes') || '').split(',').filter(Boolean);
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      let hasNode = false;
      nids.forEach(nid => {{
        const card = svg.querySelector('#' + nid);
        if (!card) return;
        hasNode = true;
        const x = parseFloat(card.getAttribute('data-x'));
        const y = parseFloat(card.getAttribute('data-y'));
        const w = parseFloat(card.getAttribute('data-w'));
        const h = parseFloat(card.getAttribute('data-h'));
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x + w);
        maxY = Math.max(maxY, y + h);
      }});
      if (!hasNode) return;
      const padX = 20.0, padTop = 32.0, padBtm = 20.0;
      const rx = minX - padX;
      const ry = minY - padTop;
      const rw = (maxX - minX) + padX * 2;
      const rh = (maxY - minY) + padTop + padBtm;
      const rect = cGroup.querySelector('rect');
      if (rect) {{
        rect.setAttribute('x', rx.toFixed(1));
        rect.setAttribute('y', ry.toFixed(1));
        rect.setAttribute('width', rw.toFixed(1));
        rect.setAttribute('height', rh.toFixed(1));
      }}
      const txt = cGroup.querySelector('text');
      if (txt) {{
        txt.setAttribute('x', (rx + 14).toFixed(1));
        txt.setAttribute('y', (ry + 20).toFixed(1));
      }}
    }});
  }}

  // 全体表示 (Fit to View) の動的計算と適用
  function updateFitView() {{
    if (!isFitMode) return;
    const cards = svg.querySelectorAll('.sticky-card');
    if (!cards.length) return;
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    cards.forEach(card => {{
      const x = parseFloat(card.getAttribute('data-x'));
      const y = parseFloat(card.getAttribute('data-y'));
      const w = parseFloat(card.getAttribute('data-w'));
      const h = parseFloat(card.getAttribute('data-h'));
      if (!isNaN(x) && !isNaN(y) && !isNaN(w) && !isNaN(h)) {{
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x + w);
        maxY = Math.max(maxY, y + h);
      }}
    }});

    svg.querySelectorAll('.aether-container rect').forEach(rect => {{
      const x = parseFloat(rect.getAttribute('x'));
      const y = parseFloat(rect.getAttribute('y'));
      const w = parseFloat(rect.getAttribute('width'));
      const h = parseFloat(rect.getAttribute('height'));
      if (!isNaN(x) && !isNaN(y) && !isNaN(w) && !isNaN(h)) {{
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x + w);
        maxY = Math.max(maxY, y + h);
      }}
    }});

    const pad = 50.0;
    const fitX = Math.max(0, minX - pad);
    const fitY = Math.max(0, minY - pad);
    const fitW = (maxX - minX) + pad * 2;
    const fitH = (maxY - minY) + pad * 2;

    svg.setAttribute('viewBox', `${{fitX.toFixed(1)}} ${{fitY.toFixed(1)}} ${{Math.max(fitW, 400).toFixed(1)}} ${{Math.max(fitH, 300).toFixed(1)}}`);
    
    const wrapper = svg.closest ? svg.closest('.aether-canvas-wrapper') : document.querySelector('.aether-canvas-wrapper');
    if (wrapper) {{
      wrapper.style.height = `${{Math.min(initViewH, 540)}}px`;
    }}
  }}

  window.__toggleFitView = function() {{
    isFitMode = !isFitMode;
    const btn = document.getElementById('btn-toggle-fit');
    const wrapper = svg.closest ? svg.closest('.aether-canvas-wrapper') : document.querySelector('.aether-canvas-wrapper');
    if (isFitMode) {{
      if (btn) {{
        btn.textContent = '📐 1:1';
        btn.style.background = 'rgba(0,0,0,0.08)';
      }}
      updateFitView();
    }} else {{
      if (btn) {{
        btn.textContent = '🔍 全体 (Fit)';
        btn.style.background = 'transparent';
      }}
      svg.setAttribute('viewBox', `0 0 ${{initViewW}} ${{initViewH}}`);
      if (wrapper) {{
        wrapper.style.height = `${{initViewH}}px`;
      }}
    }}
  }};

  // 詳細インスペクターの更新
  window.__selectNode = function(nid) {{
    currentFocusId = nid;
    svg.querySelectorAll('.sticky-card').forEach(c => c.classList.remove('focused'));
    const targetCard = svg.querySelector('#' + nid);
    if (targetCard) targetCard.classList.add('focused');

    const meta = nodeMeta[nid];
    const insp = inspector || document.getElementById('aether-inspector');
    if (!meta || !insp) return;

    const b = document.getElementById('insp-badge');
    const t = document.getElementById('insp-title');
    const s = document.getElementById('insp-sub');
    const d = document.getElementById('insp-desc');
    if (b) b.textContent = meta.id.toUpperCase();
    if (t) t.textContent = meta.title;
    if (s) s.textContent = meta.subtitle || '—';
    if (d) d.textContent = meta.desc;

    // 接続エッジの構築
    const edgeContainer = document.getElementById('insp-edges');
    if (edgeContainer) {{
      edgeContainer.innerHTML = '';
      try {{
        const inEdges = edgesList.filter(e => e.dst === nid);
        const outEdges = edgesList.filter(e => e.src === nid);

        if (!inEdges.length && !outEdges.length) {{
          edgeContainer.innerHTML = '<span style="color:#94a3b8;">（接続エッジなし）</span>';
        }} else {{
          inEdges.forEach(e => {{
            const div = document.createElement('div');
            div.style.padding = '2px 0';
            div.innerHTML = '⬅️ <strong>' + e.src + '</strong> から ' + (e.lbl ? '<span style="opacity:0.85;">[' + e.lbl + ']</span>' : '');
            edgeContainer.appendChild(div);
          }});
          outEdges.forEach(e => {{
            const div = document.createElement('div');
            div.style.padding = '2px 0';
            div.innerHTML = '➡️ <strong>' + e.dst + '</strong> へ ' + (e.lbl ? '<span style="opacity:0.85;">[' + e.lbl + ']</span>' : '');
            edgeContainer.appendChild(div);
          }});
        }}
      }} catch (err) {{
        console.error('Edge render error:', err);
      }}
    }}

    insp.classList.add('open');
    insp.style.transform = 'translateX(0)';
    insp.style.opacity = '1';
    insp.style.pointerEvents = 'auto';
  }};

  window.__closeInspector = function() {{
    const insp = inspector || document.getElementById('aether-inspector');
    if (insp) {{
      insp.classList.remove('open');
      insp.style.transform = 'translateX(320px)';
      insp.style.opacity = '0';
      insp.style.pointerEvents = 'none';
    }}
    svg.querySelectorAll('.sticky-card').forEach(c => c.classList.remove('focused'));
    currentFocusId = null;
  }};

  // キーボードナビゲーション (矢印キー ↑↓←→)
  window.addEventListener('keydown', e => {{
    if (!['ArrowRight', 'ArrowLeft', 'ArrowDown', 'ArrowUp', 'Escape'].includes(e.key)) return;
    if (e.target && ['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;

    if (e.key === 'Escape') {{
      window.__closeInspector();
      return;
    }}

    e.preventDefault();
    if (!nodeIds.length) return;

    if (!currentFocusId) {{
      window.__selectNode(nodeIds[0]);
      return;
    }}

    const currCard = svg.querySelector('#' + currentFocusId);
    if (!currCard) return;

    const curX = parseFloat(currCard.getAttribute('data-x')) + parseFloat(currCard.getAttribute('data-w')) / 2;
    const curY = parseFloat(currCard.getAttribute('data-y')) + parseFloat(currCard.getAttribute('data-h')) / 2;

    let bestId = null;
    let minScore = Infinity;

    nodeIds.forEach(id => {{
      if (id === currentFocusId) return;
      const c = svg.querySelector('#' + id);
      if (!c) return;
      const nx = parseFloat(c.getAttribute('data-x')) + parseFloat(c.getAttribute('data-w')) / 2;
      const ny = parseFloat(c.getAttribute('data-y')) + parseFloat(c.getAttribute('data-h')) / 2;
      const dx = nx - curX;
      const dy = ny - curY;

      let valid = false;
      let score = Infinity;

      if (e.key === 'ArrowRight' && dx > 20) {{
        valid = true;
        score = Math.hypot(dx, dy * 1.8);
      }} else if (e.key === 'ArrowLeft' && dx < -20) {{
        valid = true;
        score = Math.hypot(-dx, dy * 1.8);
      }} else if (e.key === 'ArrowDown' && dy > 20) {{
        valid = true;
        score = Math.hypot(dx * 1.8, dy);
      }} else if (e.key === 'ArrowUp' && dy < -20) {{
        valid = true;
        score = Math.hypot(dx * 1.8, -dy);
      }}

      if (valid && score < minScore) {{
        minScore = score;
        bestId = id;
      }}
    }});

    if (bestId) {{
      window.__selectNode(bestId);
    }}
  }});

  // 整列機能
  window.__realignAether = function(mode) {{
    const inDeg = {{}};
    const adj = {{}};
    nodeIds.forEach(id => {{ inDeg[id] = 0; adj[id] = []; }});
    edgesList.forEach(e => {{
      if (inDeg[e.dst] !== undefined) inDeg[e.dst]++;
      if (adj[e.src] !== undefined) adj[e.src].push(e.dst);
    }});

    if (mode === 'radial') {{
      let maxDeg = -1, center = nodeIds[0];
      nodeIds.forEach(id => {{
        const deg = (inDeg[id] || 0) + (adj[id] ? adj[id].length : 0);
        if (deg > maxDeg) {{ maxDeg = deg; center = id; }}
      }});
      const outers = nodeIds.filter(id => id !== center);
      const cx = 460, cy = 240, r = Math.max(190, outers.length * 36);

      const cCard = svg.querySelector('#' + center);
      const cw = parseFloat(cCard.getAttribute('data-w')) || 190;
      const ch = parseFloat(cCard.getAttribute('data-h')) || 90;
      if (cCard) applyCardPos(cCard, cx - cw / 2, cy - ch / 2);

      outers.forEach((id, i) => {{
        const card = svg.querySelector('#' + id);
        if (!card) return;
        const w = parseFloat(card.getAttribute('data-w')) || 190;
        const h = parseFloat(card.getAttribute('data-h')) || 90;
        const angle = (2 * Math.PI * i) / outers.length;
        applyCardPos(card, cx + r * Math.cos(angle) - w / 2, cy + r * Math.sin(angle) - h / 2);
      }});
    }} else {{
      const rank = {{}};
      nodeIds.forEach(id => rank[id] = 0);
      let q = nodeIds.filter(id => inDeg[id] === 0);
      if (!q.length) q = [...nodeIds];
      const visited = new Set();
      while (q.length) {{
        const curr = q.shift();
        visited.add(curr);
        (adj[curr] || []).forEach(nbr => {{
          if (rank[nbr] < rank[curr] + 1) rank[nbr] = rank[curr] + 1;
          if (!visited.has(nbr) && !q.includes(nbr)) q.push(nbr);
        }});
      }}
      const groups = {{}};
      nodeIds.forEach(id => {{
        const r = rank[id];
        groups[r] = groups[r] || [];
        groups[r].push(id);
      }});

      let maxGroupSize = 1;
      Object.values(groups).forEach(g => {{ maxGroupSize = Math.max(maxGroupSize, g.length); }});

      Object.entries(groups).forEach(([rStr, ids]) => {{
        const r = parseInt(rStr, 10);
        ids.forEach((id, idx) => {{
          const card = svg.querySelector('#' + id);
          if (!card) return;
          if (mode === 'LR') {{
            const totalH = ids.length * 130;
            const offsetY = (maxGroupSize * 130 - totalH) / 2.0;
            applyCardPos(card, 60 + r * 270, 60 + offsetY + idx * 130);
          }} else {{
            const totalW = ids.length * 270;
            const offsetX = (maxGroupSize * 270 - totalW) / 2.0;
            applyCardPos(card, 60 + offsetX + idx * 270, 60 + r * 130);
          }}
        }});
      }});
    }}

    let step = 0;
    const animInterval = setInterval(() => {{
      updateEdges();
      updateContainers();
      step++;
      if (step > 15) {{
        clearInterval(animInterval);
        if (isFitMode) updateFitView();
      }}
    }}, 20);
  }};

  // 現在の手動配置のまま単体HTMLとして保存
  window.__exportCurrentLayoutHTML = function() {{
    const wrapper = svg.closest ? svg.closest('.aether-canvas-wrapper') : document.querySelector('.aether-canvas-wrapper');
    if (!wrapper) return;

    const clone = wrapper.cloneNode(true);
    const cloneInsp = clone.querySelector('#aether-inspector');
    if (cloneInsp) {{
      cloneInsp.classList.remove('open');
      cloneInsp.style.transform = 'translateX(320px)';
      cloneInsp.style.opacity = '0';
      cloneInsp.style.pointerEvents = 'none';
    }}
    clone.querySelectorAll('.sticky-card').forEach(c => c.classList.remove('focused'));

    const docStr = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Aether Graph Flow (Custom Layout)</title>
  <style>
    body {{{{
      background: {th['bg']};
      background-image: radial-gradient({th['grid']} 1px, transparent 1px);
      background-size: 20px 20px;
      padding: 30px;
      margin: 0;
      font-family: system-ui, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      box-sizing: border-box;
    }}}}
  </style>
</head>
<body>
  ${{clone.outerHTML}}
</body>
</html>`;

    const blob = new Blob([docStr], {{ type: 'text/html;charset=utf-8' }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'aether_{theme_key}_custom_layout.html';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }};

  // 手書き風スケッチモードの切り替え
  window.__toggleSketchMode = function() {{
    svg.classList.toggle('sketch-mode');
    const btn = document.getElementById('btn-toggle-sketch');
    if (btn) {{
      btn.style.background = svg.classList.contains('sketch-mode') ? 'rgba(0,0,0,0.08)' : 'transparent';
    }}
  }};

  let isDragging = false;

  svg.querySelectorAll('.sticky-card').forEach(card => {{
    card.addEventListener('pointerdown', e => {{
      if (e.button !== 0) return;
      target = card;
      isDragging = false;
      pointerStart = {{ x: e.clientX, y: e.clientY }};
      card.style.transition = 'none';

      const rect = svg.getBoundingClientRect();
      const pt = svg.createSVGPoint();
      pt.x = e.clientX;
      pt.y = e.clientY;
      const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());
      offset.x = svgP.x - parseFloat(card.getAttribute('data-x'));
      offset.y = svgP.y - parseFloat(card.getAttribute('data-y'));
    }});
  }});

  window.addEventListener('pointermove', e => {{
    if (!target) return;
    const dist = Math.hypot(e.clientX - pointerStart.x, e.clientY - pointerStart.y);
    if (dist > 3) {{
      isDragging = true;
    }}
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());
    const nx = svgP.x - offset.x;
    const ny = svgP.y - offset.y;
    applyCardPos(target, nx, ny);
    updateEdges();
    updateContainers();
  }});

  window.addEventListener('pointerup', e => {{
    if (!target) return;
    const card = target;
    target = null;
    card.style.transition = 'transform 0.25s cubic-bezier(0.2, 0, 0, 1)';

    const dist = Math.hypot(e.clientX - pointerStart.x, e.clientY - pointerStart.y);
    // ドラッグ移動距離が手振れ範囲（6px未満）なら「クリック」と判定してパネルを開く
    if (!isDragging && dist < 6) {{
      window.__selectNode(card.id);
    }}
    if (isDragging && isFitMode) {{
      updateFitView();
    }}
    isDragging = false;
  }});

  window.addEventListener('pointercancel', e => {{
    if (target) {{
      target.style.transition = 'transform 0.25s cubic-bezier(0.2, 0, 0, 1)';
      target = null;
      isDragging = false;
    }}
  }});

  // キャンバスの背景クリック（カード以外）でインスペクターを閉じる
  svg.addEventListener('click', e => {{
    let el = e.target;
    let hitCard = false;
    while (el && el !== svg) {{
      if (el.classList && el.classList.contains('sticky-card')) {{
        hitCard = true;
        break;
      }}
      el = el.parentNode;
    }}
    if (!hitCard) {{
      window.__closeInspector();
    }}
  }});

  // 初期化時に Fit モードが有効なら適用
  if (isFitMode) {{
    updateFitView();
  }}
}})();
</script>'''


# ==========================================
# Graph 本体
# ==========================================
class Graph:
    def __init__(self, title: str = "Aether Flow"):
        self.title = title
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.containers: Dict[str, Container] = {}
        self.layout_mode: str = "LR"
        self.sketch_mode: bool = False
        self.fit_mode: bool = False

    def add_container(self, container: Container) -> 'Graph':
        self.containers[container.id] = container
        return self

    def add_node(self, node: Node) -> 'Graph':
        if node.widget and node.w == 190.0:
            node.w = 230.0
        self.nodes[node.id] = node
        return self

    def add_edge(self, source: str, target: str, label: str = "", dashed: bool = False, style: str = "bezier", color: Optional[str] = None) -> 'Graph':
        self.edges.append(Edge(source=source, target=target, label=label, dashed=dashed, style=style, color=color))
        return self

    def auto_layout(self, direction: Optional[str] = None, spacing_x: float = 270.0, spacing_y: float = 130.0, start_x: float = 60.0, start_y: float = 70.0):
        if not self.nodes:
            return

        direction = direction or self.layout_mode
        self.layout_mode = direction

        if direction == "radial":
            degrees = {nid: 0 for nid in self.nodes}
            for e in self.edges:
                if e.source in degrees: degrees[e.source] += 1
                if e.target in degrees: degrees[e.target] += 1

            center_nid = max(degrees.keys(), key=lambda k: degrees[k]) if degrees else list(self.nodes.keys())[0]
            outer_nids = [nid for nid in self.nodes if nid != center_nid]

            center_x = 460.0
            center_y = 250.0
            radius = max(210.0, len(outer_nids) * 36.0)

            self.nodes[center_nid].x = center_x - self.nodes[center_nid].w / 2.0
            self.nodes[center_nid].y = center_y - self.nodes[center_nid].h / 2.0

            for i, nid in enumerate(outer_nids):
                angle = (2.0 * math.pi * i) / len(outer_nids)
                nx = center_x + radius * math.cos(angle) - self.nodes[nid].w / 2.0
                ny = center_y + radius * math.sin(angle) - self.nodes[nid].h / 2.0
                self.nodes[nid].x = max(40.0, nx)
                self.nodes[nid].y = max(40.0, ny)
            return

        in_degree = {nid: 0 for nid in self.nodes}
        adj = {nid: [] for nid in self.nodes}
        for e in self.edges:
            if e.target in in_degree:
                in_degree[e.target] += 1
            if e.source in adj:
                adj[e.source].append(e.target)

        rank = {nid: 0 for nid in self.nodes}
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        if not queue:
            queue = list(self.nodes.keys())

        visited = set()
        while queue:
            curr = queue.pop(0)
            visited.add(curr)
            for neighbor in adj.get(curr, []):
                if rank[neighbor] < rank[curr] + 1:
                    rank[neighbor] = rank[curr] + 1
                if neighbor not in visited and neighbor not in queue:
                    queue.append(neighbor)

        ranks: Dict[int, List[str]] = {}
        for nid, r in rank.items():
            ranks.setdefault(r, []).append(nid)

        max_nodes_in_rank = max([len(nids) for nids in ranks.values()] + [1])

        for r, nids in sorted(ranks.items()):
            for idx, nid in enumerate(nids):
                node = self.nodes[nid]
                if direction == "LR":
                    node.x = start_x + r * spacing_x
                    total_h = len(nids) * spacing_y
                    offset_y = (max_nodes_in_rank * spacing_y - total_h) / 2.0
                    node.y = start_y + offset_y + idx * spacing_y
                else:
                    node.y = start_y + r * spacing_y
                    total_w = len(nids) * spacing_x
                    offset_x = (max_nodes_in_rank * spacing_x - total_w) / 2.0
                    node.x = start_x + offset_x + idx * spacing_x

    @staticmethod
    def calc_dynamic_ports(ux: float, uy: float, uw: float, uh: float, vx: float, vy: float, vw: float, vh: float):
        cx_u = ux + uw / 2.0
        cy_u = uy + uh / 2.0
        cx_v = vx + vw / 2.0
        cy_v = vy + vh / 2.0

        dx = cx_v - cx_u
        dy = cy_v - cy_u

        if abs(dx) >= abs(dy):
            if dx >= 0:
                p1 = (ux + uw, cy_u)
                p2 = (vx, cy_v)
                dist = max(40.0, abs(dx) * 0.45)
                c1 = (p1[0] + dist, p1[1])
                c2 = (p2[0] - dist, p2[1])
            else:
                p1 = (ux, cy_u)
                p2 = (vx + vw, cy_v)
                dist = max(40.0, abs(dx) * 0.45)
                c1 = (p1[0] - dist, p1[1])
                c2 = (p2[0] + dist, p2[1])
        else:
            if dy >= 0:
                p1 = (cx_u, uy + uh)
                p2 = (cx_v, vy)
                dist = max(40.0, abs(dy) * 0.45)
                c1 = (p1[0], p1[1] + dist)
                c2 = (p2[0], p2[1] - dist)
            else:
                p1 = (cx_u, uy)
                p2 = (cx_v, vy + vh)
                dist = max(40.0, abs(dy) * 0.45)
                c1 = (p1[0], p1[1] - dist)
                c2 = (p2[0], p2[1] + dist)

        d = f"M {p1[0]:.1f} {p1[1]:.1f} C {c1[0]:.1f} {c1[1]:.1f}, {c2[0]:.1f} {c2[1]:.1f}, {p2[0]:.1f} {p2[1]:.1f}"
        mid_x = (p1[0] + p2[0]) / 2.0
        mid_y = (p1[1] + p2[1]) / 2.0 - 8.0
        return d, mid_x, mid_y

    def to_svg(self, width: int = 980, height: int = 480, interactive: bool = True, theme_key: str = "academic_light", direction: Optional[str] = None, sketch: Optional[bool] = None, fit: Optional[bool] = None) -> str:
        """グラフ全体をSVGおよび完全自立型HTMLパーツとして出力"""
        self.auto_layout(direction=direction)
        th = THEMES.get(theme_key, THEMES["academic_light"])
        palette = th["palette"]
        sketch_active = self.sketch_mode if sketch is None else sketch
        sketch_cls = "sketch-mode" if sketch_active else ""
        fit_active = self.fit_mode if fit is None else fit

        max_x = max([n.x + n.w for n in self.nodes.values()] + [width - 60])
        max_y = max([n.y + n.h for n in self.nodes.values()] + [height - 60])
        view_w = int(max(width, max_x + 60))
        view_h = int(max(height, max_y + 60))
        wrapper_h = min(view_h, 540) if fit_active else view_h

        html_parts = []
        html_parts.append(f'<div class="aether-canvas-wrapper" style="width:100%; max-width:{view_w}px; height:{wrapper_h}px; min-height:{wrapper_h}px; background:{th["wrapper_bg"]}; border:1px solid {th["wrapper_border"]}; border-radius:16px; overflow:hidden; position:relative; box-shadow:{th["card_shadow"]}; transition:height 0.3s ease;">')
        html_parts.append(_build_css(th))

        if interactive:
            html_parts.append(_build_toolbar(th, sketch_active, fit_active))

        # SVGキャンバス描画
        svg_parts = [
            f'<svg id="aether-svg" class="{sketch_cls}" width="100%" height="100%" viewBox="0 0 {view_w} {view_h}" style="width:100%; height:100%; display:block; touch-action:none; user-select:none; background:{th["wrapper_bg"]};">',
            _build_defs(th),
            _build_containers_svg(self.containers, self.nodes, palette),
            _build_edges_svg(self.edges, self.nodes, th),
            _build_nodes_svg(self.nodes, palette, th, interactive),
            '</svg>'
        ]
        html_parts.append("\n".join(svg_parts))

        # インタラクティブUI（インスペクター・イベント制御スクリプト）
        if interactive:
            html_parts.append(_build_inspector_html(th))
            edge_pairs = [{"src": e.source, "dst": e.target, "lbl": e.label} for e in self.edges]
            node_meta_dict = {
                nid: {
                    "id": n.id,
                    "title": n.title,
                    "subtitle": n.subtitle,
                    "desc": n.desc or "詳細な記述はありません。",
                    "color": n.color,
                    "widget": n.widget
                }
                for nid, n in self.nodes.items()
            }
            html_parts.append(_build_client_script(list(self.nodes.keys()), node_meta_dict, edge_pairs, th, theme_key, init_view_w=view_w, init_view_h=view_h, fit_active=fit_active))

        html_parts.append('</div>')
        return "\n".join(html_parts)


# ==========================================
# DSLパーサー
# ==========================================
def parse_dsl(text: str, title: str = "Aether Flow") -> Graph:
    g = Graph(title=title)
    lines = [line.strip() for line in text.strip().splitlines() if line.strip() and not line.strip().startswith("#")]

    current_container_id = None
    container_counter = 0

    for line in lines:
        if line.startswith("@layout:"):
            g.layout_mode = line.split(":", 1)[1].strip().lower()
            continue

        if line.startswith("@sketch:"):
            val = line.split(":", 1)[1].strip().lower()
            g.sketch_mode = val in ["true", "1", "yes", "on"]
            continue

        if line.startswith("@fit:") or line.startswith("@view:"):
            val = line.split(":", 1)[1].strip().lower()
            g.fit_mode = val in ["true", "1", "yes", "on", "fit"]
            continue

        # コンテナブロック終了
        if line == "}":
            current_container_id = None
            continue

        # 1行コンテナ定義: group: "名前" | color=purple = [M1, DE4]
        if re.match(r'^(group|container):\s*.+=\s*\[', line, re.I):
            parts = line.split("=", 1)
            header_part = parts[0].split(":", 1)[1].strip()
            nodes_part = parts[1].strip()
            
            c_meta = {}
            c_title = header_part
            if "|" in header_part:
                c_title, c_meta_str = header_part.split("|", 1)
                c_title = c_title.strip().strip('"\'')
                for kv in c_meta_str.split(","):
                    if "=" in kv:
                        k, v = kv.split("=", 1)
                        c_meta[k.strip().lower()] = v.strip()
            else:
                c_title = c_title.strip().strip('"\'')

            c_nids = [n.strip() for n in nodes_part.strip("[]").split(",") if n.strip()]
            container_counter += 1
            cid = f"c{container_counter}"
            g.add_container(Container(
                id=cid,
                title=c_title,
                node_ids=c_nids,
                color=c_meta.get("color", "slate"),
                dashed=c_meta.get("dashed", "true").lower() in ("true", "1", "yes")
            ))
            continue

        # ブロックコンテナ開始: group: "名前" | color=purple {
        if re.match(r'^(group|container):\s*.+\{?$', line, re.I) and not re.search(r'(\-\>|\>\>)', line):
            header_part = line.split(":", 1)[1].rstrip("{").strip()
            c_meta = {}
            c_title = header_part
            if "|" in header_part:
                c_title, c_meta_str = header_part.split("|", 1)
                c_title = c_title.strip().strip('"\'')
                for kv in c_meta_str.split(","):
                    if "=" in kv:
                        k, v = kv.split("=", 1)
                        c_meta[k.strip().lower()] = v.strip()
            else:
                c_title = c_title.strip().strip('"\'')

            container_counter += 1
            current_container_id = f"c{container_counter}"
            g.add_container(Container(
                id=current_container_id,
                title=c_title,
                node_ids=[],
                color=c_meta.get("color", "slate"),
                dashed=c_meta.get("dashed", "true").lower() in ("true", "1", "yes")
            ))
            continue

        # ノード定義抽出
        node_defs = re.findall(r'\[([^\]]+)\]', line)
        for nd in node_defs:
            parts = nd.split(":", 1)
            nid = parts[0].strip()
            title_part = parts[1].strip() if len(parts) > 1 else nid
            
            meta = {}
            if "|" in title_part:
                title_clean, meta_str = title_part.split("|", 1)
                title_part = title_clean.strip()
                for kv in meta_str.split(","):
                    if "=" in kv:
                        k, v = kv.split("=", 1)
                        meta[k.strip().lower()] = v.strip()

            if nid not in g.nodes:
                g.add_node(Node(
                    id=nid,
                    title=title_part,
                    subtitle=meta.get("sub", ""),
                    desc=meta.get("desc", ""),
                    color=meta.get("color", "cyan"),
                    widget=meta.get("widget", "")
                ))

            if current_container_id and current_container_id in g.containers:
                if nid not in g.containers[current_container_id].node_ids:
                    g.containers[current_container_id].node_ids.append(nid)

        # エッジ定義抽出
        arrow_pattern = r'(\-\>|\>\>)'
        tokens = re.split(arrow_pattern, line)
        if len(tokens) >= 3:
            idx = 0
            curr_src = None
            pending_edge_label = ""
            pending_dashed = False

            while idx < len(tokens):
                tok = tokens[idx].strip()
                if tok in ("->", ">>"):
                    if tok == ">>":
                        pending_dashed = True
                elif tok.startswith("(") and tok.endswith(")"):
                    lbl_content = tok[1:-1].strip()
                    if ":dashed" in lbl_content:
                        pending_dashed = True
                        lbl_content = lbl_content.replace(":dashed", "").strip()
                    pending_edge_label = lbl_content
                else:
                    nid_match = re.search(r'\[([^:\]]+)', tok)
                    nid = nid_match.group(1).strip() if nid_match else tok.strip()
                    
                    if nid and nid in g.nodes:
                        if curr_src:
                            g.add_edge(curr_src, nid, label=pending_edge_label, dashed=pending_dashed)
                            pending_edge_label = ""
                            pending_dashed = False
                        curr_src = nid
                idx += 1

    return g
