# ADR-007 四个独立仓库纳入受控 Submodule

repositoryTopology: federated-submodules-v1

状态：已采纳；2026-07-27 扩展为四仓永久治理裁决。

## 背景

Kokoro 需要同时满足两件事：从一个根 commit 可复现完整系统组合；Agent、Platform、Session、Web 又必须
独立构建、部署、扩缩容、发布和回滚。把源码导入一个 root workspace 会消除第二项能力；让 CI checkout
浮动 sibling branch 又会破坏第一项能力。

## 决策

根仓通过 `.gitmodules` 永久管理以下四个独立 Git 仓库：

- `kokoro-agent`
- `kokoro-platform`
- `kokoro-session`
- `kokoro-web`

根 tree 对四个路径只记录 mode-`160000` gitlink。子仓分别拥有 branch、lock、CI、artifact、migration、
release、rollback 与版本历史；根仓只记录经过 contract/compatibility/E2E 验证的一组 pin，并管理 root Infra、
BOM 与 promotion evidence。

跨仓调用只走版本化 HTTP/RPC、SSE 或 durable async command/event transport。不得导入兄弟仓私有源码、
共享进程内对象或跨服务直写数据库。生成 contract mirror 是消费仓提交的公开边界产物。

## Promotion

1. 子仓 commit 先通过本仓 lock-driven CI。
2. commit 推送到本仓 remote，并由新的 recoverable tag 精确锚定。
3. 根仓在 proposed gitlink 上运行 contract、compatibility matrix 和 root Infra E2E。
4. 根仓原子提交 gitlink、manifest、contract mirror 与 evidence。
5. clean recursive clone 和远端 root CI 通过后创建 root BOM tag。

`.gitmodules` 只声明 name/path/url，不声明浮动 branch 或自定义 update command。生产和 CI 禁止
`git submodule update --remote`。回滚通过新的 root revert 恢复上一组 pin；不得 force-update branch/tag。

## 影响

- 一个子仓故障可以单独回滚服务；根仓组合也可以整体回退。
- Root-only tooling lock 不得吸收任何子仓依赖，子仓 lock 永远独立。
- Platform 内部可按模块和 RPC adapter 支持独立部署，但“可部署”本身不足以创建新仓库。
- 新增第五个子仓需要新的 ADR，证明所有权、发布、安全或规模边界，而不是只证明代码能拆开。

相关：[仓库地图](../technical/01-repository-map.md)、[Wave 0 v2.0](../../superpowers/specs/2026-07-25-wave-0-repository-contract-foundation-design.md)。
