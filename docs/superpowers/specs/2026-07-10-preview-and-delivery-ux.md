# 产物预览与成果呈现设计（待审）

状态：草案，未获认可（呈现层设计；实现归块D/块7）
日期：2026-07-10
上级：`2026-07-10-agent-system-model.md`；姊妹篇：`2026-07-10-deliver-design.md`（数据层）、`2026-07-10-hitl-design.md`（§7 呈现协议）

## 0. 一句话

> 三层内容面各司其职：**消息流卡片**（发生了什么）→ **canvas 预览**（看内容）→ **成果区**（拿走什么）；文件是过程、成果是结论，两者卡片语义分开，预览体共用一套格式矩阵。

## 1. 现状底子（不重造）

web 已有：`artifact-card`（文件卡+`PreviewBody` 格式矩阵）、`canvas-panel`（manus 式右栏，文件可变重开即最新）、HITL 三卡、snapshot.files 投影。本设计在其上补"成果"维度与联动协议。

## 2. 两种卡片，语义分开

| | 文件卡（现状，保留） | **成果卡（新）** |
|---|---|---|
| 触发 | agent write/edit 文件（"路径即预览"） | `delivery.created` 事件 |
| 语义 | 过程草稿，可变（重开即最新） | **冻结结论**，内容永不漂移 |
| 视觉 | 常规卡 | 强调态（完成徽标/标题/大小/类型），会话内聚合到"成果区" |
| 动作 | 打开 canvas / 下载（当前态） | 打开 canvas（冻结版）/ **下载冻结副本** / （未来）分享·归库 |
| 数据源 | files 端点（可变直读） | deliveries 读接口（content_hash 寻址） |

- 同一文件先有文件卡、后被 deliver：成果卡**另立**（引用 path 与 hash），文件卡不升格——过程与结论并存，历史可读。
- 成果区：会话侧栏/顶部聚合位，列出本会话全部成果（终态一目了然，不用翻消息流）。跨会话"成果库"（用户级，按 namespace 聚合 deliveries 读模型）= 块7 页面，数据层已天然支持。

## 3. canvas 预览协议

- **预览体统一**：`PreviewBody` 格式矩阵是唯一渲染器（md/代码高亮/图片/音频/视频/pdf 按 mime 分派；不支持的类型给下载态）——文件卡、成果卡、HITL 卡三处复用，不做三套。
- **来源双模**：canvas 按"来源"取内容——`file:`（files 端点，可变，重开即最新）与 `delivery:`（deliveries 端点，冻结，带 hash 校验缓存可永久）。成果打开的是冻结版，哪怕原文件已被改/删。
- 深链：卡片点击 → canvas 打开对应来源；canvas 内文件树（现状）补一个"成果"分组。

## 4. 与 HITL 的联动（关键打磨点）

- `write_file` 审批卡：卡内嵌**内容预览**（PreviewBody 复用，args 里的 content 直接渲染）——批之前先看到要写什么；已存在同 path 文件时展示 diff 视图（P1.5，V1 全文预览）。
- `result_review` 审核卡：点击直接在 canvas 打开被审文件（file: 来源当前态）——审的就是看到的。
- 审批决策后卡片落为**已决态**（决策+时间戳保留在消息流，可追溯），不消失。

## 5. 事件→投影协议（web 零轮询）

```text
file 变化事件(现状)        → 文件卡 upsert（同 path 去重,最新态）
delivery.created(块D 新)   → 成果卡 append + 成果区 upsert（(namespace,hash) 幂等）
human.request(HITL v2)     → 对应 kind 卡片挂 pending
run 终态                   → files 面与 snapshot 对账（现状 filesSync 机制保留）
```

刷新恢复：snapshot 补 `deliveries` 字段（与 files 并列），水合即回满三层。

## 6. 收尾环节（一并定）

- **会话能力面板**：会话信息位展示本会话快照（agent、技能卡片清单、pinned、MCP）——只读，让"这个会话能干什么"可见；入口在会话标题/侧栏。
- **fork 按钮**：会话菜单项"以最新能力复制会话"（数据语义见 skills spec §2；实现排能力管理面一波）——按钮位与文案本设计定死，功能后置。
- 空态/加载态/错误态：三层内容面各自明确（成果区空态="完成的成果会出现在这里"）。

## 7. 实施切分

- 块D（deliver 数据层）附带：`delivery.created` 事件、deliveries 读接口、snapshot.deliveries。
- 块D-ux：成果卡/成果区/canvas delivery 来源/审批卡内嵌预览（web 仓，一波）。
- 块7：成果库页面、能力面板、fork 按钮。
