# Execution Style Contract Design

## Context

Current baseline:
- `Kokoro` root: `feat/kokoro-web-bootstrap` @ `0fe0dbd`
- `kokoro-web`: `feat/bootstrap-shell` @ `fa419f4`
- `kokoro-session`: `feat/three-repo-loop` @ `712a34b`
- `kokoro-agent`: `feat/three-repo-loop` @ `63c6031`

The current UI exposes `Fast` / `Thinking`, but the runtime contract is still half-wired. The clearest symptom is `kokoro-web/src/application/session-stream-preview.ts`, where the run URL is built with a hard-coded `execution_style=default` regardless of the selected mode. Downstream, `kokoro-session` can parse and relay `execution_style`, but `kokoro-agent` does not actually consume it: the worker constructs one model outside the request loop and `run_agent` only uses `req.input`.

This creates a false product surface: the user can select a mode that does not change real execution behavior.

## Goal

Turn `execution_style` into a real, single-meaning, per-run execution contract so that:
1. the selected mode in `kokoro-web` is sent on the live request path;
2. `kokoro-session` validates and relays that mode without inventing or mutating semantics;
3. `kokoro-agent` uses that mode to choose the actual execution configuration for this run;
4. tests across all three repos prove the mode is no longer display-only.

## Recommended contract

### Chosen meaning

`execution_style` should remain a stable **business-level execution mode**, not a raw provider/model string.

Allowed values in the first pass:
- `fast`
- `thinking`

### Why this meaning

This keeps the browser contract stable and avoids leaking provider details into UI state. It also gives us room to remap either mode to different provider/model/streaming strategies later without rewriting the front-end contract.

If we instead pass raw model specs (for example `openai:glm-5`), the front end becomes tightly coupled to provider naming and deployment decisions. That is a bad fit for a product surface whose UI language is already `Fast` / `Thinking`.

## Approaches considered

### Approach A — Stable business modes (`fast | thinking`) mapped inside agent **(recommended)**

- `kokoro-web` stores and sends `fast | thinking`
- `kokoro-session` validates and relays those exact values
- `kokoro-agent` maps each mode to a real model / strategy configuration per request

**Pros**
- Clean abstraction boundary
- Front end stays provider-agnostic
- Easy to evolve later
- Best fit for the current UI labels

**Cons**
- Requires rewriting the agent model lifecycle from global-singleton to per-run resolution (or explicit keyed cache)

### Approach B — Pass raw provider/model spec through `execution_style`

- `kokoro-web` sends values like `openai:glm-5`
- session relays them as-is
- agent uses the string directly

**Pros**
- Superficially simpler
- Fewer mapping steps in agent

**Cons**
- UI becomes infrastructure-aware
- Harder to rename or rebalance modes later
- Conflicts with the current `Fast` / `Thinking` product language

### Approach C — Keep current mixed state and only thread the chosen mode into the request

- send selected mode from web
- keep current agent runtime mostly unchanged

**Pros**
- Smallest diff now

**Cons**
- Does not solve the root problem
- Agent still cannot vary behavior per run because model construction is global
- Leaves naming and lifecycle debt in place

## Decision

Choose **Approach A**.

We will keep `execution_style` as a stable business mode and rewrite the agent-side execution configuration boundary so that the selected mode changes real per-run behavior.

## Design details

### 1. Web (`kokoro-web`)

#### Current problem
- `ConversationEntry.mode` already exists and is locked after the first message
- `Composer` already renders the selector
- but `startReply()` never receives the selected mode
- and `buildRunUrl()` always writes `execution_style=default`

#### Design
- Extend the request-building path so the selected `AgentMode` enters `StartReplyInput`, `ConsumeLiveSessionInput`, and `buildRunUrl()`
- Replace the hard-coded `default` query value with the actual selected mode
- Keep the existing per-conversation lock behavior unchanged
- Preserve fallback preview behavior, but ensure the live path always uses the chosen mode when POSTing to `kokoro-session`

#### Non-goals
- Do not redesign the UI copy for Fast/Thinking in this pass
- Do not expand mode options beyond `fast | thinking`

### 2. Session (`kokoro-session`)

#### Current problem
- `http.ts` reads `execution_style` from the query string
- `start_run.ts` conditionally writes it into `run.request`
- domain schema still allows a broad optional string shape at the session layer

