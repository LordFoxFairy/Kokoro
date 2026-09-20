# Kokoro（こころ）

Kokoro 是由多个可独立发布仓库组成的 AI 产品平台。此仓库是 **Git submodule superproject**：它锁定一组经过验证的子仓 commit，维护跨仓规范、部署与组合验证；它不承载业务实现的单一 Git 历史。

## 组合结构

```text
Kokoro/
├── apps/
│   ├── kokoro-app/          # Web（Next.js）
│   ├── kokoro-mori/         # Mori 音乐产品（Next.js）
│   ├── kokoro-bff/          # Chat 与业务 BFF（TypeScript）
│   ├── kokoro-agent/        # Agent execution（Python）
│   ├── kokoro-iam/          # identity / authorization（TypeScript）
│   ├── kokoro-system/       # system control plane（TypeScript）
│   ├── kokoro-billing/      # billing / ledger（TypeScript）
│   ├── kokoro-capability/   # skills / MCP control plane（TypeScript）
│   ├── kokoro-storage/      # artifact/object metadata（TypeScript）
│   └── kokoro-scheduler/    # durable scheduling（Go）
└── libs/
    └── kokoro-web-shared/   # versioned frontend library
```

路径与 GitHub remote 的 repository 名完全一致：Web 是 `apps/kokoro-app`，不使用 `kokoro/` 或 `apps/kokoro/` alias。完整清单、职责和版本政策见 [仓库组合状态](docs/REPOSITORY_STATUS.md)。

## 快速开始

```bash
git clone --recurse-submodules https://github.com/LordFoxFairy/Kokoro.git
cd Kokoro
git submodule update --init --recursive

python3 scripts/verify-repository-topology.py
python3 scripts/verify-main-only.py
python3 -m pytest scripts/tests
```

每个子仓都有自己的依赖锁、CI、测试、构建、发布和文档。进入目标目录后按该仓 README/ACCEPTANCE 执行，例如：

```bash
cd apps/kokoro-app && pnpm check && pnpm test:e2e
cd ../kokoro-agent && uv run pytest
cd ../kokoro-scheduler && go test ./...
```

## 调用与数据边界

```text
Browser → kokoro-app same-origin adapter → kokoro-bff → owner services
```

- Web 不直连内部 owner 数据库或服务。
- BFF 不读取 owner 数据库。
- 每个 owner 只写入自己的业务事实；跨仓通过 owner 发布的版本化 contract、API/RPC 或事件交互。
- Root 不建立共享业务 lockfile、ORM schema、可编辑跨仓 contract 或 sibling source import。

## Git 与发布政策

1. Root 和每个子仓 local/`origin` 只保留 `main`。
2. 子仓先在自身完成 commit、验证与 push；Root 再提升精确 gitlink SHA。
3. `.gitmodules` 的 `branch = main` 仅提示开发更新；组合发布由 gitlink SHA 锁定。
4. 禁止把 `git submodule update --remote` 的浮动结果作为发布组合。

## 文档入口

1. [当前状态](docs/CURRENT.md)
2. [仓库组合状态](docs/REPOSITORY_STATUS.md)
3. [代码地图](docs/CODEBASE_MAP.md)
4. [Root 文档索引](docs/INDEX.md)
5. [ADR-032：Submodule 组合与仓标识](docs/kokoro-handbook/decisions/ADR-032-root-submodule-composition-and-repository-identity.md)
6. [工程执行规则](AGENTS.md)
