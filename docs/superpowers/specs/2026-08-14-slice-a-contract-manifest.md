---
artifact: contract-manifest
version: "1.0"
created: 2026-08-14
status: proposed-for-review
scope: kokoro-slice-a
---

# Slice A RPC、HTTP 与 SSE 精确契约清单

## 0. Authority

本文件是供人审阅的 Slice A 契约摘要；同目录的
[`2026-08-14-slice-a-contract-manifest.yaml`](2026-08-14-slice-a-contract-manifest.yaml) 是字段、枚举、方法、HTTP 与 SSE 的机器权威。
Root 将该 YAML 原字节复制为 `contract/slice-a-contract-manifest.yaml`，并逐项比较 Buf descriptor 与 OpenAPI；本 Markdown 由机器权威校验，不反向转写不完整表格。实现者不得从仓内旧 Controller、Mongo shape
或 UI 猜字段。字段名为 `snake_case`；UUID 用 canonical lowercase string；时间使用
`google.protobuf.Timestamp`/HTTP RFC3339；摘要为 64 位 lowercase hex SHA-256；分页 cursor 是服务端 opaque string。浏览器省略会话列表 `limit` 时，BFF 明确发送 `PageRequest.limit=50`；显式值仍限制为 `1..100`。

所有 RPC 都通过 metadata 携带 `authorization: Bearer <workload-token>` 和 `x-kokoro-request-id`。需要用户身份的 Site/IAM/Chat
调用另带 `x-kokoro-user-authorization: Bearer <iam-access-jwt>`；业务 request 不接受 principal/role/permission header 替代。

Method-level caller map is exact: Web may call Site, IAM Authentication and Chat; Chat may call IAM Authorization and Agent; Agent may call Model and Capability; IAM JWKS alone is public. Interceptor tests exercise every method with its valid caller, every other valid token and no token. A valid token from the wrong caller is `PERMISSION_DENIED`, not a member of a shared IAM allowlist.

IAM access JWT uses only `RS256`, header `typ=JWT` and a nonempty active-JWKS `kid`. Signed claims are exact: `iss=kokoro-iam`, `aud=kokoro-user-backend`, `sub=principal_id`, `site_id`, `organization_id`, `auth_session_id`, `iat`, and `exp`; the four IDs are canonical UUIDs, `nbf` is absent, TTL is at most 900 seconds and clock skew is at most 30 seconds. Chat and IAM reject algorithm confusion, unknown keys, bad signature, wrong issuer/audience, expired/future-issued/overlong tokens and malformed IDs. IAM additionally proves the active auth session is bound to that principal/Site/Organization; Chat derives its ActorContext only from the successful IAM `Authorize` result, never by trusting decoded claims alone. Contract tests cover forged wrong issuer, wrong audience/organization and expiry.

`StreamConversationEvents` closes no later than the access JWT `exp + 30s` clock skew and emits no frame after that deadline. The Web BFF refreshes its sealed IAM session and reconnects from the last committed sequence. An already-open stream therefore cannot keep an expired/revoked identity indefinitely; revocation exposure is bounded by the 900-second JWT TTL plus skew.

## 1. Common types and errors

### 1.1 `kokoro.common.v1`

| Message | Fields (`number:name:type:rule`) |
|---|---|
| `PrincipalContext` | `1:principal_id:string:uuid`, `2:site_id:string:uuid`, `3:organization_id:string:uuid`, `4:permission_keys:repeated string:sorted unique` |
| `CommandIdentity` | `1:command_id:string:uuid`, `2:request_digest:string:sha256` |
| `PageRequest` | `1:limit:uint32:1..100`, `2:cursor:string:optional opaque` |
| `PageResult` | `1:next_cursor:string:optional opaque` |
| `ErrorDetail` | `1:code:ErrorCode`, `2:request_id:string:nonempty`, `3:message:string:bounded diagnostic`, `4:retryable:bool`, `5:current_generation:uint64:optional` |
| `ControlDecision` | `1:kind:DecisionKind`, `2:target_id:string:nonempty`, `3:payload_json:bytes:canonical bounded JSON` |

