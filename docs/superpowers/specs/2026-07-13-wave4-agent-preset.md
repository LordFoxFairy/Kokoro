# Wave 4 · AGENT-PRESET 子 spec——目录即配置的 preset(agent 半场;web 选择 UX 另批)

状态:执行稿(上级=总设计稿 §6 Wave4,已获批)。纲领:目录即配置的 preset、session 首条锁(已落)、
agent 选择 UX(web 半场,批3 随 web lane;本 spec 只做 agent 半场,避免 web 双写者)。

## 现状

契约 RuntimeConfig.agent(optional,缺省 general)已上 wire;session 首条锁已落;agent 侧
assembly 按 agent_type 分派配方,但 preset"加目录零代码"未落——agent 名现在如何被消费需先测绘
(prompts/<agent>.md 解析键在契约注释里,实现未必在)。

## 语义

- **目录即配置**:agents 资产目录(现有 prompts/资产布局内)每个 preset 一个子目录或 md 文件:
  `<agent>.md`(人格 system prompt,frontmatter 可带 description/缺省 tools/skills 倾斜——形状
  按现有资产文件风格定,别发明新配置语言)。新增 preset=加文件,零代码改动。
- 装配:RuntimeConfig.agent=名→资产目录解析→找不到=assembly_failed fail-loud(不静默回退
  general;缺省未带 agent 才是 general)。
- 与 agent_type 关系:preset 是 general 类型下的具名人格(纲领:agent 是类型下的具名实例);
  不新增 agent_type 枚举。
- 列表读面:session/hub 现不需要枚举 preset(web 选择 UX 批3 时再定读路径;若届时要上契约由主控冻)。

## 验收

- 加一个 fixture preset 目录→装配走它的 system prompt(测试断言 prompt 内容进装配);未知名
  fail-loud=assembly_failed;缺省缺席=general 不变。
- agent 全量只增不减三绿;e2e 回归绿(gate 现流不带 agent 字段,透明)。
