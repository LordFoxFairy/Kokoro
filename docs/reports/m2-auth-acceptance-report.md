# 验收报告（含测试明细）：M2 鉴权主线 + 失败可读性

- 日期：2026-07-06
- 规格：technical/15 §3 P1（鉴权）/ P2（失败可读性）
- 设计原则（用户裁定）：不复杂化——零新依赖、开发零配置不变、单一裁权收口

## P1 鉴权：验收判据 vs 结果

| # | 判据 | 结果 | 证据 |
|---|---|---|---|
| 1 | 未配 secret = 直通模式（开发零配置不变，owner=本地常量） | **通过** | AU-1；verify-all/既有全套在无 secret 下原样绿 |
| 2 | 配 secret = 全路由强制 Bearer JWT（HS256），无/坏/过期 token → 401 | **通过** | AU-2 / AU-4；HS256 手写验签（node:crypto timingSafeEqual，零新依赖） |
| 3 | owner = payload.sub，会话归属固化到属主 | **通过** | AU-2（session.owner_id=sub） |
| 4 | 属主裁权：他人会话六路全 403 session_forbidden | **通过** | AU-3（messages/snapshot/events/files/control/delete 六路）；单一收口 rejectIfDeleted |
| 5 | 跨栈闭环：web 全请求（含 SSE）携 token | **通过** | client token 注入 + shell localStorage 通道；E2E-30 |
| 6 | 真栈 auth-on：gate 全程强制模式跑全部断言 | **通过** | verify-all 六档 PASS（四 gate 变体 auth-on + chaos 跨 pod 收养在鉴权下）；E2E-30 负例 401/403 |

## P2 失败可读性

前几轮已交付（run.failed 契约三层码 + web failureCopy 文案表 + enqueue/assembly
区分 + 重试按钮语义），本轮收口确认，无新改动——按"不复杂化"不重复造。

## 设计边界（入册）

```text
agent 侧不加 user 维度：信任边界=session（RunRequest 只能由 session 从内网 Redis
  投递，agent 不直面公网）。审计⑥的同租户互访由属主裁权在 session 唯一入口收口。
token 签发归 platform 用户体系（session 只验不签）；web 侧 token 暂经 localStorage
  kokoro.auth.token 注入——platform 登录接入前的部署方通道，登录 UI 属 platform 主线。
HS256 单密钥：多租户/密钥轮转/RS256 等属 platform 身份体系演进，V1 不投机实现。
```

## 结论

**验收通过。** M2 鉴权主线以最简正解落地：零新依赖、开发零配置不变、生产一个
env 开关 + 一处裁权收口；失败可读性沿用既有交付。测试：session 194 / web 176 /
gate 全程 auth-on + E2E-30 / verify-all 六档 PASS。
