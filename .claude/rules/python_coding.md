# Coding Rules & Principles

## Python Implementation

- **Python 3.11+**, type hints everywhere.
- 4-space indentation.
- `snake_case` (functions/modules), `PascalCase` (classes), `UPPERCASE` (constants).
- **Silent Operator**: コード自体をドキュメントとして機能させ、コメントやdocstringは省略します。これはLLMのコンテキストを節約し、本質的なロジックのみに集中させるためです。
- **Zero-Fat**: 
    - try-exceptブロックは使用せず、失敗時は素直にクラッシュさせます。エラーの根本原因を隠蔽せず、上位レイヤーに確実に関知させるのが目的です。
    - リトライやタイムアウトのロジックはインフラ側に委ね、コードには含めません。複雑さを排除し状態の蓄積を防ぎます。
    - 生の辞書（dict）ではなく `src/models.py` のPydanticモデルを使用し、型の安全性を担保します。
- **Success Path Only**: インフラ層やリポジトリ層の実装は正常系のみを記述し、過剰な防御的プログラミングを避けてシンプルに保ちます。

## Linting & Formatting

- Tool: `ruff`
- Command: `uv run ruff check src` & `uv run ruff format src`

## Directory Structure Enforcement

- `src/domain/`: Entities & Interfaces.
- `src/use_cases/`: Core logic.
- `src/infrastructure/`: Port implementations.
- `src/models.py`: Shared data models.
- **Avoid root file creation**.
