# Mori Navigation Shell Revision

> 状态：approved for implementation by the active Mori refinement task
> 日期：2026-09-02
> 范围：Mori preview 的全局导航、页面分层、播放器与上下文抽屉

## 1. 修订原因

第一版把 Create 工作台的三栏布局误用为整个产品的页面框架，导致 Library、Projects
和 Create 都同时承载右侧 Inspector 与底部播放器，页面职责不清、内容区域被切碎。
本修订将 Suno 已验证的产品骨架与网易云式的音乐播放习惯拆成两层：产品级 Shell 负责
导航和播放，页面级 Surface 负责当前任务，Queue/Inspector 只在需要时作为上下文抽屉
出现。

## 2. 核心模型

```text
Mori App Shell
├── Rail（全局，可展开 / 收起）
├── Surface（当前页面的连续主画布）
└── Global Player（有选中歌曲时出现）

Surface context
├── Create：Composer + 可选 Queue Drawer
├── Projects：项目集合
├── Library：资产集合
└── Studio：编辑器 + 版本轨道
```

页面不再共享 Create 的三栏几何。全局播放器采用 fixed bottom bar，主内容只按其可见
状态预留底部空间；Expanded details 由播放器自己的详情动作触发。

## 3. 路由与导航

```text
/                         Home / Discover
/create                   Create
/projects                 Projects
/projects/{project_ref}  Project Overview
/projects/{project_ref}/studio/{version_ref}  Studio
/library                  Library
```

Rail 一级入口固定为 Home、Create、Projects、Library；New creation 指向 `/create`。
`MoriAppShell` 统一管理 Rail 展开状态，所有页面使用同一份状态与宽度变量。收起后仍
保留图标、可访问名称和明确的展开按钮。

## 4. 页面职责与布局

| 页面 | 主任务 | 默认右侧区域 | 播放器 |
|---|---|---|---|
| Home | 发现最近项目和方向 | 无 | 选中歌曲后显示 |
| Create | 从想法提交一次生成 | 关闭 | 全局 Mini Player |
| Projects | 找到并继续项目 | 无 | 选中歌曲后显示 |
| Library | 管理歌曲、版本和资产 | 无 | 选中歌曲后显示 |
| Studio | 编辑已有版本 | Studio 内部版本轨道 | 全局 Mini Player |

Create 的 Queue Drawer 只在用户点击 Queue 或提交生成后打开；Library、Projects 不挂载
Queue/Inspector。Studio 的版本轨道属于 Studio 内容，而不是全局右栏。

## 5. Global Player 状态

```text
没有选中歌曲  → 隐藏
已选中         → Mini Player
播放中         → Mini Player + progress
点击 Details   → Expanded Player / Song Detail
```

播放器的最小结构是封面、歌曲信息、transport、进度、Queue、Details；不使用大面积
卡片包围主页面。预览版仅使用 deterministic waveform 与 fixture 状态，不访问外部音频
服务。

## 6. 视觉连续性

- 页面背景统一使用暖白与低对比度 lavender/peach/mint atmosphere。
- Rail 是唯一独立的导航面，主 Surface 不再由多个带阴影的白色大卡片拼接。
- Create 的 Composer、Library 的列表、Projects 的卡片只作为内容分组使用边界；不为
  每个区域重复玻璃效果。
- 渐变只承担品牌、主 CTA、封面和播放进度四类语义。
- 默认浅色；键盘焦点、对比度和 `prefers-reduced-motion` 保持可用。

## 7. 实现边界

新增 `MoriAppShell` 作为 Shell 唯一入口；`MoriCatalogShell` 只负责为目录类页面提供
内容和预览播放器；`MoriWorkspace` 负责 Create 的 queue 状态，不再直接拥有 Rail 与
全局播放器布局。现有 Mori domain 与 API seam 不变，后端契约继续保持 provider-neutral。

## 8. 验收条件

1. Create 首次渲染看不到 Queue Drawer，但可以通过按钮打开并关闭。
2. Rail 在 Create、Projects、Library、Home 使用同一个展开 / 收起交互。
3. `/` 显示 Home，`/create` 显示 Create，New creation 与 Create 导航均指向 `/create`。
4. 全局播放器不再参与三栏 grid；它作为底部层覆盖在主 Surface 下方并有稳定的内容
   底部间距。
5. Library 与 Projects 不挂载 Generation queue region。
6. 现有 lint、typecheck、Vitest 与 production build 继续通过。
