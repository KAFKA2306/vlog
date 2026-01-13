# VRChat Auto-Diary システム構成図

> マスタードキュメント → [docs/overview.md](file:///home/kafka/projects/vlog/docs/overview.md)  
> 開発ガイド → [AGENTS.md](file:///home/kafka/projects/vlog/AGENTS.md)

このシステムがどのように動いているかを図で説明します。

---

## ① 全体の流れ（データフロー図）

**この図は何？**: あなたがVRChatで遊んだ音声が、最終的にWebサイトで読める日記になるまでの流れを表しています。

```mermaid
flowchart LR
    A["🎮 VRChat起動"] --> B["🎤 録音<br/>data/recordings/*.flac"]
    B --> C["📝 音声→テキスト<br/>data/transcripts/*.txt"]
    C --> D["🧹 前処理<br/>フィラー除去・重複削除"]
    D --> E["🤖 AI要約<br/>data/summaries/*.txt"]
    E --> F["☁️ クラウド保存<br/>Supabase"]
    F --> G["🌐 Webで閲覧<br/>kaflog.vercel.app"]
    B --> H["📦 アーカイブ<br/>data/archives/"]
    
    style A fill:#9C27B0
    style B fill:#F44336
    style C fill:#FF9800
    style D fill:#FFC107
    style E fill:#4CAF50
    style F fill:#2196F3
    style G fill:#00BCD4
    style H fill:#9E9E9E
```

**実際の体験で言うと**:

1. VRChatを起動すると、自動で録音開始
2. VRChatを終了すると、録音停止
3. 裏で自動的に音声がテキストに変換される
4. 不要な言葉（あー、えー など）を削除
5. AIが日記形式に要約してくれる
6. クラウド（Supabase）に保存される
7. Webサイトで読める
8. 処理済み録音はアーカイブに移動

---

## ② VRChat起動・終了の監視（状態遷移図）

**この図は何？**: システムが「VRChatが起動したか？」「終了したか？」を常に監視して、状態を切り替えている様子です。

```mermaid
stateDiagram-v2
    [*] --> 監視中: Windowsにログオン
    
    監視中 --> 録音中: VRChat起動を検出
    録音中 --> 処理中: VRChat終了を検出
    処理中 --> 監視中: 日記作成完了
    
    note right of 監視中
        300秒ごとに
        VRChatが動いているか
        チェックしている
    end note
    
    note right of 録音中
        マイクの音を
        FLACファイルに保存中
    end note
    
    note right of 処理中
        文字起こし→前処理→要約→保存
        を自動実行中
    end note
```

**実際の体験で言うと**:

- **監視中**: 何もしていない。VRChatの起動を待っている
- **録音中**: VRChatでプレイ中。裏で録音している
- **処理中**: VRChatを終了した後、裏で日記を作っている（5〜10分かかる）

---

## ③ VRChat終了後の自動処理（シーケンス図）

**この図は何？**: VRChatを終了した後、裏で何が起きているかを時系列で表しています。

```mermaid
sequenceDiagram
    participant 👤 as あなた
    participant 🎮 as VRChat
    participant 🤖 as システム
    participant ☁️ as クラウド

    👤->>🎮: VRChatを起動
    🎮->>🤖: 起動を検出
    🤖->>🤖: 🎤 録音開始
    
    Note over 👤,🎮: VRChatでプレイ中...
    
    👤->>🎮: VRChatを終了
    🎮->>🤖: 終了を検出
    🤖->>🤖: 🎤 録音停止
    
    Note over 🤖: ここから裏で自動処理
    
    🤖->>🤖: 📝 音声をテキスト化 (数分)
    🤖->>🤖: 🧹 不要な言葉を削除
    🤖->>🤖: 🤖 AIで日記に要約
    🤖->>☁️: ☁️ クラウドに保存
    ☁️-->>🤖: 完了
    🤖->>🤖: 📦 録音をアーカイブに移動
    
    Note over 🤖: 完了！Webで読める状態に
```

**実際の体験で言うと**:

1. あなたがVRChatを終了
2. システムが録音を止める
3. その後は自動で処理（5〜10分くらい）
4. 完了したら、Webサイトで日記が読める状態に
5. 録音ファイルは自動的にアーカイブに移動

---

## 自動/手動の区別

| やること | 自動？ | いつ動く？ |
|---|:---:|---|
| 📌 VRChatの監視 | ✅ 完全自動 | Windowsログオン時から常に |
| 🎤 録音の開始/停止 | ✅ 完全自動 | VRChat起動/終了を検出したら |
| 📝 音声→テキスト | ✅ 完全自動 | 録音が終わったら |
| 🧹 テキスト前処理 | ✅ 完全自動 | 文字起こしが終わったら |
| 🤖 テキスト→日記 | ✅ 完全自動 | 前処理が終わったら |
| ☁️ クラウド保存 | ✅ 完全自動 | 日記作成が終わったら |
| 📦 録音アーカイブ | ✅ 完全自動 | すべて完了したら |
| 🌐 Webサイト更新 | ❌ 手動 | 開発者が`task web:deploy`を実行 |

**つまり**: VRChatで遊ぶだけで、日記が勝手にできあがる！

---

## ファイルの置き場所

```bash
vlog/
data/
  ├── recordings/     🎤 録音ファイル (FLAC形式)
  ├── transcripts/    📝 音声から変換したテキスト
  ├── summaries/      ✨ AIが作った日記
  └── archives/       📦 処理済み録音の保管場所
logs/
  └── vlog.log        📋 システムの動作記録
```

**トラブル確認方法**: WSLで`task status`を実行すると、今何をしているかがわかります。

---

## 技術スタック

- **録音**: sounddevice + soundfile (FLAC形式、16kHz) → `system.py`
- **文字起こし**: Faster Whisper (large-v3-turbo, CUDA) → `system.py`
- **前処理**: カスタムロジック（フィラー除去、重複削除） → `system.py`
- **要約・小説生成**: Google Gemini 3 Flash → `ai.py`
- **画像生成**: Diffusers (Z-Image-Turbo) → `ai.py`
- **DB**: Supabase (PostgreSQL) → `repositories.py`
- **フロントエンド**: Next.js + Vercel
- **タスクランナー**: Task (Taskfile.yaml)

