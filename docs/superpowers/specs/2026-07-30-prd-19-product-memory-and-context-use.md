---
artifact: product-requirements-document
prdId: PRD-19
version: "1.0"
created: 2026-07-30
status: internal-review-active
scope: product-memory-explicit-instructions-past-chat-context-temporary-chat-context-use-explainability-data-rights
accountableProductRole: Personalization & Memory Product Lead
mandatoryCosigners: [Privacy, Security, Platform Memory, Session, GA, Web, Data Governance, Model Platform, Accessibility, QA, Support, SRE]
engineeringOwner: team:platform-memory-engineering
qaOwner: team:memory-context-quality
supportOperationsOwner: team:memory-data-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-19：Product Memory、Past-chat Context 与可解释使用

## 1. Overview

### Problem

Kokoro 的不同 Site、Chat、Studio 和未来 Coding Agent 都需要在多次使用之间延续用户偏好、事实、项目约束与
过去工作，但不能把完整聊天记录、GA checkpoint 或一份不可解释的向量集合当作“长期记忆”。那样会导致错误
事实反复影响回答、跨 Site/账户泄漏、用户删不干净、临时对话仍被学习，以及无法回答“这次为什么这样回复”。

当前 Platform 已有 dormant M0 authority kernel：Site-local MemorySpace、稳定 Entry、append-only Revision/
Provenance、显式 remember/correct/forget、pause/reset/revocation fence 和 owner-scoped receipt。它尚无公开 API、
生产进程、检索、自动学习、Session source feed 或 GA MemoryPort，因此不能对用户宣称已具备长期记忆。

### Solution

建设一个由 Platform Memory 管理、Session 与 GA 通过版本化边界协作的产品记忆系统：

- 显式指令、用户保存的记忆、系统学习的候选记忆、过去聊天检索和当前 Run 工作上下文相互分离；
- 默认上下文由“固定记忆 + 本轮相关检索”组成，并冻结为可审计的 `MemorySelectionSnapshot`；
- GA 只使用 opaque namespace、run-bound handles、refs、digests 和受限内容结果，不接收 Site/账户身份轴；
- 用户可查看、纠正、删除、暂停学习、暂停使用、重置、导出，并能看到每次回答实际使用了什么；
- Temporary Chat 不读取、不写入、不建议任何产品记忆；
- 删除先立即撤销使用，再异步完成内容、embedding、索引、缓存、导出与 checkpoint 派生内容的可验证 purge。

本 PRD 定义产品行为与验收；技术 authority、RPC 和数据边界以
[`ADR-013`](../../kokoro-handbook/decisions/ADR-013-product-memory-and-context-authority.md) 为准。

### Target users

- 在同一独立 Site 中持续使用 Chat 或 Studio 的个人用户；
- 在 Project 中共享明确项目上下文的当前成员；
- 需要检查/纠正“系统记住了什么”的隐私敏感用户；
- 诊断错误个性化、删除与检索问题的 Support/Data operator；
- 通过受限 MemoryPort 使用上下文的 GA、子 Agent 与未来 Coding Agent。

## 2. Goals、metrics and non-goals

### Goals

1. 让跨会话个性化可感知、可解释、可纠正，而不是扩大隐藏上下文。
2. 对 Site、subject generation、Project membership、purpose、Run 和临时模式执行零信任隔离。
3. 把用户控制变成产品主路径：remember、correct、forget、pause use/learn、reset、export 均有 receipt。
4. 在不改变 GA graph/checkpoint/handoff authority 的前提下，为 Chat、Studio 和 Coding Agent 提供同一记忆能力。
5. 用 provenance、有效时间、置信度、冲突与 suppression 防止错误记忆静默覆盖正确事实。

### Success metrics

