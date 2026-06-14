# Kokoro Protocols

## Purpose

These documents define cross-repository contracts for the Kokoro system.

这里是 **spec-first** 的协议源头：先在 `Kokoro` 仓把语义和边界写清，再到运行时仓落地。

## Repositories

- `Kokoro`: specification source and cross-repository protocol docs

## Current priority runtime repositories

- `kokoro-session`: session/SSE/replay owner and browser-facing session stream producer
- `kokoro-web`: Next.js UI and session stream consumer
- `kokoro-agent`: Python worker and raw execution event producer consumed by `kokoro-session`

其他未来中台仓不是当前优先级；当前跨仓契约的主干先围绕这三个运行时仓收敛。

## Versioning

Each protocol document declares:
- status
- current version
- producer repository
- consumer repository
- backward-compatibility rule

## Rule of use

- 这里定义的是**契约**，不是实现代码
- 浏览器只通过 `kokoro-session` 消费会话流
- `kokoro-agent` 不直接面向浏览器暴露事件流
- 任何 breaking change 先改协议文档，再分别落到运行时仓

## Cross-repo contract change checklist

1. Update the spec in this directory first.
2. Identify which repo owns the boundary:
   - browser-facing session stream: `kokoro-session`
   - raw execution events into session: `kokoro-agent`
3. For browser-facing changes, update `kokoro-session` producer schemas/tests and `kokoro-web` consumer schemas/tests in the same slice.
4. For raw agent-event changes, update `kokoro-agent` emitters and `kokoro-session` agent-event parsing together.
5. Do not let duplicate boundary types drift across repos; if names or payloads change, sync the owner, producer, consumer, and spec before calling the contract updated.
