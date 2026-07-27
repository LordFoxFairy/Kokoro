---
artifact: superseded-implementation-plan
status: superseded
supersededBy: 2026-07-27-federated-repository-governance-correction-implementation-plan.md
repositoryTopology: federated-submodules-v1
---

# Wave 0 旧实现计划（已整体替代）

本文件原先包含 snapshot import、single-root-lock、移除 gitlink 和集中 CI/release 的错误路线。
这些任务不是“暂缓”，而是永久取消；不得从 Git 历史或旧引用恢复执行。

当前唯一执行计划：

[`2026-07-27-federated-repository-governance-correction-implementation-plan.md`](2026-07-27-federated-repository-governance-correction-implementation-plan.md)

稳定裁决：根仓长期保留 `.gitmodules` 和四个 mode-`160000` gitlink；四个子仓独立拥有 lock、CI、
artifact、部署、release、rollback 与历史，根仓只做 contract、Infra、兼容验证、BOM 和 pin promotion。
