# 阶段 A（引擎通用链）+ L3（商业）详细规划 — 到接口/数据模型级

状态：详规稿（不碰代码；深化 master-plan 的 A 与 L3）
日期：2026-07-24
上游：`plans/2026-07-24-universal-engine-master-plan.md`、`specs/2026-07-24-*`

---

# 阶段 A：引擎通用链「GA 调 kokoro-model 任意模态模型 → artifact → featureKey 计费」

**A 的意义**：证明"能力调模型"这条通用链对**任意模态**成立。成立=引擎成立，Studio/Chat 皆配置。
**能拆两条腿并进**：A-LLM（DeepSeek 真云模型，验计费+真用量）｜ A-媒体（先 mock 图片 provider，验产 artifact 链）。

## A1 · kokoro-model 收全模态（schema 已就绪，主要加数据 + 媒体 transport）

现状事实：binding 已有 `featureKey / inputModalities / outputModalities / transportKind / provider / gatewayModelName`。

- **加 transportKind**：现有 `litellm`（LLM 流式）。加 `media`（媒体 provider 适配，可同步或 job 式）。
- **注册媒体模型**（示例）：
  ```
  label  image-gen   featureKey=image   in=[text]  out=[image]   transport=media   provider=<mock|openai|replicate|fal>
  label  music-gen   featureKey=music   in=[text]  out=[audio]   transport=media   provider=<mock|suno-like>
  ```
- **provider 凭据**：同 model key 口径（env/加密注入，绝不入库），归 model 域。
- 产出：kokoro-model 给上层一个**不分模态的"按 label 解析→拿到调用描述符"**的面。

## A2 · 统一模型调用网关（litellm 之于 LLM，媒体同理）

- **LLM**：litellm 网关（现成，claude-code 别名→后端；已接 DeepSeek）。
- **媒体**：网关侧加**媒体 adapter**——litellm 原生覆盖的（如 OpenAI images）直接走；不覆盖的（Suno 类）写薄 adapter，**统一归一成"媒体调用"**。
- **异步**：媒体耗时 → adapter 内 poll/webhook，对上层呈现"一次调用得结果"；GA run 自身承载等待（无独立 job 服务）。
- 口径：上层只认"调 label"，网关按 transport/provider 分派。

## A3 · GA `invoke_model` 通用能力（引擎核心新链）

一个统一签名，对话/媒体同构：
```
invoke_model(label, params, *, namespace, run_id) -> Output           # Output = message | artifact
  1. resolve  = model.resolveBinding(label, featureKey)               # provider/gateway/transport/out-modality
  2. hold     = credit.hold(namespace, featureKey, estimate, run_id)  # 按 featureKey 费率(+订阅倍率,见 L3)
  3. invoke:
       chat  -> litellm 流式 -> message tokens(现有)
       media -> 网关 media adapter -> 媒体结果(bytes/url)
  4. output:
       chat  -> message
       media -> deliver 成 artifact(内容寻址, 进产物库)
  5. settle   = credit.settle(hold, actualUsage)                      # 用量单位见 A4
  6. return Output
```
- **对话**：即现有 run 的模型路径（DeepSeek 已通）。
- **媒体**：GA 的一个**工具**（`generate_image`/`generate_music` = invoke_model 的封装）；Chat 里 GA 自选、Studio 参数直给，**底下同一 invoke_model**。
- 落 kokoro-agent（provider 适配在网关侧，GA 只"调 label"）。

## A4 · credit settle 泛化：用量单位按模态（关键，接 L3）

现状：settle 吃 token_usage（对话）。泛化为**统一"用量"**：
```
UsageUnit = { kind: tokens|images|seconds|tracks, input?, output?, count? }
计费 = 单位数 × featureKey 费率(× 订阅倍率) → ceil 到整积分(现有)
```
- 对话：tokens（现有，DeepSeek 报 usage → 真扣）。
- 图片：张数 × 图片费率。音乐：秒/首 × 音乐费率。
- pricing 规则加 image/music featureKey（成本地板 + 定价，见 L3/货币化 spec）。

## A 的验证（真栈 e2e）
- **A-LLM**（现在就能，DeepSeek）：对话 run → run.completed → settle 按真 token 扣减 → ledger model_call 带 run_id。
- **A-媒体**（mock 图片 provider）：GA `generate_image` → 出 artifact + 按 image featureKey 扣减 → 隔离正确。
- **两条腿都绿 = 引擎通用链成立**（对话 + 产 artifact 的媒体，同一 invoke_model）。

---

# L3：商业（credit 三桶 + Plan + 权益 + 供给三渠道 + 懒刷新）

## L3.1 · credit 三桶 + 消费顺序 + 懒 materialize

