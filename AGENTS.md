# Kokoro Agent 工作指南

本文件是执行入口：明确任务范围、规范入口、工程边界和验收方式，不承载任务历史或完整语言手册。
Root 是 Git submodule superproject；业务实现、契约、数据与发布归子仓，Root 负责组合版本和跨仓治理。

## 1. 开始任务与命令入口

1. 确认用户要求、完成条件和允许修改的范围；查看 Git 状态与目标文件 diff，保留已有工作。
2. 按第 2 节读取相关规范，按第 3 节选择流程；只完成本次要求，不顺手修复或升级任务外内容。
3. 按第 7 节验证，按第 10 节交付；文档任务交付文档，调查任务交付结论，不默认转入实现。

```bash
git status --short
git diff --check
```

以下是按影响面选择的验证入口，**不是每次全部执行的清单**。子仓命令在对应目录运行，先核对 README、manifest 与 CI；版本以本仓配置和 lockfile 为准。

| 范围 | 入口与用途 |
| --- | --- |
| Root 文档 | `git diff --check`、本地链接检查、直接相关的 `scripts/tests/` 测试 |
| Root 拓扑/gitlink | `python3 scripts/verify-repository-topology.py` |
| Root 治理逻辑 | `python3 -m pytest scripts/tests`；跨仓规范审计用 `python3 scripts/verify-ten-repository-standard.py --format json` |
| TypeScript | `pnpm lint`、`pnpm typecheck`、`pnpm test`、`pnpm build`；有对应脚本时补 `pnpm format:check` |
| Web | TypeScript 入口；交互变更补本次主路径浏览器验收，相关 E2E 用 `pnpm test:e2e` |
| Python Agent | `uv lock --check`、`uv sync --frozen`、`uv run ruff format --check .`、`uv run ruff check .`、`uv run pyright`、`uv run pytest`、`uv build` |
| Go Scheduler | `gofmt -l .`（输出为空）、`go vet ./...`、`go test ./...`、`go build ./...` |
| 数据 owner | 本仓 Schema 安装/迁移入口；`pnpm db:apply-schema` 仅在指定隔离测试资源上执行 |

`scripts/verify-ten-repository-full.sh` 与 `scripts/e2e/run_stage2_owner_health.py` 已暂停，诊断后退出 2，不作为验收入口。
`scripts/e2e/run_system_owner_smoke.py` 只验证其隔离 System 跨仓 HTTP 链路，不代表全产品验收。

## 2. 按需读取与规则归属

平台指令与当前用户要求确定执行权限和本次范围。本文件定义项目执行流程；专项手册管理语言/SQL 规则，总体架构与有效 ADR 管理 owner/协议，子仓指南补充本仓入口、命令和已批准例外。

| 需要了解什么 | 入口 |
| --- | --- |
| 路径与组合身份 | `.gitmodules`、[代码地图](docs/CODEBASE_MAP.md)、[组合状态](docs/REPOSITORY_STATUS.md)；实际路径以 `.gitmodules` 和 checkout 为准 |
| 当前任务与阻塞 | [当前事实](docs/CURRENT.md)、[任务记录](docs/task.md)；按任务 ID/owner 只读相关条目 |
| 跨仓边界与协议 | [总体架构](docs/ARCHITECTURE_STANDARD.md)及其引用的有效 ADR |
| TypeScript 后端 | [TypeScript 手册](docs/kokoro-handbook/standards/08-typescript-backend-engineering.md)；设计/重构重点核对 §1、§4–6、§8.4 |
| Python | [Python 手册](docs/kokoro-handbook/standards/09-python-backend-engineering.md) |
| SQL、Schema、查询 | [PostgreSQL 手册](docs/kokoro-handbook/standards/03-sql-and-postgresql.md) |
| 并发、API、测试 | [事务](docs/kokoro-handbook/standards/04-transaction-repository-idempotency.md)、[API](docs/kokoro-handbook/standards/05-api-rpc-and-error-contracts.md)、[测试](docs/kokoro-handbook/standards/06-testing-and-quality-gates.md) |

