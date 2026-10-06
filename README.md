# aether-next

Aether UI の **並行サンドボックス**（our-room [#30](https://github.com/ogaogamirai/our-room/issues/30) 承認済み）。

- **正本 UI（本番）:** `G:\マイドライブ\Tools\aether` — Phase 4 まで触らない
- **本パッケージ:** marimo コックピット + 単一 SVG エンジン + **legacy DSL v3/v4 アダプタ**
- **将来:** DSL v2 精錬（`docs/DSL_V2_ROADMAP.md`）— v1 は読取・描画のみ

## クイックスタート

```powershell
cd "G:\マイドライブ\Tools\aether-next"
python -m pip install -e ".[dev]"
marimo edit apps/cockpit.py
```

## テスト

```powershell
python -m pytest -q
```

## 閉じ役（GitHub）

初回リポ作成・push は **Nova**（Aether 系）— 実装 J.T. との分担は #30 で記録。
