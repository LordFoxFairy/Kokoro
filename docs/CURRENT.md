# 当前活跃文档白名单

状态：2026-07-25
用途：降低 agent 阅读负担。做当前 runtime / capability / deliver 主线时，默认只读这里列出的文档。

## 必读

1. [Codebase Map](CODEBASE_MAP.md)
2. [docs 总入口](README.md)
3. [Kokoro 总手册](kokoro-handbook/README.md)
4. [**Kokoro V1 最终技术方案（定稿事实源）**](kokoro-handbook/technical/20-kokoro-v1-technical-plan.md)

## 当前目标架构评审主线

以下文档描述尚未实现、正在书面复审的 clean-rewrite 目标。它们优先于旧过程稿，但在批准并迁入 handbook
前不得写成当前代码事实：

1. [整体业务、Platform、Web、Session 与 Agent 产品目标架构 v1.5](superpowers/specs/2026-07-25-platform-web-session-target-architecture-design.md)
2. [Production Delivery Program](superpowers/plans/2026-07-25-kokoro-production-delivery-program.md)
3. [Wave 0 Repository/Toolchain/Contract Foundation v1.2](superpowers/specs/2026-07-25-wave-0-repository-contract-foundation-design.md)
4. [产品需求治理、Launch Profile 与 PRD Registry](superpowers/specs/2026-07-25-product-requirements-governance-and-prd-registry-design.md)
5. [Model Control、Model Gateway 与 LiteLLM 目标架构](superpowers/specs/2026-07-25-model-control-gateway-litellm-architecture-design.md)
6. [PRD-00 Launch Profile 与 Journey Contract](superpowers/specs/2026-07-25-prd-00-launch-profile-and-journey-contract.md)
7. [PRD-01 Site Identity 与 Account Security](superpowers/specs/2026-07-25-prd-01-site-identity-and-account-security.md)
8. [PRD-02 Workspace、Membership 与 Project](superpowers/specs/2026-07-25-prd-02-workspace-membership-and-project.md)
9. [PRD-03 Account、Plan、Redeem 与 Credit](superpowers/specs/2026-07-25-prd-03-account-plan-redeem-and-credit.md)
10. [PRD-04 Checkout、Subscription 与 Billing](superpowers/specs/2026-07-25-prd-04-checkout-subscription-and-billing.md)
11. [PRD-05 Chat Conversation、Run 与 Interaction](superpowers/specs/2026-07-25-prd-05-chat-conversation-run-and-interaction.md)
12. [PRD-06 Asset Intake 与 Attachment Safety](superpowers/specs/2026-07-25-prd-06-asset-intake-and-attachment-safety.md)
13. [PRD-11 Support、Recovery 与 Appeals](superpowers/specs/2026-07-25-prd-11-support-recovery-and-appeals.md)
14. [PRD-12 Site Lifecycle 与 Fleet](superpowers/specs/2026-07-25-prd-12-site-lifecycle-and-fleet.md)
15. [PRD-14 Localization 与 Accessibility](superpowers/specs/2026-07-25-prd-14-localization-and-accessibility.md)
16. [PRD-15 Notification、Preferences 与 Data Rights](superpowers/specs/2026-07-25-prd-15-notification-preferences-and-data-rights.md)
17. [PRD-16 Trust、Content Safety 与 Media Rights](superpowers/specs/2026-07-25-prd-16-trust-content-safety-and-media-rights.md)
18. [全项目模块、能力与闭环覆盖审计](reports/2026-07-25-kokoro-module-capability-coverage-audit.md)
19. [Redeem-first Production Launch Checklist](reports/2026-07-25-kokoro-production-launch-readiness-checklist.md)

## 当前技术主线

1. [V1 最终技术方案（定稿）](kokoro-handbook/technical/20-kokoro-v1-technical-plan.md)
2. [Platform × 主链闭环（正式册,P1-P5 已落地事实）](kokoro-handbook/technical/21-platform-mainchain-closure.md)
3. [跨仓闭环与遗留对齐总设计（待评审纲领,Wave 0-6）](superpowers/specs/2026-07-11-cross-repo-closure-and-legacy-alignment-design.md)
4. [能力中台正式册](kokoro-handbook/technical/22-capability-hub.md)（历史入口:specs/2026-07-11-capability-hub-and-polish.md）
5. [WP-0 落地与审核交接](handoffs/2026-07-09-wp0-landing-and-next-review-handoff.md)
6. 扩展附录（查细节才读，冲突以 20 为准）：[19 评审版全记录](kokoro-handbook/technical/19-current-runtime-capability-review-plan.md)、[18 详细附录](kokoro-handbook/technical/18-capability-namespace-auth-sandbox-artifacts.md)
7. 历史派工单（已过期，不作架构事实）：[2026-07-07 runtime buildout](handoffs/2026-07-07-runtime-buildout-next-handoff.md)、[2026-07-07 capability buildout](handoffs/2026-07-07-capability-buildout-handoff.md)

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
