# 历史分支与旧工作树：语义承接及安全收拢

日期：2026-11-15（America/New_York）。本轮不是新功能或全仓扫描；仅处置上一轮保留的 BFF 18 个提交和 7 个旧 worktree。

## 1. 裁定

- **没有确认需要从这些旧树恢复的现行产品缺陷。** 不能把“不在 main 的提交 SHA”直接当作遗漏；也不能把被后继替代的实现倒灌 main。
- BFF 18 项逐提交核意图；App 两大历史树为共享 80 项加后继 27 项，合计 107 项，不重复计成 187 项。Admin 工作区另有 86 个 tracked 修改／删除和 43 个 untracked 源文件，逐路径分类与保护。
- 7 个旧 checkout、BFF 过时分支名已移除；未修改任何子仓生产源码、契约、Schema 或 Root gitlink。历史 Git 引用仍保留，未进行 GC 或历史重写。
- 保留一个 **H-01 可选历史能力候选**，不是确认缺陷，也不是已经完成的新功能；见第 4 节。

审查基线：Root `138201388931a8fa3198c9298eb7f9cf341e1c02`、App `f8215c105285ab6207bcff3b84aca56631642ee4`、BFF `2e0affb14fd3207f8d18248512b727d6bf0ddb53`、Storage `7155093c1eb98d3f3b8b02781fba4d4ccbc87367`。两位只读 agent 分审 BFF 与 App 大树，主控核小切片、Storage、归档和删除，并独立复核主要承接路径。下文测试名称仅是现有覆盖定位，**不是本轮重跑通过证据**。

## 2. BFF：18 项逐项裁定

以下路径相对 `apps/kokoro-bff`。18 项均无须 cherry-pick；旧分支 `codex/archive-bff-mcp-closure-777325d` 的 tip 为 `777325d6d83501051d856347b049a36b8f8334e8`。

| 旧提交 | 原意图 | 当前承接／处置 |
| --- | --- | --- |
| b2959be | Billing v1 本人读、Platform 直接凭据 | `billing-personal-read.ts`、`projection-http.ts` 及正式 owner client 已承接 |
| 59bb71f | MCP direct service credentials、typed CRUD | `mcp.module.ts`、`mcp-personal-connect.ts` 及 server input/response 已承接 |
| e8fa7ac | 私有 MCP server 删除 | 当前 DELETE／CAS／原命令 ACK 已承接 |
| 25e7620 | 合并 GET admission、免读后 Session 鲜验 | 装配后继已承接；免鲜验策略已由读后 fresh Session＋action／原主体围栏替代，不回退 |
| a4bc97c | JSON 原子导入、Custom API CRUD | `mcp-personal.ts`、`mcp-personal-json-import-response.ts`、`custom-api.ts` 已承接 |
| 775413f | `custom_api_personal` 凭据 purpose | 当前 credential profile 与 Nest 注入已承接 |
| cd2210c | Product OIDC authorize/callback relay | 当前 native Session relay3.0 闭集已替代，不复活 Product OAuth 旧入口 |
| 7e553c8 | 非生产 loopback MCP fixture gate | 当前 URL parser 保留明确环境门和 URL 限制 |
| 0499bc8 | 投影本地 fixture descriptor | 当前 server projector 按环境门承接 |
| 41060d4 | JSON import 新分配 server ID | 当前批次 ACK／connector-server 绑定承接，不要求预造 ID |
| 675fd9b | 非生产 loopback OAuth handoff URL | 当前 authorization response projector 承接；这是外部 MCP 授权，不是 Product OIDC |
| 2a6db3f | OAuth owner additive fields 安全投影 | 当前白名单 projector 承接，不 raw passthrough |
| c3f70a3 | RPC correlation header | 当前两具名 header 读取及普通 RPC exact 校验承接 |
| 1f14479 | OAuth handoff 的窄 correlation 豁免 | 当前 authorization 调用的具名 option 承接，不扩大到所有 RPC |
| d49f28d | 上项 handoff 的 cache header 处理 | 当前同一窄分支已承接，不新增宽松策略 |
| 33c7b5a | 当时正式 Platform pin | 当前正式后继固定 artifact 已替代，不回钉旧版本 |
| 0a4f631 | 当时 IAM relay machine policy | 当前 native relay policy／独立固定来源已替代 |
| 777325d | 测试跟随当时正式 owner | 当前 generator pin／精确原件与 relay 测试已承接，不恢复退休测试常量 |

主控复核入口：[本人 MCP 路由](../../apps/kokoro-bff/src/http/routes/mcp-personal.ts)、[native relay policy](../../apps/kokoro-bff/src/http/routes/iam-protocol-relay.policy.ts)、[MCP 个人授权回归](../../apps/kokoro-bff/test/mcp-personal-http.test.mjs)。原提交保留在既有 `refs/archive/local-closure-20261020/branches/feat/mcp-personal-closure` 与 `kokoro-bff-1/head`，删除的是活跃本地分支名，不是历史对象。

## 3. 七棵旧树与工作区内容

