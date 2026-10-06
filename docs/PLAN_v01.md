# Aether-next 実行計画 v01

承認: Captain 2026-10-07  
議論正本: our-room #30  
実装: J.T. · GitHub 閉じ役（予定）: Nova

## フェーズ

| Phase | 内容 | 状態 |
|---|---|---|
| 0 | 合意・スコープ v1（閲覧専用） | 完了 |
| 1 | `Tools/aether-next` 隔離・engine・legacy アダプタ・cockpit | **進行中** |
| 2 | DB 読取・ロール辞書・検索ビルダー・export 固定 | 未 |
| 3 | 三家検証・UX バックログ | 未 |
| 4 | LIVE 切替（Captain GO） | 未 |

## v1 スコープ

- Must: legacy `sticky`/`relation` + compact DSL → SVG、marimo コックピット
- Won't: IndexedDB 編集、DB 書き戻し、旧 UI 全機能パリティ、**DSL v2 互換**

## ゴールデンボード

- `aether_dsl_test.txt`
- `aether_dsl_succession_navi.txt`
- `aether_dsl.txt` (meta)
- `colonial_geopolitics_route`（Phase 2）

## 安全

- DB 読取のみ（Phase 2 以降も write は別ゲート）
- 旧 `Tools/aether` 無改変
- pytest スモーク + ノード/エッジカウント
