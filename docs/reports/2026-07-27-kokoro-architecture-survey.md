---
artifact: architecture-survey
version: "1.0"
created: 2026-07-27
status: current-fact
scope: repository-topology-process-roles-boundary-protocols-isolation-governance
---

# Kokoro 架构梳理（当前事实）

本文只写**已经存在于代码和门禁里的事实**，不写目标架构。目标架构在
`docs/superpowers/specs/`，尚未批准实现。

## 1. 一句话系统定义

Kokoro 是一台 **federated 多仓通用 agent 引擎**：`kokoro-web` 出浏览器面，`kokoro-session` 拥有会话与
浏览器传输，`kokoro-platform` 拥有平台业务域（身份/站点/模型/积分/支付/能力中台），`kokoro-agent` 是
LangGraph/DeepAgents 执行运行时。四者是**独立仓库、独立 lock、独立 CI、独立 artifact、独立 rollback**，
只通过版本化协议通信。

## 2. 仓库拓扑与所有权

根仓 `Kokoro/` 保留 `.gitmodules` 与四个 mode-`160000` gitlink，**不吸收子仓 source**。

| 边界 | 路径 | 归根仓所有的东西 |
|---|---|---|
| `root.superproject` | `.` | pin manifest、architecture manifest、治理门 |
| `root.contract` | `contract/` | 跨仓契约唯一真源（protobuf + spec YAML）与生成器 |
| `root.scripts` | `scripts/` | 治理/基建/兼容性门禁 |
| `root.deploy` | `deploy/` | 单机 compose 与 k8s 编排 |
| `root.ops` | `ops/` | 可观测性栈 |

pin 权威是 `config/repository/federated-repositories.json`：每仓一条 `pin`（精确 commit）+
**每仓独立**的 `recoverableRef`（annotated tag）。校验器 `scripts/repository/verify-federated-repositories.mjs`
支持 `--tree index|head` 与 `--remote`。

架构清单 `config/architecture/index-roots.yaml` 登记 **57 个 root：23 boundary + 34 component**。
`kokoro-platform` 内部再分 10 个 module boundary（credit / hub / litellm / model / payment / admin /
kit / site / user / deploy.docker）。

## 3. 跨边界协议清单（这是当前最重要的事实）

`config/repository/compatibility-matrix.json` 声明 5 条契约，全部有真实运行时场景覆盖：

| 契约 | provider → consumer | 传输现状 |
|---|---|---|
| `session-browser` v1 | session → web | HTTP/JSON + SSE |
| `platform-runtime` v1 | platform → session | HTTP/JSON，Zod mirror 由 `contract/spec` 生成 |
| `session-agent-execution` v1 | agent → session | Redis streams + durable outbox/inbox |
| `model-gateway` v1 | platform → agent | HTTP/JSON（LiteLLM 门面） |
| `platform-admin-auth` v1 | platform → web | **protobuf / Connect（唯一已上线的 RPC 服务）** |

**诚实结论：内部 RPC 只完成了 1/5。** `platform-admin-auth v1` 是唯一走 protobuf/Connect 的服务，
带 protovalidate 约束、`CommandIdentity`/`CommandReceipt` 幂等信封、`GetCommandReceipt` 超时对账口，
以及 `RetryClass` 错误分类。其余内部调用仍是：

- `contract/spec/*.yaml` 生成的 Zod mirror（19 份，字节级校验）——有 schema，但没有服务定义、没有方法级契约；
- `kokoro-platform/kokoro-platform-kit/src/http/internal-client.ts` 的 `callService`——**stringly-typed**：
  path 是字符串、响应 schema 由**调用方**自己声明，服务端与客户端之间没有编译期链接。
  现存 4 处：`payment→credit`、`credit→site`、`credit→user`、`hub→user`。

`callService` 里还留着一处 `@deprecated` legacy 单一共享密钥模式——项目未上线，这是应删的兼容残留。

### 3.1 为什么用 protobuf/Connect 而不是 tRPC

tRPC 的核心价值是**同一个 TypeScript 类型图内**由 router 类型推导出客户端类型。本项目两个硬条件让它失效：

