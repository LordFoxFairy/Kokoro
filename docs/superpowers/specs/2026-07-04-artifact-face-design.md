# 产物面设计（R-artifact，2026-07-04 定稿——决策完备，"继续"即可执行）

站在 LangChain 原生件上，吸取 CC（文件系统真源/路径心智）、OpenAI CI（id+MIME 引用、
下载端点）、claude.ai artifacts（按类型渲染）。music/video 成品的硬前置。

## 一、核心难点与定案

**难点：产物字节的跨服务旅行。** agent 与 session 是独立进程/pod；deepagents backend
文件系统对 session 不可达（state 虚拟盘活在 checkpoint 里；local_shell 是 worker 本机盘；
多 pod 更不通）。产物不能只落 backend FS。

**定案：双面分工——backend FS 服务模型，产物库服务人。**
- 模型侧：工具照常可写 backend FS（模型后续轮可re-read，CC 心智不变）；
- 用户侧：产物注册即写入**共享产物库（ArtifactStore）**，wire 只带引用，
  session 从产物库出字节。两侧解耦，state 后端与多 pod 天然安全。

## 二、四层设计

### 1. agent：ArtifactStore 端口 + 工具通道
- `storage/artifacts.py`：`ArtifactStore` 协议
  `put(run_id, name, mime, data) -> ArtifactRef` / `get(artifact_id) -> (mime, bytes)`；
  双实现随既有后端二元律：**本地目录**（`KOKORO_ARTIFACTS_DIR`，sqlite 档单机）/
  **mongo GridFS**（多 pod 档）。artifact_id = `{run_id}/{uuid8}-{name}`（不透明字符串）。
- `ArtifactRef` 模型：`{artifact_id, name, mime, bytes}`（bytes=大小）。
- 产物类工具用 LangChain 原生 `response_format="content_and_artifact"`：
  content=给模型的一句摘要；artifact=ArtifactRef（**类型化元数据通道，拒绝路径嗅探**）。
  工具经装配注入 `save_artifact` 闭包（政策装配注入：run 归属在装配期绑定）。
- 投影层：`tool_returned_payload` 读 ToolMessage.artifact（TypeAdapter 洗净，
  非 ArtifactRef 形状忽略——第三方工具可能塞任意 artifact），升到 wire。

### 2. 契约（spec 单源，无生产者期自由重塑——不留兼容层）
- `objects` 加 `Artifact {artifact_id, name, mime, bytes:int}`；
- `tool.returned.artifact_ref: string?` → `artifact: object:Artifact?`（缺席=无产物）；
  `subagent.tool.returned` 同步加 `artifact?`（子代理也能产出）。
- http spec：`GET /sessions/{sid}/artifacts/{artifact_id}` 二进制响应（content-type=mime）。

### 3. session：产物端点
- relay 透传 artifact 字段（穷尽 case）；消息/暂停台账不存字节；
- HTTP 端点直连同一 ArtifactStore 后端（读侧实现与 agent 对称：目录/GridFS），
  流式回体 + content-type + content-length；未知 id → 404。

### 4. web：按 MIME 渲染（全格式预览矩阵）
- tool 行有 `artifact` 时渲染产物卡，按 MIME 主类分派（用户裁定：预览支持各种格式）：
  `audio/*`→播放器；`video/*`→播放器；`image/*`（含 svg）→图；
  `text/markdown`→富文本（复用 thread 的 markdown 渲染器）；
  `application/json`→格式化高亮；`text/csv`→表格（首 200 行）；
  `text/html`→sandboxed iframe（srcdoc + sandbox 属性，禁脚本外联）；
  `application/pdf`→iframe 内嵌预览；其余 `text/*`→等宽文本（首 64KB，截断标注）；
  未知类型→下载卡（文件名+大小+MIME）。
- 文本类预览由 web fetch 端点字节自行解码（UTF-8，失败降级下载卡）；
  预览一律懒加载（点开产物卡才拉字节），大文件不拖累会话流。

## 三、首个真实生产者（验证锚）
`generate_audio_sample` 暂不做——**用 execute/write 路径造不出真媒体**；验证锚改为：
测试注入的假产物工具（unit/e2e）+ 真模型场景 G：挂一个把文本转 wav 的本地工具
（纯 Python 合成正弦波，零外部依赖）→ 真产物字节经全链到 web 播放器可放。
music 真工具（suno 等 API）属成品批次，接在本面之上零改动。

## 四、验收清单（执行期照单）
1. agent：ArtifactStore 矩阵测试（目录/GridFS 同语义：put/get/未知 id fail）+
   投影升 wire 测试 + 洗净边界（畸形 artifact 忽略不炸）；
2. 契约：generate/check 全镜像 + 计数门禁更新；
3. session：端点测试（MIME/404/字节一致）+ relay 穷尽；
4. web：产物卡渲染测试 + tsc/lint（他人 i18n 现场不碰）；
5. e2e：假产物工具全链（POST→事件带 artifact→端点回体字节一致）；
6. 真模型场景 G：正弦波工具真产物 + Playwright 播放器截图；
7. 四仓提交推送 + CI 绿。

## 五、边界（明确不做）
- 产物版本/编辑（claude.ai 式迭代）——canvas 批次；
- 产物入库 hub/跨会话检索——hub 批次；
- 大小治理：V1 单产物上限 64MB（env 可调），超限工具侧 fail-loud；
- 清理：随 R-retention 分层 TTL，本面只按 run 归属键预留。

## 六、打磨补遗（执行前最后一轮自审）

1. **路径穿越防御**：artifact_id 进 URL 且含名字段——目录后端 get 时 resolve 后必须
   断言仍在根目录内（`..`/绝对路径注入即 404）；GridFS 天然免疫。
2. **产物幂等**：id 弃随机 uuid，改 `{run_id}/{tool_call_id}-{name}`（确定性）——
   HITL resume 重放/崩溃重拾重跑工具时 put 幂等覆盖，不产孤儿副本；
   与 keep-first 工具结果缓存双保险。
3. **后端选择归一**：`KOKORO_ARTIFACT_BACKEND=dir|mongo`（缺省 dir，随 checkpoint
   二元律；mongo 档复用既有 KOKORO_MONGO_URL/DB），dir 根 `KOKORO_ARTIFACTS_DIR`
   （缺省 ./kokoro_artifacts）。
4. **摘要与截断**：content（给模型摘要）照常走 result 通道与 4000 字截断护栏，
   与 artifact 字段互不影响；产物卡渲染不依赖 result 文本。
5. **端点安全面**：session 产物端点沿用既有 CORS 锁定（仅本机 web），无鉴权前
   不对公网暴露（与 messages 端点同边界，不新增风险面）。
