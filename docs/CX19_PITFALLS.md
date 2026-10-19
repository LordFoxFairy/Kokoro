# CX-19 已识别踩坑与固定约束

本记录只保留会造成错误交付判断或复发的事实；每一条都对应闭环表中的实际复核项。

| 编号 | 踩坑 | 造成的问题 | 固定约束 |
| --- | --- | --- | --- |
| P-01 | 用通用设备断点或截图物理像素推断设置模式 | 将 `48rem` 以上直接切到双栏，并把 Retina 截图中的 760 物理像素误当作 760 CSS 像素，导致紧凑弹窗放大到近全屏 | 设置模式按实测容器空间决定：当前以 `<96rem` 为紧凑横栏、`≥96rem` 为双栏；紧凑弹窗以浏览器计算值 `380×580 CSS px` 为准，变更后必须分别实测两端 |
| P-02 | 用固定位置强制滚动已选标签 | 深链打开“连接器/技能”时，“账户”被裁成尾字，右侧标签压边 | 按参考视口读取已选项的真实 `scrollLeft` 并只在该轨内定位；不得硬锚到零或把更多当作替代轨 |
| P-03 | 空目录时禁用搜索和范围筛选 | 用户看见灰色不可操作控件，和 Manus 的可探索状态不一致 | 空态保留搜索、筛选、探索和添加入口；空数据只改变结果区 |
| P-04 | 以通用加载弹窗或居中 spinner 衔接异步读取 | 页面跳动、内容区坍缩，并产生“正在加载”的阻断感 | 保留已确认投影；首次读取用与最终列表同几何的骨架，详情只在数据就绪后打开 |
| P-05 | 让旧单项 MCP 表单承担 JSON 导入 | 多服务器 JSON 会被浏览器拆开、丢失 STDIO/SSE 语义或伪装成 HTTP | JSON 导入必须消费 Platform 原子导入契约；发布前不启用旧兼容循环 |
| P-06 | 运行时仍接旧 IAM/Platform 数据面 | Provider 目录为空、管理员入口拒绝、OAuth 无法联动 | 建立隔离本地运行时：现行 schema、开发管理员和标准本地 OAuth/MCP Provider 必须属于同一 owner 数据面 |
| P-07 | 用局部页面可打开或静态检查代替闭环 | 菜单看似存在，但 CRUD、失败恢复、回调或窄屏仍缺失 | 每项按“列表→创建→详情→编辑→状态变化→删除/撤销→错误恢复”实操；同时留 Manus/实现/结果证据 |
| P-08 | 旧样式和旧模块被默认保留 | 历史布局持续影响新页面，导致补丁叠补丁 | 发现与目标结构冲突的旧入口直接替换并删除依赖；按功能组件边界重构，不保留双实现 |
| P-09 | 将设置“更多”菜单 portal 到 Dialog 外却未恢复事件命中 | 菜单能显示但 `body { pointer-events: none }` 使条目完全点不动，造成视觉存在、交互失效 | 所有 Dialog 自有 portal 子层显式声明 `pointer-events: auto`；每次必须实际点进至少一个隐藏分类，而不是只检查菜单截图 |
| P-10 | 在 Settings 首次挂载后才启动连接器读取 | 首次点开连接器会先出现空白/骨架，即使用户刚刚在首页完成登录 | AppFrame 在已准入会话建立后预热 MCP 与 Custom API 投影；Settings 只复用同一 client/subject 缓存。验收必须从首页等待后实际点击进入，而不是直接深链刷新 |
| P-11 | 用精确的“更多菜单成员”断言固化旧视觉 | 过期的定向 UI case 要求“技能”仍在更多菜单，反过来把已按 Manus 修正的主分类布局判为失败 | 删除这类对内部位置和旧标签归属的断言；只保留用户旅程和真实交互风险测试，视觉归档与实际浏览器对照才是布局验收依据 |
| P-12 | 将“更多”当作横栏的替代品 | 为避免拥挤而隐藏 Mail、电脑等后续标签；本地滚动轨宽度只有 `416px`，参考轨则保留完整分类并为 `963px` | 横栏始终保留完整分类，更多只作快捷入口；选中“连接器”时读取真实 `scrollLeft` 对照，而非凭静态可见标签判断 |
| P-13 | 本地组合只注入 Skills 所需 IAM 资料 | Platform 现在对 projection、MCP、Custom API、Admin 采用分 surface 的本地 service credential；缺任一 owner-only 文件会使应用表现为目录为空或管理入口拒绝 | 隔离运行时必须为每个 BFF surface 创建独立 0600 凭据，并同时传入 MCP/Custom API 的独立 keyring；凭据只在本 run 临时目录存在，关闭时销毁 |
| P-14 | Custom API mutation 后只刷新 MCP connector 投影 | owner 已成功保存的备注/版本仍由 Settings 内存列表展示旧数据；立即再次打开详情会误判为保存失败 | Custom API owner command 的响应先替换同一 admitted subject 的 profile cache，再后台 re-read；删除同样先从 cache 移除。实际浏览器必须验证“编辑→无需关闭设置再次打开即可读到新值” |
| P-15 | 把未预热或失败的 Settings 分区当成已无加载问题 | 连接器已无阻断加载后，团队分区仍先出现加载并在当前 owner read 失败时落入错误态，造成“只修一个 tab”的错觉 | 每个 Settings tab 必须分别执行首次进入、回访与错误恢复；团队读取需由其 owner 链路单独修复，当前只替换成同布局 skeleton，未把错误隐藏为成功 |
| P-16 | 让紧凑横栏在“更多”按钮下继续占满滚动视口 | 末端标签会绘制到悬浮的菜单图标下，视觉上像“集成”等文字互相重叠 | “更多”必须拥有独立的 `32px` 列；横向滚动 `TabsList` 的可视宽度在此列之前结束。验收时分别查看默认选中、末端横向滚动和打开菜单三种状态 |
| P-17 | 把旧 URL 说明字段和未收拢的 OAuth 字段直接堆进基础弹窗 | URL 基础态底部按钮被推出视口；进阶态出现大块空白且与 Manus 的单一进阶框不一致 | 基础态仅保留名称、URL、进阶开关、提示和操作；OAuth 输入收在开关下方连续边框内。每次复核基础与进阶两态的弹窗尺寸、底部操作和键盘可达性 |
| P-18 | 外部 Skills 仍使用退役的 `/self/skills/catalog` 通用 Hub 路径，且与 Settings 各自冷读 | Settings 使用 owner-backed读模型时可用，但外部 `/app/skills` 走旧路径直接收到 404；即使修正路由，独立 adapter 也会让 Settings 再闪一次骨架 | Settings、外部页和 AppFrame 预热必须复用同一个 owner-backed Skills client；不得因入口不同各自选择旧/新传输。首页准入后先预热，打开 Settings 直接复用已确认投影；首读保留工具栏和最终卡片几何，不出现独立居中加载态 |
| P-19 | 用旧的定向 UI case 固化已退役的 `/self/skills/catalog` 读取 | 真实页面已切换到 owner 的 `ListHubSkills` / `ListSkills`，测试却把旧路径当作唯一正确行为，导致“测试通过”与实际页面错误彼此冲突 | 删除旧路径断言；保留对两个 typed owner 读取、单次读取与用户可见目录结果的行为验证。测试不得要求恢复退役 adapter 或历史布局。 |
| P-20 | 在私有 MCP 已注册、远端 Prepare 失败时只保留结果弹窗而不刷新底层投影 | owner 已创建 pending server/connector，但用户取消重试层后列表仍来自旧缓存，看起来像注册丢失；实际又会留下难以发现的待连接记录 | 自定义 MCP、URL 和 JSON 入口在收到注册 receipt 后立即请求同一 admitted subject 的列表 revalidation；弹窗继续保留失败/重试/OAuth 状态，只有 ready 才关闭。 |

