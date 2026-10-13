# 开发交接：现有 main、远程基础设施与完整 dev 栈

核验时间：2026-10-13 03:39 EDT（America/New_York）。本次只整理文档，不恢复已暂停的功能开发，不重置数据、不新增测试脚手架。

## 1. 提交基线与未完成项

- Root：`e14852453656fec55117d80c1f059050f8c4059e`，已推送 main；本交接在其后经文档 PR 更新。
- App：`12acfc6b3ccb9bc0873e8060f8a3c45cea993266`。修正 URL MCP 注册回包校验：registered server 对应 active connector，pending 对应 pending，不再把正确回包拒为 502。
- Platform（物理仓 capability）：`7da4e09e8eb0bfa4b83fd55af95cc674330ce007`。增加可配置 HTTPS DoH resolver；保留 SSRF 地址校验与连接 pinning。
- BFF：`95fbd894ee01053f6c9cabeca481e50151cd4f15`；Admin：`e1af4333c7c5d67323e6c382cb12a9ee3f35c549`。其他子仓版本由 Root gitlink 固定。
- 上一轮收尾确认所有子仓 main、工作区 clean；后续重新检查，不据历史断言当前状态。新改动遵守 topic 分支 → PR → 审查/验证 → main。

**已知未闭环，接手时不得标为完成：**

1. Skills/MCP 与 Manus 的视觉、布局、交互尚未逐项验收。现连接器卡片直接暴露编辑/启用/删除，不是用户要求的参考详情与管理菜单结构。
2. 私有 URL MCP 注册成功不等于已连接或已启用。真实 DeepWiki 注册返回 registered/active/enabled=false；随后启用返回 400。当前启用前置要求有效 Connection 与 capability selectors，而该路径未形成对应 Connection。应在 Platform 解决生命周期，BFF/Web 消费真实状态；禁止在 UI 强行置成功或放宽授权条件。
3. 临时“保存并发布直接启用”调用已撤销；注册回包修正保留。真实第三方 OAuth 回跳 → Connection → Enable 仍未完整验收。
4. 官方 Skill 创建/上传/发布已有路径，但完整用户/管理员 CRUD、文件树、导入与 UI 对照仍需实际验证；已有局部通过不代表整个能力完成。

上一轮最小验证：App 注册契约 10 PASS、Platform DNS/HTTP/OAuth 57 PASS，两仓 TypeScript 检查与 diff 检查通过；不是全栈业务验收。本次文档交接不新增视觉源码断言或执行全仓无关测试。

## 2. 基础设施：已经在使用，不再另起本机同类实例

Mac 运行源码应用；Windows 运行共享基础设施，经现有 SSH 隧道访问。当前 SSH 连接成功，Windows Docker 输出 PostgreSQL、Redis、MinIO、etcd、Milvus 五容器均 healthy。MinIO readiness 与 Milvus health 经 Mac 隧道分别返回 200。

| 设施 | Mac 本地隧道地址（无凭据） | 当前使用/边界 |
| --- | --- | --- |
| PostgreSQL | `127.0.0.1:15432` | IAM、Storage、Platform、BFF 实际进程使用；单应用数据库、owner schema 隔离 |
| Redis | `127.0.0.1:16379` | 上述四 owner 实际进程使用；复用实例，保留各 owner namespace/DB 约定 |
| MinIO | `http://127.0.0.1:19000`；console `19001` | Storage 实际使用；不绕过 Storage 业务边界 |
| Milvus | `http://127.0.0.1:19530`；health `19091` | 已部署并健康；应用绑定/向量业务未在本轮验收，按实际需求接入 |
| etcd | 无 Mac 应用直连端口 | Milvus 内部依赖，不给业务仓追加直接调用 |

私有入口（只引用位置，不复制凭据）：

- 远程记录：`/Users/nako/.codex/WINDOWS_SSH.md`。
- 连接配置：`/Users/nako/.codex/windows-infra/connections.mac.env`。
- 重连入口：`/Users/nako/.codex/windows-infra/connect-mac.sh`。
- 当前私有应用启动包装：`/Users/nako/.codex/windows-infra/run-kokoro-service.sh`。

**配置陷阱：** 多个仓 `.env.local` 仍写着本机 5432/6379/39190；当前已核四 owner 通过私有包装覆盖这些值。直接运行 `pnpm dev` 而未加载正确环境，可能连回旧实例。接手先核有效环境、schema 与当前监听，禁止把旧 env 的存在当作已迁移证据。当前包装尚未支持 Agent/Mori，不是完整统一启动器；Agent 的本地入口文件为 `.env.http.local`，需按该仓配置词汇核验，不套用其它仓变量。

