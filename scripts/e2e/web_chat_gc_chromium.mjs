#!/usr/bin/env node
/** Observe a genuine browser SSE 410 after the production owner GC runs. */

import { createHash, X509Certificate } from "node:crypto"
import { createRequire } from "node:module"
import { readFileSync } from "node:fs"
import path from "node:path"
import process from "node:process"
import { createInterface } from "node:readline"
import { pathToFileURL } from "node:url"

const assert = (condition, message) => { if (!condition) throw new Error(message) }
const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex")
const lines = createInterface({ input: process.stdin, crlfDelay: Infinity })[Symbol.asyncIterator]()
const protocol = (value) => process.stdout.write(`${JSON.stringify(value)}\n`)
async function command(timeoutMs) {
  let timer
  try {
    const next = await Promise.race([
      lines.next(),
      new Promise((_, reject) => { timer = setTimeout(() => reject(new Error("GC browser command deadline")), timeoutMs) }),
    ])
    assert(!next.done, "GC browser command absent")
    return JSON.parse(next.value)
  } finally { clearTimeout(timer) }
}
let browser
let page
let targetConversation = null
let targetFirstArtifact = null
let recoveryOldCursor = null
let recoveryNewCursor = null
let firstCardIndex = null
let secondCardIndex = null
let downloadDigestMatch = null
let downloadFilenameMatch = null
let downloadCompleted = null
const sseResponses = []
let gatedRequest = null
let releaseHeldRoute = null
let phase = "parse-input"
function parseInput(line) {
  let value
  try { value = JSON.parse(line) } catch { throw new Error("invalid input") }
  const fields = ["web_origin", "web_host", "web_root", "web_certificate", "screenshot", "owner_email", "owner_password", "first_sha256", "second_sha256", "timeout_ms"]
  if (!value || typeof value !== "object" || Array.isArray(value) ||
      Object.keys(value).sort().join(",") !== fields.sort().join(",") ||
      !fields.filter((field) => field !== "timeout_ms").every((field) => typeof value[field] === "string" && value[field] !== "") ||
      !Number.isInteger(value.timeout_ms) || value.timeout_ms < 20_000 || value.timeout_ms > 600_000 ||
      !/^[a-f0-9]{64}$/u.test(value.first_sha256) || !/^[a-f0-9]{64}$/u.test(value.second_sha256) ||
      !path.isAbsolute(value.web_root) || !path.isAbsolute(value.web_certificate) || !path.isAbsolute(value.screenshot) ||
      path.basename(value.web_certificate) !== "web.crt" || path.dirname(value.web_certificate) !== path.dirname(value.screenshot)) throw new Error("invalid input")
  let origin
  try { origin = new URL(value.web_origin) } catch { throw new Error("invalid input") }
  if (origin.origin !== value.web_origin || origin.protocol !== "https:" || origin.hostname !== value.web_host) throw new Error("invalid input")
  return value
}