#### Design
- Tighten session-side validation to the explicit allowed values for this pass: `fast | thinking`
- Fail loud on unknown values instead of silently relaying arbitrary strings
- Continue to treat session as a narrow boundary: it validates and relays, but does not choose provider/model behavior

#### Non-goals
- Do not embed provider-specific knowledge in `kokoro-session`

### 3. Agent (`kokoro-agent`)

#### Current problem
- `RunRequest.execution_style` exists with a default value
- but `worker.py` builds one model before entering the subscribe loop
- and `run_agent()` does not inspect `req.execution_style`
- therefore per-run execution style cannot change anything

#### Design
- Introduce an explicit per-run execution configuration resolver at the agent boundary
- That resolver takes `req.execution_style` and returns the model/strategy config for this run
- The first-pass mapping should be:
  - `fast` → default production model config (current real-provider path)
  - `thinking` → a distinct strategy branch, even if initially mapped to the same provider family, with an explicit code path proving the runtime consumed the mode
- Move model acquisition so that it can vary by request
  - acceptable implementations:
    - per-run model construction; or
    - an internal keyed cache by resolved execution config
- `run_agent()` must receive the resolved model for the current request and no longer rely on a single worker-global model instance

#### Important quality rule
If `thinking` ends up using the exact same resolved model and exact same flags as `fast`, then this task is **not complete**. A passing implementation must prove that selecting `thinking` changes the actual execution configuration for that run.

### 4. Naming and contract discipline

For this pass, `execution_style` remains the transport field name because it already exists in session and agent boundaries. But its semantics become explicit and narrow:
- transport field name: `execution_style`
- allowed values: `fast | thinking`
- meaning: business-level execution mode chosen per run

If future work needs richer concepts (provider, model id, reasoning depth, tool budget), those should be introduced behind the agent resolver or via a new contract object, not by overloading `execution_style` with arbitrary strings.

## Testing strategy

### Web tests
Add or update tests to prove:
- the selected mode is included in the live run request query
- `fast` and `thinking` generate different `execution_style` query values
- mode lock behavior still works after wiring the request path

Target files likely include:
- `kokoro-web/tests/application/session-stream-preview.test.ts`
- `kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx`
- `kokoro-web/tests/application/conversation-store.test.ts`

### Session tests
Add or update tests to prove:
- POST `/sessions/:id/runs?...&execution_style=fast` enters `run.request` correctly
- `thinking` also passes validation
- invalid values fail loud

Target files likely include:
- `kokoro-session/tests/http.test.ts`
- `kokoro-session/tests/start-run.test.ts`
- `kokoro-session/tests/agent-events.test.ts`

### Agent tests
Add or update tests to prove:
- `RunRequest.execution_style` is consumed by runtime logic
- different execution styles choose different resolved execution configs
- worker lifecycle supports per-run configuration instead of a single fixed model instance

Target files likely include:
- `kokoro-agent/tests/test_worker.py`
- `kokoro-agent/tests/test_model.py`
- `kokoro-agent/tests/test_events.py`
- a new focused test file for execution-style resolution if that boundary is extracted

### End-to-end verification
After implementation, run one real multi-repo verification where:
- Fast path is selected and a run is started
- Thinking path is selected and a run is started
- evidence clearly shows where the behavior differs (request parameter, session relay, and agent-side execution config)

## Rewrite vs refactor guidance

### Rewrite
Rewrite the agent model-lifecycle boundary if needed. The current worker-global model construction is the wrong lifecycle for per-run execution style. This is structural, not cosmetic.

### Refactor
Refactor the web request path to thread the chosen mode through existing abstractions.

### Patch
Patch the session boundary only as needed to tighten validation and tests. Its overall layering is already correct.

## Risks

1. **False completion risk**
   The UI request value changes but agent behavior stays the same. This must be treated as incomplete.

2. **Overloading risk**
   People may try to stuff provider/model strings into `execution_style`. This design explicitly rejects that for the current pass.

3. **Lifecycle regression risk**
   Reworking agent model resolution can accidentally disturb local fake mode or non-streaming behavior. Tests must cover both.

## Success criteria

This design is complete when all of the following are true:
1. web no longer hard-codes `execution_style=default`;
2. session only accepts valid execution-style values for this pass;
3. agent per-run behavior really depends on `req.execution_style`;
4. automated tests in all touched repos cover the new contract;
5. a live verification demonstrates that `Fast` and `Thinking` are not just cosmetic UI labels.
