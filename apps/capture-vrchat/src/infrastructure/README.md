# infrastructure

外部依存の実装層。Domain層のインターフェースを実装。

## ファイル一覧

| ファイル | クラス/関数 | 責務 |
|----------|------------|------|
| `ai.py` | `JulesClient` | Jules AI連携（タスク解析、チャット、画像プロンプト生成） |
| `ai.py` | `ImageGenerator` | Stable Diffusion画像生成 |
| `ai.py` | `Novelizer` | Gemini小説生成 |
| `ai.py` | `Summarizer` | Gemini要約生成 |
| `ai.py` | `Curator` | コンテンツ品質評価 |
| `observability.py` | `TraceLogger` | AIトレースログ記録（latency, chars） |
| `repositories.py` | `FileRepository` | ファイル操作（読み書き、アーカイブ） |
| `repositories.py` | `TaskRepository` | タスクJSON永続化 |
| `repositories.py` | `SupabaseRepository` | Supabase同期 |
| `settings.py` | `Settings` | Pydantic設定クラス |
| `system.py` | `AudioRecorder` | 録音（FLAC保存） |
| `system.py` | `Transcriber` | Faster Whisper文字起こし |
| `system.py` | `ProcessMonitor` | VRChatプロセス監視 |
| `system.py` | `TranscriptPreprocessor` | フィラー除去、重複削除 |

## 設定パラメータ詳細

### Audio設定 (`config.yaml` → `AudioRecorder`)

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| `sample_rate` | 16000 | Whisper最適化サンプリングレート |
| `channels` | 1 | モノラル（音声認識に最適） |
| `block_size` | 1024 | 1回の読み取りサンプル数 |
| `SILENCE_THRESHOLD` | 0.02 | RMS閾値（無音判定、録音サイズ削減） |

### Whisper設定 (`config.yaml` → `Transcriber`)

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| `model_size` | large-v3-turbo | 高速・高精度モデル |
| `device` | cpu | 実行デバイス（cuda対応可） |
| `compute_type` | int8 | CPU向け量子化（メモリ削減） |
| `beam_size` | 5 | ビームサーチ幅（精度向上） |
| `vad_filter` | true | Voice Activity Detection有効化 |
| `vad_min_silence_duration_ms` | 100 | 無音判定最小時間 |
| `vad_speech_pad_ms` | 360 | 音声前後のパディング |
| `language` | ja | 日本語固定 |
| `temperature` | 0.0 | 決定論的出力 |
| `repetition_penalty` | 1.08 | 繰り返し抑制 |

### フィラー除去リスト (`TranscriptPreprocessor.FILLERS`)

```
えー, あのー, うーん, えっと, なんて, まあ, そうですね, あー, んー, うん,
ふん, あ, はは, ははは, なんか, え, お, ふんふん, ふんふんふん,
うんうん, うんうんうん, はいはい, はいはいはい, はいはいはいはい,
おー, ああ, んふん, そっか, そっかぁ, そうか, そうなんだ, えへへ,
あの, あのね, あのさ, ん
```

### 画像生成設定 (`config.yaml` → `ImageGenerator`)

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| `model` | Tongyi-MAI/Z-Image-Turbo | 高速推論モデル |
| `num_inference_steps` | 9 | 推論ステップ数（Turbo向け低ステップ） |
| `guidance_scale` | 0.0 | CFG無効化（Turbo向け） |
| `width` / `height` | 1024 | 出力解像度 |
| `seed` | 42 | 再現性のための固定シード |
| `prompt_filters` | (List) | プロンプトから削除する正規表現パターンリスト |

### 画像生成フロー

1. **Julesによるプロンプト生成**: 小説本文から視覚要素を抽出。
2. **フィルタリング**: `prompt_filters` に定義された単語（例: `pig`, `translucent`）を削除。
3. **テンプレート適用**: `prompts.yaml` のテンプレートに埋め込み。
4. **画像生成**: 指定されたモデルとパラメータで生成。


### 小説生成設定 (`config.yaml` → `Novelizer`)

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| `model` | gemini-3-flash-preview | 高速LLM |
| `max_output_tokens` | 4096 | 最大出力トークン数 |