| P-21 | 删除 owner 已确认后仍让旧 connector projection 卡片留在列表，等待慢速后台回读 | 用户刚确认删除却仍短暂看到同一行，误以为删除失败；这不是“无感”，也会和弹窗关闭形成不一致 | 仅在 `deletePrivateMcpServer` / `removeMcpConnector` 成功返回后立即把对应连接器从当前渲染投影排除，同时发起 owner revalidation；失败不隐藏，不能用先删 UI 的乐观假象替代 owner 回执。 |
| P-22 | 只依赖组件级 WeakMap 预热 | 同一页切换虽快，但硬重载会丢内存缓存并再次露出骨架；这与 Manus 在既有会话中的稳定卡片感不一致 | 对不含 endpoint、header、credential 的 MCP 列表/目录首屏，按已准入 subject 以严格 schema 校验写入 tab-scoped sessionStorage；恢复后立刻后台 owner revalidate，身份变化、请求失败或私密配置永不复用该缓存。 |
| P-23 | Custom API 详情直接套用 Custom MCP 的固定高度 detail 样式 | 轻量 profile 详情被强制撑到 MCP 详情高度，字段之后出现大片空白；同组件名但不同 DOM 结构还让标题、正文、操作栏丢失专属排版 | Custom API 与 Custom MCP 只共享 dialog primitive，不共享内容布局。每种 aggregate 必须有显式 detail/editor layout class，并在真实详情、编辑、确认删除三态逐一实拍。 |
| P-24 | 同一 owner projection 在 Settings 与外部页使用不同 identity 格式 | Settings 已预热的 subject 投影无法被 `/app/plugins` 复用，页面会再次画骨架，看似“加载无感”只在一个入口生效 | 跨入口读取同一 subject-visible resource 时缓存 identity 必须一致；session generation 只在确有独立 owner 事实时参与失效，不能作为展示缓存命名空间后缀。 |
| P-25 | 将 Platform 的所有 `AlreadyExists` 一律映射成幂等键冲突 | 已登记 endpoint 的重复创建在页面上被错误显示为“连接异常”或“幂等冲突”，用户无法知道应编辑已有连接器 | BFF 只对 owner 明确的 `private MCP URL already registered` 映射 `mcp_personal_server_url_conflict`；其他 `AlreadyExists` 保持幂等语义。App schema 允许该码，Custom MCP 与 URL MCP 都必须用可理解的恢复文案。 |
| P-26 | 会话判定前用整页 RuntimeLoading 覆盖深链页面 | `/app/plugins`、`/app/skills` 冷打开时先露出居中“正在加载工作区”，再跳到最终布局，和稳定工作台感相冲突 | 判定期只渲染不含私有数据 client 的 booting AppFrame，保留产品外壳和禁用输入；认证失败仍走登录/显式不可用状态，不能借此 fail-open。 |
| P-27 | App/BFF 允许带 query 的 MCP endpoint，而 Platform canonical identity 禁止 query | 表单允许提交，直到 owner 端才失败并显示泛化连接错误；失败也无法建立可重试的注册状态 | URL 校验在 App UI、App hub schema、BFF body parser 与 Platform canonical identity 同步要求无 query/hash/userinfo。浏览器对 query URL 保持保存禁用，不发起 mutation。 |

