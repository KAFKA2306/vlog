---
description: VLogプロジェクトの自律的なヘルスチェック、ログ修復、およびメンテナンス手順。
---

# VLog メンテナンスワークフロー

システムの健全性を維持し、安定した運用を確保するための統合手順です。

## 1. システムヘルスチェック
// turbo-all
1.  **サービスのステータス確認**:
    ```bash
    task status
    ```
2.  **エラー検知**: `vlog.log` にエラーが含まれているか確認します。
    ```bash
    tail -n 100 data/logs/vlog.log | grep -E "Error|Exception|Critical"
    ```
    - エラーが検出された場合 → **ステップ 2（診断・修復）** へ進む。
    - エラーなし → **ステップ 3（インフラ監査）** へスキップ。

## 2. 診断・修復（エラー検出時のみ）
// turbo-all
1.  **事実確認**: `FileNotFoundError` が報告されている場合、物理的なファイルパスを確認します。
    ```bash
    ls -l data/recordings/
    ```
2.  **修復エージェントの実行**: `tasks.json` の整合性を強制的に再構築します。
    ```bash
    task repair
    ```
3.  **パス正規化の確認**: `tasks.json` 内に `\` が残っていないか確認します。
    ```bash
    grep "\\\\" data/tasks.json
    ```
4.  **リカバリ処理**:
    ```bash
    task process:all
    ```
5.  **修復後の再検証**: エラーが解消されたことを確認します。
    ```bash
    tail -n 50 data/logs/vlog.log | grep -E "Error|Exception"
    ```
    - まだエラーがある場合 → **ステップ 5（エスカレーション）** へ。

## 3. ゼロ・ファット インフラ監査
// turbo-all
1.  **同期確認**: Supabase とローカルタスクが 1:1 であることを確認します。
    ```bash
    task sync
    ```
2.  **プロセス監査**: 放置されている録音を特定し、処理します。
    ```bash
    task process:pending
    ```

## 4. コードの整合性
// turbo-all
1.  **リンターとフォーマッタ**: 厳格なコーディング規約を適用します。
    ```bash
    task lint
    ```
2.  **品質検証**: ヘルスチェック・スイートを実行します。
    ```bash
    task check
    ```

## 5. エスカレーション
- 修復に失敗した場合は、`docs/logs/YYYYMMDD_crash_analysis.md` を作成してください。

## 6. 完了

- **エビデンスの確認**: `vlog.log` を最後にもう一度確認し、エラーが出ていないことを確認します。
- **状態のコミットと同期**: 
  変更を適用し、リモートへ反映するために次のコマンドを呼び出してください。
  ```bash
  /git
  ```

