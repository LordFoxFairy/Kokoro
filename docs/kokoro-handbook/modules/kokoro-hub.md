# kokoro-hub 能力中台

状态：正式册（HUB-1/2/3 已落地，HUB-4 部分；边界规则长期有效）
边界与内部通信定案见 [technical/22-capability-hub](../technical/22-capability-hub.md)。

## 职责

skill / MCP 的**管理写面**：注册、上传（GitHub 导入 preview→confirm）、审核状态机、版本历史、per-user/官方启停、namespace 配额、运营位。落位在 platform workspace 内（`@kokoro/hub`，与 user/credit 平级），复用 platform-kit（envelope/健康检查/启动器/admin manifest）与部署编排；服务端口 4251，主存储 Mongo（包体走 S3）。

## 三权限面（见 [specs/2026-07-12-wave1-hub-authz-and-mcp-revision](../../superpowers/specs/2026-07-12-wave1-hub-authz-and-mcp-revision.md)）

按调用方等级分三前缀（合流 TRUST-ROUTES caller 框架，见 [technical/23](../technical/23-platform-ops-console.md) §6）：

- **runtime resolver**（`/hub/runtime/**`，仅 session runtime caller）：按已验 namespace 返回有效池，供装配热路径读。
- **namespace self-service**（`/hub/self/**`，仅 web-bff caller）：scope 恒等于信封 namespace（路由不收 scope）；skills 读写开放，**MCP 只读**（mutation fail-closed，HUB-CONSIST 跨仓 E2E 过后才开）。
- **official/admin**（`/hub/admin/**`，仅 admin 网关代理）：审核、curation、official flags、跨 namespace 运营。

## 读写分离边界

**hub 写、agent 读，读写分离同库**：hub 是唯一写入方（Mongo + S3）；agent 装配热路径**直读同库**，不经 hub RPC。每 run 跨服务调 hub 是可用性耦合，明确禁止。双层守门（hub 入库校验 + agent 装配防御校验）不算重复，是信任边界各自校验。

## 与 session / agent 的关系

- **session**：池查询经 hub（`GET /hub/skills/pool`），是 session `pool.ts` 与 agent 旧双实现的收敛终点，单实现消除漂移。
- **agent**：直读 hub 写入的 Mongo skill/MCP 注册数据与 S3 包体，装配 resolve_cards/物化/MCP 懒连接；不写 hub，不面向浏览器。
</content>
