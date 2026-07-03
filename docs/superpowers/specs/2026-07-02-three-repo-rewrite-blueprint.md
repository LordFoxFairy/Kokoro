# 三仓重写蓝图（2026-07-02）

> 状态：待用户认可。认可后即为阶段二施工的唯一基准，旧结构物理抹除，不留兼容层。
> 硬约束：LangChain + DeepAgents 不可更换；一套词汇贯穿三仓；每个不变量只有一个属主。
> 诊断来源：4 个深读审计（agent/session/web/跨仓契约）+ 3 份独立架构方案合成，审计原始数据见会话 scratchpad `phase1/`。

---

## 一、诊断报告（病灶总览）

### 跨仓契约层（最重）

1. **契约单源只覆盖事件下行面**。控制面（run.request / run.resume / run.cancel / ResumeDecision / execution_style / permission_mode 枚举）是 2–4 处手写镜像、零门禁（session `run-control.ts` ↔ agent `worker/messages.py` ↔ web `transport.ts`），改协议漏改任何一处都无 CI 报警。
2. **agent 是唯一不受漂移门禁的生产端**。`contract/events.yaml` 的 agent_out 视图（~80 行）与真实 wire（`run/events.py` 发 `agent_status`/`text_chunk`）根本对不上，`verify.py` 自述不 gate agent 边界并引用不存在的 `envelope.py`。
3. **三套词汇 + 逐层改名**：`text_chunk` → `message.delta` → `message-delta`，为命名审美供养 session 改名层 + web 167 行 mapper + 185 行 render union 整层冗余。
4. **docs/protocol 四份"spec-first"规范描述的是已不存在的 wire**（text.delta/XREADGROUP/message_ref），与 yaml、与代码三方互斥。
5. **HITL 核心不变量三仓各自实现**：agent 从 checkpoint 裁决（权威）、session 从 Mongo 事件史重建 pending 并预裁决（第二真理源 + read-your-write 竞态）、web hook 内嵌 agent 对齐算法。
6. **传输生命周期无契约**：流名字面量双仓手抄；请求流永不裁剪、无 checkpoint，session/agent 每次重启 O(全部历史 run) 全量重放；per-run 流永生；HITL control 消息被 session dispatcher 误报为 malformed run.request。
7. **投机字段供养 + 真实数据蒸发**：`agui_out_web_extra` 9 个无生产者字段进了 web schema；agent 认真算的 token_usage 在 normalize 层被扔掉。
8. **一条文本增量过 5–6 次运行时校验**（含 session 对自己刚构造的信封自检、Mongo 每次出库重 parse）。

### kokoro-agent

- **critical**：~7 个零引用占位文件（skills/、mcp/、run/lifecycle|capabilities|context.py、storage/memory.py），`test_package_architecture.py` 逐文件冻结包布局把死代码钉死成合法结构；lifecycle 终态枚举与真实 wire 矛盾。
- **high**：`execution/` 六职责大杂烩，331 行调度器藏在名为 `resume_agent.py` 的文件里并私藏 wire 流键；`AppConfig.from_env()` 6 处深层重读 env；`leases.py` 名为租约实为永久认领——pod 崩溃后 run 永久悬死。
- **medium**：`agent_status` 压扁 5 种语义靠 data.status 二次分发，payload 契约仅 TypedDict（无运行时校验）；HITL pending 计算两处重复；`_load_callable(importlib+getattr)` 把 `create_deep_agent` 洗成无类型；事件流无 maxlen 无限增长；`_custom_source` 三份拷贝、subagent_source 五层透传。
- **low**：`_tasks` done_callback 按 run_id 弹出，resume 竞态误删新任务句柄。

### kokoro-session

- **critical**：dispatcher 无 checkpoint/consumer-group，重启全量重放 + 每历史 run 重开 relay 与独立 redis 连接。
- **high**：HITL control 复用请求流但 dispatcher 误报 malformed；SSE/relay 订阅无取消机制——空闲断开永久泄漏 redis 连接与 pending promise；cursor 字符串手术（`cursor.split("-")[0]`）击穿 StreamProtocol 抽象，redis 同毫秒 seq 撞号。
- **medium**：生成类型被 `Record<string,unknown>` 宽化再 cast 回（掩盖 `runtime-custom` 幻影枚举漂移）；session.created 每 run 重发且 owner_id="kokoro-agent" 语义造假；四层 DDD 对 21 文件纯仪式且层名说谎；去重职责三仓涂抹。
- **low**：port 死方法（delete 零调用、close 不生效）；500 回显内部错误。

