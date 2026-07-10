# Kokoro Skills 完整技术方案 v2（待审）

状态：**草案 v2（吸收生产级参考的抽象设计后重写），未获认可，代码冻结中**
日期：2026-07-10
定位：skills 从格式、存储、池与状态、会话快照、加载物化、模型使用到测试的完整方案；认可后回灌 handbook `20` 并解冻实现。

## 0. 生态对齐（不自造规范）

- 格式 = **Agent Skills 开放规范**（目录 + `SKILL.md` frontmatter: name/description + 附件），字节兼容 CC / 开放技能生态——用户未来可直接导入 GitHub 上的技能包。
- Kokoro 定义的只是"多租户云端怎么存、怎么进会话、怎么进沙箱"。

## 1. 存储分层（Mongo = 元数据+正文快照；S3 = 包体权威源）

```text
Mongo `skills`（元数据 + 高频读的正文）:
  scope             # "official" | <namespace>     —— (scope,name) 唯一索引
  name, display_name, description                  # frontmatter 提取,入库强校验
  skill_md          # SKILL.md 全文快照（正文高频小,读它不碰 S3）
  files_manifest    # [{path, size}]（附件清单,不含内容）
  file_count, package_size
  content_hash      # 整包 sha256 —— 唯一版本标识/内容锁
  package_ref       # S3 包体键
  source            # deploy | upload | github
  revision          # 文档级 CAS,防并发写半截
  official_enabled, official_required              # 官方状态位(visible/read_only 后续管理面加)
  updated_at, deleted_at                           # 软删=状态位

S3（minio,S3 协议——后续换 AWS/R2 仅换 endpoint 配置）:
  skills/{scope}/{name}/{content_hash}.zip         # 内容寻址,不可变;发布时预打包
```

- **分层理由**：正文（小、高频、进模型）走 Mongo 直读；附件（可大、低频、进沙箱）走 S3——30MB 级包也不压库。
- `per-user 启停`独立小表 `skill_state {namespace, name, enabled}`——用户偏好不改共享本体；`official_required` 的技能默认注入、拒绝关闭。

## 2. 会话快照（动态死局的解法,已与你对齐的方向；v2.1 修正内容锁实现）

- **session 创建（首条消息）一次定死**,快照直接存进 session 文档：
  `session.agent + agent_hash`、`session.skills = [(name, content_hash, description)]`（enabled 池**卡片全量**快照）、`session.pinned_skills`（输入框显式选的,清单置顶强调）、`session.mcp_servers`。后续消息带不同值 → 400。
- **清单零查询**：装配时清单段直接由 session 快照的卡片渲染——不再回查池,恒定是数据结构自带的,不靠查询纪律。
- **内容锁的真源 = S3**（v2.1 修正:Mongo 表是覆盖 upsert,旧版正文只在 S3 的内容寻址 zip 里永存）。正文取回双路：hash==库当前版 → Mongo `skill_md` 快读；老版（官方已升级的进行中会话,罕见路径）→ 按 hash 从 S3 取 zip 解包。物化恒按 hash 取 S3,天然锁。
- **wire 字段名实相符**：首条消息的字段是 `pinned_skills`（强调语义）；授权池快照由 session 查 enabled 自动完成,**不上 wire**。
- **跨语言读池走单源生成**：session(TS) 读池集合的文档 schema 进 `contract/spec/storage.yaml`,生成 zod+pydantic 双镜像（复用既有生成器）——不手写两份会漂移的 schema。
- **fork**：复制消息史开新会话 + 能力按当前池重新快照（"新 thread 首 run 重放注入",复用既有 message_id 去重）。排期在能力管理面一波。

## 3. 加载与物化（names+hashes → 沙箱映射）

