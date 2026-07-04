# Kokoro 系统总方案 v2（web + session + agent 全栈，面向 music/video 成品）

2026-07-04 定稿，取代同日 agent-master-plan（v1 只覆盖 agent 仓）。
本文吸收当日全部裁定：命名法典、成品/子代理二元论、对偶性定律、能力束流动、
steering、子代理可见性、"两个家+bundle"三元结构。与 handbook 冲突以 handbook 裁决记录为准。

---

## 一、系统总览：三仓四面

```
kokoro-web（Next.js/React 自研 UI+engine 状态机）
   │  browser 面（19 kind SSE，contract 生成）+ HTTP（messages/control/snapshot）
kokoro-session（业务归一层：入口表 resolve、消息真源、relay、HITL pause 台账）
   │  raw 面（18 kind）+ control 面（run.request/resume/cancel/steer）——redis streams
kokoro-agent（执行引擎：多租户 namespace 单轴、多 pod、可插拔）
   ▲
contract/spec/*.yaml（单源真理）→ generate.py → 14 镜像 → check.py 字节比对门禁
```

一句话数据流：**web 发消息 → session 解析入口出 RuntimeConfig → agent 装配执行、
全过程事件上 wire → session 落库转发 → web 折叠渲染**。

## 二、词汇法典（全栈十词）

| 词 | 唯一含义 | 落点 |
|---|---|---|
| state | LangGraph 图状态（messages/todos/files/scope） | agent `state.py` |
| scope | run 身份四元组（namespace/session/run/thread） | 同上 `RunScope` |
| ledger | 控制面账本（去重/租约/终态/token/用量/steer 信箱/工具结果缓存） | agent `storage/ledger.py` |
| context | 模型可见面组合（人格+skills；工具用法不在此——见 tools） | agent `orchestration/context.py` |
| **product/entry** | 顶层成品：用户面对的主人格，session 入口表一行或代码型配方 | session 入口表 + agent recipes |
| **subagent** | 内部工人：task 委派、无会话语境、单次进出 | catalog/wire/配置 |
| **bundle** | 成品能力束声明（tools 名集/skills/model 偏好） | session `EntrySpec`（数据；将来 hub） |
| **recipe** | 成品装配代码（仅当超出通用管线） | agent `orchestration/<type>.py` |
| **prompts** | 人格资产域（文本进 .py 即红灯） | agent `prompts/<type>.md` |
| steer | 运行中插话（信箱→模型轮前注入） | 契约 `run.steer` + ledger + middleware |

## 三、成品体系（music/video 的地基）

**本体论**：成品与子代理四维对立（面向谁/语境/生命周期/身份来源），形状相似绝不合并。
**对偶性定律**：成品被选中=主位（配方生效），未选中=自动降格为可委派子代理
（只投影声明束；wire_subagents 主 index 优先→注册表兜底已修通）。
**三元结构**：资产（prompts/）+ bundle（session 入口表=数据）+ 配方（orchestration/，可选）。

**新类型落地手册**（对 music 与 video 同构）：
1. 专属工具：`tools/<type>_*.py` 纯原语实现（description 携用法）→ 注册 `KOKORO_TOOLS`；
2. bundle：namespace profile `agents.<type> = {description, system_prompt, tools, model?}`
   （hub 化后为 hub 记录）；
3. 若需专属编排：`prompts/<type>.md` + `orchestration/<type>.py` + 契约加配方分派键（届时）；
4. web 零改动（渲染面通用）——**除产物预览外**（见下）。

**video/music 的硬前置=产物面**：媒体成品的产出不是文本。所以路线图重排（见六），
`tool.returned.artifact_ref`（契约位已留）+ 产物存储 + session 产物端点 + web 预览
从"等 canvas"升级为 music/video 的前置工程。形态已定：工具用
`content_and_artifact`（给模型摘要+完整产物分离，产物不烧上下文），落
`/artifacts/{run_id}/...`（state 虚拟盘/local_shell 真盘/e2b 后对象存储），
登记环节译成 artifact_ref 上 wire，session 出 HTTP 产物端点，web 按 MIME 渲染
（音频播放器/视频播放器/图像）。

