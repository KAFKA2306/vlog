---
name: python-coding-rules
description: Modern Python (uv, Ruff, Pydantic, ty) および Zero-Fat 原則に基づく高信頼性システムの設計・実装規約。
---

# Modern Python & Zero-Fat 規約

## 1. ツールチェーンの統合的最適化

### パッケージ・プロジェクト管理: uv
- **再現性**: `uv.lock` による決定論的な依存解決。CI/CD 環境を含め「環境の揺らぎ」を完全に排除する。
- **標準操作**: `uv add`, `uv sync`, `uv run` を基本とし、Python インタープリタ管理も `uv` に委譲する。

### 静的解析・フォーマット: Ruff
- **統合**: `pyproject.toml` で全 16 種の厳格なカテゴリ（TRY, PL, ANN 等）を有効化。
- **自動修正**: `uv run ruff check --fix` により規約違反を機械的に排除する。

### データモデル: Pydantic v2
- **定義**: `BaseModel` と `Annotated` を活用し、バリデーションロジックをモデルに内包。
- **不変性**: `frozen=True` を設定し、副作用を排除した予測可能なデータ境界を構築する。

### 型チェック: Pylance / ty
- **Any 禁止**: `typing.Any` の使用を完全に禁止（Ruff ANN401）。
- **フィードバック**: `ty` による超高速型検証を CI パイプラインに組み込む。

## 2. Zero-Fat 原則 (Core Philosophy)

### Fail Fast (例外処理の禁止)
- `try-except` によるエラー隠蔽を禁止。不具合は即座にクラッシュさせ、根本原因を早期に特定・修正する。

### Self-Documenting (コメント排除)
- コメントや docstring を「維持コストの高い不正確な情報」と見なし、排除する。命名と型システムによって意図を表現する。

### Success Path Only (ロジックの単純化)
- 関数本体は「正常系」のみをクリーンに記述。例外状況は境界やインフラ層に委譲する。

## 3. 実装上の要請
- 横断的関心事（ロギング等）はデコレータへ分離。
- 設定値は `config.yaml` に集約し、ハードコードを徹底排除。

---
*詳細規約: [docs/coding_rules.md](file:///home/kafka/projects/vlog/docs/coding_rules.md)*