### kokoro-web

- **critical**：会话引擎 5 个 hook 靠共享裸 ref 互穿（4 个 ref 作为公开 API），effect 声明顺序是正确性前提。
- **high**：前端套 DDD 完全错配（副作用在 application、纯函数在 infrastructure）；reducer.ts 兼任 barrel 兼容层抹平依赖图；三份状态真相（SSE 闭包 state / liveStore / localStorage）`?? persistedStore` 六处散弹合并；**后端任何失败静默降级为本地假回复**（吞 500、demo 代码在生产路径）。
- **medium**：replay O(n²)（每事件全量拷贝 Set/数组）；本地 conv id 冒充后端 sessionId；中文 UI 文案硬编码进状态层；三套手写 localStorage 机制；2186 行巨型壳测试兜住全部行为规格；3001 端口/localhost 嗅探 + demo id 硬编码。

### 必须保留的资产（keep）

三层职责切分本身；`agent_wire.py` 的"类型即真理"生成方向（推广而非放弃）；transport cursor 作 SSE 续传轴 + DB 真源 + 有界 live bus；确定性 event_id 幂等链；claim-before-emit 单终态不变量；HITL fail-loud 对齐协议（收敛为单处实现）；v3 四投影 queue 合流 pump；窄 Protocol 挡 LangGraph 泛型；LocalFakeChatModel 离线 e2e；skip-and-continue 脏数据隔离；全边界 strict/forbid 纪律；web 事件溯源投影模型、runId 锚定收束、rejected 不降级、IME/双发守卫等微正确性。

---

## 二、契约中枢（新 contract/）

```
contract/
├── spec/
│   ├── events.yaml      # 唯一事件立法：13 语义 kind，一套词汇（snake_case + dot-kind）三仓贯穿；
│   │                    #   agent_status 复用解开为一等 kind；每字段类型+必选性；终态枚举；
│   │                    #   tool.awaiting_approval 携带 pending_tool_ids（同帧完整待批集合，
│   │                    #   HITL"凑齐才提交"成为契约字段而非 agent 算法泄漏）；
│   │                    #   token_usage 正式挂 run.completed 全链路贯通；投机字段零容忍
│   ├── control.yaml     # 控制面首次进单源：run.request/resume/cancel + ResumeDecision 判别联合
│   │                    #   + execution_style/permission_mode 枚举（四处手抄归一）
│   ├── streams.yaml     # 传输生命周期立法：流名模板、所有权与裁剪（见 §四）、consumer-group 名、
│   │                    #   MAXLEN/BLOCK_MS、cursor 不透明、seq=store 分配的 per-session 单调整数
│   └── http.yaml        # session HTTP 面：3 端点 body/回执/错误形状、SSE Last-Event-ID=seq 续传语义
├── generate.py          # 唯一生成器：spec → 三仓 contract/ 目录全部 py+ts；确定性字节输出；
│                        #   自带 golden-file 测试（生成器首次有自己的测试）
├── check.py             # 唯一门禁：重生成 + git diff --exit-code；三仓 CI 各跑一次
└── README.md            # 由 generate.py 从 spec 渲染的人读协议文档（docs/protocol 手写规范的替代品）
```

**抹除**：`verify.py`（461 行正则 TS 解析器）、`agent_wire.py`（反向生成造成双 master）、events.yaml 三视图结构与 agui_out_web_extra 机制、docs/protocol/ 四文件。

---

## 三、三仓新目录树

### kokoro-agent（Python，LangChain + DeepAgents worker）