进入子仓先读其 `AGENTS.md`、README 及相关实现/测试；涉及对应语言/数据时，先读专项手册相关章节，不默认通读历史台账。
不复制完整手册，不使用已替代 ADR 或历史完成报告覆盖当前决定。发现冲突先核对适用范围与有效 ADR，未裁决部分暂停，其余独立工作继续；代码与设计不一致时如实区分当前态/目标态。

## 3. 范围与设计门

| 任务 | 必要流程 |
| --- | --- |
| 讨论、只读调研、文档/注释 | 读取相关材料 → 结论或文档 → 相关检查；不自动登录目标站、采集页面/源码、安装技能或开展业务实现 |
| 不改变边界的局部修复/机械调整 | 定位职责与行为基线 → 修改 → 定向验证；不新增计划、ADR 或设计表 |
| 单仓功能、多文件行为变更 | 简述目标、写区与验收，按完整业务切片实施；既定方案内扩展不重复审批 |
| owner、模块/进程、跨仓契约、数据模型变化或重大重构 | 先过下述设计门，再实施；任务同时符合多行时，以实际边界/数据影响为准 |
| 部署、破坏性数据操作、新的不可逆决定 | 明确资源、风险与恢复措施；尚未授权的具体操作先确认 |

- 明确要求或已有裁决直接执行；只有影响目标/验收的歧义、新 owner/破坏性契约、写入冲突或未授权操作需要确认，其余采用最小合理假设并说明。
- 无关未提交文件不阻塞任务；目标文件有归属不明的重叠 diff 时先确认写区。不要覆盖、回滚或提交他人的未交接改动。
- 跨仓、多 Agent 或需要跨会话续接的工作复用当前有效计划，记录目标、owner、写区、依赖、状态与验证；简单任务用会话内简述即可，不为步骤数量新增任务中心。

结构性变更的设计门只记录必要结论：owner/基线、目标目录与依赖、受影响的契约/数据/状态机和失败恢复、删除项及验证。新边界比较可行位置；已有裁决直接引用，不重复做方案竞赛。
仅对本次受影响的设计面收敛：`docs/TECHNICAL_DESIGN.md`、`docs/API_CONTRACT.md` 与机器契约、`docs/DATA_MODEL.md` 与 canonical schema。
文档门未通过时，不执行依赖该未决设计的搬迁、改表或业务重写；允许继续盘点、验证方案和独立局部修复。
新顶层边界/重大取舍记录技术设计或 ADR；普通文件和既定方案内扩展不要求 ADR。无数据/传输 owner 时不建空 Schema/contract，不为局部修复补齐整套文档。

## 4. 工程底线

- 一个业务事实只有一个 owner 和写入边界；服务只访问自己的数据。Root 不建立跨仓可编辑 contract 中心；不共享 ORM schema、SQL、业务 DTO，不通过相对路径导入 sibling 源码。
- Browser → Web same-origin adapter → BFF → 内部 owner；Web 不直连内部服务，BFF 不读取 owner 数据库。
- 使用 `apps/kokoro-app`、`apps/kokoro-capability` 等实际路径；Capability → Platform 未完成原子切换前不冒称完成、不引入 alias。完整 owner/模块地图见总体架构。
- System 配置归实际业务模块，Capability/目标 Platform 拥有 Skills/MCP 控制面，不成为任意配置或共享工具垃圾桶；Scheduler 不拥有 BFF ScheduledTask 或 Agent Run。
- 跨仓使用 owner 发布的 API/RPC/事件与固定版本、commit 和 digest 的 generated client/artifact；每个传输边界只保留一个可编辑事实源，生成物由生成命令更新。
- HTTP 业务 API 显式 `/v1`、外部 JSON `snake_case`；原生认证协议与 health 路由按 owner 契约。错误、分页、幂等和并发遵循 API 手册，不把业务 API 命名规则强加给原生协议。
- tenant、actor、subject、service identity 来自受信上下文；服务身份、人类权限和执行授权分开，认证方案按当前架构/有效 ADR，不信任 body 自报身份。
- Web/BFF Agent 网络事件只使用 AG-UI；BFF 拥有 durable ledger/cursor/replay，Web 映射到 AI SDK UIMessage，不恢复 legacy envelope 或第二套网络协议。
- 代码按业务能力聚合、保持单一变化原因；不建空层、机械四层、BaseRepository 或重复类型。Domain Model、CQRS、抽象和状态机只在真实复杂度需要时引入，遵循语言手册。
- 每个数据 owner 只维护一份 canonical schema：SQL-first 使用 `database/schema.sql`，ORM-first 使用技术方案批准的唯一 schema。时间瞬时点用 UTC，本地日历/周期显式建模 IANA timezone。
- 已批准的 clean-slate 替换同步删除旧入口/Schema、alias、fallback 和重复实现；承接仍有效的权限、事务、幂等、取消与恢复保障，不清理任务外代码。
- 依赖采用稳定兼容版本并锁定；新增核心依赖/重大替换记录候选、许可证、维护/供应链风险与退出路径，不顺手追浮动 `latest`。