try {
  const first = await lines.next()
  assert(!first.done, "input absent")
  const input = parseInput(first.value)
  phase = "certificate-pin"
  const certificate = new X509Certificate(readFileSync(input.web_certificate))
  assert(certificate.checkHost(input.web_host) === input.web_host, "certificate host drift")
  const pin = createHash("sha256").update(certificate.publicKey.export({ type: "spki", format: "der" })).digest("base64")
  phase = "launch-browser"
  const require = createRequire(pathToFileURL(path.join(input.web_root, "package.json")))
  const { chromium } = require("@playwright/test")
  browser = await chromium.launch({ headless: true, args: [
    `--host-resolver-rules=MAP ${input.web_host} 127.0.0.1`, "--no-proxy-server", `--ignore-certificate-errors-spki-list=${pin}`,
  ] })
  const context = await browser.newContext({ ignoreHTTPSErrors: true, locale: "en-US" })
  page = await context.newPage()
  await page.addInitScript(() => {
    window.localStorage.setItem("kokoro.locale", "en")
    window.__gcNetwork = { snapshots: [], events: [], probe: false }
    const originalFetch = window.fetch.bind(window)
    window.fetch = async (...args) => {
      const raw = args[0] instanceof Request ? args[0].url : String(args[0])
      const url = new URL(raw, location.href)
      const method = (args[1]?.method ?? (args[0] instanceof Request ? args[0].method : "GET")).toUpperCase()
      const target = url.origin === location.origin && /^\/api\/session\/sessions\/[^/]+$/u.test(url.pathname) && method === "GET"
      const stream = url.origin === location.origin && /^\/api\/session\/sessions\/[^/]+\/events$/u.test(url.pathname) && method === "GET"
      const headers = new Headers(args[1]?.headers ?? (args[0] instanceof Request ? args[0].headers : undefined))
      const lastEventId = stream ? headers.get("last-event-id") : null
      const response = await originalFetch(...args)
      if (target) {
        const record = { path: url.pathname, status: response.status, probe: window.__gcNetwork.probe,
          watermark: null, deliveries: [], activeRun: undefined }
        window.__gcNetwork.snapshots.push(record)
        if (response.status === 200) {
          try {
            const body = await response.clone().json()
            record.watermark = body?.event_watermark ?? null
            record.deliveries = Array.isArray(body?.deliveries) ? body.deliveries.map((item) => [item.conversation_id, item.artifact_id]) : []
            record.activeRun = body?.active_run
          } catch { /* Owner wire will fail the later evidence assertion. */ }
        }
      }
      if (stream) {
        const record = { path: url.pathname, status: response.status, lastEventId, code: null }
        window.__gcNetwork.events.push(record)
        if (response.status === 410) {
          try { record.code = (await response.clone().json())?.error?.code ?? null } catch { /* Real malformed 410 fails below. */ }
        }
      }
      return response
    }
  })
  async function login() {
    const callbacks = []
    page.on("response", (response) => {
      const url = new URL(response.url())
      if (url.origin === input.web_origin && url.pathname === "/api/auth/callback/kokoro-iam") callbacks.push(response.status())
    })
    const entry = await page.goto(`${input.web_origin}/login`, { waitUntil: "domcontentloaded", timeout: input.timeout_ms })
    assert(entry?.status() === 200 && new URL(page.url()).pathname === "/auth/sign-in", "real IAM form absent")
    await page.getByRole("heading", { name: "欢迎回来", exact: true }).waitFor({ state: "visible", timeout: input.timeout_ms })
    await page.locator('input[name="email"][type="email"]').fill(input.owner_email)
    await page.locator('input[name="password"][type="password"]').fill(input.owner_password)
    await page.getByRole("button", { name: "登录", exact: true }).click()
    await page.waitForURL((url) => url.pathname === "/iam/interactions/consent" ||
      (url.origin === input.web_origin && url.pathname === "/app"), { timeout: input.timeout_ms })
    if (new URL(page.url()).pathname === "/iam/interactions/consent") {
      await page.getByRole("heading", { name: "Review requested access", exact: true }).waitFor({ state: "visible", timeout: input.timeout_ms })
      await page.getByRole("button", { name: "Agree and continue", exact: true }).click()
    }
    await page.waitForURL((url) => url.origin === input.web_origin && url.pathname === "/app", { waitUntil: "domcontentloaded", timeout: input.timeout_ms })
    const projection = await page.evaluate(async () => {
      const response = await fetch("/api/auth/session", { credentials: "same-origin", cache: "no-store" })
      return { status: response.status, body: await response.json() }
    })
    const cookies = (await context.cookies(input.web_origin)).filter((cookie) => cookie.name === "kokoro_product_session")
    assert(projection.status === 200 && projection.body?.authenticated === true && typeof projection.body.subject === "string" &&
      callbacks.length === 1 && callbacks[0] === 303 && cookies.length === 1 && cookies[0].httpOnly === true &&
      cookies[0].secure === true && cookies[0].sameSite === "Lax" && cookies[0].path === "/", "real IAM Product Session invalid")
    return { subject: projection.body.subject, form_status: entry.status(), callback_status: callbacks[0],
      session_status: projection.status, product_cookie: "HttpOnly+Secure+Lax" }
  }
  phase = "owner-login"
  const owner = await login()
  const subject = owner.subject
  page.on("response", (response) => {
    const url = new URL(response.url())
    if (url.origin === input.web_origin && /^\/api\/session\/sessions\/[^/]+\/events$/u.test(url.pathname)) {
      sseResponses.push({ path: url.pathname, status: response.status(),
        lastEventId: response.request().headers()["last-event-id"] ?? null,
        isGatedOriginal: response.request() === gatedRequest?.request })
    }
  })
  phase = "first-product-post"
  const composer = page.locator('[data-slot="composer-input"]')
  await composer.waitFor({ state: "visible", timeout: input.timeout_ms })
  const receiptPromise = page.waitForResponse((response) => {
    const url = new URL(response.url())
    return url.origin === input.web_origin && /^\/api\/session\/sessions\/[^/]+\/messages$/u.test(url.pathname) && response.request().method() === "POST"
  }, { timeout: input.timeout_ms })
  await composer.fill("Create first GC-window Agent Artifact.")
  await page.locator('[data-composer-action="send"]').click()
  const firstReceiptResponse = await receiptPromise
  assert(firstReceiptResponse.status() === 202, "first Product message not accepted")
  const conversation = decodeURIComponent(new URL(firstReceiptResponse.url()).pathname.split("/")[4])
  targetConversation = conversation
  const firstReceipt = await firstReceiptResponse.json()
  assert(/^conv_[A-Za-z0-9_-]+$/u.test(conversation) && typeof firstReceipt?.run_id === "string", "first Product receipt invalid")
  const eventPath = `/api/session/sessions/${encodeURIComponent(conversation)}/events`
  const snapshotPath = `/api/session/sessions/${encodeURIComponent(conversation)}`
  phase = "first-sse-200"
  if (!sseResponses.some((item) => item.path === eventPath && item.status === 200)) {
    await page.waitForResponse((response) => new URL(response.url()).origin === input.web_origin &&
      new URL(response.url()).pathname === eventPath && response.status() === 200, { timeout: input.timeout_ms })
  }
  protocol({ milestone: "first_subscribed", conversation_id: conversation, run_id: firstReceipt.run_id,
    post_status: 202, sse_status: 200 })
  phase = "first-agent-delivery"
  const deliveredFirst = await command(Math.min(30_000, input.timeout_ms / 3))
  assert(deliveredFirst?.command === "first_delivered" && /^artifact:[a-f0-9]{64}$/u.test(deliveredFirst.artifact_id), "first Agent delivery identity invalid")
  targetFirstArtifact = deliveredFirst.artifact_id
  const cards = page.getByRole("button", { name: "Open delivery Delivered work", exact: true })
  await cards.first().waitFor({ state: "visible", timeout: input.timeout_ms })
  assert(await cards.count() === 1, "first browser card count invalid")
  phase = "first-owner-snapshot"
  await page.waitForFunction(async ({ target, artifactId }) => {
    window.__gcNetwork.probe = true
    try {
      const response = await fetch(target, { credentials: "same-origin", cache: "no-store" })
      const body = await response.json()
      return response.status === 200 && body?.active_run == null && body?.deliveries?.length === 1 &&
        body.deliveries[0]?.artifact_id === artifactId && typeof body.event_watermark === "string" && body.event_watermark.length > 0
    } finally { window.__gcNetwork.probe = false }
  }, { target: snapshotPath, artifactId: deliveredFirst.artifact_id }, { timeout: input.timeout_ms })
  const old = await page.evaluate((target) => window.__gcNetwork.snapshots.filter((item) => item.path === target && item.status === 200 &&
    item.deliveries.length === 1 && item.activeRun == null).at(-1)?.watermark ?? null, snapshotPath)
  assert(typeof old === "string" && old, "first snapshot watermark absent")
  recoveryOldCursor = old
  phase = "gate-original-browser-sse"
  let gateObserved
  const gateSeen = new Promise((resolve) => { gateObserved = resolve })
  let gateRelease
  const gateReleased = new Promise((resolve) => { gateRelease = resolve })
  releaseHeldRoute = gateRelease
  let armed = true
  await page.route((url) => url.origin === input.web_origin && url.pathname === eventPath, async (route) => {
    const request = route.request()
    const lastEventId = request.headers()["last-event-id"] ?? null
    if (armed && request.method() === "GET" && lastEventId === old) {
      armed = false
      gatedRequest = { lastEventId,
        beforeNetwork: !sseResponses.some((item) => item.path === eventPath && item.lastEventId === old), request }
      gateObserved()
      await gateReleased
    }
    await route.continue()
  })
  await page.reload({ waitUntil: "domcontentloaded", timeout: input.timeout_ms })
  let gateTimer
  try {
    await Promise.race([gateSeen, new Promise((_, reject) => {
      gateTimer = setTimeout(() => reject(new Error("real original SSE gate absent")), input.timeout_ms)
    })])
  } finally { clearTimeout(gateTimer) }
  const hydration = await page.evaluate((target) => window.__gcNetwork.snapshots.find((item) =>
    item.path === target.path && item.status === 200 && item.probe === false && item.watermark === target.old),
  { path: snapshotPath, old })
  // The page's own hydration snapshot, rather than the probe, must precede the held SSE.
  assert(hydration?.deliveries?.length === 1 && hydration.deliveries[0][1] === deliveredFirst.artifact_id,
    "refresh did not hydrate first owner snapshot before gated SSE")
  assert(await cards.count() === 1, "first hydrated card absent")
  protocol({ milestone: "first_gated", conversation_id: conversation, first_run_id: firstReceipt.run_id,
    first_artifact_id: deliveredFirst.artifact_id, first_delivery_count: 1, first_card_count: 1,
    first_snapshot_status: hydration.status, first_sse_status: 200, old_watermark: old,
    gated_last_event_id: gatedRequest?.lastEventId, gated_before_network: gatedRequest?.beforeNetwork === true,
    owner_subject: subject })
  phase = "second-same-browser-product-post"
  const secondPost = await page.evaluate(async (target) => {
    const response = await fetch(`${target}/messages`, {
      method: "POST", credentials: "same-origin", cache: "no-store",
      headers: { "content-type": "application/json", "idempotency-key": crypto.randomUUID() },
      body: JSON.stringify({ content: "Create second GC-window Agent Artifact." }),
    })
    return { status: response.status, body: await response.json() }
  }, snapshotPath)
  assert(secondPost.status === 202 && typeof secondPost.body?.run_id === "string" &&
    secondPost.body.run_id !== firstReceipt.run_id, "second Product run not accepted")
  protocol({ milestone: "second_submitted", conversation_id: conversation, post_status: secondPost.status,
    run_id: secondPost.body.run_id })
  phase = "second-agent-delivery"
  const deliveredSecond = await command(Math.min(30_000, input.timeout_ms / 3))
  assert(deliveredSecond?.command === "second_delivered" && /^artifact:[a-f0-9]{64}$/u.test(deliveredSecond.artifact_id) &&
    deliveredSecond.artifact_id !== deliveredFirst.artifact_id, "second Agent delivery identity invalid")
  phase = "second-owner-projection"
  await page.waitForFunction(async ({ target, firstId, secondId, conversationId }) => {
    window.__gcNetwork.probe = true
    try {
      const response = await fetch(target, { credentials: "same-origin", cache: "no-store" })
      const body = await response.json()
      const keys = body?.deliveries?.map((item) => JSON.stringify([item.conversation_id, item.artifact_id])) ?? []
      return response.status === 200 && body.active_run == null && keys.length === 2 &&
        new Set(keys).size === 2 && keys.includes(JSON.stringify([conversationId, firstId])) &&
        keys.includes(JSON.stringify([conversationId, secondId]))
    } finally { window.__gcNetwork.probe = false }
  }, { target: snapshotPath, firstId: deliveredFirst.artifact_id, secondId: deliveredSecond.artifact_id,
    conversationId: conversation }, { timeout: input.timeout_ms })
  protocol({ milestone: "second_projected", second_artifact_id: deliveredSecond.artifact_id, snapshot_delivery_count: 2 })
  phase = "production-owner-gc"
  const gc = await command(Math.min(30_000, input.timeout_ms / 3))
  assert(gc?.command === "gc_complete" && typeof gc.new_watermark === "string" && gc.new_watermark !== old,
    "owner GC completion missing")
  recoveryNewCursor = gc.new_watermark
  protocol({ milestone: "gc_ack", original_route_held: gatedRequest !== null &&
    !sseResponses.some((item) => item.isGatedOriginal), old_cursor_gated: gatedRequest?.lastEventId === old })
  phase = "release-original-network-request"
  gateRelease()
  releaseHeldRoute = null
  const recovered = await page.waitForFunction(({ path, oldCursor, newCursor }) => {
    const events = window.__gcNetwork.events.filter((item) => item.path === path)
    const expired = events.find((item) => item.lastEventId === oldCursor && item.status === 410 && item.code === "event_cursor_expired")
    const snapshots = window.__gcNetwork.snapshots.filter((item) => item.path === path.slice(0, -7) &&
      !item.probe && item.status === 200 && item.watermark === newCursor && item.deliveries.length === 2)
    const resumed = events.find((item) => item.lastEventId === newCursor && item.status === 200)
    return expired && snapshots.length > 0 && resumed ? { expired, snapshot: snapshots[0], resumed } : false
  }, { path: eventPath, oldCursor: old, newCursor: gc.new_watermark }, { timeout: Math.min(30_000, input.timeout_ms / 3) })
  const recovery = await recovered.jsonValue()
  assert(sseResponses.some((item) => item.isGatedOriginal && item.status === 410 && item.lastEventId === old),
    "original gated browser request did not receive owner 410")
  protocol({ milestone: "recovered", expired_status: recovery.expired.status,
    expired_code: recovery.expired.code, snapshot_delivery_count: recovery.snapshot.deliveries.length,
    resume_status: recovery.resumed.status, old_cursor_matched: recovery.expired.lastEventId === old,
    new_watermark_matched: recovery.snapshot.watermark === gc.new_watermark &&
      recovery.resumed.lastEventId === gc.new_watermark })
  phase = "two-unique-cards-and-canvas"
  await cards.nth(1).waitFor({ state: "visible", timeout: Math.min(25_000, input.timeout_ms / 3) })
  assert(await cards.count() === 2, "Chat did not show two unique Delivery cards")
  const keys = recovery.snapshot.deliveries
  const firstIndex = keys.findIndex(([conversationId, artifactId]) => conversationId === conversation && artifactId === deliveredFirst.artifact_id)
  const secondIndex = keys.findIndex(([conversationId, artifactId]) => conversationId === conversation && artifactId === deliveredSecond.artifact_id)
  firstCardIndex = firstIndex
  secondCardIndex = secondIndex
  assert(keys.length === 2 && new Set(keys.map((key) => JSON.stringify(key))).size === 2 &&
    firstIndex >= 0 && secondIndex >= 0 && firstIndex !== secondIndex, "two binary Delivery identities absent")
  protocol({ milestone: "cards_ready", dom_card_count: await cards.count(),
    first_key_count: keys.filter(([conversationId, artifactId]) => conversationId === conversation && artifactId === deliveredFirst.artifact_id).length,
    second_key_count: keys.filter(([conversationId, artifactId]) => conversationId === conversation && artifactId === deliveredSecond.artifact_id).length })
  const canvas = page.getByRole("complementary", { name: "canvas details Delivered work", exact: true })
  async function downloadCard(label, index, expectedDigest) {
    downloadDigestMatch = null
    downloadFilenameMatch = null
    downloadCompleted = null
    const canvasDeadline = Date.now() + Math.min(25_000, input.timeout_ms / 3)
    const remaining = () => Math.max(1_000, canvasDeadline - Date.now())
    const bounded = async (operation) => {
      let timer
      try {
        return await Promise.race([operation(), new Promise((_, reject) => {
          timer = setTimeout(() => reject(new Error("Canvas deadline")), remaining())
        })])
      } finally { clearTimeout(timer) }
    }
    phase = `${label}-card-click`
    await cards.nth(index).click({ timeout: remaining() })
    phase = `${label}-canvas-visible`
    await canvas.waitFor({ state: "visible", timeout: remaining() })
    phase = `${label}-download-event`
    const downloadPromise = page.waitForEvent("download", { timeout: remaining() })
    await canvas.getByRole("button", { name: "Download", exact: true }).click({ timeout: remaining() })
    const download = await downloadPromise
    phase = `${label}-download-bytes`
    const digest = sha256(readFileSync(await bounded(() => download.path())))
    downloadFilenameMatch = download.suggestedFilename() === "delivered-work.txt"
    downloadCompleted = await bounded(() => download.failure()) === null
    downloadDigestMatch = digest === expectedDigest
    assert(downloadFilenameMatch && downloadCompleted && downloadDigestMatch, "Canvas original bytes drift")
    await bounded(() => download.delete())
    phase = `${label}-canvas-close`
    await canvas.getByRole("button", { name: "Close preview", exact: true }).click({ timeout: remaining() })
    await canvas.waitFor({ state: "hidden", timeout: remaining() })
    // Hidden occurs at the start of the exit transition; wait until the
    // deferred onClose has actually unmounted this controlled Canvas.
    await page.locator('[data-slot="context-panel"]').waitFor({ state: "detached", timeout: remaining() })
    return digest
  }
  const firstCanvasDigest = await downloadCard("first", firstIndex, input.first_sha256)
  protocol({ milestone: "first_canvas_done", first_canvas_sha256: firstCanvasDigest })
  const canvasDigest = await downloadCard("second", secondIndex, input.second_sha256)
  protocol({ milestone: "second_canvas_done", second_canvas_sha256: canvasDigest })
  phase = "screenshot"
  await page.screenshot({ path: input.screenshot, fullPage: true, timeout: Math.min(20_000, input.timeout_ms / 3) })
  protocol({ milestone: "complete", gated_original_released: true,
    owner_subject: subject, login: { owner },
    expired_status: recovery.expired.status, expired_code: recovery.expired.code,
    expired_last_event_id: recovery.expired.lastEventId,
    snapshot_after_410_status: recovery.snapshot.status,
    snapshot_after_410_count: recovery.snapshot.deliveries.length,
    snapshot_after_410_watermark: recovery.snapshot.watermark,
    resume_last_event_id: recovery.resumed.lastEventId, resume_status: recovery.resumed.status,
    first_card_count: keys.filter(([conversationId, artifactId]) => conversationId === conversation && artifactId === deliveredFirst.artifact_id).length,
    second_card_count: keys.filter(([conversationId, artifactId]) => conversationId === conversation && artifactId === deliveredSecond.artifact_id).length,
    first_artifact_id: deliveredFirst.artifact_id, second_artifact_id: deliveredSecond.artifact_id,
    first_canvas_sha256: firstCanvasDigest, canvas_sha256: canvasDigest, screenshot: input.screenshot })
  await context.close()
} catch {
  releaseHeldRoute?.()
  let diagnostic = null
  if (page && targetConversation && targetFirstArtifact) {
    try {
      let diagnosticTimer
      try {
        diagnostic = await Promise.race([page.evaluate(({ conversationId, artifactId, oldCursor, newCursor, original410 }) => {
        const snapshotPath = `/api/session/sessions/${encodeURIComponent(conversationId)}`
        const eventPath = `${snapshotPath}/events`
        const snapshots = (window.__gcNetwork?.snapshots ?? []).filter((item) => item.path === snapshotPath).slice(-5)
        const events = (window.__gcNetwork?.events ?? []).filter((item) => item.path === eventPath)
        const oldAttempts = events.filter((item) => item.lastEventId === oldCursor)
        const newAttempts = events.filter((item) => item.lastEventId === newCursor)
        const newSnapshots = snapshots.filter((item) => item.status === 200 && item.watermark === newCursor)
        const canvas = document.querySelector('[aria-label="canvas details Delivered work"]')
        const contextPanel = document.querySelector('[data-slot="context-panel"]')
        const cardButtons = [...document.querySelectorAll('button[data-canvas-opener="true"][aria-label="Open delivery Delivered work"]')]
        return {
          snapshot_count: snapshots.length,
          snapshots: snapshots.map((item) => ({ status: item.status, delivery_count: item.deliveries.length,
            artifact_match: item.deliveries.some(([conversation, artifact]) => conversation === conversationId && artifact === artifactId),
            active_run_kind: item.activeRun === null ? "null" : item.activeRun === undefined ? "absent" : typeof item.activeRun,
            watermark_present: typeof item.watermark === "string" && item.watermark.length > 0, probe: item.probe })),
          sse_200_count: events.filter((item) => item.status === 200).length,
          card_count: document.querySelectorAll('button[data-canvas-opener="true"][aria-label="Open delivery Delivered work"]').length,
          original_410_response: original410,
          old_fetch_410: oldAttempts.some((item) => item.status === 410),
          old_fetch_code_match: oldAttempts.some((item) => item.status === 410 && item.code === "event_cursor_expired"),
          old_cursor_200: oldAttempts.some((item) => item.status === 200),
          new_snapshot_200: newSnapshots.length > 0,
          new_snapshot_two_deliveries: newSnapshots.some((item) => item.deliveries.length === 2),
          new_sse_200: newAttempts.some((item) => item.status === 200),
          canvas_visible: canvas !== null && canvas.getClientRects().length > 0,
          canvas_heading_match: canvas?.querySelector('h1,h2,h3')?.textContent?.trim() === "Delivered work",
          context_panel_count: document.querySelectorAll('[data-slot="context-panel"]').length,
          context_panel_state: contextPanel?.getAttribute('data-state') ?? "absent",
          card_visible_count: cardButtons.filter((item) => item.getClientRects().length > 0).length,
        }
        }, { conversationId: targetConversation, artifactId: targetFirstArtifact,
          oldCursor: recoveryOldCursor, newCursor: recoveryNewCursor,
          original410: sseResponses.some((item) => item.isGatedOriginal && item.status === 410) }),
        new Promise((resolve) => { diagnosticTimer = setTimeout(() => resolve(null), 2_000) })])
      } finally { clearTimeout(diagnosticTimer) }
      if (diagnostic !== null) {
        diagnostic.first_card_index = firstCardIndex
        diagnostic.second_card_index = secondCardIndex
        diagnostic.download_digest_match = downloadDigestMatch
        diagnostic.download_filename_match = downloadFilenameMatch
        diagnostic.download_completed = downloadCompleted
      }
    } catch { /* Only whitelisted bounded counters are diagnostic. */ }
  }
  protocol({ milestone: "failed", phase, diagnostic })
  process.stderr.write(`FAILURE_PHASE:${phase}\n`)
  process.exitCode = 1
} finally {
  if (browser) await browser.close()
  lines.return?.()
}
