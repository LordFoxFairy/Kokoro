# V2 技术方案（下一版本）

- 状态：定案待用户裁决（2026-07-05）
- 触发：用户五问——修当前问题 / agent 链路闭环 / 整体链路错误 / assets 缺架构思想 / 新方案+新 PRD
- 姊妹篇：`product/09-v2-prd.md`（产品切片）；审计明细见本文 §1
- 落地更新（2026-07）：**G1 鉴权 / G2 失败码 / G4 i18n 已落地**。失败呈现（§1.2③）已修为按码讲人话；web 静态 i18n（中/英，`kokoro-web/src/i18n`）已上线；身份签发+验签链与登录闸已落地，浏览器密封 cookie 形态见 [AUTH-P0](../../superpowers/specs/2026-07-12-wave1-auth-p0.md)（**已落地**，user e4068d6/6260da5/8c26740：web BFF httpOnly cookie + magic-link + nonce 防 CSRF + 日志脱敏）。以下正文维持 2026-07-05 原文。

## 0. 一句话主题

**从"跑通"到"生产可用"**：V1 把三仓链路与验证马具立起来了；V2 收编三块结构债
（skills 供给、鉴权、失败可读性），并把配置管理引向 platform 后台。

## 1. 链路审计结论（agent 闭环 + 跨栈整体）

（本节由两路只读审计代理产出，结论按"OK / 缺口→处置"记账；
"本轮已修"= V2 方案落地前先行修复的缺陷。）

### 1.1 agent 闭环（六项）

```text
① 失败路径终态单一性  基本 OK（四路共用原子认领，不双发）。
   缺口A steer 入账失败误杀健康 run → 已修（dispatch 内隔离，只记日志；回归钉
     test_steer_persist_failure_does_not_kill_healthy_run）。
   缺口B 裂脑窗口：网络分区假死副本被重拾后短暂双跑，带副作用工具可能双执行
     → V2-M1：执行前 fencing（checkpoint 乐观锁）。
② HITL 崩溃恢复      OK 自愈（pause 哨兵+control 收养+emitter 重算，chaos 实证）。
③ sandbox 与终态对齐  缺口：零主动销毁，终态后容器活到 TTL（成本泄漏非正确性）
   → V2-M1：终态/cancel 路径挂 backend teardown 钩子。
④ 中间件交互          基本 OK。窄缺口：steer 排空与 checkpoint 落盘非原子，
   窄窗丢一条插话（可重发）→ V2-M1：checkpoint 提交后再消费信箱。
⑤ retention 竞态      thread TTL 时间扫会误删活现场（高危）→ 本轮裁定 A：
   机制整体拆除，转会话删除级联（见 §2A）。events/run TTL 保留（只清终态垃圾）。
⑥ namespace 隔离      修订后边界：GA 只认 namespace，且 namespace 自身就是独立空间。
   不补 user 维度，不在 GA 契约里加 userId/ownerId/workspaceId。web/session/platform
   负责把用户、团队、站点和权限解析成最终 namespace。
```

### 1.2 跨栈整体（七项）

```text
① relay 崩溃窗口   缺口（已修）：inserted 守卫使"append 已落库、投影前崩溃"永久漏投影
   （暂停失踪→control 挂死）→ 投影恒执行（全分支幂等），回归钉 ×1。
② 终态投影次序     缺口（已修，严重）：markRunTerminal 先于终态事件 append，中途崩溃
   run 永卡 active → 终态事件先落定（幂等锚点）再投影，回归钉 ×1。
③ 失败呈现         缺口（已修）：web 丢弃 run.failed 载荷→按码讲人话（failureCopy 表）；
   enqueue_failed 未实现契约承诺→投递失败即合成终态收口（枚举扩值+503+回归钉）。
④ 控制撞终态       部分缺口：resume/裁决撞 409 时 web 卡 awaiting-hitl 不对账
   → V2-M2：409 触发 snapshot 对账清 stale pause。
⑤ files 安全       缺口（已修）：软链逃逸（realpath 双侧校验）+25MB 读上限+nosniff，
   回归钉 ×4（顺带抓出 macOS /var 软链根的实现 bug）。
⑥ SSE 重连         OK（回放源=Mongo 全量，live 裁剪安全，eventId 去重）。
⑦ 鉴权面           全裸（已知）：五路由无身份、owner 硬编码 → V2-P1 主线。
```

## 2. 核心重构：Skills V2——从"资产全文注入"到"backend 供给 + 原生渐进披露"

### 2.1 现状病理（用户直觉"assets 很奇怪"的技术实锤）

