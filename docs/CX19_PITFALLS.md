## 2026-10-18 真实 Next HTTP 回归的两类运行隔离故障

- **共享依赖目录不是独立副本**：复制workspace源码但把整个node_modules软链回正常目录，再从副本执行包管理脚本，可能自动把正常workspace链接改指向嵌套副本；Next临时夹具随后导入重复路径而500。验证副本应独占workspace链接目录，依赖包可复用只读目标；直接执行仓内原脚本入口，不借候选工作区让包管理器重配正常依赖。核对正常链接、源码/lockfile SHA及自有子进程终止，不只看副本源码没变。
- **2GiB build预算不等于完整HTTP套件预算**：Next16.2.6的start-server在used heap超过上限80%时主动exit77，CLI重启worker；长套件会把在途认证连接打断，看似登录恢复超时/连接拒绝。原87例、1worker和同源码的2GiB运行捕获两次memory warning/exit77，56PASS/31FAIL；仅改4GiB后87PASS、零77。没有修改产品认证、断言、timeout或禁用Next阈值。当前48GiB宿主可为本地HTTP验收显式预留4GiB/worker，并限制并行总预算；构建仍可单worker/2GiB，不对所有环境硬编码同一容量。

进程诊断只记role/PID/退出码/heap/RSS，不记录请求凭据或正文。原失败与A/B收据在Root ignored var/dev/app-rp-process-20261018；单例通过不代替完整套件。资源不足时先按现有预算拆开执行或明确失败，不删测试、不重试成绿后隐去原因。

# CX-19 已识别踩坑与固定约束

本记录只保留会造成错误交付判断或复发的事实；每一条都对应闭环表中的实际复核项。

| 编号 | 踩坑 | 造成的问题 | 固定约束 |
| --- | --- | --- | --- |
| P-01 | 用通用设备断点或截图物理像素推断设置模式 | 将 `48rem` 以上直接切到双栏，并把 Retina 截图中的物理像素误当作 CSS 像素，导致紧凑弹窗放大到近全屏或被压成小窗 | 设置模式按实测容器空间决定：当前以 `<96rem` 为紧凑横栏、`≥96rem` 为双栏；Skills 的紧凑 Settings sheet 以浏览器计算值 `380×580 CSS px` 为准，变更后必须分别实测两端 |
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

### P-45：紧凑 Settings 横栏必须以完整标签为最小布局单元
- **现象**：compact sheet 曾同时渲染七个主标签与独立更多列。窄视口下第七项“技能”只剩一个“技”字贴在菜单按钮之前，虽然路由可达，视觉和点击边界都已失效。
- **处理**：在 `<48rem` 的紧凑 sheet 只渲染六个完整主标签；“技能”与其余溢出项只出现在更多菜单。desktop rail 和足够宽的横向轨不使用这条收缩规则。
- **验收**：以 `640×900` 实际打开连接器、展开更多、进入技能；确认横栏末端无残字，更多内存在“技能”，进入后页面显示已添加技能与探索入口。

### P-46：外部 Skills/MCP 首帧不能保留 rail 的文字型 loading 行
- **现象**：外部 `/app/skills` 的内容区已用稳定骨架过渡，但左 rail 的专案与会话区域仍直接绘制“正在加载专案…”和“正在加载会话…”。页面会同时呈现两种加载语言，破坏无感切换。
- **处理**：将 rail 的两处 owner-read 首态收敛为同一个 typed `WorkspaceRailLoadingPlaceholder`：保留最终行高与无文本骨架；仅以 `role=status` / `aria-label` 向辅助技术表达待读取状态。
- **验收**：实际硬重载 `/app/skills`；首帧不出现可见“正在加载”文案，稳定后分别进入真实专案/会话空态与 Skills owner 空态。错误和可重试状态保持显式文案，不被骨架吞没。

