# CX-19 设置、连接器与 Skills 闭环清单

状态只使用三种值：`未开始`、`修复中`、`已实测`。`已实测`表示已和 Manus 参考状态逐项对照并完成相应的本地实际操作；接口可调用、页面可打开或旧测试通过不改变状态。

| 顺序 | 项目 | 当前问题 / 目标 | 状态 | 当前记录 |
| --- | --- | --- | --- | --- |
| S-01 | 动态设置布局切换 | Manus 的紧凑横栏覆盖常见笔记本宽度；只有能同时容纳左栏和可读内容栏的宽屏才使用双栏 | 修复中 | 直接读取同一 `733×764` CSS 视口的 Manus：`380×580`；本地已改为同一尺寸（此前错误地使用 `768px` 级宽度）。桌面双栏还需以同一参考会话复核 |
| S-02 | 窄屏分类栏 | 选中分类前后的标签保持同一水平滚动轨；更多为快捷入口，不删除轨中的后续分类 | 已实测 | 本地硬重载 `账户 / 连接器 / 技能`，每个选中项均完整可见；焦点原生滚动后按完整标签边界回正，不再从“捷键”等半个 CJK 标签开始。更多保留独立 `32px` 轨道且实际打开复核。 |
| S-03 | 设置外壳与滚动 | 弹窗尺寸、左右栏、内容滚动区、边界和遮罩与 Manus 对齐；无双滚动或裁切 | 修复中 | 当前紧凑参考为 `380×580 CSS px`；桌面使用独立双栏 envelope，仍需在同一参考会话下完成两端截图对照 |
| S-04 | 加载体验 | 切换设置不重置成居中“正在加载”；已有内容保持，首读仅保留同布局骨架 | 修复中 | MCP 与 Skills 投影均已提升至 AppFrame 会话预热；MCP 还会将已通过 schema 校验、无密钥的首屏 owner 投影按 subject 留在本 tab 的 `sessionStorage`，重载先画已确认卡片、同时后台 revalidate。真实浏览器二次重载 780ms 时卡片已在、无文字加载或骨架；Team 当前实际读取会进入“团队列表加载失败”，已去除文字加载中间态但 owner read 故障仍待独立闭环 |
| M-01 | MCP 创建入口 | “创建”显示 Custom API、Custom MCP、JSON 导入、URL 添加四项，顺序和菜单层级与 Manus 一致 | 已实测 | 本地菜单已实际打开复核四项 |
| M-02 | 自定义 API | 新建、详情、编辑、密钥、错误恢复、删除后的列表更新、图标边界完整闭环 | 修复中 | 已在本地真实同源链执行临时 profile 的新建→详情（密钥仅显示“已配置”）→编辑备注→立即列表/详情回读→确认删除→列表消失，并清理临时记录；错误恢复与图标 asset-ref 契约仍未闭环 |
| M-03 | 自定义 MCP | 新建、详情、管理、headers、保存、断开、删除、状态刷新完成闭环 | 修复中 | 已在真实同源链完成失败注册→待连接行即时出现→详情→管理→删除→立即移除；删除在 owner 成功响应后先从当前投影隐藏，再后台回读，消除旧卡残留。既有真实 MCP 也已实际执行编辑备注→保存→“试用一下”→已连接回读并恢复备注。上传控件为与参考一致的独立 `64×32px` 按钮。新建成功 Prepare、headers 变更、断开仍待逐项闭环 |
| M-04 | JSON 导入 MCP | 多服务器 JSON 由 Platform 原子导入，前端显示逐项结果；不保留旧的单一 HTTP 浏览器循环 | 修复中 | 当前输入明确只接受一条远程 Streamable HTTP 配置，已撤下会误导用户的 STDIO/SSE 示例；owner 导入能力尚未发布到 BFF/App artifact |
| M-05 | URL MCP / OAuth | URL 校验、发现、授权新窗口、回调、重连、撤销、失败恢复均由隔离本地标准 Provider 跑通 | 修复中 | 已实际打开并对照基础、进阶 URL 表单：基础态移除错误的说明输入框，进阶 OAuth 字段收进同一设置框且固定为 `480×496px`；授权新窗口、回调、重连、撤销与失败恢复仍待隔离本地 Provider |
| M-06 | Provider 目录与 Admin | 应用目录、详情与 Admin 管理使用同一现行 owner 数据面并可联动 | 修复中 | Admin 已去除每个 Provider 请求的重复身份预检并修正转发路径；当前 `3310` 运行时仍与现行 owner schema 脱节，隔离本地运行时待建立 |
| M-07 | 连接器列表视觉 | 宽屏双列卡片、紧凑设置单列卡片、图标、状态、描述截断、空态、搜索、滚动与 Manus 对齐 | 修复中 | 实测 `1436×900` 紧凑单列（行宽 `736px`）、`600×900` 紧凑单列（行宽 `536px`）、`1600×900` 工作台双列（各 `378px`）；图标、空态与滚动仍待对照 |
| R-01 | 隔离本地组合运行时 | 同一 run 启动 IAM、BFF、Platform、Storage、App，并向 Platform 传入精确的 MCP/Custom API/Admin service credential 与 owner-only keyring；不启动 Mori | 修复中 | 启动器已扩为生成 run-owned 0600 service credential、MCP/Custom API keyring，并启用 `mcp-personal`、`custom-api-personal`、`mcp-provider-admin`；当前仍待固定 Platform→BFF artifact 后实际启动并完成真实流程 |
| K-01 | Skills 空态控制 | 空态下搜索和范围筛选保持可操作，不展示禁用的灰色控件 | 已实测 | 已在 Settings 与外部 `/app/skills` 实际刷新复核：两处均保留搜索、分类、探索/添加入口，并在 owner 返回空目录时稳定显示空态 |
| K-02 | Skills 目录视觉 | 卡片、开关、过滤、搜索、详情与 Manus 对齐；有数据时不再呈空目录 | 修复中 | 已修复外部页面仍调用已退役 `/self/skills/catalog` 而得到 404 的分叉；Settings 与外部均使用同一 owner-backed 目录读模型。当前本地 owner 真实返回空目录，因此卡片/开关仅能在有发布数据的隔离 owner run 中继续对照，不伪造目录项 |
| K-03 | Skills CRUD | 探索、安装/启用、关闭、导入、详情、失败恢复和列表刷新逐项闭环 | 修复中 | 已实际打开 Settings 已添加页→探索目录及外部 `/app/skills`；读链可达且无错误卡。安装/启用、关闭、导入、详情、失败恢复和刷新仍须以真实可用 Skill 的完整纵向旅程验收 |
| V-01 | 对照归档 | 每个完成项保存 Manus 参考、Kokoro 实现、实际操作结果三份证据 | 修复中 | 已有参考归档；后续按此表逐项补齐实现证据 |

