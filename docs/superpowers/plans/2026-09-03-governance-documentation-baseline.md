# Wave 0：十仓治理与文档基线实施计划

> **执行要求：** 使用测试先行；每完成一个任务即运行该任务的验证命令并形成小粒度提交。

**目标：** 把 Root 的中文工程手册从“七个 owner 后端仓”升级为“Web、BFF、Agent + 七个 owner 仓”的十仓可执行规范，并建立后续并行重构所依赖的静态审计基线。

**架构边界：** Root 只保存治理规则、仓库拓扑、计划、门户编排和跨仓验证，不复制子仓 OpenAPI、SQL、DTO 或生成物。

**实现技术：** Markdown、Python 3.11+、pytest、Bash、Git。

---

## Task 1：锁定十仓治理契约

**文件：**

- 修改：`AGENTS.md`
- 修改：`docs/ARCHITECTURE_STANDARD.md`
- 修改：`docs/CODEBASE_MAP.md`
- 修改：`docs/CURRENT.md`

**步骤：**

- [x] 将适用范围从七仓改为十仓，写清 Web、BFF、Agent 与七 owner 的事实边界；
- [x] 保留 plural category directory 规则：`models/`、`enums/`、`services/`、`repositories/`，文件名按单一职责使用单数；
- [x] TypeScript strict 增加 `useUnknownInCatchVariables`；补充 `any`、断言、DB Row 与 mapper 的例外审批方式；
- [x] 加入 Python Pydantic/TypedDict/dataclass/Protocol/Enum 分工和 file-wide suppression 禁令；
- [x] 加入模块、函数、React、CSS 的粒度预算以及显式豁免格式；
- [x] 加入 Web 交互状态、CSS token、focus、reduced motion、Playwright/axe/visual gate；
- [x] 加入公开/浏览器私有/内部 owner/event 四类 API visibility；
- [x] 加入 AG-UI 唯一网络协议与 Vercel AI SDK 内部 adapter 裁决；
- [x] 加入十仓文档最低集合、contract provenance 和 Developer API 门户边界；
- [x] 更新本地 Redis 逻辑库：IAM=1、System=2、Model=3、Billing=4、Capability=5、Storage=6、Scheduler=7、BFF=8、Agent=9，0 保留；
- [x] 明确本地只探测/复用一个 PostgreSQL 和一个 Redis，不为各仓重复启动依赖。

**验证：**

```bash
rg -n 'kokoro-bff|kokoro-agent|useUnknownInCatchVariables|AgUiChatTransport|docs/TECHNICAL_DESIGN.md|BFF=8|Agent=9' AGENTS.md docs/ARCHITECTURE_STANDARD.md
python3 scripts/verify-repository-topology.py
```

**提交：**

```bash
git add AGENTS.md docs/ARCHITECTURE_STANDARD.md docs/CODEBASE_MAP.md docs/CURRENT.md
git commit -m "docs(governance): define ten-repository engineering standard"
```

## Task 2：测试先行升级静态验证器

**文件：**

- 新建：`scripts/tests/test_ten_repository_standard.py`
- 重命名：`scripts/verify-seven-repository-standard.py` -> `scripts/verify-ten-repository-standard.py`
- 修改：`scripts/verify-ten-repository-standard.py`
- 修改：`scripts/INDEX.md`

**步骤：**

- [x] 先写测试，断言正式仓集合恰好十个、Redis 映射为 1..9、必需文档矩阵完整；
- [x] 运行测试并确认旧实现因缺少 Web/BFF/Agent 而失败；
- [x] 将 TypeScript 仓分类为 Web、BFF、六个 owner，分别执行适合其职责的目录和 schema 规则；
- [x] 为 Python Agent 增加 canonical schema、Pyright strict、生产 double、分层 import、文件粒度和机器契约检查；
- [x] 为 Web 增加直连 owner、legacy SessionEvent/fallback、超大 React/CSS、focus 与质量脚本检查；
- [x] 为 BFF 增加公开 OpenAPI、真实 store、显式 owner adapter、canonical schema 和 package manager 检查；
- [x] 为全部十仓增加标准文档矩阵和 `contract/README.md` 条件性检查；
- [x] 输出稳定的 repository/rule/detail 诊断，便于并行 Agent 按 owner 修复。