`ErrorCode` wire numbers are frozen: `UNSPECIFIED=0`, `INVALID_ARGUMENT=1`, `UNAUTHENTICATED=2`,
`PERMISSION_DENIED=3`, `NOT_FOUND=4`, `COMMAND_DIGEST_MISMATCH=5`, `CONFLICT=6`,
`PRECONDITION_FAILED=7`, `STALE_GENERATION=8`, `SNAPSHOT_REQUIRED=9`, `DEPENDENCY_UNAVAILABLE=10`,
`RATE_LIMITED=11`, `INTERNAL=12`, `MAGIC_LINK_INVALID=20`, `MAGIC_LINK_EXPIRED=21`,
`MAGIC_LINK_CONSUMED=22`, `AUTH_SESSION_REPLAYED=23`, `AUTH_SESSION_REVOKED=24`,
`CONVERSATION_RUN_ACTIVE=30`, `CONVERSATION_SCOPE_MISMATCH=31`, `INTERACTION_NOT_PENDING=32`,
`AGENT_ADMISSION_REJECTED=40`. `DecisionKind` is `UNSPECIFIED=0,APPROVE=1,EDIT=2,REJECT=3,RESPOND=4,SUBMIT=5`; `ControlStatus` is `UNSPECIFIED=0,PENDING=1,PERSISTED=2,APPLIED=3,FAILED=4`. Both live in `kokoro.common.v1` so Chat and Agent do not import each other’s application DTOs.

`ControlDecision.payload_json` is not an open object. The machine manifest freezes a strict discriminated payload per kind: approve `{args?}`, edit `{args}`, reject `{reason?}`, respond `{response}` with nonempty response, submit `{value}` where value is a JSON object, each with `additionalProperties=false` and explicit byte/string bounds. Chat validates then stores canonical JSON bytes; Agent validates the same schema again before resume.

RPC failures use canonical gRPC status plus one serialized `ErrorDetail` in the binary trailing metadata key `kokoro-error-bin`; this avoids a second googleapis schema dependency. HTTP errors use the exact body
`{"error":{"code":<lower_snake enum name>,"request_id":string,"message":string,"retryable":boolean,"current_generation"?:string}}`.
Internal errors never return stack/provider/SQL text.

## 2. Owner RPC inventory

### 2.1 Site

| RPC | Request fields | Response fields |
|---|---|---|
| `SiteService.ResolveSiteByHost` | `1:host:string`, `2:request_id:string` | `1:site_id:string`, `2:key:string`, `3:canonical_host:string`, `4:default_locale:string`, `5:timezone:string`, `6:generation:uint64` |

Host is lowercased IDNA ASCII with the port removed before lookup. Only `active` Site/domain rows resolve.

### 2.2 IAM authentication and authorization

| RPC | Request fields | Response fields |
|---|---|---|
| `IamAuthenticationService.RequestMagicLink` | `1:request_id:string`, `2:command:CommandIdentity`, `3:site_id:string`, `4:email:string`, `5:redirect_uri:string`, `6:nonce_digest:string` | `1:magic_link_id:string`, `2:expires_at:Timestamp`, `3:delivery_ref:string`, `4:replayed:bool` |
| `IamAuthenticationService.ConsumeMagicLink` | `1:request_id:string`, `2:command:CommandIdentity`, `3:site_id:string`, `4:token:string`, `5:nonce_digest:string` | `1:principal:PrincipalContext`, `2:auth_session_id:string`, `3:access_token:string`, `4:access_expires_at:Timestamp`, `5:refresh_token:string`, `6:refresh_expires_at:Timestamp`, `7:replayed:bool` |
| `IamAuthenticationService.RefreshSession` | `1:request_id:string`, `2:command:CommandIdentity`, `3:refresh_token:string` | same fields `1..7` as `ConsumeMagicLinkResponse` |
| `IamAuthenticationService.Logout` | `1:request_id:string`, `2:command:CommandIdentity`, `3:refresh_token:string` | `1:auth_session_id:string`, `2:revoked:bool`, `3:replayed:bool` |
| `IamAuthenticationService.GetSession` | `1:request_id:string` | `1:principal:PrincipalContext`, `2:auth_session_id:string`, `3:access_expires_at:Timestamp` |
| `IamAuthorizationService.Authorize` | `1:request_id:string`, `2:site_id:string`, `3:organization_id:string`, `4:permission_key:string` | `1:allowed:bool`, `2:principal:PrincipalContext`, `3:membership_generation:uint64`, `4:reason_code:string` |

