# Mori API 契约 v0.1

> 状态：preview contract，供 Mori BFF 与前端接线评审
> 日期：2026-09-02
> 适用范围：`kokoro-mori` 的音乐业务 HTTP projection

## 1. 契约定位

这是 Mori 面向浏览器的业务契约，不是 Suno、Tad 或其他音乐供应商的 API 镜像。浏览器
只访问同源 `/api/v1/*`；BFF 负责身份、权限、幂等、owner 调用和 provider adapter。公开
字段不暴露 provider 名称、provider task id、供应商状态或供应商内部 URL。

```text
Mori Web → same-origin BFF → Music owner → provider-neutral adapter → provider
```

Project 是业务组织根；SongPlan、Generation、Candidate、Version、Asset 和 Export 均
通过 opaque ref 关联。`request_id` 只用于追踪，不能替代 command identity。

## 2. HTTP 通用规则

### 2.1 成功和错误 envelope

所有成功响应使用：

```json
{
  "data": {},
  "meta": { "request_id": "REQUEST_ID" }
}
```

所有错误响应使用：

```json
{
  "error": {
    "code": "stable_error_code",
    "message": "Log-safe message",
    "retryable": false,
    "details": null
  },
  "meta": { "request_id": "REQUEST_ID" }
}
```

外部 JSON 字段统一 `snake_case`。列表和事件游标放在 `data.next_cursor`，不放在
`meta`。BFF 不接收浏览器传入的 tenant、subject、actor 作为可信身份字段。

### 2.2 Header 规则

```http
Content-Type: application/json
Idempotency-Key: IDEMPOTENCY_KEY
```

会产生事实变化的 POST 必须携带 `Idempotency-Key`。BFF 将 key 与已验证身份、操作名、
资源 ref 和 canonical request digest 绑定；同 key 同 payload 重放原始 receipt，同 key
不同 payload 返回 `idempotency_key_reused`，并发处理中返回 `idempotency_in_progress`。

查询不使用随机 offset；列表使用不透明 cursor。事件流使用 SSE，`Last-Event-ID` 只作
replay anchor，不作为业务状态字段。

## 3. 资源状态

### 3.1 Generation

```text
queued → preparing → generating → post_processing → succeeded
                                      ├──────────────→ failed
queued/preparing/generating ─────────┴──────────────→ cancelled
queued/preparing/generating/post_processing ────────→ expired
```

终态为 `succeeded`、`failed`、`cancelled`、`expired`。取消是独立命令；网络断开不代表
取消。生成成功后 Candidate 由 Generation 关联，Promote 才创建或确认一个 Version。

### 3.2 Version

Version 是不可变音频快照；项目的 `current_version_ref` 是可变指针。旧版本保留为
`draft` 或 `archived`，不能通过修改 Version 本身改变音频事实。

## 4. 端点

### 4.1 Project

```http
POST /api/v1/projects
GET  /api/v1/projects?cursor=CURSOR&limit=20
GET  /api/v1/projects/{project_ref}
```

创建请求：

```json
{ "title": "First Light", "description": "A patient song about finding your way home." }
```

项目详情至少返回：

```json
{
  "project_ref": "PROJECT_REF",
  "title": "First Light",
  "description": "...",
  "current_version_ref": "VERSION_REF",
  "candidate_count": 2,
  "last_activity_at": "2026-09-02T12:00:00Z"
}
```

### 4.2 Song Plan

```http
POST /api/v1/projects/{project_ref}/song_plans
```

```json
{
  "prompt": "A warm late-night track for the drive home.",
  "mood": "warm hopeful",
  "tempo_bpm": 102,
  "structure": ["intro", "verse", "lift", "chorus", "outro"],
  "instruments": ["soft_synth", "muted_guitar", "brush_drums"],
  "vocal_direction": "intimate lead vocal with a gentle lift in the chorus",
  "lyrics_intent": "small moments becoming a reason to keep going"
}
```