| 对象 | 当前承接／裁定 |
| --- | --- |
| MCP settings alignment，a32dcc14 | Settings 搜索及桌面两列已承接；旧固定 20rem 搜索宽度被现多语言 wrap／min-max 布局替代。`next-env.d.ts` 差异仅生成路径 |
| Project rail hierarchy，2abaeb07 | 当前 `project-identity.tsx` 的 loading skeleton 和现有 workspace 用例完整承接 |
| Skills catalog spacing，6c03ab1d | 当前类别测量行／自适应工具栏替代旧 padding 微调，不把旧像素值当需求 |
| Skills settings alignment，cb047c07 | 桌面两列、compact 单列、卡片元数据对齐已承接；旧 8rem 标题带由后继布局替代 |
| r257-admin-web，a540084d＋129 状态 | 文档／生成契约由正式后继替代；内嵌 Admin 由独立 Admin 承接；导航／Project／Settings、版本发布／withdraw／unknown 恢复、目录四读取／exact revision、上传／GitHub 导入／分享／九语言按现能力承接。旧 native 前的 SDK／OAuth 接线不恢复。H-01 单独保源 |
| web-skills-release，c9b02b6f | 包含上述 80 项及后继 27 项；独立 Admin 交接、正式 Skills 目录／下载／导入由现实现承接，最终旧提交本身已撤掉替代后台。不是把 107 项全判“没有价值”，而是不再需要保留活跃 checkout |
| Storage r353，a1206d01＋单文件修改 | 旧 local legacy smoke 的 NULL canonical／同 hash 重传 scan／旧事实不变／退休与下载断言，已由正式 maintenance smoke、RR snapshot 和 canonical-snapshot 套件承接；不新增几百行重复试验 |

App 主要证据：[当前版本发布](../../apps/kokoro-app/src/ui/skills/personal-skill-publish-dialog.tsx)、[AI prompt starter](../../apps/kokoro-app/src/components/blocks/app-frame/use-app-frame-actions.ts)、[Project 标题](../../apps/kokoro-app/src/features/app/project-identity.tsx)；Storage 主要证据：[正式 legacy maintenance smoke](../../apps/kokoro-storage/test/smoke/legacy-canonical-maintenance.e2e.test.ts)、[canonical snapshot](../../apps/kokoro-storage/test/integration/canonical-snapshot.test.ts)。未因“旧代码有此功能”恢复内嵌 Admin、旧通用 client 或过时契约。

旧“Library ZIP Artifact → AI import”入口与当前明确的 Composer prompt starter 是不同方案；当前产品范围未承诺旧 selector，不将 API 的存在直接推导为 UI 漏项。

## 4. H-01：本人草稿原地编辑，保留但未立项

旧代码实际实现 metadata／category／examples 的 CAS 保存、封面上传／清除和 discard，并非空界面或 Admin-only 操作。当前作者编辑由“新版本＋真实 ZIP 发布”承接，已存在 draft 的原地修改入口则不同；当前产品文档未承诺整套普通用户原地编辑器，故本轮既不判产品缺陷，也不把它当无价值文件删除。

- 保留来源：旧 `skill-draft-editor.tsx`、draft workspace、`skill-product-client.ts`、schema／server adapter、UI/client 回归等，连同所有调用点／文案／删除状态，完整包含在下述 129 项 working-tree 归档中。
- 当前权限仍归本人：BFF `skill-draft-mutations-native.ts` 做 current `update_draft/discard_draft` 授权，Capability 核同 tenant／owner／draft／CAS；不是从 Admin 偷渡写入。
- 若后续明确需要，仅先做 **已有本人 draft 的 metadata PATCH＋fresh 读回**，复用现正式 client、原 CAS/body/key、unknown／取消边界；不顺带引入 cover/discard/AI，不恢复整个旧 workspace。
- 唯一 TODO 将其放入“产品决策候选”，不算已确认核心缺陷或自动开工项。

## 5. 保存与清理证据

- 所有旧 HEAD／既有 archive refs 保留，不合并旧代码。原 Admin 工作区的 129 项由独立 `GIT_INDEX_FILE` 按明确 NUL／literal 路径保存，86 个 tracked 修改／删除＋43 个 untracked 全部逐文件核内容、删除状态和 Git mode；原 index 未被修改。未复制整个源码树、依赖或缓存。
- 该完整工作状态的新增本地引用：`refs/archive/local-cleanup-20261115/kokoro-r257-admin-web/working-tree`，commit `29cbf05694a4945a3335d33640680a6d6b4ea302`。这是本地历史保护引用，**未推送、不属于 main**；不是“该候选已经交付”。
- Storage 单文件和 Next 生成路径差异与既有 work archive 逐字核等；4 份私有配置（含一个指向主仓配置的 symlink）和 6 份旧技术日志单独私有保留，未入 Git，未跟随链接复制或修改主仓配置。
- 删除前核 HEAD／status／ignored 清单、所有保护引用和文件指纹、全 FD 无占用；占用探测命令失败即停止。只恢复已保护的明确 tracked 路径，按核等清单移除已归档 untracked，再执行普通 `git worktree remove`，不强制删除 checkout。BFF 分支删除用原 SHA 的 compare-and-swap，两个旧归档引用保持。
- 复核 129 项归档及 10 份私有文件均可读取、指纹一致，主仓依赖 inode、所有子仓 HEAD 和 Root gitlink 不变。子仓已只剩 main 分支和各自唯一主 checkout；Root 本轮文档 PR 承接最后 main／topic 清理。
- Mori、System 保持 Root 的 detached pin：本地分支只有 main，不因其后继仅树相等就擅改精确组合。

本轮验证为有限静态语义审查、Git／逐文件归档核等及文档链接／diff 检查；没有重跑业务测试、浏览器、模型、基础设施或部署。原详细逐提交、129 路径清单及机器收据保留在本地私有审查材料中，不将源码／配置内容复制进任务台账。