### P-47：不让 React/UI 测试替 Manus 对齐作决定
- **现象**：将组件树、按钮文案、fixture 卡片和局部点击顺序写进 Skills/MCP UI 测试后，测试全绿仍会保留错误的布局与交互；为了维持绿灯而微调实现，会反过来阻碍依据最新 Manus 参考重构。
- **处理**：本轮已移除五个相关 suite（`kokoro-skills-surface`、`skills-panel`、`mcp-panel`、`settings-modal`、`kokoro-plugins-surface`），Skills/MCP 不再运行或汇报这类 UI 用例，也不以 lint、typecheck、diff 的通过状态裁决视觉完成。保留 owner/service/contract 层的权限、输入、幂等、CRUD、OAuth 与撤销验证，但它们不得规定 React DOM、CSS、文案、示例数据或空间几何。
- **验收**：按归档的 Manus URL、视口、语言、状态和动作逐页执行本地真实浏览器主路径；先确认布局、滚动、菜单、弹窗和真实数据变化，再记录截图对照。没有 owner 数据时忠实展示空态，不用 fixture 替代。

### P-49：探索目录不得在首次打开时预取整个 cursor 链
- **现象**：Settings Explore 曾在首次读取中串行请求最多 100 页目录，以“没有分页按钮”为由掩盖分页。目录稍大时，首屏会长期停留在骨架、重复请求同一 owner，还会让搜索或切换范围延迟生效。
- **处理**：首屏只读取 owner 返回的第一页；同一连续列表底部进入可视区后，才按原始 opaque cursor 顺序追加下一页。请求中的 cursor 必须前进，重复或不前进的 owner 回包转为可恢复的目录错误，不以客户端遍历上限伪造完整结果。
- **验收**：真实目录仅在用户滚至当前结果末端后读取下一页；搜索、范围切换和关闭后重开不混入上一份 cursor 链；空态和错误态继续忠实使用 owner 返回。

### P-50：本地 Skills 导入必须先核对活跃会话租户与 catalog 机器凭据索引
- **现象**：浏览器会话和 BFF 的 tenant 配置一致，但 BFF 的 tenant-indexed catalog credential 文件只含另一租户的条目。导入 Begin 在访问 Platform 前即失败；App 若把未登记的 owner 错误折叠为 `*_response_invalid`，界面会误导为响应格式问题。
- **处理**：导入链必须将 catalog credential 的缺项、格式错误、轮换和 token 获取失败统一投影为可重试的 owner 依赖不可用；保留已选文件，避免要求用户再次上传。运行组合启用前核对“活跃会话 tenant ↔ catalog credential entry ↔ IAM tenant-machine client”的一一对应；凭据通过 IAM 的正式 provision/rotate 流程生成，不复制或改写别的 tenant 条目。
- **验收**：真实浏览器选择本地 `.zip` 后，正确租户配置必须完成 Begin→对象上传→扫描→Finalize→个人列表刷新；凭据缺项时显示清晰的服务初始化状态，不出现 `local_skill_import_response_invalid`，也不要求用户重新选择文件。

### P-51：紧凑 Skills 工具栏的可见按钮必须拥有自己的命中区域
- **现象**：`380px` Settings sheet 内保留了 `200px` 搜索框和 `116px` 创建按钮，三列的总宽超过内容轨。搜索框覆盖“探索技能”按钮，按钮看得到却只能通过“添加”菜单的同名入口进入目录。
- **处理**：紧凑模式使用与 Manus 同一条 `348px` 内容轨：搜索 `172px`、探索 `72px`、添加 `84px`，并把工具栏上边距收为 `8px`；宽度由 grid track 约束，不再让子元素以固定宽度溢出。
- **验收**：同一 `448×764` CSS 视口下，Manus 与本地的 dialog、搜索、探索、添加均分别为 `380×580`、`172×32`、`72×32`、`84×32` 且 `y=317`；直接点击“探索技能”进入目录，返回后控件仍可点击。

### P-52：外部 Skills 广场必须使用当前 Manus 的分类按钮条
- **现象**：本地外部 `/app/skills` 曾在桌面宽度把分类筛选收成单个“全部”下拉；当前 Manus 实页在同一宽画布下仍展示“全部、编程、数据、自动化、商业、设计、媒体、内容、应用”横向分类条，导致页面结构直接不一致。
- **处理**：外部广场统一使用可横向滚动的九项分类按钮条，当前项有选中底色；所有按钮共享同一个 `category` 状态和同一份目录筛选函数，不分叉查询或复制控制逻辑。该规则仅作用于外部 Skills，不回流到 Settings 的已添加范围筛选。
- **排版**：标题直接采用 Manus 的 `18px / 500 / 24px / normal tracking`；不能沿用本地 `650` 加粗及负字距来“补”视觉重量。
- **验收**：在当前宽屏 Manus 与本地分别检查标题、搜索/我的技能/创建行及九项分类条；切换任一分类后仅该项高亮，窄画布超出部分可横向滚动，状态和结果不因布局变化而重置。

