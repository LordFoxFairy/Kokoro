---
status: 🟢 已定
updated: 2026-05-20
---

# 动效语言

> 动效服务"心"人格：柔、慢半拍、有呼吸。
> 任何打破下列原则的动效都需要专门理由，否则一律按本文规范走。

## 摘要

- 缓动：只用 ease-out 或自然 cubic-bezier。**不弹不 spring 不 overshoot**。
- 时长：常规过渡 200-300ms，关键状态 400-500ms，loading 周期 1.8s。
- Loading：**永远不用 spinner / 旋转**，用呼吸脉动 / 渐变 / 接力点。
- 入场比出场略慢半拍（更柔），出场不拖尾。

具体数值见 [tokens.md](./tokens.md) 动效 token 节。

---

## 五条核心原则

1. **柔比快重要**：宁可慢半拍，不要急停 / 急启
2. **呼吸比旋转重要**：节奏感（pulse / breath）替代机械感（spin / rotate）
3. **方向比强度重要**：入场从下往上 / 从浅到深，符合"被托起"的感觉
4. **状态切换要被看见**：但不能被打扰。意思 = 有过渡，无戏剧
5. **不要叠加动效**：一个交互最多两层动效（如颜色 + 位移），不要四五层炫技

---

## 该这样 / 不该这样

| 场景 | ✅ 该这样 | ❌ 不该这样 |
|---|---|---|
| Hover 卡片 | 背景色 250ms ease-out 渐入暖化 | 放大 1.05× / 阴影炸开 / 上抬 4px |
| 按钮点击 | 按下时 background 变深 100ms，松开 250ms 回 | 涟漪扩散 / 弹回 spring / 缩放抖动 |
| 弹窗入场 | opacity 0→1 + translateY 8px→0，400ms ease-out | 旋转飞入 / 缩放从 0.5× 弹大 / 多方向溅射 |
| 弹窗出场 | opacity 1→0，200ms，**不位移** | 缩回 / 旋转飞出 / 弹一下再消失 |
| Streaming 文字 | 光标 1.2s 呼吸 opacity 0.3↔1 | 光标 500ms 闪烁 / 文字逐字弹入 |
| Loading（短） | 单点呼吸 1.8s 周期 | spinner 旋转 / 进度条爬行 |
| Loading（长，多阶段） | 三点接力呼吸（依次 phase 偏移 600ms） | 三点同步闪烁 / 进度环 |
| 列表项进入 | 整列 fade-in + translateY 4px，stagger 30ms | 每项弹跳 / 从左飞入 / 旋转 |
| Sidebar 收窄 | width 300ms ease-out | spring 弹性宽度变化 |
| Canvas 打开 | Chat 区缩窄 + Canvas 从右滑入，450ms ease-out 同步 | Canvas 弹开 / Chat 区突然跳 |
| 错误 toast 出现 | 底部 translateY 16px→0 + opacity，300ms | 顶部砸下来 / 红色闪烁 / 抖动提醒 |
| 成功反馈 | 按钮文字变化 250ms（无其他动效） | 撒花 / 打勾弹跳 / 爆炸粒子 |
| 切换标签页 | crossfade 200ms | 滑动切换 / 翻页效果 |
| 头像 / 状态点 | 不动 | 持续脉冲 / 旋转光环 |

---

## 缓动函数清单

引用 [tokens.md](./tokens.md)：

| 场景 | 用 | cubic-bezier |
|---|---|---|
| 默认所有过渡 | `--easing-default` | `cubic-bezier(0.25, 0.1, 0.25, 1)` |
| 入场（弹窗 / Canvas / 卡片） | `--easing-enter` | `cubic-bezier(0.16, 1, 0.3, 1)` |
| 出场（弹窗消失） | `--easing-exit` | `cubic-bezier(0.7, 0, 0.84, 0)` |

