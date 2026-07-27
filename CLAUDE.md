# CLAUDE.md - 项目 AI 代理运行矩阵

本文件定义 AI 编码代理在本仓库中的工作方式。

核心原则：边界正确、架构简单、变更可验证、交接可延续。不要用短期速度交换长期清晰度。

---

## 适用范围与优先级

本文件是**通用工程规范**，是一份可复制到任意 Python / TypeScript 项目的基线模板。它不描述某个具体代码库的技术栈、目录结构或验证命令——落地到真实项目时，应在文件末尾追加一节「本仓库事实」，写清实际栈、目录地图、真实测试/lint 命令与运行入口，把通用规范锚定到该项目。

规则来源冲突时的裁决顺序：

1. 用户在当前会话的明确指令。
2. 本文件（项目级 `CLAUDE.md`）。
3. 全局 `~/.claude/CLAUDE.md`。

本文件未覆盖的主题，沿用全局默认；两者对同一主题给出不同规则时，以本文件为准。Commit 作者身份、平台强制署名与 PR 流程以全局规范或运行环境为准，本文件不覆盖这些外部机制。

若运行环境（harness / hook）注入了与本文件冲突的强制要求（例如强制的 commit 尾注），以运行环境的硬性要求为准，并在交接中说明该冲突。

---

## 0. 运行优先级

按以下顺序决策：

1. 保留用户意图与既有行为。
2. 保护模块边界与公开契约。
3. 系统边界数据必须类型明确，并尽量具备运行时校验。
4. 修改应小而聚焦，并匹配现有风格。
5. 声明完成前必须运行真实验证。
6. 架构决策记录在靠近代码的位置。

规则冲突时，优先保护公开契约与运行时正确性。

---

## 1. 会话启动

非平凡修改前：

- 确认工作目录与仓库根目录。
- 阅读实际存在的最近指导入口：`CLAUDE.md`、`AGENTS.md`、`README.md`、`INDEX.md`、`docs/AGENTS.md`、`docs/README.md`、`docs/CURRENT.md`、`docs/CODEBASE_MAP.md`、`docs/task.md`、`docs/lesson.md` 或同等入口文件；不要递归展开整个 `docs/`。
- 修改前检查相关 imports、exports、调用方、测试与运行入口。
- 如果是 git 仓库，先检查工作区状态。
- 未经明确要求，不得覆盖、回滚或清理用户已有改动。

小范围修改可轻量启动；架构性或多文件修改必须完整扫描上下文。

---

## 2. 局部架构地图：`INDEX.md`

`INDEX.md` 是目录或包旁边的局部架构地图。

### 什么时候创建

目录具备以下任一特征时，应创建或维护相邻 `INDEX.md`：

- 存在公开入口：Python `__init__.py`、TypeScript `index.ts`、路由注册表、插件清单或 package export。
- 被代码库其他位置稳定导入。
- 承担运行时装配、连接器契约、持久化、后台任务或框架集成。
- 内部结构复杂到未来修改前需要先读地图。

不要给每个小目录机械创建 `INDEX.md`。它用于降低协作成本，不制造文档负担。

### 应写什么

保持短小、准确、当前有效：

- 目录职责。
- 公开 API：exports、支持的 import、入口文件、非公开内部实现。
- 关键协作者：上游调用方与下游依赖。
- 运行时约束：持久化、副作用、环境变量、异步/线程、外部服务。
- 扩展规则：新代码位置、禁止跨边界 import 的内容。
- 当前陷阱：只写仍有效的 gotchas，不写历史演进。

### 更新规则

修改已建图目录前，先读最近的 `INDEX.md`。

以下变化必须同步更新相关 `INDEX.md`：

- 目录职责或所有权。
- 公开 exports / re-exports。
- 连接器契约、schemas、protocols、API 边界。
- 持久化格式、迁移行为、副作用、运行时约束。
- 跨包依赖方向。

移动代码时，同时更新来源与目标目录的 `INDEX.md`。过时描述直接删除，除非项目明确使用 ADR，否则不保留“历史演进说明”。

`__init__.py` / `index.ts` 的公开 re-export 是最高公开契约。新增或删除 re-export 必须反映在 `INDEX.md` 中。

非公开符号不得跨 Package 边界直接导入。确需外部使用时，应提升到公开入口并记录。