### 4.3 Generation

```http
POST /api/v1/projects/{project_ref}/generations       → 202
GET  /api/v1/generations/{generation_ref}
GET  /api/v1/generations/{generation_ref}/events      → text/event-stream
POST /api/v1/generations/{generation_ref}/cancel      → 202
```

生成请求：

```json
{
  "song_plan_ref": "SONG_PLAN_REF",
  "mode": "smart",
  "prompt": "A warm late-night track for the drive home.",
  "lyrics": null,
  "lyrics_mode": "instrumental",
  "style": "dream_pop intimate organic",
  "reference_asset_refs": [],
  "voice_ref": null,
  "duration_seconds": 180
}
```

`202` receipt 只携带业务资源和状态，request tracking 位于 `meta`：

```json
{
  "data": {
    "generation_ref": "GENERATION_REF",
    "status": "queued"
  },
  "meta": { "request_id": "REQUEST_ID" }
}
```

### 4.4 Generation events

```http
GET /api/v1/generations/{generation_ref}/events
Accept: text/event-stream
Last-Event-ID: GENERATION_REF:12
```

事件 id 是服务端生成的 replay cursor；事件 data 仍使用 Mori envelope：

```text
id: GENERATION_REF:13
event: generation.progress
data: {"data":{"generation_ref":"GENERATION_REF","status":"generating","progress":64},"meta":{"request_id":"REQUEST_ID"}}
```

终态事件必须可回放。客户端刷新时先读取 Generation 快照，再从最近的 `Last-Event-ID`
继续事件流；客户端不自行推进 cursor 或推断终态。

### 4.5 Candidates and Versions

```http
GET  /api/v1/projects/{project_ref}/candidates?cursor=CURSOR
POST /api/v1/candidates/{candidate_ref}/promote       → 201
POST /api/v1/versions/{version_ref}/remix             → 202
```

Candidate 公开字段包含 `candidate_ref`、`generation_ref`、`title`、`duration_seconds`、
`audio_asset_ref`、`waveform_asset_ref`、`style_tags` 和 `created_at`。Promote 返回新
Version 的 `{version_ref, project_ref, source_candidate_ref, status}`。

### 4.6 Library and Export

```http
GET  /api/v1/library?kind=all&cursor=CURSOR&limit=20
POST /api/v1/versions/{version_ref}/exports                  → 202
GET  /api/v1/exports/{export_ref}
```

Library 是跨 Project 的只读 projection；筛选参数属于 Library 查询，不提升为全局导航。
Export 是异步资源，下载地址只由 BFF 在权限校验后返回短时 projection，不把对象存储
路径或 provider 地址写入浏览器契约。

## 5. Mori 前端 seam 映射

`src/lib/mori-api.ts` 只承载浏览器可见的请求与 receipt 类型：

```text
CreateDraft → createGenerationRequest() → POST /api/v1/projects/{ref}/generations
                                             + Idempotency-Key
202 receipt  → GenerationControllerState → GET snapshot / SSE replay
```

预览 adapter 可以返回 fixture，但必须保持相同 envelope 和字段命名。真实接线时新增
同源 fetch adapter，不改组件使用的 domain 对象，不让组件直接读取 provider response。

## 6. 必须覆盖的契约测试

1. 每个成功响应都有 `data` 和 `meta.request_id`。
2. 每个错误响应都有稳定 `error.code`、`error.retryable` 和 `meta.request_id`。
3. 外部 JSON 没有 camelCase、provider 字段或顶层分页 cursor。
4. 相同 `Idempotency-Key` + 相同 digest 重放原 receipt；不同 digest 被拒绝。
5. Generation 状态迁移、取消和终态事件可回放。
6. SSE 从 `Last-Event-ID` 后继续，不重复消费已确认事件。
7. BFF 不信任浏览器提交的 tenant/subject/provider 字段。
