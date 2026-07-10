# Kokoro Deliver（成果交付）技术方案（未实现，待认可）

状态：**纯方案，一行代码未写，认可后才开工（块5）**
日期：2026-07-10

## 0. 一句话

> agent 做完东西,调一个 `deliver` 工具把成品交付给用户——交付即冻结:内容按 hash 存到独立位置,之后工作区怎么改都不影响已交付的成果。

## 1. 三个概念分清（不混）

| 概念 | 是什么 | 可变性 |
|---|---|---|
| workspace 文件 | agent 干活的草稿区（真实目录直读） | 随时被改/删 |
| workspace 归档 | 工作区的备份面（path 键，覆盖写） | 跟随目录 |
| **成果（delivery）** | agent 显式交付的成品 | **冻结不可变** |

## 2. 工具（agent 面,唯一动词）

```text
deliver(path, title, note?)
  1. 经 backend 读文件字节（读到哪份字节就冻结哪份——构造上自洽,无需 quiesce）
  2. sha256(字节) = content_hash
  3. 上传 deliveries/<namespace>/<content_hash>
     （同内容同 key=天然幂等；异内容异 key=物理上不可能覆盖）
  4. 发 delivery.created 事件: {run_id, path, title, mime, size, content_hash}
```

- **agent 是唯一定稿者**（纯 agent 驱动,用户不 promote/demote——V1 明确不做）。
- hash 由归档动作计算（非模型自报），session 不二次校验。
- V1 单文件；多文件成品先 zip 再交付。
- **存储配置定案**：workspace 存储配置文件（ADR-009 yaml）新增 `deliveries` 节（s3 桶/前缀 或 本地目录，与 workspace 同文件不同前缀），dev 无 S3 也能跑；schema 在块A 一并定，避免排到块D 才撞见。注意与 workspace 归档（path-keyed 覆盖写）是**不同 keyspace 不同语义**，deliver 为 content-hash-keyed 不可变写，实现不复用 archiver 的覆盖路径。

## 3. session 读模型与接口

- 事件 → session upsert `deliveries` 读模型：键 `(namespace, content_hash)`，`session_id/run_id/path/title` 为元数据——天然支持未来"作品统一归库"（用户级），V1 先给 session 级展示。
- 新增读接口：成果 list + 下载（从 deliveries key 取回冻结副本）——**成果必须取得回来**，与 workspace 文件接口（可变直读）分开。

## 4. 失败/边角语义（全部定死）

- 重复 deliver 同内容 → 同 content_hash → 同一条记录（幂等，无重复）。
- deliver 后源文件被改/删 → 成果不变（指向冻结副本）。
- 文件不存在 → 工具返回 error 文本（模型自纠），不炸 run。
- 成果副本受 retention 保护，不随 workspace 归档 GC。
- 远程沙箱（E2B/Daytona）依赖其文件拉取原语（WP-2 范畴）；V1 dev 用 local/docker 即闭环。

## 5. 命名（D8 已过）

工具 `deliver`（普通英语动词）；概念中文"成果"，垂类皮肤可显示"作品"（site skin 层，不改契约）；事件 `delivery.created`。

## 6. 验收断言

- deliver 后改/删源文件，下载内容不变。
- 同内容重复 deliver 返回同一记录。
- 不同 namespace 的成果互不可见。
- agent 410+ 与 session 全量测试三绿；e2e 断言成果面与文件面分离。
