# Applications

Deployable and user-facing entry points live here.

| Boundary | Status | Responsibility |
|---|---|---|
| `capture-vrchat/` | implemented | VRChat detection, recording, transcription, and current processing orchestration |
| `reader/` | implemented | Next.js private/public reader |
| `api/` | reserved | HTTP API over canonical memory and artifacts |
| `mcp/` | reserved | read-first MCP tools (`search`, `timeline`, `get_evidence`, `list_open_loops`) |

Applications may depend on packages and adapter interfaces. Packages must not import application code.
