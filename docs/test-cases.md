# Kokoro 测试用例总表

四层验证体系，从快到慢、从免费到走钱。任何改动按影响面选层跑；发版前 L1–L3 必须全绿，涉及模型行为再加 L4。

一键入口：

```bash
# L1（三仓套件，各仓内跑）
cd kokoro-agent   && uv run pytest -q && uv run pyright && uv run ruff check .
cd kokoro-session && npm test && npx tsc --noEmit
cd kokoro-web     && npm test && npx tsc --noEmit

# L2+L3（确定性跨栈，需 redis:6379 + mongo:27017）
python3 scripts/verify-all.py

# L4（真模型，需 kokoro-agent/.env 真凭据，走钱）
python3 scripts/verify-all.py --real
```

---

## L1 单元 / 契约套件（秒级，无外部依赖*）

*store-mongo / transport-redis 检测到本机服务才跑，否则 skip 并显式标注。

| 仓 | 命令 | 覆盖域 |
|---|---|---|
| kokoro-agent（pytest ~411） | `uv run pytest -q` | 契约门禁（raw 18 kind 逐字段）、HITL 中间件（审批/问答/结果审核）、steering、subagent HITL 透传、supervisor、memory/skills/MCP 挂载、run-scope state、storage/streams（sqlite/mongo 同语义矩阵含 sandbox 绑定）、docker/e2b/custom 编排（连接器注册表+枚举覆盖守卫；resume 重连/keep-first）、统一配置树（yaml 摊平+env 覆盖+凭据禁入）、workspace S3 归档（minio 实测）、架构分层守卫、边界 pragma 审计、LocalFake 全链（`tests/e2e/test_local_fake_run.py`） |
| kokoro-session（vitest ~178） | `npm test` | 契约门禁（browser 20 kind + HTTP 形状）、relay 归一化、message.user 合成、control 裁决/幂等、SSE 续传、恢复扫描、store（memory+mongo）、transport（memory+redis）、namespace profile 解析（含 swarm 成员校验矩阵） |
| kokoro-web（vitest ~181） | `npm test` | reducer（20 kind 折叠幂等）、水合=全量回放语义、engine 状态机（开流/重连/adopt user id）、HITL staging、持久化、投影、UI smoke（session-shell 刷新重建线程） |

类型/静态：`pyright`（agent 0 error）、`tsc --noEmit`（session/web 0 error）、`ruff check`。

---

## L2 确定性跨栈 e2e（`scripts/e2e-v21-gate.py`，LocalFake，~1 分钟）

真 redis+mongo+双进程（session npm start + agent worker），LocalFake hitl 脚本：ask_user → write_file（审批+结果审核双暂停）→ 文本流。

**多底座同一套断言**：文件面默认 local（目录直读），`E2E_WORKSPACE_BACKEND=s3` 切 S3 归档档
（agent 写时归档 → minio → session S3 reader）；执行沙箱默认 local_shell，
`E2E_SANDBOX_BACKEND=docker` 切容器隔离档（execute 进容器、文件面留宿主）；两轴可组合（docker+s3 组合档）。minio 前置：

```bash
docker run -d --name kokoro-minio -p 9100:9000 \
  -e MINIO_ROOT_USER=kokoro -e MINIO_ROOT_PASSWORD=kokoro-secret \
  cgr.dev/chainguard/minio:latest server /data
```

| ID | 用例 | 预期 |
|---|---|---|
| E2E-01 | POST messages | 202 + receipt（run_id/user_message_id/assistant_message_id） |
| E2E-02 | 同 idempotency_key 重发 | 重放同 receipt，不开新 run |
| E2E-03 | SSE 合成事件 | session.created → run.created 领衔 |
| E2E-04 | **message.user 合成** | event_id=user_message_id，content=原文（事件史即线程真源） |
| E2E-05 | ask_user_question 暂停 | tool.awaiting_approval(kind=ask_user_question) |
| E2E-06 | 活跃 run 期间新消息 | 202 转 steer，归属活跃 run 同 assistant 占位 |
| E2E-07 | steer 幂等 | 同 key 重发同 receipt |
| E2E-08 | **steer 消息进事件史** | 第二条 message.user（event_id=steer message_id） |
| E2E-09 | snapshot 暂停点 | pending_pauses 恰 1 条 ask_user_question |
| E2E-10 | respond 提交 + decision_id 幂等 | 202/202；tool.returned(responded=true) |
| E2E-11 | write_file 审批暂停 | kind=tool_approval，allowed_decisions 含 approve 无 respond |
| E2E-12 | respond 用于审批工具 | 400 族拒绝 |
| E2E-13 | approve → 结果审核 | result_review 暂停带已执行 result，allowed=[approve,respond,reject] |
| E2E-14 | 审核 respond 替换 | tool.returned.result=替换文本 + responded=true |
| E2E-15 | 文本流与终态 | message.delta → message.completed → run.completed(completed) |
| E2E-16 | 终态 snapshot | active_run 清零、无 pending、assistant completed |
| E2E-17 | **snapshot.files** | 含 plan.md（mime=text/markdown，bytes>0，真目录 walk） |
| E2E-18 | **files 端点直读** | GET files/plan.md → 200 + 原文字节 + MIME |
| E2E-19 | **files 路径穿越** | `..%2F..%2Fetc%2Fpasswd` → 404 |
| E2E-20 | Last-Event-ID 续传 | 从中段续传只收水位后事件，拿到终态 |
| E2E-21 | **seq=0 全量回放（刷新水合语义）** | message.user ×2 + 全事件面可完整重建线程 |
| E2E-22 | 终态后新 run | 202 新 run_id 并跑到终态 |
| E2E-23 | entry=poet 具名入口 | wire 上人格 system_prompt + 其余预设为下属 + 租户 namespace |
| E2E-24 | entry 未知 | 400 unknown_entry |
| E2E-25 | run.cancel | 202 → run.completed(status=cancelled) |
| E2E-26 | 事件面覆盖 | 首连收齐 8 类核心 kind |

