#!/usr/bin/env node

import { createRequire } from "node:module"
import path from "node:path"
import process from "node:process"
import { createInterface } from "node:readline"
import { pathToFileURL } from "node:url"

async function rejectedMembershipAbsent(input, context, invitationUrl) {
  const cookies = (await context.cookies(invitationUrl)).filter((cookie) =>
    ["kokoro-issuer.session_token", "__Secure-kokoro-issuer.session_token"].includes(cookie.name) &&
    cookie.path === "/iam" && cookie.httpOnly)
  if (cookies.length !== 1) throw new Error("issuer session cookie unavailable for membership check")
  const response = await fetch(`${input.iam_base_url}/iam/organization/list`, {
    headers: { accept: "application/json", origin: input.web_origin,
      cookie: `${cookies[0].name}=${cookies[0].value}` },
    redirect: "manual", signal: AbortSignal.timeout(10000),
  })
  if (response.status !== 200 || response.headers.get("content-type")?.split(";", 1)[0] !== "application/json" ||
      response.body === null) throw new Error("IAM membership list unavailable")
  const reader = response.body.getReader()
  const chunks = []
  let length = 0
  while (true) {
    const part = await reader.read()
    if (part.done) break
    length += part.value.byteLength
    if (length > 65536) {
      await reader.cancel()
      throw new Error("IAM membership list oversized")
    }
    chunks.push(part.value)
  }
  const organizations = JSON.parse(Buffer.concat(chunks).toString("utf8"))
  if (!Array.isArray(organizations) || organizations.some((item) =>
    item === null || typeof item !== "object" || Array.isArray(item) ||
    typeof item.id !== "string" || item.id === "")) {
    throw new Error("IAM membership list malformed")
  }
  const ids = new Set(organizations.map((item) => item.id))
  if (ids.has(input.tenant_id) || (input.account === "existing" && !ids.has(input.existing_tenant_id))) {
    throw new Error("rejected invitation changed IAM membership")
  }
  return true
}

function inputFromStdin(raw) {
  if (process.argv.length !== 2) throw new Error("expected stdin JSON input")
  const value = JSON.parse(raw)
  const fields = ["web_origin", "web_host", "web_root", "invitation_path", "email", "password", "decision", "screenshot",
    "iam_base_url", "tenant_id", "existing_tenant_id", "account"]
  if (value === null || typeof value !== "object" || Array.isArray(value) ||
      Object.keys(value).sort().join(",") !== fields.sort().join(",") ||
      !fields.every((field) => typeof value[field] === "string" && value[field] !== "") ||
      !["accept", "reject"].includes(value.decision) || !["existing", "new"].includes(value.account)) {
    throw new Error("invalid Chromium invitation input")
  }
  const origin = new URL(value.web_origin)
  if (origin.protocol !== "https:" || origin.origin !== value.web_origin || origin.hostname !== value.web_host ||
      !origin.port || !/^\/iam\/interactions\/invitation\?id=[0-9a-f-]{36}$/u.test(value.invitation_path)) {
    throw new Error("invalid Chromium invitation target")
  }
  const iam = new URL(value.iam_base_url)
  if (iam.protocol !== "http:" || iam.origin !== value.iam_base_url || iam.hostname !== "127.0.0.1" || !iam.port ||
      !/^[A-Za-z0-9_-]{1,128}$/u.test(value.tenant_id) ||
      !/^[A-Za-z0-9_-]{1,128}$/u.test(value.existing_tenant_id) || value.tenant_id === value.existing_tenant_id) {
    throw new Error("invalid local IAM membership target")
  }
  return value
}

