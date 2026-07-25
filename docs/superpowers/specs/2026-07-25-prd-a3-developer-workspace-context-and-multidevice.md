---
artifact: product-requirements-document
prdId: PRD-A3
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: developer-workspace-repository-worktree-context-diff-test-code-checkpoint-rewind-git-pr-multidevice
accountableProductRole: Developer Agent Product Lead
mandatoryCosigners: [Developer Workspace, Execution Runtime, Source Control, Security, GA Owner, Accessibility, Support, SRE, QA]
engineeringOwner: team:developer-workspace-engineering
qaOwner: team:developer-workspace-quality
supportOperationsOwner: team:developer-workspace-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-A3：Developer Workspace、Context 与 Multi-device

## 1. Overview

### Problem

开发代理不仅需要“运行shell”，还要理解Repository/Revision、尊重dirty worktree、隔离并行修改、展示diff、运行test、建立可恢复
checkpoint并安全创建commit/PR。如果把Worktree当ExecutionTarget、把Git commit当GA checkpoint，或者把聊天rewind解释为
`git reset --hard`，会覆盖用户修改、污染分支、泄漏secret并让多设备/多Agent无法确定谁拥有当前状态。

### Solution

建立GA外部Developer Workspace domain：RepositoryBinding、WorkspaceSnapshot、Worktree、ChangeSet、TestRun、CodeCheckpoint和
SourceControlOperation均为版本化对象；文件/命令实际effect通过ExecutionTarget。Context按manifest和budget选择，不默认上传整库。
attach/fork/new run共享Client Access语义；CodeCheckpoint是产品级conversation/workspace关联，不等于或暴露GA内部checkpoint。

### User stories

| ID | User story | Priority |
|---|---|---|
| DEV-US-01 | 用户可连接repository并看到当前branch、revision、dirty状态和安全范围 | P0 advanced |
| DEV-US-02 | Agent可在隔离worktree中搜索、修改、运行test并展示可审阅diff | P0 |
| DEV-US-03 | 用户可接受、部分接受、拒绝或继续修改ChangeSet，不覆盖原有工作 | P0 |
| DEV-US-04 | 用户可创建CodeCheckpoint，并在安全条件下恢复/派生新工作区状态 | P0 |
| DEV-US-05 | 用户可显式创建commit/push/PR并看到CI状态，credential不暴露给GA | P0 |
| DEV-US-06 | 用户在Web/CLI/Desktop/IDE间attach/fork/new run时看到同一Task和workspace事实 | P0 |

## 2. Goals、Metrics and Non-Goals

### Goals

1. Repository、Workspace、Worktree、Target、Run和GA checkpoint概念不混淆。
2. 用户既有dirty/untracked/ignored修改在未明确授权时永不覆盖、删除或上传。
3. 并行Run/ChildRun/AgentTeam默认独立Worktree/branch，冲突显式合并。
4. 每个文件/command/git effect有exact TargetAction identity、permission、receipt和diff provenance。
5. CodeCheckpoint可恢复产品上下文但不改写Git/GA历史或复制未授权secret/permission。
6. context选择、test、commit、push、PR和CI形成可审计闭环。

### Success metrics

| Metric | Target |
|---|---:|
| 未授权覆盖/删除用户dirty、untracked或ignored文件 | 0 |
| path/symlink/worktree边界外读取或写入成功 | 0 |
| 并行Agent写入同一worktree未声明冲突策略 | 0 |
| CodeCheckpoint/rewind改写GA checkpoint或published Git history | 0 |
| commit/push/PR缺用户授权、diff digest或credential lease | 0 |
| secret进入prompt/context/log/Artifact/Support bundle | 0 |
| attach/reconnect重复command/test/push/PR effect | 0 |

### Non-goals

- 不实现完整Git hosting、IDE、CI provider或云开发环境产品。
- 不提供任意`git reset --hard`、force push、delete branch/repo或绕过branch protection的快捷方式。
- Worktree不是ExecutionTarget kind；RepositoryBinding也不是Project membership。
- CodeCheckpoint不是LangGraph/GA checkpoint，不读取或修改GA内部state。
- 不默认索引/上传整个repository、`.git` objects、ignored files、credential或用户home目录。
- 本PRD不授权改变GA graph/prompt/tool/Handoff/checkpoint/cancel/terminal。

## 3. Canonical objects

