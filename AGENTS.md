# VRChat Auto-Diary

See [Global Configuration](file:///home/kafka/projects/.agent/AGENTS.md)

## Domain Overrides

### VRChat Process Monitoring
- Process names: `VRChat.exe`, `vrchat`
- Check interval: 5 seconds
- Auto-start recording on process detection

### Audio Pipeline
- Sample rate: 48000 Hz
- Channels: 2 (stereo)
- Silence threshold: -40 dB
- Minimum recording: 60 seconds

### Supabase Schema
- `recordings`: session metadata
- `transcripts`: Whisper output
- `summaries`: Gemini-generated summaries

### Whisper Config
- Model: `large-v3`
- Device: `cuda` (fallback: `cpu`)
- VAD filter: enabled
- Language: `ja`

### Gemini Config
- Model: `gemini-2.5-flash`

## Commands

See `Taskfile.yml` for all commands.

Key tasks:
- `task dev` - Auto-monitoring mode
- `task process FILE=audio.wav` - Process single recording
- `task sync` - Supabase sync
- `task web:dev` - Frontend dev server

## Agentic Management

See [.agent/workflows/agentic-management.md](file:///home/kafka/projects/vlog/.agent/workflows/agentic-management.md) for maintenance procedures.
See [.agent/workflows/agentic-optimization.md](file:///home/kafka/projects/vlog/.agent/workflows/agentic-optimization.md) for content quality improvement procedures.

### Zero-Fat Development Constraints
すべてのエージェントは、[docs/coding_rules.md](file:///home/kafka/projects/vlog/docs/coding_rules.md) に定義された **Zero-Fat 原則** を厳守しなければならない：
- **Fail Fast**: エラーハンドリングによる不具合の隠蔽を禁止。
- **Success Path Only**: 関数本体は正常系ロジックのみを記述。
- **Any 禁止 / コメント排除**: 厳密な型定義を行い、自然言語による説明をコードから排除。

Agents should perform a weekly health check and audit processed recordings.

## MCP Servers

- `supabase-mcp-server` - Database operations
- `netlify` - Frontend deployment






