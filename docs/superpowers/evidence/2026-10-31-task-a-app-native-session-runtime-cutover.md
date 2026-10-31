# Task A App native-session runtime cutover receipt

日期：2026-10-31  
范围：C-1.3 App same-origin native session read/admission

## 变更

- App 子仓提交 `61bafcb`/`c3b3055` 新增不依赖旧 Redis/Product Session/OIDC client secret 的 native BFF 配置解析与 `admittedNativeSession`。
- `GET /api/auth/session` 在 native issuer cookie 存在时，先通过固定 Web origin/Host、Cookie allowlist、request-id、body/header/query 边界，再请求 BFF `/v1/me`；native proof 成功后直接返回 `mode: native`，不要求 `oidcRpConfig`、Product Session 或 refresh reservation。
- `POST /api/auth/signout` 在 native issuer cookie 存在时直接返回固定 issuer end-session handoff、清理残留 Product Session cookie，并不要求旧 RP config；issuer 最终确认仍由 `/iam/oauth2/end-session` native relay 完成。
- native identity admission 与既有 `admittedProductSession` 复用同一 `/v1/me` projection，失败保持 401/503 fail-closed；旧 RP/Product Session 仅作为 native cookie 缺失时的 transitional fallback，未删除。

## 证据

- TDD red/green：`tests/server/product-bff.test.ts` 先以缺失 `nativeProductBffConfig` 失败，随后覆盖无 Redis/RP secret/OIDC client 的 native config 与 BFF identity admission；`tests/app/native-session-route.test.ts` 覆盖旧 RP 配置为空时 native session 仍能返回 authenticated projection。
- App focused：`pnpm exec vitest run tests/server/product-bff.test.ts tests/app/native-session-route.test.ts tests/server/native-session-bff.test.ts`，3 files / 10 tests passed。
- App lint：`pnpm lint` 通过。
- `pnpm typecheck` 未通过既有 baseline：`src/components/blocks/app-frame/app-frame-main-surface.tsx:186` 向不含 `onReconnect` 的属性类型传值；该错误不由本切片引入，未扩大范围。
- `git diff --check` 通过；Root topology 在 gitlink 同步后另行复核。

## 未关闭范围

该切片关闭 native session read 与 Web sign-out handoff 对旧 RP 配置的运行时依赖，但尚未证明 issuer end-session 最终确认、sign-in、active-tenant switch、撤权与多标签 late-response 的真实 UI/HTTPS receipt；旧 Auth.js/OIDC RP、Product Session store/refresh reservation、旧 relay 测试继续保留。A-01/A-02/A-07 继续停写。
