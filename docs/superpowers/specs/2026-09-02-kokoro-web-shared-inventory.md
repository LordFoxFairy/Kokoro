# kokoro-web-shared 提取清单

> 日期：2026-09-02
> 来源：`kokoro/packages`
> 目标：`kokoro-web-shared`

## 提取范围

当前 package bootstrap 包含三个独立 package：

```text
packages/
├── i18n/
├── tsconfig/
└── web-core/
```

### `@kokoro/i18n`

- `package.json`：package name、exports、test/typecheck/lint scripts。
- `tsconfig.json`：ES2020、bundler resolution、strict、noEmit。
- `vitest.config.ts`：Vitest 与覆盖率阈值。
- `eslint.config.mjs`：package-local ESLint 配置。
- `INDEX.md`：公开 API 与 fallback 约束。
- `src/index.ts`：`createI18n`、`interpolate` 和相关类型。
- `test/i18n.test.ts`：插值、语言协商、fallback、翻译行为测试。

### `@kokoro/web-core`

- `package.json`：framework-free package metadata 和 typecheck/lint scripts。
- `tsconfig.json`：共享 TypeScript 基线引用。
- `src/index.ts`：`ResourceState`、`ActionState`、`ThemeTokens`、`NavigationItem`、
  `RuntimeManifest` 和 `isResourceReady`。

### `@kokoro/tsconfig`

- `package.json`：共享 TypeScript 配置 package metadata。
- `base.json`：strict、bundler、React JSX、noEmit 基线。

## 排除范围

- `*.tsbuildinfo` 等生成文件不进入共享仓库。
- `kokoro/src/i18n` 的产品词典留在产品仓库，由消费方注入 `@kokoro/i18n`。
- `kokoro/src/ui`、`kokoro/src/features` 的页面组合和业务状态留在产品仓库。
- `kokoro/src/lib/server`、BFF 地址、tenant/runtime identity、认证信封和内部 token 留在服务边界。
- 音乐领域的 Project、Generation、Candidate、Version、Stem、Export 留在 `kokoro-mori`。

## 迁移后的依赖方向

```text
kokoro / kokoro-mori
        ↓ package dependency
kokoro-web-shared
        ↓
framework-free contracts + i18n + TypeScript baseline
```

共享包不反向依赖任一产品源码。新产品先使用本地 package bridge 验证，发布阶段再切换
到私有 registry、semver 和 lockfile。