```text
RepositoryBindingRevision
  immutable siteId / repositoryBindingId / projectRef / sourceControl provider ref?
  repository opaque identity / canonical root policy / default branch / access policy
  binding revision / status / observedAt

RepositoryRevision
  immutable siteId / bindingRef / commit object identity / parent refs
  branch/tag safe refs / tree digest / observed provider revision

WorkspaceSnapshotRevision
  immutable siteId / binding+repository revisions / target+worktree refs
  tracked/dirty/untracked/ignored safe manifest / root+path policy / digest
  createdAt / scanner+tool revisions

WorktreeRevision
  immutable siteId / worktreeId / bindingRef / targetRef / root opaque identity
  base RepositoryRevision / branch ref? / owner execution ref / isolation policy
  state / lease+worktreeEpoch / created+expiry

ContextManifestRevision
  immutable siteId / workspace snapshot / included file+symbol+artifact refs
  exclusion+redaction reasons / byte+token budgets / generatedAt / digest

ChangeSetRevision
  immutable siteId / worktree+base snapshot / ordered file operations
  patch/blob refs / generatedBy Run+Action refs / conflict+validation state / digest

TestRun
  immutable siteId / worktree+ChangeSet revisions / command profile
  TargetAction ref / environment+dependency lock digest / outcome+Artifact refs

CodeCheckpoint
  immutable siteId / checkpointId / task+session+conversation leaf refs
  WorkspaceSnapshot+Worktree+ChangeSet refs / ExecutionManifest ref
  createdBy / label / lifecycle / digest

SourceControlOperation
  immutable siteId / kind=commit|push|pull_request|merge_request
  binding+worktree+base+ChangeSet refs / exact diff digest
  target branch/repo / permission+credential lease refs / idempotency / receipt
```

所有local root/path/repository URL在server侧只保存opaque identity或safe derivative；raw path/credential不进入cross-device projection。

## 4. Repository onboarding and trust

- local repository由Client/ExecutionTarget connector检测root、VCS、owner、安全目录、remote safe class、branch和dirty状态。
- remote repository使用Site-scoped Connection/OAuth，secret只在SourceControl adapter materialize；GA/Workspace不见token。
- 用户确认exact Project、repository identity、root boundary、默认read scope和是否允许创建isolated worktree。
- symlink/junction/mount/nested repo/submodule/LFS/large/binary/ignored policy在binding revision冻结。
- repository remote变化、owner transfer、root移动、unsafe ownership或credential revoke使binding stale/restricted。
- 同remote URL或commit hash不跨Site自动关联Project、context、permission或Task。

## 5. Snapshot and context selection

- 每次Run/Operation冻结WorkspaceSnapshotRevision，不依赖mutable“current files”。
- manifest区分tracked clean、tracked dirty、untracked、ignored、binary、secret-suspect、too-large和unreadable。
- 默认context从用户intent、explicit files、repository map、symbol/search results和dependency graph逐步选择；不先读取全库再过滤。
- `.gitignore`不是security boundary，但ignored文件默认不读/上传；显式需要时单独permission和secret scan。
- context budget按bytes/tokens/file count/depth/time限制；truncation列出未包含内容和reason，不伪装complete。
- secret detector产生evidence并redact/block；不得把secret值发送模型以询问“是否敏感”。
- ContextManifest包含exact file revisions/ranges、encoding/newline和tool revision；相同path变化后旧manifest不继续写入。
- generated/vendor/build artifacts按policy排除；需要分析时使用独立scope和size budget。

## 6. Worktree and concurrency

- 默认每个并行写execution拥有独立WorktreeRevision和worktree lease；read-only tasks可共享immutable snapshot。
- 用户选择共享worktree时，必须显示冲突风险并使用file/ChangeSet expectedVersion；不能依靠“Agent会小心”。
- stale worktreeEpoch无法写file、ChangeSet、Test或SourceControlOperation receipt。
- Agent不得清理/format/move与任务无关的用户changes；发现overlap先进入conflict/waiting_interaction。
- base branch更新不自动rebase运行中worktree；用户显式refresh/rebase/merge创建新revision和diff。
- worktree TTL只清理无active action、无uncommitted ChangeSet、无checkpoint/retention引用且已fence的资源。
- nested Agent/ChildRun提交ChangeSet给parent/aggregator，不直接写另一个member worktree。

## 7. Editing and ChangeSet review

- file mutation使用typed create/update/move/delete/patch Action；path、base content digest、encoding和newline冻结。
- patch apply前重读exact file/real path；base mismatch返回conflict，不fuzzy apply到未审阅区域。
- binary/large/generated file使用明确replacement contract，不把binary塞text patch。
- ChangeSet显示summary、per-file diff、generated/renamed/deleted、secret/security signals、test impact和unrelated detection。
- 用户可accept all、按file/hunk选择、request changes或discard Agent-ownedChangeSet；discard不回滚用户原修改。
- partial accept创建新ChangeSetRevision和workspace snapshot，原proposal保留审计。
- formatter/codegen只在显式计划和已批准范围运行；机械大diff与源schema/template linkage分别展示。

## 8. Test、build and verification

