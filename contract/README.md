<!-- GENERATED — DO NOT EDIT. Source: contract/spec/*.yaml -->
<!-- Regenerate: python3 contract/generate.py -->

# Kokoro wire contract

One vocabulary (snake_case fields + dot-kind) travels agent -> session -> web.
`spec/` is the only truth; `generate.py` renders every mirror and this doc;
`check.py` gates drift. Never hand-edit a generated file.

## Envelopes

- agent -> session (raw): `{ kind, run_id, index, timestamp, payload }` — `index` per-run monotonic.
- session -> web (browser): `{ kind, event_id, seq, session_id, run_id, timestamp, payload }`
  — `event_id = f(run_id, index)`; `seq` per-session monotonic (store-assigned). run.started is
  replaced by the synthetic session.created + run.created; the other 13 raw kinds pass through.

## Raw events (agent -> session, 14)

| kind | payload |
| --- | --- |
| `run.started` | (none) |
| `thinking.delta` | segment_id, delta |
| `message.delta` | segment_id, delta |
| `message.completed` | segment_id, content |
| `tool.invoked` | segment_id, tool_id, name, args |
| `tool.output.delta` | segment_id, tool_id, name, delta |
| `tool.awaiting_approval` | segment_id, tool_id, name, args, description, allowed_decisions, kind, risk?, editable, input_schema?, pending_tool_ids, result? |
| `tool.returned` | segment_id, tool_id, name, result, is_error, truncated?, rejected?, reject_reason?, responded?, summary? |
| `todo.updated` | todos |
| `subagent.started` | segment_id, subagent_id, name, description, subagent_type, source |
| `subagent.finished` | segment_id, subagent_id, name, subagent_type, source, failed?, error? |
| `subagent.thinking.delta` | segment_id, subagent_id, delta |
| `subagent.text.delta` | segment_id, subagent_id, text |
| `subagent.text.completed` | segment_id, subagent_id, text |
| `subagent.tool.invoked` | segment_id, subagent_id, tool_id, name, args |
| `subagent.tool.returned` | segment_id, subagent_id, tool_id, name, result, is_error, truncated? |
| `delivery.created` | path, title, mime, size, content_hash, note? |
| `run.control.receipt` | decision_id, control_status |
| `run.completed` | status, token_usage? |
| `run.failed` | code, error_kind, message |

## Browser events (session -> web, 15)

| kind | payload |
| --- | --- |
| `session.created` | title, owner_id |
| `run.created` | run_id |
| `message.user` | message_id, content |
| `message.delta` | segment_id, delta |
| `message.completed` | segment_id, content |
| `thinking.delta` | segment_id, delta |
| `tool.invoked` | segment_id, tool_id, name, args |
| `tool.output.delta` | segment_id, tool_id, name, delta |
| `tool.awaiting_approval` | segment_id, tool_id, name, args, description, allowed_decisions, kind, risk?, editable, input_schema?, pending_tool_ids, result? |
| `tool.returned` | segment_id, tool_id, name, result, is_error, truncated?, rejected?, reject_reason?, responded?, summary? |
| `delivery.created` | path, title, mime, size, content_hash, note? |
| `todo.updated` | todos |
| `subagent.started` | segment_id, subagent_id, name, description, subagent_type, source |
| `subagent.finished` | segment_id, subagent_id, name, subagent_type, source, failed?, error? |
| `subagent.thinking.delta` | segment_id, subagent_id, delta |
| `subagent.text.delta` | segment_id, subagent_id, text |
| `subagent.text.completed` | segment_id, subagent_id, text |
| `subagent.tool.invoked` | segment_id, subagent_id, tool_id, name, args |
| `subagent.tool.returned` | segment_id, subagent_id, tool_id, name, result, is_error, truncated? |
| `run.completed` | status, token_usage? |
| `run.failed` | code, error_kind, message |

## Control plane (session -> agent)

| message | fields |
| --- | --- |
| `run.request` | run_id, thread_id, input, runtime, context, trace |
| `run.resume` | run_id, thread_id, decision_id, decisions |
| `run.cancel` | run_id, thread_id, decision_id |
| `run.steer` | run_id, thread_id, message_id, content |

ResumeDecision (discriminated on `type`):

- `approve`: tool_id, args?
- `edit`: tool_id, args
- `reject`: tool_id, reason?
- `respond`: tool_id, response
- `submit`: request_id, value

## Streams

| stream | owner | reader | maxlen |
| --- | --- | --- | --- |
| `kokoro:runs:requests` | session | agent | 10000 |
| `kokoro:run:{run_id}:events` | agent | session | 10000 |
| `kokoro:run:{run_id}:control` | session | agent | 10000 |
| `kokoro:session:{session_id}:live` | session | session | 512 |

Consumer group `kokoro-agent`; BLOCK 1000ms; `event_id = {run_id}:{index}`; lease `kokoro:agent:lease:{run_id}`.

## HTTP (session)

| method | path |
| --- | --- |
| POST | `/sessions/{session_id}/messages` |
| GET | `/sessions` |
| GET | `/models` |
| GET | `/billing/summary` |
| GET | `/billing/ledger` |
| GET | `/sessions/{session_id}` |
| GET | `/sessions/{session_id}/deliveries/{content_hash}` |
| GET | `/sessions/{session_id}/events` |
| GET | `/sessions/{session_id}/files/{path}` |
| GET | `/sessions/{session_id}/runs/{run_id}/control/{decision_id}` |
| POST | `/sessions/{session_id}/runs/{run_id}/control` |
| DELETE | `/sessions/{session_id}` |

POST messages -> 202 `{ run_id, user_message_id, assistant_message_id }`; a non-matching
idempotency_key against an active run returns 409 `session_run_active`.
GET /sessions/:id returns the snapshot; SSE resumes from `Last-Event-ID` = last `seq`.
