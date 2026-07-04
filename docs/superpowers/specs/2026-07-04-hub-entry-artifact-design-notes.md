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

## 一·v2 修订：用户资产库（用户指正：初版是管理员视角，漏了 C 端自助维度）

**统一概念——"用户资产库"**：用户在 web 上拥有并随身携带的三类资产同构管理：
skills（技能包）、MCP 配置（含个人凭据）、agent 预设（自定义子代理/入口人格）。
作用域从三级修为**四级**：

    platform 公共库 → namespace 团队库 → user 个人库 → entry/session 选择

**遮蔽与治理**：同名冲突=更近者胜（entry > user > namespace > platform），但
namespace 政策可**禁用/限制 user 资产**（企业治理：技能=提示注入面，团队空间可要求
只用审核过的）。信任分级：platform=官方审核 / namespace=管理员审 / user=自担，
user 级资产默认只作用于本人会话。

**UGC 生命周期**：上传（web 表单/文件包）→ 校验（SKILL.md schema/大小/敏感内容 lint）
→ 存储+lock(sha256) 版本化 → 挂个人库 → 可分享提升（user→namespace 采纳、
namespace→platform 投稿审核）→ **下载/导出**（打包 zip，格式与 CC 目录约定兼容
——数据可携带，也是与 CC 生态互通的入口）。

**被用户维度暴露的两个契约缺口（实锤）**：
1. `McpServer` 无凭据字段——个人 MCP（自带 token）上不了 wire。补法：加 `headers?`
   （V1 直传，内网）；升级路径=改传 secret 引用、worker 从密钥托管取（用户私钥
   绝不进 namespace 可见面）。
2. `user_id` 此前因无产无消从契约移除（当时正确）；用户资产库是它回归的真需求
   触发点（连带记忆按人分层）——**auth 先行，字段随用而归**。

**放置结论不变且更清晰**：hub 全部归 platform/session 侧（含用户库的 CRUD/上传下载面）；
agent 仍是纯消费者——四级作用域在 session resolve 合并成最终 RuntimeConfig，
agent 契约除上述两个字段外零改动。

## 优先级建议（v2）

1. hub 数据模型+用户库上传/下载（platform/session 面，等产品排期）；
2. McpServer.headers 契约补齐（小，可先行——个人 MCP 的最小可用）；
3. auth/user_id 回归（hub 与记忆按人分层的共同前置）；
4. 产物（等 canvas 消费面）；入口切换零改动已成立。

## 一·v3 修正（用户指正：user 不是独立轴——单轴归一）

v2 的"user 层级 + user_id 回归"**违背既定法律**（namespace 模型：teams/个人=namespace 实例）。修正：

    platform 公共库 → namespace 库 → entry/session 选择   （单轴）

- 用户资产库 = 用户**个人 namespace** 的库；上传/下载/管理落在自己的空间。
- 跨空间携带 = **namespace 间资产授权（grant/import）**：个人→团队采纳、团队→平台投稿
  是同一个动词，经目标空间治理审批。
- 记忆按人分层自然消解：个人记忆=个人 namespace 的 store 前缀（现机制原样覆盖）；
  团队会话引用个人记忆=同一跨空间授权问题。
- **user_id 永不进 agent 契约**（此前删除是永久正确）；auth/成员关系全归 platform/session
  成员模型。信任分级改述：platform 官方审 / 目标 namespace 管理员审 / 个人 namespace 自担。
- agent 含义：零改动——单轴 namespace 已是完美消费者形态；用户自定义 subagent/入口预设
  = 个人 namespace 的 agents 表项，grant 机制同上。

**防漂移法则（lessons 收录）**：空间/身份一律收敛 namespace 单轴，任何"再加一条身份轴"
的设计冲动即红灯。
