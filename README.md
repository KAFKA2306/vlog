<div align="center">

# 🎮 VRChat Auto-Diary

**Transform your VRChat experiences into beautifully crafted diaries, novels, and artwork — all automatically.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ecf8e?style=flat-square&logo=supabase)](https://supabase.com)
[![License](https://img.shields.io/badge/License-Private-gray?style=flat-square)]()

[Live Demo](https://kaflog.vercel.app) · [Documentation](docs/overview.md) · [Development Guide](AGENTS.md)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎤 **Auto Recording** | Detects VRChat launch/exit and records audio automatically |
| 📝 **AI Transcription** | Faster Whisper (large-v3-turbo) for high-accuracy speech-to-text |
| 📖 **Smart Summaries** | Gemini 2.5 Flash transforms conversations into diary entries |
| 📚 **Novel Generation** | Long-form narrative chapters from your daily experiences |
| 🎨 **AI Artwork** | Auto-generated illustrations matching your story's mood |
| ☁️ **Cloud Sync** | Seamless sync to Supabase with public/private control |
| 🌐 **Web Reader** | Modern Next.js frontend to browse your memories |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- [Task](https://taskfile.dev) runner

### Installation

```bash
# Clone and setup
git clone https://github.com/yourusername/vlog.git
cd vlog
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Run

```bash
# Linux/WSL - Start as service
task up

# Windows - Double-click or run
windows\run.bat
```

---

## 📁 Project Structure

```
vlog/
├── src/                    # Python backend
│   ├── infrastructure/     # AI, audio, repositories
│   │   ├── system.py       # Recording, transcription, monitoring
│   │   ├── ai.py           # Summarizer, Novelizer, ImageGenerator
│   │   └── repositories.py # File, Task, Supabase repos
│   ├── use_cases/          # Business logic
│   └── domain/             # Entities & interfaces
├── frontend/reader/        # Next.js web app
├── data/                   # Local storage
│   ├── recordings/         # Audio files (FLAC)
│   ├── summaries/          # AI-generated diaries
│   ├── novels/             # Long-form chapters
│   └── photos/             # Generated artwork
└── docs/                   # Documentation
```

---

## 🔧 Commands

| Command | Description |
|---------|-------------|
| `task up` | Start systemd service |
| `task down` | Stop service |
| `task status` | Check system status |
| `task logs` | Real-time log streaming |
| `task process FILE=...` | Process single audio file |
| `task sync` | Sync to Supabase |
| `task web:dev` | Start frontend dev server |
| `task web:deploy` | Deploy to Vercel |

---

## 🏛️ Philosophy & Quality: Zero-Fat

本プロジェクトは、冗長性を排除し本質的なロジックのみを追求する **Zero-Fat 原則** に基づいて設計・実装されています。

- **Fail Fast**: エラーを隠蔽せず、即座に顕在化させることで堅牢性を担保。
- **Self-Documenting**: コメントを廃し、厳格な型定義と命名によってコード自体に語らせる。
- **Modern Toolchain**: Astral 製ツールチェーン（uv, Ruff, ty）を統合し、機械的な品質保証を実現。

詳細は [Modern Python & Zero-Fat 規約](docs/coding_rules.md) および [インタラクティブダッシュボード](docs/coding_rules_dashboard.html) を参照してください。

---

## 🛠️ Tech Stack

<table>
<tr>
<td align="center" width="96">
<b>Backend</b>
</td>
<td align="center" width="96">
<b>AI/ML</b>
</td>
<td align="center" width="96">
<b>Frontend</b>
</td>
<td align="center" width="96">
<b>Infra</b>
</td>
</tr>
<tr>
<td align="center">
Python 3.11<br/>
sounddevice<br/>
Pydantic
</td>
<td align="center">
Faster Whisper<br/>
Gemini 2.5<br/>
Diffusers
</td>
<td align="center">
Next.js 16<br/>
React 19<br/>
TypeScript
</td>
<td align="center">
Supabase<br/>
Vercel<br/>
systemd
</td>
</tr>
</table>

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [AGENTS.md](AGENTS.md) | Development guide & coding conventions |
| [docs/overview.md](docs/overview.md) | Complete system documentation |
| [docs/architecture.md](docs/architecture.md) | Visual system diagrams |
| [docs/image.md](docs/image.md) | Image generation subsystem |

---

## 🌐 Live

**Production**: [kaflog.vercel.app](https://kaflog.vercel.app)

---

<div align="center">

Made with ❤️ for VRChat memories

</div>