| Metric | Baseline | Launch target | Evaluation window |
|---|---:|---:|---|
| 跨 Site、跨 subject generation、Temporary Chat 内容泄漏 | 未上线 | 0 | 每次 release + continuous canary |
| 回答中使用的 memory/search item 绑定 exact revision 与可解析 citation | 未上线 | 100% | 每个完成 Run |
| 用户 forget/reset/pause-use 后在 documented revocation boundary 继续返回内容 | 未上线 | 0 | continuous race suite |
| 明示“记住/纠正/忘记”命令恢复同一 receipt 且无重复 revision | M0 local | 100% | API/retry suite |
| 自动学习 precision（用户保留或确认，无纠正/删除） | 未上线 | ≥95%，且敏感类不自动激活 | 28-day qualified cohort |
| 自动选择有用率（用户反馈 + blinded eval） | 未上线 | 显著优于 no-memory baseline，幻觉率不升高 | staged evaluation |
| Memory 关闭/降级导致正常 Session message 无法提交 | 未上线 | 0 | continuous |
| purge 完成但仍残留 plaintext/embedding/search cache/export payload | 未上线 | 0 | deletion certification |

指标必须按 Site、LaunchProfile、surface、memory category、selection class、model/index revision 切分；不得记录原始
query、memory content、Session excerpt 或可逆个人标签。

### Non-goals

- 不把 Session 聊天历史迁移到 Platform Memory；Session 继续拥有 conversation truth 与 cited past-chat search。
- 不把 GA scratchpad、checkpoint、计划、隐藏 reasoning 或 tool result 自动提升为用户记忆。
- 不允许 GA/子 Agent/网页/MCP 直接写 active memory；它们只能提交 proposal。
- 不把 explicit instructions 存进 learned-memory aggregate，也不允许模型推断自动成为 instruction。
- 不跨 Site 共享账户或记忆；未来共享只能通过显式 export/import 或标准 OAuth 用户动作。
- M1 不承诺知识图谱、全自动项目总结、组织级程序性记忆或无限上下文。

## 3. Product model and authority

| Object | Product meaning | Authority |
|---|---|---|
| ExplicitInstructionRevision | 用户/管理员明确要求持续遵守的规则 | Platform Project Context |
| MemorySpace | 一个 Site-local user/project/agent-product 记忆空间及 use/learn policy | Platform Memory |
| MemoryEntry / Revision | 稳定逻辑记忆及不可变内容修订 | Platform Memory |
| MemoryProvenance | 来源、actor、source revision、有效时间与策略证据 | Platform Memory |
| MemoryProposal | 尚未成为 active memory 的候选事实/偏好/总结 | Platform Memory |
| MemorySelectionSnapshot | 某次 Run 初始使用的 exact entry revisions 与选择解释 | Platform Memory |
| MemorySearchReceipt | Run 内动态检索的 query identity、结果、分数、截断与索引版本 | Platform Memory |
| ConversationSearchReceipt | 过去聊天检索的 exact cited result | Session |
| RunContextManifest | 产品、项目、记忆与会话上下文的 admitted ref/digest 集合 | Platform Admission |
| ContextUseReceipt | 某个完成回答实际使用过的 instruction/memory/chat-search refs | producing Run + Session projection |

### 3.1 Scope

- User scope：`site_ref + subject_ref + subject_generation`；账户删除重建后不得继承旧记忆。
- Project scope：`site_ref + project_ref + membership/authorization epochs`；只对当前有权成员可见。
- Agent-product scope：继承一个 User 或 Project 父空间，只能收窄，不创建新的 Workspace authority。
- Site 是隔离边界，不是可选 query filter。浏览器、GA 和 provider 都不能提交或覆盖 owner scope。

### 3.2 Memory classes

| Class | Example | Write policy | Initial context policy |
|---|---|---|---|
| explicit saved fact/profile | 姓名、职业、固定背景 | 用户命令立即 active | 可 pin；仍受 policy/token budget |
| preference | 喜欢简洁回复、默认深色图 | 显式命令或合格 proposal | 相关时选择；冲突时提示 |
| episodic reference | 过去某次讨论/产物 | Session search receipt，不复制全文 | on-demand cited search |
| project context | 输出标准、repo/asset refs | Project Context explicit revision | mandatory/priority context |
| learned candidate | 从对话推断的稳定事实 | proposal → policy/confirmation → active | 默认不自动 pin |
| procedural/skill | 做事流程、工具能力 | Skills/Capability authority | 不是 Product Memory |

