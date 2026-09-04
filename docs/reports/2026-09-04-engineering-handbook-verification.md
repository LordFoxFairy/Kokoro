# 工程手册收敛与验证记录

核验日期：2026-09-04。证据对应包含本记录的根仓提交；提交号可由 `git log -1 --format=%H -- docs/reports/2026-09-04-engineering-handbook-verification.md` 取得。

## 范围与结论

本轮交付为四个中文规范入口及其引用、示例和预检机制：

- [AGENTS](../../AGENTS.md)：控制流程、规范路由、owner、文档先行门和验收。
- [SQL](../kokoro-handbook/standards/03-sql-and-postgresql.md)：项目约束、条件字段、查询/事务与生命周期。
- [TypeScript](../kokoro-handbook/standards/08-typescript-backend-engineering.md)：业务模块、自然命名、框架和类型、运行与测试。
- [Python](../kokoro-handbook/standards/09-python-backend-engineering.md)：能力 package、边界类型、配置、async 和验证。

旧 54/55 综合规范改为导航页；01/02 仅保留建模概念，04/05/06 同步消除强制四层、默认 migration/FK 和机械 Command 等冲突。
本轮未重构任何子仓实现，未修改子仓依赖、数据库 schema 或提交其 submodule 指针。工作树原有 `kokoro-agent` 指针修改及 `.tmp/` 不属于本次提交。

“规范可执行且内部一致”与“现有服务已达生产标准”是两个结论。本记录只证明前者的文档、示例与预检结果，不替代逐仓契约、故障、容量与 SLO 验收，不使用无证据的百分制认证。

## 要求与证据

| 要求                           | 本轮证据                                                                           |
| ------------------------------ | ---------------------------------------------------------------------------------- |
| AGENTS 中文、只引用专项细节    | 三份固定引用；无 TS/Python/SQL 实现模板；根仓回归断言                              |
| 命名和目录按业务，而非机械 DDD | TS 模块与 Python package 的展开条件、职责/依赖决策表；旧目录模板撤销               |
| 每次设计先思考                 | 新建/结构变更先放置表，局部修复简化；先完成技术方案/API/数据文档门                 |
| SQL 不默认堆字段/约束          | 最小 DDL 不含 status/version/业务 UNIQUE/CHECK；软删除策略、例外与无 FK 完整性明确 |
| UTC、强类型、真实边界          | TS strict/typed lint；Python Pyright strict；真实 PG 日期/UUID/NULL 映射验证       |
| 不过时和不盲追新               | 来源分类、核验日期、release/peer/供应链审查；依赖快照与 lock 固定                  |
| 防止只写 Markdown              | 可从当前文档提取示例，固定工具、运行时回归，以及根级预检的正反样本                 |

## 实际验证结果

- 根仓 `pytest`：28 passed；Ruff 0.16.5 格式及检查通过；compileall 通过。
- TS 示例：Node 24.13.0，pnpm 11.25.0，TypeScript 6.0.3；frozen install、tsc、typed ESLint 和 Prettier 通过。
- TS 运行回归：7 passed，覆盖配置、401、未知字段400、JSON/大小/介质错误、真实 SQL/tenant/软删除、403/500 脱敏、404 envelope。
- Python 示例：Python 3.14.3、Pyright 1.1.411：0 errors/0 warnings；Ruff 0.16.5 通过。
- Python 运行回归：4 passed，覆盖大写 env/文件覆盖/生产不加载开发文件、Pydantic 未知字段、结构化依赖与固定时钟、psycopg 类型与事务回滚。
- PostgreSQL 16.15：复用已有本地实例，创建任务独有临时库；当前 DDL 安装成功，直接重复执行 `IF NOT EXISTS` 成功，外键数 0；验证后已删除临时库。
- 未新建 PostgreSQL/Redis 实例；Redis 本轮无可执行示例，未声称已做 Redis 故障测试。
- Markdown 检查覆盖本次修改/新增的文档：代码围栏成对、仓内文件链接存在；`git diff --check` 通过。

供应链验证曾拦截观察窗口内的 Fastify 5.12.3、ESLint 10.10.0。最终验证快照选择通过 1440 分钟观察窗口的 Fastify 5.12.1、ESLint 10.9.1，未关闭安全策略。
精确依赖见 [TS fixture manifest](../../scripts/tests/fixtures/handbook/package.json)、[lockfile](../../scripts/tests/fixtures/handbook/pnpm-lock.yaml) 和 [Python 快照](../../scripts/tests/fixtures/handbook/requirements.txt)。这些是验证快照，不是永久最新版本声明。

## 可重复验证

从根仓生成一份临时示例；业务源码从 Markdown 提取，fixture 不复制另一份实现：

```bash
ROOT="$(git rev-parse --show-toplevel)"
OUT="$(mktemp -d)"
python3 -m scripts.governance.handbook_examples --output "$OUT"
cp "$ROOT"/scripts/tests/fixtures/handbook/{package.json,pnpm-lock.yaml,pnpm-workspace.yaml,eslint.config.mjs} "$OUT/typescript/"
mkdir -p "$OUT/python/tests"

# 使用 Node 24 / pnpm 11.25.0
cd "$OUT/typescript"
pnpm install --frozen-lockfile
pnpm exec tsc
pnpm exec eslint src --max-warnings=0
pnpm exec prettier --check src

cd "$OUT/python"
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python -r "$ROOT/scripts/tests/fixtures/handbook/requirements.txt"
.venv/bin/pyright --pythonpath .venv/bin/python
.venv/bin/ruff format --check .
.venv/bin/ruff check .
```

运行数据库测试前，复用已有 PostgreSQL，创建本次独有的临时数据库，将其 URL 放入环境变量 `HANDBOOK_DATABASE_URL`；不得指向业务库。
安装提取出的 schema，再运行固定测试：

```bash
psql "$HANDBOOK_DATABASE_URL" -v ON_ERROR_STOP=1 -f "$OUT/schema.sql"
node "$ROOT/scripts/tests/fixtures/handbook/runtime-check.mjs" "$OUT/typescript"
PYTHONPATH="$OUT/python/src" "$OUT/python/.venv/bin/python" -m pytest -q \
  "$ROOT/scripts/tests/fixtures/handbook/runtime_check.py"
```

完成后仅删除自身临时数据库与目录。测试中的模拟身份只用于验证框架/业务权限边界，不是可部署的认证实现。

## 当前实现仍待逐仓对齐

`python3 scripts/verify-ten-repository-standard.py --format json` 返回 FAIL，当前物理十仓有 **114 条静态诊断**，Root 文档缺失诊断为 0。
主要涉及目录、Node/ESM/strict 配置、构建策略和旧路径；诊断数不是独立缺陷数，也不是性能/安全评分。该工具明确只作预检，完整 import graph、权限、并发、容量仍靠子仓 CI 和运行验证。

目标拓扑的 Model→System、Capability→Platform 尚未实施，因此审计仍遍历真实十仓；不提前修改 inventory 假装九仓已完成。
下一阶段按用户要求一次处理一个子仓：技术方案、API 契约、SQL/数据设计先通过，再按业务切片实现、验证与提交。