| P-28 | 把“菜单能打开”当作四种创建功能已闭环 | 四个按钮视觉存在，但表单可能复用错误组件、丢字段、底栏裁切或出现通用加载层 | 每种创建类型必须分别执行菜单点击、表单打开、关闭、字段/底栏可见性和对应真实 command 旅程；只共用 dialog primitive，不共用不同 aggregate 的内容布局。 |
| P-29 | 将空目录用演示卡或占位成功态包装 | 看似 Skills/MCP 已有数据，但安装、启停、详情和删除没有对应 owner 事实，后续联动必然失真 | 空目录忠实显示 owner 空态，同时保留所有可操作入口；需要真实 CRUD 时使用隔离、可清理的 owner 数据，不能用前端 fixture 伪造闭环。 |

| P-30 | 隔离 IAM runtime 把通用 user client 当成 Product-Web client | 即使管理员事实已经写入且审计成功，`session-authorizations/verify` 仍会返回 `platform_admin=false`，导致 Admin 看似“权限没有生效” | 有 `webOidcClient` 时，测试 runtime 的 `IAM_PRODUCT_WEB_CLIENT_ID` 必须指向该 Product-Web client；开发管理员 ready 前必须用该 client 的真实 PKCE token 回读准入，不能用通用 user grant 推断结果。 |
| P-31 | Product client 已受信任时仍强制经过 consent 页面 | 本地 Product-Web PKCE fixture 在已有受信任策略时直接回调，旧 helper 把这条正常路径误判为失败 | 隔离 OAuth 验收同时支持“显式 consent → callback”和“已受信任 → 直接 callback”，两条均须校验精确 callback URI、PKCE code exchange 与最终 owner 准入。 |
| P-32 | 用 JavaScript 的 viewport 断点判断 CSS 已切换的紧凑导航模式 | 桌面应用的缩放/DPR 会让 JS 与 CSS 的断点结果不同：页面已是横向滚动栏，但定位逻辑仍按桌面纵向 rail 运行，当前选中“技能”会留在视口之外 | 导航定位以实际 `TabsList` 的 computed `overflow-x` 为模式事实，并用同一滚动容器的 rect 计算位置；验证必须覆盖硬重载后的账户、连接器、技能和更多四种选中状态，不能只复核其中一个。 |

| P-33 | 把“移除 loading 文案/Spinner”做成整页空白 | 认证判定虽不再出现文字加载态，但首帧没有 rail/header 几何，外部 Skills/MCP 仍像闪退后重开 | server-admitted 首帧须保留静态、无交互的工作台几何（窄 rail、顶部栏、Composer）；不启动 Runtime、不加 Spinner/脉冲，稳定 owner 页面到达后再替换。 |

