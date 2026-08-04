# Applications

Deployable and user-facing entry points live here.

| Boundary | Responsibility | Migration source |
|---|---|---|
| `capture-vrchat/` | VRChat detection, recording, transcription orchestration | current `src/app.py`, `src/main.py`, and capture-facing CLI code |
| `reader/` | Next.js private/public reader | current `frontend/reader/` |
| `api/` | HTTP API over canonical memory and artifacts | new |
| `mcp/` | read-first MCP tools (`search`, `timeline`, `get_evidence`, `list_open_loops`) | new |

Applications may depend on packages and adapter interfaces. Packages must not import application code.
