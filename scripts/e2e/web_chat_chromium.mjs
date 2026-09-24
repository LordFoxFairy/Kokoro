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
  const fields = ["web_origin", "web_host", "web_root", "screenshot", "headed", "hold_seconds", "email", "password", "tenant_id", "chat_content", "expected_reply", "chat_timeout_ms", "fail_after_chat_receipt"]
  if (
    value === null ||
    typeof value !== "object" ||
    Array.isArray(value) ||
    Object.keys(value).sort().join(",") !== [...fields].sort().join(",") ||
    ![...fields.slice(0, 4), ...fields.slice(6, 11)].every((field) => typeof value[field] === "string" && value[field] !== "") ||
    typeof value.headed !== "boolean" ||
    typeof value.fail_after_chat_receipt !== "boolean" ||
    typeof value.hold_seconds !== "number" ||
    value.hold_seconds < 0 ||
    !Number.isInteger(value.chat_timeout_ms) ||
    value.chat_timeout_ms < 20_000 ||
    value.chat_timeout_ms > 600_000
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
  const observedAguiResponses = []
  const browserErrors = []
  const sseAttempts = []
  const pendingSse = new Map()
  page.on("request", (request) => {
    const pathname = new URL(request.url()).pathname
    observedPaths.push(pathname)
    if (pathname.endsWith("/events")) {
      const attempt = { startedAt: Date.now(), status: null, headersMs: null, endedMs: null, outcome: "open" }
      sseAttempts.push(attempt)
      pendingSse.set(request, attempt)
    }
    if (pathname === "/api/auth/csrf") csrfRequests += 1
    if (pathname === "/api/auth/signin/kokoro-iam") signInRequests += 1
  })
  page.on("response", (response) => {
    const url = new URL(response.url())
    if (url.origin === input.web_origin) observedResponses.push(`${response.status()} ${url.pathname}`)
    if (url.origin === input.web_origin && url.pathname.endsWith("/events")) {
      observedAguiResponses.push({ status: response.status(), pathname: url.pathname })
      const attempt = pendingSse.get(response.request())
      if (attempt) {
        attempt.status = response.status()
        attempt.headersMs = Date.now() - attempt.startedAt
      }
    }
    if (url.origin === input.web_origin && response.status() >= 400) {
      failedRequests.push(`${response.status()} ${url.pathname}`)
    }
  })
  page.on("requestfailed", (request) => {
    const url = new URL(request.url())
    if (url.origin === input.web_origin) failedRequests.push(`failed ${url.pathname}`)
    const attempt = pendingSse.get(request)
    if (attempt) {
      attempt.endedMs = Date.now() - attempt.startedAt
      attempt.outcome = "failed"
      pendingSse.delete(request)
    }
  })
  page.on("requestfinished", (request) => {
    const attempt = pendingSse.get(request)
    if (attempt) {
      attempt.endedMs = Date.now() - attempt.startedAt
      attempt.outcome = "finished"
      pendingSse.delete(request)
    }
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
  process.stderr.write("MILESTONE:iam\n")
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
  process.stderr.write("MILESTONE:app\n")
  const appScreenshot = path.join(path.dirname(input.screenshot), `app-${input.web_host}.png`)
  const composer = page.locator('[data-slot="composer-input"]')
  const send = page.locator('[data-composer-action="send"]')
  await composer.waitFor({ state: "visible", timeout: input.chat_timeout_ms })
  const receiptPromise = page.waitForResponse((response) => {
    const url = new URL(response.url())
    return url.origin === input.web_origin &&
      /^\/api\/session\/sessions\/[^/]+\/messages$/u.test(url.pathname) &&
      response.request().method() === "POST" && response.status() === 202
  }, { timeout: input.chat_timeout_ms })
  await composer.fill(input.chat_content)
  await send.click()
  const receiptResponse = await receiptPromise
  const conversationId = decodeURIComponent(new URL(receiptResponse.url()).pathname.split("/")[4])
  const receipt = await receiptResponse.json()
  if (
    !conversationId.startsWith("conv_") ||
    typeof receipt?.run_id !== "string" || !receipt.run_id ||
    typeof receipt?.user_message_id !== "string" ||
    typeof receipt?.assistant_message_id !== "string"
  ) {
    throw new Error("Browser DOM submit returned an invalid 202 receipt")
  }
  process.stderr.write("MILESTONE:receipt\n")
  if (input.fail_after_chat_receipt) {
    throw new Error("Injected browser failure after committed 202 receipt")
  }
  const snapshotPath = `/api/session/sessions/${encodeURIComponent(conversationId)}`
  try {
    await page.waitForFunction(
      ({ content, reply }) => {
        const users = [...document.querySelectorAll('[data-slot="user-message-body"]')]
        const assistants = [...document.querySelectorAll('[data-slot="markdown-message"]')]
        return users.filter((element) => element.textContent === content).length === 1 &&
          assistants.some((element) => element.textContent?.includes(reply))
      },
      { content: input.chat_content, reply: input.expected_reply },
      { timeout: input.chat_timeout_ms },
    )
  } catch {
    const owner = await page.evaluate(async (target) => {
      const response = await fetch(target, { credentials: "same-origin", cache: "no-store" })
      const body = await response.json().catch(() => ({}))
      return {
        snapshot_status: response.status,
        messages: Array.isArray(body.messages) ? body.messages.map((message) => ({ role: message.role, status: message.status, length: message.content?.length ?? null })) : [],
        has_watermark: typeof body.event_watermark === "string" && body.event_watermark.length > 0,
      }
    }, snapshotPath).catch(() => ({ snapshot_status: null, messages: [], has_watermark: false }))
    const dom = await page.evaluate(() => ({
      dom_users: document.querySelectorAll('[data-slot="user-message-body"]').length,
      dom_assistants: document.querySelectorAll('[data-slot="markdown-message"]').length,
      web_view: document.querySelector('[data-web-view]')?.getAttribute("data-web-view") ?? null,
      visible_alerts: [...document.querySelectorAll('[role="alert"]')]
        .filter((element) => element.getClientRects().length > 0)
        .map((element) => element.textContent?.trim().slice(0, 150) ?? "")
        .slice(0, 3),
    })).catch(() => ({ dom_users: -1, dom_assistants: -1, web_view: null, visible_alerts: [] }))
    const failureScreenshot = path.join(path.dirname(input.screenshot), `chat-timeout-${input.web_host}.png`)
    await page.screenshot({ path: failureScreenshot, fullPage: true }).catch(() => undefined)
    const sse_attempts = sseAttempts.map((attempt) => ({
      status: attempt.status,
      headers_ms: attempt.headersMs,
      elapsed_ms: attempt.endedMs ?? Date.now() - attempt.startedAt,
      outcome: attempt.outcome,
    }))
    throw new Error(`Browser assistant DOM did not converge; path=${new URL(page.url()).pathname}; ${JSON.stringify({ ...owner, ...dom, sse_attempts, browser_error_count: browserErrors.length, failed_paths: failedRequests.slice(-5), screenshot: failureScreenshot })}`)
  }
  process.stderr.write("MILESTONE:assistant\n")
  if (observedAguiResponses.filter((response) => response.status === 200 && response.pathname === `/api/session/sessions/${encodeURIComponent(conversationId)}/events`).length < 2) {
    throw new Error(`Browser app did not reconnect AG-UI SSE before assistant DOM; observed=${JSON.stringify(observedAguiResponses)}`)
  }
  const snapshot = await page.evaluate(async (target) => {
    const response = await fetch(target, { credentials: "same-origin", cache: "no-store" })
    return { status: response.status, body: await response.json() }
  }, snapshotPath)
  const messages = snapshot.body?.messages
  const users = Array.isArray(messages) ? messages.filter((message) => message.role === "user") : []
  const assistants = Array.isArray(messages) ? messages.filter((message) => message.role === "assistant") : []
  if (
    snapshot.status !== 200 || users.length !== 1 || assistants.length !== 1 ||
    users[0].content !== input.chat_content ||
    assistants[0].content !== input.expected_reply || assistants[0].status !== "completed" ||
    typeof snapshot.body.event_watermark !== "string" || !snapshot.body.event_watermark
  ) {
    throw new Error("Browser owner snapshot was not one durable completed turn")
  }
  const replay = await page.evaluate(async ({ target, timeoutMs }) => {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), timeoutMs)
    const frames = []
    try {
      const response = await fetch(`${target}/events`, {
        credentials: "same-origin", cache: "no-store",
        headers: { accept: "text/event-stream" }, signal: controller.signal,
      })
      if (response.status !== 200 || !response.headers.get("content-type")?.startsWith("text/event-stream") || !response.body) {
        return { status: response.status, frames: [] }
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""
      while (!controller.signal.aborted && frames.length < 32) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        let split = buffer.search(/\r?\n\r?\n/u)
        while (split >= 0) {
          const block = buffer.slice(0, split)
          buffer = buffer.slice(split).replace(/^\r?\n\r?\n/u, "")
          const id = /^id: ?(.+)$/mu.exec(block)?.[1]
          const data = /^data: ?(.+)$/mu.exec(block)?.[1]
          if (id && data) {
            const event = JSON.parse(data)
            frames.push({ id, type: event.type })
          }
          split = buffer.search(/\r?\n\r?\n/u)
        }
        if (frames.some((frame) => frame.type === "RUN_FINISHED")) break
      }
      await reader.cancel().catch(() => undefined)
      return { status: response.status, frames }
    } finally {
      clearTimeout(timeout)
      controller.abort()
    }
  }, { target: snapshotPath, timeoutMs: input.chat_timeout_ms })
  const frameTypes = replay.frames.map((frame) => frame.type)
  const expectedTypes = ["RUN_STARTED", "TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END", "RUN_FINISHED"]
  if (
    replay.status !== 200 || JSON.stringify(frameTypes) !== JSON.stringify(expectedTypes) ||
    replay.frames.at(-1)?.id !== snapshot.body.event_watermark ||
    new Set(replay.frames.map((frame) => frame.id)).size !== replay.frames.length
  ) {
    throw new Error(`Browser AG-UI replay drift: ${JSON.stringify(replay)}`)
  }
  process.stderr.write("MILESTONE:replay\n")
  await page.reload({ waitUntil: "domcontentloaded" })
  await page.waitForFunction(
    ({ content, reply }) => {
      const users = [...document.querySelectorAll('[data-slot="user-message-body"]')]
      const assistants = [...document.querySelectorAll('[data-slot="markdown-message"]')]
      return users.filter((element) => element.textContent === content).length === 1 &&
        assistants.filter((element) => element.textContent?.includes(reply)).length === 1
    },
    { content: input.chat_content, reply: input.expected_reply },
    { timeout: input.chat_timeout_ms },
  )
  const reloadUserCount = await page.locator('[data-slot="user-message-body"]').count()
  const reloadAssistantCount = await page.locator('[data-slot="markdown-message"]').count()
  process.stderr.write("MILESTONE:reload\n")
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
      conversation_id: conversationId,
      run_id: receipt.run_id,
      message_post_status: receiptResponse.status(),
      agui_first_status: 200,
      agui_frame_types: frameTypes,
      agui_frame_ids: replay.frames.map((frame) => frame.id),
      event_watermark: snapshot.body.event_watermark,
      reload_user_count: reloadUserCount,
      reload_assistant_count: reloadAssistantCount,
      reload_reply_visible: true,
    }),
  )
  await context.close()
} catch (error) {
  fail(error instanceof Error ? error.message : "Chromium milestone failed")
} finally {
  await browser?.close().catch(() => undefined)
}
