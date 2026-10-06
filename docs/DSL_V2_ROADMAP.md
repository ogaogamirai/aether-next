# DSL v2 精錬（将来目標）

Captain 合意: **v1 では legacy v3/v4 をアダプタ経由で読むのみ**。記法の美しい統一は v2 で別設計。

## なぜ後回しにするか

- 現行 export は `sticky` / `relation` / `drawing` が混在し、JS パーサーと 10k 行 UI が暗黙仕様になっている
- compact DSL（`[ID: title | ...]`）はプロトタイプ用に別系統
- 「互換をコンパクトに美しく」は **二重 AST + 段階的 deprecate** が必要で、描画エンジン刷新と同時だとリスクが倍になる

## v2 で検討する軸

| 軸 | 方向性（草案） |
|---|---|
| 記法 | 1 ノード 1 行 + ブロック最小（YAML 風は避け、diff しやすい） |
| 拡張性 | `@directive` と `builder` 登録（エンジン側） |
| 可読性 | `role`/`time` を first-class、長文は `|` 折り畳み参照 |
| 記述容易さ | marimo セルから snippet 生成、CLI `aetherdb project --format v2` は **Phase 5** |

## 移行イメージ（将来）

1. v2 正本 + v3/v4 **import only**（legacy → IR）
2. export は v2 既定、v3 shim は 1 リリース cycle
3. 破壊変更は our-room + KNOW で版管理

v1 の `aether_next.load.detect_format` に v2 分岐を足すだけで足せる構造にする。