`GetSession` and `Authorize` derive the principal from `x-kokoro-user-authorization`; no token or principal field exists in their request.
`RequestMagicLink` returns only delivery metadata, never the token. Slice A permissions are exactly the five keys frozen in the master plan.
The BFF reads the mounted `web.session-key` through `KOKORO_WEB_SESSION_KEY_FILE` and derives `state_key=HKDF-SHA256(session_key, info="kokoro.magic-state.v1")`. It then computes a 32-byte nonce as `base64url(HMAC-SHA256(state_key,UUID_BYTES(site_id)||UUID_BYTES(command_id)))`, hashes it and sends the same `nonce_digest` on request and consume. This makes a lost-response retry with the same idempotency key derive the same value without adding a secret. The 202 response sets `kokoro_auth_nonce` as `Path=/api/auth; Max-Age=900; HttpOnly; Secure; SameSite=Lax`; callback clears it on success/failure. IAM stores the digest with the magic link and constant-time compares it before the single-use transition; missing/wrong/replayed nonce is rejected.

Pre-auth callback and background session commands also have frozen identities. Consume uses `UUIDv5(site_id,UTF8("consume-magic-link\n")||ASCII_HEX(SHA256(token)))`; Logout uses `UUIDv5(auth_session_id,UTF8("logout"))`. Refresh uses an unpredictable `refresh_command_id` sealed beside the old refresh token in the Web envelope. A lost response retries the same token/command and re-derives the identical successor; after a delivered response Web seals a fresh command ID with the successor. Reusing the old token with a missing/different command ID triggers family revoke. Refresh tokens are deterministically derived from the IAM refresh-derivation key, session ID and family generation while SQL stores only SHA-256; access JWT may be freshly signed for the same session.
The browser never chooses `redirect_uri`: BFF constructs `https://<resolved active canonical Site host>/api/auth/callback`, and IAM independently rejects any RPC redirect outside that Site's active domains or exact callback path.
IAM also exposes public `GET /.well-known/jwks.json` with `200 application/json`, cacheable JWKS containing only active public signing keys.

### 2.3 Capability and Model

| RPC | Request fields | Response fields |
|---|---|---|
| `CapabilityRuntimeService.ResolveRuntimeSnapshot` | `1:request_id:string`, `2:command:CommandIdentity`, `3:organization_id:string`, `4:agent_namespace:string`, `5:requested_selectors:repeated string` | `1:snapshot_id:string`, `2:organization_id:string`, `3:scope_key:string`, `4:digest:string`, `5:items:repeated CapabilitySnapshotItem`, `6:replayed:bool` |
| `ModelCatalogService.ResolveModel` | `1:request_id:string`, `2:site_id:string`, `3:label:string` | `1:model_revision_id:string`, `2:provider_id:string`, `3:provider_model_name:string`, `4:transport:ModelTransport`, `5:routing_policy_id:string`, `6:routing_policy_generation:uint64`, `7:digest:string` |

`CapabilitySnapshotItem` is reserved for Slice B but its shape is frozen now: `1:kind enum(SKILL=1,MCP=2)`,
`2:qualified_name`, `3:revision`, `4:content_digest`. Slice A requires `items=[]` and installs no item table.
`ModelTransport` is `UNSPECIFIED=0,LITELLM=1`; production rejects every other value.
The machine manifest uses package-unique type-prefixed protobuf symbols for every value (for example `MODEL_TRANSPORT_LITELLM` and `RUN_STATE_COMPLETED`); the shortened names in this review table do not define wire symbols.

### 2.4 Chat command/query