**验证：**

```bash
uv run --frozen pytest scripts/tests/test_ten_repository_standard.py -q
python3 scripts/verify-ten-repository-standard.py
```

第二条在十仓尚未修复前预期输出准确缺口并返回非零；Task 2 的完成标准是测试通过且诊断可操作，不是伪造全绿。

**提交：**

```bash
git add scripts/tests/test_ten_repository_standard.py scripts/verify-ten-repository-standard.py scripts/INDEX.md
git commit -m "feat(governance): audit all ten active repositories"
```

## Task 3：升级全量验证编排

**文件：**

- 重命名：`scripts/verify-seven-repository-full.sh` -> `scripts/verify-ten-repository-full.sh`
- 修改：`scripts/verify-ten-repository-full.sh`
- 修改：`README.md`
- 修改：`scripts/INDEX.md`

**步骤：**

- [ ] 在启动依赖前探测已有共享 PostgreSQL/Redis，存在即复用，不存在时只启动各一个；
- [ ] 使用独立临时 database 验证 BFF 和 Agent，使用 Redis DB 8/9；
- [ ] Web 从源码启动并执行 Playwright/axe/关键交互路径，不以 app Docker 代替开发验证；
- [ ] 保留七 owner 的 fresh-schema、真实 integration、candidate image 和数据库不变量检查；
- [ ] 对 Agent 增加 crash/recovery/fencing/duplicate-effect 场景；
- [ ] 对 BFF 增加 durable outbox/AG-UI cursor/reconnect 场景；
- [ ] 最后才构建十仓候选镜像并执行 security/smoke；
- [ ] trap 只清理本脚本创建的 database、进程和容器，不停止用户已有共享依赖。

**验证：**

```bash
bash -n scripts/verify-ten-repository-full.sh
shellcheck scripts/verify-ten-repository-full.sh
```

完整运行放在所有子仓修复完成后的 Wave 6。

**提交：**

```bash
git add scripts/verify-ten-repository-full.sh README.md scripts/INDEX.md
git commit -m "feat(governance): orchestrate ten-repository verification"
```

## Task 4：生成并冻结文档缺口清单

**文件：**

- 新建：`docs/reports/2026-09-03-ten-repository-gap-baseline.md`
- 新建：`docs/reports/2026-09-03-ten-repository-gap-baseline.json`
- 修改：`docs/CURRENT.md`

**步骤：**

- [ ] 在当前十仓 commit 上运行静态验证器；
- [ ] JSON 记录每仓 branch、HEAD、dirty 状态、缺失规则和 owner；
- [ ] Markdown 按 P0/P1/P2 汇总，P0 固定为 Agent 三项正确性问题与暴露时的 Mori 匿名可信代理问题；
- [ ] 记录 `kokoro-bff/docs/api/v1/agui-chat.md` 为既有协作者改动，不纳入 Root 修改；
- [ ] 将报告加入 `docs/CURRENT.md` 当前实施入口。

**验证：**

```bash
python3 -m json.tool docs/reports/2026-09-03-ten-repository-gap-baseline.json >/dev/null
rg -n 'kokoro|kokoro-bff|kokoro-agent|kokoro-iam|kokoro-system|kokoro-model|kokoro-billing|kokoro-capability|kokoro-storage|kokoro-scheduler' docs/reports/2026-09-03-ten-repository-gap-baseline.md
```

**提交：**

```bash
git add docs/reports/2026-09-03-ten-repository-gap-baseline.* docs/CURRENT.md
git commit -m "docs(governance): record ten-repository gap baseline"
```

## Task 5：Wave 0 主工作区复核

- [ ] `uv run --frozen pytest scripts/tests -q`；
- [ ] `python3 scripts/verify-repository-topology.py`；
- [ ] `python3 scripts/verify-backend-design.py --manifest-only`；
- [ ] `bash -n scripts/verify-ten-repository-full.sh`；
- [ ] `git diff --check`；
- [ ] 审查 `git status --short`，只包含 Wave 0 预期文件；
- [ ] 更新计划复选框与当前 evidence，不以子 Agent 报告代替复核。
