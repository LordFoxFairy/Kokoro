# Claude Code 研究 · 01 · 产品哲学 / 用户心智模型 / 入门流程

> 抓取日期：2026-05-20
> 抓取范围：overview / quickstart / common-workflows / memory / troubleshooting，外加为补充语境而抓的 how-claude-code-works 与 sessions
> 仅为产品哲学与入门主题，Features 详情、settings/hooks/skills/MCP/subagents 不在本文件范围。

---

## 一句话概括

Claude Code 把自己定位为一个 **"运行在你工作环境里的 agentic coding 工具"**——核心心智不是"聊天框里的助手"，而是一个"在你的代码库里读文件、改文件、跑命令、自己验证结果的协作者"，让你像"派活给一位有能力的同事"那样和它工作。

关键证据（逐字引用）：

- overview 开篇副标题：*"Claude Code is an agentic coding tool that reads your codebase, edits files, runs commands, and integrates with your development tools. Available in your terminal, IDE, desktop app, and browser."*
- how-claude-code-works：*"Claude Code is an agentic assistant that runs in your terminal."*
- 风格指南：*"Think of delegating to a capable colleague. Give context and direction, then trust Claude to figure out the details."*
- 反 chatbot 的关键定位：*"This is different from inline code assistants that only see the current file."*

---

## 抓到的 URL 清单（每条 1-3 句要点）

1. **https://code.claude.com/docs/en/overview** — 顶层定位 + 安装入口 + "What you can do" 八条故事板（自动化琐事、建特性/修 bug、commit/PR、MCP、CLAUDE.md/skills/hooks、agent 团队、CLI 管道、定时任务）。强调"同一引擎、多个 surface"。
2. **https://code.claude.com/docs/en/quickstart** — 8 步上手：装→登录→开 session→问"这项目是干嘛的"→改第一处代码→用 git→修 bug 或加特性→其他常见 workflows。明确"像跟同事聊一样跟 Claude 聊"。
3. **https://code.claude.com/docs/en/common-workflows** — 7 大 prompt recipes（探索代码库 / 修 bug / 重构 / 测试 / PR / 文档 / 图片），加 5 个 session 级机制（resume / worktrees / plan mode / 派 subagent / 管道脚本）。
4. **https://code.claude.com/docs/en/memory** — 双轨记忆：用户写的 CLAUDE.md（指令） + Claude 自己写的 auto memory（学习/经验）。详述加载顺序、scope、size 建议、`.claude/rules/` 拆分。
5. **https://code.claude.com/docs/en/troubleshooting** — 性能/稳定/搜索三类问题，附 `/doctor` 自检入口、`/compact` 与"thrashing"恢复路径。强调 session 中断不丢历史，重启可 `--resume` 回来。
6. **https://code.claude.com/docs/en/how-claude-code-works**（补抓）— 解释 agentic loop（gather context → take action → verify → 循环）、tools 五大类、context window、checkpoints、permission modes。
7. **https://code.claude.com/docs/en/sessions**（补抓）— session = 绑定到目录的可命名/可分支/可恢复的对话；transcript JSONL 本地存 30 天；fork vs resume 的区别。

---

## 5 个问题逐条作答

### Q1. Claude Code 把自己定位成什么？

不是"chatbot"，不是"代码补全"，而是 **"agentic coding tool / agentic assistant"**，关键词是 **"agentic"**。

逐字引用：

- overview：*"Claude Code is an **agentic coding tool** that reads your codebase, edits files, runs commands, and integrates with your development tools."*
- overview 第二段：*"Claude Code is an **AI-powered coding assistant** that helps you build features, fix bugs, and automate development tasks. It understands your entire codebase and can work across multiple files and tools to get things done."*
- how-claude-code-works：*"Claude Code is an **agentic assistant** that runs in your terminal. While it excels at coding, it can help with anything you can do from the command line."*
- how-claude-code-works：*"Claude Code serves as the **agentic harness** around Claude: it provides the tools, context management, and execution environment that turn a language model into a capable coding agent."*

关键 metaphor 不是"copilot"也不是"pair programmer"，而是 **"capable colleague / delegating"**：
- *"Think of delegating to a capable colleague. Give context and direction, then trust Claude to figure out the details."*
- *"Talk to Claude like you would a helpful colleague."*

### Q2. 它的核心用户场景是哪几个？

overview "What you can do" 八条用户故事（按官方顺序）：

1. **Automate the work you keep putting off** — 写测试、修 lint、merge 冲突、依赖升级、release notes
2. **Build features and fix bugs** — 自然语言描述需求 → 跨文件实现 + 验证
3. **Create commits and pull requests** — git stage / commit / branch / PR 全语义化
4. **Connect your tools with MCP** — 接 Google Drive、Jira、Slack 等
5. **Customize with instructions, skills, and hooks** — CLAUDE.md / skills / hooks
6. **Run agent teams and build custom agents** — 多 agent 并行 + Agent SDK
7. **Pipe, script, and automate with the CLI** — Unix 管道哲学，可在 CI / pre-commit 用
8. **Schedule recurring tasks** — Routines / Desktop scheduled / `/loop`