---

## 3. 依赖方向与循环依赖

循环依赖是架构问题，不是类型问题。

发现 import cycle 时，禁止用以下方式遮掩：

- 用 `if TYPE_CHECKING` 遮掩运行时循环依赖。
- 函数内部局部 import。
- 只为绕开 import 的字符串前向引用。
- 保留相同依赖形状的 lazy import 包装。
- `cast`、宽泛 ignore 或其他类型系统逃生口。

必须改为：

- 画出依赖链，找出错误依赖边。
- 删除造成反向依赖的 re-export。
- 将共享 schemas、值对象、protocols、基础契约下沉到 `base`、`common`、`contracts`、`schemas` 等低层模块。
- 高层代码只依赖稳定窄协议。
- 保持 domain/core 独立于框架、传输层和基础设施。

纯类型导入可以使用 `TYPE_CHECKING`，但只能用于不改变运行时依赖方向的类型辅助，不能保留错误边界。

---

## 4. Python 边界规则

Python 类型提升开发期清晰度；Pydantic v2 保护运行时边界。

### 边界数据

禁止使用裸 `dict`、`dict[str, Any]`、`dict[str, object]`、`Mapping[str, Any]`、`Any`、`object`、裸 `list`、`list[Any]`、`list[dict]` 作为系统边界传输载体。

外部 JSON 或第三方 payload 进入系统时，必须在边界附近校验为 Pydantic `BaseModel`，通常放在 `schemas.py` 或对应业务模块。

无法预先建模的第三方 SDK 透传 payload、日志 metadata、实验性 adapter 输入，可以短暂使用宽类型，但必须隔离在边界层，并尽快收敛成明确模型、白名单字段或受控 passthrough。宽类型不得进入核心业务层、持久化模型或跨模块公开 API。

边界模型默认配置：

```python
from pydantic import BaseModel, ConfigDict


class BoundaryModel(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
```

只有确需运行时可变时，才允许去掉 `frozen=True`。`strict=True` 不会自动保护嵌套模型；每个嵌套边界模型都必须显式配置 strict。

优先使用显式约束：

```python
from typing import Annotated
from pydantic import Field

UserCount = Annotated[int, Field(strict=True, ge=0)]
```

### 校验与序列化

- 反序列化使用 `Model.model_validate(raw)`。
- 序列化使用 `model_dump()` / `model_dump_json()`。
- 除非是文档化的边界转换，否则不手写字段映射。
- 区分必填可空字段（`field: T | None`）与可选字段（`field: T | None = None`）。
- 跨字段不变量使用 `@model_validator(mode="after")`。

### 逃生口

避免 `# type: ignore`、`cast(...)`、跨模块访问 `_name`、函数内部局部 import、在边界适配器之外传播宽泛 `Any`。

确需逃生口时，保持局部化，说明原因，并补测试。

---

## 5. TypeScript 边界规则

在 API、存储、worker、CLI、消息总线、浏览器和第三方接口边界：

- 禁止 `any` 或裸 `object` 作为边界类型。
- 不可信输入必须用 Zod、TypeBox、Valibot 或项目既有 schema 系统校验。
- 尽量从运行时 schema 推导静态类型。
- 区分 `.optional()` 与 `.nullable()`。
- 对未知字段明确选择 `.strict()`、`.strip()` 或等价策略。
- 校验包含异步 refine 时，必须使用 `parseAsync`。

Python/TypeScript 混合系统优先从单一事实来源生成客户端类型，例如 OpenAPI、JSON Schema、protobuf 或共享 schema package。不要手工维护两套会漂移的契约。

---

## 6. 实现纪律

- 引入新模式前，先匹配本地风格。
- 不为假想未来添加投机性抽象。
- 修复局部问题时，不顺手重构无关代码。
- 只在确认死代码无用，或它属于本次清理范围时删除。
- 注释只解释为什么，不复述代码。
- 优先使用标准库与项目已有 helper，不轻易引入依赖。
- 对结构化数据使用结构化解析器与 schema 工具，不用脆弱字符串拼接或正则凑合。
- 行为变化必须同步更新测试与文档。

---

## 7. 安全、依赖、生成与迁移

适用于影响运行环境、供应链、数据安全或生产状态的修改。

