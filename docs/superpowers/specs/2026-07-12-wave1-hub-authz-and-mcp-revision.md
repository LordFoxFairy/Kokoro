# Wave 1 · HUB-AUTHZ 与 MCP-REVISION 子 spec(Hub 链前两级)

状态:执行稿(上级=总设计稿 D4/§6 Wave1-4/-5,已获批)。依赖:TRUST-ROUTES 合流(caller 等级框架)。

## HUB-AUTHZ(kokoro-platform/kokoro-hub + session HttpSkillPool 前置口)

三权限面(D4 原文):
- **runtime resolver**:仅 runtime caller(session);按已验 namespace 返回有效池。现 `/hub/skills/pool` 归此面;新增 `/hub/runtime/resolve?namespace=` 聚合出口(SkillGrant[] + McpGrant[],为 HUB-CONSIST 的 session 单解析器准备,先返回 skills+现 mcp_servers names 视图)。
- **namespace self-service**:仅 web-bff caller;scope 恒=信封 namespace(路由不收 scope 参数,收到即 400);先经 user 服务校验 active membership(读=member,写=owner/admin;TEAM-1 前 personal-team owner 即够)。开放:skills 读写(pool/启停/上传 preview·confirm/版本/配额);**MCP 只读**;MCP mutation 一律 `503 capability_registration_disabled`(fail-closed 门,HUB-CONSIST 跨仓 E2E 过后才开)。
- **official/admin**:仅 admin caller(网关代理,operator RBAC 已有):审核/curation/official flags/跨 namespace。
落点:hub 路由重排进三前缀(/hub/runtime/**、/hub/self/**、/hub/admin/**;旧路径 301 或直接迁移+调用方同步,内部 API 无外部消费者→直接迁移);membership authorizer=callService(user /owners 或新窄口 /memberships/check,读现实现定);负向:web-bff 打 admin 面 403、scope 伪造 400、非 member 403、member 写 403、MCP mutation 恒 503。

## MCP-REVISION(根契约,主控串行冻结;实现随 HUB-CONSIST)

storage.yaml 增:
```yaml
  - name: McpServerRevisionDoc   # append-only:定义每次修改新增一行,旧会话锁原 revision
    fields:
      - {name: scope, ...} / {name: name, ...}
      - {name: revision, type: int}                 # 每 (scope,name) 单调递增
      - {name: config_hash, type: string_nonempty}  # transport/url/allowed_tools/secret_ref 规范化 sha256
      - {name: transport/url/allowed_tools/secret_ref, ...同 McpServerDoc}
      - {name: created_at, type: int}
    unique: [scope, name, revision]
```
control.yaml `McpGrant {scope, name, revision, config_hash}`;RuntimeConfig.mcp_servers: array:string → array:object:McpGrant(**破坏性,四镜像+session 快照+agent 消费同波改**,归 HUB-CONSIST 一次切,本项只冻结形状)。
安全例外语义(纲领原文):当前 definition disable/revoke → 旧 grant 也 fail-closed;secret handle 轮换实时生效不改 revision(handle 内容不入 config_hash)。
测试口径(HUB-CONSIST 时落):配置版本锁定/紧急撤销/secret 轮换三分离场景。

## 不做(本两项内)
MCP-SECRET(broker/SSRF/egress,独立子项);session/agent 消费切换(HUB-CONSIST);TEAM-1 完整成员体系。
