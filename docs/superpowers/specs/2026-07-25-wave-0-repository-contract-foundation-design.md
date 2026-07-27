---
artifact: architecture-spec
version: "2.0"
created: 2026-07-25
revised: 2026-07-27
status: approved-for-wave-0-implementation
repositoryTopology: federated-submodules-v1
---

# Wave 0：Federated Repository、Contract、Infra 与交付治理

## 1. 裁决

Kokoro 根仓是治理型 superproject，不是源码 monorepo。以下四个目录永久保持 `.gitmodules` 管理的
mode-`160000` gitlink：

- `kokoro-agent`
- `kokoro-platform`
- `kokoro-session`
- `kokoro-web`

每个子仓独立拥有源码、Git 历史、依赖锁、CI、构建产物、数据库迁移、发布、扩缩容和回滚。
根仓只拥有跨仓 contract 单源、root-only 工具链、Infra 与集成编排、兼容矩阵、BOM、验证证据和经过
评审的 gitlink pin promotion。

## 2. 为什么采用子仓

子仓边界服务于独立部署，而不是为了目录观感。任何一个服务都应能在不重建其他服务的情况下独立构建、
发布、扩缩容和回滚。根仓 pin 表示一组经过组合验证的版本，不接管子仓生命周期。

仓库边界与进程边界不机械等同。Platform 可以在同一仓内保留 modular core，并为需要独立部署的模块提供
RPC adapter；只有所有权、发布节奏、安全或规模边界真正独立时，才考虑新增仓库。

## 3. 运行时通信

跨仓运行时只允许版本化远程协议：

| 调用 | 协议 | 约束 |
|---|---|---|
| Web → Session | HTTP + SSE | Web 不直连 Agent 或业务数据库 |
| Session ↔ Platform | internal HTTP/RPC | Site、principal、credit、model binding 等由 Platform 决策 |
| Session → Agent | durable async request/event transport | Session 不执行 Agent；异步流不伪装成同步 RPC |
| Agent → Model Gateway/LiteLLM | versioned HTTP | GA 不拥有价格、积分或 provider 管理事实 |

禁止跨仓兄弟源码 import、共享进程内对象、构建时读取兄弟仓私有文件、跨服务直写数据库。生成的 contract
mirror 是各消费仓提交并验证的构建产物，不形成运行时根目录依赖。

## 4. 交付协议

1. 子仓变更先通过本仓 lock-driven CI。
2. 子仓 commit 推送到自己的 remote，并由新的可恢复 tag 精确锚定。
3. 根仓以候选 gitlink 运行 contract、兼容矩阵和 root Infra E2E。
4. 根仓原子提交 contract/evidence/manifest 与 gitlink 组合。
5. clean recursive clone 重放验证后才提升远端分支与 BOM tag。
6. 回滚通过新的 root revert 恢复上一组 pin；子仓仍可单独回滚服务。

禁止浮动 checkout sibling `main`、`git submodule update --remote`、删除 `.gitmodules`、普通目录导入、
合并子仓 lock、关闭子仓 CI 或归档子仓发布入口。

## 5. Wave 0 交付物

- 四仓 manifest：URL、pin、lock、required checks、artifact、protocol、recoverable ref。
- proposed-index 与 committed-HEAD 两种 exact-pin verifier。
- 根 contract CI 只初始化当前根 commit 的四个 gitlink。
- 四仓独立 CI；root-only 工具锁不吸收任何子仓依赖。
- exact-pin compatibility matrix 与 root Infra deterministic E2E evidence。
- clean clone、BOM、远端 CI、rollback rehearsal 证据。

## 6. 非目标

- 不在 Wave 0 修改 GA graph、checkpoint、handoff、tool 或 model runtime 语义。
- 不以“可独立部署”为由把 Platform 每个模块拆成新仓库。
- 不用根仓 CI 取代子仓测试，也不用子仓单测冒充跨仓兼容验证。

实施以
[`2026-07-27-federated-repository-governance-correction-implementation-plan.md`](../plans/2026-07-27-federated-repository-governance-correction-implementation-plan.md)
为唯一当前计划；旧 snapshot-import 任务已被本 v2.0 全文替代。