### 安全与 Secrets

- 不得读取、打印、提交、复制或总结 secrets，包括 API keys、tokens、cookies、私钥、`.env`、生产凭据、用户隐私数据。
- 调试必须确认 secret 时，只报告“存在/缺失”，不输出实际值。
- 新增外部请求、命令执行、文件上传、SQL/NoSQL 查询、模板渲染、路径拼接时，必须考虑注入、遍历、SSRF、权限绕过和敏感信息泄漏。
- 日志、错误信息、文档、测试快照不得包含真实凭据、生产数据或可识别个人信息。
- 示例配置只能使用明显假值，例如 `example-token`、`localhost`、`user@example.com`。

### 依赖与供应链

- 不为小问题引入新依赖。
- 新增或升级依赖必须说明原因、影响范围、lockfile 变化和验证结果。
- 不引入无人维护、来源不明、许可不兼容或功能过大的依赖。
- 依赖升级不得混入无关重构；安全升级可独立提交并附验证说明。

### 生成文件

- 生成文件必须能追溯到生成命令、输入 schema、模板或工具版本。
- 通常修改源 schema 或模板后重新生成，不手改生成文件。
- 大量生成 diff 必须在交接中说明原因，不混入无关功能变更。

### 数据库与迁移

- Schema、迁移脚本、数据修复脚本必须说明数据影响、兼容策略、回滚或前滚方式。
- 不写会直接破坏生产数据的脚本，除非用户明确要求并提供边界条件。
- 迁移尽量向前兼容：先扩展、再双写/回填、最后收缩。
- 持久化格式变化必须更新 `INDEX.md`、运行手册或迁移说明。

---

## 8. 重构与重写模式

默认小步、聚焦、低风险修改。用户明确要求重构/重写/架构优化/质量治理，或现有结构阻碍正确实现时，进入重构与重写模式。

### 进入条件

- 用户明确要求重构、重写、重新设计、架构升级或质量治理。
- 当前设计导致循环依赖、边界泄漏、类型逃逸、重复实现或测试难覆盖。
- 继续补丁式修复会让系统更复杂。
- 新需求与旧抽象方向不一致，继续兼容会产生长期技术债。

### 工作方式

先提出方案，再动手：

- 说明旧结构的核心问题。
- 给出目标结构：模块边界、依赖方向、公开 API、数据契约、迁移步骤。
- 明确哪些行为保持，哪些行为改变。
- 不确定设计允许短期 spike，但产物必须在临时路径，不混入正式实现。
- 优先删除错误抽象，而不是继续加层。
- 允许大幅移动、合并、拆分或重命名，但必须同步更新 imports、tests、`INDEX.md` 与相关文档。
- 不保留“兼容旧内部结构”的无意义适配层；只有外部公开 API 需要兼容时才保留，并标注迁移路径。

### 质量门槛

必须验证：

- 应保留的旧行为核心路径。
- 新边界的失败路径与非法输入。
- 公开 API、exports、CLI、路由、配置入口。
- 删除或移动代码后是否存在陈旧 import、文档、测试。

重构目标不是“看起来整齐”，而是依赖方向更清楚、边界更硬、行为更易验证、未来修改成本更低。

---

## 9. 文档与中间产物

文档分为长期文档和中间产物。

长期文档放入 `docs/`、相邻 `INDEX.md`、`README.md` 或项目既有文档目录，用于记录架构决策、模块边界、公开契约、运行手册、故障处理和长期维护规范。长期文档必须准确、短小、当前有效；不得混入推理草稿、调研过程或废弃方案。

中间产物默认不进入版本控制。优先放在已被 `.gitignore` 覆盖的 `tmp/`、`.tmp/`、`scratch/`、`worklog/`，或系统临时目录。必须在仓库内新建临时目录时，先确认 `.gitignore` 覆盖它，或交接前删除。

`progress.md` 与 `tasks/` 是任务状态记录，不是随手草稿；可按项目约定提交或忽略，但只记录事实状态、下一步和阻塞点，不记录大段推理、失败尝试或实验细节。

中间产物包括临时分析、方案对比、一次性迁移清单、调试输出、实验脚本、临时截图、探索记录。任务结束前必须删除、确认被忽略，或提炼成长期文档。只有整理成迁移指南、ADR、`INDEX.md` 或正式设计文档后，才允许提交。