## 执行规则

1. 先完成 S-01 至 S-04，锁定设置的桌面/窄屏结构，再进入各功能面。
2. 每个 MCP 或 Skills 项按“列表 → 创建 → 详情 → 编辑 → 状态变化 → 删除/撤销 → 错误恢复”执行；不跳过中间步骤。
3. 每项结束时更新本表的状态和证据位置；未实测保持原状态。
4. 已归档的 Manus 参考位于 `var/dev/screenshots/manus-comparison/2026-10-13/connectors-alignment/`；新增材料与实现截图按同一功能名归档。

## 2026-10-14：本轮真实浏览器补充复核

- **M-01（已实测）**：同一已登录本地会话依次进入并关闭四种创建入口：自定义 API、自定义 MCP、JSON 导入、URL 添加 MCP（Beta）。四个入口均为独立表单，未出现通用“正在加载”层；URL 使用实际 `menuitem` 可达，而非只检查菜单文字。
- **M-02（修复中）**：以临时 Custom API profile 完成真实同源 `创建 → 详情 → 编辑备注 → 列表回读 → 确认删除`。密钥值从未回显；删除 owner 成功后 1.1 秒内列表已无该行，临时 profile 已清理。详情此前错误复用 Custom MCP 的固定高度样式并留下大块空白；现已拆出 API 的详情/编辑布局类，详情按内容收拢，编辑层维持可滚动正文和固定操作栏。
- **S-04（修复中）**：从 Settings 跳转至外部 `/app/plugins` 时，外部页曾把同一 admitted subject 加上 session generation 作为 MCP projection identity，破坏既有预热命中并露出骨架。现与 Settings 使用同一 subject-scoped identity；在已预热后跳转实测无“正在加载”文字。目录真实为空时只显示 owner 返回的空态，不伪造 Provider 卡片。
- **K-01（已实测）**：外部 `/app/skills` 实际访问后直接保留搜索、分类、添加和真实空结果；无“正在加载”或读取失败卡。当前 owner 返回空目录，技能卡、启停、详情和安装仍遵循 K-02/K-03 的真实数据前提。

## 2026-10-14：错误恢复与外部页冷启动复核

- **M-03 / M-05（修复中）**：真实浏览器分别在“自定义 MCP”和“通过 URL 添加 MCP”输入已登记的本地 MCP endpoint。此前 owner 的“URL 已注册”与幂等键冲突都被 BFF 归成 `mcp_personal_idempotency_conflict`，前端只能显示“连接异常”。现 BFF 保留真实幂等冲突的既有语义，并把 owner 的明确 URL 冲突映射为 `mcp_personal_server_url_conflict`；App 代理允许该稳定错误码，两个表单均显示“此服务器 URL 已添加。请编辑已有连接器或使用其他 URL。”。两次尝试均未创建临时记录。headers 的正向创建仍需使用一个可删除的、未登记真实 endpoint 单独验收。
- **S-04 / 外部连接器与技能（修复中）**：直接冷打开 `/app/plugins`、`/app/skills` 与 `#/account/settings/skills`。会话判定期间改为 data-free 的 AppFrame booting shell，不再用居中的“正在加载工作区”文本/Spinner 替换整页；该 shell 不挂 Runtime 数据 client。会话完成后外部连接器稳定显示真实 Provider 空态，外部技能和 Settings 技能均保留真实 owner 空态及搜索/筛选/添加入口。此项不将空目录伪称为有卡片的目录闭环。

