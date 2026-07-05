# ADR-011: 资产源统一（skills/personas 从哪来）

- 状态：已采纳（2026-07-05）
- 关联：ADR-009（workspace 存储形态）、ADR-010（配置树与 BYO）、technical/11 实现注记

## 问题

skills/personas 资产化（配置只传名称）落地后，"文件从哪来"这件事在系统里出现了两套答案：

- workspace（会话文件面）：`KOKORO_WORKSPACE_CONFIG` 类型化 yaml，local/s3 判别，双侧共读；
- 资产（skills/personas）：只有本地目录 env（`KOKORO_SKILLS_DIR`/`KOKORO_PERSONAS_DIR`），
  多 pod 部署被迫留了一条红线——"资产目录必须随镜像/共享卷一致分发，pod 间漂移即 prompt 不一致"。

同一个关切（文件来源）两套机制，且第二套把一致性问题外包给了运维。

## 决策

资产源与 workspace 同一套配置心智：**type 判别 yaml + 凭据 env-only + 缺省零配置**。

```yaml
# KOKORO_ASSETS_CONFIG（缺省不配 = local 档，目录走 KOKORO_SKILLS_DIR/PERSONAS_DIR）
assets:
  type: local | s3
  # local: skills_dir / personas_dir
  # s3:    endpoint / bucket / region / force_path_style / prefix
```

对象键布局：`{prefix}/skills/<name>/SKILL.md`、`{prefix}/personas/<name>.md`。
凭据 `KOKORO_ASSETS_S3_ACCESS_KEY/_SECRET_KEY` env-only，写进 yaml fail-loud。

架构（`kokoro_agent/assets/` 域）：

- `source.py`：`AssetSource` 协议（`load_skills`/`load_personas`）+ `LocalAssetSource`/`S3AssetSource`
  两实现 + 配置模型。"文件从哪来"归源。
- `skills.py`/`personas.py`：`SkillLibrary`/`PersonaLibrary` 纯内存快照库。"怎么用"归库，
  库不知道源的存在。

## 快照语义（取代 sha256 运行期复核）

worker 启动时把资产源**读一次装成不可变快照**，进程期内容恒定：

- 旧机制：启动扫描锁 sha256，装配期重读文件并复核，篡改 fail-loud。
- 新机制：装配期零文件/零网络依赖，启动后盘上/桶里怎么改都不影响在跑进程；
  改资产 = 上传/落盘后滚动重启。

两者对"启动后内容不得静默漂移"的保证等价，快照严格更可用：s3 档不把 run 启动
耦合到对象存储可用性上；同一 worker 生命周期内 prompt 恒定（HITL resume 前后一致）。

## 多 pod 红线的消解

- local 档：红线仍在（各 pod 目录须一致——镜像内置或共享卷）；
- s3 档：红线消除——所有 pod 启动读同一 bucket，一致性由源保证。
  滚动重启窗口内新旧 pod 快照可能短暂不同版本，属滚动发布的常规语义，不另设机制。

s3 档同时是 platform 后台管理资产的落点：后台写 bucket，worker 滚动重启生效。

## 升级路径（P2，未授权实施）

namespace 级资产隔离：键布局天然可扩展为 `{prefix}/namespaces/<ns>/skills/...`，
库快照按 namespace 分片；机制不变，装载面加一层分组。