quickstart 中给新用户的"第一组任务"是更克制的子集：
- "what does this project do?"
- "add a hello world function to the main file"
- "commit my changes with a descriptive message"
- "refactor the authentication module to use async/await"
- "write unit tests for the calculator functions"
- "review my changes and suggest improvements"

common-workflows 列出的 prompt recipe 类目（按页面顺序）：**Understand new codebases → Find relevant code → Fix bugs → Refactor → Tests → PRs → Documentation → Notes & non-code folders → Images → @-references → Schedules → Ask Claude about its capabilities**。

### Q3. memory / context / session 是怎么分层的？

这是对 Kokoro 多轮对话设计最直接的部分。官方把"持久知识"和"当下对话"明确切成 **3 层**：

1. **Session（当下对话）**
   - 定义：*"A session is a saved conversation tied to a project directory."*
   - 每个 session 起步时拿到一个干净的 context window：*"Each Claude Code session begins with a fresh context window."*
   - 可命名（`claude -n auth-refactor`）、可恢复（`--continue` / `--resume`）、可分支（`/branch` 或 `--fork-session`，复制历史进入新 ID，原 session 不动）
   - 本地存为 JSONL：`~/.claude/projects/<project>/<session-id>.jsonl`，默认保留 30 天

2. **Context window（这一轮里 Claude 实际看到的东西）**
   - 内容：*"Claude's context window holds your conversation history, file contents, command outputs, CLAUDE.md, auto memory, loaded skills, and system instructions."*
   - 自动管理：*"Claude Code manages context automatically as you approach the limit. It clears older tool outputs first, then summarizes the conversation if needed."*
   - 用户可见工具：`/context`（看占用） / `/compact [focus]`（带方向地压缩） / `/clear`（清空但 session 仍可 resume）

3. **跨 session 的持久知识（两个并行机制）**
   - **CLAUDE.md（人写的指令）**：放规则、规范、build 命令。多层级（managed / user `~/.claude/CLAUDE.md` / project `./CLAUDE.md` / local `./CLAUDE.local.md`），加载顺序由广到窄，全量进 context
   - **Auto memory（Claude 自己写的学习）**：每个项目一个 `~/.claude/projects/<project>/memory/`，入口是 `MEMORY.md`，只前 200 行/25KB 自动加载，其他 topic 文件按需读
   - 关键引言：*"Claude Code has two complementary memory systems... Use CLAUDE.md files when you want to guide Claude's behavior. Auto memory lets Claude learn from your corrections without manual effort."*

补充：**compaction 之后的"什么会幸存"是被明确文档化的**——project root 的 CLAUDE.md 会在 `/compact` 后从磁盘重读重新注入；conversation-only 的指令则可能丢。这是个非常用户友好的设计承诺。

### Q4. 入门门槛长什么样？

低到极致——**"装 + 登录 + cd + 一句 `claude`"四步**。

quickstart 的 Step 1-3 几乎只是装+登录+`cd /path && claude`。Step 4 让新用户问的第一句话不是"教我用"，而是：

- *"what does this project do?"*
- *"what technologies does this project use?"*
- *"where is the main entry point?"*

也就是说，**入门的"第一价值"是让 Claude 立刻干一件有用的事（解释这个项目），而不是让用户先学 Claude 怎么用**。

关键 UI 承诺：*"Claude Code reads your project files as needed. You don't have to manually add context."* —— 没有"上传文件"、"选模型"、"选模式"这类前置摩擦。

第一次打开的 welcome screen：*"You'll see the Claude Code welcome screen with your session information, recent conversations, and latest updates. Type /help for available commands or /resume to continue a previous conversation."*

Step 5 是关键的"信任建立"步：*"Claude Code always asks for permission before modifying files."* —— 通过"先 propose 再让你 approve"建立用户对 agent 的信任，而不是默认放权。

### Q5. 它如何向用户解释"这是 agent 不是普通 chatbot"？

四个手法：

**(a) 反复使用 "agentic" 这个词作为差异化锚点**，并配一张图：how-claude-code-works 有一张 `agentic-loop.svg`，alt 文本是：*"The agentic loop: Your prompt leads to Claude gathering context, taking action, verifying results, and repeating until task complete. You can interrupt at any point."*

**(b) 三阶段叙事**：*"it works through three phases: **gather context**, **take action**, and **verify results**."* —— 不是"问→答"，而是"理解→动手→自检"。

**(c) 直接拿 inline assistant 作对比**：*"Because Claude sees your whole project, it can work across it... This is different from inline code assistants that only see the current file."*

**(d) "delegate, don't dictate" metaphor**：