本机仍有 PostgreSQL 5432、Redis 6379 监听，并有一个历史 BFF checkout 在 59464 监听且有效配置仍指向本机实例。不要据四 owner 已切换就关掉所有本机基础设施：先盘点全部客户端并完成需要的切换，再停止确认为重复的本机进程/容器，保留持久卷和数据。本次未执行停止或删除。Mailpit、ClamAV 的当前可用性需随全栈启动核验；未声称已迁至 Windows。

## 3. 强制要求：全部服务一起启动后才进入 dev 联调

这是用户要求，不是可选建议。开发栈覆盖 `apps/` 的所有 11 个应用/服务及其必需常驻 worker；共享库只安装/构建，不启动一个虚构服务。允许按依赖先后启动，最终必须一起就绪。

| 仓/进程 | 源码启动入口 | 本次运行快照 |
| --- | --- | --- |
| kokoro-app | `pnpm dev`，用户入口 3310 | `/app` 返回 307 登录跳转；当前页面行为未验 |
| kokoro-admin | `pnpm dev`，内部 3320，对外仍 3310 `/manage` | 同源 `/manage` 与内部入口均 200 |
| kokoro-mori | `pnpm dev`，端口依本仓配置且不冲突 | 未证实运行 |
| kokoro-iam | 正确私有环境 + `pnpm dev` | 53711 `/readyz` 200 |
| kokoro-storage | 正确私有环境 + `pnpm dev` | 8085 `/readyz` 200 |
| kokoro-capability / Platform | 正确私有环境 + `pnpm dev` | 8086 `/readyz` 200 |
| kokoro-bff | 正确私有环境 + `pnpm dev` | 53714 `/readyz` 200 |
| kokoro-system | 正确私有环境 + `pnpm dev` | 登记 53719，当前未监听 |
| kokoro-billing + payment-events worker | 正确私有环境 + `pnpm dev`；另运行 `pnpm worker:payment-events` | 登记 4245 未监听；worker 未证实 |
| kokoro-scheduler | 正确私有环境 + `go run ./cmd/scheduler` | 登记 8087，当前未监听 |
| kokoro-agent HTTP + worker | 按本仓私有配置分别 `uv run kokoro-agent-http`、`uv run kokoro-agent-worker` | 登记 HTTP 53763 未监听；worker 未证实 |
| kokoro-web-shared | 消费方依赖安装/构建 | 非常驻服务 |

**下一次启动顺序与检查：**

1. 检查 SSH 隧道及 Windows 基础设施；复用既有健康实例，不运行重复 Compose、不重复安装 schema。
2. 核验各仓私有环境中的远程连接、owner schema、端口、服务凭据与依赖地址。新 owner schema 缺失时按 owner 安装说明处理；已有数据不随启动清理。
3. 先启动 IAM、System、Storage、Billing、Platform 等 owner，再启动 Agent HTTP/worker、BFF、Scheduler 与 Billing worker，最后 App/Admin/Mori。如有具体 readiness 依赖，按实际依赖调整顺序；不跳过最终成员。
4. 复用正常源码进程，缺失才启动。记录全部进程的仓库/source、commit、端口、有效配置来源和健康结果到被忽略的 `var/dev/`；旧 registry PID/端口仅是线索。
5. 每个 HTTP owner readiness 通过；worker 按该仓的实际消费/心跳机制检查，Web 实际打开验证。一个服务返回 200 不替代其它服务、worker 或浏览器行为验证。
6. 必要时重启失效应用，由主控串行协调，记录原因与新进程；不重复启动、不关闭其它任务服务、不重置库/Redis/桶。
7. 全套一起就绪后执行当前改动对应的真实 dev 链路。单元测试可隔离，但“测试 PASS”不替代全栈就绪，也不替代 Manus 页面对照。失败项具名记录，不为清零增加兼容层或无价值测试。

当前快照**未达到这个完整 dev 条件**。本次是停止开发后的交接整理，不以部分监听或文档承诺称为全栈已启动。

## 4. 接手范围与入口

- 当前未完成事项仍是 Skills/MCP 与其真实用户/后台路径；先解决注册、授权、Connection、启用的真实生命周期，再按已登录 Manus 页面核对界面。不要新写第二个 Admin，不恢复历史 fallback/alias。
- 同源入口固定：用户 `/app`、管理员 `/manage`；浏览器不因后台跳转改变对外端口。
- 长期规范：[Root AGENTS](../../AGENTS.md)；当前事实：[CURRENT](../CURRENT.md)；owner 地图：[CODEBASE_MAP](../CODEBASE_MAP.md)。子仓 API/schema 以各仓现行 contract/设计为准，不在交接复制第二份。
- UI 先核参考页面结构、菜单/详情/弹窗、字体/颜色/间距和状态，再改组件；测试不决定设计、不硬编码旧布局。完成态必须对应完整可执行的操作链。
- 用户已停止此前开发目标。接手推进新的功能前以新的明确任务为准；这份文档仅交接事实和后续开发必需条件。