---

## 10. 测试与验证

声明完成前，运行能证明变更正确的最小命令集合。

常见验证：

- Python：`ruff`、`pyright` 或 `mypy`、定向 `pytest`。
- TypeScript：`tsc --noEmit`、定向 `vitest` / `jest`，以及项目配置的 lint。
- Full-stack/API：契约测试、schema 生成检查、smoke test。
- Frontend：UI 行为变化时运行组件测试或浏览器验证。
- 数据库/迁移：迁移 dry run、回滚或前滚验证、数据兼容性检查。
- 安全敏感变更：注入、权限、路径、secret 泄漏、最小权限验证。

边界测试按相关性覆盖：缺失必填、未知字段、错误类型、`None` / `null`、空字符串、空列表、空对象、数值边界、重复调用幂等性。涉及权限、文件路径、外部 URL、SQL/命令执行时，覆盖越权、路径遍历、注入和非法目标。

不得声称测试通过，如果：

- 必要命令被跳过。
- 测试被静默 `skip` 或 `only`。
- 类型或 lint 错误仍存在但未解释。
- 变更触及边界却只验证 happy path。

无法运行验证时，说明原因和下一步应运行的命令。

---

## 11. 失败处理

出现非预期错误时：

1. 停止继续改代码。
2. 重新阅读相关代码路径、exports 与测试。
3. 判断是计划错误还是实现错误。
4. 更新计划后再继续。

不要在没有新假设的情况下重复重试命令。若正确修复需要改变公开行为、schema 契约、迁移或跨包依赖方向，必须先明确说明。

---

## 12. Git 与 Commit 规范

本节约束 commit 的**内容质量与工作区安全**。commit 作者身份、平台强制署名与 PR 创建流程由全局规范或运行环境决定；但 agent 不得主动添加额外暴露 AI 身份的 message 内容或尾注。

如果当前目录是 git 仓库：

- 重要修改前运行 `git status --short`；默认未提交改动属于用户或其他协作者，不得覆盖、格式化、移动、删除或回滚。
- 修改脏文件前先理解现有改动；无法安全合并时说明风险。
- 禁止 `git reset --hard`、`git checkout -- <file>`、`git clean`、强制覆盖文件，除非用户明确要求。
- 不确定分支用途时，查看分支名、上游分支与最近提交；新功能、重构或高风险修改优先使用独立分支或项目既有隔离机制。
- 未经明确要求，不主动 rebase、force push、改写已发布历史；pull/merge/rebase 前确认工作区是否干净。
- 冲突解决必须理解双方意图，不机械选择 ours/theirs。
- Commit 聚焦、可 review；行为变更、测试更新、相关文档更新可以同提交，但不得混入无关格式化、临时文件、调试输出、生成噪音。
- 大型重构尽量拆成可验证阶段：移动/重命名、契约调整、行为实现、清理删除。
- Commit message 遵循仓库规范；无规范时用简洁祈使句或 Conventional Commits，例如 `fix: validate webhook payload`。禁止泛泛的 “update” / “misc fixes”。
- Agent 不得主动在 commit message、PR 描述或交接文本中添加 `Co-Authored-By: Claude`、AI 生成签名、自动追踪 footer 或任何额外暴露 AI 身份的尾注；运行环境强制注入的除外。
- 交接前查看 diff 与 `git status --short`；生成文件必须有意纳入；临时文件、中间草稿、调试输出必须删除、确认被 `.gitignore` 忽略，或提炼为正式文档。

---

## 13. 交接标准

任务结束时报告：

- 改了什么，触碰了哪些文件。
- 运行了哪些验证命令，结果是什么。
- 已知风险、阻塞点或后续工作。

长任务若已有 `docs/task.md`（跨会话任务状态）或 issue tracker，维护事实型进度记录：已完成、阻塞点、下一步命令、下一步文件。操作级教训归 `docs/lesson.md`（唯一权威，勿再另起 lessons 文件）。

不要留下过时计划、失真架构说明或误导性 TODO。

---

## 14. 结束前速查清单

前文各节是完整规则；本节只是交接前的最后一遍自检，命中任一「否」就回到对应章节。

