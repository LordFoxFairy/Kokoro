# Kokoro MCP 完整技术方案（已实现，供裁决）

状态：**已实现（块3b，417 tests 三绿）——但设计未经你逐案认可，本文供裁决；有异议代码跟改**
日期：2026-07-10

## 0. 一句话

> MCP server 的定义与凭据住 agent 侧部署配置，wire 只传 names；模型永远只见三个恒定工具（list/describe/call），server/tool/schema 全是工具返回的数据——远端怎么变都动不了前缀。

## 1. 配置（server 定义在哪）

agent 侧部署 yaml（`KOKORO_MCP_CONFIG`），不上 wire、不进 ledger：

```yaml
servers:
  github:
    url: https://mcp.example/github
    allowed_tools: [search_issues, create_issue]   # 白名单外的工具模型永远看不见
    timeout_s: 10
    headers:
      authorization: ${GH_MCP_TOKEN}   # 凭据只走 env（整值占位），yaml 里只有引用名
```

- `${ENV}` 引用缺失 → 启动 fail-loud（绝不带残缺凭据连接）。
- 进程环境只在 worker/main 读取（架构测试钉死），配置加载函数由调用方显式注入 env。

## 2. wire（session → agent）

`RuntimeConfig.mcp_servers: string[]`——只有名字。旧的 `McpServer` 明文对象（含 headers）已从契约删除，负向测试钉死：wire 里出现对象/headers 直接被 strict 契约拒收。

## 3. 运行时（恒定三工具）

```text
mcp_list_tools()                  → 各授权 server 的工具摘要（server/tool — 描述首行）
mcp_describe_tool(server, tool)   → 该工具的参数 schema（此刻才暴露给模型）
mcp_call(server, tool, arguments) → 真实调用，结果序列化返回
```

- **装配期零连接**：只校验 names（未知名 fail-loud，配置即授权边界）；首次使用才连——run 启动不再被挂掉的 server 拖死。
- run 内按 server 缓存 tools/list（一次连接，list/describe/call 共享）。
- **运行时不可达 = 外部常态**：降级为该次调用的 error 文本（模型可自纠），不炸 run。
- 白名单（allowed_tools）外的工具在 list/describe/call 全不可见。

## 4. 前缀账（为什么必须三工具而不是动态注册）

动态注册（把远端工具展开进模型工具面）时，tools 块在 API 前缀最前——远端 server 的 schema/顺序漂移（完全不受我们控制）会打穿同会话全部缓存,等效每次新会话。三工具下 server 集 A/B/空 切换,工具面**逐字节相同**（测试钉死）。

## 5. 与 skills 的池模型关系

同为"池自动注入、用户不逐消息勾选"，但池的性质不同：skill 是静态文本（可海量），MCP 是活的外部连接（有凭据副作用、天然少量）。入池动词：skill=添加，MCP=**连接**（显式授权，ChatGPT connectors 心智）。

## 6. 测试（审核修订：真件为主）

- **主体用真 FastMCP server**（进程内起,已有先例）：白名单过滤、懒连接+run 内缓存、list→describe→call 真往返、不可达降级——真传输真协议。
- fake client 仅兜底极难真跑的分支（如连接计数断言），归 test 替身纪律管理。
- 配置层：`${ENV}` 展开/缺失 fail-loud、未知名装配期炸、三工具面逐字节恒定。
- （现状实现为 fake 为主+一条 live——按本节要求在块C 期间翻转比例。）

## 7. 边界与后续

- V1：server 集部署静态。用户"连接自己的 MCP"（写面+设置 UI）= 后续块。
- 危险工具的 approval policy（进 HITL）= 后续（现走 permissions.approval_tools 逐名配置）。
- secret-ref/gateway 服务 = P2（V1 凭据即部署 env）。