- **M-03 / M-05（修复中）**：真实表单验证发现 BFF/App 曾允许带 query 的 MCP URL，但 Platform 的 canonical server identity 明确拒绝 query，结果用户点击后才得到泛化“连接异常”。现 App 的 Custom MCP、URL MCP 与 hub schema，以及 BFF 请求解析共同拒绝 query/hash/userinfo；浏览器输入 `http://127.0.0.1:43191/mcp?invalid=query` 后保存按钮保持禁用，未发送写入也没有产生临时记录。该约束与 Platform `normalizeMcpServerIdentity` 完全一致。
- **M-03 / M-05（修复中，补充）**：上述 query URL 的 Custom MCP 浏览器复核同时确认：输入后立即显示字段内“填写有误：请检查名称、URL 和传输方式。”并保持保存禁用；不是静默禁用，也不会等到远端返回泛化错误。

## 2026-10-14：四种创建表单与 Skills/外部入口复测

- **M-01（已实测，复测）**：在同一已登录本地 Settings 会话中逐一执行“创建 → 自定义 API → 关闭 → 自定义 MCP → 关闭 → JSON 导入 → 关闭 → URL 添加 MCP → 关闭”。四个入口均为各自的独立表单：API 的名称/图标/备注/密钥区、MCP 的名称/传输/URL/headers、JSON 的编辑区、URL 的基础/进阶设置和固定底栏均在首屏完整可见；没有通用编辑层或“正在加载”中间态。
- **K-01（已实测，复测）**：Settings 技能页实际打开“添加”，四个真实入口（AI 创建、上传、GitHub 导入、官方技能）均显示且未挤压页面。外部 `/app/skills` 冷打开后为可操作的搜索、范围标签、我的技能/添加和 owner 空态；外部 `/app/plugins` 冷打开后为搜索、目录标签、管理/创建和 Provider 空态。三处均不使用虚构卡片填充空目录。
- **S-02 / S-04（修复中，复测）**：本轮连接器、技能和外部页的连续跳转没有出现文本型“正在加载”、整页替换或布局坍缩。紧凑导航保留真实水平轨和独立更多入口；实际 owner 返回空集合时只改变内容区的空态，工具栏和标签位置不发生跳动。
- **仍待真实依赖**：Skills 的上传/安装/启停/详情/删除要求至少一条可删除的真实 owner Skill；JSON 原子导入要求已发布的 Platform artifact；URL OAuth 与 Provider/Admin 联动要求真实隔离 OAuth Provider 与开发管理员会话。它们继续保持“修复中”，不由当前空目录或界面可打开替代。

## 2026-10-14：隔离开发管理员运行时

- **R-01（修复中，新增实测）**：本地 IAM 的 `web-oidc-flow-host` 现在支持仅在 `IAM_TEST_SKILL_SANDBOX_MODE=1` 的隔离资源中启用 `IAM_TEST_PLATFORM_ADMIN=1`。它通过 IAM 的 `PlatformAdminManagementService`、同一 CAS 事务和 AuditWriter 创建开发管理员事实，再签发真实 Product-Web PKCE 会话并由 `/internal/v1/session-authorizations/verify` 确认 `platform_admin=true` 后才发出 ready。该 fixture 已使用临时命名数据库/Redis prefix 实测启动与 stop 清理成功；没有修改当前浏览器用户、没有伪造 Admin cookie，也不会启动 Mori。
- **R-01（修复中）**：`scripts/dev/serve_local_login.py --platform-admin` 只允许和受管 Platform 一起运行，避免将开发管理员标志误接到旧的非 Platform 组合。完整的 App + BFF + Platform + Storage 启动仍需要固定的 Platform artifact；当前脏工作树不会放宽启动器的 release-source 一致性检查。
- **M-06 / K-03（未完成）**：隔离管理员会话已经具备真实准入基础，但 Provider 目录样本、Admin CRUD 联动、Skills 的真实可删除目录项仍需在该完整 owner run 中逐项实测，继续保持“修复中”。

## 2026-10-14：本轮真实 owner 与浏览器复核