```
kokoro-agent/src/kokoro_agent/
├── __init__.py            # 仅版本号
├── config.py              # AppConfig：全仓唯一 os.environ 读取点，仅 worker/main.py 调用一次
├── observability.py       # Langfuse trace config 构造，吃注入 config
├── contract/              # ⚙ 全目录生成（DO NOT EDIT）
│   ├── __init__.py        # ⚙ re-export，业务代码唯一协议入口
│   ├── events.py          # ⚙ 出站 wire：13 kind Pydantic strict 判别联合 + 信封（含 per-run 单调 index）
│   ├── control.py         # ⚙ 入站联合 run.request/resume/cancel + ResumeDecision + 枚举
│   └── streams.py         # ⚙ 流名模板 + consumer-group + MAXLEN/BLOCK_MS 常量
├── worker/
│   ├── main.py            # 进程入口：config 解析一次 → 显式装配 → Supervisor.serve
│   └── supervisor.py      # 长驻调度（正名）：XREADGROUP 消费请求流 + ack、按 kind 三路分发、
│                          #   per-message 隔离、任务表按任务身份弹出（修竞态）、租约心跳
├── run/
│   ├── builder.py         # 静态 import create_deep_agent 装配（删 _load_callable 洗型）
│   ├── invoke.py          # 单次 run 编排：claim-before-emit 终态原子认领三路共用（keep 原语义）
│   ├── pump.py            # v3 四投影并发消费 + queue 合流单点发布 + 哨兵必达 drain（keep）
│   ├── emit.py            # 投影→contract.events 构造唯一地点；index 在此递增；source 标签一次贴齐
│   ├── hitl.py            # pending 集合全仓唯一实现 + resume 按 tool_id fail-loud 对齐 +
│   │                      #   reject/respond 快照直发（合并两份重复）
│   └── prompts.py         # 系统提示词资源
├── ports.py               # LangGraph/DeepAgents 窄 runtime_checkable Protocol（keep 原 protocols.py）
├── model/
│   ├── factory.py         # openai/anthropic 按 fast/thinking 映射 effort
│   └── local_fake.py      # 免凭证确定性脚本模型，驱动真实 DeepAgents 离线 e2e（keep）
├── subagents.py           # 内建 + env 自定义子代理目录（原 4 文件收拢）
├── tools/
│   ├── ask_user.py        # ask_user HITL 工具
│   └── approvals.py       # 工具名注册 + interrupt_on 构造，吃注入 config
├── sandbox.py             # filesystem 权限 + backend 选择（原 2 文件 31 行收拢）
├── streams/
│   ├── protocol.py        # StreamProtocol：publish/read_all/subscribe(可取消)/ack，cursor 不透明
│   ├── memory.py          # 内存实现（带上限裁剪）
│   ├── redis.py           # xreadgroup+xack、断线指数退避（keep）、XADD maxlen 裁剪（新增）
│   └── factory.py         # 按注入 config 选后端
└── storage/
    ├── run_state.py       # RunStateStore 协议：TTL 租约 try_claim/renew/reclaim_expired +
    │                      #   try_mark_terminal 原子认领（修永久认领黑洞，名实相符）
    ├── sqlite.py          # WAL+busy_timeout（keep 原子语义）+ 过期租约重拾
    ├── mongo.py           # $setOnInsert + DuplicateKeyError 兜竞态（keep）+ lease TTL 字段
    └── checkpoints.py     # LangGraph checkpointer 工厂（sqlite/mongo/memory）

tests/：test_contract_gate / test_architecture（只断依赖方向，删文件清单冻结）/
        test_supervisor（分发、租约过期重拾、任务句柄竞态）/ test_invoke（三路径单终态）/
        test_hitl（对齐缺/多/重复 fail-loud 矩阵）/ test_streams / test_storage /
        e2e/test_local_fake_run（LocalFake 全链路）
```

### kokoro-session（TS/Node，归一化 + 持久 + SSE）

