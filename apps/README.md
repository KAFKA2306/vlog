# Applications

Deployable and user-facing entry points live here.

| Boundary | Status | Responsibility |
|---|---|---|
| `capture-vrchat/` | implemented | current capture and processing runtime |
| `reader/` | implemented | current Next.js Reader |
| `api/` | reserved | future HTTP boundary over canonical data |
| `mcp/` | reserved | future read-first retrieval tools |

Applications may depend on packages and adapters. Packages must not import applications. See [current architecture](../docs/architecture.md).
