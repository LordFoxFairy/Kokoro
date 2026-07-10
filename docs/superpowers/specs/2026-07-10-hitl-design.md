# Kokoro HITL 通用化设计（待审）

状态：草案，未获认可
日期：2026-07-10
上级：`2026-07-10-agent-system-model.md`（运行层的"暂停原语"；interrupt/resume 皆历史 append，前缀天然安全）

## 0. 一句话

> 一切人机暂停 = 一次 HumanRequest（kind + schema + context + policy）；工具在**任意执行点**都能发起，不再只有"调用前审批"一个卡点；现状三种场景降级为预设形态，MCP elicitation 等新场景零成本接入。

## 1. 现状与缺口

已稳（保留不动）：pause 持久化、SSE 事件、decision_id 幂等 keep-first、pending 闸、快照恢复续跑（有跨栈 e2e）。
缺口：形态写死为三种（tool_approval / ask_user_question / result_review），且全部是"工具边界"卡点——**工具执行中途需要人**（OAuth 中途授权、验证码、长操作中途确认、MCP elicitation）没有通用通道，每加一种要手写一种。

## 2. 统一抽象

```text
HumanRequest
  request_id                  # 幂等锚（替代/统摄 tool_id 锚定，工具边界场景仍带 tool_id 关联）
  kind: approval | question | review | input
  schema                      # 期待回应的 JSON Schema（PendingPause.input_schema 已预留）
  context                     # 展示载荷：tool_name/args/risk/description/candidates…
  policy                      # allowed_decisions / （后续）超时与默认行为；可由 agent 包 manifest 声明

回应（resume 载荷）
  responses: [{request_id, decision?, value?}]   # value 按 schema 校验；approve/edit/reject/respond 是
                                                 # kind=approval/question 下的合法 decision 集
```

## 3. 工具侧原语（核心增量）

```python
# 任何工具内、任意执行点：
response = await request_human(kind="input", schema=OtpSchema, context={...})
```

- 实现 = 包装 langgraph 原生 `interrupt(payload)` / `Command(resume=value)`；挂起点由 checkpoint 承载（现状机制）。
- 调用前审批 = 框架在工具边界自动注入的 `kind=approval`（interrupt_on 声明面不变，来源 = permissions + agent 包 manifest.approval_tools）。
- `ask_user_question` 工具 = `kind=question` 薄封装；result_review = `kind=review`。
- **MCP elicitation** = server 的 elicitation 请求桥接为 `kind=input`（schema 透传）——协议标准场景直接落位。

## 4. wire / 事件 / web

- 事件统一为 `human.request`（kind 字段区分）；V1 兼容期保留既有三事件名做投影别名，session 读模型统一存 HumanRequest 形态。
- resume 契约：`run.resume{responses}`——现状 decisions 四型是其子集（迁移期兼容映射 tool_id→request_id）。
- web 一套渲染器：按 kind 分派 + **schema 驱动表单**（kind=input 按 JSON Schema 自动渲染）——新场景零前端开发。

## 5. 不变量（继承现状，全部保留）

挂起持久（进程死/浏览器关都不丢）；response 幂等（request_id keep-first）；同 run 多 pending 有序呈现；resume 只认当前 pending；恢复重放不复活已决请求；前缀安全（interrupt/resume 皆历史 append）。

## 6. 实施切分

- H1（与主线并行可后置）：`request_human` 原语 + 现状三场景改为预设形态（内部重构，wire 兼容）。
- H2：`kind=input` + schema 驱动表单（web）+ `run.resume{responses}` 契约演进。**迁移面明示**：session 的 pauses 存储现以 tool_id 为唯一锚（resolvePause 按其过滤），H2 需加 request_id 锚并兼容映射（tool 边界场景 request_id=tool_id），这是 session store 改动，不只是契约改动。
- H3：MCP elicitation 桥接；policy 超时/默认行为；manifest 审批策略。

## 7. 呈现协议（web 侧，打磨补充）

- **一 kind 一渲染器，schema 兜底**：approval/question/review 沿用现有三卡升级为 HumanRequest 渲染器；`kind=input` 用 **JSON Schema 驱动表单**（字段类型→控件映射：string→输入框、enum→单选、boolean→开关、array→多选；不认识的 schema 给原始 JSON 编辑器兜底）——新场景零前端开发的落点。
- **与预览联动**（见 preview spec §4）：write_file 审批卡内嵌内容预览（批前看到要写什么）；review 卡一键在 canvas 打开被审文件。
- **多 pending 呈现**：同 run 多个待决请求按序列出（队列可见），resume 可单条或批量提交（契约 responses 数组天然支持）；已决请求落为已决态卡片（决策+时间戳，可追溯不消失）。
- **过期/失效态**：run 已终态（如被 cancel）后仍挂着的请求卡渲染为失效态（不可交互，说明原因）——防"点了没反应"。
- 移动端：卡片纵向堆叠可用即可，canvas 联动降级为全屏预览（V1 不做专门布局）。

## 8. 不做

不做审批工作流引擎（多级审批/会签——那是平台后台域）；不做同步阻塞式 UI 长轮询（一切走既有 SSE+resume）。
