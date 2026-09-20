# ADR-032：Root Submodule 组合与远端仓标识

状态：已采纳，2026-09-19。

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

每个正式仓本地和远端仅保留 `main`。执行中的临时工作先在 `main` 完整集成、验证、push 后删除本地分支、远端分支和
关联 worktree。删除前在 Root 工作区外生成可校验的 Git bundle 与未跟踪文件归档；归档不是正式分支，也不进入发布组合。

Root 使用 gitlink 锁定每个子仓的精确 SHA；`.gitmodules` 的 `branch = main` 仅作开发提示，绝不充当发布锁。禁止
`git submodule update --remote` 生成浮动发布组合。

### 4. 迁移与验证

先完成每仓 `main` 收敛，再在隔离 Root worktree 创建 `apps/`、`libs/` gitlink 并移除旧同级 gitlink/checkouts。当前组合已按此路径落地。
迁移完成后必须在新目录外验证：

```bash
git clone --recurse-submodules ROOT_URL fresh-kokoro
git -C fresh-kokoro submodule status --cached --recursive
python3 fresh-kokoro/scripts/verify-submodule-topology.py
python3 fresh-kokoro/scripts/verify-main-only.py
```

验证器必须证明精确清单、路径与远端名一致、gitlink SHA 由远端可获取、工作树 clean、local/remote 仅有 `main`；子仓
自己的 lint/typecheck/test/build 仍由各自仓 CI 执行。Root 组合级 contract/integration/e2e/smoke 放在 `verification/`，
不得复制子仓 unit test 或机器契约。

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
