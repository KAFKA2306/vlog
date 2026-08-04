---
codd:
  node_id: "req:adr-0009"
  type: adr
  status: accepted
  links:
    - to: data/config.yaml
      type: configuration
    - to: apps/capture-vrchat/src/infrastructure/system.py
      type: implementation
    - evidence: "rg -n \"large-v3-turbo|compute_type|device|model_size\" data/config.yaml apps/capture-vrchat/src/infrastructure/system.py apps/capture-vrchat/src/infrastructure/README.md .claude/CLAUDE.md"
    ---


# ADR-0009: Whisper Large-v3-Turbo への移行による文字起こしの効率化

## ステータス

承認済み (Accepted)

## コンテキスト

VLog システムの文字起こしエンジンとして `large-v3` モデルを使用してきた。このモデルは極めて高い精度を持つ一方で、以下の課題に直面していた：

1. **高いリソース消費**: VRAM を 10GB 以上消費するため、VRChat や画像生成タスクと並行して動作させる際にリソース不足による不安定化のリスクがあった。
2. **推論速度のボトルネック**: 長時間の音声データを処理する際、数分から数十分の時間を要し、日次処理全体の完了を遅延させていた。
3. **過剰な精度**: 本システムにおける文字起こしは、Gemini による要約や小説化のための中間データであり、`large-v3` レベルの極限的な精度は必ずしも必要とされていなかった。

## 意思決定

推論効率と精度のバランスが最適化された最新の蒸留モデル **`large-v3-turbo`** へ移行する。

### 1. モデルの選定

- OpenAI が公開した `large-v3-turbo` を採用。
- `large-v3` の精度を維持しつつ、デコーダー層の削減により高速化を実現したモデルである。

### 2. パフォーマンスの最適化

- 推論エンジンとして `faster-whisper` を継続利用。
- `compute_type="float16"` および `device="cuda"` を明示的に設定し、GPU 性能を最大限に活用。
- モデルサイズを従来の約半分（約 800M パラメータ）に抑え、VRAM 使用量を約 6GB 前後まで低減。

### 3. 設定の統一

- `data/config.yaml` を唯一のソースオブトゥルースとし、CLI およびバックグラウンドサービスで一貫したモデルが使用されるように設定。

## 影響

- **メリット**:
  - 推論速度が従来の **約 8 倍** に向上し、日次処理時間が劇的に短縮される。
  - VRAM 使用量の削減により、マルチタスク環境下でのシステムの安定性が向上する。
  - `large-v2` 以上の精度を維持しており、後続の Gemini プロンプトへの入力品質に悪影響を与えない。
- **デメリット**:
  - 極めてノイズの多い環境や、非常に特殊な固有名詞の認識において、`large-v3` に比べ僅かに精度が低下する可能性がある。