| RPC | Request fields | Response fields |
|---|---|---|
| `ChatCommandService.CreateConversation` | `1:request_id:string`, `2:command:CommandIdentity`, `3:title:string` | `1:conversation_id:string`, `2:agent_namespace:string`, `3:generation:uint64`, `4:watermark:uint64`, `5:replayed:bool` |
| `ChatCommandService.SubmitMessage` | `1:request_id:string`, `2:command:CommandIdentity`, `3:conversation_id:string`, `4:content:string`, `5:requested_model_label:string:optional`, `6:requested_agent_key:string:optional` | `1:launch_id:string`, `2:user_message_id:string`, `3:assistant_message_id:string`, `4:conversation_generation:uint64`, `5:watermark:uint64`, `6:replayed:bool` |
| `ChatCommandService.DecideInteraction` | `1:request_id:string`, `2:command:CommandIdentity`, `3:conversation_id:string`, `4:interaction_id:string`, `5:expected_generation:uint64`, `6:decisions:repeated ControlDecision` | `1:control_id:string`, `2:interaction_generation:uint64`, `3:control_status:ControlStatus`, `4:watermark:uint64`, `5:replayed:bool` |
| `ChatQueryService.ReadConversationSnapshot` | `1:request_id:string`, `2:conversation_id:string` | `1:conversation:Conversation`, `2:messages:repeated Message`, `3:active_run:RunView:optional`, `4:pending_interactions:repeated Interaction`, `5:watermark:uint64` |
| `ChatQueryService.ListConversations` | `1:request_id:string`, `2:page:PageRequest` | `1:conversations:repeated ConversationSummary`, `2:page:PageResult` |
| `ChatQueryService.StreamConversationEvents` (server streaming) | `1:request_id:string`, `2:conversation_id:string`, `3:after_seq:uint64` | repeated frames `1:event:BrowserSessionEvent`; event fields are `event_id,seq,session_id,run_id,timestamp,kind,payload_json` and must validate against §5 |

User identity and Site/organization scope come only from verified metadata. `ControlDecision`, `DecisionKind` and `ControlStatus` are the common types frozen in §1.1.
Omitted Submit selectors resolve inside Chat before persistence to model label `default` and Agent preset key `general`; the launch digest covers those resolved values. Chat rejects malformed syntax only. A syntactically valid unknown model/preset is deterministically rejected by Agent admission and converged through Chat's `AGENT_ADMISSION_REJECTED` path. Model release bootstrap must publish the requested Site's `default` label, and Agent code owns the `general` preset. Slice A Capability accepts only `requested_selectors=[]`; any nonempty selector is the same deterministic admission rejection, never silently discarded into an empty snapshot.

The first local New Chat submit uses two stable commands. After nonempty content validation, Web derives the CreateConversation title as `Array.from(content).slice(0,80).join("")`—the first 80 Unicode code points, without trimming or fallback—then uses a distinct stable idempotency key for SubmitMessage. Each lost-response retry reuses its original key and canonical digest.

Read-model messages:

| Message | Fields |
|---|---|
| `Conversation` | `1:conversation_id`, `2:organization_id`, `3:site_id`, `4:title`, `5:agent_namespace`, `6:state enum(ACTIVE=1,ARCHIVED=2,TRASHED=3)`, `7:generation`, `8:created_at`, `9:updated_at` |
| `ConversationSummary` | `1:conversation_id`, `2:title`, `3:state`, `4:generation`, `5:updated_at` |
| `Message` | `1:message_id`, `2:conversation_id`, `3:parent_message_id optional`, `4:role enum(USER=1,ASSISTANT=2,SYSTEM=3,TOOL=4)`, `5:status enum(PENDING=1,STREAMING=2,COMPLETED=3,FAILED=4)`, `6:ordinal:uint64`, `7:generation:uint64`, `8:parts:repeated MessagePart`, `9:created_at`, `10:updated_at` |
| `MessagePart` | `1:part_id`, `2:ordinal:uint32`, `3:kind enum(TEXT=1,TOOL_CALL=2,TOOL_RESULT=3,STATUS=4,THINKING=5,TODO=6,SUBAGENT=7,DELIVERY=8)`, `4:schema_version:uint32`, `5:payload_json:bytes`, `6:status enum(PENDING=1,COMPLETE=2,FAILED=3)` |
| `RunView` | `1:launch_id`, `2:agent_run_id optional`, `3:conversation_id`, `4:epoch:uint64`, `5:state`, `6:received_seq:uint64`, `7:projected_seq:uint64`, `8:terminal_kind optional`, `9:generation:uint64` |
| `Interaction` | `1:interaction_id`, `2:agent_run_id`, `3:conversation_id`, `4:kind enum(APPROVAL=1,QUESTION=2,REVIEW=3,INPUT=4)`, `5:action_digest`, `6:schema_version:uint32`, `7:status enum(PENDING=1,RESOLVED=2,CANCELLED=3,EXPIRED=4)`, `8:payload_json:bytes`, `9:expires_at optional`, `10:generation:uint64` |

