---
status: 🔴 待用户拍板        # 🟢 已定 / 🟡 草稿 / 🔴 待用户拍板
layer: capabilities          # product / capabilities / flows / contracts
owner: claude                # 谁起草
updated: 2026-06-14
refs:                        # 链到 ADR / protocol / spec / 测试 slug;流程层必含 ≥1 个 test:
  - ADR-xxx
  - test:web-xxx
---

# <标题>

> 一句话:这篇约束什么。

## 需求

系统**必须**做什么。用「必须 / 应当 / 不得」表述,可验证、不含实现细节。

## 验收

> 流程层用 Given/When/Then;能力层用条目化断言。每条对应 `refs` 里的 test slug。

- [ ] ...

## 不做 / 边界

明确不在本篇范围、留给扩展位或其他层的部分。

## 引用

- 契约/实现细节链过去,不复制:[protocol/...](../../protocol/...) · [spec/...](../../superpowers/specs/...)
