# 当前活跃文档白名单

状态：2026-07-07
用途：降低 agent 阅读负担。做当前能力中台 / namespace / auth / sandbox / artifact 主线时，默认只读这里列出的文档。

## 必读

1. [Codebase Map](CODEBASE_MAP.md)
2. [docs 总入口](README.md)
3. [Kokoro 总手册](kokoro-handbook/README.md)
4. [Namespace 运行时隔离](kokoro-handbook/technical/17-namespace-runtime-isolation.md)

## 当前技术主线

1. [能力中台、namespace、登录、沙箱与产物正式技术方案](kokoro-handbook/technical/18-capability-namespace-auth-sandbox-artifacts.md)
2. [Capability Hub 设计](superpowers/specs/2026-07-07-capability-hub-design.md)
3. [产品化技术主图](superpowers/specs/2026-07-07-product-technical-roadmap.md)
4. [能力 buildout 派工单](handoffs/2026-07-07-capability-buildout-handoff.md)

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
