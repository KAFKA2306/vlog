# src/services

アプリケーションのワークフローをまとめるサービス層です。

- `recorder_service.py`: プロセス監視と連動して録音を開始・停止します。
- `processor_service.py`: 録音ファイルを文字起こし→要約→日記保存まで実行します。

外部依存は `infrastructure` に委譲し、ここではフロー制御に集中させます。
