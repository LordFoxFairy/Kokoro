# Wave 5 · session 三项子 spec(CONV-UX / SESSION-FLAKE / M6-SNAPSHOT;同 lane 串行,逐项独立 commit 独立验收)

状态:执行稿(上级=总设计稿 §6 Wave5,已获批)。主仓 kokoro-session+web 重命名 UI 一小块。

## CONV-UX(会话重命名)

- 契约已冻结(4f20939):PATCH /sessions/{id}/title {title}→{ok:true}。
- session:端点(同属主守门;软删/不存在 404;title 长度上限 256 超限 422;store 显式改写 title——
  ensureSession keep-first 语义不动,新增 renameSession 方法双后端+行为矩阵);列表/快照即时反映。
- web:rail 条目重命名入口(悬停菜单或双击)+会话头部标题可改;乐观更新+失败回滚。
- 验收:session 三绿+负向(他人 403/软删 404/超长 422);web 三绿+实走截图 wave5-rename-*;
  gate 断言一条(rename→列表反映新题)。

## SESSION-FLAKE(并发时序根治)

- 台账:263 并发套件时序 flake,单跑绿。先复现:`npx vitest run --repeat`(或多轮循环)定位 flaky
  文件;根因通常=真实计时依赖(setTimeout 竞态/共享端口/共享 mongo db 名冲突)。修法:注入 clock/
  唯一化资源名/waitUntil 轮询替代固定 sleep。**根治不是调大超时**;每个修复附复现说明。
- 验收:全量 vitest 连续 5 轮全绿(贴 5 轮尾部);单个 flaky 用例修复前后对照写进 commit body。

## M6-SNAPSHOT(snapshot.messages 双份另一半)

- 先测绘 M-6 定案(handbook 22/相关 spec):已做=delta 只 live 不落库;另一半=snapshot 与事件回放
  双份携带 messages 的读模型冗余。方案取向:snapshot 保留 messages(水合快路径)而回放从
  event_watermark 之后增量(web 已按 watermark 续传?测绘 web 水合逻辑)——若结论是 snapshot 瘦身
  或契约字段变(SessionSnapshot.messages 语义修改),**停手报主控冻结,本项只落无契约变更的部分**
  (如 web 侧去重/session 侧回放起点收紧)。
- 验收:测绘结论+落地部分三绿;双份传输量对照(粗量级即可)写报告;e2e 回放断言不破。

## 总验收

session vitest/tsc/eslint 只增不减;web 三绿;主仓 python3 scripts/e2e-v21-gate.py 全绿(含
rename 断言)。
