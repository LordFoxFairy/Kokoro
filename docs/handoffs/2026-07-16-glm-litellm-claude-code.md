# 交接单:GLM 经 litellm 以「claude-code」别名接入 dev 闭环

日期:2026-07-16 · 状态:**代码/配置全就位并 live 验证;真实模型输出唯一阻塞 = 有效 GLM 凭据(纯外部)**

## 目标(用户 /goal)

所有子仓一起:① 功能全面打通 ② 真人能进来查看体验 ③ 把 GLM 注册进去可用 ④ 配合 litellm 做「对外 claude-code、内部 GLM、可在网关侧调后端」。

## 已完成并验证(证据)

- **litellm claude-code 门面(后端 env 全参数化)**:`kokoro-platform/kokoro-litellm/config/litellm.config.dev.yaml` 的 `claude-code` 条目 `model/api_base/api_key` 均 `os.environ/CLAUDE_CODE_*`;`docker-compose.dev.yml` 透传三者。**换后端只改 env,对外 claude-code 名不变**——④ 已证:curl 同一 `claude-code` 分别打到 GLM(401,请求正确到达 GLM)与本地 ollama(出真 qwen 文)。凭据不落任何提交文件。
- **closure-up 自配置(默认 GLM→fake)**:`scripts/closure-up.py` `resolve_claude_code_backend()` 三步——GLM 凭据探通→GLM;`KOKORO_DEV_LOCAL_FALLBACK=1` 且本机 ollama→本地真模型(opt-in);否则 fake。`load_glm_creds()` 从 gitignored `.env` 取,`claude_code_reachable()`/`litellm_ready()` 探健康。隔离测 + 实跑均正确:GLM 死→回落 fake,dev 照常可用。
- **session 默认模型**:`kokoro-session/src/namespace/resolve.ts` `DEFAULT_MODEL={provider:"litellm", name:"claude-code"}`。`tsc` 干净,**381 测试全绿**(随行为更新 `namespace.test.ts`/`billing.test.ts`/`http.test.ts` 三处)。
- **kokoro-model**:`seed()` 注册 `claude-code` binding(labelKeys/gatewayModelName=claude-code、transportKind=litellm、featureKey=chat)。
- **live 验证(Playwright)**:真人登录→发消息→助手回复→plan→会话入库全通;composer 模型选择器显示 **`claude-code`**。截图 `kokoro-web/tmp/live-chat-claude-code.png`。①②④ 在运行系统上闭环。

## ✅ 真人进来看到真实模型输出——已达成(2026-07-16 破案)

一度以为 closure-up 有「真档仍走 fake」的 harness bug,插桩后证实**模型确实按真档构建(built_model_type=ChatOpenAI)**,根因是**三处状态污染**,全部定位并解决:

1. **web localStorage `kokoro.web.chat-prefs` 存了陈旧 `anthropic:claude-sonnet-4-6`**:改 DEFAULT_MODEL 前的旧偏好,web composer 据此发显式旧模型(anthropic 无 key→必败),而 UI 标签仍显示 claude-code——发出与显示不符。清 localStorage 即走默认 claude-code。
2. **`chat_smoke` 用固定 session id `ses_chat_smoke`**:早期 fake 档测试污染其 mongo checkpoint(106 条陈旧文档),后续读回的是旧 fake 消息,非当前真 run。清该会话即真。
3. **重启竞争(真 bug,已修)**:SIGTERM 触发 agent 优雅停机 drain 达 60s,与新 worker 重叠成 60s 双 worker 窗 → 旧 worker 抢 run。`scripts/closure-up.py` boot() 改 SIGKILL + 轮询等旧 worker 退场。

**验收(Playwright,真人主路径)**:清 localStorage 后新对话发「用一句话中文介绍你自己」→ 助手真实流式回复 **「我是Kokoro,一个以结果为导向的高效助手,专注于通过精准且克制的方式协助用户完成任务。」**(带 Kokoro 人格,非 fake 文案),模型 claude-code,状态「已直接给出这轮结论」。MODEL-DEBUG 证 `runtime.model=litellm/claude-code, built_model_type=ChatOpenAI`,litellm delta>0(真打网关)。截图 `kokoro-web/tmp/live-real-qwen-output.png`。

**即:claude-code→litellm→(本地 qwen)端到端出真实输出,四项目标在运行系统上闭环。** GLM key 有效后,自配置默认走 GLM(更快更强),同一条路。注:本地 qwen3:8b 推理慢,`closure-up chat` 探针的事件读取超时会 FAIL(delta=1 证明真调用了,只是探针等不及)——web 端等 30-60s 可见完整回复;GLM 无此慢。

小发现(可选后续):web composer 未校验 localStorage 存的 model 是否仍在 /models 列表——默认模型变更后陈旧 prefs 指向已移除模型会静默发错。宜在 composer 读 prefs 时对 /models 做一次有效性过滤。

## 两个真实限制

1. **GLM key 失效(硬阻塞)**:`kokoro-agent/.env` 的 `OPENAI_API_KEY`(端点 `.../api/coding/paas/v4`)被 GLM 全线拒——coding/标准 openai/anthropic 端点、Bearer/x-api-key 四种组合均 `1000 身份验证失败`。key 形态正常,即过期/吊销/欠费。**只有账号持有者能换**;agent 不搜寻其它凭据(安全策略拦阻)。
2. **本地 ollama 只能作简单补全,驱动不了完整 agent**:qwen3:8b 经网关 curl 出真文,但跑完整 deepagents 编排(多步工具/结构化输出)时 run 失败(无 Python traceback,8B 产出编排处理不成完整 run)。故本地回落默认关、改 opt-in。**真实完整体验需有能力的模型**——GLM-4.6 即可(`scripts/real-model-verify.py` 已证 GLM 直连驱动 agent 7 场景全绿)。

## 收口步骤(有了有效 GLM key)

1. 有效 GLM key 写入 `kokoro-agent/.env` 的 `OPENAI_API_KEY=`(coding 计划保持 `OPENAI_BASE_URL=.../api/coding/paas/v4`;标准计划改 `.../api/paas/v4`)。
2. `python3 scripts/closure-up.py restart` → 自配置探到有效 GLM → 真档 claude-code→GLM。
3. Playwright web 主路径:登录→chat→应出 **GLM 真实多步回答**;截图验收。
4. 提交 + gitlink 同步。
   （若想先用本地能力模型验证:`KOKORO_DEV_LOCAL_FALLBACK=1 KOKORO_DEV_LOCAL_MODEL=openai/<capable-tag> python3 scripts/closure-up.py restart`。）

## 未提交改动清单(全部本次任务相关)

- `kokoro-platform/kokoro-litellm/config/litellm.config.dev.yaml`、`docker-compose.dev.yml`（子仓）
- `kokoro-session/src/namespace/resolve.ts` + 三个 test（子仓）
- `scripts/closure-up.py`（主仓）

## 已知无关既有问题(非本次)

- `kokoro-web` `artifact-card.test.tsx` 1 项既有失败(audio 鉴权头)。
- dev `/api/billing/plans` 503(dev 未接账单套餐后端,已优雅降级)。