`RunView` and `Interaction` use Chat-local projected enums (`RunViewState`, `RunViewTerminalKind`, `ProjectedInteractionKind`). `launch_id` is the stable RunView identity; before Agent admission, snapshot synthesizes `PREPARING` with absent `agent_run_id` and zero projection cursors from the committed active launch. It never invents an Agent ID. The projector maps later Agent values explicitly; `chat.proto` never imports Agent owner types, so Web's Chat consumer closure contains no Agent proto file.

Internal Chat streaming is only the generated `StreamConversationEvents` RPC over the same HTTP/2-capable Connect/gRPC listener. Web BFF and Root E2E consume it with their own generated Chat clients and exact workload/user metadata; there is no hidden `/v1` SSE route. BFF alone serializes those validated frames to the browser SSE format in §5.

### 2.5 Agent runtime

| RPC | Request fields | Response fields |
|---|---|---|
| `AgentRuntimeService.LaunchRun` | `1:request_id`, `2:launch_id`, `3:launch_request_digest`, `4:message_id`, `5:content`, `6:namespace`, `7:session_id`, `8:thread_id`, `9:site_id`, `10:organization_id`, `11:requested_agent_preset_key`, `12:requested_model_label`, `13:requested_capability_selectors repeated` | `1:agent_run_id`, `2:state enum(PREPARING=1,QUEUED=2,ADMISSION_FAILED=3)`, `3:manifest_digest optional`, `4:replayed` |
| `AgentRuntimeService.ApplyControl` | `1:request_id`, `2:agent_run_id`, `3:command:CommandIdentity`, `4:control_kind enum(DECIDE=1,CANCEL=2,STEER=3)`, `5:decisions:repeated ControlDecision`, `6:message_id optional`, `7:content optional` | `1:receipt_id`, `2:status:ControlStatus`, `3:replayed` |
| `AgentRuntimeService.ReadRunEvidence` | `1:request_id`, `2:agent_run_id`, `3:after_seq:uint64`, `4:limit:uint32` | `1:agent_run_id`, `2:state`, `3:epoch:uint64`, `4:events:repeated AgentEvent`, `5:next_seq:uint64`, `6:terminal:bool`, `7:usage:RunUsage optional` |
| `AgentRuntimeService.AckProjection` | `1:request_id`, `2:agent_run_id`, `3:consumer_key`, `4:epoch:uint64`, `5:projected_seq:uint64` | `1:stored_epoch:uint64`, `2:stored_projected_seq:uint64` |

Only `LaunchRunRequest` carries Site/organization admission axes. No other Agent request, response, event, manifest or GA message may contain
principal/site/organization/membership/role/permission. Agent rejects `session_id != thread_id`; Chat sets both to Conversation ID.

`RunUsage` fields: `1:input_tokens:uint64`, `2:output_tokens:uint64`, `3:total_tokens:uint64`,
`4:model_revision_id:string`, `5:digest:string`.

## 3. Exact Agent event union

`AgentEvent` envelope fields are `1:event_id`, `2:agent_run_id`, `3:epoch:uint64`, `4:seq:uint64`,
`5:occurred_at:Timestamp`, then a `oneof payload` using field numbers `20..39` in the following frozen order:

