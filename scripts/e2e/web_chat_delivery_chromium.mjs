#!/usr/bin/env node
/** Browser-owned POST202/SSE200 handshake before real Agent delivery. */

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
async function boundedLine(timeoutMs) {
  let timer
  try {
    return await Promise.race([
      lines.next(),
      new Promise((_, reject) => { timer = setTimeout(() => reject(new Error("delivery handshake timeout")), timeoutMs) }),
    ])
  } finally { clearTimeout(timer) }
}
let browser
let page
let targetConversation = null
let targetEventPath = null
let targetArtifactId = null
let phase = "parse-input"

function parseInput(line) {
  let value
  try { value = JSON.parse(line) } catch { throw new Error("invalid input") }
  const fields = ["web_origin", "web_host", "web_root", "web_certificate", "screenshot", "owner_email", "owner_password", "member_email", "member_password", "content_sha256", "timeout_ms"]
  if (!value || typeof value !== "object" || Array.isArray(value) ||
      Object.keys(value).sort().join(",") !== fields.sort().join(",") ||
      !fields.filter((field) => field !== "timeout_ms").every((field) => typeof value[field] === "string" && value[field] !== "") ||
      !Number.isInteger(value.timeout_ms) || value.timeout_ms < 20_000 || value.timeout_ms > 600_000 ||
      !/^[a-f0-9]{64}$/u.test(value.content_sha256) ||
      !path.isAbsolute(value.web_root) || !path.isAbsolute(value.screenshot) ||
      !path.isAbsolute(value.web_certificate) || path.basename(value.web_certificate) !== "web.crt" ||
      path.dirname(value.web_certificate) !== path.dirname(value.screenshot)) throw new Error("invalid input")
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
  await page.addInitScript((terminalBarrierMs) => {
    window.localStorage.setItem("kokoro.locale", "en")
    // Clone only the actual browser AG-UI fetch. The UI retains the original
    // response; this observer cannot synthesize a Delivery from a snapshot.
    window.__liveDeliveryFrames = []
    window.__aguiObservedFrames = []
    window.__aguiAttempts = []
    window.__snapshotGets = []
    window.__deliveryAudit = null
    const originalFetch = window.fetch.bind(window)
    window.fetch = async (...args) => {
      const raw = args[0] instanceof Request ? args[0].url : String(args[0])
      const url = new URL(raw, location.href)
      const method = (args[1]?.method ?? (args[0] instanceof Request ? args[0].method : "GET")).toUpperCase()
      const snapshot = url.origin === location.origin && /^\/api\/session\/sessions\/[^/]+$/u.test(url.pathname) && method === "GET"
      const stream = url.origin === location.origin && /^\/api\/session\/sessions\/[^/]+\/events$/u.test(url.pathname) && method === "GET"
      const snapshotGet = snapshot ? { id: window.__snapshotGets.length + 1, path: url.pathname, ended: false } : null
      if (snapshotGet) window.__snapshotGets.push(snapshotGet)
      const headers = new Headers(args[1]?.headers ?? (args[0] instanceof Request ? args[0].headers : undefined))
      const attempt = stream ? { id: window.__aguiAttempts.length + 1, path: url.pathname,
        lastEventId: headers.get("last-event-id"), responseStatus: null, ended: false,
        endedReason: null, frameCount: 0, parseErrors: 0 } : null
      if (attempt) window.__aguiAttempts.push(attempt)
      let response
      try { response = await originalFetch(...args) }
      catch (error) {
        if (snapshotGet) snapshotGet.ended = true
        if (attempt) { attempt.ended = true; attempt.endedReason = "network-error" }
        throw error
      }
      if (snapshotGet) snapshotGet.ended = true
      if (attempt) attempt.responseStatus = response.status
      if (attempt && response.status === 200 && response.body) {
        const reader = response.clone().body.getReader()
        void (async () => {
          let buffered = ""
          const decoder = new TextDecoder()
          try {
            for (;;) {
              const { done, value } = await reader.read()
              if (done) { attempt.endedReason = "complete"; break }
              buffered += decoder.decode(value, { stream: true })
              for (;;) {
                const boundary = /\r?\n\r?\n/u.exec(buffered)
                if (!boundary) break
                const frame = buffered.slice(0, boundary.index)
                buffered = buffered.slice(boundary.index + boundary[0].length)
                const data = frame.split(/\r?\n/u).filter((line) => line.startsWith("data: ")).map((line) => line.slice(6)).join("\n")
                if (!data) continue
                let event
                try { event = JSON.parse(data) }
                catch { attempt.parseErrors += 1; continue }
                attempt.frameCount += 1
                if (window.__aguiObservedFrames.length < 32) {
                  window.__aguiObservedFrames.push({ attemptId: attempt.id, type: String(event?.type ?? "unknown").slice(0, 40),
                    name: String(event?.name ?? "").slice(0, 60), openAtFrame: !attempt.ended })
                }
                if (event?.type === "CUSTOM" && event.name === "kokoro.delivery.created") {
                  window.__liveDeliveryFrames.push({ name: event.name, artifact_id: event.value?.artifact_id,
                    conversation_id: event.metadata?.kokoro?.session_id, attemptId: attempt.id,
                    lastEventId: attempt.lastEventId, openAtEvent: !attempt.ended })
                }
              }
            }
          } catch { attempt.endedReason = "stream-error" }
          finally { attempt.ended = true }
        })()
      } else if (attempt) {
        attempt.ended = true
        attempt.endedReason = "non-stream-response"
      }
      if (attempt && response.status === 200 && response.body) {
        // Forward every authentic byte frame unchanged. The sole barrier holds
        // this initial stream's real terminal frame until the live card renders;
        // it never manufactures a Delivery or changes the owner event order.
        let pendingBytes = new Uint8Array(0)
        const frameEnd = (bytes) => {
          for (let index = 0; index < bytes.length - 1; index += 1) {
            if (bytes[index] === 10 && bytes[index + 1] === 10) return index + 2
            if (bytes[index] === 10 && bytes[index + 1] === 13 && bytes[index + 2] === 10) return index + 3
            if (bytes[index] === 13 && bytes[index + 1] === 10 && bytes[index + 2] === 10) return index + 3
            if (bytes[index] === 13 && bytes[index + 1] === 10 && bytes[index + 2] === 13 && bytes[index + 3] === 10) return index + 4
          }
          return -1
        }
        const eventType = (frame) => {
          const text = new TextDecoder().decode(frame)
          const data = text.split(/\r?\n/u).filter((line) => line.startsWith("data: ")).map((line) => line.slice(6)).join("\n")
          try { return JSON.parse(data)?.type ?? null } catch { return null }
        }
        const transformed = response.body.pipeThrough(new TransformStream({
          async transform(chunk, controller) {
            const joined = new Uint8Array(pendingBytes.length + chunk.length)
            joined.set(pendingBytes)
            joined.set(chunk, pendingBytes.length)
            pendingBytes = joined
            if (pendingBytes.length > 1_048_576) throw new Error("SSE frame boundary exceeded")
            for (;;) {
              const end = frameEnd(pendingBytes)
              if (end < 0) break
              const frame = pendingBytes.slice(0, end)
              pendingBytes = pendingBytes.slice(end)
              const audit = window.__deliveryAudit
              if (eventType(frame) === "RUN_FINISHED" && audit?.eventPath === attempt.path &&
                  audit.initialAttemptId === attempt.id) {
                audit.terminalHeld = true
                if (!audit.firstCard) {
                  await new Promise((resolve, reject) => {
                    const timer = setTimeout(() => reject(new Error("terminal frame barrier expired")), Math.min(terminalBarrierMs, 60_000))
                    audit.releaseTerminal = () => { clearTimeout(timer); resolve() }
                  })
                }
                audit.terminalReleased = audit.firstCard !== null
              }
              controller.enqueue(frame)
            }
          },
          flush() {
            if (pendingBytes.length !== 0) throw new Error("incomplete SSE frame")
          },
        }))
        return new Response(transformed, { status: response.status, statusText: response.statusText, headers: response.headers })
      }
      return response
    }
  }, input.timeout_ms)

  async function login(target, email, password) {
    const callbacks = []
    target.on("response", (response) => {
      const url = new URL(response.url())
      if (url.origin === input.web_origin && url.pathname === "/api/auth/callback/kokoro-iam") callbacks.push(response.status())
    })
    const entry = await target.goto(`${input.web_origin}/login`, { waitUntil: "domcontentloaded", timeout: input.timeout_ms })
    assert(entry?.status() === 200 && new URL(target.url()).pathname === "/auth/sign-in", "real IAM form absent")
    await target.getByRole("heading", { name: "欢迎回来", exact: true }).waitFor({ state: "visible", timeout: input.timeout_ms })
    await target.locator('input[name="email"][type="email"]').fill(email)
    await target.locator('input[name="password"][type="password"]').fill(password)
    await target.getByRole("button", { name: "登录", exact: true }).click()
    await target.waitForURL((url) => url.pathname === "/iam/interactions/consent" ||
      (url.origin === input.web_origin && url.pathname === "/app"), { timeout: input.timeout_ms })
    if (new URL(target.url()).pathname === "/iam/interactions/consent") {
      await target.getByRole("heading", { name: "Review requested access", exact: true }).waitFor({ state: "visible", timeout: input.timeout_ms })
      await target.getByRole("button", { name: "Agree and continue", exact: true }).click()
    }
    await target.waitForURL((url) => url.origin === input.web_origin && url.pathname === "/app", { waitUntil: "domcontentloaded", timeout: input.timeout_ms })
    const projection = await target.evaluate(async () => {
      const response = await fetch("/api/auth/session", { credentials: "same-origin", cache: "no-store" })
      return { status: response.status, body: await response.json() }
    })
    const cookies = (await target.context().cookies(input.web_origin)).filter((cookie) => cookie.name === "kokoro_product_session")
    assert(projection.status === 200 && projection.body?.authenticated === true && typeof projection.body.subject === "string" &&
      callbacks.length === 1 && callbacks[0] === 303 && cookies.length === 1 && cookies[0].httpOnly === true &&
      cookies[0].secure === true && cookies[0].sameSite === "Lax" && cookies[0].path === "/", "real IAM Product Session invalid")
    return { subject: projection.body.subject, form_status: entry.status(), callback_status: callbacks[0],
      session_status: projection.status, product_cookie: "HttpOnly+Secure+Lax" }
  }

  phase = "owner-login"
  const owner = await login(page, input.owner_email, input.owner_password)
  const sseResponses = []
  page.on("response", (response) => {
    const url = new URL(response.url())
    if (url.origin === input.web_origin && /^\/api\/session\/sessions\/[^/]+\/events$/u.test(url.pathname)) {
      sseResponses.push({ path: url.pathname, status: response.status() })
    }
  })
  phase = "browser-post-202"
  const composer = page.locator('[data-slot="composer-input"]')
  await composer.waitFor({ state: "visible", timeout: input.timeout_ms })
  const receiptPromise = page.waitForResponse((response) => {
    const url = new URL(response.url())
    return url.origin === input.web_origin && /^\/api\/session\/sessions\/[^/]+\/messages$/u.test(url.pathname) && response.request().method() === "POST"
  }, { timeout: input.timeout_ms })
  await composer.fill("Create a live Agent Artifact.")
  await page.locator('[data-composer-action="send"]').click()
  const receiptResponse = await receiptPromise
  assert(receiptResponse.status() === 202, "browser Product message POST was not 202")
  const conversation = decodeURIComponent(new URL(receiptResponse.url()).pathname.split("/")[4])
  targetConversation = conversation
  const receipt = await receiptResponse.json()
  assert(/^conv_[A-Za-z0-9_-]+$/u.test(conversation) && typeof receipt?.run_id === "string" && receipt.run_id, "browser Product receipt invalid")
  phase = "browser-sse-200"
  const eventPath = `/api/session/sessions/${encodeURIComponent(conversation)}/events`
  targetEventPath = eventPath
  // Response headers are the subscription milestone, not a timer or a pre-delivery poll.
  if (!sseResponses.some((response) => response.path === eventPath && response.status === 200)) {
    await page.waitForResponse((response) => new URL(response.url()).origin === input.web_origin &&
      new URL(response.url()).pathname === eventPath && response.status() === 200,
    { timeout: input.timeout_ms })
  }
  assert(sseResponses.some((response) => response.path === eventPath && response.status === 200), "browser did not subscribe to target AG-UI SSE200")
  const before = await page.evaluate(async (target) => {
    const response = await fetch(target, { credentials: "same-origin", cache: "no-store" })
    return { status: response.status, body: await response.json() }
  }, `/api/session/sessions/${encodeURIComponent(conversation)}`)
  assert(before.status === 200 && Array.isArray(before.body?.deliveries) && before.body.deliveries.length === 0 &&
    await page.getByRole("button", { name: "Open delivery Delivered work", exact: true }).count() === 0,
  "Delivery existed before live handshake")
  const snapshotPath = `/api/session/sessions/${encodeURIComponent(conversation)}`
  const handshake = await page.evaluate(({ eventPath, snapshotPath }) => {
    const initial = window.__aguiAttempts.filter((attempt) => attempt.path === eventPath &&
      attempt.lastEventId === null && attempt.responseStatus === 200 && !attempt.ended)
    const gets = window.__snapshotGets.filter((item) => item.path === snapshotPath)
    const audit = { eventPath, snapshotPath, snapshotCountAtHandshake: gets.length,
      pendingAtHandshake: gets.filter((item) => !item.ended).length,
      initialAttemptId: initial.length === 1 ? initial[0].id : null, firstCard: null,
      terminalHeld: false, terminalReleased: false, releaseTerminal: null }
    window.__deliveryAudit = audit
    const observer = new MutationObserver(() => {
      if (audit.firstCard || !document.querySelector('button[data-canvas-opener="true"][aria-label="Open delivery Delivered work"]')) return
      audit.firstCard = { snapshotGetCount: window.__snapshotGets.filter((item) => item.path === snapshotPath).length }
      audit.releaseTerminal?.()
      observer.disconnect()
    })
    observer.observe(document.body, { childList: true, subtree: true, attributes: true })
    return { initialAttemptIds: initial.map((item) => item.id),
      snapshotGetCount: audit.snapshotCountAtHandshake, pendingSnapshotGets: audit.pendingAtHandshake }
  }, { eventPath, snapshotPath })
  assert(handshake.initialAttemptIds.length === 1 && handshake.pendingSnapshotGets === 0,
    "initial SSE attempt or settled pre-delivery snapshot absent")
  const initialAttemptId = handshake.initialAttemptIds[0]
  protocol({ milestone: "subscribed", conversation_id: conversation, run_id: receipt.run_id,
    post_status: receiptResponse.status(), sse_status: 200, snapshot_before_delivery_count: 0,
    initial_sse_attempt_id: initialAttemptId, initial_sse_last_event_id: null,
    initial_sse_open_at_handshake: true, initial_sse_ended_at_handshake: false,
    snapshot_get_count_at_handshake: handshake.snapshotGetCount,
    pending_snapshot_gets_at_handshake: handshake.pendingSnapshotGets })

  phase = "await-owned-delivery"
  const command = await boundedLine(input.timeout_ms)
  assert(!command.done, "delivery handshake closed")
  let delivered
  try { delivered = JSON.parse(command.value) } catch { throw new Error("delivery handshake malformed") }
  assert(delivered?.command === "delivered" && delivered.conversation_id === conversation &&
    typeof delivered.artifact_id === "string" && /^artifact:[a-f0-9]{64}$/u.test(delivered.artifact_id), "delivery handshake identity invalid")
  targetArtifactId = delivered.artifact_id
  phase = "live-sse-delivery"
  await page.waitForFunction(({ artifactId, conversationId }) =>
    window.__liveDeliveryFrames.some((frame) => frame.artifact_id === artifactId && frame.conversation_id === conversationId &&
      frame.attemptId === window.__deliveryAudit?.initialAttemptId && frame.openAtEvent === true),
  { artifactId: delivered.artifact_id, conversationId: conversation }, { timeout: input.timeout_ms })
  phase = "live-sse-identity"
  const liveFrames = await page.evaluate(() => window.__liveDeliveryFrames)
  const matchingFrames = liveFrames.filter((frame) => frame.artifact_id === delivered.artifact_id &&
    frame.conversation_id === conversation && frame.attemptId === initialAttemptId &&
    frame.lastEventId === null && frame.openAtEvent === true)
  assert(matchingFrames.length === 1, "initial open SSE attempt did not carry exact binary Delivery")
  phase = "live-card-visible"
  const card = page.getByRole("button", { name: "Open delivery Delivered work", exact: true })
  await card.waitFor({ state: "visible", timeout: input.timeout_ms })
  const beforeReloadCount = await card.count()
  assert(beforeReloadCount === 1, "Chat did not render one live binary Delivery card")
  phase = "live-card-before-snapshot"
  await page.waitForFunction(() => window.__deliveryAudit?.terminalReleased === true,
    null, { timeout: input.timeout_ms })
  const liveAudit = await page.evaluate(() => ({
    firstCard: window.__deliveryAudit?.firstCard,
    snapshotCountAtHandshake: window.__deliveryAudit?.snapshotCountAtHandshake,
    initialAttemptId: window.__deliveryAudit?.initialAttemptId,
    terminalHeld: window.__deliveryAudit?.terminalHeld,
    terminalReleased: window.__deliveryAudit?.terminalReleased,
  }))
  assert(liveAudit.firstCard?.snapshotGetCount === liveAudit.snapshotCountAtHandshake &&
    liveAudit.initialAttemptId === initialAttemptId,
  "Chat card appeared after a post-handshake snapshot GET")
  phase = "terminal-barrier-release"
  assert(liveAudit.terminalHeld === true && liveAudit.terminalReleased === true,
    "real terminal SSE frame was not gated by live Chat card")
  phase = "live-canvas-download"
  await card.click()
  const canvas = page.getByRole("complementary", { name: "canvas details Delivered work", exact: true })
  await canvas.waitFor({ state: "visible", timeout: input.timeout_ms })
  assert(await canvas.getByRole("heading", { name: "Delivered work", exact: true }).count() === 1, "Canvas metadata absent")
  const downloadPromise = page.waitForEvent("download", { timeout: input.timeout_ms })
  await canvas.getByRole("button", { name: "Download", exact: true }).click()
  const download = await downloadPromise
  const nativeDigest = sha256(readFileSync(await download.path()))
  assert(download.suggestedFilename() === "delivered-work.txt" && await download.failure() === null &&
    nativeDigest === input.content_sha256, "Canvas native download bytes drift")
  await download.delete()
  phase = "live-reload-snapshot"
  await page.reload({ waitUntil: "domcontentloaded", timeout: input.timeout_ms })
  await card.waitFor({ state: "visible", timeout: input.timeout_ms })
  const afterReloadCount = await card.count()
  assert(afterReloadCount === 1, "Chat refresh duplicated or lost binary Delivery")
  const snapshot = await page.evaluate(async (target) => {
    const response = await fetch(target, { credentials: "same-origin", cache: "no-store" })
    return { status: response.status, body: await response.json() }
  }, `/api/session/sessions/${encodeURIComponent(conversation)}`)
  assert(snapshot.status === 200 && snapshot.body?.deliveries?.length === 1 &&
    snapshot.body.deliveries[0].conversation_id === conversation && snapshot.body.deliveries[0].artifact_id === delivered.artifact_id,
  "refresh snapshot lost exact binary Delivery")
  await page.screenshot({ path: input.screenshot, fullPage: true })

  phase = "member-private"
  const memberContext = await browser.newContext({ ignoreHTTPSErrors: true, locale: "en-US" })
  const memberPage = await memberContext.newPage()
  await memberPage.addInitScript(() => window.localStorage.setItem("kokoro.locale", "en"))
  const member = await login(memberPage, input.member_email, input.member_password)
  assert(member.subject !== owner.subject, "same-tenant privacy actor reused owner")
  const privateResults = await memberPage.evaluate(async ({ conversationId, artifactId }) => {
    const options = { credentials: "same-origin", cache: "no-store" }
    const chat = await fetch(`/api/session/sessions/${encodeURIComponent(conversationId)}`, options)
    const chatBody = await chat.json()
    const selector = `/api/hub/library/artifacts/${encodeURIComponent(conversationId)}/${encodeURIComponent(artifactId)}`
    const detail = await fetch(selector, options)
    const content = await fetch(`${selector}/content`, options)
    return { chat: chat.status, chatDeliveries: chatBody?.deliveries, detail: detail.status,
      content: content.status, disposition: content.headers.get("content-disposition") }
  }, { conversationId: conversation, artifactId: delivered.artifact_id })
  assert(privateResults.chat === 404 && !Array.isArray(privateResults.chatDeliveries) &&
    privateResults.detail === 404 && privateResults.content === 404 && privateResults.disposition === null,
  "same-tenant member reached private Chat Delivery")
  protocol({ milestone: "complete", browser: "chromium", entry_url: `${input.web_origin}/login`,
    owner_subject: owner.subject, member_subject: member.subject, login: { owner, member },
    conversation_id: conversation, artifact_id: delivered.artifact_id, content_sha256: input.content_sha256,
    live_event_name: "kokoro.delivery.created", live_event_count: matchingFrames.length,
    initial_sse_attempt_id: initialAttemptId, initial_sse_last_event_id: null,
    delivery_sse_attempt_id: matchingFrames[0].attemptId, delivery_sse_last_event_id: matchingFrames[0].lastEventId,
    delivery_sse_open_at_event: matchingFrames[0].openAtEvent,
    delivery_sse_attempt_ended_at_event: !matchingFrames[0].openAtEvent,
    snapshot_get_count_at_handshake: liveAudit.snapshotCountAtHandshake,
    snapshot_get_count_at_first_card: liveAudit.firstCard.snapshotGetCount,
    terminal_held_until_first_card: liveAudit.terminalHeld,
    terminal_released_after_first_card: liveAudit.terminalReleased,
    card_count_before_reload: beforeReloadCount, card_count_after_reload: afterReloadCount,
    canvas_native_download_sha256: nativeDigest, member_chat_status: privateResults.chat,
    member_detail_status: privateResults.detail, member_content_status: privateResults.content,
    screenshot: input.screenshot })
  await memberContext.close()
  await context.close()
} catch {
  // No OAuth URL, credential, request body, or stack trace enters process logs.
  let diagnostic = null
  if (page && targetConversation && targetEventPath) {
    try {
      diagnostic = await page.evaluate(({ eventPath, conversationId, artifactId }) => {
        const snapshotPath = `/api/session/sessions/${encodeURIComponent(conversationId)}`
        const snapshots = (window.__snapshotGets ?? []).filter((item) => item.path === snapshotPath)
        return {
          attempts: (window.__aguiAttempts ?? []).filter((item) => item.path === eventPath).slice(0, 8).map((item) => ({
            id: item.id, status: item.responseStatus, last_event_id_present: item.lastEventId !== null,
            ended: item.ended, ended_reason: item.endedReason, frame_count: item.frameCount, parse_errors: item.parseErrors,
          })),
          frames: (window.__aguiObservedFrames ?? []).slice(-16).map((item) => ({
            attempt_id: item.attemptId, type: item.type, name: item.name, open_at_frame: item.openAtFrame,
          })),
          delivery_frames: (window.__liveDeliveryFrames ?? []).slice(-8).map((item) => ({
            attempt_id: item.attemptId, artifact_present: typeof item.artifact_id === "string",
            conversation_present: typeof item.conversation_id === "string",
            artifact_match: item.artifact_id === artifactId,
            conversation_match: item.conversation_id === conversationId,
            open_at_event: item.openAtEvent,
          })),
          audit_initial_attempt_id: window.__deliveryAudit?.initialAttemptId ?? null,
          snapshot_get_count: snapshots.length,
          pending_snapshot_gets: snapshots.filter((item) => !item.ended).length,
          first_card_snapshot_get_count: window.__deliveryAudit?.firstCard?.snapshotGetCount ?? null,
          first_card_seen: Boolean(window.__deliveryAudit?.firstCard),
          card_count: document.querySelectorAll('button[data-canvas-opener="true"][aria-label="Open delivery Delivered work"]').length,
          terminal_held: window.__deliveryAudit?.terminalHeld === true,
          terminal_released: window.__deliveryAudit?.terminalReleased === true,
        }
      }, { eventPath: targetEventPath, conversationId: targetConversation, artifactId: targetArtifactId })
    } catch { /* A closed page has no diagnostic, never a raw exception. */ }
  }
  protocol({ milestone: "failed", phase, diagnostic })
  process.stderr.write(`FAILURE_PHASE:${phase}\n`)
  process.exitCode = 1
} finally {
  if (browser) await browser.close()
  lines.return?.()
}