## 4. Canonical journeys

### MEM-01 — Explicit remember and inspect

1. 用户在 Chat 中说“记住……”或在 Memory settings 创建记忆。
2. Web 显示将保存的 scope、category 和可编辑内容；敏感/越权内容要求确认或拒绝。
3. Platform 以 command identity + canonical digest 创建/恢复同一 receipt。
4. 用户可在统一列表中看到 active content、scope、来源、更新时间和“可能在哪些产品中使用”。
5. Chat 内命令成功必须链接可打开的 Memory item；网络超时通过 receipt 恢复，不换 key 重发。

终态：`remembered`、`confirmation_required`、`policy_rejected`、`idempotency_conflict`。

### MEM-02 — Correct, contest and forget

1. 用户可从回答的“使用了记忆”说明、Memory settings 或聊天命令进入 exact item。
2. Correct 创建 append-only successor revision；旧 Run 保持历史 ref，新 Run 只使用 current active revision。
3. 冲突来源进入 `contested`，不 last-write-wins；UI 展示安全来源摘要并请求用户选择/修正。
4. Forget 立即推进 revocation epoch、停止新选择与动态返回，随后进入 purge workflow。
5. 删除完成前显示 `deletion_in_progress`；完成后只保留 content-free tombstone/receipt，不允许 restore plaintext。

终态：`corrected`、`contested`、`revoked_purge_pending`、`purged`、`legal_retention_explained`。

### MEM-03 — Automatic learning proposal

1. Session 只通过 durable source facts 发布可学习来源，不同步回调 Memory，也不把聊天全文常驻复制过去。
2. Memory worker 在 pause/policy/generation/source grant 验证后读取 bounded exact excerpt。
3. extractor 生成带 provenance、confidence、valid time、sensitivity 和 conflict evidence 的 proposal。
4. 明示用户事实可按 policy 自动接受；敏感、低置信、行为改变、冲突或外部来源必须用户确认。
5. 用户拒绝/删除产生 suppression receipt，后续相同内容不能被另一轮提取立即“复活”。

终态：`active`、`confirmation_required`、`rejected`、`suppressed`、`expired`、`source_revoked`。

### MEM-04 — Context selection and response explanation

1. Platform Admission 冻结 ProductContext、ProjectContext 和 memory policy/grants。
2. Platform Memory 对本轮 query 做 policy filter、exact lexical/semantic candidate search、deterministic fusion 和 budget cut。
3. 固定/pinned 与本轮 retrieved items 分开标记，但进入同一个 immutable selection snapshot。
4. GA 只能通过 run-bound handle 读取 snapshot 或发起 journaled dynamic search；不能更改 scope/policy。
5. 完成回答形成 `ContextUseReceipt`。Web 至少显示 closed state：none、instructions、saved memory、project memory、
   past chats、mixed；展开后可看 citation、current state 与 correction/forget action。

若 Memory 非 mandatory personalization 依赖不可用，回答可在明确 `memory_unavailable` 下无记忆继续；managed security/
Project instructions 无法解析时 admission fail closed。

### MEM-05 — Past-chat search

1. 初始上下文不把所有历史聊天拼入 prompt。
2. GA 通过 Session-issued `conversation_search_handle` 搜索当前 Site/subject/session policy 可见历史。
3. 每个结果含 Session/message/source revision、时间、snippet truncation 与 search receipt；点击可回到仍有权的来源。
4. 已删、无权、retention-expired 或 source-revoked 结果变成 typed unavailable，不返回缓存内容。
5. Memory 可引用 source ref/provenance，但不成为 conversation owner。

### MEM-06 — Pause, reset, temporary and data rights

- Pause learning：保留现有记忆供选择，拒绝新的 inferred proposal，并使已排队旧 generation 工作失效。
- Pause use：保留内容但新 Run 不签发 selection access；learn policy可独立配置。
- Reset：推进 generation/revocation，撤销全部 active use，异步 purge 派生内容并保留 completion receipt。
- Temporary Chat：创建时冻结 temporary，所有 branch 继承；不签发 Memory/Conversation-search handle，不发布 source/proposal。
- Export：异步、版本化、加密交付；包含允许的 revision/provenance/policy/deletion state，不含 secret/hidden reasoning。
- Import：只产生 quarantined external provenance proposals；不能导入 instruction、foreign authorization 或 foreign Site identity。

