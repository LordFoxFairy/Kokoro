# Todo

- [x] Create `kokoro-web/` as an independent Git repository.
- [x] Scaffold Bun + Next.js + Tailwind + shadcn/ui baseline.
- [x] Add DDD folders and dependency boundaries.
- [x] Add strict protocol schemas with failing tests first.
- [x] Add replay reducer with failing tests first.
- [x] Render the minimal chat shell using seed events.
- [x] Run test, lint, typecheck, and build.

## Documentation alignment

- [x] Add a durable three-primary-runtime architecture overview.
- [x] Record the main-agent/user-alignment lesson and defensive rule.
- [x] Persist the DeepAgents/LangChain orchestration reuse preference in project memory.
- [x] Clarify the protocol docs so the current minimal session-stream closed loop is distinct from browser-reserved parse-and-ignore event families.

## First-screen shell redesign (staged)

- [x] Add `run.created` to the protocol union as a parse-and-ignore family (maps to null) with red→green tests.
- [x] Replace the two-card protocol demo with the approved minimal first-screen shell (rail + hero + static composer).
- [x] Rework `globals.css` for the first-screen layout.
- [x] Keep the SSE reducer wired but surfaced via `data-*` while message rendering is deferred to the chat-view slice.
- [x] Gitignore local agent/MCP scratch dirs (`.playwright-mcp/`, `.superpowers/`).
- [ ] NEXT slice — chat view: render reducer messages/run status and re-mount `ArtifactPreview` (currently reserved, unmounted), then wire the composer to a real session.
