# ADR-007 kokoro-platform 纳入受控子模块

状态：已采纳（2026-06-28）。

## 背景

kokoro-platform 长期在 `.gitmodules` 中声明，却从未作为 gitlink 提交进主仓树（一直是 untracked）。审计 M7 指出它"尚未纳入任何 ADR，要么补 ADR、要么移出规划区"；ADR-009 又规定主仓只承载 docs/protocol/原型、不承载运行时代码。三者叠加形成"声明了却不跟踪"的混合态：GitHub 主仓页面看不到它，版本也无法被复现锁定。

## 决策

把 kokoro-platform 作为受控 submodule 纳入主仓，与 kokoro-agent/session/web 一视同仁：

```text
.gitmodules 增第 4 条：path=kokoro-platform，url=…/kokoro-platform.git，branch=main。
gitlink 指向其 main 最新且已推送的 commit（首次 c6eff6a）。
主仓只记录指针（gitlink），不承载其运行时源码。
```

## 理由

```text
平台域（site/user/model/credit/payment/litellm）是本手册的核心模块，需要可复现地锁定版本。
与运行时三仓统一管理，消除"四仓声明、三仓跟踪"的不一致。
gitlink 是版本指针不是源码，纳入它不违反 ADR-009（主仓不承载运行时代码）。
```

## 约束

```text
指针 bump 是显式动作：子仓 main 前进后，须在主仓 git add 子模块再提交，git 不会自动跟。
gitlink 指向的 commit 必须已推送到子仓 main，否则 GitHub 上是坏链。
branch=main 仅供 git submodule update --remote 拉取，不改变页面显示（页面恒显示 SHA）。
不把 kokoro-platform 源码合并进主仓（保持四仓独立，见 ADR-009）。
```

## 替代方案（已否决）

```text
仅跟踪运行时三仓（审计 M7 现状）   平台域在手册中是核心，却不可复现锁定，自相矛盾。
把 kokoro-platform 源码并入主仓     违反四仓独立边界（ADR-009）。
```

## 影响

`.gitmodules` 变为 4 条；主仓 main 显示 4 个子模块；仓库地图随之更新。落地提交为注册 gitlink → c6eff6a 的那次提交。后续子仓前进按上述约束手动 bump 指针。

相关：[ADR-005 MySQL 与 Mongo 数据边界](ADR-005-mysql-and-mongo.md)、[仓库地图](../technical/01-repository-map.md)、[kokoro-platform 模块](../modules/kokoro-platform.md)。