- **契约**：公开行为、exports、schema、迁移是否变化？变了是否同步更新 `INDEX.md` 与相关文档？（§2 §3 §7）
- **边界**：新增跨信任边界的数据是否有运行时校验、未知字段策略与嵌套 strict？（§4 §5）
- **验证**：是否运行了能证明变更正确的真实命令，而非只跑 happy path？跳过的是否已说明？（§10 §12）
- **安全**：是否可能读取、输出或提交 secrets、生产数据或个人信息？（§7）
- **收尾**：中间产物是否已删除或确认被忽略？是否避免了无关清理与暴露 AI 身份的尾注？（§9 §12）

---

## 本仓库事实：Kokoro 文档归属

本节只适用于 Kokoro 主仓。若本文件被复制到其他项目，应替换为目标项目自己的文档归属规则。

Kokoro 主仓 `docs/` 历史材料较多，agent 不应递归读取整棵目录。默认入口是：

Kokoro 的 `kokoro-agent`、`kokoro-platform`、`kokoro-session`、`kokoro-web` 是 `.gitmodules`
管理的独立仓库。根仓不得把它们机械导入为 ordinary tracked tree，也不得删除 gitlink、合并为单 lock/单 CI；
跨仓治理由 root contract、Infra、兼容矩阵、验证编排和明确的 submodule pin 更新承担。

1. `docs/AGENTS.md`
2. `docs/CURRENT.md`
3. `docs/README.md`
4. `docs/CODEBASE_MAP.md`

除非任务点名或上述入口明确要求，不要把 `docs/product/`、`docs/prototypes/`、`docs/research/`、`docs/brainstorm/`、`docs/plans/` 当作当前实现事实来源。

### 技术方案放哪里

- 正式跨仓技术方案、稳定跨仓规则、长期架构、产品/技术权威结论：放 `docs/kokoro-handbook/`，并在 `docs/kokoro-handbook/README.md` 保持入口。
- 打磨期跨仓草案、方案对比、历史入口：放 `docs/superpowers/specs/YYYY-MM-DD-<topic>.md`。一旦成为正式技术方案，迁入 handbook，specs 只保留指针或历史入口。
- 实现计划：放 `docs/superpowers/plans/YYYY-MM-DD-<topic>.md`。这是执行用计划，不是长期权威。
- 短期派工、交接、worker handoff：放 `docs/handoffs/YYYY-MM-DD-<topic>.md`。派工单过期后不要继续当架构事实。
- 审计、测试、验收、阶段性结果：放 `docs/reports/`。
- 子仓实现细节、调试说明、局部测试说明：放对应子仓的 `kokoro-*/docs/README.md` 和 `kokoro-*/docs/<repo>/...`。不要把跨仓总方案放进 `kokoro-web/docs/`。
- 贴近代码的局部架构地图：放相邻 `INDEX.md`。
- 外部参考、截图、探索笔记、一次性对比、临时脚本：只放 `tmp/` 或 `kokoro-*/tmp/`，不得进入正式文档或正式代码。

通常判断：

- 影响多个子仓或定义系统边界，且仍在打磨：先写主仓 `docs/superpowers/specs/`。
- 已经作为正式方案或长期规则：迁入 `docs/kokoro-handbook/`。
- 只解释某个子仓怎么实现、怎么运行、怎么测试：写到该子仓 `docs/`。
- 只是为了本轮 agent 参考、比对或截图：写到 `tmp/`。

### 当前活跃规则

- 当前主线白名单由 `docs/CURRENT.md` 维护；新增或切换主线时同步更新。
- 给并行 worker 派活时必须注入 `docs/CODEBASE_MAP.md` 和任务相关 spec/plan/handoff。
- 文档冲突时，优先级为：当前用户指令 > 本文件 > `docs/kokoro-handbook/` > `docs/CURRENT.md` / `docs/README.md` / `docs/CODEBASE_MAP.md` > 当前 spec/plan/handoff > 历史产品/原型/研究材料。
- GA / kokoro-agent 只消费不透明 `namespace` 作为运行时隔离键。不得在 GA 侧把 `namespace` 改写为 `user:<ownerId>`，也不得把 `ownerId` / `userId` / `workspaceId` 作为第二身份轴传入 GA；这些身份语义由上游 web/session/platform 解析后映射到 namespace。
