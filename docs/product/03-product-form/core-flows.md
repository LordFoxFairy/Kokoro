---
status: 🟡 草稿
updated: 2026-05-20
---

# 核心流程

## 当前研发验收基线（2026-10-03）

完整研发范围沿既有 Wave0–7；以下汇总用户已确认的流程，不新增角色、收费或部署方案。每条在 [测试总台账](../../test-cases.md) 原ID验收；本节是需求，不是已完成声明。

| 用户旅程 | 产品规则与唯一事实owner | 现测试ID / 独立推进关系 |
|---|---|---|
| 正常登录→工作区 | IAM负责认证/逐请求权限；产品可见普通用户、管理员；受信自家Web不展示内部scope中转，第三方连接器仍真实授权 | T-L01–05；不等待Agent能力实现 |
| 新建/打开普通会话 | 会话独立存在，不必先建项目；BFF拥有会话/消息，Web只拥有浏览器交互与同源session | T-C01–03；列表/创建/权限不依赖模型执行 |
| 项目中的会话 | 项目是组织与上下文容器，会话可归属项目；不复制同一个会话，不把任务或Run当会话。会话/文件默认个人私有；显式分享仅指Conversation（T-C04），不新增Project分享，Project访问仍按现IAM/BFF授权 | T-C02/04/05；删除规则见下方已批准裁决，owner实现/关联生命周期仍待验 |
| 独立定时任务 | ScheduledTask是独立资源，project_id仅关联；Scheduler拥有Occurrence/Lease，Agent拥有实际Run | T-P01–05；管理CRUD与执行/恢复分开验收，不等整Agent才实现管理面 |
| 输入→排队→流式回复→恢复 | 同会话FIFO一个活动head；Run不等于会话。提交中/排队/执行/审批/恢复/取消/终态按服务端事实展示 | T-C06–10/T-A01–06；生产者契约先固定，消费者切换依赖该artifact，不等全服务完成 |
| Skills/MCP管理→实际使用 | Platform拥有安装/启用/连接与授权事实；选择或安装不冒充已加载/已执行，Agent真实加载事件才展示ready | T-K01–07/T-A02；管理面与运行消费独立切片 |
| 文件/作品/积分 | Storage拥有真实作品；Billing拥有赠送/余额/预占/结算/释放/流水及可配置倍率，前端不算价格、不伪造免费。支付渠道最后 | T-F/T-B原组；按实际owner契约验收，不以UI出现当执行或扣款证明 |

交互复用现shadcn/ui、Vercel AI SDK与唯一AG-UI传输；不自建第二套网络/状态协议。简单聊天无需强制Canvas/计划/工具过程，复杂任务按真实Todo/Skill/工具/审批事实渐进披露。

### 已批准的项目删除与失败收费（2026-10-03）