- **M-06（真实 owner 事务，已补证）**：以独立命名 PostgreSQL 数据库运行 Platform 的 Provider 管理集成：创建 Provider → 去重/规范化策略读回 → 状态版本冲突拒绝 → 禁用 → 删除 → 目录为空及软删除版本读回。该路径使用实际 Prisma schema 与 `McpProviderAdminService`，共 1 项通过；它证明 owner 的 Provider CRUD 状态机可执行，但不替代 App/Admin 的完整隔离组合联动。
- **M-03 / M-05（真实 owner 事务，已补证）**：以独立命名 PostgreSQL 数据库运行 Product MCP 集成：个人连接器创建、编辑、版本冲突、软删除、OAuth claim 的先持久化与重复开始拒绝、按用户/查询绑定的分页，另含撤销行为；共 7 项通过。OAuth 仍缺标准本地 Provider 的浏览器新窗口→回调→撤销现场，故保持“修复中”。
- **K-02 / K-03（真实 owner 事务，已补证）**：以独立命名 PostgreSQL/Redis 数据库运行 Skills 目录与本地导入 owner 集成，目录过滤/分页、Begin、感染拒绝、Finalize、安装事实、并发与回读等共 32 项通过。当前 `3310` 的真实目录仍为空；卡片安装、开关、详情、删除的浏览器旅程仍须使用该隔离组合中的真实可删除 Skill，不能用测试 fixture 或示例卡替代。
- **K-03（环境边界已记录）**：补跑完整 Skill installation integration 时，通用本地 PostgreSQL URL 先被 Platform schema guard 拒绝；补齐 `schema=kokoro_platform` 后，目标共享数据库没有 Platform 表而被测试主动拒绝。没有在共享数据库建表或写入样本。该旅程只能在启动器创建的 run-owned Platform schema 内执行，正是 R-01 尚未完成的隔离组合工作，不将该失败归因于页面或用例。
- **M-01（浏览器复核）**：本地同一 Settings 会话逐一打开 Custom API、Custom MCP、JSON Import；三者均为各自独立层，未出现通用“正在加载”层。JSON 层为独立 `600×458` 配置编辑器而非复用 Custom MCP 的详情层。已打开既有 JSON MCP 的详情；它当前在 owner 模型中属于私有 MCP，因此按 Custom MCP 信息模型展示。URL 表单与该详情的逐像素成对复拍仍保持待办。
- **S-02（已实测，修复）**：此前技能深链硬重载会让选中项停在右侧轨外；即使先让浏览器为键盘焦点原生滚动，也会从“捷键”这类半个 CJK 标签开始。导航轨现在把已挂载的选中 tab 作为明确的组件状态，在实际滚动容器 resize / focus 后按完整条目边界回正。真实浏览器已重新硬重载技能并打开更多菜单：`通用 / 快捷键 / 个性化 / 连接器 / 技能` 均为完整标签，技能选中态与更多菜单同时可见。


## 2026-10-14：本轮外部 Skills/MCP 与无感加载复核

- **S-02（已实测）**：重新以真实浏览器硬重载 `#/account/settings/skills` 和 `#/account/settings/mcp`。技能与连接器均展示完整的选中标签；焦点滚动不再从半个汉字开始。打开更多菜单后，后续分类位于独立菜单层，未与内容区或菜单按钮重叠。
- **M-01（已实测，复测）**：连接器创建菜单和四个独立表单再次逐项实际打开：自定义 API、自定义 MCP、JSON 导入、URL 添加 MCP（Beta）。字段模型、进阶设置和固定操作栏互不复用，全部首屏可见，没有通用“正在加载”编辑层。
- **K-01（已实测，复测）**：外部 `/app/skills` 冷导航在会话判定期只显示禁用的产品输入外壳，没有可见的“正在加载”文字或 Spinner；完成后稳定进入真实 owner 空目录（搜索、分类、我的技能、添加仍可操作）。这不替代 K-02/K-03：可安装 Skill 的真实卡片、启停、详情、删除仍需隔离 owner 组合。

## 2026-10-14：外部页首帧连续性补充

- **S-04（修复中，已补实际首帧）**：外部 `/app/skills` 强制重载后，浏览器先捕获到 server-admitted 的禁用输入外壳，再稳定进入 Skills 目录。首帧现在保留与工作台一致的静态窄 rail、顶部栏与 Composer 几何；没有“正在加载”文字、Spinner、脉冲或跳动的居中卡片。该外壳不启动 Runtime client、无可操作控件，完成会话判定后才替换为 owner-backed 页面。`/app/skills` 最终状态继续是实际 owner 空目录，搜索、分类、我的技能、添加均可用。
- **验证**：本地真实浏览器依次保留首帧与稳定态截图；新增一条组件级行为回归只保护“静态结构存在、禁用、无可见加载文案”，不以 CSS 字符串或 fixture 断言代替浏览器验收。完整 Skills 卡片生命周期及外部 MCP/OAuth 仍按 K-02/K-03、M-04/M-05 保持修复中。

## 2026-10-14：本轮 MCP 原子导入与四表单复核

