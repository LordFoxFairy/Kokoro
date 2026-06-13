# 契约 codegen 设计 — events.yaml → 6 镜像全生成

> 定位:item 4 旗舰。把 13-kind 契约从「单源 yaml + verify.py 门禁(防漂移但仍手维 6 镜像)」升级为「单源 yaml → 确定性 generator → 全生成 6 镜像」。编辑一次 yaml 即重生成,杜绝双向维护(用户最恨)。
> 用户拍板:**全生成(旗舰级)**;保持 4 仓独立(generator 在 root,生成进各仓)。
> 安全网:无 byte-reproduce 要求(无兼容清生成);**行为等价**由现有 430+ 测试(agent 140/session 78/web 236)+ contract verify + SSE gate 验证。

## 1. 现状(被替换的)

`contract/events.yaml`(单源,声明 transport/envelope/13 kind × 3 视角的 payload **名集** + kind/event 名 + 命名转换 + agui_only 扇出)+ `contract/verify.py`(漂移门禁:结构化解析 6 镜像,比对名集)。镜像仍手维。

6 镜像(verify.py 权威清单):
1. `kokoro-agent/.../domain/agent_event.py` — agent-out(`AgentKind = Literal[...]` + docstring payload 表)
2. `kokoro-session/.../domain/agent-event.ts` — agent-out 复校(zod by `kind`)
3. `kokoro-session/.../domain/session-event.ts` — agui-out(zod by `event` + `envelopeFields` const)
4. `kokoro-web/.../infrastructure/transport-event-schema.ts` — agui-out wire-in(zod + envelope enum + web-extra 可选)
5. `kokoro-web/.../domain/session-stream-event.ts` — render(TS union,camelCase,扁平)
6. transport 常量:`stream-port.ts` + `stream_port.py`(CURSOR_WIDTH/REDIS_FIELD/BLOCK_MS)

## 2. yaml 富化(做减法,最小侵入)

**`payload: [names]` 结构不动**(verify.py 继续工作)。新增两段,只 generator 读:

- `field_types:` — 全局 field-name → 类型覆盖。**默认 `string_nonempty`(`z.string().min(1)` / `str`)**,只声明例外:
  ```yaml
  field_types:
    is_error: boolean
    retryable: boolean
    args: record            # z.record(z.unknown()) / dict
    todos: todo_list        # array of {content, status}
    citations: array_unknown
    token_usage: unknown
    delta: string           # z.string()（可空串，非 min(1)）
    text: string
    content: string
    status: string          # web render 放宽（见 notes）
    role: enum:message_role
    source: enum:subagent_source
    description: string
  ```
- `enums:` — 命名枚举(供 field_types `enum:<name>` 引用):
  ```yaml
  enums:
    message_role: [assistant, user]
    subagent_source: [built-in, config-custom, runtime-custom]
    todo_status: [pending, in_progress, completed]
  ```
- 可选字段:沿用现有 `agui_out_web_extra`(web wire-in 可选)+ render 里以 `optional_fields: [...]` 声明(如 finalMessageId/retryable/requestId)。
- `notes:` — 关键 WHY 注释(每 kind/field 可选),generator 原样emit 进生成文件,保住理由(如 is_error 严格、run.completed status 放宽)。

> 类型是按字段语义全局一致的(segment_id 恒 string_nonempty、is_error 恒 boolean),故全局 map 足够,无需每视角重复——做减法。

## 3. generator(`contract/generate.py`)

```
generate.py            # 读 events.yaml,emit 5 schema 文件(+ 校验 transport 常量)
generate.py --check    # 重生成到内存,与磁盘 diff,有别即非零退出(CI 门禁)
```

- 纯 Python 标准库 + pyyaml(与 verify.py 同栈)。
- 每镜像一个 emitter 函数(`emit_agent_py` / `emit_session_agent_ts` / `emit_session_event_ts` / `emit_web_schema_ts` / `emit_web_render_ts`)。
- 每个生成文件顶部:`# DO NOT EDIT — generated from contract/events.yaml by contract/generate.py`。
- 命名转换:snake→camel(render)、kind dash 化(render)、text→delta/message.* 重命名(agui)由 yaml 既有声明驱动。
- transport 常量(文件 6):2 行/仓,保持手写 + verify.py 门禁(不值得生成,做减法);generator 不碰。

## 4. 落地顺序(增量,每步行为等价网验证)

每个 emitter 落地即:重生成该文件 → 跑对应仓全套 + `python3 contract/verify.py` → 必须全绿(名集不变 + 行为不变)。逐文件替换手写镜像,中途态安全(verify 仍门禁全部)。

1. **web render union**(文件 5,最简:纯 TS 类型)→ web 236 + verify 绿
2. **web transport schema**(文件 4:zod + enum + web-extra)→ web 236 + verify 绿
3. **session session-event.ts**(文件 3:zod by event + envelopeFields)→ session 78 + verify 绿
4. **session agent-event.ts**(文件 2:zod by kind)→ session 78 + verify 绿
5. **agent agent_event.py**(文件 1:Literal + docstring 表)→ agent 140 + verify 绿
6. **CI**:各仓 CI 加 `python3 contract/generate.py --check`(root 已有 contract.yml,扩成 generate --check);删「手维」叙述。
7. 全链 SSE gate 复验零漂移。

## 5. 验收

- [ ] `generate.py` 重生成 5 镜像,三仓全套 + verify + SSE gate 全绿(行为等价)
- [ ] `generate.py --check` 干净(生成==磁盘);故意改 yaml 一字段 → --check 非零(门禁有效)
- [ ] 生成文件保留关键 WHY 注释(is_error 严格 / status 放宽)
- [ ] CI 接入 --check;手维镜像叙述删除
- [ ] 4 仓独立不变(generator 在 root)

## 6. 边界
- transport 常量(文件 6)不生成,保持 verify.py 门禁(做减法)。
- 不改契约语义(纯生成等价替换);任何字段/类型变更是独立后续。
- verify.py 保留(name-set 门禁仍有价值,且校验 generator 未漂移语义);与 --check 互补。