| P-34 | 把 Platform 已实现的 JSON 批量能力提前标成浏览器闭环 | owner 的原子 RPC 尚未进入 BFF pinned artifact 时，App 只能走旧单项命令；提前放开多项 UI 会把第二项变成无契约写入或静默丢失 | JSON UI 只能在 Platform 发布不可变 artifact、BFF 重新生成 client、同源路由返回逐项 receipt 后切换到批量模式；owner PostgreSQL 事务证据与浏览器 CRUD 证据分别记录。 |

### P-35：外部页不能以 Settings 的标题压缩策略作为默认布局
- **现象**：永久侧栏会显著减少主内容可用宽度；若标题格允许压缩而操作条保持固有宽度，CJK 标题会退化为逐字竖排，右侧按钮还会越界。
- **处理**：将外部 MCP 标题保留为 `max-content` + `white-space: nowrap`；在可用空间不足的断点改为“标题行 + 工具栏行”。Settings 的紧凑单行规则必须通过 `data-settings-layout` 单独限定。
- **验收**：至少在默认侧栏宽度和 `1440×900` 两个视口真实重载外部页；逐项确认标题、搜索、管理、创建、分类和空态均未裁切。

### P-36：自定义 header 名称的 UI 校验必须与 BFF 入参完全一致
- **现象**：App 曾允许 `X-Kokoro-*` 等 BFF 保留 header 名称，提交后才收到泛化的 `invalid_mcp_personal_request`，用户既不清楚字段错误也无法在写入前修正。
- **处理**：创建表单、私有 MCP 详情编辑与 hub schema 共用一份 header-name policy；保存前拦截所有 BFF 禁止的固定名与前缀，提示具体可恢复原因。secret 值仍不读回。
- **验收**：实际浏览器输入 `X-Kokoro-E2E` 时显示错误、保存禁用且无 POST；替换为 `X-Client-Key` 后完成创建、读回、编辑、prepare 发现 tool 的真实 owner 链路。

### P-37：同一连接器域不等于同一入口角色
- **现象**：将外部 `/app/plugins` 当作 Settings/连接器的内联副本，会让“管理连接器”替换广场内容，丢失 Manus 的“外部广场 → 设置管理弹层”层级；目录为空时又会误把真实 Provider 空态当作同步失败。
- **处理**：外部入口默认是 Provider 广场；“管理连接器”通过 AppFrame 打开共享 Settings/连接器。二者共享 admitted subject、owner read contract 和缓存 identity，但不共享默认视图；广场只显示 Provider 目录，设置只显示用户已添加列表。
- **验收**：实际访问外部广场，点击“管理连接器”必须出现 Settings/连接器并显示同一用户的已添加项；关闭后回到广场。Provider 空态和已添加列表都必须来自各自 owner 数据，不互相伪造或替换。

### P-38：Hub 同源代理必须随 owner 新命令同步闭环
- **现象**：Platform/BFF 已实现 JSON 批量导入，但 App 的路径表、输入校验、201 成功码与回执投影遗漏该命令。浏览器只能收到本地 `400`，错误被误显示为“JSON 格式无效”。
- **处理**：每个新 owner mutation 在 App 代理、BFF 路由、client 成功状态、safe response projection 和完成后的列表失效上逐层登记；批量 receipt 必须校验每项名称、URL、server/connector 关联和 pending 状态，不能把 owner 回执当作任意 JSON 透传。
- **验收**：干净隔离组合中实际执行单项 `导入→详情→prepare→删除` 和双项原子导入；同时确认原始配置、header secret 不会出现在页面或回执中。

### P-39：OAuth 新窗口的 URL 约束和实际回调路由必须端到端一致
- **现象**：Platform 已在非生产环境安全地产生本机回环授权 URL，BFF/App schema 也接受它，但弹窗 hook 仍硬编码 HTTPS，导致请求 200 后浏览器在真正导航前拒绝。隔离启动器同时把 redirect URI 指向一个不存在的 `/api` 路由，使已授权的新窗口停在 404。
- **处理**：本机回环 HTTP 只在非生产环境、无 userinfo 的 `localhost`/`127.0.0.1`/`[::1]` 上获准；App hook、传输 projection 和 Platform discovery 使用同一规则。隔离运行时将 redirect URI 指向实际渲染并完成 owner callback 的 `/mcp/oauth/callback` 页面；生产仍严格要求 HTTPS。
- **验收**：真实新窗口必须完成授权并自动关闭，Settings 列表出现连接成功图标；随后从详情执行断开连接，确认同源 DELETE 收到 owner 200 且列表立即无该项。仅看到 begin authorization 的 200 不算闭环。

