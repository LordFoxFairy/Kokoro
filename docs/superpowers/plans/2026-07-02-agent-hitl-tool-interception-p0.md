# Agent HIL Tool Interception P0 Implementation Plan

> **For agentic workers:** REQUIRED: Use
> superpowers:subagent-driven-development or superpowers:executing-plans to
> implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the agent-side P0 for standard HIL and tool interception
without inventing a parallel runtime.

**Architecture:** DeepAgents remains the execution substrate. Kokoro adds a
small `ToolPolicyMiddleware` hook, passes middleware into `create_deep_agent`,
enriches `tool_call_awaiting` raw events, and restricts `respond` to
`ask_user`.

**Tech Stack:** Python 3.14, DeepAgents 0.6.6, LangChain 1.3.2,
LangGraph 1.2.2, Pydantic v2, pytest, ruff, pyright.

---

## Scope

This plan only changes `kokoro-agent`. `kokoro-session` and `kokoro-web`
follow after the agent raw event contract is correct.

Reference design:

- `docs/kokoro-handbook/technical/12-agent-hitl-tool-interception.md`
- `docs/kokoro-handbook/modules/kokoro-agent.md`

## Files

- Modify: `kokoro-agent/src/kokoro_agent/execution/deepagents.py`
- Modify: `kokoro-agent/src/kokoro_agent/execution/create_agent.py`
- Modify: `kokoro-agent/src/kokoro_agent/execution/approvals.py`
- Modify: `kokoro-agent/src/kokoro_agent/execution/events.py`
- Modify: `kokoro-agent/src/kokoro_agent/run/events.py`
- Modify: `kokoro-agent/src/kokoro_agent/tools/permissions.py`
- Modify: `kokoro-agent/src/kokoro_agent/tools/ask_user.py`
- Modify: `kokoro-agent/src/kokoro_agent/tools/names.py`
- Modify: `kokoro-agent/src/kokoro_agent/tools/registry.py`
- Create: `kokoro-agent/src/kokoro_agent/tools/middleware.py`
- Test: `kokoro-agent/tests/test_factories.py`
- Test: `kokoro-agent/tests/test_permission.py`
- Test: `kokoro-agent/tests/test_tools.py`
- Test: `kokoro-agent/tests/projection/test_hitl.py`
- Test: `kokoro-agent/tests/run/test_hitl_e2e.py`
- Test: `kokoro-agent/tests/test_package_architecture.py`

## Task 1: Pass Middleware Into DeepAgents

- [ ] Write a failing test in `tests/test_factories.py` proving `build_agent()`
      forwards a `middleware` sequence to `make_deep_agent`.
- [ ] Run this command and verify it fails:

        uv run pytest \
          tests/test_factories.py \
          -q

- [ ] Add `middleware` parameter to `execution/deepagents.py::make_deep_agent`.
- [ ] Pass the middleware into `create_deep_agent(..., middleware=list(middleware))`.
- [ ] Build middleware in `execution/create_agent.py`.
- [ ] Re-run the targeted test and verify it passes.

## Task 2: Add ToolPolicyMiddleware

- [ ] Write failing tests in `tests/test_tools.py` for a middleware that can
      forward a tool call unchanged and can override args.
- [ ] Create `tools/middleware.py`.
- [ ] Implement a minimal `ToolPolicyMiddleware(AgentMiddleware)` using
      `awrap_tool_call`.
- [ ] Use `request.override(tool_call=...)` for deterministic argument
      normalization hooks.
- [ ] Keep the first implementation conservative: no policy mutation unless a
      normalizer is explicitly registered.
- [ ] Re-run targeted tests.

## Task 3: Implement ask_user Tool Boundary

- [ ] Write failing tests that `ASK_USER_TOOL_NAME == "ask_user"` is
      registered.
- [ ] Implement `tools/ask_user.py` as a `StructuredTool`.
- [ ] Its callable should fail loud if executed, because normal operation must
      be interrupted and resumed with `respond`.
- [ ] Register it in `BUILT_IN_TOOLS`.
- [ ] Add `ASK_USER_TOOL_NAME` to `tools/names.py`.
- [ ] Re-run `tests/test_tools.py`.

## Task 4: Restrict respond To ask_user

- [ ] Update `tests/test_permission.py` so default dangerous tools allow only
      `approve/edit/reject`.
- [ ] Add a test that `ask_user` allows only `respond`.
- [ ] Update `tools/permissions.py::build_interrupt_on`.
- [ ] Keep `ask_user` respond-only in every mode; `auto` only skips ordinary
      dangerous-tool approval.
- [ ] Re-run `tests/test_permission.py`.

## Task 5: Enrich tool_call_awaiting

- [ ] Update `tests/projection/test_hitl.py` to assert `description`,
      `allowed_decisions`, `kind`, and `editable`.
- [ ] Update `execution/approvals.py` to keep `description` and
      `review_configs.allowed_decisions`.
- [ ] Update `run/events.py` so awaiting payload is not limited to
      `ToolStartData`.
- [ ] Update `execution/events.py` only if the helper type needs to accept the
      enriched payload.
- [ ] Re-run projection tests.

## Task 6: Preserve Resume Behavior

- [ ] Update `tests/run/test_hitl_e2e.py` for `respond` only on `ask_user` and
      for normal tool reject behavior.
- [ ] Ensure `_decision_dict()` still strips `tool_id`.
- [ ] Ensure multi-tool pending alignment still uses `tool_id`.
- [ ] Re-run:

        uv run pytest \
          tests/run/test_hitl_e2e.py \
          tests/run/test_supervisor.py \
          -q

## Task 7: Architecture Guard

- [ ] Add `tools/middleware.py` to `tests/test_package_architecture.py`.
- [ ] Ensure no forbidden directories are reintroduced.
- [ ] Run `uv run pytest tests/test_package_architecture.py -q`.

## Verification

Run from `kokoro-agent/`:

    uv run pytest
    uv run ruff check src tests
    uv run pyright

Expected:

    pytest: all tests pass
    ruff: All checks passed
    pyright: 0 errors

## Follow-up Plan

After agent P0 passes:

- `kokoro-session`: persist pending pauses and validate control against `allowed_decisions`.
- `kokoro-web`: split tool approval UI from `ask_user` UI.
- Cross-stack: verify refresh/replay preserves pending pause.
