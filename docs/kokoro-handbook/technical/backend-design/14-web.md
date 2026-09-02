# `kokoro` Web 业务边界设计卡

## 定位

`kokoro` 是独立的用户 Web 子仓库和唯一浏览器入口。它负责页面、交互、SSE/UI 状态与 BFF client，
不承载其他 owner 的领域事实，也不再包含 `src/site` 或旧 monorepo 子目录。

## 数据与依赖边界

- Web 只调用配置的 BFF base URL；System、Billing、Capability 等 owner 地址由 BFF 管理。
- `.env.local`、`.env.test`、`.env.prod` 只声明 site/domain/BFF 运行配置，不把浏览器 header 当作租户权威。
- 所有 Web API route 保留 BFF 的错误码、request id 和分页 cursor。

## 契约与验收

验收覆盖三套 env、刷新/加载 workspace、Chat、项目/任务拖动、skills/MCP、错误 envelope、响应式
布局和生产构建；Docker 仅用于生产镜像，本地开发直接运行 dev server。
