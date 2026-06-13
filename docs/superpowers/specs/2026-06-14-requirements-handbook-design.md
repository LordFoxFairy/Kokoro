# 需求手册设计 — `docs/requirements/`

> 定位:为 Kokoro 建一套**工程可验证的真实 PRD**,从「为什么做」一路贯到「怎么保证做对」。
> 起因:`docs/product/` 描述的是**静态原型时代**产品(canvas 生成器矩阵,仅原型),而真实造出来的是**三仓 stream 聊天系统**(kokoro-web 聊天壳 + agent 活动流)。两者已漂移。一份「完美的需求手册」不能建立在过时的产品形态上。
> 用户拍板:① 新建 `requirements/` 层,`product/` 作为愿景/设计层保留不动;② **「新的」**——既有文档只作参考,不继承其过时内容;③ 分层清晰,产品愿景 ↔ 工程实现两者兼顾。

---

## 1. 文档版图与定位

| 文档体 | 角色 | 本手册如何对待 |
|---|---|---|
| `docs/product/` | 产品愿景 / 设计语言(原型时代,部分过时) | **参考**,链接引用,不复制、不修改 |
| `docs/decisions/` (ADR ×9) | 已锁决策 | **引用为权威**,需求层链回 ADR |
| `docs/protocol/` (5 份) | 跨仓契约(当前、准确) | **契约层指向它**,不重写 |
| `docs/superpowers/specs/` (15 spec + 测试总目录 + 质量评估) | 工程设计 spec(当前、准确) | **引用为实现真相**,契约/流程层链接 |
| **`docs/requirements/`(本手册)** | **真实 PRD:系统必须做什么 + 如何验收** | 新建,单一真相围绕真实系统 |

核心原则:**requirements/ 是「需求 + 验收」的单一入口,不与既有文档双向维护**。凡契约/实现细节,链过去,不抄过来(避免漂移——用户最恨兼容/重复)。

## 2. 四层结构

```
docs/requirements/
├── README.md              总索引 · 新增规范 · 状态约定 · 文档版图
├── _TEMPLATE.md           新增文档模板(强制 frontmatter)
│
├── 00-product/            【产品层】为什么 / 给谁 / 做成什么样
│   ├── vision.md            产品定位 + 北极星(链 ADR-001/004)
│   ├── users-and-jobs.md    T0 用户 + 核心 JTBD
│   ├── scope-and-boundary.md  ★已建 / 已设计 / 已规划 三态边界
│   └── trust-modes.md       Plan/Default/Auto 信任档位(链 ADR-003)
│
├── 01-capabilities/       【能力层】系统必须能做什么(静态能力域)
│   ├── conversation.md      会话:发起 / 续接 / 多会话
│   ├── agent-activity.md    活动流:todo / 工具 / 子代理 / 思考
│   ├── streaming.md         流式呈现:连续性 / 分段 / 首 token 不跳
│   ├── resume.md            中断恢复:重连续传 / replay 幂等
│   ├── tools.md             工具接入:内置 + 撞名守卫 + 错误呈现
│   └── extension-points.md  扩展位:workspace / teams / HITL(留缝,未建)
│
├── 02-flows/              【流程层】端到端业务流程 + 验收
│   ├── README.md            流程索引 + 验收规范(每流程映射 ≥1 测试)
│   ├── send-and-stream.md   发送 → 流式作答 → 落定
│   ├── interrupt-resume.md  刷新/瞬断 → 重连续传
│   ├── tool-run.md          工具调用 → 渲染 → 错误
│   ├── multi-conversation.md  多会话:新建/切换/删除/持久化
│   └── degrade-and-reject.md  降级与严格拒收(后端缺席/脏事件)
│
└── 03-contracts/          【契约层】怎么保证(薄桥,不重写)
    └── index.md             需求 → protocol / specs / test-catalog 映射索引
```

### 分层理由
- **产品层 ≠ 能力层 ≠ 流程层**:产品层是「为什么/给谁」(决策前提),能力层是静态「能做什么」,流程层是动态「端到端路径 + 验收」。三者读者用途不同,分开才清晰(用户要的「两者兼顾,分层清晰」)。
- **契约层是薄桥**:protocol/ 和 specs/ 已写好契约,03-contracts 只做**需求↔契约↔测试的映射表**,杜绝双向维护。

## 3. 新增规范(「以后新增的都在这里如何」)

### 3.1 强制 frontmatter
每个 doc 顶部:
```yaml
---
status: 🟡 草稿        # 🟢 已定 / 🟡 草稿 / 🔴 待用户拍板
layer: capabilities    # product / capabilities / flows / contracts
owner: claude          # 谁起草
updated: 2026-06-14
refs:                  # 链到 ADR / protocol / spec / test slug
  - ADR-003
  - test:web-send-message
---
```

### 3.2 三态状态(沿用 product/ 的成熟约定)
- 🟢 **已定**:ADR 锁定或用户拍板,改动需新 ADR
- 🟡 **草稿**:已起草,等审阅
- 🔴 **待用户拍板**:只有问题清单,需用户输入

### 3.3 新增流程
1. 判断归层(产品前提→00 / 能力域→01 / 端到端→02 / 契约→03)
2. 复制 `_TEMPLATE.md`,填 frontmatter
3. 在对应层 README 的索引表注册一行
4. 流程层文档**必须**在 `refs` 写 ≥1 个 `test:<slug>`(指向测试总目录);缺测试 → 标 🔴 并入 item 3 缺口

### 3.4 验收锚点
- 流程层每条 Given/When/Then 验收,映射测试总目录(`docs/superpowers/specs/2026-06-13-test-case-catalog.md`)的 62 条 slug(web 30 / session 15 / agent 17)。
- item 3「完美测试用例」反向消费本手册流程层的缺口标记。

## 4. 真实系统快照(手册内容的事实基线)

来源:`2026-06-11-stream-event-architecture-spec.md` + 测试总目录,逐条核准,非记忆编造。

- **三层流**:agent(Python,13 kind 原始执行事件,per-run 单调 seq + segment_id,写 redis run-events)→ session(TS,归一化 AGUI 信封 + 去重补归属 + replay + SSE fan-out + Last-Event-ID 续订)→ web(React,strict 解析 → reducer 折叠有序 thread → 渲染)。
- **标识符**:seq(唯一领域排序源)/ stream_id(传输游标 + 续点)/ segment_id(一段输出统一 id)/ event_id(`evt_{run_id}_{seq}_{event}` 确定性派生,重放幂等)。
- **不变量**:strict 拒收(zod/pydantic)/ 畸形 fallback(skip-and-continue 不杀循环)/ 幂等去重 / 终态关流。
- **scope 三态**:已建 = 三仓 stream 聊天 + agent 活动流;已设计 = canvas 创作矩阵(仅原型 product/);已规划 = tools(已通)/ workspace / teams / HITL(留缝)。

## 5. 边界(不吞 item 3/4)
- **不吞 item 3**:流程层只**引用**测试总目录,item 3 再打磨/补齐用例。
- **不吞 item 4**:契约层只**指向**架构 spec,item 4 再做 monorepo 等架构打磨。

## 6. 验收(本手册自身)
- [ ] 四层目录 + README + _TEMPLATE 落地
- [ ] 每个 doc 有合规 frontmatter,无 placeholder
- [ ] 所有交叉引用(ADR / protocol / spec / test slug)真实存在
- [ ] 流程层每条映射 ≥1 个测试 slug
- [ ] scope-and-boundary 三态分界与真实代码一致(不写未建的当已建)