## 5. 协作

- 单文件、紧密依赖或决策密集任务主 Agent 直接做；至少两个独立工作面时提议并行，有收益且工具可用再派工，不强制开满 Agent。
- 按写区隔离；同一文件、contract、Schema、lockfile、公共入口和任务表指定唯一 writer，不强制整个仓串行。依赖契约先由 owner 交付，再更新消费者。
- 派工公开角色，提供中文目标、绝对目录、基线、允许/排除路径、依赖、验收及相关代码地图/手册入口；不复制规范全文。越界需求先报告，调整范围后再写。
- 共享 checkout 的 Git index、分支、提交/PR 和集成由主 Agent 串行负责；只读角色不改文件或共享资源。
- worker 交付文件清单、SHA（如已提交）、实际验证与风险；主 Agent 复核 diff 并重跑相关验证。最终验收绑定交付 commit 或受影响文件停写后的基线，并发编辑中的结果只作阶段证据。
- 工具/skill 是手段，不固定模型、worker 数量或外部 CLI；缺少非必需工具时使用已可用方法。缺少必要证据时报告具体缺口，不把安装工具或 worker 退出码当作完成证明。

## 6. Git 与 PR

采用 [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow) 与 [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)，具体保护与合并方式遵循仓库现行规则。

- 一个完整需求一个分支/PR，内部允许多个自洽 commit；复用同一个 draft PR，不按文件、按钮或实施切片拆 PR，不额外引入长期 develop/release 分支。
- 开始新实现且工作区适合切换时，从同步后的 `main` 建 `feat/<功能>`、`fix/<问题>`、`refactor/<范围>`；版本交付用 `feat/v<版本>`。继续既有任务沿用分支，不在混合工作区强行切换。
- 消息格式为 `type(scope): description`，如 `fix(skills): preserve dialog scroll position`；破坏性契约变化用 `!` 或 `BREAKING CHANGE:` 说明影响。
- 提交前审查 diff/暂存区，按明确路径暂存，不用 `git add .` / `git add -A`；只提交本需求源码、契约、测试和必要文档，不夹带凭据、缓存、产物或机器运行记录。
- 子仓独立提交、验证并推送后，Root 才更新精确 gitlink；Root 与子仓分开提交/PR，不混入无关版本，不用浮动更新代替已验证组合。
- PR 说明需求/验收、契约/Schema 影响、实际验证和风险；UI 变更附参考/实现对照。`main` 只通过已审查/已验证 PR 更新，不直接提交或本地绕过 PR 合并。
- 按用户项目约定，正常走 PR 合并，不将远端 CI 作为等待条件，不为此反复 push 或重跑 CI；仍完成本地相关验证、代码审查和冲突处理，并如实记录 CI 未运行/失败，不伪造绿色状态或绕过 GitHub 强制分支保护。
- 开始集成、最终推送和合并前先 fetch 远端 main 与对应 PR 分支，核对新增提交和分叉；保留并整合其他人的更新，不用 force push、整树择一或盲目 pull 覆盖混合工作。Root/子仓显式使用非递归 fetch，避免并行更新同一 submodule ref；存在未提交改动时先保护，在独立集成区验证后再回填。
- 提交、推送、建 PR、合并和分支清理遵循本次授权；“修改文档/代码”不自动扩大为发布。需求合并后，仅在无未交接工作时回到同步 main，核对 PR 已合并且分支没有合并后新增提交后，清理对应远程分支和无人使用的本地 topic 分支，并 fetch --prune 清理失效远端引用；仍被工作树占用或包含未交接工作的本地分支保留，待工作树收尾后再删除，不丢弃他人工作或未合并提交。

