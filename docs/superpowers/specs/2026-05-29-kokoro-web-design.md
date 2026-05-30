# Kokoro Web Bootstrap Design

- **Date:** 2026-05-29
- **Status:** approved-by-user-delegation
- **Scope:** 在 `Kokoro/` 下创建独立子仓库 `kokoro-web/`，但由其自身 Git 与 `.gitignore` 管理；父仓只保留文档、协议与原型。
- **Related:** `docs/decisions/ADR-007-prototype-and-production-stack.md`, `docs/decisions/ADR-009-repository-boundaries-and-ownership.md`, `docs/protocol/session-stream.md`, `docs/protocol/session-replay-and-resume.md`

---

## 1. Goal

启动一个可独立演进的 `kokoro-web` 前端仓库，满足以下最小闭环：

1. 独立 `git init`，不与父仓发生源码耦合。
2. 采用 **Bun + Next.js App Router + Tailwind CSS + shadcn/ui + @a2ui/react**。
3. 目录按严格 DDD 分层：`domain / application / infrastructure / interfaces`。
4. 先落地 **协议驱动的聊天壳骨架**，不直连 `kokoro-agent`，只为未来 `kokoro-session` 的 HTTP + SSE 集成预留边界。
5. 用严格类型和测试先锁住最关键的前端领域逻辑：SSE 会话事件 schema、replay / resume 收敛逻辑、UI 状态折叠规则。

这轮**不做**真实后端、真实 SSE 服务端、认证、数据库、Redis 或生产部署。

---

## 2. Constraints

### Repository boundary

- 父仓 `Kokoro` 继续只拥有 docs / ADR / protocol / prototype。
- `kokoro-web` 放在父仓目录下仅为统一管理，但必须是**独立 Git 仓库**。
- 父仓 `.gitignore` 新增 `kokoro-web/`，避免把子仓源码卷入父仓历史。

### Protocol boundary

- 浏览器只面向 `kokoro-session`。
- 事件模型以 `session-stream.md` 和 `session-replay-and-resume.md` 为单一契约源。
- `kokoro-web` 只能实现事件消费、去重、收敛、展示；不能实现 Redis、agent orchestration 或权限最终裁决。

### Engineering boundary

- 不使用 `any`。
- 外部数据一律先经过 `zod` 严格解析。
- 共享 schema / DTO 只放在 `src/domain/shared/`。
- 先写失败测试，再写最小实现。

---

## 3. Approaches Considered

### Approach A — Next.js empty scaffold + 手工补齐 DDD + 手工接 shadcn（推荐）

**做法：** 用 Bun 创建标准 Next.js App Router 项目，再按我们自己的边界手工建立 `src/domain/shared`、`src/application`、`src/infrastructure`、`src/interfaces`，只安装最少的 shadcn 组件与 `@a2ui/react`。

**优点：**
- 最轻量，完全贴合 Kokoro 的边界。
- 不会引入社区 boilerplate 的隐含结构。
- 更容易保持 DDD 单向依赖。

**缺点：**
- 需要手工补少量工程骨架与测试脚本。

### Approach B — shadcn CLI 直接生成完整 Next 模板

**做法：** 让 shadcn CLI 直接生成 Next 模板，再在其上叠加 DDD 分层。

**优点：**
- 初始化快。
- 组件和主题配置更省事。

**缺点：**
- 模板会带入与本项目无关的默认约定。
- 后续再重构到严格分层会产生额外噪音。

### Approach C — Vite + React + Tailwind + shadcn

**做法：** 用 Vite 启动前端，保留轻量 SPA 结构。

**优点：**
- 更轻。
- 构建速度快。

**缺点：**
- 与 ADR-007 已锁定的 Next.js 方向不一致。
- 后续接入 App Router、RSC、流式页面结构时需要返工。

### Decision

选择 **Approach A**。

理由：它最符合现有 ADR、协议优先和严格 DDD 约束，也能把这轮范围控制在“聊天壳 + 协议消费核心”这一条主线上。

---

## 4. Target Repository Shape

```text
Kokoro/
├── docs/
├── kokoro-web/               # 独立 git 仓库，父仓忽略
│   ├── .gitignore
│   ├── package.json
│   ├── components.json
│   ├── next.config.ts
│   ├── eslint.config.mjs
│   ├── tsconfig.json
│   ├── src/
│   │   ├── app/
│   │   ├── domain/
│   │   │   └── shared/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── interfaces/
│   └── tests/
└── ...
```

### Layer rules

- `domain/shared/`: 协议 schema、值对象、纯函数，不依赖 React/浏览器。
- `application/`: 把事件折叠成 UI state 的 use-case / reducer。
- `infrastructure/`: EventSource 适配、环境读取、runtime transport glue。
- `interfaces/`: 页面、组件、view-model mapping、A2UI 渲染边界。

依赖方向只能是：

```text
domain <- application <- infrastructure <- interfaces
```

React 组件不得反向 import 基础设施内部实现。

---

## 5. Initial Feature Slice

首刀只做一个最小但可信的功能切片：

### 5.1 Strict protocol model

在 `domain/shared` 中定义 `zod` schema：
- SSE envelope 基础字段
- 首批受支持事件：`session.created`、`message.delta`、`message.completed`、`artifact.available`、`permission.required`、`run.completed`、`run.failed`

目标：把“不可信后端载荷”变成可安全消费的前端领域对象。

### 5.2 Replay-safe reducer

在 `application` 中实现纯函数 reducer：
- 按 `event_id` 去重
- 按 `message_id` 聚合 `message.delta`
- `message.completed` 覆盖最终内容
- `run.completed` / `run.failed` 幂等收敛状态

目标：未来无论实时流还是 replay，都走同一条状态折叠逻辑。

### 5.3 Browser shell

在 `interfaces` 中渲染一个首页壳：
- Kokoro 品牌标题
- 协议状态摘要
- 聊天输入占位区
- 会话流时间线卡片
- A2UI / artifact 槽位适配边界

这轮 UI 只消费**本地 seed data**，不接真实网络。

---

## 6. Testing Strategy

### 必测核心

1. **Schema 崩塌测试**
   - 缺字段
   - 多余字段
   - 错误事件名
   - 非法 cursor / timestamp / payload 结构

2. **Replay / idempotency 测试**
   - 同一 `event_id` 重放两次只生效一次
   - 多个 `message.delta` 正确拼接
   - `message.completed` 覆盖 delta 聚合结果
   - `run.completed` 重放不重复改变终态

3. **UI 收敛测试**
   - reducer 输出的 message 列表顺序稳定
   - terminal state 与 permission pending 不冲突

### 验证命令

- `bun run test`
- `bun run lint`
- `bun run typecheck`

---

## 7. Commit Strategy

1. 父仓：提交设计与计划文档。
2. 父仓：提交 `.gitignore` 与交接文件更新。
3. 子仓 `kokoro-web`：提交初始化骨架。
4. 子仓 `kokoro-web`：提交协议 schema + reducer + tests。
5. 子仓 `kokoro-web`：提交页面壳与组件集成。

每次提交只覆盖一个内聚变化。

---

## 8. Success Criteria

本轮完成的判定标准：

- `kokoro-web/` 已创建且是独立 Git 仓库。
- 子仓有独立 `.gitignore`、Bun lockfile、Next.js 工程与 DDD 目录。
- `@a2ui/react`、Tailwind、shadcn/ui 已纳入工程。
- 协议 schema 与 replay reducer 有失败先行的自动化测试，并全部通过。
- 页面能以本地 seed data 渲染出最小聊天壳。
- 父仓已记录 spec / plan / progress，并忽略子仓目录。
