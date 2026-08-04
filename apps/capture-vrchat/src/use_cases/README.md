# use_cases

ビジネスロジック層。Domainエンティティを使用し、Infrastructureを調整。

## ファイル一覧

| ファイル | クラス/関数 | 責務 |
|----------|------------|------|
| `process_recording.py` | `ProcessRecordingUseCase` | 録音処理ユースケース本体 |
| `process_recording.py` | `.execute()` | ファイルパス指定で処理 |
| `process_recording.py` | `.execute_session()` | セッション処理（複数ファイル対応） |
| `process_recording.py` | `._process_transcript()` | 文字起こし→前処理 |
| `process_recording.py` | `._save_summary()` | 重複チェック付き要約保存 |
| `process_recording.py` | `._generate_novel_and_photo()` | 小説・画像の存在チェック付き生成 |
| `build_novel.py` | `BuildNovelUseCase` | 小説生成ユースケース |
| `build_novel.py` | `.execute()` | 日付指定で小説と画像生成 |
| `evaluate.py` | `EvaluateDailyContentUseCase` | コンテンツ評価ユースケース |
| `evaluate.py` | `.execute()` | 要約と小説の品質評価 |

## 処理フロー工夫

### ProcessRecordingUseCase

1. **重複処理防止**: `_save_summary()`で既存要約をチェック、スキップ
2. **小説・画像の独立生成**: novel/photoそれぞれ存在チェック、片方だけ生成可能
3. **メモリ管理**: `_transcriber.unload()`でWhisperモデル解放

### BuildNovelUseCase

1. **追記モード**: 既存小説がある場合、新チャプターを追記
2. **原子的生成**: 小説生成後に画像生成（順序保証）

## サブディレクトリ

- `mbti/` - MBTI分析ユースケース