- 项目删除按用户指定的ChatGPT规则：确认后移除项目、其会话/指令及仅项目文件，用户不可恢复；需要保留的会话先移出项目。独立保存或其他有效资源引用的文件保留，不连带删除外部会话或独立定时任务。参考：[OpenAI官方项目说明](https://help.openai.com/en/articles/10169521-projects-in-chatgpt)，核验2026-10-03。Kokoro关联任务上下文、Run取消及Storage清理需按现owner契约门明确，未实现不算闭环。
- failed/cancelled/部分输出只结算已核实的实际消耗，释放其余可确认未使用预占；未调用不扣，用量unknown持久待证据与对账，不当零、不直接整笔释放。Billing采用冻结价格/倍率/换算版本，前端不算金额；晚证据、重投、取消与结算竞态不能重复扣费。
- 两项业务决定已确认，系统验收T-C05/T-B07从待决策转未验；详细前置、操作、预期和异常/安全/状态分支维护在原测试总台账，不新建计划中心。

> 下方为2026-05历史产品草案，不作为当前实现完成证据；与本节或 Root/owner 当前契约冲突时不作为研发依据。尚未批准的增长、样式与路线问题保持草稿，不另起架构。


> 三条主用户路径。其他次要 flow 在 [06-screens/](../06-screens/) 各页文档展开。

---

## Flow 1 · 一句话造产物（首屏 → Canvas → 分享）

```
用户进首屏
  └─ 看到引导语 + 输入框 + 几个产出物 chip（"做小红书海报""做策划案"...）
     └─ 用户输入一句话 + 选 chip 或纯文本
        └─ Kokoro 在 Canvas 里实时生成
           └─ 用户可继续追问 / 调整 / 重做
              └─ 用户点"分享"
                 └─ 生成 share link + OG 图（带印记）
                    └─ 分享出去
```

**关键体验点**：
- 首屏 → Canvas 之间没有任何中间步骤
- Canvas 生成过程**可见**，能让用户感觉"在做" 而不是"在等"
- 分享按钮位置显眼（一等公民）

---

## Flow 2 · 持续对话深化（Chat → 多轮 → Canvas 累积）

```
用户进对话
  └─ 多轮对话讨论想法
     └─ Kokoro 提议 "要不要把这个落到 Canvas 上"
        └─ 用户同意 → Canvas 出现
           └─ 来回多次（chat → canvas → chat → canvas）
              └─ 完成 / 暂停 / 分享
```

**关键体验点**：
- Chat 和 Canvas 之间的"过渡"要顺
- 不要强迫用户提前决定"要 Canvas 还是只 chat"

---

## Flow 3 · 用模板（模板库 → 一键起飞）

```
用户进模板库（或被首屏推荐）
  └─ 浏览 / 搜索模板
     └─ 选定一个
        └─ 一键复制到我的 Canvas
           └─ 用 Kokoro 帮我"按这个风格做一份"
              └─ Kokoro 在 Canvas 里调整为用户场景
                 └─ 用户微调 / 分享 / 自己再转模板
```

**关键体验点**：
- 模板不是静态文件，是"半成品 + AI 适配"
- 用户改完可以一键转模板回馈社区

---

## 共享子流程

### A. 触发 Plan mode

任何用户输入涉及**多步骤 / 风险 / 不确定**时，Kokoro 自动进入 Plan mode：

```
用户输入
  └─ Kokoro 判断"这个需要规划"
     └─ 进 Plan mode：生成 plan preview
        └─ 用户 Approve / Refine / Cancel
           └─ Approve → 执行
              Refine → 用户调整 plan，再 Approve
              Cancel → 回到 chat
```

参考：[04-architecture/modes.md](../04-architecture/modes.md) + [Claude Code learnings/03-agentic-primitives.md](../../research/claude-code/learnings/03-agentic-primitives.md)

### B. 危险操作熔断

任何"不可逆 / 影响他人 / 跨账号"的操作：

```
Kokoro 准备执行
  └─ circuit breaker 触发
     └─ 弹 modal："你要 ___，我做完就回不去了。确认？"
        └─ 用户 Confirm / Cancel
```

参考：[09-safety/circuit-breakers.md](../09-safety/circuit-breakers.md)

---

## 反例（不要这样做）

- ❌ 首屏需要选择"我要 chat 还是 Canvas"——增加心智成本
- ❌ 分享按钮藏在三级菜单——违反一等公民
- ❌ 模板需要付费才能用——破坏增长引擎
- ❌ Plan mode 必须手动开——应自动进入

## 待答题

- [ ] Flow 1 的"产出物 chip"个数：3 / 5 / 7？（决定首屏布局）
- [ ] Flow 2 的"chat → canvas 过渡"用什么触发？（用户主动 / Kokoro 提议 / 自动判断）
- [ ] 是否允许"未登录"试用？（影响 funnel 顶部宽度）

## 关联

- [shape.md](./shape.md)
- [feature-map.md](./feature-map.md)
- [04-architecture/](../04-architecture/)
- [06-screens/home.md](../06-screens/home.md)
