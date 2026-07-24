# Kokoro 通用引擎重塑 — 总执行规划

状态：规划稿（不碰代码，先规划到位）
日期：2026-07-24
收束自：`specs/2026-07-24-unified-plan-monetization-design.md`（Plan+卡密+三桶+懒刷新）、
`specs/2026-07-24-capability-and-studio-architecture.md`（v3 共同本质）、
`reports/2026-07-24-product-capability-inventory.md`（有/缺/不足）。

---

## 0. 北极星：一台通用引擎

```
意图 → GA 编排能力 → 调 kokoro-model 的模型(任意厂商/任意模态) → artifact → credit → namespace
```
唯二变量：**surface（Chat/Studio）× 模型**。其余恒定。**产品=配置，引擎=打磨对象。**

三个统一抽象：**GA(一个运行时) · kokoro-model(一个全模态模型注册表) · Plan(一个套餐抽象)**；credit/artifact/namespace 恒定。

---

## 1. 现状事实（已核，规划落在这上面）

- **强（引擎骨）**：GA run（流式/durable/HITL/checkpoint）、hub 能力装配、session/SSE、credit hold/settle、artifact 库、namespace/siteId 隔离、认证、部署。
- **model 域已多模态就绪**：binding schema 有 `featureKey/inputModalities/outputModalities/transportKind/provider/gatewayModelName`——**收全模态主要是加条目 + 媒体 transport，schema 基本不动**。
- **真缺的引擎链**：agent 侧只有 `make_chat_model`（LLM-only）→ **"调非对话模型（音乐/图片→artifact）"是要打通的核心新链**。
- **商业**：Plan/三桶/权益/卡密/订阅生命周期/懒刷新——全缺（设计已就绪）。
- **组织纵深**：workspace/project 未建。**风控**：零。**Studio/媒体能力**：零。

---

## 2. 目标架构分层（每层：具体改动 + 落哪个仓）

### L1 模型层 kokoro-model（收全模态）
- 加**媒体模型条目**（音乐/图片，各 provider + featureKey=music/image + modalities）。schema 已支持。
- 加**媒体 transport/adapter**：litellm 管 LLM；媒体走 provider 适配（Suno/Replicate/fal…），**统一"模型调用网关"口径**（凭据同 model key，只经 env/加密注入）。
- 产出：给上层一个"**按 label 解析→调用→得输出**"的统一模型调用面，不分模态。

### L2 能力层（GA 调模型的通用链）——**引擎核心**
- GA 加一类**通用能力"invoke_model(label, params) → artifact/message"**：解析 kokoro-model 的模型 → 经网关调用（对话=流式 message；媒体=provider job→artifact）→ 按 featureKey hold/settle → 产物入库。
- 媒体的异步由 **GA run 自身**承载（工具调 provider→等→deliver），**不建独立 job 服务**。
- 落 kokoro-agent（provider 适配在模型网关侧，GA 只"调某模型"）。

### L3 商业层 credit + Plan + 供给
- credit：**三桶**（每日/周期/永久）+ 消费顺序（过期先扣）+ **懒 materialize**（水位 CAS，非 cron）。
- **Plan 目录**：免费/积分包/订阅统一为 Plan；**权益层**（模型档位准入 + 消耗倍率 + 并发/优先级）。
- **供给三渠道**：直接支付 / 订阅 / **卡密兑换**（零支付集成，解无商户）。
- 落 kokoro-credit（桶/权益/Plan）+ kokoro-payment（交易/卡密/订阅生命周期，与支付分层）。

### L4 surface 层（通用 Chat + 通用 Studio）
- **通用 Studio 框架**：读配置 `{model_ref, 参数schema, 布局, featureKey, 产物类型}` → 控制面 → 组装 GA run → 预览/版本/导出。
- **Image/Music Studio = 各一份配置**；Chat = GA 自选能力（含媒体）→ **反哺自动**。
- 落 kokoro-web/apps/user（暖纸感设计系统）。

### L5 组织纵深 workspace/project
- 新实体 team→workspace→project；artifact/session/计费按 project 归属。落 kokoro-user/site + 各消费方。

### L6 运营 + 风控（上线前）
- admin 升"Plan 治理 + 运营看板（MRR/包收入/卡密兑换率/积分负债/漏斗）"；**风控/内容审核**（生成前后过滤）。落 platform-admin + agent/hub。

### L7 增长 + 设计系统（随产品成形）
- SEO/营销站生成、邀请裂变、埋点；@kokoro/ui 共享设计系统。

---

## 3. 依赖图 + 关键路径

```
L1 model 收全模态 ──► L2 能力调模型通用链(引擎核心) ──► L4 通用 Studio 框架 ──► Image Studio ──► Music Studio ──► 反哺 chat
                                     │
L3 credit 三桶/Plan/权益/卡密 ───────┴──► featureKey 计费接入(媒体)         L5 workspace/project ──► 产物按 project 归类
L6 风控 ──► 上线闸                                                        L7 增长/设计系统 ──► 增长
```
**关键路径**：L1 → L2 → L4 → Image Studio。L3 可与 L1/L2 并行；L5/L6/L7 相对独立后置。

---

## 4. 分阶段 roadmap（**先打通通用基本能力**，每阶段带验证）

### 阶段 A — 引擎通用链打通（最高优先，你的定调）
- A1 **kokoro-model 收一个媒体模型**（图片，先接 mock/单 provider）+ 媒体 transport。
- A2 **GA `invoke_model` 通用能力**：调该图片模型 → 出 artifact → 按 image featureKey hold/settle。
- **验证**：一次 GA run 调图片模型 → 真出 artifact + credit 扣减 + 隔离正确（真栈 e2e）。**引擎成立的铁证。**

### 阶段 B — 商业连贯（可与 A 并行）
- B1 credit 三桶 + 消费顺序 + 懒刷新。 B2 Plan 目录 + 权益层。 B3 卡密兑换。 B4 订阅生命周期(mock 支付下可跑)。
- **验证**：真栈——每日赠送惰性刷新扣减、卡密兑换到账、订阅权益 gating 模型、三桶按序扣。

### 阶段 C — 通用 Studio 框架 + Image/Music
- C1 通用 Studio 框架（配置→GA run→预览/版本/导出）。 C2 **Image Studio**（配置）。 C3 **Music Studio**（换音乐模型配置）。
- **验证**：Studio 参数→GA run→产物/版本；换配置即得另一 studio（"加配置不加代码"实证）。

### 阶段 D — 反哺 chat
- 能力已在 GA 池 → chat 里 GA 自选即用 + 空态引导。**验证**：chat "生成一张图" → 产物卡。

### 阶段 E — 组织纵深 / 阶段 F — 运营+风控 / 阶段 G — 增长+设计系统
- 按依赖后置；风控为上线闸。

---

## 5. 卡点（依赖你 / 明确记账）

1. **模型 key**：LLM 真 key（现 fake/ollama）+ **媒体 provider key**（音乐/图片）。给了即真；架构先用单 provider/mock 验证通用链。
2. **商业收口点**（货币化 spec §11）：消费顺序（我定过期先扣）、订阅=权益为主、USD 价值化——确认即锁。
3. **媒体能力形态**：GA 只"调 kokoro-model 的模型"、provider 适配在网关侧（我倾向，已随共同本质定）。

---

## 6. 打磨纪律

- 每层动手前发对齐单；每阶段收工贴真栈 e2e。
- 一切按"共同本质"落：不造 bespoke、不造平行服务；新垂类=配置。
- 现有机器**统一收编**（credit/payment/model/hub/artifact），加法迁移，不推倒。
