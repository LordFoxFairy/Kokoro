# Kokoro cross-repository contracts

当前 Goal 2 的七仓契约注册表见
[`goal2-repository-contract-manifest.json`](goal2-repository-contract-manifest.json)。它是根仓对
owner、文档、Root wire 文件、数据库基线和同步规则的机器可验证索引；七个 owner 的具体
请求/响应、状态机和错误投影仍以各仓 `API_CONTRACT`/API docs 为准。

正式业务 owner 只有：`kokoro-iam`、`kokoro-system`、`kokoro-model`、`kokoro-billing`、
`kokoro-capability`、`kokoro-storage`、`kokoro-scheduler`。Credit 已经是
`kokoro-billing` 的内部模块；MCP Connector 是 `kokoro-capability` 的 MCP 子域，不创建
新的顶层仓库。`kokoro-platform`、`kokoro-gateway`、`kokoro-session` 和旧 Site 不属于
Goal 2 新业务实现目标。

Goal 2 的根索引不把每个 owner 的 HTTP/config surface 伪装成一个重复的 Root Proto：
Model、Capability、Storage、IAM 的跨仓 wire 仍引用 Root Proto；Billing 的 v1 HTTP
surface 由本仓 OpenAPI 维护；System 的 control/manifest HTTP surface 和 Scheduler 的
configuration/internal-command surface 由各自 owner contract 维护。所有这些 owner
contract 都必须通过根索引和 mock closure gate。

```bash
python3 scripts/goal2/mock_cross_repository_closure.py
```

以下 Slice A 文件保留为既有 Web/BFF/Agent 兼容闭环的历史/并行契约输入，不替代 Goal 2
七仓注册表。

阶段 1 当前运行基线见 [storage-baseline-v1.md](spec/storage-baseline-v1.md)：新代码只使用
PostgreSQL + Redis，Chat 由 `kokoro-bff` 的 Chat 业务边界承接，Web/BFF/Agent 三仓闭环优先于
历史 Session/Gateway 和 MySQL/Mongo 迁移材料。下文中出现的旧 owner 名称仅作为历史生成来源，
不代表阶段 1 要重新创建或接入这些子仓库。

跨仓契约与 owner 技术方案的同步规则见 [51-跨子仓 API/AIP 契约与技术方案同步](../docs/kokoro-handbook/technical/51-cross-repository-contract-sync.md)。

`slice-a-contract-manifest.yaml` is the reviewed machine authority for the historical SQL-backed contract material. For the
current Phase 1 closure, the browser-facing source of truth is the BFF OpenAPI/contract excerpt documented in the three
active repositories; the root manifest remains an index and validation input, not a reason to create a new owner repository.
It renders:

- manifest 管理的 Protobuf files under `proto/` for Site, IAM, Chat, Agent, Model and Capability;
- separate owner contract slices for Storage and Credit are kept under the same `proto/` tree and have their own manifests/gates;
- the browser-only Web BFF contract at `openapi/slice-a-web-v1.yaml`;
- consumer-scoped TypeScript or Python artifacts declared by `consumers.yaml`.

Run the frozen local gates:

```bash
python3 contract/validate_slice_a_manifest.py contract/slice-a-contract-manifest.yaml
uv run python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --check
pnpm exec buf format --diff --exit-code contract/proto
pnpm exec buf lint contract
pnpm exec buf breaking contract --against contract/breaking/slice-a-v1.binpb
pnpm exec redocly lint contract/openapi/slice-a-web-v1.yaml
```

`contract/generate.py` reads only a caller-supplied clean Root commit and emits one declared consumer closure. Child repositories never modify Root Proto/OpenAPI or generated files by hand. Browser traffic remains Web BFF HTTP/SSE; service-to-service calls use generated Connect/gRPC contracts.

## 子仓同步边界

API/AIP 契约只在根仓 `contract/` 修改一次；阶段 1 的三个 active owner（Web、BFF、Agent）按
`consumers.yaml` 声明的 consumer closure 重新生成类型。子仓可以维护本仓的**契约摘录与实现说明**，但不能新增平行的
Proto、OpenAPI 或手写 DTO：

```text
Root contract/proto + manifest
  -> generated active consumers (Web / BFF / Agent)
  -> owner adapter + contract/projection tests
```

聊天边界也遵循同一规则：Root Chat DTO 定义跨仓字段；阶段 1 由 `kokoro-bff` 的 Chat 业务边界承接
Chat 业务与 HTTP 投影，`kokoro-agent` 只负责 Run 执行、事件产出、HITL 与恢复；不再创建独立
`kokoro-session` 或独立 `kokoro-chat` owner。LangChain checkpoint/message ID 不进入浏览器 Chat contract。实现细节分别记录在
`kokoro/docs/integration/chat-bff-contract-v1.md`、`kokoro-bff/docs/api/` 与 `kokoro-agent/docs/agent/api-contract.md`。

`root-e2e` is a test-harness consumer rather than a browser boundary. Its declared closure includes IAM authentication and authorization for the complete Refresh → Authorize → Logout lifecycle, while `kokoro` remains restricted to the browser-facing public closure.

`StreamConversationEventsResponse` uses an additive `payload` oneof: the existing
`BrowserSessionEvent event = 1` wire field is preserved and
`StreamConversationEventsReady ready = 2` is the explicit establishment signal. Chat emits
typed authentication, scope and cursor failures before any response; a successful stream
immediately emits exactly one `ready`, including when the validated cursor is already at the
watermark, and emits only `event` messages afterward. This Proto-only revision intentionally
does not change the browser OpenAPI/SSE document. Compatibility checks use the current generated
descriptor and verify that field-1 event bytes remain readable while older readers discard the
field-2 ready arm.

## 历史 Credit slice

`contract/legacy/credit/` 下的 Credit v1 Proto、消费者 manifest、buf 配置和测试是历史
兼容材料，不能再解释成独立 `kokoro-credit` owner 或 MySQL runtime。当前 Credit 的生产 owner
是 `kokoro-billing`，以其 `contract/openapi/v1/openapi.yaml` 与
`docs/API_CONTRACT.md` 为实现契约；Billing 内部负责 Credit account、Hold、Commit、
Refund、Ledger 的一致性。