### MEM-07 — Operator recovery

- Support 只能按 Site-scoped case 查看 safe metadata、receipt lineage、watermarks 和 current availability。
- Data operator 可重试 proposal/purge/index jobs，但必须 lease/fence/idempotency；不能直接 UPDATE owner table 或查看明文。
- Admin 命令要求 reason、step-up、expected version、审计和 maker-checker（批量 purge/LegalHold conflict）。

## 5. Functional requirements

### User controls

- FR-01：Web 必须提供 list/search/detail/create/correct/forget/pause-use/pause-learn/reset/export；每个 mutation 可按 receipt 恢复。
- FR-02：Saved memory、past-chat history、explicit instructions 三类开关和说明必须分开，不得用一个模糊“个性化”开关。
- FR-03：每个完成回答必须能解释是否以及使用了哪些上下文；“未使用”也是可验证状态。
- FR-04：用户 correction/forget 后，相关 source citation 和旧 ContextUseReceipt 显示 current-state 提示，不篡改历史 receipt。
- FR-05：Temporary Chat 在入口、会话 header、export 和 branch flow 中持续可见，不能中途转为 standard。

### Learning and safety

- FR-06：只有 authenticated user source 或经 policy 合格来源才能形成 user fact/preference proposal；assistant/tool/web/MCP 输出默认不可信。
- FR-07：credential、token、hidden reasoning、任意 executable instruction、受限敏感类别不得存储、embedding、日志或导出。
- FR-08：proposal 必须携带 source refs/revisions、confidence、valid time、policy/generation 和 content digest；缺任一项拒绝。
- FR-09：冲突、纠正、supersession、suppression 与 source deletion 必须是显式状态，不允许覆盖或静默复活。
- FR-10：automatic learning 默认关闭，必须由 Site release 与用户 policy 同时允许；敏感类别始终需显式确认或禁止。

### Retrieval and context

- FR-11：初始选择必须先执行 authorization/policy/current-revision filter，再进行检索/rank；数据库 RLS 不是近似向量检索的后置补救。
- FR-12：每次 selection/search 有 exact model/index/policy/query/result digest、per-component scores、citations、budget 与 truncation receipt。
- FR-13：固定上下文、相关检索、动态 memory search 和 past-chat search 分开计量并服从总 token/result budget。
- FR-14：同一 Run 的 admitted selection 不随后台修订漂移；显式 rebase/new Run 创建新 snapshot。
- FR-15：删除/安全 revocation 优先于历史可复现性；过 fence 后返回 content-free revoked/purged 状态。

### Isolation, reliability and privacy

- FR-16：所有公开对象/commands/receipts 使用 Site-composite authority；默认 scope 由 verified caller context 导出，浏览器不得选择 Site。
- FR-17：GA MemoryPort 不出现 Site/user/workspace/payment 字段，只接受 opaque namespace、run-bound handle、refs/digests 与 bounded request。
- FR-18：Memory outage 不回滚 Session message commit；proposal 异步退避。mandatory instruction resolution 失败则 admission 明确拒绝。
- FR-19：purge 必须覆盖 content、revision payload、embedding、FTS、cache、excerpt、export、GA checkpoint/evidence 派生内容和 backup policy participant。
- FR-20：同一 source 删除与 proposal/materialization 并发时，以 source cutoff + ingress/materialization watermarks 证明没有旧内容复活。

## 6. UX and edge cases

### Primary surfaces

- Chat/Studio response：低干扰“使用了记忆/过去聊天”标识，可展开来源与操作。
- Memory settings：Saved、Learned、Project 三个分区；search/filter/sort、history、source、correct/forget。
- Personalization controls：Saved use、past-chat use、automatic learning、sensitive categories、pause/reset、Temporary Chat。
- Admin/Support：健康度、队列、purge/index lag、typed denial、receipt/watermark，不展示内容。