### P-53：紧凑 Skills 详情不能把桌面大标题直接放大到手机
- **现象**：详情弹窗的卡片、操作和正文在窄视口虽然可显示，但本地将标题放大为 `28px/650`，操作按钮也使用 semibold；当前 Manus 的实际详情是 `95vw×600px` 容器、`20px/600/26px` 标题与 `14px/500` 的 `32px` 操作按钮。
- **处理**：紧凑详情保留固定 `222px` 头部和 `24px` 内容边界，标题、操作、摘要行高和示例卡片按当前 Manus 的直接测量收敛；封面图在紧凑详情隐藏，不改变桌面详情的右侧封面布局。
- **验收**：有真实目录 Skill 后，在 `448×764` 依次打开卡片、详情、文件阅读；确认详情容器、标题、添加/查看详情、正文及示例卡片与 Manus 同视口对照，随后验证返回卡片和焦点恢复。
## P-54：技能文件阅读器不能在窄屏退化成满屏页

**现象**：详情预览已是居中 `95vw` 弹窗，但文件阅读器在窄屏被单独设为近满屏高度，导致标题、工具图标和正文的视觉层级与同一条 Manus 详情链路断裂。

**规则**：阅读器沿用详情弹窗的容器策略：`95vw × min(600px, 90dvh)`；标题栏保持 `60px`，标题采用 Manus 实测的 `18px / 600 / 24px`。读取真实 owner 的 `SKILL.md` 后，再对文件树和正文滚动逐项复核。

### P-55：紧凑文件阅读器不能永久占用侧栏列

**现象**：桌面文件阅读器的树状导航直接缩成窄侧栏，会挤压 `SKILL.md` 阅读宽度；Manus 在紧凑窗口仅保留一个 `52px` 菜单行内的 `32px` 文件入口，树在用户请求时才覆盖展开。

**规则**：窄屏将目录树收为可访问的菜单按钮，正文维持完整单列阅读宽度；树展开时覆盖正文而不重新分栏。桌面继续保留并列文件树。

### P-56：广场“我的技能”必须进入同一设置面

**现象**：外部 Skills 广场把“我的技能”实现成一套独立的个人列表页，导致设置内 Skills 与广场入口读取、筛选和返回行为分叉；Manus 的该按钮实际是在当前工作区上打开 Settings 并定位到“技能”。

**规则**：从广场进入“我的技能”只调用 AppFrame 的同一 Settings handoff，并把按钮本身作为返回焦点；个人筛选通过同一 handoff 的路由意图传递。不得再维护第二个 personal Skills 页面或第二份读取状态。


### P-57：广场到“我的技能”的个人筛选必须成为可恢复的路由意图

**现象**：仅把广场按钮接到 Settings 的 `skills` tab，会让它和直接打开设置一样默认选中“全部”；刷新后更会丢失来源语义。Manus 的广场入口是 `settings/skills/personal`，进入后选中“个人”。

**规则**：广场入口写入 `#/account/settings/skills/personal`；Settings 从该路由解析一次 `SkillsScopeFilter` 并传入同一个 `SkillsPoolTab`。直接设置入口保持“全部”。不得以独立个人页面、临时全局状态或复制一套查询来承接该差异。

