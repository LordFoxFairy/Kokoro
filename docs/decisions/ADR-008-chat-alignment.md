# ADR-008 · 聊天对齐：标准右用户 / 左 AI，撤销 Gemini 居中借鉴

- **日期**：2026-05-22
- **状态**：accepted（supersedes 之前在 anatomy.md / chat.md / 原型里把"用户气泡居中"当成 Kokoro 特征的写法）
- **决策者**：用户反馈触发，Claude 起草
- **关联**：[03-product-form/core-flows.md](../product/03-product-form/core-flows.md)、[06-screens/chat.md](../product/06-screens/chat.md)、[research/gemini/anatomy.md](../research/gemini/anatomy.md)、`docs/prototypes/variant-a-mi-mu/`

---

## 决策

聊天对齐走**业界标准**：

- **用户消息：右对齐**（带气泡）
- **AI 回应：左对齐**（保留 Kokoro 现有的"无气泡纯文本"叙述流）

撤销之前所有"借鉴 Gemini 用户气泡水平居中"的说法与实现。

---

## 错在哪（坦白）

之前我把"用户气泡居中"误判为 Gemini 的可借鉴优势。一路写到：
- `docs/research/gemini/anatomy.md` §4.1（"水平居中（非右对齐！Gemini 的辨识特征）"）
- `docs/product/06-screens/chat.md`
- `docs/product/03-product-form/core-flows.md`
- variant-a-mi-mu 的 chat.html / chat-error / chat-limit

用户实际看到原型时反馈"与正常的聊天设计差异不一样，不习惯"——这是对的。

## 用户脑里已经存在的肌肉记忆

| 产品 | 用户气泡 | AI 回应 |
|---|---|---|
| WeChat / iMessage | **右对齐** | 左对齐 |
| ChatGPT | **右对齐** | 左对齐 |
| Claude.ai | **右对齐** | 左对齐 |
| WhatsApp / Telegram / Slack | **右对齐** | 左对齐 |
| Gemini | **居中**（异类） | 左对齐 |

居中只在 Gemini 成立——因为 Gemini 用户基数足够大，肯接受不习惯。Kokoro 早期没这个本钱，应该走最低认知摩擦的标准对齐。

---

## 理由

1. **用户直接反馈**："不习惯"——这是早期产品最值钱的信号
2. **认知摩擦**：聊天界面是用户每天都在用的范式（IM / 短信 / 客服），偏离标准要付额外学习成本
3. **"心人格 ≠ 怪"**：心路线是"克制 + 温度"，不是"故意不一样"。差异化应该在产物（Canvas）、气质（视觉 token）、Voice & Tone 上，不在用户已有的肌肉记忆上
4. **保留 AI 无气泡叙述流**是仍然成立的差异化：让 Kokoro 的回复"像一封信，不像一条消息"——这个克制是有意义的

---

## 否决项

| 候选 | 否决理由 |
|---|---|
| 用户气泡居中（Gemini 风格） | 用户反馈不习惯；Kokoro 没有 Gemini 的用户基数撑得起这种偏离 |
| 用户气泡左对齐 / AI 右对齐 | 跟所有 IM 反着，更糟 |
| 用户与 AI 都左对齐无气泡（纯叙述） | 长对话里两者混淆；新用户首次进对话会困惑哪条是谁说的 |
| 用户与 AI 都右对齐 | 反直觉 |

---

## Tradeoff

- **少了一个"辨识特征"**：用户消息居中本来可以成为 Kokoro 视觉印记之一，现在没了。但这本来就是 Gemini 的，不是 Kokoro 自己的资产
- **AI 回应仍保留无气泡**：依然有"叙述流"差异化，没有完全融入 IM 范式

---

## 撤回 / 修订清单

| 文件 | 动作 |
|---|---|
| `docs/research/gemini/anatomy.md` §4.1 | 保留观察记录，但 § 8（Kokoro 可吸收）删除"用户气泡居中"那条 |
| `docs/product/06-screens/chat.md` | "用户气泡居中"改为"用户气泡右对齐"，AI 仍无气泡 |
| `docs/product/03-product-form/core-flows.md` | 删除"参考 Gemini 特征"的备注 |
| `docs/product/04-architecture/ia.md` | 如有相关 ASCII 速写更新 |
| `docs/prototypes/variant-a-mi-mu/css/components.css` | `.message--user` 从 center → right；右内边距 / 与右缘距离的 token 化 |
| `docs/prototypes/variant-a-mi-mu/` 全部 chat 相关 HTML | 检查内联 alignment 覆盖 |
| 截图 02 / 03 / 12 / 13 | 重截 |

---

## 后果

- 聊天界面的视觉与 ChatGPT / Claude 走得更近——**这是好事**，新用户上手成本极低
- Kokoro 的差异化担子完全压在：**Canvas 产物 + 气质（米+木+纸感）+ Voice & Tone + 模式（信任档位）+ 心人格 copy + 心人格视觉印记**——这些已经足够撑住
- ADR-001 心人格的"克制"内涵更明确：不是"用奇怪做出差异"，是"用品质做出差异"