> *"Think of **delegating to a capable colleague**. Give context and direction, then trust Claude to figure out the details: 'The checkout flow is broken for users with expired cards. The relevant code is in src/payments/. Can you investigate and fix it?' You don't need to specify which files to read or what commands to run. Claude figures that out."*

**(e) "Conversational, not one-shot" 配合"可打断"**：
- *"It's a conversation"*（小标题）
- *"Claude Code is conversational. You don't need perfect prompts. Start with what you want, then refine."*
- *"You can interrupt Claude at any point. If it's going down the wrong path, just type your correction and press Enter."*

---

## 给 Kokoro 的具体启示（5 条，可落地）

### 启示 1 ｜ 给 Kokoro 一个"反 chatbot"的产品定位句

不要把 Kokoro 写成 *"AI assistant for conversations and Canvas"*，那等同于 ChatGPT 的描述。借鉴 Claude Code 的 "agentic X" 公式，Kokoro 应该有一句 **"agentic + 它实际在做的具体动作"** 的开篇——例如 *"Kokoro 是一个 agentic Canvas 助手，它读你的 Canvas、改你的 Canvas、把对话变成可执行的产物"*。

落地：改 `README.md` 顶部副标题 + Web 首页 hero copy。这一句决定用户进来第一秒的预期。

### 启示 2 ｜ 把"记忆"切成 3 层而不是一层

Claude Code 的 **session / context window / 跨 session 持久知识（CLAUDE.md + auto memory）** 三层架构，是对 Kokoro "多轮对话 + Canvas" 直接可借鉴的设计模板：

- **Session 层（当下这次对话）**：可命名、可恢复、可分支（用户随时 fork 出一条对话试另一个方向，原对话不动）
- **Context window 层**：自动管理，但给用户 `/context` 这样的可见性入口和 `/compact [focus]` 这样的可控压缩
- **跨 session 持久层**：分"用户写的规则"（类 CLAUDE.md，例如"我的写作风格"）和"AI 自己学到的"（类 auto memory，例如"用户喜欢简短回复"）

落地：
- 在 Kokoro 的 conversation 模型里加 `name`、`forked_from` 字段，前端加 `/branch` 操作
- 在用户设置页加"我的指令"（用户写）和"Kokoro 记住的"（AI 写、用户可审查可删除）两个分区，而不是合并成一个"个性化"

### 启示 3 ｜ 第一次打开，让 Kokoro 立刻干活而不是教用户怎么用

Claude Code quickstart 的 Step 4 让新用户的第一句话是 *"what does this project do?"*——它在示范"你不用学我，你直接用我"。

Kokoro 的 onboarding 应该模仿这个心智：用户首次进来，**默认 prompt 提示不应该是"试试问我任何问题"**，而是 **"我可以帮你做：① 把对话整理成 Canvas ② 续写你的 Canvas ③ 解释你 Canvas 里的某段"** —— 三个具体动词，让用户点一下就看到价值。

落地：改 Kokoro 首次空状态（empty state）的 placeholder + suggested prompts。

### 启示 4 ｜ "Propose → Approve" 模式建立信任

Claude Code 默认不直接改文件，而是 *"Show you the proposed changes / Ask for your approval / Make the edit"*。这对"AI 改用户的 Canvas"这种破坏性操作尤其重要。

Kokoro 在让 AI 改用户 Canvas 时，**应该有"先给 diff 预览、用户确认才落盘"的默认模式**（对应 Claude Code 的 default permission mode），同时提供"Auto-accept edits"开关给信任度高的用户（对应 Claude Code 的 Shift+Tab 切换）。**checkpoints / "Esc Esc 撤回"也是关键**：让用户敢让 AI 动手的前提是"动错了能秒回滚"。

落地：
- Canvas 的 AI 修改默认走 diff 预览路径
- 每次 AI 写入 Canvas 前 snapshot，给用户一键回滚（Claude Code: *"Every file edit is reversible"*）
- 设置里给"信任模式"开关

### 启示 5 ｜ 对话是可打断、可分支、可恢复的，不是线性的

Claude Code 的 *"You can interrupt Claude at any point"* + `/branch` + `claude --resume` 三件套，定义了一种 **非线性对话**：用户随时可以打断、复制一份去试另一条路、几天后回来续上。

这对 Kokoro 的 Canvas 协作场景非常贴：用户经常会"AI 正在写第三段时，我想让它换个方向"或者"我喜欢这一版，但我也想看看另一种风格"。

落地：
- 流式生成时给"打断 + 改指令"按钮（不是只能"停止"，而是"停止 + 继续写但改方向"）
- 对话页有"从这里 fork 一份"操作
- 历史对话默认可恢复，不是删档式的"new chat"

---

## 未抓到的 URL 清单

- 无。本任务的全部 5 个起步 URL 都抓到了内容（memory / troubleshooting 都返回 200 + 完整 markdown）。
- 补抓的 `how-claude-code-works` 和 `sessions` 也都返回了完整内容。
