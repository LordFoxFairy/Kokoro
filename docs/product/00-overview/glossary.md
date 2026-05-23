---
status: 🟡 草稿
updated: 2026-05-20
---

# 术语表

> 本手册中使用的产品 / 设计 / 工程术语，统一在此定义。
> 任何新引入的术语应该先在这里注册再使用。

---

## 产品术语

| 术语 | 定义 |
|---|---|
| **Kokoro** | 产品名。来自日语「こころ」= 心 / 内心 |
| **Canvas** | 主区域右侧的工作面板，承载视觉产物（文档 / 图 / 海报 / 落地页 等） |
| **Chat** | 主区域中央的对话区，用户与 Kokoro 交互的主入口 |
| **Skill** | Kokoro 的可扩展单元，markdown + frontmatter 格式，参考 Claude Code 的 skills |
| **Template** | 用户产物一键转化的模板，存入社区模板库 |
| **心人格** | Kokoro 的产品人格定调（[ADR-001](../../decisions/ADR-001-product-personality.md)） |

## 增长术语

| 术语 | 定义 |
|---|---|
| **产物印记** | Canvas 产物自带的视觉/品牌标识，让分享者一眼可辨"这是 Kokoro 出品" |
| **分享一等公民** | 分享链接 / OG / 嵌入在产品出生第一天就具备的能力 |
| **模板沉淀循环** | 用户产物 → 转模板 → 新用户用模板 → 更多产物 |

## 安全 / 权限术语（参考 Claude Code）

| 术语 | 定义 |
|---|---|
| **permission rules** | 进程级规则评估链：deny → ask → allow |
| **permission modes** | 决定打扰频率的模式档位（plan / acceptEdits / default / bypass 等） |
| **protected paths** | 即使 bypass 模式仍受保护的路径 / 资源 |
| **circuit breaker** | 危险操作熔断器，独立于 permission mode 兜底 |
| **session** | 绑定到工作上下文的可命名 / 可分支对话单元 |
| **context** | 当下这一轮 Kokoro 可见的内容（用户可见可控） |
| **persistent memory** | 跨 session 的持久层，分"用户写的指令"和"Kokoro 自学的"两区 |

## 待补

- design tokens 命名约定（等设计系统稿）
- 工程术语（等架构稿）
