# 画像生成サブシステム詳細仕様書 (Image Generation Subsystem Internal Specification)

> マスタードキュメント → [docs/overview.md](file:///home/kafka/projects/vlog/docs/overview.md)  
> 開発ガイド → [AGENTS.md](file:///home/kafka/projects/vlog/AGENTS.md)

このドキュメントは、Vlogプロジェクトにおける画像生成サブシステム（Image Generation Subsystem）の技術仕様、アーキテクチャ、運用、およびトラブルシューティングに関する包括的なリファレンスです。

## 目次

1. [システム概要](#システム概要)
2. [技術アーキテクチャ](#技術アーキテクチャ)
3. [詳細処理フロー](#詳細処理フロー)
4. [プロンプトエンジニアリング戦略](#プロンプトエンジニアリング戦略)
5. [設定パラメータリファレンス](#設定パラメータリファレンス)
6. [データモデルとディレクトリ構造](#データモデルとディレクトリ構造)
7. [使用モデル詳細](#使用モデル詳細)
8. [手動操作とCLIツール](#手動操作とcliツール)
9. [トラブルシューティングとFAQ](#トラブルシューティングとfaq)

---

## 1. システム概要

Vlogの画像生成サブシステムは、日々の活動ログ（音声認識→要約→小説化）の最終工程として機能し、その日の出来事や感情を視覚的に表現するデジタルアートを生成します。

本システムの設計思想は「物語の文脈を汲み取った高品質イラストの自動生成」です。LLM（Gemini 3 Flash）を用いて小説の文章から「視覚的に映える要素」を自然言語で抽出し、それを最新の画像生成AI（Z-Image-Turbo）に渡すことで、一貫性と美観を兼ね備えた画像を生成します。

---

## 2. 技術アーキテクチャ

### 2.1 コンポーネント構成

| コンポーネント | 実装 | 役割 |
|---|---|---|
| Orchestrator | `BuildNovelUseCase` (`src/use_cases/build_novel.py`) | プロセス全体の指揮者。小説生成完了をトリガーとして画像生成を開始 |
| Core Generator | `ImageGenerator` (`src/infrastructure/ai.py`) | 画像生成ロジックの本体。プロンプト構築、モデルロード、推論実行、ファイル保存を一元管理 |
| Prompt Engineer | `JulesClient` (`src/infrastructure/ai.py`) | Gemini 3 Flash APIへのインターフェース。「アートディレクター」として自然言語の小説を画像プロンプトへ変換 |
| Inference Engine | `Hugging Face Diffusers` | Z-Image-Turboを使用。PyTorchバックエンド上でCUDAアクセラレーションを活用 |

### 2.2 依存ライブラリ

- Python: 3.11+
- Torch: 2.5.1+ (CUDA 12.x)
- Diffusers: 最新版 (Gitベース推奨)
- Transformers: 4.46.3+
- Accelerate: 1.1.1+
- Google Generative AI: 0.8.0+

---

## 3. 詳細処理フロー

```mermaid
sequenceDiagram
    participant Orchestrator as BuildNovelUseCase
    participant Generator as ImageGenerator
    participant LLM as JulesClient (Gemini 3 Flash)
    participant Pipeline as Z-Image-Turbo

    Note over Orchestrator: 小説生成完了通知
    Orchestrator->>Generator: generate_from_novel(full_text, output_path)
    
    rect rgb(20, 20, 40)
        Note right of Generator: Phase 1: Context Analysis
        Generator->>LLM: generate_image_prompt(full_text)
        LLM->>LLM: Analyze Context & Mood
        LLM->>LLM: Extract Visual Elements
        LLM-->>Generator: return natural language description
    end

    rect rgb(40, 40, 20)
        Note right of Generator: Phase 2: Prompt Engineering
        Generator->>Generator: Remove Ban-words (pig, translucent, etc.)
        Generator->>Generator: Apply Template
        Generator->>Generator: Load Negative Prompt
    end

    rect rgb(20, 40, 20)
        Note right of Generator: Phase 3: Generation (Inference)
        Generator->>Pipeline: Check Model Cache / Load Model
        Pipeline->>Pipeline: Move to CUDA (bfloat16)
        Generator->>Pipeline: __call__(prompt, neg_prompt, ...)
        
        loop Denoising Steps (9 steps)
            Pipeline->>Pipeline: Transformer Prediction
            Pipeline->>Pipeline: Scheduler Step
        end
        
        Pipeline-->>Generator: return PIL.Image
    end

    rect rgb(40, 20, 20)
        Note right of Generator: Phase 4: Persistence
        Generator->>Generator: Save Image (PNG)
        Generator->>Generator: Save Prompt Log (TXT)
    end
```

### 3.1 Phase 1: Context Analysis

小説の全文（最大2000文字）を `JulesClient` に渡します。
Gemini 3 Flash は以下の要素を自然言語で記述します。

- 被写体: 外見、服装、ポーズ、表情
- 場所・環境: 屋内/屋外、場所の種類、時間帯、天候
- 雰囲気: 色調、照明効果、構図

### 3.2 Phase 2: Prompt Engineering

LLMから返された自然言語プロンプトに対し、以下の処理を行います。

1. 禁止語フィルタリング: 特定の不要な語句をフィルタリング
   - `pig`, `swine`, `hog`, `boar`, `piglet`
   - `translucent`, `transparent`, `semi-transparent`, `ethereal`

2. テンプレート適用: シンプルなパススルー（`{text}` のみ）

3. ネガティブプロンプト: 最小限の品質ガード

### 3.3 Phase 3: Generation

組み立てられたプロンプトとネガティブプロンプトを用いて画像生成を実行します。
プロセスは GPU (CUDA) 上で `bfloat16` 精度で計算されます。

---

## 4. プロンプトエンジニアリング戦略

本システムでは「自然言語プロンプティング」を採用しています。これはGoogle Imagen / Gemini Image 系モデルのベストプラクティスに基づいています。

### 4.1 image_prompt テンプレート

```yaml
jules:
  image_prompt: |
    You are an expert art director. Read the novel text and extract key visual elements 
    to create a structured image prompt using descriptive natural language sentences.

    Output Rules:
    - Output a detailed, descriptive natural language prompt.
    - Describe the subject, action, lighting, and atmosphere in a cohesive paragraph.
    - Focus on physical descriptions and visual details.

    Detailed Instructions:
    - Focus on the visual core of the scene.
    - If specific details are missing, creatively infer them to match the mood.
    - STRICTLY PROHIBITED: Terms referencing the virtual/digital nature of the platform.
    - Avoid cliche tags like "coffee" or "steam" unless essential.

    Novel Text:
    {chapter_text}

    Output: natural_language_description
```

### 4.2 image_generator テンプレート

```yaml
image_generator:
  template: |
    {text}
  negative_prompt: |
    low quality, ugly, distorted, blurry, bad anatomy, bad hands, text, watermark
```

従来のDanbooruタグ形式から脱却し、自然言語による記述を採用しています。

---

## 5. 設定パラメータリファレンス

設定は `src/infrastructure/settings.py` および `data/config.yaml` で管理されています。

### 5.1 現在の設定値

| パラメータ | 設定キー | 現在値 | 説明 |
|---|---|---|---|
| Model ID | `image.model` | `Tongyi-MAI/Z-Image-Turbo` | Z-Image-Turbo (Flow Matching) |
| Device | `image.device` | `cuda` | 計算デバイス |
| Width | `image.width` | `1024` | 生成画像の幅 |
| Height | `image.height` | `1024` | 生成画像の高さ |
| Steps | `image.num_inference_steps` | `9` | ノイズ除去ステップ数 (Turboモデル向け) |
| Guidance Scale | `image.guidance_scale` | `0.0` | CFG無効 (Flow Matchingの特性) |
| Seed | `image.seed` | `42` | 乱数シード (実行時にランダム化) |

### 5.2 Gemini設定

| パラメータ | 設定キー | 現在値 |
|---|---|---|
| Model | `gemini.model` | `models/gemini-3-flash-preview` |

---

## 6. データモデルとディレクトリ構造

### 6.1 ファイルシステム

```
data/
├── photos/                  # 生成された画像ファイル
│   ├── 20251201.png
│   └── ...
└── photos_prompts/          # 生成時のプロンプトログ
    ├── 20251201.txt
    └── ...
```

### 6.2 データベース (Supabase)

生成された画像のパスは `novels` テーブルに紐付けられます。

- `image_url`: 生成された画像のストレージパス

---

## 7. 使用モデル詳細

### 7.1 現在の設定: Z-Image-Turbo

| 項目 | 値 |
|---|---|
| Model ID | `Tongyi-MAI/Z-Image-Turbo` |
| アーキテクチャ | Flow Matching (DiT系) |
| テキストエンコーダ | Qwen3系 (約4Bパラメータ) |
| 推奨ステップ数 | 8-10 |
| 推奨VRAM | 16GB |
| Guidance Scale | 0.0 (CFG不要) |

> [!CAUTION]
> Z-Image-Turboは巨大なQwen3テキストエンコーダを使用するため、メモリ消費が大きくなります。
> VRAM不足時にはOOMが発生する可能性があります。

### 7.2 代替モデル: Animagine XL 3.1

RAM/VRAM制約がある環境では、従来のAnimagine XL 3.1を使用できます。

```yaml
image:
  model: "cagliostrolab/animagine-xl-3.1"
  num_inference_steps: 28
  guidance_scale: 7.0
```

---

## 8. 手動操作とCLIツール

### 8.1 単一画像生成

```bash
# 小説ファイルから画像生成
task photo novel=data/novels/20251201.md

# 全小説から一括生成
task photos
```

### 8.2 汎用画像生成スクリプト

```bash
uv run python scripts/generate_image.py "テキストプロンプト" 出力パス.png
uv run python scripts/generate_image.py data/novels/20251201.md test_output.png
```

### 8.3 ヘッダー画像合成

```bash
uv run python scripts/create_composite_header.py data/photos/img1.png data/photos/img2.png --output header.png
```

---

## 9. トラブルシューティングとFAQ

### Q1. "CUDA out of memory" エラー

対策:
1. `torch_dtype=torch.bfloat16` が設定されているか確認
2. `device_map="balanced"` でモデルオフロードを有効化
3. 他のGPUプロセスを終了

### Q2. 生成された画像が崩れている

対策:
1. ネガティブプロンプトを確認
2. 解像度を1024x1024に維持
3. ステップ数を増加 (9→12)

### Q3. 生成が極端に遅い

対策:
1. `nvidia-smi` でGPU認識を確認
2. `image.device` が `cuda` か確認
3. PyTorchがCUDA版か確認

### Q4. 全く関係ない画像が生成される

対策:
1. `data/photos_prompts/` のログを確認
2. `data/prompts.yaml` の `image_prompt` を調整

---

*Document Revision: 2.0.0*
*Last Updated: 2026-01*
