---
status: 🔴 待你拍板
updated: 2026-05-20
---

# Plugins

> Plugin = 带代码的扩展。给 Kokoro 加新工具、新 Canvas 类型、新视觉能力。
> 跟 skill 的根本区别：**skill 是用 prompt 改我的行为，plugin 是给我新的手脚**。
> v2+ 范围。MVP 不做。

---

## 0. 立场

不急着做。Claude Code 的经验是：扩展生态的**信任**和**安全模型**比扩展机制本身复杂十倍。MCP 是协议层抽象，skill 是 prompt 层抽象，plugin 是**代码层抽象**——风险曲线最陡。

排序：

1. v1：**只做 skills**。证明扩展抽象本身能用，攒第一批用户写的东西
2. v2 早期：上 **MCP 客户端**（[mcp.md](./mcp.md)）。借开放协议先把外部工具接入打通，不自造轮子
3. v2 中期：**plugins**。在 MCP 已经能解决 70% 接入需求的前提下，plugins 专门补「MCP 解决不了的」：Canvas 类型扩展、视觉渲染、本地化交互

这个顺序很重要：**先借标准，再造私有**。

---

## 1. Plugin 跟 Skill 跟 MCP 的差异

| | Skill | MCP server | Plugin |
|---|---|---|---|
| **本体** | markdown + frontmatter | 独立进程 / HTTP 服务，实现 MCP 协议 | Kokoro 私有扩展包 |
| **加的是什么** | 行为指令（prompt） | 工具调用（外部能力） | 工具 + UI + Canvas 类型 + 视觉渲染 |
| **跑在哪** | Kokoro 主上下文 | 用户机器 / 远端服务器 | 沙箱里（前端 worker / 后端容器） |
| **生态** | 完全开放 | 跨厂商标准（GitHub / Notion / Sentry 都有） | Kokoro 私有 |
| **典型用途** | "帮我整理日记" | "查我的 Notion 待办" | "新加一个流程图 Canvas 类型 + 配套渲染器" |
| **门槛** | 会写 markdown | 会写 server（任意语言） | 要懂 Kokoro 插件 SDK |

**判断该用哪个的简单原则**：

- 只是想换我说话的方式 / 改流程 → skill
- 想接入一个 SaaS 工具 → MCP
- 上面两个都做不到 → plugin

---

## 2. Plugin 能扩展什么

按从易到难：

### 2.1 注册新命令（≈ skill 的代码版）

跟 skill 重叠，区别是 plugin 可以在执行命令时跑代码（不止 prompt）。适合需要做计算 / 调本地 API 的命令。

### 2.2 注册新工具

让我能调用一个新的「工具」——读 PDF、跑 SQL、转换图片格式之类。比 MCP 轻：

- MCP 需要起 server
- Plugin 注册的工具直接跑在 Kokoro 沙箱里

### 2.3 注册新 Canvas 类型

> 这是 plugin 最有价值的扩展点。

内置 Canvas 类型（PPT / 海报 / 文档 / 课件 ...）的覆盖永远有限。Plugin 可以新增：

- 流程图 Canvas（脑图 / 决策树 / 时间线）
- 数据可视化 Canvas（接入 plugin 自带的渲染库）
- 代码沙箱 Canvas
- 音频/视频 timeline Canvas
- 3D 场景 Canvas

每种新 Canvas 类型 plugin 需要提供：

- 数据模型（schema）
- 渲染器（前端组件）
- 我能用的编辑工具（让我修改这种 Canvas 的方法）
- 默认模板（这种 Canvas 新建时的初始内容）
- 心人格适配指南（颜色 / 字体 token 怎么对齐）

### 2.4 注册新的 hook handler

Plugin 可以订阅 Kokoro 的生命周期事件（参见 04-architecture 里的事件模型）：

- `BeforeCanvasEdit`：在我改 Canvas 前做拦截 / 转换 / 验证
- `AfterCanvasEdit`：自动 format / lint / 计数
- `OnShare`：分享前自动生成 OG 图
- `OnSessionStart`：注入项目上下文

### 2.5 注册 UI 面板

Plugin 可以在右侧栏 / Canvas 工具栏注册自己的面板。配合上面几种能力组合出比较深的体验。

---

## 3. Plugin 的形态

```
my-plugin/
├── manifest.json       # 必需，元信息 + 声明
├── skills/             # 可选，捆绑的 skills
│   └── ...
├── src/                # 代码
│   ├── tools.ts
│   ├── canvas/         # 自定义 Canvas 类型
│   └── ui/             # 面板组件
├── assets/             # 图、字、模板
└── README.md
```

### Manifest

