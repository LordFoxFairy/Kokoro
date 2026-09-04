# ADR-029 System Model Catalog 与 Platform 边界收敛

状态：已接受，待 clean-slate 实施（2026-09-04）。

## 背景

当前拓扑把 Model Catalog/Provider/Routing 单独放在 `kokoro-model`，把 Skills/MCP 控制面放在
`kokoro-capability`，同时历史 `kokoro-platform` 已归档。V1 尚无独立 Model 团队、生产 SLO 或容量证据；继续维护
独立 Model 服务会增加数据库、Redis、镜像、凭据、RPC 和故障点。产品后续还需要一个明确承载 Agent 中间能力的
Platform owner。

## 决策

1. `kokoro-model` 合入 `kokoro-system`，成为 `model-catalog` 业务模块。
2. `kokoro-capability` clean-slate 重命名为 `kokoro-platform`。
3. Platform 首批一级业务域为 `skills` 和 `mcp`；未来中间平台能力必须单独 ADR 后加入。
4. 历史归档 `kokoro-platform` 的实现不恢复、不作为兼容层；目标实现从当前有效 Capability 事实重新收敛。
5. 两项拓扑变更分成独立实施目标，分别完整更新 contract、schema、service identity、配置、部署和消费者。

## System 内 Model Catalog 边界

```text
kokoro-system/src/modules/model-catalog/
  catalog/
  providers/
  revisions/
  routing/
  availability/
```

- `model-catalog` 保持 `model_*` 表、`kokoro.model.v1` 协议语义、独立权限和测试。
- System 其他模块不得直接查询 `model-catalog` 内部表；通过模块公开 Service API 交互。
- Model PostgreSQL 事实合入 System 的唯一 schema；Redis DB 3 退出，缓存并入 System namespace。
- Agent/BFF 只调用唯一模型解析/目录接口，删除本地重复解析和旧 Model service fallback。
- 出现独立团队、独立 SLO、显著流量/写入差异或强安全隔离证据时，可以按稳定 contract 重新拆出。

System 不是通用配置仓。新配置归入其业务事实 owner；只有具备独立身份、生命周期、权限、契约与查询模型时才
增加一级模块。禁止每新增一种配置就创建 `<name>-config`，也禁止任意 key/value `configs` 模块。

## Platform 边界

```text
kokoro-platform/src/modules/
  skills/
    catalog/
    revisions/
    packages/
    installations/
  mcp/
    providers/
    connectors/
    servers/
    connections/
    authorizations/
```

Platform 是 Agent Capability Control Plane，不是共享 helper 仓。新增一级模块必须有：

- 独立业务名和事实 owner；
- 明确状态、数据生命周期和 contract；
- tenant/authz/secret 边界；
- 运行、扩缩容、readiness、SLO 和故障恢复；
- 与现有 owner 的比较及未来拆分路径。

Skills 与 MCP 可使用同一仓、数据库和镜像，但可以拥有独立 runtime profile、workload identity、readiness 与扩缩容。
Skill installation 与 MCP connection 保持不同生命周期，不抽象为万能 `CapabilityService`。

## 淘汰方案

### 保留独立 `kokoro-model`

优点是部署隔离；缺点是当前没有相应团队/SLO/容量证据，且核心 Resolve 链路尚未形成足够收益。V1 不采用。

### 保留 `kokoro-capability` 名称

名称准确但不满足已确定的产品拓扑命名。改为 Platform，同时用模块准入规则防止范围无限扩张。

### 把所有“中间服务”直接放入 Platform

会形成无 owner 的垃圾桶。拒绝；每个新模块必须先通过上述准入 ADR。

## 实施约束

- 不保留兼容 service、旧环境变量 alias、旧 owner 名、双读、双写或 contract 副本。
- 先更新事实 owner contract，再更新消费者。
- V1 使用 fresh database，不迁移历史开发数据。
- 两项 cutover 各自形成可审查 commit/PR，并执行全仓 contract、integration、schema 和 smoke。
- 物理 cutover 完成前，`docs/CURRENT.md` 与 `docs/REPOSITORY_STATUS.md` 必须区分当前态和目标态。

## 结果

目标正式运行仓从十个收敛为九个；减少一个无独立运行依据的服务，同时建立边界明确、可扩展但受准入控制的
Platform owner。
