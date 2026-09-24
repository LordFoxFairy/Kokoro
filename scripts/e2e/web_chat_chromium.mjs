#!/usr/bin/env node

import { createRequire } from "node:module"
import path from "node:path"
import process from "node:process"
import { pathToFileURL } from "node:url"

const fail = (message) => {
  process.stderr.write(`${message}\n`)
  process.exitCode = 1
}

const parseInput = () => {
  if (process.argv.length !== 3) throw new Error("expected one JSON input")
  const value = JSON.parse(process.argv[2])
  const fields = ["web_origin", "web_host", "web_root", "screenshot", "headed", "hold_seconds"]
  if (
    value === null ||
    typeof value !== "object" ||
    Array.isArray(value) ||
    Object.keys(value).sort().join(",") !== [...fields].sort().join(",") ||
    !fields.slice(0, 4).every((field) => typeof value[field] === "string" && value[field] !== "") ||
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
  if (entry === null || entry.status() !== 200) throw new Error("Web login entry was not HTTP 200")
  try {
    // /login owns the single automatic handoff. Request observers are attached
    // before navigation so a fast hydration cannot race a later waitForRequest.
    await page.waitForURL(
      (url) => url.origin === input.web_origin && url.pathname === "/auth/sign-in" && url.search.length > 1,
      { waitUntil: "commit", timeout: 12000 },
    )
    if (csrfRequests !== 1 || signInRequests !== 1) {
      throw new Error(`Expected one automatic OIDC handoff, observed csrf=${csrfRequests}, signin=${signInRequests}`)
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
    }),
  )
  await context.close()
} catch (error) {
  fail(error instanceof Error ? error.message : "Chromium milestone failed")
} finally {
  await browser?.close().catch(() => undefined)
}
