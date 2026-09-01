# General Chat 产品手册

状态：当前 Feature-first General Chat 定义，2026-08-22。`FEATURE_KEY_GENERAL_ASSIST` 是用户进入的产品 Feature；GA 内部
Workflow 决定 single/lead/swarm/flow，Session 不存 Agent、member、Skill/MCP、图或模型配方。详见
[General Chat 链路](../business-flows/general-chat.md)；产品结果、质量/成本 baseline 与上线门见
[41 Feature 结果契约](../technical/41-feature-outcome-contracts-and-quality-gates.md)。

## 定位

General Chat 是 Kokoro 的通用入口。用户用自然语言表达任务，系统判断是否需要调用工具、Agent、模型、Studio 能力或生成产物。

## 用户任务

```text
询问和解释
  知识问答、资料解释、文本润色。

轻量创作
  写文案、生成想法、规划内容、创建初稿。

能力调用
  生成音乐、图片、视频、代码等，以简化参数完成。

任务编排
  让通用 Agent 调用专业 Agent、skill、MCP、模型或工具。

产物管理
  查看生成结果、继续修改、保存到项目或导出。
```

## 界面原则

```text
第一屏是可用的聊天体验，不做营销页式假入口。
输入框是核心，不用复杂表单阻碍开始。
复杂参数逐步暴露，用户需要时再打开。
能力结果以 artifact card 展示，不把所有结果塞成纯文本。
agent 活动流可展开，但默认不干扰主阅读。
```

## 能力呈现

General Chat 中的能力是简化版：

```text
music.generate   一句话生成歌曲草稿。
image.generate   一句话生成图片。
video.generate   一句话生成短视频草稿。
code.generate    一句话生成脚本、页面或工具。
```

任务复杂时，General Chat 可以建议进入 Studio，但不强制跳转。用户可继续在对话中完成，也可进入专业工作台。

## 与 Agent 的关系

General Chat 是 Chat App 的 `FEATURE_KEY_GENERAL_ASSIST` Feature：它由 General Assistant 为 entry，需要时以 GA 已发布的 Agent
组合 Music、Image、Video、Code 专员。产品结果契约要求安全 assistant final，并按任务允许 Job/Artifact card；内部成员、图和
work_profile 仍只属于 GA。统一入口、App/Feature 与组合关系见 [37 Kokoro 统一入口、App 与 Agent 产品架构](../technical/37-product-experience-agent-studio-architecture.md)；GA 内部编译与恢复见 [36 GA 整体 Agent 技术方案](../technical/36-ga-final-agent-technical-plan.md)。

通用 Agent 可以：

```text
调用专业 Agent、skill、MCP、模型。
通过 Studio public `CreateJob/QueryJob` 创建 job、查询进度和 artifact。
消费报价、hold、终态和退款结果；不拥有或直调 Credit。
```

通用 Agent 不可以：

```text
直接扣积分。
直接写 payment order。
绕过 session 发浏览器事件。
绕过 siteId 访问其它站点数据。
```

skill 和 MCP 的产品形态见 [06-skill-hub-and-mcp-hub](06-skill-hub-and-mcp-hub.md)。

## 与 Studio 的关系

General Chat 和 Studio 共享底层能力，但不是同一个 UI。

```text
General Chat   用户表达意图，系统帮忙选择路径。
Studio         用户进入明确专业对象，控制参数和版本。
```

General Chat 可以把一个对话结果升级为 Studio project：

```text
用户: 帮我做一首适合广告的电子乐
系统: 生成 music job
结果: 展示草稿
用户: 进入 Music Studio 精修
系统: 用 artifact/job/project 创建 studio workspace
```

## 计费

General Chat 走 `general.*` featureKey，与 Studio 的 `studio.*` 分开计价。扣费走 credit 闭环，见 [../business-flows/credit-reserve-commit-refund.md](../business-flows/credit-reserve-commit-refund.md) 和 [07-pricing-credit-plans](07-pricing-credit-plans.md)。

## 成功指标

```text
用户能在 30 秒内开始第一轮有效任务。
非专业用户能完成轻量 music/image/video/code 请求。
专业任务能自然升级到 Studio。
agent 活动可解释但不喧宾夺主。
```

## 后续任务

```text
P0  定义 General Chat 的 featureKey。
    定义 artifact card 基础结构。
    定义通用 Agent 调用专业能力的业务链路。
P1  能力推荐和参数渐进展开。
    对话结果转 Studio project。
    对话内报价和扣费提示。
```
