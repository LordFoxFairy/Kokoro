# Kokoro 主仓文档入口

主仓 `docs/` 是产品、架构、业务链路和跨仓规范的总入口。

- **总手册（权威）**：[`kokoro-handbook/`](kokoro-handbook/README.md) —— 产品形态、技术方案、模块边界、业务链路、运营和 ADR 的总入口。新设计一律从这里进入。
- **历史与协议材料**：`product/`、`protocol/`、`requirements/`、`research/`、`decisions/`、`plans/` 等保留既有设计与协议过程，不再作为全局总设计的权威来源。
- **架构审计**：[`reports/2026-06-27-three-repo-architecture-audit.md`](reports/2026-06-27-three-repo-architecture-audit.md) —— 三仓运行时重写与子模块拓扑的诊断依据。

## 治理规则

```text
1. docs/kokoro-handbook 是跨仓方案、模块职责、业务链路和 ADR 的总入口。
2. 子仓 docs 只写实现细节、调试和测试说明，不替代主仓手册。
3. 新关键决策必须先在 handbook 有入口，再落到子仓 README 或实现文档。
4. siteId 是第一业务隔离边界；web/gateway 不绕过 SiteContext。
5. 不新增 kokoro-contracts，不引入 PostgreSQL，不把 Redis 当长期真源。
```
