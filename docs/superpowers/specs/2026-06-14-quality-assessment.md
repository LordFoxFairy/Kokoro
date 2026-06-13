# Kokoro 三仓质量评估 — 维度评分 / 顶级差距 / 打磨到顶级的路径

> 定位:对 kokoro-agent / kokoro-session / kokoro-web 当前状态做一次诚实的整体评估。打分基准 = 同类顶级开源(agent UI / streaming chat / 事件驱动后端)的成熟度。
> 边界:用户明确——**不拓展功能,在现有基础上打磨到顶级,利于后续维护**。故"如何进一步"一节只谈打磨与固化,不谈新特性。
> 体量:agent 1439 src / 1849 test;session 1045 src;web 4576 src / 5399 test;14 份 spec。测试:源码比 agent 1.3:1、web 1.2:1。

---

## 1. 维度评分(1–10,基准=顶级开源)

| 维度 | 分 | 依据(强) | 差距(到顶级) |
|---|---|---|---|
| **契约 / 类型安全** | **9.0** | events.yaml 单源 + verify.py 门禁锁 6 镜像;zod/pydantic 两端 `.strict()`/`extra=forbid`;零 `any`/`cast`/`# type: ignore`;strict 生产 / 宽容消费的 Postel 纪律 | 无 codegen(手维 6 镜像,verify 拦漂移但不自动生成);phase-2 generator 一直 YAGNI 挂起 |
| **Stream / SSE 设计** | **8.5** | ordered-parts(seq 唯一排序源)+ segment 分段 + transport cursor 续订 + 确定性 event_id(重放幂等)+ skip-and-continue + 终态关流;交错 text→tool→text 正确分段 | 无背压/限流上限文档化;XTRIM 裁剪检测是 TODO;多 run 并发 UI 未做 |
| **Stream UI 交互** | **8.0** | A 连续性(共享气泡骨架)/B 可读性(重连状态条)/C 持久化(展开意图)/D 密度(chevron+失败聚合);a11y(inert/aria/focus-visible)+ reduced-motion;答案在上过程在下的成熟信息架构 | HITL 未接(下节);长 thread 无虚拟化(全量 DOM);工具失败 run 仍整体 fail(无工具级恢复) |
| **DDD / 架构分层** | **8.5** | 三仓统一 4 层(domain/application/infrastructure/interfaces);依赖倒置(Protocol/ports);domain 零框架泄漏;独立部署、仅经 redis+SSE 耦合 | application 个别无状态 infra helper 直接 import(已判 defensible) |
| **测试** | **7.5** | 133+76+221 单测 + contract 门禁 + SSE 回环门禁 + 7 轮对抗复核 + 测试用例总目录;红→绿 + 注入证非空洞 + 变异检验 | **无 CI 自动化**(门禁全手动跑);**无 Playwright e2e 套件**(浏览器验证是 ad-hoc);覆盖率无数字化追踪 |
| **代码整洁 / 可维护性** | **8.5** | 注释只写 WHY ≤1 行;死代码即删(D2 不可达就移除);对抗复核每轮抓"投机/空洞";四仓长期 0 dirty | 个别长文件(use-conversation 469 行)接近上限 |
| **文档** | **8.0** | 14 份 spec(stream 架构 / 测试目录 / 能力扩展 / 连续性设计 / 本评估);claude-progress 跨会话连续性 | 无面向新贡献者的 README/onboarding;spec 偏内部决策记录 |
| **可观测性 / 运维** | **5.0** | 结构化 logging;LOCAL_FAKE_MODEL 凭据无关 e2e;隔离 redis db 纪律 | **最弱项**:无 metrics/tracing;无 run-inspector;无健康检查/就绪探针;无部署清单 |

**加权总评:≈ 8.0 / 10。** 上半身(契约/架构/stream/整洁)接近顶级;下半身(CI/e2e 自动化/可观测性)是明显短板——而这正好全是**打磨项,不是新功能**,符合用户边界。

---

