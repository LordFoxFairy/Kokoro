# kokoro-hub 能力中台（历史 legacy）

> 状态：历史 Hub 实现记录，不是当前 owner 规则。当前分界以
> [Agent 设计卡](../technical/backend-design/09-agent.md)、
> [Agent 专项 §6](kokoro-agent.md#6-数据-owner唯一-writer-与当前原型边界) 和
> [Capability × Storage §9](../technical/29-capability-storage-runtime-architecture.md#9-artifact-与-agentsession-协作) 为准。
>
> 本文记录的“Hub 写、Agent 直读同库”和启动期 seed 行为已经进入删除迁移面：GA 原生
> DeepAgents Skill 默认由 GA 直接绑定；其余由 GA `find_skills/load_skill` 发现自身 catalog 与 CA user/session
> path；CA/Storage 只提供来源辅助，加载后成为 GA runtime state。

迁移期名称曾为 `kokoro-hub`，目标能力按上面的两条来源路径拆分。下文仅保留历史链路和
迁移取证，不能据此新增 Hub 写面或 Agent 对 Hub Mongo/S3 的直读。

## 职责

skill / MCP 的**管理写面**：注册、上传（GitHub 导入 preview→confirm）、审核状态机、版本历史、per-user/官方启停、namespace 配额、运营位。落位在 platform workspace 内（`@kokoro/hub`，与 user/credit 平级），复用 platform-kit（envelope/健康检查/启动器/admin manifest）与部署编排；服务端口 4251，主存储 Mongo（包体走 S3）。

## 三权限面（见 [specs/2026-07-12-wave1-hub-authz-and-mcp-revision](../../superpowers/specs/2026-07-12-wave1-hub-authz-and-mcp-revision.md)）

按调用方等级分三前缀（合流 TRUST-ROUTES caller 框架，见 [technical/23](../technical/23-platform-ops-console.md) §6）：

- **runtime resolver**（`/hub/runtime/**`，仅 session runtime caller）：按已验 namespace 返回有效池，供装配热路径读。
- **namespace self-service**（`/hub/self/**`，仅 web-bff caller）：scope 恒等于信封 namespace（路由不收 scope）；skills 读写开放，**MCP 只读**（mutation fail-closed，HUB-CONSIST 跨仓 E2E 过后才开）。
- **official/admin**（`/hub/admin/**`，仅 admin 网关代理）：审核、curation、official flags、跨 namespace 运营。

## 读写分离边界

**历史实现**为“hub 写、agent 读，读写分离同库”：hub 写 Mongo + S3，Agent 装配热路径直读同库。这条规则不再用于新实现；它既混淆 GA 原生配置与 Client/租户 Skill，也让 worker 依赖 legacy 物理存储。目标是 GA default binding + `find_skills/load_skill`/CA path 两条稳定来源路径，均不在 worker 中 seed/upsert。

## 与 session / agent 的关系

- **session**：池查询经 hub（`GET /hub/skills/pool`），是 session `pool.ts` 与 agent 旧双实现的收敛终点，单实现消除漂移。
- **agent（历史）**：曾直读 hub 写入的 Mongo skill/MCP 注册数据与 S3 包体。目标实现改为：GA 默认配置直接绑定；其余 Skill 由 `find_skills/load_skill` 发现 GA catalog 与 CA path；注入、物化、MCP 懒连接仍由 GA runtime 负责。
</content>