## 四、运行时能力矩阵（现状全绿）

- **流式**：thinking/正文/todo/工具过程；子代理全程可见（subagent.tool.* 通道）。
- **HITL**：审批（approve/edit/reject）/提问（respond）/结果审核；子代理内同权
  （嵌套帧回退+review 下发）；凑齐才提交读契约 pending_tool_ids。
- **steering**：活跃 run 的 POST 落库转 `run.steer` → ledger 信箱 keep-first →
  模型轮前注入（稳定 id 幂等；正文通道只认 node=="model"，注入永不冒充 assistant）。
- **治理**：ToolPolicy fail-closed、Terminal/TokenBudget 守卫全链下发（含 GP 同名覆盖）、
  SSRF 防护、审批集政策注入。
- **韧性**：TTL 租约重拾、暂停收养、稳定 message_id 幂等重放、SIGTERM drain、
  单终态原子认领；用量跨段累计真源。
- **观测**：langfuse 全链 trace；审批卡 description=工具自述（wire 只带数据，文案归 web/zh）。

## 五、设计法则汇编（全部已裁定）

1. namespace 单轴（个人=personal 实例；跨空间=grant；任何第二身份轴=红灯）
2. 契约单源（spec→generate→check；optional=缺席省略，null 永不上 wire）
3. 政策装配注入（工具零租户/vendor 概念；scope/审批/预算/provider 在配方注入）
4. config 单点消费（env 只在 main 解析；orchestration 只收领域设置，架构法测试执法）
5. 诚实挂载（依赖不可用整个不挂，不设空壳）
6. 守卫下发（子代理链逐个下发，否则委派即旁路）
7. fail-loud（未知名/lock 失配/对齐失配即抛，绝不静默降级）
8. 初期不留兼容层（删旧换新，无垫片无双拼写）
9. wire 只带数据（展示文案归 web/zh；执行侧英文模板上屏=红灯）
10. 成品三元各归其家 + 对偶性检验句（"降格为子代理还能工作吗"）
11. prompt 文本不进 .py（prompts/ 资产域）
12. 工具用法活在 description（LangChain 经 schema 交模型，system prompt 零工具指引）
13. 拼装点只持有排序与组合（删一个工具只改一个文件）

## 六、路线图（以 music/video 为北极星重排）

1. **R-artifact（新首位，music/video 硬前置）**：content_and_artifact 工具形态 +
   artifact_ref 生产者（agent）→ session 产物存储与 HTTP 端点 → web MIME 预览。
2. **R-hub**：三级库（platform→namespace→entry）数据模型 + 上传下载 + skills 铺文件
   同步器（修 SkillMount.path 单机假设）+ `profile.subagents` 纯工人表（本体论文档缺口）。
3. **首个垂类成品（music）**：按三元手册落地——R-artifact 完成后即可开工；
   video 同构复用（多一档产物体积/时长治理）。
4. **R-retention**：分层 TTL（提案已备，半天量）。
5. 外部件不变：e2b（连带 skills 渐进披露回归）、response_format（等 job）、
   auth 成员模型（platform）。
6. 小尾巴：steer 投递失败 UI toast；动态 skills 尾部化（前缀缓存友好，
   context-layer-notes 已记方向）。

## 七、验证马具（全栈）

单测：agent 335 / session 152 / web 173（+双 tsc+lint）。
跨栈：e2e 32 项（含 steer 幂等）、chaos 双场景、trace 7 项。
真模型：26 项六场景（A 子代理+内部工具事件 / B thinking / C search / D skills /
E execute 审批 / F 运行中插话改变产出）。
UI：Playwright 主路径走查+截图。CI：四仓独立门禁。
