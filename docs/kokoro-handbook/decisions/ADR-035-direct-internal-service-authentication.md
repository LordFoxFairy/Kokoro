# ADR-035：内部服务直接认证，不重复 IAM OAuth

- 日期：2026-10-13。
- 状态：用户已决定内部服务不重复走 IAM/OAuth；实施与组合验收待完成。
- 范围：App 所需内部 owner 调用；Mori 与其他 Web 功能开发不在本次范围。
- 依据：当前 BFF/Platform/Agent 源码及用户本次明确要求；这是项目选择，不是通用行业结论。

## 2026-10-23 执行纠偏：Billing 内部机器 OAuth 不续期

用户再次确认内部服务不反复签发／交换短期token。本ADR的直接服务认证决定不变：撤回新增Billing client_credentials缓存／续期实现，不将300秒有效期延长或自动刷新作为最终方案。本片起始基线IAM的Billing verify走JWT＋内省，按IAM先发行直接凭据认证profile、Billing再固定消费替换；原Run／预算业务授权不删除。Agent→Platform仍存的机器OAuth继续沿本ADR已有barrier约束退出，不把Billing一跳完成当全内部切换完成。

人类登录的原生会话、授权码／PKCE／CSRF与内部机器身份是不同边界。App已有Auth.js只验证交易、Product cookie＋Redis持有会话；不因内部认证切换再新增另一套登录机制。登录失败／多标签／注销与候选配对统一在AUTH-1实测，不以协议正确代替用户体验验收。

当前状态与实施范围见有效产品计划和各owner三面文档；本段为决定纠偏，不是正常运行已切换声明。

## 2026-10-23 范围澄清：替换机器认证，不替换在线权限来源

用户明确允许按正确边界重构、删除旧流程，不继续补token续期。此次 Agent→Platform 与 Platform→IAM 只替换机器身份认证：Platform复用既有local service authorizer；IAM原 `verifyExecutionAuthorization`／`DIRECT_USER_CURRENT`、Serializable当前权限判断、proof、BFF绑定和审计保持。服务凭据和tenant/user/Run上下文分开，不伪装 `credential_id` 为 OAuth `client_id`，相关机器身份字段正式发行消费者契约后一起切换。

下文barrier/claim是**替代在线权限判断来源**时的后继设计，不作为本次保留在线判断、删除机器换票的前置；本片不新增授权状态机、权限中心或共享认证SDK。此前将两项合并为前置的实施判断已纠正。现有“撤权后下次在线判断拒绝”必须保留；不冒称已解决所有在途副作用与撤权的全局原子排序，也不删除后继更强撤权保证的记录。

Billing→IAM 接收端已发行 `2f881d0`／SDK0.17，Billing `c158270`固定消费。该跳实际compiled Client→IAM/PG/Redis观察零OAuth请求；它不表示Agent的两跳旧OAuth已经删除或正常环境已整体切换。

## App 读取优先切片（2026-10-13）

按用户后续优先修复 App 503/404 与 v1 的要求，先独立切换 Platform `projection` surface 及 BFF 对应 HTTP/Connect 读取；同一 surface 只接受直接服务凭据，不保留 OAuth fallback。Catalog 写入、Skills/MCP 管理和 Agent execution 后继尚未切换，不把读取片称为全内部认证完成。

Tenant 使用 IAM 已有的原样 opaque 标识（受长度和字符边界约束），不是 UUID；不能为匹配凭据验证器更换现有租户。每次认证仍绑定固定 tenant，拒绝空白/控制字符和 caller/surface 越界。机器配置与真实运行证据仅保存在本地私有/ignored 记录。

下面“当前事实”描述本 ADR 建立时的基线；源码提交、正常运行与浏览器验收以本轮任务记录区分。

## AUTH-P3 范围补充（2026-10-16）

沿已存在的 Custom API 专属控制面与 `ProductCustomApiService`，BFF 固定 caller/surface 配对补齐 `custom_api_personal`，与 `catalog|projection|skills_admin|mcp_personal|mcp_admin` 一并构成六种普通 BFF 用途。不是任意 caller/surface 扩展，也不授予 Custom API 执行权限。每个 BFF credential 只允许一个用途、固定 tenant，使用独立 secret/entry；新机器 profile 正式发行并由 BFF 固定消费后一次收敛余下 catalog/skills_admin。删除旧 OAuth source 与专用旧配置名，改用明确 direct service-credential 配置，不保留别名/旧 JSON/fallback。

本片可按下文普通 BFF 独立验收决定先行；`tenant_execution|global_register` 保持原受控链，Agent/IAM 撤权 barrier 与 Billing 业务授权仍是后继门，不因普通控制面完成而放行执行。下文“当前事实”和五种用途列表是决策建立时的基线，当前六用途以本段补充为准。

## 当前事实