`seq` starts at 1 and is globally monotonic for the complete `agent_run`; a new lease epoch never resets it. Epoch is fence evidence only. Emit from an old epoch is rejected, `ReadRunEvidence.after_seq` is the global cursor, and `AckProjection` stores the acknowledged epoch plus global projected sequence while rejecting stale-epoch or sequence-regression updates. Cross-epoch recovery is exact: epoch 1 seq 10 is followed by epoch 2 seq 11, and reading after 10 returns 11.

Slice A has exactly one projection consumer: authenticated Chat with `consumer_key="chat"`. `AckProjection` requires the field to equal the caller-derived key; empty or unknown keys return `INVALID_ARGUMENT` before reading or writing `agent_projection_ack`. Future consumers require an explicit machine-manifest allowlist revision, so arbitrary keys cannot create rows or pin retention.

| oneof # / message / kind | Payload fields |
|---|---|
| `20 RunStarted / run.started` | none |
| `21 ThinkingDelta / thinking.delta` | `1:segment_id`, `2:delta` |
| `22 MessageDelta / message.delta` | `1:segment_id`, `2:delta` |
| `23 MessageCompleted / message.completed` | `1:segment_id`, `2:content` |
| `24 ToolInvoked / tool.invoked` | `1:segment_id`, `2:tool_id`, `3:name`, `4:args_json:bytes` |
| `25 ToolOutputDelta / tool.output.delta` | `1:segment_id`, `2:tool_id`, `3:name`, `4:delta` |
| `26 ToolAwaitingApproval / tool.awaiting_approval` | `1:segment_id`, `2:tool_id`, `3:name`, `4:args_json:bytes`, `5:description`, `6:allowed_decisions:repeated DecisionKind`, `7:interaction_kind:InteractionKind`, `8:risk_json:bytes optional`, `9:editable:bool`, `10:input_schema_json:bytes optional`, `11:pending_tool_ids:repeated string`, `12:result:string optional` |
| `27 ToolReturned / tool.returned` | `1:segment_id`, `2:tool_id`, `3:name`, `4:result`, `5:is_error:bool`, `6:truncated:bool`, `7:rejected:bool`, `8:reject_reason optional`, `9:responded:bool`, `10:summary_json:bytes optional` |
| `28 TodoUpdated / todo.updated` | `1:todos:repeated Todo` where Todo=`1:content,2:status(PENDING=1,IN_PROGRESS=2,COMPLETED=3)` |
| `29 SubagentStarted / subagent.started` | `1:segment_id`, `2:subagent_id`, `3:name`, `4:description`, `5:subagent_type`, `6:source enum(BUILT_IN=1,CONFIG_CUSTOM=2,RUNTIME_CUSTOM=3)` |
| `30 SubagentFinished / subagent.finished` | previous identity fields `1..3`, `4:subagent_type`, `5:source`, `6:failed:bool`, `7:error optional` |
| `31 SubagentThinkingDelta / subagent.thinking.delta` | `1:segment_id`, `2:subagent_id`, `3:delta` |
| `32 SubagentTextDelta / subagent.text.delta` | `1:segment_id`, `2:subagent_id`, `3:text` |
| `33 SubagentTextCompleted / subagent.text.completed` | `1:segment_id`, `2:subagent_id`, `3:text` |
| `34 SubagentToolInvoked / subagent.tool.invoked` | `1:segment_id`, `2:subagent_id`, `3:tool_id`, `4:name`, `5:args_json:bytes` |
| `35 SubagentToolReturned / subagent.tool.returned` | `1:segment_id`, `2:subagent_id`, `3:tool_id`, `4:name`, `5:result`, `6:is_error`, `7:truncated` |
| `36 DeliveryCreated / delivery.created` | `1:path`, `2:title`, `3:mime`, `4:size:uint64`, `5:content_hash`, `6:note optional` |
| `37 RunControlReceipt / run.control.receipt` | `1:command_id`, `2:status:ControlStatus` |
| `38 RunCompleted / run.completed` | `1:status enum(COMPLETED=1,CANCELLED=2)`, `2:usage:RunUsage optional` |
| `39 RunFailed / run.failed` | `1:code enum(TOKEN_BUDGET_EXCEEDED=1,RECURSION_LIMIT_EXCEEDED=2,ASSEMBLY_FAILED=3,ENQUEUE_FAILED=4,DISPATCH_EXHAUSTED=5,CONTRACT_INCOMPATIBLE=6,INTERNAL_ERROR=7,AGENT_ADMISSION_REJECTED=8)`, `2:error_kind`, `3:message` |