### P-58：工作区侧栏不得把运行时导航清单直接平铺成产品信息架构
- **现象**：Kokoro 直接把 `agent / skills / mcp / scheduled / library` 平铺到侧栏，导致 Skills 与连接器抢占了 Manus 的一级结构；同一页面在 Manus 中应呈现“新建任务、电脑、Agent、资料库、创作、自动化、插件、更多”，其中当前未落地能力必须降级为置灰项。
- **处理**：保留运行时注册表作为唯一的路由事实，但在 `WorkspaceRailNavigation` 的展示层显式分组：已交付的 Agent、资料库、插件直接进入一级；Skills 与排程收进“更多”菜单并在其任一子路由激活时高亮；电脑、创作、自动化使用不可点击的置灰项，不伪装为已完成入口。不要因为进入 Sheet 就额外插入“聊天”一级项：品牌和“新建任务”已覆盖该入口，Manus 的窄侧栏与宽侧栏使用同一主导航序列。账户行使用圆形头像、单行产品账户名与设备/通知槽位，不在 rail footer 再显示“个人工作区”副标题；继续复用既有账户和通知交互。
- **验收**：外部 Skills 路由上“更多”为激活态；展开后可见“技能、已排程”且可进入既有路由；Agent、资料库、插件保持直接点击；电脑、创作、自动化在可访问树中标记为 disabled；`448×764` Sheet 和宽侧栏的主导航均为“新建任务、电脑、Agent、资料库、创作、自动化、插件、更多”，窄轨折叠、展开以及账户菜单焦点恢复不复制新的导航状态。

### P-59：个人技能空态与全范围目录空态不能共用引导
- **现象**：本地曾把「个人」筛选的空状态沿用为通用「还没有可用技能」和长说明，且只在工具栏提供添加入口；实际 Manus 的个人页在无已安装技能时显示「尚无技能」及居中的「创建」菜单。将两种状态合并会让用户误以为必须先上传文件，也会丢失记录和 GitHub 导入入口。
- **处理**：`SkillsPoolTab` 以同一 TypeScript 菜单组件承接工具栏添加与个人空态创建：工具栏菜单可含「探索技能」，个人空态菜单仅含创建、记录、上传、GitHub 导入；全范围目录空态继续保留通用引导。两个入口复用相同真实导入/创建 action，不复制业务逻辑。
- **验收**：在 `#/account/settings/skills/personal` 且真实列表为空时，显示「尚无技能」与居中「创建」；打开菜单后只有四项创建动作。切回全部范围时保留通用空态与工具栏探索入口。

### P-60：Settings 的探索目录必须替换右栏标题，不得嵌套第二个标题栏
- **现象**：本地在“已添加的技能”标题之下又渲染一层“探索技能”标题和返回按钮。视觉上形成双标题、额外分隔线与约一行高度的空白；Manus 将探索目录视为同一 Settings 右栏的子状态，顶层标题直接切换为“探索技能”。
- **处理**：`SettingsPanel` 保有唯一的 `skillsCatalogOpen` 状态与返回焦点 ref；`SettingsPanelHeader` 根据该状态显示“探索技能”和返回已添加列表的按钮。目录组件只渲染搜索、范围和连续列表，不再拥有第二个 header；返回后在下一帧恢复“探索技能”触发按钮焦点。
- **验收**：从设置 > 技能点“探索技能”后，右栏只保留一个“探索技能”标题、一个返回箭头、搜索和范围按钮；点击返回恢复“已添加的技能”，并且焦点回到“探索技能”入口。

### P-61：窄视口工作区侧栏必须覆盖内容，不能参与桌面 flex 挤压
- **现象**：旧的 `useIsMobile` 把 `(pointer: coarse)` 作为窄宽度的额外条件。桌面指针在 `448px` 画布下因此仍采用 desktop rail；打开侧栏会从页面宽度扣除约 `256px`，将 Skills 标题、工具栏和内容压成窄列，且没有 Manus 的背景遮罩。
- **处理**：导航组合只按实际 CSS 画布宽度在 `768px`（含）切换。窄画布统一使用现有 `Sheet` 覆盖层（`min(18rem, 100vw - 2rem)`）和遮罩；宽画布继续使用 in-flow desktop rail。不得再用输入设备类型推翻可用布局宽度。
- **验收**：在本地 `448×764` 打开 `/app/skills`，点击“展开侧栏”后侧栏覆盖主内容、主页面不缩列、遮罩可见；按 Escape 关闭后恢复完整主页面。再回到宽画布确认仍是 desktop rail。

