# Lessons

- 2026-05-28: Do not collapse Kokoro frontend, session/backend, and agent into a monorepo by default. The user requires each major system to be planned as an independent repository.
- 2026-05-29: For frontend engineering in Kokoro, proactively lean on relevant superpower skills plus frontend/design skills where they fit.
- 2026-06-02: Keep the main agent aligned with the user-facing conversation while background agents handle bounded execution, dispatch, and exploration. Defensive rule: restate the user goal in the main thread before delegating, give each background agent a narrow scope, and return synthesized progress/decisions instead of raw executor chatter.
