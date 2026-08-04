# domain

ビジネスロジックの核心。外部依存なし。

## ファイル一覧

| ファイル | クラス/関数 | 責務 |
|----------|------------|------|
| `entities.py` | `RecordingSession` | 録音セッションエンティティ |
| `interfaces.py` | `TranscriberProtocol` | 文字起こし抽象 |
| `interfaces.py` | `TranscriptPreprocessorProtocol` | トランスクリプト前処理抽象 |
| `interfaces.py` | `SummarizerProtocol` | 要約生成抽象 |
| `interfaces.py` | `StorageProtocol` | ストレージ同期抽象 |
| `interfaces.py` | `FileRepositoryProtocol` | ファイル操作抽象 |
| `interfaces.py` | `NovelizerProtocol` | 小説生成抽象 |
| `interfaces.py` | `ImageGeneratorProtocol` | 画像生成抽象 |

## エンティティ詳細

### RecordingSession

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `start_time` | `datetime` | 録音開始時刻 |
| `file_paths` | `tuple[str, ...]` | 録音ファイルパス（複数対応） |
| `end_time` | `datetime \| None` | 録音終了時刻 |

## インターフェース設計

Protocol（構造的部分型）を使用。実装クラスは明示的な継承不要。

| Protocol | メソッド | 戻り値 |
|----------|----------|--------|
| `TranscriberProtocol` | `transcribe_and_save(audio_path)` | `tuple[str, str]` |
| `TranscriberProtocol` | `unload()` | `None` |
| `TranscriptPreprocessorProtocol` | `process(text)` | `str` |
| `SummarizerProtocol` | `summarize(transcript, session)` | `str` |
| `StorageProtocol` | `sync()` | `None` |
| `FileRepositoryProtocol` | `exists(path)` | `bool` |
| `FileRepositoryProtocol` | `save_text(path, content)` | `None` |
| `FileRepositoryProtocol` | `archive(path)` | `None` |
| `NovelizerProtocol` | `generate_chapter(summary, novel_so_far)` | `str` |
| `ImageGeneratorProtocol` | `generate_from_novel(chapter, output_path)` | `None` |

