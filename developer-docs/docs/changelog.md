# 变更记录

## 2026-09-04 · Developer 门户完善

- 将阅读入口、导航、平台行为和工作流说明统一为中文，并明确 contract fact、客户端策略和当前缺口的边界。
- reference 生成器现在展示 owner、visibility、stability、idempotency、permission、security、参数约束、嵌套字段、组合 schema、response header 和示例。
- 增加 canonical 与 generated publication policy，校验 metadata 枚举、`Idempotency-Key` 一致性、危险内容和受管输出路径。
- TypeScript 生命周期示例改为增量消费长连接 AG-UI，在等待审批后 resume，并用 `Last-Event-ID` 重连；fixture 以分块且保持连接的方式验证该顺序。

## 2026-09-04 · Portal Phase 1

- 建立从固定 `kokoro-bff` public v1 artifact 生成 reference 的流程，当前目录枚举 63 个 public operation。
- 提供无真实凭据的 cURL、TypeScript、Python 示例，并由本地 fixture 执行。
- 加入概念、生命周期、平台行为、provenance、搜索和响应式导航。

## API `1.0.0` beta

- public 路径空间为 `/v1`，当前 operation 标记为 beta。
- AG-UI public frame 使用 BFF 拥有的 opaque `agui_*` cursor。
- canonical contract 当前没有 webhook registration、delivery 或 signature-verification operation；门户不会把内部 callback 写成 public API。
