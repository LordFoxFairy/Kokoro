# Wave 2 · R3 子 spec——tool effect journal(unknown-outcome 不自动重放)

状态:执行稿(上级=总设计稿 §6 Wave2-4,已获批)。仓面:仅 kokoro-agent(私有 ledger,无契约变更)。

## 语义(纲领原文:「tool effect journal;unknown-outcome 不自动重放,支持 idempotency key 才自动收敛」)

- 副作用工具执行前先落 journal 行{run_id, tool_call_id, name, status: started, at}(keep-first,
  锚=tool_call_id);工具返回后置 succeeded|failed(附 result_hash 可选)。
- **重放守门**:checkpoint takeover/resume 重放路径上,工具节点执行前查 journal:
  - 无行→正常执行(先落 started)。
  - 行=succeeded/failed→不重执行,直接以记录结果短路(幂等重放)。
  - 行=started(=unknown-outcome:上次崩在执行中)→**默认不自动重放**:返回
    is_error 工具结果(文案含 unknown_outcome 语义),交模型/HITL 决策;仅当该工具声明
    idempotent(V1 白名单:纯读类 read_file/list_dir/glob/grep 等无副作用工具)才允许重执行收敛。
- 判定范围:经 backend 执行的副作用工具(write/execute/deliver 类);纯读工具可整体豁免 journal
  (白名单即豁免表,一处维护)。MCP 工具一律按非幂等处理(外部副作用不可知)。
- journal 行随 run 终态后按既有 ledger TTL 语义回收,不做独立 GC。

## 验收

- 故障注入:started 后崩溃→重放不重执行非幂等工具且结果为 unknown_outcome 错误;幂等白名单工具
  重执行收敛;succeeded 后崩溃→重放短路返回已记录结果,不双写。
- agent 全量只增不减三绿;e2e 全绿(happy path 透明)。
