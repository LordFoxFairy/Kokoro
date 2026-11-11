# Kokoro 文档

从你要解决的问题进入，不从历史方案目录开始。

| 读者／问题 | 当前入口 |
| --- | --- |
| 用户：如何开始、选择资料、看结果、设置计划 | [产品使用指南](https://github.com/LordFoxFairy/kokoro-app/blob/2b2522b784492c248d3a95e6530fba9b03f562b4/developer-docs/docs/product/index.md)（现有 VitePress 门户源码） |
| 产品／研发：批准的需求和对象关系 | [产品要求 PRD](kokoro-handbook/product/09-v2-prd.md) |
| 工程：链路、身份、事件、数据分别由谁负责 | [当前技术总览](kokoro-handbook/technical/00-system-overview.md) |
| 接口调用者：怎样接入 | [开发者文档](https://github.com/LordFoxFairy/kokoro-app/blob/2b2522b784492c248d3a95e6530fba9b03f562b4/developer-docs/docs/introduction.md)，参考页由 BFF 正式合同生成 |
| 协作：本次交付、未验和下轮事项 | [当前事实](CURRENT.md)、[唯一 Task A TODO](../todo.md)；Task B 由其独立负责人维护 |
| 改代码：目录、规范与验证入口 | [代码地图](CODEBASE_MAP.md)、[总体架构](ARCHITECTURE_STANDARD.md)、[完整索引](INDEX.md) |

## 怎么判断一份文档是否有效

- 产品指南写当前操作与限制；PRD 写已批准需求，不把目标写作通过记录。
- 技术总览说明当前实现，owner 契约与 canonical schema 管字段／数据，Root 不复制第二份可编辑事实源。
- 长期规范和有效 ADR 保留；已替代 Task A 执行方案与错误旧拓扑从工作区删除，历史从 Git 固定版本追溯。
- `product/` 里的早期研究与其它 owner 的有效规则分开保留，不作为当前操作手册。Task B 文档不因 Task A 收尾而自动完成或删除。
- 内部日志与收据不发布到公开门户。公开门户已有搜索和导航；本轮不新建站点、不部署。

产品文档组织参考 [Manus 在线文档](https://manus.im/docs/introduction/welcome)的任务导向表达，核对于 2026-11-11 UTC；不因此承诺其全部产品能力。