1. 四个仓是**独立仓库**，没有共享 TS 类型图。tRPC 跨仓要么发 npm 包，要么生成 `.d.ts` 镜像——
   一旦走生成，就已经是 codegen，tRPC 的推导优势消失。
2. `kokoro-agent` 是 **Python**。`model-gateway` / `session-agent-execution` 两条契约跨语言，
   tRPC 无法覆盖，会被迫引入第二套 RPC 机制。

protobuf + buf 同时满足：单一契约真源、TS 与 Python 都能生成客户端、`buf breaking` 提供跨版本兼容门、
Connect 同时支持 HTTP/JSON 与二进制。因此**保留 protobuf/Connect 作为内部 RPC 权威**，把
`callService` 逐服务迁上去，而不是再引入 tRPC。

## 4. 隔离模型

两个隔离键，语义严格分离，不可混用：

- **`siteId`** = platform 业务隔离边界。由边缘从 host/会话解析，内部逐 hop 收窄，owner 在 effect point 强制。
- **`namespace`** = GA（`kokoro-agent` runtime）**唯一**隔离键，opaque id，不拼 `user:<id>` 业务前缀。
  GA 不消费 `siteId` / `userId` / `ownerId` / `workspaceId`。

当前 `siteId` 以 request context header 形态流转，**由每条路由各自再派生**，尚未成为内部 RPC 信封的
一等字段。这是隔离模型最薄的一环。

## 5. 已真实强制的治理门

根仓 CI（`.github/workflows/contract.yml`）与本地同一套命令，全部在干净 recursive clone 复现通过：

| 门 | 当前数字 |
|---|---|
| federated pin + remote recoverableRef 校验 | 4 仓 |
| contract 字节镜像校验 | 19 mirror |
| contract 生成器与契约测试 | 35 passed |
| buf format / lint / breaking | pass |
| 生成 RPC 契约镜像一致性 | pass |
| architecture 治理测试 | 15 passed |
| INDEX 覆盖门 | 57 roots |
| 依赖方向门 | 57 roots / 13 internal package edges |
| repository 治理测试 | 72 passed |
| Python 兼容适配器测试 | 6 passed |
| 真基建运行时兼容性门 | 5 场景全 pass（mysql/redis/mongo/minio/litellm） |

依赖方向门是 fail-closed 的：禁止 sibling source import、禁止跨仓共享进程内对象、
禁止跨服务写私有 DB。这是「后续可拆分」真正的保障——不是靠 review 记住，而是靠门禁挡住。

## 6. 代码与测试基线

| 仓 | source 文件 | 测试文件 | INDEX.md |
|---|---:|---:|---:|
| kokoro-agent | 132 | 45 | 5 |
| kokoro-platform | 390 | 150 | 13 |
| kokoro-session | 84 | 32 | 6 |
| kokoro-web | 251 | 63 | 24 |
| 根仓 | — | — | 5 |

四个子仓各自 remote CI 在本轮候选 SHA 上均 success。

## 7. 诚实差距清单（按优先级）

1. **内部 RPC 只迁了 1/5 契约。** 4 处 `callService` 仍是 stringly-typed，响应 schema 由调用方声明，
   服务端改形状不会让调用方编译失败。
2. **`siteId` 不是 RPC 信封的一等字段**，靠每条路由自觉派生；缺跨 site / 跨 environment replay 的
   否定矩阵。
3. **`callService` 的 `@deprecated` legacy 共享密钥模式未删**（未上线不需要兼容）。
4. **`kokoro-agent` 无 `.python-version`**：`requires-python = ">=3.11"`，本机 `uv` 解析到 3.14，
   子仓 CI 用 3.11——同一 lock 在不同解释器下跑，determinism 有缺口。
5. **`freeze-snapshots.mjs` 仍服务已废弃的单体 monorepo baseline**，与 federated manifest 方向不一致。
6. **session `legacy-admission-adapter.ts` 的 unknown / not_found 未实现真 Admission RPC**——
   归 Wave 3，不得当作已完成。

## 8. 相关文档

- [Codebase Map](../CODEBASE_MAP.md)
- [当前活跃文档白名单](../CURRENT.md)
- [Platform Modular Core 与 Internal RPC](../superpowers/specs/2026-07-25-platform-modular-core-internal-rpc-design.md)