```json
{
  "name": "flowchart-canvas",
  "version": "0.1.0",
  "author": "...",
  "description": "把流程图作为一种 Canvas 类型加到 Kokoro。",
  "permissions": [
    "canvas.register-type",
    "canvas.edit",
    "network.fetch:example.com"
  ],
  "extends": {
    "canvas-types": ["flowchart"],
    "tools": ["flowchart.render", "flowchart.export"],
    "commands": ["/flowchart"],
    "hooks": ["AfterCanvasEdit"]
  },
  "compatibility": {
    "kokoro": ">=2.0.0 <3.0.0"
  }
}
```

`permissions` 字段必须**显式声明**所有需要的能力。装的时候用户看到的就是这张清单。

---

## 4. 安全模型（联动 [09-safety](../09-safety/)）

Plugin 是 Kokoro 安全模型最严的接入点。原则：

### 4.1 沙箱

- 前端代码跑在 Web Worker / iframe 沙箱里，**不能访问主页面 DOM**
- 后端代码跑在容器里，**不能访问其他 plugin 的数据 / 用户全局历史**
- 网络访问按 manifest 声明的域名白名单走

### 4.2 权限三态（抄 Claude Code）

每次 plugin 要做敏感动作（读用户文件、调网络、改 Canvas），权限按 `deny → ask → allow` 评估：

- `deny`：永远不允许（manifest 没声明的）
- `ask`：第一次问，可以"这次允许 / 永远允许 / 拒绝"
- `allow`：用户已经永久授权

**deny 永远胜过 allow**。

### 4.3 装的时候问什么

用户装 plugin 时弹一张「这个 plugin 想要什么权限」的卡片：

```
flowchart-canvas 想要：
✓ 添加新的 Canvas 类型「流程图」
✓ 读写流程图 Canvas
⚠️ 访问 example.com（用来加载图标库）
✗ 不要本地文件访问
```

用户能选「装上」/「不装」/「装但拒绝标⚠️的」。

### 4.4 卸载干净

装 plugin = 给 Kokoro 加东西。卸载必须是反向操作：

- 移除所有 plugin 注册的工具 / Canvas 类型 / 命令 / hook
- 询问用户：plugin 创建的 Canvas（比如所有流程图）怎么办——保留只读 / 导出 / 删除

不允许卸载留垃圾。

---

## 5. 上架审核（v2+ 后期）

Kokoro 官方插件市场，开放第三方上架。审核维度：

| 维度 | 检查什么 |
|---|---|
| **代码安全** | 自动扫加密混淆 / 已知漏洞 / 可疑 API 调用 |
| **权限合理性** | 声明的权限跟功能是否对得上（一个流程图插件没理由要本地文件读权限） |
| **心人格** | 文案 / 视觉是否冲突——可以不"心"，但不能反「心」 |
| **隐私** | 是否把用户数据发出去；发出去要在 manifest 和说明里写清楚 |
| **稳定性** | 自动跑 plugin 的基础测试 |
| **维护** | 作者是否响应 issue / 长期不更新会下架 |

通过的 plugin 标"已审核"。用户也能装"未审核"的 plugin（手动加载或从社区 URL），但有醒目警告。

---

## 6. v2+ 路线图

| 阶段 | 内容 |
|---|---|
| v2.0 | 内部 plugin（Kokoro 自家先用 plugin 机制实现一些功能，验证 API） |
| v2.1 | 开放给受邀开发者，闭环测一批 |
| v2.2 | 公开 SDK + 文档 |
| v2.3 | 上架审核流程 + 官方市场 |
| v3.0 | 收益分成 / 付费插件（看市场反应） |

每个阶段都要先回看：**MCP 已经能解决多少需求？plugin 真正剩下要做的是什么？** 如果 MCP 接入路径足够顺，plugin 可以更轻——只做 Canvas 类型扩展和 UI 这两件 MCP 做不了的事。

---

## 7. 待你拍板

- [ ] Plugin 是 v2.x 还是 v3？取决于 v1/v2 时 skill + MCP 能不能撑住第三方接入需求
- [ ] 是否允许"未审核" plugin？开放生态需要，但跟「心人格 = 安全感」有张力
- [ ] 付费插件是否纳入商业模式？跟 [01-strategy/business-model.md](../01-strategy/business-model.md) 联动
- [ ] Canvas 类型扩展用 plugin 还是用更轻的「Canvas 类型 schema 包」？后者只是数据 + 渲染器，没代码

---

## 关联

- [skills.md](./skills.md) — 行为扩展（无代码）
- [mcp.md](./mcp.md) — 外部工具接入（开放协议）
- [../09-safety/](../09-safety/) — 权限模型 / 沙箱
- [../03-product-form/canvas-types.md](../03-product-form/canvas-types.md) — Canvas 类型扩展依赖这里的 schema 设计
- [../../research/claude-code/learnings/03-agentic-primitives.md](../../research/claude-code/learnings/03-agentic-primitives.md) — MCP / 沙箱借鉴