| Scenario | Expected behavior |
|---|---|
| 相同 command 超时重试 | 返回同一 receipt；相同 identity 不同 digest typed conflict |
| 两来源对同一事实冲突 | contested，不覆盖；提示用户确认或限定有效时间 |
| 用户删除聊天但已显式保存记忆 | 分别提示两个 authority；source 删除触发 provenance re-evaluation，不假装一项操作必然删除另一项 |
| 已打开回答期间 Memory 被删除 | UI 立即标 source revoked；下次 tool call 不返回内容；旧文本不被偷偷改写 |
| Project 成员被移除 | 新选择/search 立即拒绝；existing run 受 authorization/revocation policy fence；不泄漏 project existence |
| embedding/provider 故障 | lexical fallback 或 no-memory continuation；不得跨 scope broaden search |
| empty/low-confidence result | 返回 none + receipt，不用全局热门记忆填充 |
| very long memory | bounded canonical payload，selection truncates with ref；按需再查，不截断 authority record |

## 7. Technical considerations

### Constraints

- Platform Memory 作为 `kokoro-platform` 内独立 module/process role 发布，不新建第五仓库、不增加默认 Infra container。
- `platform-api` 提供 Web/Admin OpenAPI；`platform-memory-runtime` 提供 GA ConnectRPC；`platform-memory-worker` 处理 proposal/index/purge。
- Session 独占 conversation history/search/source；GA 独占 execution/checkpoint；Platform Memory 独占 learned memory/proposals/selections。
- M1a 先用 PostgreSQL FTS/trigram；pgvector 必须通过 extension、RLS prefilter、recall、migration/rollback、backup/restore 与 capacity gate 后在 M1b 开启。
- embedding 只能经 Model Gateway 的 `memory-selection` purpose/model policy；不能由 worker 直连 provider。
- 一个 memory payload ≤16 KiB，query ≤8 KiB，proposal ≤32 KiB，selection/search ≤20 items，provenance ≤32 sources；超限 typed reject/truncate。

### Integration points

- Platform Identity/Site/Project：scope、subject generation、membership/authorization epoch、feature policy。
- Platform Admission：RunContextManifest 与两个 owner-issued handles 的编排，不自行签发。
- Model Gateway：embedding authorization、routing、usage evidence；Memory 不持 provider key。
- Session：conversation search/source/outbox、ContextUse projection、data-governance participant。
- GA：Root-generated typed MemoryPort；proposal/read/search receipts 进入 durable evidence。
- Data Governance：revoke/purge/export/LegalHold coordinator 与 participant receipts。
- Web：Site BFF public controls、Temporary Chat、per-response explanation；不得直连 internal runtime。

### Data requirements

- revision/provenance/selection/search/use receipts append-only；current head 以 CAS 推进。
- content 加密 at rest；key revision/audience/associated-data digest 显式；plaintext/query 不进入日志、metric、trace、receipt safe payload。
- logical revoke 同步生效，physical purge 异步且有 cutoff/watermark；content-free tombstone 不能含稳定公共 content hash。
- prelaunch 旧实验数据不迁移为产品记忆；M2 hard-cut 后 Agent 旧 free-form memory store 不进入生产 composition。

## 8. Dependencies and risks

| Dependency | Owner | Status | Impact if delayed |
|---|---|---|---|
| Platform M0 authority kernel and protected content adapter | Platform Memory | authority kernel dormant; protector absent | M1 public mutation不能激活 |
| Site/Subject/Project authorization facts | Platform Identity/Workspace | available foundation | 无法安全开放 user/project scope |
| Session cited search/source contracts | Session + Root Contract | not implemented | past-chat 与 automatic learning 延后 |
| MemoryPort/RunContextManifest promotion | Root + GA + Platform + Session | ADR accepted, contract absent | GA 不能生产使用 Memory |
| Model Gateway embedding role | Model Platform | not qualified | M1b 延后，M1a lexical 仍可上线 |
| Data Governance purge participants | Privacy/Data Governance | partial PRD only | delete/reset certification No-Go |
| Web Memory settings/explanation | Web Site Kit | not implemented | 不能对用户开放 automatic learning |