### P-62：紧凑 Settings 的 Skills 空态高度必须服从剩余视口
- **现象**：设置内 Skills 在桌面使用 `25rem` 的空态舞台；将该固定最小高度带入 `448×764` 的 `380×580` 紧凑卡片后，筛选栏下的空态一直延伸到 Dialog 裁切区之外，用户只看得到 puzzle 图标，看不到“还没有可用技能”和引导说明。
- **处理**：仅在紧凑 Settings 下将嵌入式空态最小高度收为 `10.25rem`，保留居中关系与桌面 `25rem` 舞台。个人范围的“尚无技能 / 创建”继续使用同一几何，不建立第二套空态结构。
- **验收**：本地 `448×764` 的 Settings > Skills 在“全部”空态中，图标、标题和引导均位于 Dialog 边界内；切至“个人”后“尚无技能”和“创建”也完整可见，创建菜单仍只有四项个人创建动作。

### P-63：侧栏边界必须只在一种布局组合中生效
- **现象**：`768px` 同时命中紧凑 desktop rail 与窄画布断点，但前者仍采用 in-flow 的 `Sidebar`。点击菜单时主内容被 rail gap 推到右侧；同时自定义 seam 使用比 gap/container 更长的过渡，rail 已到终点时仍残留一条半透明竖线。
- **处理**：将 `768px` 纳入 `Sheet` 覆盖层范围，使主页面始终保持完整宽度、侧栏仅从左侧覆盖到右侧；boot 首帧沿用同一边界，避免加载时闪现 52px rail。桌面 seam 的 `left` 过渡与 Sidebar gap/container 统一为 `200ms linear`，不再保留第二条滞后边界。
- **验收**：本地 `768×764` 点击“展开侧栏”后，`sidebar-gap`、desktop container 与 seam 均不存在，`Sheet` 位于左侧且主内容仍为 `768px` 宽并带遮罩；回到 `854×764` 展开宽 rail 后，gap/container/seam 都在 `300px` 边界对齐。

### P-64：折叠 rail 的内容投影不能早于物理轨道收缩
- **现象**：桌面 rail 点击收起时，Sidebar 的 `300px → 52px` gap/container 会在 `200ms` 内过渡，而内部导航立即换成图标模式。过渡中的宽轨只剩左侧图标，形成整段灰色空白；截图会误读为折叠态仍占用了完整 rail。
- **处理**：物理 Sidebar 状态继续立即切换并驱动宽度；内层 rail 的内容投影仅在收缩过渡结束后切为图标模式。展开则立即恢复完整内容，让它随宽轨从左至右揭示。焦点恢复依赖该投影状态，确保收起后的品牌按钮已挂载再接收焦点。
- **验收**：本地宽屏从展开点击“收起侧栏”时，导航文本与 300px 轨道同步裁切，不出现图标加整段空白；稳定后 gap/container/rail 都为 `52px`，主内容从 `x=52px` 开始。展开后恢复 `300px` 轨道与完整文字导航。

### P-65：Skills 广场的内容列须随 rail 状态调整，而非固定居中
- **现象**：将广场 header/content 固定为 `72rem` 后，展开 rail 时卡片列过宽；折叠到图标 rail 后又因固定居中而从 rail 留出过大的空白。两种状态都与 Manus 的“展开聚焦、折叠铺开”网格不同。
- **处理**：以 Skills surface 的实际内联容器宽度切换列宽：展开 rail 的约 `1130px` 画布维持 `60rem` 聚焦列；仅在图标 rail 释放出的 `75rem+` 画布中扩为最大 `80rem` 的三卡列。该规则只改变外部 Skills 广场，不影响 Settings 内的 Skills 列表。
- **验收**：本地 `1430×764` 下，展开 rail 时标题/筛选与三卡列左边界同为 `x=385px`；折叠后 rail/gap/container 均为 `52px`，Skills 标题和筛选跟随至约 `x=100px`，不再保留 300px 灰色占位或 72rem 居中空白。

### P-66：项目区标题、折叠与创建必须分离为真实动作
- **现象**：Kokoro 仅将“项目”显示为静态分组标题和一个二级创建菜单，缺少 Manus 的标题 disclosure、项目选项与直接创建入口；点击“+”会立即生成带随机后缀的项目，用户没有命名机会。
- **处理**：项目标题成为独立 disclosure，收起时仅隐藏 owner-backed 项目列表而不改变列表、路由或任务区状态；ellipsis 始终展示“项目排序方式 / 新建分区”，当前未交付的能力置灰。`+` 打开 shell-owned TypeScript 创建对话框，先采集项目名称再以同一幂等创建命令提交；文件夹选择显示为禁用能力，不伪造本地路径或成功状态。
- **验收**：展开侧栏中依次验证项目标题的展开/收起、选项菜单的禁用状态、`+` 的创建对话框和空名称禁用创建；命名提交沿用既有 owner 创建命令的幂等、错误与重试投影，待有隔离 owner 项目空间时再保存真实创建证据。收起项目区后任务区紧随标题上移，重新展开时恢复同一 owner 列表。

