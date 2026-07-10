# 当前活跃文档白名单

状态：2026-07-10
用途：降低 agent 阅读负担。做当前 runtime / capability / deliver 主线时，默认只读这里列出的文档。

## 必读

1. [Codebase Map](CODEBASE_MAP.md)
2. [docs 总入口](README.md)
3. [Kokoro 总手册](kokoro-handbook/README.md)
4. [**Kokoro V1 最终技术方案（定稿事实源）**](kokoro-handbook/technical/20-kokoro-v1-technical-plan.md)

## 当前技术主线

1. [V1 最终技术方案（定稿）](kokoro-handbook/technical/20-kokoro-v1-technical-plan.md)
2. [WP-0 落地与审核交接](handoffs/2026-07-09-wp0-landing-and-next-review-handoff.md)
3. 扩展附录（查细节才读，冲突以 20 为准）：[19 评审版全记录](kokoro-handbook/technical/19-current-runtime-capability-review-plan.md)、[18 详细附录](kokoro-handbook/technical/18-capability-namespace-auth-sandbox-artifacts.md)
4. 历史派工单（已过期，不作架构事实）：[2026-07-07 runtime buildout](handoffs/2026-07-07-runtime-buildout-next-handoff.md)、[2026-07-07 capability buildout](handoffs/2026-07-07-capability-buildout-handoff.md)

## 稳定架构入口

- [仓库地图](kokoro-handbook/technical/01-repository-map.md)
- [Agent / Session / Web V1 运行时](kokoro-handbook/technical/11-agent-session-web-v1-runtime.md)
- [V2 技术方案](kokoro-handbook/technical/15-v2-technical-plan.md)
- [能力中台、namespace、登录、沙箱与产物正式技术方案](kokoro-handbook/technical/18-capability-namespace-auth-sandbox-artifacts.md)
- [Skill Hub 与 MCP Hub 产品手册](kokoro-handbook/product/06-skill-hub-and-mcp-hub.md)

## 默认不读

这些目录是历史、过程、原型或研究材料。除非任务点名，否则不要让 agent 展开：

```text
product/
prototypes/
research/
brainstorm/
plans/
superpowers/plans/
```

需要考古时，先在 `docs/README.md` 判断目录性质，再打开具体文件。
