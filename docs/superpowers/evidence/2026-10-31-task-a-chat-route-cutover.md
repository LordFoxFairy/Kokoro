# Task A Chat archive/share route cutover（2026-10-31）

## 变更

- BFF `2df4bcc`（前序 `6de89c7`）：`ChatModule` 注册 `CHAT_SERVICE`，由唯一 `BFF_DATABASE` 构造 `ChatApplicationService`。
- 新增 `src/http/routes/chat-native.ts` 与 `src/modules/chat/chat.middleware.ts`，承接：
  - `GET /v1/account/archived-tasks`
  - `GET /v1/account/shared-tasks`
  - `GET/POST /v1/sessions/:id/archive`
  - `GET/POST /v1/sessions/:id/restore`
- `ChatMiddleware` 继续承接 `GET/PUT /v1/sessions/:id/messages/:message/feedback`，复用同一 `CHAT_SERVICE` 的 feedback read/CAS provider。
- 从 `handleBffRequest` 删除上述旧分支；`createBffServer` 仅通过显式 Chat adapter seam 兼容现有 raw HTTP fixture。
- `BffBusinessStore.chatService` 与 `BffServerComposition.chatService` 是过渡 seam；不复制 Chat repository、SQL、幂等或 admission 逻辑。

## 闭环证据

```text
route inventory
  → ChatModule/CHAT_SERVICE owner seam
  → chat-native adapter + middleware
  → 删除 server.ts 旧分支
  → architecture negative assertions
  → focused HTTP/admission tests
```

## 验证

- `pnpm typecheck`：通过。
- `pnpm build`：通过。
- `pnpm lint`：通过。
- `pnpm format:check`：通过。
- `node --test test/nest-feature-architecture.test.ts test/archived-tasks-http.test.mjs test/shared-tasks-http.test.mjs`：通过（38/38；包含 ChatModule ownership assertion）。
- `node --import tsx --test --test-concurrency=1 test/personal-file-upload.test.mjs`：通过（11/11）；验证 partial `businessStore` fixture 不因 Chat provider seam 崩溃。
- `pnpm test:nest-architecture`：12/12 通过，包含 Chat feedback adapter ownership 与 Agent/Chat module graph 断言。
- build-output focused HTTP fixtures：message feedback、run display、project binding 合计 78 项通过。
- 历史切片基线曾为 2296 tests，2240 pass，54 fail，2 skip；C-4 后已由 v28.18 Account profile inverse、IAM 0.18/profile-read governance 与 build-output fixture 收敛。最新 BFF 串行 `pnpm test` 为 2309 tests，2307 pass，0 fail，2 skip；Chat feedback/run-display/project-binding focused 78/78 通过。2 个 skip 仍是资源门禁保护的真实 PostgreSQL 条件测试，不计为通过。

## 未关闭项

- `LegacyRoutesRuntime`、`handleBffRequest` 和 `BffBusinessStore` 仍承载未迁移 route/worker，不能删除。
- C-1.3 真实 IAM cookie→BFF→IAM receipt、sign-in/sign-out/tenant-switch/revocation 旅程仍待环境与独立 evidence。
- A-01/A-02/A-07 继续停写。