| Risk | Likelihood | Impact | Mitigation |
|---|---:|---:|---|
| 错误记忆降低信任 | M | H | proposal/confirmation、citation、confidence、correction、offline eval + canary |
| 删除后缓存/embedding 残留 | M | H | revocation fence 先行、participant watermark、purge certification、backup policy |
| vector filter 跨 scope 泄漏 | L | Critical | authorization prefilter/candidate partition、RLS、negative canary；未过 gate 不启用 pgvector |
| prompt injection 被学成指令 | M | Critical | instruction authority分离，外部/assistant/tool只可 proposal，sensitive/executable deny |
| 自动学习成本/延迟失控 | M | M | durable debounced worker、batch、quotas、Site policy、proposal lag SLO |
| 多 Agent 相互污染 | M | H | stable proposer identity、parent scope、proposal only、no direct active write |
| immutable Run 与删除冲突 | M | H | privacy revocation优先，content-free receipt保留审计，checkpoint participant purge |

## 9. Milestones and launch gates

| Milestone | Deliverable | Promotion gate |
|---|---|---|
| M0 — Authority | schema/domain/receipts/explicit mutation/control，全部 dormant | fresh migration、role/RLS audit、no route/process/grant |
| M1a — User memory + lexical retrieval | public CRUD/settings、FTS/trigram、selection snapshot、Temporary Chat、purge/export | isolation/delete/citation 100%；Web controls complete |
| M1b — Semantic retrieval | approved embeddings、deterministic hybrid rank、index rebuild/rollback | pgvector qualification、recall/latency/cost、RLS negative certification |
| M2 — GA integration | MemoryPort、RunContextManifest、dynamic search/proposal receipts、ContextUse UI | four-repo compatibility、replay/revocation/expiry race suites、GA core review |
| M3 — Automatic learning | Session source feed、extract/dedupe/conflict/confirmation/suppression | precision target、sensitive-category No-Go tests、user opt-in and undo |
| M4 — Advanced project context | reviewed project summaries、branch lineage、multi-agent attribution | Project membership/revocation/export/delete certification |

Release certification additionally requires clean-clone builds, generated mirror zero-diff, rollback rehearsal, no extra default
container, operator runbook/alerts, and zero open Critical/High privacy or authorization findings.

## 10. Open questions

- [ ] 首个 LaunchProfile 默认只开放 explicit saved memory，还是同时开放 past-chat lexical search？Owner: Personalization Product Lead
- [ ] 哪些 sensitive categories 永久禁止存储，哪些允许 explicit-only？Owner: Privacy + Security
- [ ] `memory used` indicator 的默认展开层级与 mobile/a11y 交互？Owner: Web Design + Accessibility
- [ ] M1a 的 lexical recall baseline 与 golden evaluation set 如何按语言/Site 构建？Owner: Memory QA
- [ ] 删除时 retained financial/security facts 与 Memory source citation 的用户文案？Owner: Data Governance + Legal

## 11. References

- [ADR-013: Product Memory and Context Authority](../../kokoro-handbook/decisions/ADR-013-product-memory-and-context-authority.md)
- [PRD-05: Chat Conversation, Run and Interaction](2026-07-25-prd-05-chat-conversation-run-and-interaction.md)
- [PRD-15: Notification, Preferences and Data Rights](2026-07-25-prd-15-notification-preferences-and-data-rights.md)
- [OpenAI: saved memories and chat-history reference](https://help.openai.com/en/articles/11146739-how-does-reference-saved-memories-work)
- [Google Gemini: personalization from past chats](https://support.google.com/gemini/answer/16598469?hl=en)
- [LangGraph memory concepts](https://docs.langchain.com/oss/python/concepts/memory)
- [LangGraph memory service template](https://github.com/langchain-ai/memory-template)
- [Letta AI Memory SDK](https://github.com/letta-ai/ai-memory-sdk)

## 12. Revision history

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-07-30 | Kokoro architecture/product review | Initial product-memory PRD aligned to ADR-013 and M0 authority |