### P-67：Settings「探索技能」使用单一目录筛选下拉，不能误用已添加页的范围分组
- **现象**：本地探索目录曾在搜索框下方展开九项分类标签；这把外部 Skills 广场的信息架构误搬进 Settings。当前 Manus 的 Settings Explore 工具栏只有搜索框和右侧带筛选图标的「全部」下拉；已添加列表才使用「全部 / 个人 / 官方 / 第三方」范围分组。
- **处理**：Settings Explore 读取同一份 catalog 投影，工具栏固定为搜索与单一目录分类下拉。下拉菜单承载「全部、编程、数据、自动化、商业、设计、媒体、内容、应用」，只改变浏览器内可见结果，不重置 cursor、安装状态或详情身份。已添加列表继续保留其范围筛选，两种语义不混用。
- **验收**：在当前 Manus `settings/skills/explore` 与本地同视口检查标题、搜索、右侧「全部」下拉和列表轴；选择“商业”后菜单关闭、触发器更新为“商业”，搜索与返回“已添加的技能”均保持可用。目录无数据时保持真实空态，不伪造卡片。

### P-73：探索目录查询不能为每次输入重绘整页骨架
- **现象**：目录资源 key 包含搜索词；每个字符都会切换到一个冷 key，使已确认的卡片或空态短暂清空并重绘整组 skeleton，视觉上像页面闪烁。
- **处理**：保留最近一次已确认的 owner catalog 作为过渡投影，并先应用同一份本地文本、范围与分类过滤；新 key 的 owner 响应到达后原子替换。初次读取和真正无缓存错误仍显示相应 skeleton/错误态，不将旧数据写回 owner 或当作当前搜索结果。
- **验收**：在设置 > 探索技能连续输入、删除搜索词：工具栏和已确认内容不闪白；空目录的关键词查询即时显示“没有匹配的技能”；成功响应后列表、分页和添加状态以 owner 回包为准。

### P-68：项目与任务是独立的侧栏 disclosure，不得把任务伪装为静态“聊天”标题
- **现象**：本地仅给项目区提供收起动作，直接会话则以静态“聊天”标题渲染。与 Manus 的「项目 / 任务」两段式侧栏不一致；项目收起后也缺少任务区随之上移的清晰边界。把两组 header 套用同一种可见性也会错过 Manus 的差异：项目承担常驻组织入口，而任务的附加操作更轻。
- **处理**：项目保持 owner-backed 项目列表，并常驻呈现 Manus 的「项目 / chevron / ellipsis / +」组织入口；直接会话外层由 shell 提供独立的「任务」disclosure。二者只切换可见投影，已挂载的列表读、加载/错误状态、路由和 owner 数据均不被销毁或重置。任务的 chevron 及右侧操作仅在 hover 或 focus-within 时显现；任务使用已有「新建任务」命令，未交付的任务选项与筛选以禁用按钮真实标注。图标轨不渲染文字 disclosure，继续只显示既有可达图标入口。
- **验收**：在本地 `/app/skills` 展开侧栏，依次点击「收起任务 / 展开任务」与「收起项目 / 展开项目」：对应列表分别隐藏和恢复，另一分区不受影响；项目 header 始终呈现 disclosure、选项和新建入口，Tab 到任务标题后其操作显现；项目选项菜单仍呈现禁用的「项目排序方式 / 新建分区」，任务的未交付操作为 disabled 而「新建任务」保持可用。

### P-69：外部 Skills 的标题字阶要以实页测量为准
- **现象**：外部广场标题在本地保留了 `20px`，虽然标题行和分类条位置接近，仍比当前 Manus `18px` 标题显得更重、更大。
- **处理**：广场 `h1` 固定为 `18px / 500 / 24px / normal tracking`，不通过放大标题修补 rail 与内容列的视觉间距。
- **验收**：在同一宽画布读取已登录 Manus 和本地 `/app/skills` 的计算样式，标题分别为 `18px`、`500`、`24px`；标题行不引入额外高度或改变搜索/操作行对齐。