- test command来自repository/project published profile或用户明确命令，不由Agent拼任意shell绕过permission。
- TestRun冻结worktree/ChangeSet、dependency lock、runtime、env/network/sandbox和command digest。
- output先结构化/redact/size-limit，再成为Artifact；ANSI/links/path不可信。
- timeout/cancel/connector disconnect按TargetAction certainty收口；unknown TestRun不能自动重跑。
- skipped/only/filter、flaky retry和unreachable integration必须显式；“exit 0”不等于全部required verification通过。
- result区分passed/failed/partial/canceled/unknown/environment_error，列出coverage与未运行项。
- dependency install、migration、paid integration或external side effect需要独立permission/budget。

## 9. CodeCheckpoint and rewind

- CodeCheckpoint是Task/Conversation leaf与WorkspaceSnapshot/ChangeSet/ExecutionManifest的产品关联，便于比较、派生和恢复。
- 创建checkpoint不提交Git、不复制workspace bytes、不冻结GA internal checkpoint；只引用immutable facts/Artifacts。
- “rewind”默认创建新WorktreeRevision/branch from checkpoint base并保留当前worktree；不是destructive checkout/reset。
- 若用户明确要求覆盖当前Agent-owned worktree，先证明无用户dirty/untracked/unknown action并展示destructive diff；仍禁止宽路径删除。
- published commit/push/PR不被rewind改写。需要revert时创建新SourceControlOperation/commit。
- checkpoint恢复重新验证Site/Project/repository/Target/permission/secret/Dependency revisions和Budget；旧grants不继承。
- GA conversation/Run恢复只使用Session/GA既有contract；CodeCheckpoint不能导入或编辑LangGraph state。

## 10. Commit、push and PR

- commit、push和PR是三个独立typed Actions；用户允许commit不等于允许push，push不等于允许开PR/merge。
- commit review冻结exact staged ChangeSet/diff digest、message、author policy和verification evidence；未选择文件不stage。
- hook执行策略、签名、DCO/CLA和secret scan由Project/Repository policy冻结；失败不自动`--no-verify`。
- push冻结remote/repository、branch、expected remote head、force policy和credential lease；默认拒绝force push。
- remote head变化返回conflict；不自动rebase/force。
- PR冻结base/head、title/body safe draft、diff/commit/test refs和reviewers policy；response丢失查询same provider operation。
- provider callback/CI映射到exactSite/repository/PR；unknown/duplicate/late使用inbox/reconcile，不伪造merged/passed。
- merge、release、deploy另属SourceControl/Application Runtime command，不因PR创建自动执行。

## 11. Multi-device、attach and fork

- TaskView展示safe repository/worktree/ChangeSet/Test/PR projection和freshness，不传raw local path/credential。
- attach在新客户端查看同Task/Workspace facts，使用same Action/receipt，不创建Run/Test/push。
- fork从选定conversation/CodeCheckpoint创建新Session branch、ExecutionRoot和通常新Worktree；保留parent lineage，不复用Hold/permission。
- new run使用current selected WorkspaceSnapshot或显式新snapshot，显示revision diff并重新Admission。
- local target离线时其他设备可review已有Artifact/diff，但不能假装能读取/修改离线filesystem。
- 多设备并发accept/permission/commit使用expectedVersion；loser刷新，不last-write-wins。

## 12. Cost、retention and data rights

- model/tool/Target/test/CI/Artifact Usage绑定同ExecutionBudget tree；Workspace不计算customer price。
- repository indexing/context storage、persistent worktree和CI provider成本需Offering/Profile显式开放，不做隐藏持续扣费。
- WorkspaceSnapshot/ContextManifest/ChangeSet/TestArtifact/CodeCheckpoint/PR refs是Data Rights participants，按Site/Project retention。
- source control provider/Git remote已有副本不宣称由Kokoro删除；删除结果区分local cache、cloud worktree、Artifact和external provider。
- LegalHold/incident可能保留safe diff/evidence；用户export不包含secret、credential或其他Site data。

## 13. User-visible states

| State | Meaning | Recovery |
|---|---|---|
| repository_ready / stale / restricted | binding可用、变化或受限 | refresh/re-auth/rebind |
| snapshot_ready / incomplete | context事实完整或有排除 | inspect/include with permission |
| worktree_ready / busy / conflict / offline | 可编辑、占用、冲突或Target离线 | wait/new worktree/resolve/reconnect |
| changes_proposed / accepted / rejected | Agent改动等待或已有决定 | review/partial accept/request changes |
| test_running / passed / failed / partial / unknown | verification状态 | view/query/fix/new explicit test |
| checkpoint_ready / restore_blocked | 可派生或当前条件不满足 | fork/re-auth/new target |
| commit_pending / pushed / pr_open / ci_pending | source control进展 | query same operation/review/support |

## 14. Admin and support

