---
status: 🟡 草稿
layer: flows
owner: claude
updated: 2026-06-14
refs:
  - test:web-preview-fallback
  - test:web-transport-strict-parse
  - test:strict-reject-no-skip
  - test:web-localstorage-persistence
  - test:failure-run-failed-boundary
---

# 流程 · 降级与严格拒收

> 主路径:外部坏了(后端缺席、脏事件、脏存储、模型崩),系统**显性失败或安全降级**,绝不静默污染或整体崩溃。这是「禁止兼容写法 + 显性失败」的流程兑现。

## 验收

**D1 后端缺席降级**
- Given session/agent 不可达
- When 用户提交
- Then 降级到本地预览(可辨提示),不假装成功、不卡死(`test:web-preview-fallback`)

**D2 web 严格解析隔离**
- Given SSE 到达一条畸形/未知 kind 事件
- When web strict 解析(缺字段/多余键即抛)
- Then 单条隔离 skip-and-continue,不污染 thread、不整体崩(`test:web-transport-strict-parse`)

**D3 session 严格拒收(无 skip)**
- Given 进入 session 的载荷畸形
- When zod `.strict()` 校验
- Then 抛 400/拒收,**不**写入 replay;注意 session 入口是**严格拒收非 skip**(与 relay 中继的 skip-and-continue 区分)(`test:strict-reject-no-skip`)

**D4 脏存储降级**
- Given localStorage 有脏数据
- When 加载解析
- Then 丢坏的、保好的,不崩(`test:web-localstorage-persistence`)

**D5 模型/执行异常**
- Given agent 模型解析失败或工具异常
- When 异常冒泡
- Then 落终态 `run.failed`,worker 存活(不崩调度循环);边界外区域行为明确(`test:failure-run-failed-boundary`)

## 不变量来源

strict 拒收 / 畸形 fallback / 幂等 / 空流防御 / 终态关流 — [stream 架构 §5](../../superpowers/specs/2026-06-11-stream-event-architecture-spec.md)。

## 引用

- 契约:[safety-and-permission-envelope](../../protocol/safety-and-permission-envelope.md)