let browser
let stage = "input"
try {
  const lines = createInterface({ input: process.stdin })[Symbol.asyncIterator]()
  const first = await lines.next()
  if (first.done) throw new Error("missing Chromium invitation input")
  const input = inputFromStdin(first.value)
  stage = "browser"
  const require = createRequire(pathToFileURL(path.join(input.web_root, "package.json")))
  const { chromium } = require("@playwright/test")
  browser = await chromium.launch({
    headless: true,
    args: [`--host-resolver-rules=MAP ${input.web_host} 127.0.0.1`, "--no-proxy-server"],
  })
  const context = await browser.newContext({ ignoreHTTPSErrors: true, locale: "zh-CN" })
  const page = await context.newPage()
  const target = input.web_origin + input.invitation_path
  const navigationStatuses = []
  page.on("response", (response) => {
    if (response.request().isNavigationRequest()) {
      const pathname = new URL(response.url()).pathname
      navigationStatuses.push(`${pathname}:${response.status()}`)
      if (navigationStatuses.length > 8) navigationStatuses.shift()
    }
  })
  let postCount = 0
  page.on("request", (request) => {
    if (request.url() === target && request.method() === "POST") postCount += 1
  })
  stage = "invitation-entry"
  const entry = await page.goto(target, { waitUntil: "domcontentloaded" })
  if (entry?.status() !== 200 || page.url() !== target) throw new Error("invitation entry unavailable")
  await page.getByRole("heading", { name: "加入 Kokoro", exact: true }).waitFor({ state: "visible" })
  const signInForm = page.locator('form:has(input[name="decision"][value="sign-in"])')
  if (await signInForm.count() !== 1 || await signInForm.locator('input[name="csrf_token"]').count() !== 1 ||
      await page.getByRole("heading", { name: /连接中|重试登录|登录服务暂不可用/u }).count() !== 0 ||
      await page.getByRole("button", { name: /重试登录|重新加载/u }).count() !== 0) {
    throw new Error("invitation form or legacy intermediary drift")
  }
  await page.screenshot({ path: input.screenshot, fullPage: true })
  process.stderr.write("MILESTONE:entry\n")
  let registrationVerified = false
  let unverifiedLoginDenied = false
  let verificationReturned = false
  if (input.account === "new") {
    stage = "registration"
    await page.locator("details.invitation-register summary").click()
    const signUpForm = page.locator('form:has(input[name="decision"][value="sign-up"])')
    if (await signUpForm.count() !== 1 || await signUpForm.locator('input[name="csrf_token"]').count() !== 1) {
      throw new Error("invitation registration form missing")
    }
    await signUpForm.locator('input[name="name"]').fill("New invited recipient")
    await signUpForm.locator('input[name="email"]').fill(input.email)
    await signUpForm.locator('input[name="password"]').fill(input.password)
    const registeredResponse = page.waitForResponse((response) =>
      response.url() === target && response.request().method() === "POST", { timeout: 15000 })
    stage = "registration-submit"
    await signUpForm.getByRole("button", { name: "创建账号", exact: true }).click()
    const registered = await registeredResponse
    stage = "registration-result"
    await page.getByRole("heading", { name: "请查收邮件", exact: true }).waitFor({ state: "visible", timeout: 15000 })
    if (registered.status() !== 200 || page.url() !== target) throw new Error("registration did not await email")
    const signupCookies = await context.cookies(target)
    if (signupCookies.some((cookie) => cookie.name.includes("issuer.session_token") || cookie.name === "kokoro_product_session")) {
      throw new Error("registration created a session")
    }
    stage = "unverified-login"
    await page.goto(target, { waitUntil: "domcontentloaded" })
    const deniedForm = page.locator('form:has(input[name="decision"][value="sign-in"])')
    await deniedForm.locator('input[name="email"]').fill(input.email)
    await deniedForm.locator('input[name="password"]').fill(input.password)
    const deniedResponse = page.waitForResponse((response) =>
      response.url() === target && response.request().method() === "POST", { timeout: 15000 })
    await deniedForm.getByRole("button", { name: "登录并查看邀请", exact: true }).click()
    const denied = await deniedResponse
    await page.getByRole("heading", { name: "加入 Kokoro", exact: true }).waitFor({ state: "visible", timeout: 15000 })
    const deniedCookies = await context.cookies(target)
    unverifiedLoginDenied = denied.status() === 200 && page.url() === target &&
      deniedCookies.every((cookie) => !cookie.name.includes("issuer.session_token") && cookie.name !== "kokoro_product_session") &&
      await page.locator('[role="alert"]').count() > 0
    if (!unverifiedLoginDenied) throw new Error("unverified recipient admitted")
    process.stdout.write("REGISTERED\n")
    stage = "email-verification"
    const second = await lines.next()
    if (second.done) throw new Error("verification mail absent")
    const verification = new URL(second.value, input.web_origin)
    if (verification.origin !== input.web_origin || verification.pathname !== "/iam/verify-email" ||
        !verification.searchParams.has("token") || verification.searchParams.get("callbackURL") !== target) {
      throw new Error("verification mail target invalid")
    }
    const verifyResponse = page.waitForResponse((response) =>
      response.url() === verification.href && response.request().method() === "GET", { timeout: 15000 })
    const verified = await page.goto(verification.href, { waitUntil: "domcontentloaded" })
    const relay = await verifyResponse
    verificationReturned = relay.status() === 302 && relay.headers().location === target &&
      relay.headers()["referrer-policy"] === "no-referrer" &&
      relay.headers()["cache-control"]?.includes("no-store") &&
      verified?.status() === 200 && page.url() === target &&
      await page.getByRole("heading", { name: "加入 Kokoro", exact: true }).isVisible()
    if (!verificationReturned) throw new Error("verification did not return to invitation")
    registrationVerified = true
    process.stderr.write("MILESTONE:verified\n")
  }
  stage = "issuer-sign-in"
  const activeSignInForm = page.locator('form:has(input[name="decision"][value="sign-in"])')
  await activeSignInForm.locator('input[name="email"]').fill(input.email)
  await activeSignInForm.locator('input[name="password"]').fill(input.password)
  const signInResponse = page.waitForResponse((response) =>
    response.url() === target && response.request().method() === "POST", { timeout: 15000 })
  await activeSignInForm.getByRole("button", { name: "登录并查看邀请", exact: true }).click()
  const signedIn = await signInResponse
  try {
    await page.getByRole("heading", { name: "你收到一份邀请", exact: true }).waitFor({ state: "visible", timeout: 15000 })
  } catch {
    const heading = await page.locator("h1").allTextContents()
    const knownHeadings = ["加入 Kokoro", "邀请不可用", "邀请请求已拒绝", "请求过于频繁", "暂时未能打开邀请", "你收到一份邀请"]
    const pageHeading = heading.length === 1 && knownHeadings.includes(heading[0]) ? heading[0] : "unknown"
    const sent = await signedIn.request().allHeaders()
    const expectedCookie = sent.cookie?.split("; ").some((cookie) => cookie.startsWith("kokoro_iam_csrf_invite_signin=")) === true
    const originKind = sent.origin === input.web_origin ? "expected" : sent.origin === undefined ? "absent" :
      sent.origin === "null" ? "null" : sent.origin === `https://${input.web_host}` ? "no-port" : "other"
    throw new Error(`recipient preview unavailable; sign-in status=${signedIn.status()}; heading=${pageHeading}; origin=${originKind}; host-ok=${sent.host === new URL(input.web_origin).host}; csrf-cookie=${expectedCookie}`)
  }
  if (page.url() !== target || await page.getByText("工作空间", { exact: true }).count() !== 1 ||
      await page.getByText("member", { exact: true }).count() < 1 ||
      await page.locator('input[name="password"]').count() !== 0 ||
      await page.locator('form:has(input[name="decision"][value="accept"])').count() !== 1 ||
      await page.locator('form:has(input[name="decision"][value="reject"])').count() !== 1) {
    throw new Error("recipient-only invitation preview drift")
  }
  const productBefore = await page.evaluate(async () => {
    const response = await fetch("/api/auth/session", { credentials: "same-origin", cache: "no-store" })
    return { status: response.status, body: await response.json() }
  })
  if (productBefore.status !== 200 || productBefore.body?.authenticated !== false) {
    throw new Error("invitation preview unexpectedly has Product Session")
  }
  process.stderr.write("MILESTONE:preview\n")
  stage = "invitation-decision"
  const form = page.locator(`form:has(input[name="decision"][value="${input.decision}"])`)
  const decidedResponse = page.waitForResponse((response) =>
    response.url() === target && response.request().method() === "POST", { timeout: 15000 })
  await form.getByRole("button", { name: input.decision === "accept" ? "接受邀请" : "拒绝邀请", exact: true }).click()
  const decided = await decidedResponse
  if (postCount !== (input.account === "new" ? 4 : 2) || decided.status() !== (input.decision === "accept" ? 303 : 200)) {
    throw new Error("invitation decision POST drift")
  }
  let productLoginStarted = false
  let productAuthenticated = false
  let rejectedAnonymous = false
  let membershipAbsent = false
  if (input.decision === "accept") {
    stage = "product-login"
    try {
      await page.waitForURL((url) => url.origin === input.web_origin && url.pathname === "/iam/interactions/consent" && url.search.length > 1,
        { waitUntil: "commit", timeout: 15000 })
    } catch {
      throw new Error(`accepted invitation Product login navigation drift; path=${new URL(page.url()).pathname}; navigation=${navigationStatuses.join(",")}`)
    }
    await page.getByRole("heading", { name: "Review requested access", exact: true }).waitFor({ state: "visible", timeout: 15000 })
    productLoginStarted = true
    await page.getByRole("button", { name: "Agree and continue", exact: true }).click()
    try {
      await page.waitForURL((url) => url.origin === input.web_origin && url.pathname === "/app", { timeout: 15000 })
    } catch {
      throw new Error(`accepted invitation Product callback drift; path=${new URL(page.url()).pathname}; navigation=${navigationStatuses.join(",")}`)
    }
    const projection = await page.evaluate(async () => {
      const response = await fetch("/api/auth/session", { credentials: "same-origin", cache: "no-store" })
      return { status: response.status, body: await response.json() }
    })
    productAuthenticated = projection.status === 200 && projection.body?.authenticated === true
    if (!productAuthenticated) throw new Error("accepted invitation did not establish Product Session")
  } else {
    stage = "rejected-session"
    await page.getByRole("heading", { name: "已拒绝邀请", exact: true }).waitFor({ state: "visible", timeout: 15000 })
    const projection = await page.evaluate(async () => {
      const response = await fetch("/api/auth/session", { credentials: "same-origin", cache: "no-store" })
      return { status: response.status, body: await response.json() }
    })
    rejectedAnonymous = projection.status === 200 && projection.body?.authenticated === false
    if (!rejectedAnonymous) throw new Error("rejected invitation gained Product Session")
    stage = "iam-membership"
    membershipAbsent = await rejectedMembershipAbsent(input, context, target)
  }
  process.stderr.write("MILESTONE:decision\n")
  stage = "consumed-invitation"
  const consumed = await page.goto(target, { waitUntil: "domcontentloaded" })
  const consumedPending = consumed?.status() === 404 &&
    await page.getByRole("heading", { name: "邀请不可用", exact: true }).isVisible()
  if (!consumedPending) throw new Error("consumed invitation remained pending")
  process.stderr.write("MILESTONE:consumed\n")
  process.stdout.write(JSON.stringify({
    browser: "chromium", decision: input.decision, account: input.account, entry_form: true,
    registration_verified: registrationVerified, unverified_login_denied: unverifiedLoginDenied,
    verification_returned: verificationReturned,
    recipient_preview: true, legacy_intermediary_absent: true,
    decision_post_count: 1, consumed_pending: true,
    product_login_started: productLoginStarted, product_authenticated: productAuthenticated,
    rejected_anonymous: rejectedAnonymous, membership_absent: membershipAbsent,
    screenshot: input.screenshot,
  }) + "\n")
} catch {
  // Playwright errors contain URLs and form values. Only expose a controlled stage.
  process.stderr.write(`Chromium invitation failed at ${stage}\n`)
  process.exitCode = 1
} finally {
  await browser?.close()
}
