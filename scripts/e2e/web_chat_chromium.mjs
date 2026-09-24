#!/usr/bin/env node

import { createRequire } from "node:module"
import { readFileSync } from "node:fs"
import path from "node:path"
import process from "node:process"
import { pathToFileURL } from "node:url"

const fail = (message) => {
  process.stderr.write(`${message}\n`)
  process.exitCode = 1
}

const parseInput = () => {
  if (process.argv.length !== 2) throw new Error("expected stdin JSON input")
  const value = JSON.parse(readFileSync(0, "utf8"))
  const fields = ["web_origin", "web_host", "web_root", "screenshot", "headed", "hold_seconds", "email", "password", "tenant_id"]
  if (
    value === null ||
    typeof value !== "object" ||
    Array.isArray(value) ||
    Object.keys(value).sort().join(",") !== [...fields].sort().join(",") ||
    ![...fields.slice(0, 4), ...fields.slice(6)].every((field) => typeof value[field] === "string" && value[field] !== "") ||
    typeof value.headed !== "boolean" ||
    typeof value.hold_seconds !== "number" ||
    value.hold_seconds < 0
  ) {
    throw new Error("invalid Chromium milestone input")
  }
  const origin = new URL(value.web_origin)
  if (origin.origin !== value.web_origin || origin.protocol !== "https:" || origin.hostname !== value.web_host) {
    throw new Error("invalid Chromium Web origin")
  }
  return { ...value, origin }
}

