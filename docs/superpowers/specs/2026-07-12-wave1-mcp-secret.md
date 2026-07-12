# Wave 1 · MCP-SECRET 子 spec(secret broker + egress 防线)

状态:执行稿(上级=总设计稿 D4 后半,已获批)。分两半场:HUB 半场先行;AGENT 半场待 R1 腾树。
门:本项通过后 namespace MCP mutation **仍保持 503**(开门在 HUB-CONSIST 跨仓 E2E 后)。

## HUB 半场(kokoro-platform:kokoro-hub + platform-kit 窄件)

1. **opaque secret handle**:新集合 mcp_secrets{scope(namespace), handle(不透明 id,srt_ 前缀 cuid), name(用户命名), ciphertext, key_id, created_at, deleted_at}——**明文绝不落库**:AES-256-GCM 信封加密,密钥经 KMS port(接口化:V1 实现=env 主密钥 KOKORO_HUB_SECRET_MASTER_KEY(32B base64),生产可换 KMS 实现;key_id 支持轮换双读)。
2. **broker API**:
   - self 面(web-bff,授权同 HUB-AUTHZ owner/admin):POST /hub/self/mcp/secrets{name,value}→{handle}(value 只进不出);GET 列表(name+handle+created,不含值);DELETE 软删。
   - runtime 面(runtime caller):POST /hub/runtime/mcp/secrets/resolve{handles:[...], namespace}→{handle→plaintext}(仅该 namespace 的 handle;跨 namespace→404 不泄露存在性)。
3. **注册校验换轨**:mcp_servers 的 secret_ref 形状收紧——self 面(现 503,门后生效)只接受 `handle:srt_...` 且 handle∈本 namespace;`env:VAR` 仅 admin/official 面允许且 VAR∈部署 allowlist(env KOKORO_HUB_ENV_REF_ALLOWLIST 逗号分隔;不在表→400)。存量 official env: 引用不受影响。
4. **URL 预校验(注册时)**:self 面(门后)只收 https;解析 DNS 拒 loopback/private/link-local/multicast/metadata 网段(V1 用 node dns.promises 全量 A/AAAA);http/localhost 仅 admin 面+显式 KOKORO_HUB_ALLOW_INSECURE_URL=1(test profile)。egress 每次连接的动态防线在 AGENT 半场。
5. **日志脱敏**:handle 可日志,值/密文/主密钥永不;错误信封不含密文。

## AGENT 半场(kokoro-agent,待派)

registry 消费 `handle:` 引用→启动/装配期经 hub runtime resolve 换明文(caller=agent 凭据)→仅驻内存进 headers;连接期 egress guard:连接前解析目标 IP 拒私网段+禁 redirect(httpx 层)+防 rebinding(锁定解析 IP 连接);`secret:path` 旧留位废除(D1 不留兼容轴,契约注释同步)。

## 验收(HUB 半场)

加解密回环/双 key 轮换读/跨 namespace resolve 404/handle 形状负向/env allowlist 负向/URL 预校验负向全套(私网/元数据/http);日志断言无明文;hub 全量只增不减;mutation 门维持 503 的既有钉不动。
