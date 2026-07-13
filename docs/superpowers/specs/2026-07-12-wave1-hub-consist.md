# Wave 1 终局 · HUB-CONSIST 子 spec——versioned McpGrant 三仓缝合与开门

状态:执行稿(上级=总设计稿 D4/§6 Wave1-7/§8.2 9·13·14·15,已获批)。
前置:HUB-AUTHZ 三面在位;MCP-SECRET 双半场在位;MCP-REVISION 契约已冻结(主仓 7f8cc7f:
McpGrant{scope,name,revision,config_hash} 上 wire;McpServerDoc+revision;McpServerRevisionDoc/
mcp_server_revisions 入单源;RuntimeConfig.mcp_servers array:string→array:object:McpGrant 破坏性切换)。
本项=消费冻结契约,一次缝三仓,跨仓 E2E 过后开 namespace MCP mutation 门。

## HUB(kokoro-platform/kokoro-hub)

1. **revision 簿记**:define/update(admin 面现有;self 面开门后同轨)每次写活文档时 revision+1,
   并 append McpServerRevisionDoc{scope,name,revision,config_hash,transport,url,allowed_tools,
   secret_ref,created_at}(append-only,行永不改写)。config_hash=规范化 {transport,url,
   allowed_tools(排序),secret_ref} 的 sha256;secret handle 轮换(同 handle 换值)不改 secret_ref
   →不改 hash 不 bump revision(纲领:轮换实时生效)。存量文档无 revision→迁移语义:首次读到
   无 revision 的活文档按 revision=1 补齐并 append 快照行(幂等)。
2. **runtime 面扩口**:
   - resolve 聚合口返回 McpGrant[](namespace 覆盖 official 同名后的有效池,每项含当前 revision
     +config_hash),供 session 建会话快照。
   - 新增按 (scope,name,revision) 取快照行的 runtime 端点(agent 装配用),响应同时携带活文档
     现况(enabled/deleted)以支撑 fail-closed:disable/revoke→旧 grant 立即拒绝。
3. **开门**:namespace self 面 MCP mutation 撤 503(部署门=env,如 KOKORO_HUB_MCP_MUTATION=on,
   缺省 off;closure-up/e2e 环境置 on)。开门后仍全量强制既有防线:secret_ref 只收本 namespace
   `handle:srt_...`、拒 env:、URL 预校验(https/私网/metadata)。三分离场景测试(纲领原文):
   配置版本锁定(改版后旧会话锁原 revision)/紧急撤销(disable 对旧会话立即生效)/secret 轮换
   (值换、revision 不动、下次 resolve 拿新值)。

## SESSION(kokoro-session,主树)

1. 先提交已再生的契约镜像(工作树现有,与本缝合同支)。
2. buildSnapshot:mcp_servers 从名单改为经 hub runtime resolve 取 McpGrant[] 定死(对偶
   SkillGrant 内容锁;hub 不可达→建会话失败 fail-loud,不静默空池)。
3. **skills/MCP 快照统一**:SkillGrant 同走 hub runtime resolve 聚合口;MongoSkillPool 双实现
   删除(D1 不留兼容轴),session 不再直读 hub 的 Mongo 集合。

## AGENT(kokoro-agent,主树)

1. 先提交已再生的契约镜像。
2. registry 消费 McpGrant[]:按 (scope,name,revision) 经 hub 取快照行→校验 config_hash 一致
   (不一致=fail-closed 拒装)→活文档 disable/revoke→拒装(McpServerUnavailable 占位语义沿用);
   secret handle resolve 沿用 MCP-SECRET 半场(轮换不 bump revision)。yaml 兜底源仅限无 grant
   的部署级 server(E2E-33 死端口覆盖语义重述:真相在 Mongo/grant,yaml 不再参与 namespace 池)。

## 跨仓 E2E(缝合者自跑,gate 归主控收口)

§8.2 落 gate 的最低集:9(注册/禁用/覆盖→新会话快照→agent 三工具面真连)/13(门前 503;开门后
仍拒 env ref/私网/metadata)/14(改版旧会话锁原 revision、新会话取新;disable 立即生效)/15(门=
跨仓 E2E 后才开)。E2E-33 种子同步:seed 需同时写活文档(含 revision)与 revision 快照行。

## 不做

TEAM-1 完整成员体系;MCP-UX(Wave 4);R2+(control outbox,另线);根契约再改(需改即停手上报)。