- Developer Workspace Console显示safe binding/revision/worktree lease/ChangeSet/Test/Checkpoint/SourceControl receipts和retention。
- typed commands：RestrictRepositoryBinding、FenceWorktree、RebuildWorkspaceProjection、ReconcileUnknownSourceControlOperation、
  RevokeCredentialLease、StartWorktreeRetentionCleanup、RetrySafeArtifactProjection。
- 禁止Admin读取代码/secret、执行shell、改diff/Test result、force push、mark CI passed、merge PR或destructive cleanup。
- Support bundle由用户review、manifest和redaction生成短期Artifact；不自动打包repo/home/.git/ignored files。

## 15. Acceptance criteria

### AC-DEV-01 — Existing user work is preserved

```gherkin
Given a repository contains user dirty, untracked and ignored files before Agent work
When a ChangeSet is created, rejected, rewound or cleaned up
Then no pre-existing user content is overwritten, deleted, staged or uploaded without exact authorization
And Agent-owned changes remain separately attributable
```

### AC-DEV-02 — Parallel writers are isolated

```gherkin
Given two ChildRuns or AgentTeam members modify the same repository
When they execute concurrently
Then each uses an independent Worktree/ChangeSet by default with fenced epochs
And integration occurs through explicit diff/conflict/merge rather than shared mutable files
```

### AC-DEV-03 — Patch cannot drift

```gherkin
Given a file changes after a patch proposal
When the Agent attempts to apply the old ChangeSet
Then base digest and path resolution conflict before write
And no fuzzy or nearby application changes unreviewed content
```

### AC-DEV-04 — CodeCheckpoint is not GA checkpoint

```gherkin
Given a user creates or restores a CodeCheckpoint
When workspace and conversation context are reconstructed
Then only immutable product refs and a new authorized workspace state are used
And no LangGraph state, active Agent, tool journal, Hold or permission is read, edited or copied
```

### AC-DEV-05 — Rewind is non-destructive by default

```gherkin
Given current worktree contains later user or Agent changes
When rewind to an earlier CodeCheckpoint is requested
Then a new worktree or branch is created and current state remains recoverable
And published Git history or unrelated files are never reset or force-rewritten
```

### AC-DEV-06 — Commit, push and PR are separate permissions

```gherkin
Given a user approved an exact commit diff
When push or PR creation is requested
Then each operation requires its own current target, remote, branch and credential authorization
And remote-head conflict or response loss is queried without force or duplicate PR
```

### AC-DEV-07 — Secret stays outside model and durable artifacts

```gherkin
Given repository or command context contains a credential
When context selection, testing, diff, checkpoint, telemetry and Support bundle run
Then the value is blocked or redacted before model and persistence boundaries
And only a bounded non-persistable credential lease reaches the exact target action
```

### AC-DEV-08 — Multi-device attach is read/continue, not replay

```gherkin
Given test, commit or push outcome is pending when the first device disconnects
When another client attaches
Then it loads the same Task/Workspace/Action identities and queries receipts
And no Run, test, commit, push or PR is duplicated
```

## 16. Verification and release gates

- repository：local/remote/nested/submodule/LFS/symlink/mount/case/Unicode/large/binary/ignored/unsafe ownership。
- workspace：dirty/untracked preservation、snapshot/context budgets、secret redaction、worktree isolation/TTL/fencing。
- edits：patch digest/conflict、rename/delete/binary、partial accept、formatter/codegen和unrelated diff detection。
- tests：command profile、skip/only/flaky、timeout/cancel/unknown、output redaction和dependency/network permissions。
- Git/provider：commit/push/PR separation、remote race、hooks/signing、credential lease、duplicate callback和CI status。
- multidevice/a11y：attach/fork/new run、offline target、concurrent decision、desktop/mobile/CLI/IDE和diff semantic alternative。

No-Go：Worktree=Target；CodeCheckpoint=GA checkpoint；默认全库上传；读取ignored/secret；覆盖用户dirty；共享并行worktree；
fuzzy patch；rewind=hard reset；commit自动push；push自动PR/merge；force绕过conflict；Support/Admin任意读代码；attach重复effect。

## 17. Related documents and approval boundary

- [Client Access Plane](2026-07-25-client-access-plane-developer-client-design.md)
- [PRD-A2 ExecutionTarget](2026-07-25-prd-a2-target-device-permission-and-interaction.md)
- [PRD-02 Workspace/Project](2026-07-25-prd-02-workspace-membership-and-project.md)
- [PRD-15 Data Rights](2026-07-25-prd-15-notification-preferences-and-data-rights.md)

本文批准不授权实现、repository访问或Git操作。CodeCheckpoint命名不构成GA checkpoint变更授权；任何GA graph、state/checkpoint、
tool、Handoff、cancel、terminal或namespace变化必须专项与用户对齐。