- **M-04（修复中，owner 事务已补证）**：使用实际 Platform PostgreSQL owner schema 新增了批量 JSON 导入的事务回归：先写入一个既有私有 MCP，再发送“新 URL + 已存在 URL”的两项导入，owner 抛错后数据库仍保持原有 2 个 server / 2 个 connector；随后导入两项有效配置，回读为 4 个 server / 4 个 connector，并以同一 command 重放得到同一 receipt。header secret 只验证配置状态，未回显值。该集成文件在 run-owned PostgreSQL 上 3/3 通过。浏览器 JSON 表单目前仍受旧 BFF artifact 限制而只允许单条输入，故不将 owner 原子事务误记为前端已闭环。
- **M-01（已实测，再复拍）**：本地已登录 Settings 会话按“打开→查看→取消”执行了四种创建类型。Custom API、Custom MCP、JSON 导入、URL MCP 均为独立 dialog；基础字段、各自专有区域、禁用前的保存状态与取消返回均可见，无通用 loading dialog。URL MCP 的“进阶设置”保持折叠，避免把 OAuth 字段推入首屏。
- **K-01 / S-04（已实测）**：Settings 内在“连接器→技能”切换后直接进入可操作的 Skills 空态；重载 MCP Settings 首帧只出现静态工作台骨架，随后进入真实 owner 卡片列表。二者均没有文字型“正在加载”、Spinner 或居中阻断层。

## 2026-10-14：Skills 组件边界与实际 Settings 复测

- **K-01（已实测，组件化补强）**：Settings 的 Skills 主编排保留 owner/read/mutation 状态，已将资源键、安装卡片、目录对话框、版本读与卡片映射拆为独立模块；目录与卡片的视觉组件不再和连接器/设置外壳共享条件布局。重载实际 Settings 后，技能空态、搜索、四个范围筛选和“添加”四项（AI 创建、上传、GitHub 导入、官方技能）均稳定可见，菜单未压住内容，也没有 loading 弹层。
- **K-02/K-03（修复中）**：本轮没有用模拟技能填充 owner 空目录；真实安装、启停、详情、删除仍只在启动完整隔离 owner 组合并提供可清理 Skill 后标记为已实测。

## 2026-10-14：外部 Skills / MCP 冷启动再验

- **S-04（已实测）**：分别直接导航 `/app/skills` 和 `/app/plugins`。两条路径的第一帧均为静态 AppFrame 几何与禁用 Composer，不显示可见加载文案或 Spinner；约 1 秒后分别稳定进入真实 owner 返回的 Skills 空结果与 Connector Provider 空结果。搜索、分类及“我的技能/添加”或“管理连接器/创建”保持可用，空结果没有用演示卡替代。

## 2026-10-14：外部连接器标题与工具栏挤压修复

- **M-07（修复中，外部页布局补证）**：`/app/plugins` 复现到标题“连接器”被工具栏挤成逐字竖排、创建按钮向右裁切。根因是外部页和紧凑 Settings 共用 MCP 标题网格，旧规则把标题所在列设为可压缩的 `minmax(0, 1fr)`，而工具栏占据固有宽度；永久应用侧栏缩窄内容列后，纯 viewport 断点也未及时生效。
- **修复**：外部页面单独保留标题的固有宽度与不换行；当视口低于 `56rem` 时，标题和工具栏进入两个稳定行。该规则显式排除 `data-settings-layout=true`，不改变 Settings 已验证的紧凑单行工具栏。
- **实测**：默认窄视口、`1440×900` 宽屏均实际强制重载 `/app/plugins`；标题完整为单行“连接器”，搜索、管理连接器和创建按钮均完整可见，分类及真实 Provider 空态未被挤压或裁切；随后回到默认视口实际打开 Settings/连接器，搜索、浏览连接器、创建和已添加列表仍保持同一紧凑单行布局。默认视口已恢复。

## 2026-10-14：Custom MCP 浏览器写链闭环补证

- **M-03（已实测：创建→读取→编辑→重试）**：以仅监听本机回环地址的临时 MCP fixture 完成实际 Settings 写链。使用允许的 `X-Client-Key` header 后，创建 `校验测试 MCP` 成功；详情读取为“自定义 MCP”，服务端回读 headers 仅显示“已配置”，不回显值。编辑名称后硬重载仍读到 `校验测试 MCP 已编辑`；随后点击“试用一下”，owner 回执为 `prepare_status=ready`、连接器 `status=active/enabled=true`，并发现 fixture 的 `echo` tool。列表最终显示“已连接”。
- **M-03（已修复：前端预校验）**：实测此前输入 `X-Kokoro-E2E` 会穿过 App，直到 BFF 用 `invalid_mcp_personal_request` 拒绝，界面仅显示泛化异常。现在创建表单、详情编辑表单和 hub 请求 schema 共享同一 header-name 校验：保留 `Authorization`、`Cookie`、`Host`、`Proxy-*`、`Sec-*`、`X-Kokoro-*`、`X-Forwarded-*` 等名称立即显示明确原因、保存保持禁用且不发送写入；允许的 `X-Client-Key` 继续完成上述真实写链。
- **M-03（待确认清理）**：为了实际完成删除/撤销验证，当前保留唯一的本地临时记录 `校验测试 MCP 已编辑`。删除是持久化数据操作，下一步仅待用户确认后在界面点击最终删除并回读列表无此记录；临时回环 fixture 随删除验收完成即停止。

