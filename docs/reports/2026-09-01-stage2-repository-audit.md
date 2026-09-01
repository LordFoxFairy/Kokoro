# 阶段 2 全仓审计

日期：2026-09-01
范围：Root `Kokoro`、10 个 active repository、6 个 archived repository。
状态：本地拓扑与 Goal 2 mock closure 可验证；Root contract 与 architecture gate 已接入 CI。

## Active repositories

以下记录来自本地 `HEAD`、`origin` 和 `origin/main`；10 个仓库的 `origin/main` 与本地
`HEAD` 一致。`kokoro-model` 保留用户已有的两个 generated 文件本地修改，未在本轮写入。

| 本地路径 | GitHub remote | 当前 HEAD | 本地状态 | GitHub 状态 |
|---|---|---|---|---|
| `kokoro` | `LordFoxFairy/kokoro-app` | `4080377cf13ee3a1e6164547b47cf39d5951dfb9` | clean | active / main |
| `kokoro-bff` | `LordFoxFairy/kokoro-bff` | `876dfba1c012cbfe41efe1b120468d797cf026b9` | clean | active / main |
| `kokoro-agent` | `LordFoxFairy/kokoro-agent` | `4091fb2f41d9076696eddb2dc4623e30ebaab131` | clean | active / main |
| `kokoro-iam` | `LordFoxFairy/kokoro-iam` | `b662fce3b95e5d3d778f7c940ac94466fd44c5e3` | clean | active / main |
| `kokoro-system` | `LordFoxFairy/kokoro-system` | `2c4635f74666a06482973b40bbd534874673308a` | clean | active / main |
| `kokoro-model` | `LordFoxFairy/kokoro-model` | `aa8c395b9537af4138eaa8008e5b95299d6a0384` | dirty: 2 generated files | active / main |
| `kokoro-billing` | `LordFoxFairy/kokoro-billing` | `f2a947a7a7b78af6fea5e4de56ccab24cf0b8875` | clean | active / main |
| `kokoro-capability` | `LordFoxFairy/kokoro-capability` | `204805c92b062396d90200cf5eee2388da1aa11c` | clean | active / main |
| `kokoro-storage` | `LordFoxFairy/kokoro-storage` | `13c39c3cd97a167eaa86b91cabc88f36d27032a1` | clean | active / main |
| `kokoro-scheduler` | `LordFoxFairy/kokoro-scheduler` | `3ad5a54ec0b7580830673748a3c5086f70a8590d` | clean | active / main |

Root 本地 HEAD 为 `47713e15393eaa460d02c03276c0ea73a9842e90`，remote 为
`https://github.com/LordFoxFairy/Kokoro.git`，审计开始时 `origin/main` 一致，工作区 clean。

## Archived repositories

| 本地/历史名称 | GitHub 状态 |
|---|---|
| `kokoro-session` | `LordFoxFairy/kokoro-session` archived；不在 Root |
| `kokoro-gateway` | `LordFoxFairy/kokoro-gateway` archived；不在 Root |
| `kokoro-platform` | `LordFoxFairy/kokoro-platform` archived；不在 Root |
| `kokoro-web` | `LordFoxFairy/kokoro-web` archived；不在 Root |
| `kokoro-credit` | 无正式 remote；历史副本在 Root 外；Credit 归 Billing |
| `kokoro-site-kokoro` | 无正式 remote；历史/占位目录不在 Root |

## Machine gates and test thresholds

- Root architecture: `python3 scripts/verify-backend-design.py` 必须返回 0。
- Root topology: `python3 scripts/verify-repository-topology.py` 必须检查当前十个 direct Git
  repository paths、origin remote、active boundary、6 个 archived paths、Phase 1 storage
  boundary 和 Goal 2 manifest，并返回 0。
- Goal 2 closure: `python3 scripts/goal2/mock_cross_repository_closure.py` 必须检查七个 owner
  的 API/技术/BFF/验收/风险文档、Root wire 文件、request ID、幂等和 cursor 标记，并返回 0。
- Root contract: manifest parity、renderer `--check`、Buf format/lint/breaking、Redocly lint，
  以及 `uv run --frozen pytest contract/tests scripts/contract/tests -q` 必须通过。
- Hygiene: `git diff --check` 必须通过。各 active repository 的实现、测试、构建和 Docker/CI
  仍由各自仓库门禁负责，不由 Root 复制源码代替。

## Known real-closure gaps

1. 当前 Root gate 是 topology、文档/契约和 mock boundary gate；尚未把 Web→BFF→Agent→七个
   owner 的真实网络编排作为一次生产式联调验收。
2. 生产 PostgreSQL、Redis、S3-compatible ObjectStore、JWKS、provider 和 webhook 配置由部署
   环境注入；本地 fixture 不证明生产依赖或生产凭据可用。
3. IAM shutdown contract test 仍需显式 listener lifecycle 环境；Docker/真实基础设施 smoke
   仍是部署前独立证据，不把环境阻塞记为通过。

## Verification record

本报告对应的 Root 变更仅限 `.github/workflows/contract.yml`、
`scripts/verify-repository-topology.py`、`scripts/goal2/mock_cross_repository_closure.py`
和本文件；未修改历史报告或任何子仓源码，未记录任何 secret。

本轮 Root 验证结果：architecture、topology、mock closure 均返回 0；Root 相关 pytest 为
`84 passed`；manifest、renderer、Buf format/lint/breaking、Redocly 和 `git diff --check`
均通过。Redocly 报告 4 个既有 warning，但命令返回 0，未修改契约文件。
