# Lesson

- 场景：多仓库交接时，我把 parent + session + web 记成了全部待推仓库，漏掉了 agent 仓库这一维度检查。
- 我做错的：在给用户交接结论前，没有逐一按项目既有的“四仓库”结构（parent/agent/session/web）做完整核对，只按当前切片实际改动的三仓库在汇报。
- 下次怎么避免：凡是 Kokoro 交接、提交、push、PR 汇报，一律先列出四仓库清单逐一核对：parent、kokoro-agent、kokoro-session、kokoro-web；对每个仓库都分别说明两件事：① 是否有本轮相关改动；② 是否需要 commit / push。即使某仓库本轮无改动，也要显式写“已检查，无待提交改动，无需 push”。