```text
run 装配:
1. resolve: 按 session.skills 的 (name,hash) 查 Mongo → 卡片(name/description/skill_md/manifest)
2. 清单段进 system prompt（含 pinned 置顶）——session 快照下整会话恒定
3. 物化（有附件的包才需要）:
   - 已物化账本记在 graph state（checkpoint 态 → 跨 worker/resume 天然一致）: {name: hash}
   - hash 未变 → 跳过;变更/新增 → S3 取 zip 解包 → backend.upload_files → /.skills/<name>/**
   - /.skills 目录缺失（e2b 暂停被销毁重建）→ 强制全量重写,自愈
   - 会话不含的旧目录 → GC 删除（沙箱残留不是权限,但也不留噪音）
   - 加固（可选项）: 写完收回写权限,防模型自改技能
   - 单包物化失败不阻断整体（该技能标记不可用,其余照常）
4. e2b/docker/local 统一走 backend 口;e2b 经 ledger 重连既往沙箱,重建场景由第 3 步自愈
```

## 4. 模型怎么发现与使用（生产验证的形态）

- **发现 = 清单常驻**（system prompt 技能区,name+description+入口路径,pinned 置顶）。无 find、无检索、无向量。
- **使用 = `skill(name)` 单工具为主路**：返回 SKILL.md 正文 + 显式路径引导（"该技能文件位于 /.skills/<name>/,相对路径需拼接此前缀"）+ **已加载去重**（同会话重复调用返回短提示,不重复灌正文——控历史膨胀）。
- 附件 = 模型用现有文件工具按需读、`execute` 直接跑（已物化在沙箱）。
- 为什么保留工具而不是让模型裸读文件：正文直返省去模型拼路径读大文件的失误面,且去重/引导都挂在工具上——这是生产环境验证过的模型交互形态。

## 5. 入库校验（安全清单,upsert 时强制）

name 正则（小写/长度上限/保留字拒绝）、description 长度、frontmatter 完整性、**尖括号注入拒绝**（name/description 不得含 `<>`——防 prompt 注入清单）、zip 路径穿越拒绝、单一公共根目录、文件数与包大小配额。校验失败 fail-loud 不入库。

## 6. CRUD 面与实施范围

| 面 | 内容 | 排期 |
|---|---|---|
| hub 模块（agent 仓） | upsert/fetch/list_pool/mark_deleted + 校验器 + S3 发布 + CAS | **本块（块A）** |
| 官方 seed | 部署目录 → upsert(official)，hash 未变不写；不覆盖运营态状态位 | **本块（块A）** |
| session 快照 | agent/skills+hashes/pinned/mcp 首条定死 + 400 | **块B**（session+contract） |
| 装配物化+清单+skill 工具 | 上文 §3§4 | **块C**（agent 仓） |
| 用户上传/GitHub 导入（preview→confirm 两步）、启停 UI、配额、管理面、fork | 写面与产品面 | 后续逐块 |

## 7. 测试策略（真件全链路）

fixture=磁盘真实技能包目录；链路=真扫描 → seed → **真 Mongo + 真 minio**（docker,本仓 test 口径）→ 装配断言。覆盖：seed 幂等/内容更新不影响已快照会话（内容锁）/namespace 覆盖 official/required 强制注入/校验清单逐条负向/物化 hash 增量与缺目录自愈/GC/单包失败不阻断/skill 工具授权与去重/会话内 prompt 两次装配字节相同。

## 7.5 已知 P1 边角（块B 链路自查记档）

同名跨 scope 的 hash 归属错位：会话快照了 official 版卡片后，用户又上传**同名**技能——旧会话按 official hash 读取时，`_find_in_scopes` 先命中 namespace 文档、取包用其 scope 拼 ref → miss → 工具返回 error（fail-closed 不炸 run，但本应读到 official 旧版）。概率低；修法=SkillGrant 增 `scope` 字段（快照时定死归属）或取包按 scope 退避，随用户上传功能（写面块）一并落。

## 8. 与冻结代码的关系

冻结代码中可复用：Mongo store 骨架、真文件+真库测试形态；作废：files 全进 Mongo（改分层）、无脑每 run 重供（改 hash 增量 + **graph state 账本**——冻结代码的闭包局部变量 `supplied` 不算账本,重启/resume 不识别,必须按 spec 改）、零工具方案（skill 工具回归）、`fetch(scopes,name)` 无 hash 参数（改为按 hash 取,双路）。