```
kokoro-session/src/
├── main.ts                # env(Zod .catch) 一次解析 → 装配 → recover 扫描 + HTTP；
│                          #   fail-fast + 优雅关停（close 真正生效）+ isDirectEntry（keep）
├── contract/              # ⚙ 全目录生成（DO NOT EDIT）
│   ├── wire-events.ts     # ⚙ 入站 agent 事件 Zod strict（与 agent contract/events.py 同源同词汇）
│   ├── session-events.ts  # ⚙ 出站信封：envelope + payload 精确联合（删 Record 宽化与回 cast）
│   ├── control.ts         # ⚙ run.request/resume/cancel + ResumeDecision
│   ├── streams.ts         # ⚙ 流名/consumer-group/MAXLEN/删除职责
│   └── http.ts            # ⚙ 3 端点 body/回执 schema + SSE 语义
├── relay/
│   ├── start-run.ts       # POST 消息→session 签发 run_id→发布 run.request（带 MAXLEN）→就地拉起 relay
│   ├── relay-run.ts       # per-run 管道：wire parse（唯一入站信任边界）→ envelope →
│   │                      #   store.append 先行落定 seq → live publish → 终态持久后删除 per-run 流；
│   │                      #   AbortSignal + 空闲超时收束（agent 崩溃不再永久泄漏）
│   ├── envelope.ts        # 纯函数：event_id = f(run_id, index) 确定性派生（不碰 cursor）
│   ├── recover.ts         # 启动恢复：store 扫描未终态 run，从断点续接 relay（替代全量重放 dispatcher）
│   └── control-forward.ts # resume/cancel：Zod 形状校验即转发请求流，不做 pending 预裁决（裁决权归 agent）
├── store/
│   ├── port.ts            # MessageStore：幂等 append(重复 event_id 返既有 seq)→分配 per-session 单调 seq、
│   │                      #   readSession(fromSeq)、未终态 run 扫描、run 记录读写
│   ├── mongo.ts           # (session_id,event_id) 唯一索引 + $setOnInsert（keep）+ 原子 seq 计数
│   ├── memory.ts          # 同语义内存实现（测试免 docker）
│   └── factory.ts         # env 选择
├── transport/
│   ├── port.ts            # StreamPort：publish/subscribe(AbortSignal)/ack/trim/delete——每个方法都有真实调用方
│   ├── redis.ts           # per-订阅 duplicate 连接 BLOCK read（keep）+ abort 即 disconnect（修泄漏）
│   ├── memory.ts          # abort 立即唤醒终结订阅
│   ├── live-bus.ts        # 有界 live 总线（MAXLEN 裁剪安全：DB 为长期真源，keep）
│   └── factory.ts         # env 选择
└── http/
    ├── server.ts          # node:http 3 路由 + CORS 白名单 + ZodError→400 + 不透明 500（内部日志）
    ├── sse.ts             # store 历史回放（Last-Event-ID=seq，非法即全量）+ live tail；
    │                      #   req close → AbortSignal 立即释放连接（修泄漏）
    └── format.ts          # SSE chunk 格式化纯函数

tests/：contract-gate / relay（信封化幂等、终态删流、崩溃超时收口）/ recover（只重拾未终态）/
        control-forward（透传不裁决）/ store（seq 单调、幂等 append 双调）/
        transport（abort 释放、断线续读）/ sse（历史+live 缝隙、断开即释放——连接数断言）
```

### kokoro-web（Next.js 前端）