## 2026-10-14：BFF v1 连接器路由回归

- **M-03 / M-05 / M-06（路由契约补证）**：BFF 实际构建后运行 MCP private-server、OAuth authorization、connector command 与 Provider Admin 路由的聚焦回归，共 49 项通过。覆盖个人 MCP 严格入参、登记/读回/prepare/update/delete 的 CAS 与幂等、OAuth begin/reconnect/opaque callback 完成、safe projection 不泄露 header secret，以及 Provider Admin 目录读写与普通用户拒绝。该证据证明当前 BFF 边界的 v1 契约可编译、可执行；不替代仍待隔离组合的真实 OAuth 新窗口与 App/Admin 联动。

## 2026-10-14：临时 MCP 清理与外部连接器模块验收

- **M-03（已实测：删除与资源清理）**：在用户当前确认后，实际打开 `校验测试 MCP 已编辑` 的详情菜单并执行“删除 → 确认移除”。回读“已添加”列表后该条目已不存在；随后停止仅供该验证使用的本机回环 MCP fixture。此前记录的临时数据和进程均已清理。
- **M-07（已实测：外部连接器模块）**：实际访问 `/app/plugins`，确认标题为完整单行“连接器”，搜索、`管理连接器` 与 `创建` 均未裁切；创建菜单完整暴露四条真实路径（自定义 API、自定义 MCP、JSON 导入、URL 添加 MCP Beta）。点击“管理连接器”后在同一页面切换为实际已添加列表，且已删除的临时条目没有残留；点击“浏览连接器”可返回真实 Provider 目录。目录当前由 owner 返回空集合，因此仅显示真实的“当前没有可添加的连接器提供方”空态，未注入演示卡片。搜索空查询和非命中查询均保持工具栏、分类和内容区稳定，没有 loading 文案或 Spinner。
- **M-07（外部路径补测）**：在 `/app/plugins` 目录态逐项打开并取消四种真实创建表单；随后进入“管理连接器”，实际打开 `CX11 Custom MCP Ready` 的详情并返回目录。外部入口复用同一组独立表单与详情模型，但目录、已添加列表和详情切换保持各自组件边界，未产生写入或临时记录。

## 2026-10-14：外部连接器广场与管理入口分层

- **M-07（已实测修正）**：重新实测 Manus `/app/plugins#/connectors/connectors` 后确认：外部“插件”入口是 Provider 连接器广场；点击“管理连接器”会打开共享的 Settings/连接器弹层，而不是在广场内部切换成“已添加”列表。此前把两者误收敛为同一默认视图，属于错误实现，已移除。
- **修复**：Kokoro `/app/plugins` 现在固定以真实 Provider 目录为初态；`管理连接器` 委托 AppFrame 打开 `Settings → 连接器`，该弹层读取同一 admitted subject 的已添加连接器投影。两入口共享 owner 读取契约与缓存 identity，但保留不同的信息架构和默认视图。
- **浏览器复核**：实际打开本地 `/app/plugins` 后，页面保留广场标题、搜索、分类、管理/创建入口和 Provider 空态；点击“管理连接器”立即弹出 Settings/连接器，并读到当前用户的 `CX11 JSON MCP`、`CX11 Custom MCP Ready`、`CX12 Custom Fixture`、`CX11 Custom MCP Full`、`CX11 JSON DeepWiki`。关闭弹层后回到原广场。
- **数据边界**：当前 Platform Provider 目录真实为空，因此广场忠实显示空态；不注入演示 Provider 卡片或虚构可连接状态。目录有 owner 数据后，同一广场组件会直接呈现对应卡片。

## 2026-10-14：Skills 外部广场真实空目录语义

- **K-01（已修复）**：实际打开本地 `/app/skills` 时，owner 返回空 Hub 目录却被外部广场错误渲染为“没有匹配的技能”；这把“没有目录数据”和“用户搜索/筛选没有命中”混为一谈，也掩盖了 Skills 尚未闭环的真实状态。现在空目录明确显示“还没有可用技能”及上传/官方上架说明；只有存在目录项后再搜索或筛选为空时才显示“没有匹配的技能”。顶部搜索、我的技能、添加和分类均保持可操作，不加入 loading 层或演示卡片。
- **验证**：Skills 外部目录聚焦行为套件 113 项、App lint、App typecheck 与 diff check 通过。当前运行时的 Hub owner 仍返回空目录，因此真实浏览器会显示这一明确空态；目录卡片、安装、启停、详情、移除的实景验收继续以真实 owner Skill 为准。

## 2026-10-15：JSON MCP 导入同源闭环补证

