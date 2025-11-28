# domain

ビジネスロジックの核心。外部依存なし。

## ファイル

- `entities.py` - `RecordingSession` データクラス（録音セッション情報）
- `interfaces.py` - インターフェース定義（Dependency Inversionのための抽象）

## RecordingSession

録音セッションを表すエンティティ：

- `audio_path`: 録音ファイルパス
- `start_time`: 録音開始時刻
- `end_time`: 録音終了時刻

## インターフェース

他の層から依存されるインターフェース：

- `TranscriberInterface` - 文字起こし抽象
- `SummarizerInterface` - 要約抽象
- `RepositoryInterface` - データ永続化抽象