```
kokoro-web/src/
├── app/
│   ├── layout.tsx         # 根布局 + 字体
│   ├── page.tsx           # 5 行委托 SessionShell
│   └── globals.css        # 仅 design token + reset（九文件全局 BEM 树解散，样式随组件走）
├── contract/              # ⚙ 全目录生成（DO NOT EDIT）
│   ├── session-events.ts  # ⚙ SSE 事件 Zod strict + z.infer 即领域类型：与 session 出站同源同词汇
│   │                      #   （render union + 167 行 mapper 整层消失）
│   ├── control.ts         # ⚙ POST messages/control body + runId 回执（补上唯一没过 Zod 的入站口）
│   └── event-names.ts     # ⚙ SSE 具名监听注册表（keep：漏 kind 编译期暴露）
├── core/                  # 纯函数状态核：零 I/O 零 React（规格测试主战场）
│   ├── state.ts           # SessionStreamState + 显式 activeRunId（删对象键序推断）
│   ├── reducer.ts         # 事件折叠：event_id 幂等去重 + replay 批量折叠（可变草稿一次快照，修 O(n²)）
│   │                      #   + never 穷尽守卫 + rejected 不被 tool.returned 降级（keep）
│   ├── projections.ts     # thread/segment 归组投影 + seq 稳定插入（keep 模型）
│   ├── persistence.ts     # 落盘 Zod schema + satisfies 漂移检查 + 解析失败降空态（keep 手法）
│   └── conversations.ts   # 多会话列表纯操作（keep）；终态收口置结构化 status（删中文文案）
├── engine/                # 副作用层：浏览器 I/O 唯一居所
│   ├── machine.ts         # 显式状态机：idle/submitting/streaming/reattaching/awaiting-hitl；
│   │                      #   流句柄/in-flight 守卫/runId 锚定收束全部单点持有（删 5-hook 裸 ref 穿透）
│   ├── hitl-staging.ts    # 决策暂存纯逻辑：以契约 pending_tool_ids 为完备判据（删 agent 算法知识内嵌）
│   ├── reattach.ts        # pendingRunId 精确重连 + 90s 兜底（keep 语义，收进状态机事件）
│   ├── client.ts          # fetch POST + EventSource：回执/入站全走 contract Zod；
│   │                      #   失败即状态机错误态（删静默降级模拟器）
│   ├── config.ts          # NEXT_PUBLIC_SESSION_BASE_URL 唯一读取点（删端口嗅探与 demo id）
│   └── use-session-engine.ts  # 全仓唯一 React 接缝：useSyncExternalStore 快照 + 命令下发
├── lib/
│   ├── persisted-store.ts # 全站唯一 localStorage 外部 store（Zod 参数化；合并三套同构实现）
│   └── use-hydrated.ts    # SSR 首帧一致性（keep）
├── dev/
│   └── preview-transport.ts  # 显式开发模式假流（仅 env 开关注入，永不作运行时兜底）
└── ui/                    # 组件与 CSS Module 同址
    ├── shell/session-shell.tsx + .module.css      # 组装接线 use-session-engine，注入缝保留
    ├── rail/session-rail.tsx + rail-search.ts + use-rail-resize.ts + .module.css  # 删停用占位导航
    ├── thread/conversation-thread / assistant-turn / segment-process（待批强制展开 keep）/
    │        tool-call-row（HITL UI；文案按结构化 status 由此层生成）/ subagent-row /
    │        run-state（agent 裁决错误显式呈现）/ markdown-message（安全默认 keep）/
    │        message-bubble / use-auto-scroll（事件到达即信号，删全量字符扫描）/ .module.css
    ├── composer/composer（IME 守卫 keep）/ composer-menu / expand-dialog / mode-options / .module.css
    ├── todo/todo-bar.tsx + .module.css
    └── icons/（按域三分：rail / thread / composer，解散 321 行单文件）

tests/：contract-gate / core（reducer 边界矩阵 + replay 收敛 + 终态收口；projections）/
        engine（machine 全迁移矩阵：提交/重连/HITL 凑帧/双发守卫；hitl-staging 部分拒绝）/
        ui/session-shell.smoke（一条主路径冒烟，删 2186 行巨测）
```

---

## 四、边界协议法典

1. **一套词汇**：13 个语义 kind（`run.started / thinking.delta / text.delta / text.completed / tool.invoked / tool.awaiting_approval / tool.returned / todo.updated / subagent.started / subagent.finished / subagent.text.delta / subagent.text.completed / run.completed / run.failed`——run.completed/failed 为终态对，共 14 计入终态）从 agent 到像素同名同拼写（snake_case + dot-kind）。session.created/run.created 合成事件删除，会话元数据由 session 在 POST messages 时写自己的存储。
2. **身份与信封**：run_id 由 session 签发并随 run.request 下发；request_id 概念删除。agent 信封含 per-run 单调 `index`（emit.py 单点递增，pump 已串行化天然安全）。session `event_id = f(run_id, index)` 纯函数派生；`seq` 由 store 在首次 append 落定（per-session 单调整数，后端无关）；重复 append 返既有 seq。**幂等与排序属主唯一 = store**；cursor 语法永远封在 transport 内部。
3. **持久先于广播**：relay 先 append（拿 seq）再 publish live。热路径多一次 DB 写是已知代价（见风险 §六-4）。
4. **HITL 权威唯一**：pending 与 resume 对齐只活在 agent `run/hitl.py`；session 只做形状校验后透传；agent 拒绝以 wire 错误事件回流，web 渲染成人话。`tool.awaiting_approval.pending_tool_ids` 让 web 暂存逻辑读契约而非内嵌算法。
5. **传输生命周期**：session 拥有请求流（publish 带 MAXLEN；不订阅它——relay 就地拉起 + 启动恢复扫描）；agent 以 XREADGROUP + ack 消费请求流（parse 后 ack，崩溃恢复靠 TTL 租约重拾）；agent 拥有 per-run 事件流（XADD maxlen）；session relay 在终态持久化后删除该流。每条流"谁写/谁读/谁裁剪/谁删除"四问都有唯一答案，全部立法于 streams.yaml。
6. **每条数据在每个信任边界恰好校验一次**：agent 构造（Pydantic strict）→ session 入站 parse → web 入站 parse，共三次；session 出站自检与 Mongo 出库重 parse 删除。
7. **字面量归零**：任何仓源代码出现 `kokoro:` 流名前缀字面量即 CI grep 失败；base URL 全部 env 注入。