- **M-04（已实测）**：在干净隔离组合（App、BFF、Platform、IAM；未启动 Mori）真实登录后，通过 Settings 的“创建 → 通过 JSON 导入 MCP”执行了两次完整旅程。单项本地 HTTP fixture 导入后，实际进入详情并执行“试用一下”，Platform 记录了 `ImportPersonalMcpJson → GetPersonalMcpServer → PreparePersonalMcpServer`；随后从“管理 → 删除 → 确认移除”回到真实空列表。第二次以两项 Streamable HTTP 文档原子导入，本地同源 API 回读到两条不同的 owner connector，证明浏览器不再把批量文档降级成旧的单项循环。临时验证记录属于 run-owned 资源，停止隔离运行时后清理。
- **修复**：App 的同源 Hub 代理此前遗漏 `POST /mcp/servers/import`，即使 BFF/Platform 已支持批量导入也会在 Web 层提前返回 `400 invalid_mcp_personal_request`。现在代理对该路径应用同样的 origin、idempotency、body 限制、201 回执和逐项 safe projection 校验；浏览器 client 同步接受 creation 的 201。创建完成后连接器 section 使用 mutation generation 重建只读投影，避免 owner 已成功写入而旧空缓存仍留在页面。

## 2026-10-15：URL MCP OAuth 新窗口闭环补证

- **M-05（已实测）**：在干净隔离组合（App、BFF、Platform、IAM；未启动 Mori）中，通过 Settings 的“创建 → 通过 URL 添加 MCP → 进阶设置”登记本机回环 OAuth MCP。点击“连接”后，新窗口完成授权回调、自动关闭，原 Settings 列表回读连接成功图标；详情的“管理 → 断开连接”发送真实删除/撤销命令，列表随 owner `200` 回执立即回到空态。浏览器观察到 begin authorization、列表重读与 DELETE 都为同源 200；该流程不使用前端模拟连接或成功状态。
- **修复**：OAuth URL 的本地开发回环许可必须在三个边界一致：Platform 的 challenge/metadata transport、BFF/App 的 safe projection schema、以及 App 新窗口启动前的 URL 审核。此前最后一层仍只接受 HTTPS，因此 owner 返回成功授权 URL 后浏览器在打开前抛出 `invalid owner authorization URL`。此外，隔离运行时曾把回调设为不存在的 `/api/mcp/oauth/callback`；现改为真实 Next 页面 `/mcp/oauth/callback`，由页面完成 code/state 回传、发布完成消息并关闭新窗口。生产环境仍仅接受 HTTPS。

## 2026-10-15：四种连接器创建路径逐项浏览器复核

- **M-01 / M-03 / M-04 / M-05（已实测）**：同一干净隔离 Settings 会话逐项实际走完四种入口，而非依赖定向 UI 断言：
  1. 自定义 API：创建含环境变量密钥 → 详情只显示“已配置”而不回显值 → 编辑名称 → 删除确认；
  2. 自定义 MCP：创建 → 详情“试用一下”发现本机 fixture tool 并显示连接成功 → 编辑 → 删除确认；
  3. JSON 导入 MCP：导入 Manus-shaped `mcpServers` 文档 → 详情试用成功 → 删除确认；
  4. URL 添加 MCP：登记 OAuth 客户端 → 新窗口授权/回调/自动关闭 → 成功图标 → 管理菜单断开连接。
- **结果**：每条路径均在 owner 回执后立即刷新为对应列表状态，临时记录在验证中逐项删除，隔离 runtime 与 fixture 已停止。没有把“菜单可打开”或静态截图作为 CRUD 成功依据。

## 2026-10-15：外部 Skills 读取与空态修正

- **K-01（已修复）**：外部 `/app/skills` 曾继续使用退役的 flattened catalog client，因此在 Settings 健康时仍可能得到“技能池加载失败”。它现在与 Settings 一样只走 typed owner `ListHubSkills` / `ListSkills` 投影；同一读模型、缓存键和身份边界不再因入口不同而分叉。
- **空态**：owner 返回空目录时展示“还没有可用技能”及可恢复的上传/上架引导；搜索或分类后才展示“没有匹配的技能”。避免把无数据误报为加载失败，也不用演示卡片伪造目录。
- **首帧**：移除了 AppFrame 过渡层中的可见“正在加载工作区”文字，保留稳定外壳与禁用输入，避免深链/重载时以文字加载层打断布局。

## 2026-10-15：Admin Provider 同源产品会话适配器

- **M-06（代码与契约已补齐，运行组合待续）**：Admin 的 MCP Provider 控制台现在通过产品同源 `/api/admin/mcp/...` 适配器使用既有 Product Session；适配器将 browser command 精确转发至 BFF 的 `/v1/admin/mcp/...`，保留请求关联、`no-store` 和 mutation 的幂等键。此前首段错误限制为 `admin`，使真实 Admin 发出的 `mcp/providers` 在进入 BFF 前被 404；现已更正为 owner 资源首段 `mcp`/`skills`，并以聚焦契约测试覆盖成功转发、非法路径和缺会话拒绝。
- **运行证据边界**：该改动已通过 App 的聚焦契约、lint、typecheck；完整的 `/manage` 浏览器 CRUD 仍要求可重复启动的独立 Admin + IAM 配置组合。它不与四种用户 MCP Settings 创建路径混淆，也不把单元回归标为 Admin UI 浏览器闭环。

