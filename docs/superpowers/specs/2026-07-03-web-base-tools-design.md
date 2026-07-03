# 底层 Web 工具：web_fetch / web_search（2026-07-03）

> 对标 Claude Code 基础工具面（WebFetch/WebSearch/AskUserQuestion）；ask_user_question 已有，
> 本单补齐 web 双件。文件/执行/todo/task 由 deepagents 内置承担，NotebookEdit 等不做（YAGNI）。

## web_fetch（恒挂载核心工具）

- httpx 异步 GET；HTML 经 bs4 提取正文文本（去 script/style），json/text 原样。
- **SSRF 防御**（worker 是服务端进程，非 CC 的本机环境）：仅 http/https；DNS 解析后拒
  loopback/private/link-local/reserved/multicast/unspecified；重定向手动跟随 ≤5 跳、每跳复检。
  残余 TOCTOU（解析与连接间 DNS 重绑）V1 接受并注记。
- 上限：15s 超时、1MB 读取、24k 字符输出（超限带截断注记）。模型侧全文，wire 层由
  tool.returned.truncated 既有护栏承担。
- `KOKORO_WEB_FETCH_ALLOW_PRIVATE=1` 放行内网（本地开发用），默认拒。

## web_search（配置即挂载，无配置不挂空壳；用户裁定后通用化）

- 工具层 tools/web_search.py：SearchProvider 协议 + 格式化，**零 vendor 代码**（测试执法：
  vendor 词汇出现即红）。
- 适配器与工具同文件（用户裁定：一工具一文件）——web_search.py 上半部通用原语、下半部注册表：tavily（vendor-key，langchain 生态常用）/
  searxng（自托管开放标准，无 key）/ zhipu（用户现有生态）——注册表选择，谁都不特权。
  响应统一 parse_hits（url/link、content/snippet 别名归一）TypeAdapter 洗净；非 200 fail-loud。
- 装配：`KOKORO_WEB_SEARCH_PROVIDER` + `KOKORO_WEB_SEARCH_API_KEY`（searxng 用
  `KOKORO_WEB_SEARCH_URL`）配齐才挂载（实证：用户 coding key 无 zhipu web_search 资源包，
  429/1113——故默认不挂）。
- 文件形态（用户裁定）：两个工具文件 web_fetch.py / web_search.py，各一职责。

## 验收

- SSRF 矩阵（file/ftp/127.0.0.1/localhost/[::1]/10.x/169.254.x）全拒；本地 fixture 服务器
  （allow_private）HTML 提取/JSON 原样/截断注记；真实公网 URL 冒烟。
- search：fake provider 格式化；zhipu 响应解析边界矩阵（空结果/缺字段/错误体）。
- 门禁三件套 + 跨栈 e2e 回归；registry/装配测试同步。