**禁止函数**：
- `ease-in-out-back`（含 overshoot）
- 任何 spring 配置（`damping < 1` 都不行）
- `cubic-bezier(x, y, z, w)` 中 `w > 1` 或 `y < 0`（会产生弹跳）

---

## 时长档位

| 用途 | 时长 | token |
|---|---|---|
| 微交互（hover / focus 边框） | 150ms | `--duration-fast` |
| 常规过渡（颜色 / 透明度 / 小位移） | 250ms | `--duration-base` |
| 关键状态切换（弹窗 / Canvas 开关 / 页面切换） | 450ms | `--duration-slow` |
| Loading 呼吸周期 | 1800ms | `--duration-breath` |

经验法则：
- ≤ 100ms 用户感知不到 → 不用
- 100-200ms 用户感觉"快但生硬" → 慎用
- 200-300ms 是心路线甜区 → 默认
- 300-500ms 仅给关键状态 → 不滥用
- > 500ms 仅 loading → 不当过渡用

---

## Loading 三种形态

```
[ A ] 单点呼吸（默认 streaming / 短等待）
   ●        opacity 0.3 → 1 → 0.3
            1800ms 一个周期，ease-in-out

[ B ] 三点接力（多阶段 / 较长等待）
   ● ● ●    phase 偏移 0 / 600ms / 1200ms
            视觉效果：左点亮→中点亮→右点亮，循环

[ C ] 渐变扫光（Canvas 整块生成中）
   ▓▒░░░░    一条极淡的暖光从左到右扫过卡片表面
              2400ms 一个周期，opacity 峰值 0.15
```

**永不使用**：
- 旋转 spinner（任何形态）
- 进度条（除非真实有百分比，而 AI 任务通常没有）
- 沙漏 / 时钟 / 跳跃小人等 emoji 占位

---

## 微交互细则

### Focus 状态

- input focus：边框颜色 250ms 从 `border` 渐入 `border-strong`，**不发光不放大**
- 按钮 focus（键盘）：外圈 1.5px outline，accent-soft 色，**无动画直接出现**（无障碍优先）

### Hover

- 卡片：背景色 250ms 暖化（`surface` → `surface-hover`）
- 按钮：背景色 150ms 加深
- 链接：下划线 150ms 渐入（不用突然显示）

### Press / Active

- 按钮：按下瞬间背景再深一档，松手 250ms 回弹（**回弹是单向 ease-out，不是 spring**）
- 卡片：按下不缩放，仅 shadow-sm → shadow-xs 250ms

---

## 节奏与编排

- **stagger（错列）**：列表入场每项间隔 30ms，最多 stagger 10 项，超过则统一 fade（避免拖太长）
- **同步**：相关联元素（如 Sidebar 收窄 + Canvas 入场）**时长 + 缓动必须一致**，让两个动作看起来是一件事
- **不连锁触发**：A 动作完了才放 B 是机械感。除非 B 严重依赖 A 的尺寸，否则并行触发

---

## 无障碍

- 检测 `prefers-reduced-motion: reduce`：
  - 所有 transform / translate 动效 → 直接跳到终态
  - 缓动改 linear 150ms
  - Loading 脉动周期改 3s 且 opacity 振幅减半（0.6 → 1）
  - **保留** crossfade 和颜色过渡（这些不引起前庭不适）

---

## 待你拍板

- [ ] Loading 形态 A / B / C 默认用哪个？现在没指定优先级
- [ ] Canvas 入场 450ms 够柔吗？感觉不够可以加到 550ms 但会牺牲一点响应感
- [ ] Streaming 光标用呼吸（1.2s）还是更慢（2s）？涉及到"Kokoro 在思考"的感觉

## 关联

- [tokens.md](./tokens.md) — 动效 token 数值
- [components.md](./components.md) — 每个组件的状态切换走这里
- [patterns.md](./patterns.md) — 模式级的状态编排
- [visual-language.md](../02-personality/visual-language.md) — 动效语言总纲