## 2026-10-15：Admin 单会话运行时补齐

- **M-06 / R-01（修复中）**：Admin 已完成第二套 OIDC/NextAuth、Redis session、刷新与 CSRF 重放分支的 clean-slate 删除；它仅消费 Product 同源会话，并由 Product adapter 再转至 BFF 的 `/v1/admin/mcp/...`。`/manage` 入口保留一次准入读取，业务 Provider 请求不再为每个 CRUD 重复做身份预检。
- **R-01（修复中）**：本地隔离启动器新增可选 `--admin-node-bin`。该选项只能与 `--platform-admin` 和 owned Platform 同时使用，启动 Admin 后由 Web 的 `/manage` 同源网关承载；运行时只传递公开 origin、tenant 与 Product 会话，不建立 Admin 专用浏览器登录态。当前 shell 没有配置隔离 PostgreSQL/Redis 输入，因此尚未把启动器和 Admin CRUD 标为浏览器实测。
- **代码验证**：Admin 子仓已通过 110 个测试、typecheck、lint 与 diff check；启动器已通过 40 个 focused guard tests 与 Python 编译检查。真实 `/manage` CRUD 仍以具备 run-owned PostgreSQL/Redis 的隔离运行作为下一证据，不使用当前普通用户 `3310` 会话伪造管理员成功态。

## 2026-10-15：设置动态模式与侧栏重测

- **S-01 / S-03（修复中，当前视口已复测）**：在同一 `811×764 CSS px` IAB 视口读取 Manus：设置卡为 `720×687.6px`，左侧 rail 为 `221px`，连接器行 `196×32px`。本地此前以 `95.99rem` 作为紧凑模式上限，错误地在这个可容纳 desktop rail 的视口收成 `380×580px` 横栏 sheet。现将切换点收敛至 `47.99rem`：桌面空间足够时保持 rail，只有无法容纳 `720px` envelope 的窄视口才进入紧凑 sheet。
- **S-02（修复中）**：最窄 compact rail 不再增加标签内边距；旧的 `0.4rem` 覆盖会在视口收缩时反向挤掉一整项 CJK 标签。保留 `4px` 节奏，选中项仍交给实际横向轨的 ResizeObserver 定位。
- **对照结果**：修正后的本地在该视口为 `720×687.6px` 卡片、`221px` rail、`220px` tablist、`196×32px` 连接器选中项，与当前 Manus 同一参考会话的几何对齐。组件测试保留“当前 tab 获得焦点”的用户结果，删除与实现耦合且阻止浏览器完整显现深链选中项的 `preventScroll` 断言。


## 2026-10-15：设置缩窄侧栏导航回归修复

- **S-02（已实测）**：对 `760×764`、`420×764` 与 `360×740` 三个 CSS 视口执行实际浏览器回归。720px envelope 能容纳时仍是 desktop rail；窄屏进入 380px compact sheet。
- **修复**：横向导航的“向右揭示”滚动改为向后一个完整标签边界对齐。旧逻辑错误地向前取整，导致 360px 下激活“连接器”时只显示半个“连”字。
- **结果**：在 `360×740` 切换“连接器”“技能”后，激活项均完整呈现；打开更多菜单后十个溢出条目完整可见，未覆盖当前标签。`settings-modal` 聚焦回归 35 项通过；临时 viewport override 已恢复。

## 2026-10-15：Admin Provider 与外部连接器广场真实闭环

- **M-06（已实测）**：在干净、run-owned 的 App + IAM + BFF + Platform + Admin 组合中（未启动 Mori），浏览器以同一 Product 会话进入 `/manage/hub`，执行 Provider **创建 → 编辑 → 停用 → 启用 → 移除**。每个操作都取得实际 Platform `McpProviderAdminService` 回执并刷新当前列表；移除后 Admin 列表为空。
- **M-07（联动已实测）**：同一 Admin 创建并编辑 Provider 后，直接导航外部 `/app/plugins`，广场出现真实的更新后卡片与简介；从 Admin 移除该 Provider 后，重新读取广场，卡片随 owner 数据消失。广场与管理台因此不是两套静态数据或两套默认页面。
- **修复**：Product Admin adapter 现在透传 Admin 网关给出的 `x-kokoro-request-id`，而不是生成第二个 request id。此前这会使 Admin 对下游响应的关联校验必然失败，浏览器仅得到 `admin_upstream_invalid`；相关 App 契约回归已覆盖透传行为。
- **边界**：本次隔离启动器使用 `--platform-mcp-only`，其 Skills provider service 未装载；该 run 中 Skills 请求明确返回 owner `503 skill_dependency_unavailable`，未将其记作 Skills CRUD 成功。MCP Provider 与外部连接器广场链路已在上述组合中逐步回读并清理临时记录。