## 7. 测试与验收

**测试保护行为与独有风险，验证范围随变更扩大；不按数量或目录层级机械生成。**

- 新测试先查现有覆盖，选择最低充分层级，用名称/必要注释说明目的，不另建准入表。使用等价类、边界值和真实风险组合，不追全仓 100% 覆盖率。
- 默认不锁定私有方法、内部调用顺序、源码/CSS 字符串或 Markdown 标题/整段文案；公开文案、协议值或顺序本身是有效契约时例外。架构检查优先验证实际边界与有效/违规样本。
- 单元覆盖规则，集成覆盖真实 I/O/事务，contract 覆盖 wire/消费者边界，E2E 覆盖关键旅程；只有增加独有证据才跨层重复。缺陷修复补能复现问题的回归。
- 可合并、下沉、重写或删除重复/过时/实现耦合测试，先确认风险已被承接或需求已废止并说明原因；不为消除失败删断言、缩小测试范围或放宽门禁。

| 阶段/变更 | 验证要求 |
| --- | --- |
| 纯文档 | diff、链接与直接相关治理检查；不启动业务服务、目标站浏览器或全仓编排 |
| 只读调查 | 核验结论所需来源/证据；登录、页面采集或环境实测仅在明确的调查范围内进行 |
| 开发迭代、局部修复 | 相关行为/失败基线、focused test 和受影响的 lint/typecheck；按影响扩大，不每一步重复完整门禁 |
| 单仓完整需求交付/合并 | 本 owner 所需格式、lint/typecheck/test/build 等完整相关门禁；已存在的失败也如实记录，未满足合并门禁不冒称已验收 |
| 契约、数据或跨仓变更 | 在上述基础上补消费者契约、隔离真实集成、fresh schema/迁移与相关 smoke |
| UI/交互 | 实测主路径和相关状态、移动端/键盘/可访问性；视觉保留对照证据，Manus 专项按第 8 节 |

权限、tenant、幂等、并发、回滚、重复投递、恢复及超时/取消/有限重试按本次受影响行为覆盖，不对无对应能力的模块建立空套件。
mock 不称真实 integration，跳过不称通过；真实依赖/资源隔离遵循第 9 节。区分新增失败、既存失败与环境缺口，只暂停受阻交付/合并，不自动扩散修复范围。

## 8. Manus 复刻与技能分工

**仅在明确的页面/功能复刻任务中执行。视觉与交互以 Manus 实测参考为准，工程实现遵循 Kokoro owner/契约。**

1. **定范围**：指定页面/本地路由、状态与已批准的品牌/业务差异，以精确一比一为验收目标，不擅自换风格或让旧实现/测试决定布局。
2. **观察取证**：复用可用浏览器与登录 session；认证按用户授权和平台规则进行，需要用户参与时再交接，不索取或导出登录凭据。发布、支付、删除等有副作用动作单独确认授权，不因采集任务自动执行。
3. **提取规则**：读取页面已加载且可访问的 DOM、计算样式、CSS/前端 JS、字体及图片/SVG，测量布局/排版并记录触发→状态变化，不只凭截图猜样式。可访问 source map 时分析关联前端源码；前端产物、完整源码仓库和后端源码分开标注，现有证据足够时直接推进。
4. **整理并实现**：按功能分批，一页一份紧凑规格记录布局/组件关系、token、交互状态、资源来源与待核实项；复用现有文档和组件，不等整站采集完才开发，不搬入整套模板/依赖或演示业务旁路。
5. **对照验收**：固定参考 URL/采集日期、视口、主题/语言、滚动与交互状态，标注参考/实现、新/历史截图；逐项修正布局、字体、间距、图标、弹窗、滚动、响应式和动效，同时验证真实点击结果、数据变化和失败恢复。