BFF 到 Platform 的 catalog、projection、skills-admin、MCP-personal、MCP-admin 分别获取 IAM
client-credentials token；Platform 对每次请求执行 IAM introspection。Agent 到 Platform 又有 workload
OAuth 和 IAM execution-authorization 请求。System、Storage、Scheduler、Agent HTTP 已有直接服务凭据模式。

Platform HTTP 当前为 5.3.0；新认证语义尚未发行，不把下面的目标当作已运行事实。当前机器凭据与人类登录是不同边界。

## 决定与范围

1. 内部机器身份由接收方直接验证专用服务凭据，不再重复 OAuth token mint、exchange 或 introspection。
2. IAM 保留浏览器登录、会话、用户身份、membership、role、permission 及其权威事实。
3. BFF 从已认证会话建立用户上下文；Agent 从持久 Run 建立执行上下文。浏览器自报的 tenant、actor、subject
   或权限头不是可信来源。服务凭据本身不授予任意用户、租户、资源或钱包操作权。
4. 第三方 MCP 的 OAuth/PKCE、凭据密封和 Connection 生命周期保持；它们不是内部机器 OAuth。
5. Billing reserve、dispatch permit、actual-only settlement 与 unknown/pending 是业务资金授权，保持独立。
   删除内部 OAuth 不允许删除 Agent 当前资金准入拒绝，也不允许制造免费账户、费用或已授权状态。
6. 不建设新的认证中心、万能 credential SDK、共享业务模型或跨 owner SQL。

## 服务凭据与可信身份

采用标准 Bearer 承载服务凭据；用户 access token 与服务凭据不互换。每个接收 owner 独立配置 caller、用途/surface
和 tenant 范围；不使用全局通用 secret。Platform 第一组件使用固定 tenant 的凭据记录，global-register 单独使用
不带 tenant 的 System 凭据，不引入 wildcard tenant 或浏览器传入 tenant 的兜底。

固定 caller/surface 配对：`kokoro-bff` 只允许 `catalog`、`projection`、`skills_admin`、`mcp_personal`、
`mcp_admin`；`kokoro-agent` 只允许 `tenant_execution`；`kokoro-system` 只允许 `global_register`。
非法配对在配置加载时拒绝，不把两个独立枚举解释为任意组合。所需 surface 由服务端路由提供。
若调用上下文另带 expected tenant，只允许与凭据的固定 tenant 相等，绝不覆盖凭据的 tenant。
第一组件只返回机器身份，不返回人类 permission 或 execution allow。

凭据记录只来自受限 secret 文件或部署 secret mount，包含 credential ID、secret、固定 service、授权 surface 和
适用 tenant；不写业务数据库、契约示例实值、日志或异常。部署配置只用占位符。配置值与输入均严格闭集验证；
空值、重复 ID/secret、未知 caller/surface、不合法 tenant、越界用途直接拒绝。秘密按固定长度摘要常量时间比较。

请求取消、配置损坏/缺失、凭据轮换和未知身份明确分类；不回退 IAM 或旧 token。轮换使用显式独立 credential ID，
每次授权重新读取当前完整、有效的凭据文件快照，不缓存 secret、旧快照或允许决策。旧凭据移除后新发起的授权
必须拒绝；配置缺失/损坏、读取失败或取消不得恢复旧快照。已经在读取/处理中请求不承诺与文件更换之间原子撤销，
后续业务仍受 owner 当前资源权限与状态校验。实施不得自行增加旧凭据允许窗口或后台热更新控制面。

## 执行授权的独立门

Agent execution proof 的签名、issuer/audience、kid/thumbprint、tenant、actor/subject、Run/session、lease fence、
operation、请求 binding 和期限仍须验证；签名正确不替代当前资源许可或有效 Run。

旧实现的 `DIRECT_USER_CURRENT` 在线 IAM 判断不得在改名时静默丢失。替代方案须先在 Agent/Platform owner
契约确定授权事实来源、有效期、用户撤权对已执行 Run 的影响及取消/过期处理，并证明不接受旧 lease 或错主体。
这部分在 owner 设计门与真实负控通过前，不激活新执行认证；不先造“已授权”的本地 JWT 成功路径。

用户已选择：**正在执行的 Run 也立即停止授权**，不采用“已授权 Run 继续到固定期限”方案。退出断言为撤权
确认成功后零新工具/模型执行许可；取消、旧 proof、旧 lease generation、重放和网络不确定均不得恢复 allow。
在途请求按真实取消/unknown 状态收敛，已发送调用不重标成从未发送，未确认用量继续 pending。

服务直接认证与撤权事实同步是两件事。后继方案须明确 IAM 权限变更的权威确认点、BFF/Agent 控制链及
Platform 当前授权判断，证明撤权通知与新许可竞争的 fencing；仅异步通知、TTL/JWKS 缓存或“签名还有效”
均不构成即时撤权保证。没有该证明时保持现执行准入，不提前激活弱化后的路径。