Chat persists the complete envelope before projecting. Browser SSE omits `run.started` and internal `run.control.receipt`; it synthesizes
`session.created`, `run.created` and `message.user` from committed Chat owner facts, then maps the other typed payloads. The browser-facing
`tool.awaiting_approval` payload extends the mature shape with required `interaction_id` and `interaction_generation`, both assigned by the committed Chat projection, so the browser can decide without an intervening snapshot read. One Interaction represents the complete pause frame. Its decision command carries `decisions[]` with at least one entry, unique `target_id`s and the exact pending target set; Chat stores and forwards the canonical list once so mixed approve/edit/reject decisions cannot partially resume a run.

## 4. Browser OpenAPI v1

All operations are same-origin under `/api`. JSON uses the same snake_case fields as RPC. Browser never sends bearer/workload credentials.
Browser mutations carry one bounded opaque `Idempotency-Key` (`8..128` ASCII visible characters; existing `idem_<uuid>` is valid). After resolving Host, pre-auth `RequestMagicLink` derives `command_id=UUIDv5(site_id, operation_id + "\n" + idempotency_key)` because no organization exists yet. Authenticated Conversation mutations use `UUIDv5(organization_id, operation_id + "\n" + idempotency_key)`. The BFF computes `request_digest=SHA-256(canonical operation target + validated payload)` itself. The browser never supplies a command UUID or trusted digest, and `X-Kokoro-Request-Digest` is rejected.

| operationId | Method/path | Success | Request | Response |
|---|---|---|---|---|
| `requestMagicLink` | `POST /api/auth/magic-link/request` | `202` | `{email}`; redirect and nonce digest are BFF-owned | `{request_id,magic_link_id,expires_at}` |
| `consumeMagicLink` | `GET /api/auth/callback?token={token}` | `303` | query token + httpOnly nonce cookie | success Location `/`; every missing/wrong/expired/consumed/dependency failure uniformly Location `/?auth=link_unavailable`; both clear nonce and disclose no typed IAM error |
| `logout` | `POST /api/auth/logout` | `204` | empty + CSRF/Origin | empty; clears auth cookie |
| `getSessionState` | `GET /api/auth/session-state` | `200` | none | `{authenticated,principal_id?,site_id?,organization_id?,auth_session_id?,expires_at?}` |
| `createConversation` | `POST /api/session/conversations` | `201` | `{title}` | `CreateConversationResponse` JSON |
| `listConversations` | `GET /api/session/conversations?limit={1..100}&cursor={opaque}` | `200` | query | `ListConversationsResponse` JSON |
| `readConversationSnapshot` | `GET /api/session/conversations/{conversation_id}` | `200` | path UUID | complete `ReadConversationSnapshotResponse` JSON |
| `submitMessage` | `POST /api/session/conversations/{conversation_id}/messages` | `202` | `{content,requested_model_label?,requested_agent_key?}` | `SubmitMessageResponse` JSON; BFF exposes `launch_id` as the mature receipt `run_id` |
| `decideInteraction` | `POST /api/session/conversations/{conversation_id}/interactions/{interaction_id}/decisions` | `202` | `{expected_generation,decisions:[...]}` with nonempty unique exact target set | `DecideInteractionResponse` JSON |
| `streamConversationEvents` | `GET /api/session/conversations/{conversation_id}/events?after_seq={uint64}` | `200 text/event-stream` | path/query; `Last-Event-ID` may supply the same cursor | SSE envelope below |

