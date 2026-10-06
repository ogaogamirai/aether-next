# 三家共通インストール（aether-next Phase 1）

## 前提

- Python 3.11+
- ネットワーク（`pip install marimo`）

## 手順

```powershell
cd "G:\マイドライブ\Tools\aether-next"
python -m pip install -e ".[dev]"
marimo edit apps/cockpit.py
```

ブラウザが開いたら、ドロップダウンで `legacy: aether_dsl_test` などを選択。

## トラブル

- **Drive パス:** ボードプリセットは Windows 絶対パス。Mac/Linux 家は `apps/cockpit.py` の `_DEFAULT_BOARDS` を各自パスに変更（Phase 2 で `--home` 化予定）。
- **旧 LIVE:** 引き続き `Tools/aether` + `aetherdb project` を使用。