```text
① 平行造轮子：deepagents 原生 SkillsMiddleware 就是 Anthropic agent skills 规范
   ——渐进披露（prompt 只挂 name+description，用到才 read_file 全文）、YAML
   frontmatter 元数据、经 backend API 装载（state/filesystem/remote 全兼容）、
   多源分层 last-wins。我们的 SkillLibrary.render_prompt 全文注入是与之平行的
   弱化实现，违背"深度复用 deepagents 原生件"的既定法则。
   V1 理由"state backend 读不到宿主 SKILL.md"是误诊：官方口径 StateBackend 经
   invoke(files={...}) 供给 skill 文件——缺的是"供给"一步，不是原生机制不可用。
② 无能力语义：SKILL.md 被当不透明文本 blob——没有 frontmatter（name/description/
   allowed_tools），skill 无法声明自己的工具面，渐进披露没有 description 可用。
③ 无分层无租户钩子：flat 全局库，与 namespace 模型（skills 按 namespace 隔离、
   base→team 分层覆盖）无对接点；"资产库"心智把 skills 当静态文件，而它是
   agent 运行时能力包。
④ 域名错位：personas 不是"资产"——人格是 agent 定义数据（entry/subagent 的
   一部分），终局归 platform 配置管理；把它和 skills 同装在 assets/ 里是
   按存储形态分类，不是按架构角色分类。
```

### 2.2 目标架构：分发 → 供给 → 消费 三层

```text
分发层（保留，ADR-011 资产源不动）
  skills 包在哪：local 目录 / s3 bucket（多 pod 单真源、platform 后台写路径）。
  职责收窄为"包的仓库"，启动装载为不可变快照（快照语义不变）。

供给层（新增：provisioning）
  装配期把本次 run 授权的 skill 包物化进该 run 的 backend：
    state       invoke files={"/skills/<name>/SKILL.md": ...}（官方口径）
    local_shell workspace 下物化 /skills/ 子树（写盘即供给）
    docker      同 local_shell（文件面留宿主，容器挂载可见）
    e2b/custom  upload_files 上载
  供给矩阵按 backend 五档逐格测试（组合矩阵审查法则）。

消费层（切换：deepagents 原生）
  create_deep_agent(skills=["/skills/granted/"]) 挂 SkillsMiddleware：
    渐进披露：prompt 只列 name+description，agent 用到才读全文——
      多 skill 不再线性膨胀 system prompt（现 32k/skill 上限问题消解）。
    frontmatter：name/description 必填校验、allowed_tools 声明工具面。
    分层：namespace 模型落点=多 source（/skills/base/ + /skills/<ns>/，
      last-wins 覆盖），机制原生自带。
  SkillLibrary.render_prompt / compose_system_prompt 的 skills 段 / 32k 上限
  全部退役；子代理同机制（wire_subagents 传 skills sources 而非渲染文本）。
```

### 2.3 迁移步骤（一次切换，不留兼容层）

```text
S1 资产规范升级：现有 SKILL.md 补 YAML frontmatter（name/description 必填，
   allowed_tools 可选）；资产源装载期解析并校验（无 frontmatter fail-loud）。
S2 供给器落地：sandbox 域加 provision_skills(backend, packages)——写文件面
   四档矩阵 + state 档经 invoke files 注入（run_agent payload 组装点）。
S3 消费切换：build_agent 传 skills sources；删 render_prompt 注入链
   （agents/general/persona.py 回归纯人格）；契约 runtime.skills 语义不变
   （仍是名称数组=授权集），agent 侧由"渲染"变"供给+挂源"。
S4 personas 归位：PersonaLibrary 移出 assets/（人格解析留 agents 工厂层，
   数据面标注"platform 配置管理升级路径"）；assets/ 更名收窄为 skills 包
   分发域（或并入 sandbox 供给域，落地时按文件量取小者）。
S5 测试矩阵：渐进披露真图断言（prompt 只含 description、read_file 后全文
   可达）× backend 五档 × 分层覆盖 × frontmatter 负例；real-model RM-D 场景
   同步改写。
```

## 2A. 会话删除级联（2026-07-06 裁定修订：改软删除，本节 saga 仅留档不实施——见 technical/16）

### 现状与裁定

```text
现状：web "删除会话"只删浏览器 localStorage——session 的 Mongo 文档、agent 的
checkpoint、工作区文件全部残留。thread TTL 时间扫（按闲置时长猜测可删）已裁定
拆除：能否删除由业务生命周期决定，不由时长猜测。冷数据归档不做（裁定排除）。
```

### 设计：删除是一次幂等 saga（at-least-once + 全步幂等 = 多 pod 收敛）