### P-40：Admin 适配器路径必须以 BFF `/v1/admin/` 截断后的资源路径为准
- **现象**：Admin 控制台会将 `/api/v1/admin/mcp/providers` 转发为产品同源的 `/api/admin/mcp/providers`。产品适配器若仍将首段误限制为 `admin`，会在产品会话尚未被读取前返回 404；UI 看起来像空目录或无响应，实际没有抵达 BFF/Platform。
- **处理**：产品适配器仅允许 owner 资源首段（当前为 `mcp`、`skills`），并以同一已准入 Product Session 附加 BFF 内部头。禁止将浏览器 Admin 直接变成第二个 OAuth relying party。
- **验收**：适配器的真实契约回归验证 `POST /api/admin/mcp/providers` 到 `/v1/admin/mcp/providers` 的方法、幂等键、Product bearer 和 `no-store`/request-id 回传；非法 `admin/...` 路径及缺会话必须在到达 BFF 前拒绝。

### P-41：Admin 不能保留第二套产品登录与每请求预检
- **现象**：Admin 若保留自己的 OIDC/NextAuth、cookie/Redis 或在每个 Provider 请求前额外请求 `/api/admin-access`，同一用户会拥有两种会话事实；前者会把已登录用户带回授权页，后者会多一次 App+BFF 往返，并把下游精确的 `403` 折叠成不透明失败。
- **处理**：Admin 只消费 Product 同源会话。入口页面与 `/manage/api/v1/me` 可以读取一次准入；Provider CRUD 直接经 Product adapter → BFF → Platform，BFF 仍是授权与审计唯一 owner。隔离启动器只在 `--platform-admin` 时启动 Admin，禁止把管理员能力接到日常运行时。
- **验收**：隔离管理员会话中验证 `/manage/hub` 不出现第二次 OIDC；列表和每次 create/edit/enable/disable/delete 各只有一个业务 BFF 请求，普通用户仍由 BFF 得到准确的拒绝结果。

### P-42：设置模式切换必须按真实可容纳的卡片 envelope，而不是宽泛的桌面断点
- **现象**：把紧凑模式的媒体查询设到 `95.99rem`，会在 `811×764` 这类 Manus 仍显示 `720px` desktop card 和 `221px` rail 的视口过早收成 `380px` 横栏。用户缩小窗口时由此看到导航形态突变、侧栏消失和标签挤压。
- **处理**：以当前参考的实际 envelope 决定模式：能容纳 `720px` card 与外侧 inset 时保持 desktop rail；仅在 `<48rem` 的窄视口进入 compact sheet。最窄横栏不增加 tab 内边距，激活 tab 继续由真实 scroll viewport 对齐。
- **验收**：同一视口同时读取 Manus/Kokoro 的 dialog、rail、tablist 和 active row 几何；再在窄视口验证当前 tab 完整可见、更多按钮不覆盖横向轨、没有半个 CJK 标签。


### P-43：横向 rail 向右揭示选中项时不能沿用“向左取整”规则
- **现象**：在 360px 窄视口中，选中“连接器”位于滚动轨右边界外。旧算法把所需 `scrollLeft` 向前取整到前一个标签起点，得到 0；结果只露出“连”字，菜单按钮与半个标签视觉冲突。
- **处理**：向左揭示仍向前一个完整标签边界对齐；向右揭示改为向后一个标签边界对齐，使当前项完整进入轨道，同时不让轨道起点露出半个 CJK 字。
- **验收**：在 `360×740`，依次选中“连接器”和“技能”，确认 active item 完整可见；打开“更多”后，菜单十项均可见且不覆盖 active label。

### P-44：Admin 网关与产品适配器必须使用同一请求关联 ID
- **现象**：Admin 网关带着 `x-kokoro-request-id` 转发命令并校验回包；Product adapter 若忽略该头、每次新建 UUID，下游业务命令即使已正确执行，Admin 也会因关联不一致把响应判为 `admin_upstream_invalid`。这会把真实写入伪装成客户端失败，重试还可能制造冲突。
- **处理**：产品适配器从入站请求读取有效关联 ID 并原样转发到 BFF；仅在没有可信入站 ID 的独立产品请求中生成新值。保留 `no-store`、幂等键和安全响应投影。
- **验收**：真实 Admin 浏览器分别完成 Provider 创建、编辑、停用、启用和移除，并在每一步确认 Admin 列表重读；随后创建一条临时 Provider，验证外部 `/app/plugins` 出现同一 owner 卡片，移除后消失。
