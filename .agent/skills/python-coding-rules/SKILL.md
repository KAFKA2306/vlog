---
name: python-coding-rules
description: 本プロジェクトの Modern Python (uv, Ruff, Pydantic, Pylance/ty) および Zero-Fat 原則に基づくコーディング規約。
---

# Python コーディング規約 (Modern & Zero-Fat)

## 概要
本スキルは、プロジェクト内の Python コードの品質、一貫性、および「無駄を削ぎ落とした」保守性を維持するためのガイドラインを提供します。

## 1. ツールチェーン (Toolchain)

### パッケージ・プロジェクト管理: uv
- **標準操作**: `uv add`, `uv sync`, `uv run` を使用。
- **再現性**: `uv.lock` を常にリポジトリに含める。

### 静的解析・フォーマット: Ruff & Pyright
- **Lint**: `task lint` でフォーマット、Lint、型チェックを一括実行。
- **構成**: `pyproject.toml` で全 16 種の厳格なカテゴリ（TRY, PL, ERA等）を有効化。

### データモデル・バリデーション: Pydantic v2
- **定義**: `BaseModel` と `Annotated` を活用した厳格な型定義。
- **原則**: `model_validate`, `model_dump` を基本とし、副作用を避けるため `frozen` 設定を推奨。

### 型チェック: Pylance / ty
- **標準**: `Pylance` (VS Code) と `Pyright` を使用。
- **Any 禁止**: `typing.Any` の使用を完全に禁止し、厳格な型指定を行う。
- **次世代**: `ty` (Astral製) を活用した超高速チェックも検討。

## 2. Zero-Fat 原則 (Core Philosophy)

### Fail Fast (例外処理の禁止)
- **原則**: `try-except` によるエラーハンドリングを禁止する。不具合は即座にクラッシュさせ、根本原因を修正する。

### Self-Documenting (コメント禁止)
- **原則**: コード自体が目的を説明する命名・構造にする。docstring や日本語コメントを排除し、コードの純度を高める。

### Zero-Hardcoding (外部構成)
- **原則**: すべての設定値は `config.yaml` に集約し、ハードコードを徹底排除する。

### Success Path Only (ロジックの単純化)
- **原則**: リトライや冗長なタイムアウト処理を排除し、正常系（Success Path）のみをクリーンに記述する。

## 3. 実装パターン (Patterns)

### デコレータの活用
- ロギングや認証などの横断的な関心事はデコレータに分離し、関数本体はビジネスロジックに集中させる。

### 不変性の優先
- `tuple`, `NamedTuple`, Pydantic の `frozen` モデルを優先し、状態の予測可能性を高める。

---
*参照ドキュメント: [docs/coding_rules.md](file:///home/kafka/projects/vlog/docs/coding_rules.md)*