截图采集覆盖本次相关菜单/弹窗/标签、hover/focus、加载/空态/错误与响应式，复杂动效补操作记录或视频。字体渲染差异设有依据的容差，只屏蔽已识别动态噪声，不更新基线或遮盖区域掩盖错误。
原始截图、HTML/HAR 和会话相关材料默认本地 ignored；仅脱敏规格及允许复用的资产进 Git。源码/资产按许可证研究复用；不伪造业务数据、连接或成功状态，后端缺口和未观察行为明确保留。

| 技能/来源 | 用途与边界 |
| --- | --- |
| [clone-website](https://github.com/JCodesMore/ai-website-cloner-template/blob/master/.agents/skills/clone-website/SKILL.md) | 复刻观察→实现→对比流程；遵循 Kokoro 目录、接口与工具链 |
| `frontend-design` | 实现质量、响应式和可访问性；复刻时不重新选风格 |
| [awesome-design-skills](https://github.com/bergside/awesome-design-skills) | 按需参考设计系统表达，不整库加载或覆盖 Manus 样式 |
| `playwright` / `playwright-interactive` / 可用浏览器工具 | 页面观察、操作、截图与回归；复用已可用能力，不重复安装 |

技能链接是来源，不表示已安装；先核对可用性，技能中的默认脚手架、并行或风格建议不扩大本次任务。仅凭截图相似、build 或测试通过不宣称一比一完成，精确程度与剩余差异用实际对照证明。

## 9. 运行资源与安全

- 开发从源码运行；Docker 应用容器用于 release candidate smoke，不替代本地开发验证。不要覆盖正在使用的预览输出或重启他人进程。
- 先探测并复用受管 PostgreSQL/Redis/ObjectStore 与既有配置，不重复启动实例、不清理非自己创建的数据；测试使用独立 run/schema/key prefix/输出目录，只清理自身资源。
- 本地与 CI 的应用目标是一个 PostgreSQL 实例、一个数据库和一套应用 role/credential；每个数据 owner 在同库使用独立 schema 与指向该 schema 的连接 URL。代码、Schema、查询、事务和测试继续禁止跨 owner SQL/JOIN、表引用、ORM model 与 canonical schema 共享；表名前缀不代替 owner schema。现有部分 installer/URL 仍锁定 `public` 或整库空白，须由 owner 代码切片改为 schema 边界后才能宣称单库应用组合通过。测试 fixture 临时库只是运行隔离，不是新增应用数据库或角色。每 owner 独立 production role、GRANT/REVOKE、数据库 mTLS 和 NetworkPolicy 属于部署阶段，不是当前开发门禁。
- Redis 复用受管实例，各 owner 使用隔离 namespace/logical DB；不 reset 共享数据库或清空 Redis。
- 凭据、密码、私钥、token 和敏感 payload 不进入源码、文档、日志或聊天；机器配置、密钥位置、PID/健康快照只留本地 ignored/私有记录。
- 涉及 Windows SSH/远程资源/worker 时先读 `${CODEX_HOME:-$HOME/.codex}/WINDOWS_SSH.md`，实测连接状态，遵循本次授权与记录中的资源预算；未涉及远程操作的任务不加载该记录。
- 发布、CI、扫描、SLO 和运维要求按 owner 的 SECURITY/RELIABILITY/ACCEPTANCE/RUNBOOK 与测试手册执行，不作为局部文档/修复的前置条件。

## 10. 交付与维护

- 简报说明修改/结论、实际验证命令与通过/失败/跳过、未运行原因、风险与后续 owner；已提交附 SHA，未提交附基线 commit 与工作树范围。
- 组件完成、功能验收、全仓通过分别绑定对应范围证据；未决设计、环境缺口或历史报告不作为当前完成证明，不用“顶级/生产级”替代验收。
- 本文件只保留常用入口和执行边界；任务进度归有效计划，设计理由归架构/ADR，语言细节归专项手册。新规则注明触发条件与检查方式，删除重复/过时流程，优先由测试、lint 或 CI 执行。

参考：[GitHub 自定义指令建议](https://docs.github.com/en/copilot/concepts/prompting/response-customization)、[Vercel Chat 仓库指南](https://github.com/vercel/chat/blob/main/AGENTS.md)。这些是方法参考，不替代 Kokoro 的业务裁决。