后继采用现 owner 的持久撤权 barrier，而不是新增认证中心：IAM 记录撤权 pending 并停止旧入口资格；Agent
以幂等命令持久推进执行授权 generation，阻断旧资格的新 Run 与新许可、取消在途任务；收到 Agent durable
barrier ACK 后，IAM 才确认撤权完成。ACK 丢失或失联保持 pending，原身份重放恢复，不超时冒成功。

Platform 执行操作须向 Agent claim 精确绑定 tenant/subject/Run/session/lease/operation/request digest/generation
的执行许可；签名 proof 只证明绑定来源，不独立授执行权。Agent 的许可与撤权 barrier 在同一 owner 持久边界
串行化，barrier 前已 claim 的操作按在途取消/unknown 收敛，之后零新许可。权限事实仍由 IAM 拥有，执行 fence
由 Agent 拥有；不共享数据库或在 Platform 复制用户权限库。

以上是后继设计决定，Agent/IAM 新操作、状态机与消费者尚未发行或实施。先收敛这两个 owner 的三面文档及
机器契约，再激活执行认证替代；普通 BFF Platform 的本地凭据组件可独立先验收。

## 方案比较

- **采用：接收 owner 本地服务认证 + 上游可信上下文。** 复用现有直接服务调用模型，删除机器 OAuth 往返；每条
  边界保留最小权限、身份、租户和资源判断。需要协调发布 breaking auth profile 与消费者。
- **淘汰：缓存原 IAM OAuth 并延长 TTL。** 仍保留 token mint/introspection、五套重复 client 与 IAM 运行依赖。
- **淘汰：关闭 guard 或只相信 service/tenant headers。** 未认证 caller 可伪造上下文，且服务认证不等于业务授权。
- **暂不采用：新增统一请求签名/认证网关。** 当前直接凭据已能表达服务身份；没有证据要求再建公共控制面。

## 放置与依赖

| 项 | 结论 |
| --- | --- |
| Owner | Platform 拥有本方 ingress 认证；BFF/Agent 各自建立可信上下文；IAM 仍拥有人类身份与权限。 |
| 当前事实 | 现 `infrastructure/iam` 承担机器 OAuth、执行校验及其他 IAM 业务读取；不整目录盲删。 |
| 目标职责 | `infrastructure/auth` 内按 schema、文件读取、身份验证、错误职责拆分；不散落在 Skills/MCP 业务中。 |
| 位置比较 | 采用 Platform 现 infrastructure 下具名 auth 文件；淘汰新一级业务模块、每业务模块复制 guard、Root 共享认证实现。 |
| 粒度 | 先交付本地凭据组件；它不是部署完成。后继 owner auth profile/guard 与消费者按原子 cutover 闭环。 |
| 依赖 | 本地组件只依赖现配置读文件能力、运行时 schema 与 crypto；不 import IAM client 或别仓业务源码。 |
| 数据/API | 首组件不改持久 Schema 或业务 Proto。激活前 owner 正规发行 breaking auth profile/provenance，再固定消费者。 |
| 删除项 | 激活切片删除五套 BFF OAuth token 获取、Platform workload introspection、Agent workload OAuth；保留人类 IAM 业务读取及第三方 MCP OAuth。 |
| 验证 | 错凭据、caller/surface/tenant 越界、取消、文件权限/损坏、轮换、错误信息不含 secret；最终真实 HTTP/Connect 组合证明内部零 OAuth 请求。 |

## 实施顺序与退出线

1. Platform 三面文档对齐本 ADR；先实现受限本地凭据与 authorizer 组件，独立审查和 owner 主树验证。
2. Agent 先发行撤权 barrier、旧资格/Run generation 与精确许可 claim 契约；IAM 固定消费并闭合
   pending→barrier ACK→completed。Platform 随后发行 direct-service auth profile 和执行授权消费者，保持
   业务对象/Schema 不变优先；不暗改历史 frozen artifact。不在 profile 未接收时重启正常 Platform。
3. BFF 一次切换其全部 Platform 用途及受信 Run 资格；Agent/System 按同一发布物切换。消费者固定版本、commit、digest。
4. 配对重载接收方与消费者，真实 App/后台/Agent 组合验收；删除被替代的内部 OAuth、scope/provisioning 入口。
   过渡组件不是双协议运行模式；不配置旧新 fallback，不把尚未激活的组件声称为 OAuth 已删除。
5. Billing worker 和付费模型调用链按各自 owner 设计、契约与真实业务测试另行闭环。

最终退出要求：App 内部机器调用不发起 OAuth/内省；人类登录/权限和第三方 MCP OAuth 回归通过；各 owner
tenant/subject/resource/fence 负控保持；真实模型发送仍只在正式资金许可后发生。组件 unit PASS 不替代此退出线。