### P-70：Skills 详情与阅读器必须共享实测的 800×600 桌面工作台
- **现象**：把附件中更大窗口的缩放图误当成当前网页的 CSS 尺寸，曾将详情和 reader 扩成近视口大面板。当前已登录 Manus 在 `1280×720` 中实测：预览与 reader 都是居中的 `800×600` 容器；reader 左文件树为约 `200px`，而非近视口或 `320px` 侧栏。
- **处理**：桌面详情和 reader 统一为 `min(800px, viewport - 32px) × min(600px, viewport - 32px)`，标题栏保持 `60px`，摘要头保持约 `222px` 并使用右侧小封面。reader 采用 `12.5rem` 文件树；`SKILL.md` 的 YAML frontmatter 独立为可复制代码块，随后才渲染正文。窄屏继续采用 `95vw × min(600px,90dvh)` 规则。
- **验收**：用当前已登录 Manus reader 与本地有 owner package 的 reader 同视口对照：容器、标题栏、返回、分享、下载、关闭、200px 文件树、YAML 块和正文逐项可见且可操作；文件树和正文不互相压缩。

### P-71：Skills 广场卡片必须使用目录书封布局与紧凑信息阶梯
- **现象**：本地卡片保留了全幅 cover、`20px/650` 标题、`15px` 描述和固定可见的 `36px` 添加按钮；当前 Manus 卡片以灰底 `2:1` 封面舞台承接居中的竖向书封，正文使用 `14px/500` 标题、`12px/400` 两行描述、`12px` 标签/使用量，添加按钮仅在 hover 或键盘焦点时显现。
- **处理**：外部 Skills 卡片收敛为 `12px` 圆角、`0.5px` 边框、`250/250/250` 卡底；书封宽 `120px`、距封面顶 `24px`、按 `3:4` 裁切并由封面舞台裁边。正文使用 `12px 16px` 内边距及参考的标题、描述、标签、使用量节奏；已有安装动作保留真实 owner 命令，但按钮默认透明、hover/focus-within 时显现。
- **验收**：在 owner 目录实际返回带 cover 的 Skill 后，与当前 Manus `/app/skills` 同视口比对卡片根尺寸、书封位置、文字字阶、标签、使用量与 hover/focus 添加按钮；卡片、标题、封面和添加动作仍进入同一真实详情/安装链路。

### P-72：连接器广场与已添加连接器共享身份，不共享投影类型
- **现象**：把 Settings 的已添加连接器直接搬到外部广场，会把用户私有的 Custom MCP/Custom API 列表误当成可发布 Provider 目录；反过来，外部广场沿用设置工具栏的搜索又会使标题、搜索和创建动作挤在同一行，偏离 Manus 的广场布局。
- **处理**：外部 `/app/plugins` 始终读取 Platform-owned provider directory，Settings 读取当前用户的 connector projection；两者以同一 admitted identity 及 mutation 后刷新保持同步，但不得互相替代数据。广场标题和右侧管理/创建动作独占顶栏，目录搜索与分类位于下方；Provider 卡使用实际目录数据的两列紧凑行，连接状态只从真实 connector projection 投影。
- **验收**：有 Provider 目录数据时，外部广场显示真实 Provider 的图标、名称、描述和真实连接标识；点击「管理连接器」打开同一设置连接器面，Custom MCP/Custom API 只在已添加列表出现。目录为空时显示真实空态，不用本地连接器或样例 Provider 填充。

- **P74 — 设置工作流交接不能与浏览器 history.back 竞争。** 从 Skills 设置里点“使用 Kokoro 创建技能”或“记录技能”时，普通关闭会对刚推入的 Settings fragment 执行异步 `history.back()`；如果同一事件栈又把地址切到 `/app`，延迟的 traversal 会把用户恢复到 `/app/skills`，看起来像按钮失效。工作流 handoff 必须以 replace 清掉 Settings fragment，再提交目标地址、分配新会话并写入该会话草稿；普通关闭仍保留返回上一历史项的语义。用两条真实路径验证：创建技能和记录技能都落到 `/app`、显示各自预填 prompt 且 Composer 获得焦点。