## 2. 与顶级仓库的差距(诚实)

顶级同类(Vercel AI SDK chat、LangGraph Studio、成熟 agent UI)与本仓的真实差距,**按"是不是打磨能补"分类**:

**A. 纯打磨能补(应优先,符合"不拓展功能")**
1. **CI 自动化**:本仓所有门禁(pytest/pyright/ruff、tsc/vitest/eslint、verify.py、sse-loopback-gate.sh)都已存在且全绿——但**靠人记得跑**。顶级仓库这些在 PR 上自动跑。补一个 `.github/workflows` 把现有门禁串起来 = 一次性、零新功能、维护性巨大提升。
2. **Playwright e2e 套件**:我这些天的浏览器验证(交错渲染/重连条/展开持久/工具失败红色)全是 ad-hoc 注入 + 截图。顶级仓库把这些固化成可重跑的 Playwright 套件。把已做过的流程**编码成测试**,不是新功能。
3. **覆盖率数字化**:已有海量测试但无覆盖率门槛。加 `pytest --cov` / `vitest --coverage` 的阈值,把"测得多"变成"可证明测得够"。

**B. 半打磨(架构已留缝,需小幅落地)**
4. **工具级错误恢复**:当前一个工具抛异常 → 整个 run fail(本轮 tool-error 已让失败工具显红,但 run 仍死)。顶级 agent 让模型看到工具错误、继续。缝在 deepagents 的 tool-error 配置 / 工具包裹——是落地而非发明。
5. **可观测性**:事件流**本身就是 trace**(seq + event_id + 时间戳齐全)。把它暴露成一个只读 run-inspector(读 replay stream)= 用已有数据,不新增采集。

**C. 真·新功能(用户明确不在本轮范围)**
- HITL(下节只谈设计落点)、teams 多 agent、workspace 持久工件、auth/多租户、thread 虚拟化。这些是 capability,记在 `2026-06-12-capability-extension-design.md`,**本轮不做**。

---

## 3. Stream Event UI 设计评估

**强(已达成熟):**
- **信息架构正确**:一 turn 一头像 + 竖脊 + 按 segment 分段、答案气泡在上、催生它的过程(思考/工具/子代理)收成更轻的可折叠块挂在下面。这是 ChatGPT/Claude/Perplexity 同源的成熟范式,且用户主动选了"过程在下"(answer-first)。
- **交错 text→tool→text 正确**:分段归属(工具挂在它产出的那段答案下)+ ordered-parts(seq 真实时序)+ 三相位(forming→streaming→settled)都钉死了测试。第三段流式时:前段落定气泡、尾段流式气泡+光标、工具在其下、过程块默认展开。
- **转场连续**(A):forming/streaming/settled 共享同一气泡盒、首 token 不跳盒;过程块 grid 高度呼吸;摘要交叉淡入。
- **状态永远可读**(B):重连有半截正文时也有 turn 级「重连中…」脉冲条;空窗回落成形态。
- **尊重用户**(C):展开意图按 segmentId 持久化跨刷新。
- **密度可辨**(D):chevron 区分可展开/静态;失败聚合「N 个工具(K 失败)」。
- **a11y/动效到位**:折叠内容 inert 移出无障碍树;focus-visible 暖木环;prefers-reduced-motion 全局退化。

**待打磨(非新功能):**
- **长 thread 性能**:无虚拟化,几百条消息会全量挂 DOM。打磨项:react-window 类虚拟化(纯性能,不改交互)。
- **工具失败的 run 体验**:失败工具显红 ✓,但 run 整体 fail——见 §2.B4。
- **HITL 的 UI 占位**:见下节。

**整体观感:** stream UI 已是"精心打磨过"而非"能跑就行"——转场有呼吸、状态有锚点、a11y 不糊弄。距顶级就差**长列表性能**和**自动化回归护栏(Playwright)**两块,都是打磨。

---

## 4. 能力的设计落点(只谈架构缝,不实现)