let browser
try {
  const input = parseInput()
  const require = createRequire(pathToFileURL(path.join(input.web_root, "package.json")))
  const { chromium } = require("@playwright/test")
  browser = await chromium.launch({
    headless: !input.headed,
    args: [`--host-resolver-rules=MAP ${input.web_host} 127.0.0.1`, "--no-proxy-server"],
  })
  const context = await browser.newContext({ ignoreHTTPSErrors: true, locale: "en-US" })
  const page = await context.newPage()
  await page.addInitScript(() => window.localStorage.setItem("kokoro.locale", "en"))
  let csrfRequests = 0
  let signInRequests = 0
  const failedRequests = []
  const observedPaths = []
  const observedResponses = []
  const browserErrors = []
  page.on("request", (request) => {
    const pathname = new URL(request.url()).pathname
    observedPaths.push(pathname)
    if (pathname === "/api/auth/csrf") csrfRequests += 1
    if (pathname === "/api/auth/signin/kokoro-iam") signInRequests += 1
  })
  page.on("response", (response) => {
    const url = new URL(response.url())
    if (url.origin === input.web_origin) observedResponses.push(`${response.status()} ${url.pathname}`)
    if (url.origin === input.web_origin && response.status() >= 400) {
      failedRequests.push(`${response.status()} ${url.pathname}`)
    }
  })
  page.on("requestfailed", (request) => {
    const url = new URL(request.url())
    if (url.origin === input.web_origin) failedRequests.push(`failed ${url.pathname}`)
  })
  page.on("console", (message) => {
    if (message.type() === "error" && !message.text().includes("webpack-hmr")) {
      browserErrors.push(message.text().slice(0, 200))
    }
  })
  page.on("pageerror", (error) => browserErrors.push(error.message.slice(0, 300)))
  const entryUrl = `${input.web_origin}/login`
  const entry = await page.goto(entryUrl, { waitUntil: "domcontentloaded" })
  if (entry === null || entry.status() !== 200) {
    throw new Error(
      `IAM sign-in document was not HTTP 200; status=${entry?.status() ?? "none"}; ` +
      `path=${new URL(page.url()).pathname}; responses=${observedResponses.slice(-6).join("|") || "none"}`,
    )
  }
  try {
    // /login starts OIDC on the server; only the IAM interaction reaches the browser.
    await page.waitForURL(
      (url) => url.origin === input.web_origin && url.pathname === "/auth/sign-in" && url.search.length > 1,
      { waitUntil: "commit", timeout: 12000 },
    )
    if (csrfRequests !== 0 || signInRequests !== 0 || observedPaths.filter((path) => path === "/login").length !== 1) {
      throw new Error(`Expected direct server-owned OIDC start, observed csrf=${csrfRequests}, signin=${signInRequests}`)
    }
  } catch {
    const current = new URL(page.url())
    const headings = await page.locator("h1").allTextContents().catch(() => [])
    const inputs = await page.locator("input").evaluateAll((elements) =>
      elements.map((element) => `${element.getAttribute("name") ?? ""}:${element.getAttribute("type") ?? ""}`),
    ).catch(() => [])
    throw new Error(
      `IAM sign-in navigation did not complete; ` +
        `page=${current.origin}${current.pathname}; lang=${await page.locator("html").getAttribute("lang")}; ` +
        `csrf_requests=${csrfRequests}; signin_requests=${signInRequests}; paths=${observedPaths.slice(0, 5).join("|")}; ` +
        `responses=${observedResponses.slice(-8).join("|") || "none"}; ` +
        `headings=${headings.slice(0, 3).join("|") || "none"}; inputs=${inputs.slice(0, 5).join("|") || "none"}; ` +
        `failed=${failedRequests.slice(0, 5).join("|") || "none"}; errors=${browserErrors.slice(0, 5).join("|") || "none"}`,
    )
  }
  await page.getByRole("heading", { name: "Sign in", exact: true }).waitFor({ state: "visible" })
  const email = page.locator('input[name="email"][type="email"]')
  const password = page.locator('input[name="password"][type="password"]')
  await email.waitFor({ state: "visible" })
  await password.waitFor({ state: "visible" })
  if ((await email.inputValue()) !== "" || (await password.inputValue()) !== "") {
    throw new Error("IAM credential fields were not empty")
  }
  await page.screenshot({ path: input.screenshot, fullPage: true })
  await email.fill(input.email)
  await password.fill(input.password)
  await page.getByRole("button", { name: "Sign in", exact: true }).click()
  await page.getByRole("heading", { name: "Select tenant", exact: true }).waitFor({ state: "visible" })
  if (new URL(page.url()).pathname !== "/iam/interactions/select-tenant") {
    throw new Error("IAM tenant form path drift")
  }
  await page.locator('select[name="organization_id"]').selectOption(input.tenant_id)
  await page.getByRole("button", { name: "Continue", exact: true }).click()
  await page.getByRole("heading", { name: "Review requested access", exact: true }).waitFor({ state: "visible" })
  if (new URL(page.url()).pathname !== "/iam/interactions/consent") {
    throw new Error("IAM consent form path drift")
  }
  await page.getByRole("button", { name: "Agree and continue", exact: true }).click()
  await page.waitForURL(
    (url) => url.origin === input.web_origin && url.pathname === "/app",
    { waitUntil: "domcontentloaded", timeout: 12000 },
  )
  const projection = await page.evaluate(async () => {
    const response = await fetch("/api/auth/session", { credentials: "same-origin", cache: "no-store" })
    return { status: response.status, cacheControl: response.headers.get("cache-control"), body: await response.json() }
  })
  if (
    projection.status !== 200 ||
    !projection.cacheControl?.includes("no-store") ||
    projection.body?.authenticated !== true ||
    Object.keys(projection.body).sort().join(",") !== "authenticated,expires_at,subject" ||
    typeof projection.body.subject !== "string" ||
    projection.body.subject.length === 0 ||
    !Number.isInteger(projection.body.expires_at) ||
    projection.body.expires_at <= Date.now()
  ) {
    throw new Error("Browser Product Session projection invalid")
  }
  const productCookies = (await context.cookies(input.web_origin)).filter((cookie) => cookie.name === "kokoro_product_session")
  if (
    productCookies.length !== 1 ||
    productCookies[0].path !== "/" ||
    productCookies[0].httpOnly !== true ||
    productCookies[0].secure !== true ||
    productCookies[0].sameSite !== "Lax"
  ) {
    throw new Error("Browser Product Session cookie invalid")
  }
  const appScreenshot = path.join(path.dirname(input.screenshot), `app-${input.web_host}.png`)
  await page.screenshot({ path: appScreenshot, fullPage: true })
  if (input.hold_seconds > 0) await page.waitForTimeout(input.hold_seconds * 1000)
  process.stdout.write(
    JSON.stringify({
      browser: "chromium",
      entry_url: entryUrl,
      iam_page: `${input.web_origin}/auth/sign-in`,
      email_field: true,
      password_field: true,
      screenshot: input.screenshot,
      csrf_requests: csrfRequests,
      signin_requests: signInRequests,
      tenant_form: true,
      consent_form: true,
      app_page: true,
      product_session: true,
      app_screenshot: appScreenshot,
    }),
  )
  await context.close()
} catch (error) {
  fail(error instanceof Error ? error.message : "Chromium milestone failed")
} finally {
  await browser?.close().catch(() => undefined)
}