**数据（CreditAccount 扩展，加法）：**
```
daily_micros, daily_reset_on(date)      # 每日桶(免费/订阅赠送, 每天重置)
period_micros, period_reset_on(date)    # 周期桶(订阅月度, 每月重置)
permanent_micros                        # 永久桶(积分包/欢迎, 不过期)
```
**接口：**
```
ensureAllowancesFresh(account, plan, now)   # 入口先调:daily_reset_on<today→CAS 重置 daily=plan.每日额度; period 同理
hold(namespace, featureKey, estimate, run_id) -> holdId   # 预扣, 顺序 daily→period→permanent(过期先扣)
settle(holdId, usageUnits)                                # 终扣, 差额释放; 从各桶按序结算
balance(namespace) -> {daily, period, permanent, daily_reset_on, period_reset_on}
```
- **消费顺序**：过期最快先扣（daily→period→permanent），护用户价值。
- **懒刷新**：非 cron；水位 CAS（与"单 active run 准入"同纪律）；重置非累加。
- **ledger**：只记永久桶钱(买包/退款/卡密)+ 真实消费(settle)；每日/周期刷新是易逝状态不逐条记。

## L3.2 · Plan 目录 + 权益层

**Plan（新权威实体，收编积分包 seed + 定价规则）：**
```
Plan { id, name, type: free|credit_pack|subscription,
       price{ amount, currency=USD }, billing: one_time|monthly|none,
       grant{ credits_permanent?, credits_monthly?, credits_daily? },
       entitlements{ model_tiers[], multiplier, concurrency, priority, quota_micros },
       display{ order, badges } }
AccountPlanState { free(恒), packs[](已购), subscription?{ plan, period_start, period_end, next_renewal, ent_snapshot } }
```
**权益解析（横切,接引擎）：**
```
resolveEntitlements(account) -> { allowed_model_tiers, multiplier, concurrency, quota }   # 生效订阅 + 免费默认
```
- **run 受理**：校验 invoke 的 model tier ∈ allowed_model_tiers（免费=基础模型；订阅=高级）→ 否则 402/403。
- **计价**：hold/settle 乘 multiplier（订阅更便宜）。
- **调度**：concurrency/priority 作用于 agent run 并发（L2/agent 侧）。
- **配额**：quota 抬高月度上限（现有 quota 机制）。

## L3.3 · 供给三渠道（都→credit 桶，正交）

| 渠道 | 触发 | 授予 | 落点 |
|---|---|---|---|
| 直接支付 | 买积分包 | 永久桶 | payment(现有一次性)→credit grant |
| 订阅 | 月费 | 周期桶 + 权益(+可含每日) | 订阅生命周期→credit + entitlement |
| **卡密** | 输码兑换 | 永久桶(积分加量包) | 卡密兑换(零支付集成)→credit grant |

## L3.4 · 订阅生命周期（与支付分层）

```
Subscription 状态机: active[period_start,period_end] → (续费)active' | (到期)expired→落回免费权益 | cancelled | grace
- 周期起点 = 购买时刻; 月度额度 = 懒刷新(period_reset_on)
- 到期 = 懒判定(访问时 now>period_end 且未续 → 免费权益)
- 续费扣款 = payment 事件(个人无商户→延后/mock; 逻辑先行, 支付后接)
```
落 kokoro-payment(交易/卡密) + kokoro-credit(桶/权益/Plan) + 订阅生命周期层(可 mock 支付下独立跑)。

## L3.5 · 卡密（零支付集成分发）

```
CardBatch { id, plan(credit_pack), qty, expire_at, campaign/reseller }
CardCode  { code_hash(不存明文), batch, status: unused|redeemed, redeemed_by, redeemed_at }
redeem(code, namespace):  校验(存在/未用/未过期) → CAS 占用 → grant 包积分(永久桶) → ledger(归因 batch)
安全: 随机长码 · 一次性 CAS · 兑换限频 · 明文只存 hash
admin: 生成/作废批次 · 兑换率 · 按批次/分销商营收
```

## L3 的验证（真栈 e2e）
- 三桶：grant 永久 + 订阅刷周期 + 免费刷每日 → 消费按 daily→period→permanent 序扣；懒刷新惰性生效。
- 权益：订阅解锁高级模型 tier（受理 gating）+ multiplier 降扣费。
- 卡密：生成批次 → 输码 → 永久桶到账 → 二次输同码拒（一次性）。
- 订阅：mock 支付激活 → 权益生效 → 到期落回免费（懒判定）。

---

# A × L3 的咬合点（一处，避免各建各的）

**`invoke_model` 的 hold/settle 必须读 L3 的 featureKey 费率 + 订阅 multiplier + 桶顺序 + model tier gating。**
即：引擎(A)扣费时，计价与准入来自商业(L3)。一处接口 `credit.hold(namespace, featureKey, estimate)` +
`resolveEntitlements(namespace)` 把两者缝好——**不各建两套计费**。

---

# 相序（A ∥ L3，咬合点收口）
1. A-LLM（DeepSeek，验计费+真用量）— **现在可做**。
2. L3.1 三桶+懒刷新 → A4 settle 泛化用量 → 咬合点。
3. L3.2 Plan+权益 → A3 invoke_model 接 gating/multiplier。
4. A-媒体（mock 图片）→ 验产 artifact 链。
5. L3.3/4/5 供给三渠道（支付/订阅/卡密）。
6. 真媒体 provider key 到位 → A-媒体转真。
