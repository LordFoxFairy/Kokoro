# 三题设计思考：skills/MCP hub · 入口切换语义 · 产物放置（2026-07-04，讨论稿）

## 一、Skills / MCP Hub（参照 Manus / Claude Code）

**标杆拆解**：CC 是文件系统约定（用户级 ~/.claude/skills、项目级 .claude/skills、plugins 市场
分发），无中心服务，git 即分发。Manus 是平台托管的云端库（每用户知识/技能库，挂到 run）。
Kokoro 是多租户平台 → 取 Manus 形态、留 CC 格式。

**三级作用域**（skills 与 MCP 同构）：
1. platform 公共库（官方/审核过的技能与 MCP server 目录）
2. namespace 库（团队私有注册 + 对公共库的启用与密钥绑定）
3. entry 绑定（入口技能包——已实现 entry.skills）

**放哪（关键结论）**：**hub 归 platform/session 侧**（管理面 CRUD/审核/版本/分发）。
agent 已经是干净的消费者——wire 只认 `SkillMount{name,path,lock}` 与 `McpServer`，
**agent 契约与代码零改动**。hub 的实体是：存储（对象存储/git）+ 同步器
（把技能文件铺到 worker 可读路径；e2b 落地后直接注入沙箱=同一机制）+ lock(sha256)
完整性（已有）。SKILL.md 格式与 CC 对齐，将来支持"从 git 导入技能包"。

**动态变动**：agent 侧本就每 run 装配（换内容换 lock 下一 run 生效）；hub 只需在变更时
更新 profile 里的 lock——不存在 agent 侧缓存失效问题。

## 二、入口切换的上下文语义（session 不变，entry 切换）

**机制现状即正解**：system prompt 是每 run 装配参数，**不进 checkpoint**；messages 历史在
checkpoint 里连续。所以切换 entry 天然=**人格整体更换 + 历史完整保留**：
- 人格必须"更换"而非"追加"——人格叠加=人格污染（两套行为约束互相打架）；
- 历史保留是用户期望（同一会话的上下文延续）；skills/MCP 变动同理随 run 生效，
  旧技能的历史产出仍可读。

**唯一细节风险**：新人格会把旧人格说的话当成"自己说的"。三档处理：
a) 不处理（模型通常能顺，V1 默认）；b) 切换时注入一条边界标记消息（"自此轮起你是 X"）
——一行装配逻辑，需要时再加；c) swarm 落地后 entry 切换收敛为 handoff 特例
（"谁在说话"被显式化）——用户直觉正确，不为此预建机制。

## 三、agent 产物放置（结合 langchain 构造）

**langchain 原生件**：`response_format="content_and_artifact"`（工具返回"给模型的摘要 +
完整产物"两份，产物不烧上下文）+ deepagents backend 文件系统（write_file）。

**分层放置**：
- **产物本体** → 沙箱文件系统，路径约定 `/artifacts/{run_id}/...`（state 虚拟盘 /
  local_shell 真盘 / e2b 沙箱；e2b 后归档到对象存储）；
- **产物引用** → wire：`tool.returned.artifact_ref`（契约位早已预留，P1 生产者就是这单）；
- **产物读取** → session HTTP 产物端点（canvas 预览消费；web 不看全文的既有定调闭环）。

**agent 侧实施形态（届时）**：产物类工具用 content_and_artifact 返回；一个登记环节
（工具包装或 after-tool middleware）把落盘产物翻译成 artifact_ref 上 wire。
与 canvas/上传面同批做，避免只有生产者没有消费者。

## 优先级建议

hub（需要 platform 管理面）与产物（需要 canvas 消费面）都是**跨面单元**，agent 侧改动小、
等产品面拍板同批做；入口切换 V1 语义已成立（零改动），标记消息按需一行加。
