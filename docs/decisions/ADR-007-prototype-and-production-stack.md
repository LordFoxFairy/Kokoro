# ADR-007 · 原型 = 设计 spec；生产另起真栈

- **日期**：2026-05-22
- **状态**：accepted
- **决策者**：用户拍板
- **关联**：[ADR-006](./ADR-006-color-palette.md)、[03-product-form/shape.md](../product/03-product-form/shape.md)、[05-design-system/](../product/05-design-system/)、`docs/prototypes/variant-a-mi-mu/`

---

## 决策

**`docs/prototypes/variant-a-mi-mu/` 是设计 spec，不是 MVP 代码。**

- 原型用 vanilla HTML + CSS + 极少 JS，自包含、不引构建工具——保持"单击 HTML 能看"的低摩擦
- 生产 / MVP 阶段**另起一个 Next.js 仓库**，把原型当 design source 重建
- 原型负责锁：**视觉 token / 组件 anatomy / 交互模式 / 心人格 copy / 状态档位**
- 原型不负责：实际工程实现（streaming / state management / a11y 深层 / 性能 / 国际化 / 测试）

---

## 生产栈选型（待 MVP 启动时落地，本 ADR 仅记录方向）

| 层 | 选型 | 备注 |
|---|---|---|
| 框架 | **Next.js 15 + React 19** | RSC、streaming、文件路由 |
| 样式 | **Tailwind v4** | CSS 变量原生，与 token 系统天然对齐 |
| 组件 | **shadcn/ui** | 源码 copy 进项目，可重度定制为「心」气质 |
| 无头交互 | **Radix UI**（shadcn 底层） | dropdown / popover / dialog / focus-trap 不用手撕 |
| 动效 | **Framer Motion** 或 **motion.dev** | 呼吸 / 纸感 / layout 动效 |
| LLM / 流式 | **Vercel ai-sdk** | useChat / streaming / 多 model 路由 |
| Toast | **Sonner** | 堆叠 / 自动消失 |
| Markdown / 代码 | **react-markdown + Shiki** | AI 回复里的 code block / 列表 / 链接 |
| 主题 | **next-themes + CSS vars** | 明暗主题 |

**Tailwind 4 与我们的 token 系统对齐方式**：
- 原型 `css/tokens.css` 的 `--color-*` `--space-*` `--radius-*` 直接映射到 Tailwind 4 的 `@theme` 配置
- shadcn 默认的 `--background` `--foreground` `--accent` 等变量名重命名为 Kokoro 的命名

**Framer Motion 接 A 套的"纸感系统"**：
- noise overlay 用 motion `layoutId` 跨页面保持
- 呼吸 loading 用 `animate={{ scale: [1, 1.02, 1] }}` + `transition={{ duration: 1.8, repeat: Infinity }}`
- 入场缓动统一用 `cubic-bezier(0.16, 1, 0.3, 1)`

---

## 理由

1. **关注点分离**：原型设计师 / 决策者 / 早期 review 只需要看视觉与交互，无须配 npm 环境
2. **决策与实现的节奏不同**：原型迭代快（几小时一轮），生产工程慢（特性按周）
3. **避免"原型代码化生产"陷阱**：vanilla 原型直接 ship 会带历史包袱（legacy class、缺 a11y 深层、无 streaming）
4. **业界事实标准**：v0 / Cursor / Lovable / ChatGPT Web 都用上述栈，社区资源丰富

---

## 否决项

| 方案 | 否决理由 |
|---|---|
| **立即转栈到 Next.js + shadcn** | 当下没必要——视觉与交互未稳，过早工程化会拖慢决策迭代 |
| **vanilla 原型直接当 MVP ship** | 历史包袱、a11y 不够深、扩展性差、招人协作难 |
| **用 Vue + Element Plus / Ant Design** | 与 AI 产品社区生态对不齐；shadcn 更可定制 |
| **用 Svelte / Solid** | 团队招聘 / 协作面更窄 |

---

## Tradeoff

- **原型到生产的"翻译损耗"**：vanilla CSS → Tailwind class、原生 details/summary → Radix Disclosure 等转译需要做一次，估计 1-2 周专项
- **两套代码并行短期成本**：原型继续打磨期间，生产代码可能延后启动
- **原型可能"过设计"**：手撕原型容易陷入细节完美主义；要明确知道"原型的目的是锁决策不是 ship"

---

## 后果

- `docs/prototypes/variant-a-mi-mu/` 继续作为设计 spec 推进打磨
- MVP 启动时新开 `src/` 或独立仓库，按本 ADR 栈实现
- 原型与生产代码之间走 [05-design-system/](../product/05-design-system/) 作为契约层（token / 组件 anatomy）
- 当原型设计稳定到"3-5 天没大改"时，是启动生产的信号

---

## 后续待定

- [ ] MVP 启动时机：等原型稳定 / 等 vision 写完 / 用户拍板
- [ ] 生产仓库结构（monorepo 还是单仓 / 是否有 design system 独立包）
- [ ] 是否做"原型 → 真栈"翻译脚本（可选，半自动）
- [ ] CI / 部署平台（Vercel 默认，待定）