---

## L3 崩溃混沌（`scripts/chaos-verify.py`，ledger/checkpoint=mongo 生产跨 pod 形态）+ trace（`scripts/trace-verify.py`）

| ID | 用例 | 预期 |
|---|---|---|
| CH-01 | 认领 worker 在 HITL 暂停期间 SIGKILL | 另一 worker 心跳收养 control 流，resume 续走到终态 |
| CH-02 | session 进程在暂停期间 SIGKILL | 重启后 snapshot 暂停现场完好，审批续走到终态 |
| CH-03 | 双 session 实例（多 pod 形态） | B 实例跨读 snapshot（活跃 run+暂停点）、跨发插话归属同 run、跨发 resume 收敛终态 |
| TR-01 | HITL 暂停/恢复多执行段 | Langfuse 上同 session trace ≥2 且同 kokoro_run_id（langfuse:3310 可达才跑，否则 SKIP） |

---

## L4 真模型跨栈（`scripts/real-model-verify.py`，glm-5，走钱）

| ID | 场景 | 预期 |
|---|---|---|
| RM-A | 明令 task 委派 researcher 子代理 | subagent.started/finished、子代理文本流、子代理内工具事件成对且带 subagent_id |
| RM-B | 普通提问 | thinking.delta ≥1、message.completed 非空、token_usage 上 wire |
| RM-C | web_search 真调用 | tool.invoked/returned 且结果非错误（searxng 不可达则 SKIP） |
| RM-D | namespace 挂载 skill（sha256 lock） | 模型输出遵循 skill 标记约定 |
| RM-E | local_shell 下 execute 审批 | approve 后真 shell 输出回流 |
| RM-F | 运行中插话（steering） | 202 归属同 run，产出反映插话内容 |
| RM-G | 真模型 write_file 文件面 | 审批 → 落盘 → snapshot.files 含 note.md → files 端点回读原文 |

---

## L5 浏览器 UI 走查（真栈 + Playwright，视觉/交互终审）

栈：`KOKORO_WORKSPACE_ROOT` 同根 + LocalFake hitl（确定性）或真模型；session:3913 / web:3014。

| ID | 用例 | 步骤 | 预期 |
|---|---|---|---|
| UI-01 | 完整 HITL 轮 | 发消息 → ask_user 卡片选项答复 → write_file 审批批准 | 过程块实时展开：问答标记"已人工答复"、工具行 done、最终文本流出 |
| UI-02 | **run 完成后刷新** | UI-01 跑完 → 浏览器刷新 | user 消息 + 全部过程块 + 最终文本经 seq=0 回放完整重建，无空气泡 |
| UI-03 | **run 进行中刷新** | 暂停点（审批待决）刷新 | 待审批卡片恢复、可继续裁决走到终态 |
| UI-04 | 文件 chip → canvas 预览 | 展开 write_file 行点 plan.md chip | 右侧 canvas 打开，markdown 渲染真实内容（MIME/字节数正确） |
| UI-05 | canvas 文件树 | canvas 切"文件"tab | 工作区文件列表（路径+大小），点选切预览 |
| UI-06 | 运行中插话 | run 进行中输入框再发一条 | 消息立即上屏归属同轮，不开新气泡 |
| UI-07 | 本地 echo 对齐 | 发消息后观察 | 本地乐观消息与回放 message.user 不出现双份（receipt adopt） |
| UI-08 | 会话切换/新建 | 侧栏切换会话再切回 | 线程各自独立完整，无串台 |

存证要求：每次走查至少 1 张关键状态截图（walkthrough 铁律）。

---

## 已知边界（显式不在本表）

- e2b backend：编排结构就位（fake SDK 单测钉死生命周期语义），真栈行为待 key 复核；无 key 选 e2b 即 fail-loud。
- custom backend（ADR-010 BYO）：`pkg.module:factory` 引用自带实现，契约/加载/生命周期绑定已单测钉死；BYO 实现本身的正确性归其作者。
- state 盘档（backend=state）：诚实降级无文件面，snapshot.files=[]。
- trace-verify 依赖自托管 langfuse，默认 SKIP 不算失败。
