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

## 本地日常开发：固定源码、固定配置、持久数据

直接在 `apps/` 的实际子仓运行，不复制临时源码、不随启动创建数据库/账号/模型路由。
每仓自己的 `.env.local` 保存本地持久配置，权限 `0600`、不进 Git；启动时复用同一份配置。
一个 PostgreSQL 应用数据库、每 owner 独立 schema，以及一套共享 Redis；已有基础设施先复用。
这是目标拓扑，当前仅 Storage/Scheduler 完成保数据交接；其余 owner 先保留现有受管配置，
按 [当前状态](docs/CURRENT.md) 逐仓交接，不直接把旧数据库 URL 改为共享库。
停止只停止自己启动的应用进程，不删除数据库、schema、文件桶、账号或积分流水。

| 实际子仓 | 正常开发命令 | 工具链 | `.env.local` 读取 |
| --- | --- | --- | --- |
| `apps/kokoro-app` | `pnpm dev` | Node 22 / pnpm 11.25.0 | Next 原生加载 |
| `apps/kokoro-bff` | `pnpm dev` | Node 22 / pnpm 11.25.0 | 启动 shell / IDE 显式导入 |
| `apps/kokoro-agent` | `uv run kokoro-agent-http`、`uv run kokoro-agent-worker` | Python >=3.11，其余以 uv.lock 为准 | 两个进程分别显式导入同一份配置 |
| `apps/kokoro-iam` | `pnpm dev` | Node 24 / pnpm 12.3.4 | 仅 dev 命令原生加载 |
| `apps/kokoro-system` | `pnpm dev` | Node 24 / pnpm 12.3.4 | 启动 shell / IDE 显式导入 |
| `apps/kokoro-billing` | `pnpm dev` | Node 24.20.0 / pnpm 11.25.0 | 启动 shell / IDE 显式导入 |
| `apps/kokoro-capability` | `pnpm dev` | Node 24 / pnpm 11.25.0 | 启动 shell / IDE 显式导入 |
| `apps/kokoro-storage` | `pnpm dev` | Node 24.20.0 / pnpm 11.25.0 | 启动 shell / IDE 显式导入 |
| `apps/kokoro-scheduler` | `go run ./cmd/scheduler` | Go 1.26.8 | 启动 shell / IDE 显式导入 |

以各仓 manifest/lockfile 为版本事实源。对不自动读配置的仓，在目标仓目录执行以下流程
（配置保持 shell-compatible `KEY=VALUE`，IDE 也可使用等价的环境文件配置）：

```bash
set -a
source .env.local
set +a
pnpm dev
```

Agent 和 Scheduler 最后一行分别替换为表中的标准命令；Agent 的 HTTP 与 worker 都要启动。
Billing 支付事件 worker `pnpm worker:payment-events` 仅在对应任务需要时启动；
`pnpm worker:execution-events` 是按需单次消费命令，不作为无工作时的常驻循环。

依赖安装只在首次 checkout 或 lockfile 改变后执行。Schema 安装只在明确的新 owner 空 schema
首次初始化时执行，不放进日常启动/重启流程；账号、客户端授权、模型目录、报价和积分通过对应 owner 的
正常业务流程维护，不在启动时反复 seed/bootstrap。模型可见、服务 ready 都不代表真实用户聊天已通过。
Billing 当前 installer 仍限定 public schema 和整库空白；owner-schema 切换完成前，
不要对共享应用数据库执行该 installer。

Root 的本地进程收据和私有日志只放已忽略的 `var/dev/`，不作为第二份配置事实源。
当前实际常驻进程、端口、句柄及未迁移项见 [当前状态](docs/CURRENT.md)。

### 隔离测试不是日常站点

`scripts/dev/serve_local_login.py` 保留为隔离登录/模型 E2E fixture，不再作为日常开发入口。
它可能复制源码、建立自有数据并在结束时清理；只能用于明确隔离测试，不拿它更新日常站点。
现存旧预览先完成保数据交接再退出，不直接停止会清理身份/会话数据的旧 supervisor。
真实模型凭据继续只保存在 owner 私有配置/凭据文件，不放命令行、Git 或公开模型目录；
隔离测试的外部 provider credential-file 参数及互斥规则以该脚本帮助和测试任务为准，不静默回退。

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
