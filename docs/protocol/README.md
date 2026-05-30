# Kokoro Protocols

## Purpose

These documents define cross-repository contracts for the Kokoro system.

这里是 **spec-first** 的协议源头：先在 `Kokoro` 仓把语义和边界写清，再到运行时仓落地。

## Repositories

- `Kokoro`: specification source
- `kokoro-web`: frontend consumer
- `kokoro-session`: session transport owner
- `kokoro-agent`: execution event producer

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
