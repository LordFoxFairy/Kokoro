# ADR-032：Root Submodule 组合与远端仓标识

状态：已采纳，2026-09-19；2026-09-20 已按当时约束复核。2026-11-11 更正§3–4的开发分支／清理口径，§4.1历史验收事实保留，失效链接固定到原Git快照。

## 背景

Kokoro Root 当前混合了同级独立 checkout、一个旧路径 gitlink 和本地工作副本。`kokoro/` 实际指向
`LordFoxFairy/kokoro-app`，其目录名与 Root 名称和逻辑产品名产生歧义。`kokoro-mori` 是另一个可部署 Next.js
前端；`kokoro-web-shared` 是独立版本化的共享前端包。Mori P1 目录是 `kokoro-mori` 的 Git worktree，而不是另一个仓。

目标是一个可复现、可独立发布的 Git superproject：Root 记录明确的子仓 commit，子仓保持独立历史、锁文件、CI、
契约和发布。Root 不成为多语言源码 monorepo。

## 决定

### 1. 唯一仓标识

正式仓的唯一标识为其 GitHub `owner/repository` 中的 `repository` 名。该标识同时用于：

- Root `apps/` 或 `libs/` 下的物理路径；
- `.gitmodules` 的子模块名称；
- Root 拓扑、部署、发布清单、CI 与验证器的仓键。

因此现有 Web checkout `kokoro/` 的目标路径是 `apps/kokoro-app/`，而不是 `apps/kokoro/`。文档可用“Web”描述
职责，但不得以 `kokoro` 作为第二个仓名或路径 alias。

### 2. 组合分类

```text
apps/kokoro-app/        LordFoxFairy/kokoro-app        可部署 Web
apps/kokoro-mori/       LordFoxFairy/kokoro-mori       可部署 Mori Web
apps/kokoro-bff/        LordFoxFairy/kokoro-bff        服务
apps/kokoro-agent/      LordFoxFairy/kokoro-agent      服务
apps/kokoro-iam/        LordFoxFairy/kokoro-iam        服务
apps/kokoro-system/     LordFoxFairy/kokoro-system     服务
apps/kokoro-billing/    LordFoxFairy/kokoro-billing    服务
apps/kokoro-capability/ LordFoxFairy/kokoro-capability 服务
apps/kokoro-storage/    LordFoxFairy/kokoro-storage    服务
apps/kokoro-scheduler/  LordFoxFairy/kokoro-scheduler  服务
libs/kokoro-web-shared/ LordFoxFairy/kokoro-web-shared 独立版本化共享包
```

`kokoro-mori` 与 `kokoro-web-shared` 已建立正式远端、默认分支为 `main`，并在进入本清单前完成首次 push 与单仓验证。没有 `origin` 的本地目录不得伪装成已可复现的子模块。

当前正式服务 owner 仍是既定九个；Mori 增加的是独立部署的前端产品，`web-shared` 是包边界，不取得服务 owner 数据库、
契约或写入权。`kokoro-model` 是已裁决合入 System 的历史 checkout，不进入组合。`kokoro-capability` 到
`kokoro-platform` 的仓名/远端/身份 clean-slate cutover 保持独立 ADR 与独立发布，不通过路径 alias 提前伪装完成。

### 3. 分支与版本政策

`main`是集成基线，开发使用短期分支并经已审查／已验证PR合入；其他人的执行中topic分支合法存在。只在自有PR合并、分支无合并后新增提交且无未交接工作时清理对应分支／worktree，不要求全远端仅有main，不触碰他人工作。需要保留的唯一证据或本地改动先在Root外归档；归档不是发布组合。精确gitlink检出的子仓可合法处于detached HEAD。

Root 使用 gitlink 锁定每个子仓的精确 SHA；`.gitmodules` 的 `branch = main` 仅作开发提示，绝不充当发布锁。禁止
`git submodule update --remote` 生成浮动发布组合。

### 4. 迁移与验证

先完成每仓 `main` 收敛，再在隔离 Root worktree 创建 `apps/`、`libs/` gitlink 并移除旧同级 gitlink/checkouts。当前组合已按此路径落地。
迁移完成后必须在新目录外验证：

```bash
git clone --recurse-submodules ROOT_URL fresh-kokoro
git -C fresh-kokoro submodule status --cached --recursive
python3 fresh-kokoro/scripts/verify-repository-topology.py
```

拓扑验证器检查精确清单、路径／配置remote与已初始化checkout HEAD是否匹配gitlink；不校验全远端分支清零，也不冒称已证明远端可获取或工作树clean。交付时另核已推送提交的可达性与自有工作区状态；子仓自己的lint/typecheck/test/build由owner负责。Root组合级contract/integration/e2e/smoke放在 `verification/`，
不得复制子仓 unit test 或机器契约。

### 4.1 2026-09-20 复核证据与边界

本 ADR 的结构性验收已在当前组合快照上实际执行：`verify-repository-topology.py` 为 `PASS`、`verify-main-only.py` 为
`PASS`、Root `scripts/tests` 为 `322 passed`。Root、11 个 submodule 以及各自 `origin` 都只列出 `main`，且不存在
`kokoro/` 或 `apps/kokoro/` 这类 Web alias。精确 gitlink SHA 由 [Root CURRENT](https://github.com/LordFoxFairy/Kokoro/blob/4addb02c72e4cb8a769d870f6e2ca60f6eb15a6b/docs/CURRENT.md#已锁定的组合) 记录。

这不等同于每个 owner 的生产质量验收。同期的 `verify-ten-repository-standard.py --format json` 诚实报告 110 个 owner
violation 和 1 个 System TypeScript `unverified`；owner 队列与修复顺序由 [Root CURRENT](https://github.com/LordFoxFairy/Kokoro/blob/4addb02c72e4cb8a769d870f6e2ca60f6eb15a6b/docs/CURRENT.md#明确的下一轮-owner-队列)
维护。Root 的 OpenAPI 词法 preflight 也不是完整 YAML parser，不能单独证明 malformed-contract 被拒绝；owner 的 canonical
parser/linter 仍是当前 parser 完整性证据，Root parser 替换须作为独立依赖治理切片完成。

## 放置与依赖裁决

| 项目 | 结论 |
| --- | --- |
| Owner | Root 拥有组合 gitlink、路径、发布清单与跨仓验证；各子仓继续拥有代码、契约、数据与内部测试。 |
| 当前事实 | 仅 Agent 是旧根路径 gitlink；其余服务是忽略的同级 checkout；Web 当前目录为 `kokoro/`；Mori P1 是 Mori worktree。 |
| 方案比较 | 保留同级 checkout 缺乏锁定组合；严格单 Git monorepo 破坏独立发布边界；选择 Root superproject + gitlink。 |
| 粒度 | `apps/` 与 `libs/` 是长期稳定的部署/包边界；Root `verification/` 仅在组合测试实现切片创建。 |
| 禁止依赖 | 子仓禁止 sibling 相对源码 import；Root 禁止共享业务 lockfile、ORM schema 或可编辑 contract 副本。 |
| 删除项 | 完成 fresh-clone 验证后移出旧同级 checkout、旧 Agent 根 gitlink、Mori P1 worktree 与临时日志目录。 |
| 验证 | 单仓完整门禁、远端 SHA 可获取、fresh recursive clone、拓扑/分支/发布锁验证与组合 smoke。 |