## 五、Kill List（物理抹除，凭据见诊断报告）

**agent**：skills/、mcp/、run/{lifecycle,capabilities,context}.py、storage/memory.py；test_package_architecture 文件清单冻结；execution/ 整目录（拆解后删除）；ToolPolicyMiddleware；_load_callable；6 处深层 from_env；永久认领伪租约；agent_status 复用；TypedDict-only payload；三份 _custom_source；5 层 source 透传。
**session**：四层 DDD 目录；全量重放 dispatcher；pendingApprovalsFromEvents + http 预裁决；normalize 改名层；session.created/run.created 合成 + owner_id 造假；cursor 字符串手术；seenCursors 与终态豁免分支；port 死方法；500 回显。
**web**：transport-event-mapper + render union；reducer barrel；5-hook 裸 ref 状态机；fallbackToPreview 静默降级 + simulator 生产路径；三套 localStorage；app/styles 全局 BEM 树；icons 单文件；状态层中文文案；对象键序推断 activeRun；端口嗅探 + demo id；2186 行巨测。
**contract**：verify.py 正则解析器；agent_wire.py 反向生成；events.yaml 三视图 + agui_out_web_extra；generate.py 死 emitter；docs/protocol/ 四文件。

## 六、真实风险（不粉饰）

1. **原子切换**：新旧进程完全不可互通，三仓同一窗口切换；以 LocalFake + memory 后端全栈 e2e 作为切换闸门。
2. **存量数据弃档**：旧 Mongo 事件史与旧 web localStorage 对新 schema 不可读。默认清库重来（demo 阶段）；不写迁移脚本（那是变相兼容层）。**需用户拍板**。
3. **生成器单点**：generate.py 一个 bug 污染三仓，配 golden-file 测试 + 确定性输出断言。
4. **persist-before-publish**：流式首字延迟增加一次 Mongo 写往返；先压测，超阈值再做 text.delta 微批持久化（bounded follow-up）。
5. **TTL 租约双刃**：TTL 短→活 pod 被误判死、run 双执行（中间副作用可能重复，终态由 claim-before-emit 兜恰好一个）；TTL 长→恢复延迟。参数需实测调。
6. **web 状态机重写是行为最密集迁移**：先把 keep 清单的微正确性写成 machine/core 层规格测试再动刀，否则"一步到位"变"一步丢失"。
7. **consumer-group at-least-once**：ack 时机 = parse 后；崩溃窗口靠租约重拾兜底，恢复正确性压在租约实现质量上，需崩溃注入测试。
8. **web 直接消费 snake_case**：拿命名惯例换掉整个 mapper 层，lint 豁免，禁止日后加回转换层。

## 七、验收门禁（阶段二每仓必绿）

| 层 | 命令 |
|---|---|
| contract | `python3 contract/check.py`（重生成 + 字节 diff）+ generate.py golden-file 测试 |
| agent | `uv run pytest && uv run pyright && uv run ruff check src tests` |
| session | `npm test && npm run typecheck && npm run lint` |
| web | `npm test && npm run typecheck && npm run lint && npm run build` |
| 跨栈 | LocalFake + memory/redis 双后端 e2e：13 kind 事件按序全到、HITL 审批/拒绝/编辑/cancel 回路、SSE 断线续传 |
