# Claude Progress

- Date: 2026-05-29
- Active stream: kokoro-web bootstrap
- Completed:
  - Wrote kokoro-web design spec
  - Wrote kokoro-web implementation plan
  - Created independent `kokoro-web` repository with Bun + Next.js App Router scaffold
  - Added strict protocol parsing in `src/infrastructure/protocol/` and mapped it into domain-safe session stream events
  - Added replay-safe reducer plus red→green tests
  - Added a minimal AGUI/A2UI-oriented session shell with a client-only artifact preview boundary
  - Verified `bun run test`, `bun run lint`, `bun run typecheck`, and `bun run build` in `kokoro-web`
- Blocked:
  - Local git commits are still pending because the Claude Code auto-mode classifier denied commit commands while the repo contains a `CLAUDE.md` instructions file.
- Next verification / unblock step:
  - After commit authorization, run the child-repo atomic commits and the parent-repo docs/progress commit.