Auth request/callback command identity is stored only in sealed, SameSite=Lax, httpOnly state cookies; conversation mutations use the required `Idempotency-Key` header.
All JSON endpoints return the common error body. `SNAPSHOT_REQUIRED` is HTTP `409`; its error body additionally includes
`current_generation` as the snapshot watermark string. `UNAUTHENTICATED=401`, `PERMISSION_DENIED=403`, `NOT_FOUND=404`,
validation `400`, digest/state conflicts `409`, dependency unavailable `503`, unknown internal `500`.

The machine authority additionally freezes each operation's exact error status set and success headers: callback always returns 303, sets the sealed session cookie only on success, clears the nonce cookie and uses `Referrer-Policy: no-referrer`; session cookie `Max-Age` is `max(0,min(refresh_expires_at-now,2592000))`, with a fixed 30-day cap and no second runtime setting. Cookies require `Secure` except in the exact HTTP loopback fixture. Logout clears the session cookie. Browser JSON maps protobuf `uint64` only to JavaScript-safe nonnegative numbers, enums to prefix-free lower-snake strings, timestamps to RFC3339 and canonical `payload_json` bytes to a validated JSON object/value rather than base64.

## 5. SSE envelope and cursor rules

Each event is emitted as:

```text
id: <decimal seq>\n
data: {"event_id":"<uuid>","seq":<safe nonnegative integer>,"session_id":"<conversation uuid>","run_id":"<chat launch uuid>","timestamp":"<RFC3339>","kind":"<existing Web dot-kind>","payload":<existing typed Web payload>}\n\n
```

`after_seq` and `Last-Event-ID` must be equal when both appear. The server sends only committed rows with `seq > after_seq`, ascending.
The browser envelope deliberately preserves the mature Web `SessionEvent` contract: `session_id` is the internal Conversation ID and browser
`run_id` is always the Chat `launch_id`, including projected Agent events and snapshots. Agent `agent_run_id` remains an internal owner identity.

Complete snapshot reconstruction is normalized owner state, not retained SSE. The machine authority maps all 21 browser event kinds: message text, thinking, tool call/result, todo, subagent and delivery payloads materialize into typed/versioned `MessagePart` rows; awaiting frames also persist complete `Interaction.payload`; session/run/terminal kinds update Conversation/RunView/Message facts. A stream row becomes retention-eligible only after its mapped owner facts commit and snapshot watermark reaches that sequence. Unknown or not-yet-materialized kinds stay retained. The retention behavior test deletes the eligible prefix, restarts, and proves text, tool, todo, subagent and pending-interaction hydration is identical.
Chat maps owner/Agent event names into the existing dot-kind/payload union before persistence. `seq` must remain within JavaScript's safe-integer range. The browser parser consumes `data:`; an `event:` line is neither required nor authoritative.

The machine projection map is exact: `session.created.owner_id` is the Conversation `organization_id`; Agent approval/question/review/input map to Web `tool_approval/ask_user_question/result_review/input`; subagent source values map to hyphenated `built-in/config-custom/runtime-custom`; terminal Agent usage projects only `input_tokens/output_tokens` into the mature strict browser object. Risk, todo, token-usage and every other symbolic browser payload type have closed strict schemas in the machine authority.
If the cursor is older than the retained floor, the HTTP response is `409 application/json` with `SNAPSHOT_REQUIRED` before SSE headers.
Web then reads the complete snapshot, hydrates messages/parts/run/interaction, and reconnects from `watermark`. Heartbeats are comment frames
`: keep-alive\n\n` and carry no sequence. Bounded retention may delete only rows `<= snapshot watermark` after their owner snapshot is reconstructable.

## 6. Descriptor/OpenAPI gate

The Root machine-readable manifest must include every row above. Tests assert:

1. exact service/method set, message field number/name/type/cardinality and enum wire number;
2. only `LaunchRunRequest` contains Site/organization admission fields and the mapper strips both before GA `RunRequest`;
3. exact 20-event oneof, no generic unvalidated event payload;
4. exact ten OpenAPI operations, status codes, headers, schemas and common error mapping;
5. exact SSE envelope/cursor/stale-cursor behavior;
6. generated consumer closures from the Root plan and zero undeclared service or HTTP operation.