用户问的"工具执行前暂停 → 确认 → 恢复"(HITL)等能力,关键是**现有架构是否留好了缝**,以利后续维护时低成本接入。诚实盘点:

**HITL(工具执行前暂停/确认/恢复)——缝在哪:**
- **反向通道是当前唯一缺口**。现在数据流是单向 `web → POST /runs → agent → 事件 → SSE → web`。HITL 需要**运行中**的 web→agent 信令(批准/拒绝)。
- **已留的缝**:`2026-06-12-capability-extension-design.md §7` 已设计:per-run control stream(`kokoro:run:<id>:control`,redis)+ `POST /runs/:id/control` + agent worker 在 astream 循环间隙非阻塞 xread + deepagents `interrupt_on=` + checkpointer。
- **前置打磨(本轮可做的、利于将来接 HITL 的地基)**:
  1. 事件契约已能表达"等待确认"——加一个 `tool.awaiting_approval` kind 走现成的新-kind SOP(events.yaml→verify→session→web 7 步),UI 用现成的工具行红/黄态渲染。**这是契约打磨,不是功能**。
  2. deepagents 已暴露 `interrupt_on=` + `checkpointer=`(源码确认),但需 checkpointer 选型(与 workspace 持久化一起决策)。
- **结论**:HITL 不是"要不要现在做",而是"地基(control stream + checkpointer)是个明确的、已文档化的缝"。本轮**不实现**,但评估为"架构已为它留好位置,后续接入是落地不是重构"。

**其余能力的缝**(同 capability spec,均"已有挂点/留缝"):自定义工具(X1 已落,链路零改动)、teams(传输层多 run 已就绪,缺 UI 编排)、workspace(deepagents 虚拟 fs + envelope 预留字段,缺取回端点)。

**维护性视角**:这些能力都不需要推翻现有架构——契约单源 + 分层 + 新-kind SOP 让"加一种事件/能力"是例行公事。这本身就是顶级架构的标志(扩展点清晰、改动可预测)。

---

## 5. 如何进一步打磨到顶级(排序,全是打磨非功能)

按"投入小 / 维护性收益大"排序:

1. **CI 门禁自动化**(P0,半天):`.github/workflows` 串起三仓 pytest/tsc/vitest/ruff/eslint + verify.py。一次性,杜绝"忘了跑门禁"的回归。**最高 ROI 的维护性投资**。
2. **Playwright e2e 套件**(P0,1–2 天):把这些天 ad-hoc 的浏览器流程(交错渲染/重连/展开持久/工具失败/SSE 主路径)编码成可重跑套件 + playwright.config。让 UI 回归自动可证。
3. **覆盖率门槛**(P1,半天):pytest-cov / vitest coverage + 阈值,把"测得多"变"可证明够"。
4. **工具级错误恢复**(P1,1 天):deepagents 配置/工具包裹让单工具失败不杀整 run(已显红,补恢复)。
5. **run-inspector(只读可观测)**(P2,1 天):读 replay stream 暴露一个 run 事件时间线视图——用已有数据,零新采集。
6. **长 thread 虚拟化**(P2,1–2 天):react-window 类,纯性能。
7. **新贡献者 README/onboarding**(P2,半天):三仓启动 + 门禁 + 架构图,降低维护门槛。

**做完 1–3,总评从 8.0 → 8.7+**(测试维度 7.5→9,可观测性起步);做完 4–7 摸到 9.0,即"顶级且易维护"。**全程零新功能,纯固化与打磨**,完全符合用户边界。

---

## 6. 一句话结论

Kokoro 的**内核(契约/架构/stream 模型/UI 交互/整洁度)已经是顶级水准**——这部分这些天经 7 轮对抗复核打磨过,扎实。距"顶级仓库"的差距**几乎全在工程化外围(CI/e2e 自动化/可观测性)**,而这些恰好都是**打磨项而非新功能**,且每一项都利于后续维护。优先级清晰:先把已有门禁自动化(CI + Playwright),内核已经不需要大动。
