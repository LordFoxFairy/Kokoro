# Langfuse 可观测性接入设计

> 定位:给 kokoro-agent 的 LLM/工具/子代理执行接 [Langfuse](https://langfuse.com) 链路追踪。质量评估里可观测性是最弱项(5.0);这是第一步。
> 用户拍板:路线图「先 langfuse」。**opt-in**,云默认 + 自托管可覆盖。

## 为什么在 agent

LLM 调用都发生在 agent(DeepAgents/LangGraph/LangChain)。Langfuse 有原生 LangChain
`CallbackHandler`,经 LangGraph 自动传播到所有 LLM/工具/子代理调用——最低侵入、最全覆盖。
session/web 只转发事件,不发起 LLM,无需接。

## 实现(已落地)

- **依赖**:`langfuse` 4.7.1(`UV_NO_CONFIG=1 uv lock` 官方源锁)。
- **`infrastructure/observability.py`**:`build_langfuse_handler() -> CallbackHandler | None`。
  缺 `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` 任一即返回 None(tracing 关)。HOST 默认
  Langfuse Cloud,自托管设 `LANGFUSE_HOST`。
- **`application/run_agent.py::trace_config(req)`**:handler 在则返回 `{callbacks:[handler],
  metadata:{langfuse_session_id, langfuse_tags, kokoro_run_id, kokoro_conversation_id}}`,否则 None;
  经 `astream_events(config=...)` 注入。`_StreamingAgent` 协议加 `config` 参。
- **opt-in 即零兼容兜底**:未配置 → config=None → LangChain 默认无 callbacks → 行为完全不变
  (140→145 pytest、pyright 0、ruff 净、SSE gate 不受影响)。

## trace 关联

- `langfuse_session_id = req.session_id` → 同一会话多轮 run 归到一个 Langfuse session。
- `langfuse_tags = [execution_style]` → 按 fast/thinking 过滤。
- `kokoro_run_id` / `kokoro_conversation_id` → 与事件流(seq/event_id)交叉对账。

## 验证

- `test_observability.py`(5 例):env 缺/半缺 → None;配齐 → 建 handler(mock langfuse 不触网);
  trace_config 未配置 None / 配置后元数据正确。
- 真实启用冒烟:配 key 起 worker 跑一轮 → Langfuse 看板出现 trace(需用户凭据,未在本轮跑)。

## 边界 / 后续

- 本轮只接 agent 的自动 trace。手动 span/score、prompt 管理、session/web 侧指标 = 后续。
- 不接 LangSmith(路线图「先 langfuse」);如需可同模式加第二 handler。