```text
① web    DELETE /sessions/{id} → 本地照旧即时移除（乐观）。
② session（会话的 owner，级联的编排者）：
   sessions doc 置 status=deleting（墓碑，幂等）
   → 若有 active run：走既有 cancel 路径（任一 pod 认领收口）
   → 发 thread.delete{namespace, session_id} 进请求流（consumer group：恰一 worker 接）
   → 删自己拥有的：messages / session_events / pauses / runs 文档（幂等 deleteMany）
③ agent  任一 worker 消费 thread.delete（全步幂等，可重复执行）：
   对该 thread 名下未收口 run 逐个 try_mark_terminal（在跑的 pod 由终态闸自停，
     与 cancel 同语义——跨 pod 正确性复用既有机制，不新造）
   → checkpointer.adelete_thread(scoped_thread_id)（LangGraph 官方口）
   → 工作区清除：local 档删 {root}/{ns:sid}/（共享卷任一 pod 可删）；s3 档删前缀
   → ledger 按 thread 清 run 行（json_extract/投影查询，一次性命令非热路径）
   → 发 thread.deleted 确认事件
④ session 收到确认 → 硬删 sessions 墓碑。超时未确认 → 按墓碑重发 thread.delete
   （at-least-once；worker 侧全步幂等，重复执行无害）。
```

### 多 pod 正确性论证（逐格）

```text
删除时 run 正在别的 pod 跑    try_mark_terminal 原子闸 + TerminalGuard 自停（chaos 已实证的 cancel 语义复用）。
执行删除的 worker 中途崩溃    session 墓碑超时重发；步步幂等，从头再走收敛。
两个 worker 先后收到重发      幂等：adelete_thread/删文件/删行都可重复。
删除与新消息并发              墓碑在 session 受理点先挡（deleting 状态拒收新消息 409）。
session_id 复用               不存在：web 生成 uuid 型 conv id，删除后不再复用。
```

### 与既有机制的关系

```text
不引入任何时间猜测：触发源恒为用户动作（墓碑）。
events/run TTL 保留：它们只清"已终态 run"的派生垃圾，与用户现场无关。
鉴权落地（P1）后：DELETE 端点按 owner 裁权，级联语义不变。
```

## 3. 其余 V2 支柱

```text
P1 鉴权主线（生产红线）：session HTTP/SSE 全端点当前无身份校验——接平台
   账号体系（site/user JWT），files/messages/control 按 auth owner 和 session.namespace
   裁权。GA 仍只消费 namespace，多租户隔离从"约定"变"强制"。
P2 失败可读性收口：run.failed code 已上 wire（V1 末梢）——web 按码呈现
   人话失败卡（含重试按钮语义）、enqueue_failed/assembly_failed 区分展示；
   与 i18n 静态层同波（错误码→文案表是静态 i18n 第一批内容）。
P3 platform 配置后台最小集：namespace profile（entries/swarm/skills 授权）+
   资产上传（s3 assets bucket 写路径 + 滚动重启触发）先做只读展示→再做编辑；
   session 加载面不变（配置表既定方向）。
P4 i18n 静态层第一步：按 technical/14 判断落地——locale 协商 + 构建期语言包 +
   42 文件硬编码文案收编；动态覆盖层与 platform 后台同波再议。
P5 第二 agent 类型"机制就绪门"：不实现 music/video（红线），但用一个
   最小非对话型类型走通 agents/<type>/ 同构包 + 契约枚举扩展 + studio 无
   ask_user 的 pause_tools=∅ 路径，证明新增类型成本≈一个包+一行注册。
```

## 4. 里程碑切片

```text
M1 会话软删除（technical/16）+ 审计遗留（fencing/sandbox teardown/steer 原子/409 对账）+ Skills V2（S1-S5）——【已全部交付，验收见 docs/reports/m1-*】
M2 鉴权主线（P1）+ 失败可读性（P2）
M3 platform 配置后台最小集（P3）+ i18n 静态层（P4）
M4 类型就绪门（P5）+ 全量马具扩展复验（verify-all 增渐进披露档）
每个 M 收口条件：verify-all 全档 PASS + 三仓 L1 全绿 + 浏览器走查存证。
```

## 5. 不做清单（防跑偏）

```text
不实现 music/video studio（机制就绪≠功能实现）。
不做 swarm 运行时（langgraph-swarm 建图仍 P2 后置，配置表已就绪）。
不做 skills 的 git/http 安装与审核工作流（Hub 是 platform 故事）。
不做动态 i18n 覆盖层编辑面（等 platform 后台）。
不留任何旧 render_prompt 兼容层（一次切换）。
```
