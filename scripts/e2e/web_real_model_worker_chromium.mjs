#!/usr/bin/env node
/** Real model text/tool execution: no synthetic response or manual delivery. */
import { createHash, X509Certificate } from "node:crypto"
import { createInterface } from "node:readline"
import { createRequire } from "node:module"
import { readFileSync } from "node:fs"
import path from "node:path"
import process from "node:process"
import { pathToFileURL } from "node:url"
import { ChatSnapshotEvidenceError, terminalChatSnapshot, assertChatSnapshotUnchanged,
  assertCompletedMessagePrefixUnchanged, uniqueRunFrames, runTextEvidence, hydratedRunText, renderedChatEvidence, assertRenderedChatUnchanged } from "./chat_snapshot_evidence.mjs"

const assert = (condition, message) => { if (!condition) throw new Error(message) }
const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex")
const PRODUCT_COUNT_TOKENS = new Set([0, 1, 2, "overflow"])
const PRODUCT_FAILURE_CLASSES = new Set(["none", "aborted", "timeout", "dns", "tls", "connection", "other"])
const PRODUCT_ADMISSION_STATES = new Set(["accepted", "rejected", "unknown"])
const PRODUCT_CONN_STATES = new Set(["connected", "reconnecting", "unavailable", "unknown"])
const UNKNOWN_PRODUCT_UI = Object.freeze({known:false,ready:false,admission:"unknown",conn:"unknown"})

function newProductAttempt(turn) {
  if (turn !== 1 && turn !== 2) throw new Error("product attempt bound")
  return {turn,requestCount:0,responseCount:0,failedCount:0,failureClass:"none",
    preClickUi:UNKNOWN_PRODUCT_UI,postClickUi:UNKNOWN_PRODUCT_UI,finalUi:UNKNOWN_PRODUCT_UI}
}

function incrementProductCount(attempt, field) {
  const value = attempt[field]
  attempt[field] = value === "overflow" || value === 2 ? "overflow" : value + 1
}

function classifyProductRequestFailure(value) {
  const text = typeof value === "string" ? value.toUpperCase() : ""
  if (text.includes("ABORT") || text.includes("CANCEL")) return "aborted"
  if (text.includes("TIMEOUT") || text.includes("TIMED_OUT")) return "timeout"
  if (text.includes("NAME_NOT_RESOLVED") || text.includes("DNS")) return "dns"
  if (text.includes("CERT") || text.includes("TLS") || text.includes("SSL")) return "tls"
  if (text.includes("CONNECTION") || text.includes("RESET") || text.includes("REFUSED") || text.includes("CLOSED")) return "connection"
  return "other"
}

function recordProductNetwork(attempt, kind, failureText) {
  if (!attempt) return
  if (kind === "request") incrementProductCount(attempt,"requestCount")
  else if (kind === "response") incrementProductCount(attempt,"responseCount")
  else if (kind === "failed") {
    incrementProductCount(attempt,"failedCount")
    const classified = classifyProductRequestFailure(failureText)
    attempt.failureClass = attempt.failureClass === "none" || attempt.failureClass === classified ? classified : "other"
  }
}

function bindProductRequest(bindings, request, attempt) {
  if (!attempt) return
  bindings.set(request,attempt)
  recordProductNetwork(attempt,"request")
}

function recordBoundProductNetwork(bindings, request, kind, failureText) {
  const attempt = bindings.get(request)
  if (!attempt) return
  bindings.delete(request)
  recordProductNetwork(attempt,kind,failureText)
}

function isProductMessagePost(value, method, origin) {
  try {
    const url = new URL(value)
    return url.origin === origin && method === "POST" && /^\/api\/session\/sessions\/[^/]+\/messages$/u.test(url.pathname)
  } catch { return false }
}

function closedProductUi(value) {
  return value && value.known === true && typeof value.ready === "boolean" &&
    PRODUCT_ADMISSION_STATES.has(value.admission) && PRODUCT_CONN_STATES.has(value.conn)
    ? {known:true,ready:value.ready,admission:value.admission,conn:value.conn}
    : UNKNOWN_PRODUCT_UI
}

async function readProductUi(page) {
  const value = await page.evaluate(() => {
    const roots = [...document.querySelectorAll('[data-app-frame-main="true"]')]
    if (roots.length !== 1) return {valid:false}
    const root = roots[0]
    const composers = [...root.querySelectorAll('[data-slot="composer-input"]')]
    const sends = [...root.querySelectorAll('[data-composer-action="send"]')]
    const stops = [...root.querySelectorAll('[data-composer-action="stop"]')]
    const connections = [...root.querySelectorAll(":scope > [data-connection-status]")]
    const composer = composers.length === 1 ? composers[0] : null
    const form = composer?.closest("form") ?? null
    const formState = form?.getAttribute("data-state")
    const busy = form?.getAttribute("aria-busy")
    const connValue = connections[0]?.getAttribute("data-connection-status")
    if (!composer || !form || !root.contains(form) || sends.length > 1 || stops.length > 1 ||
      connections.length > 1 || !["idle","running"].includes(formState) || !["true","false"].includes(busy) ||
      (connections.length === 1 && !["reconnecting","unavailable"].includes(connValue))) return {valid:false}
    const visible = element => Boolean(element && element.getClientRects().length > 0 &&
      getComputedStyle(element).visibility !== "hidden")
    const draftNonempty = composer.value.length > 0
    const conn = connections.length === 0 ? "connected" : connValue
    const ready = visible(composer) && !composer.disabled && !composer.readOnly && draftNonempty &&
      sends.length === 1 && visible(sends[0]) && !sends[0].disabled && formState === "idle" &&
      busy !== "true" && conn === "connected"
    let admission = "unknown"
    if (!draftNonempty || formState === "running" || stops.length === 1) admission = "accepted"
    else if (draftNonempty && formState === "idle" && sends.length === 1) admission = "rejected"
    return {valid:true,known:true,ready,admission,conn}
  })
  if (!value || value.valid !== true) throw new Error("product UI projection")
  const closed = closedProductUi(value)
  if (!closed.known) throw new Error("product UI projection")
  return closed
}

async function boundedProductUi(page, timeoutMs = 250, strict = false) {
  let timer
  try {
    const sample = Promise.resolve().then(()=>readProductUi(page))
    return await Promise.race([
      strict ? sample : sample.catch(()=>UNKNOWN_PRODUCT_UI),
      new Promise(resolve=>{timer=setTimeout(()=>resolve(UNKNOWN_PRODUCT_UI),timeoutMs)}),
    ])
  } finally { clearTimeout(timer) }
}

function productAwaitFailurePhase(attempt) {
  const count = value => PRODUCT_COUNT_TOKENS.has(value) ? String(value) : "overflow"
  const network = PRODUCT_FAILURE_CLASSES.has(attempt?.failureClass) ? attempt.failureClass : "other"
  const turn = attempt?.turn === 2 ? 2 : 1
  const before = closedProductUi(attempt?.preClickUi)
  const final = closedProductUi(attempt?.finalUi)
  const after = final.known ? final : closedProductUi(attempt?.postClickUi)
  const phase = `product-response-await-t${turn}-req${count(attempt?.requestCount)}-res${count(attempt?.responseCount)}-fail${count(attempt?.failedCount)}-net-${network}-ui-${before.known ? before.ready ? "ready" : "blocked" : "unknown"}-admission-${after.admission}-conn-${after.conn}`
  return phase.length <= 240 ? phase : "product-response-await-diagnostic-bound"
}

async function safeProductAwaitFailurePhase(originalPhase, attempt, page) {
  try {
    if (originalPhase !== "product-response-await" || !attempt) return originalPhase
    attempt.finalUi = await boundedProductUi(page,250,true)
    const diagnostic = productAwaitFailurePhase(attempt)
    return /^product-response-await-[a-z0-9-]{1,220}$/u.test(diagnostic) ? diagnostic : originalPhase
  } catch { return originalPhase }
}

let browser, page, currentProductAttempt = null
const inputReader = createInterface({input:process.stdin,crlfDelay:Infinity})
const inputLines = inputReader[Symbol.asyncIterator]()
let phase = "input"
try {
  const input = JSON.parse((await inputLines.next()).value)
  const fields = ["web_origin", "web_root", "screenshot", "web_certificate", "owner_email", "owner_password", "member_email", "member_password", "marker", "content_sha256", "timeout_ms"]
  assert(input && Object.keys(input).sort().join() === [...fields].sort().join() &&
    fields.filter(key => key !== "timeout_ms").every(key => typeof input[key] === "string" && input[key]) &&
    Number.isInteger(input.timeout_ms) && input.timeout_ms >= 20000 && input.timeout_ms <= 600000 &&
    /^KOKORO_REAL_MODEL_[a-f0-9]{24}$/u.test(input.marker) && sha256(input.marker) === input.content_sha256, "input")
  const origin = new URL(input.web_origin)
  assert(origin.origin === input.web_origin && origin.protocol === "https:" &&
    /^web-[a-f0-9]{24}\.example\.test$/u.test(origin.hostname) &&
    path.isAbsolute(input.web_root) && path.isAbsolute(input.screenshot) &&
    path.isAbsolute(input.web_certificate) && path.basename(input.web_certificate) === "web.crt" &&
    path.dirname(input.web_certificate) === path.dirname(input.screenshot), "origin")
  phase = "certificate"
  const certificate = new X509Certificate(readFileSync(input.web_certificate))
  assert(certificate.checkHost(origin.hostname) === origin.hostname, "certificate")
  const pin = createHash("sha256").update(certificate.publicKey.export({type:"spki",format:"der"})).digest("base64")
  const require = createRequire(pathToFileURL(path.join(input.web_root, "package.json")))
  const { chromium } = require("@playwright/test")
  phase = "browser"
  browser = await chromium.launch({headless:true,args:[`--host-resolver-rules=MAP ${origin.hostname} 127.0.0.1`,"--no-proxy-server",`--ignore-certificate-errors-spki-list=${pin}`]})
  const context = await browser.newContext({ignoreHTTPSErrors:true,locale:"en-US"})
  page = await context.newPage()
  page.setDefaultTimeout(Math.min(input.timeout_ms, 60000))
  // Evidence lives in Node, not in a document that navigation will destroy.
  let epoch = 0, observedBytes = 0, observerFailure = false
  const documents = new Map(), posts = [], frames = [], streams = [], snapshots = [], ended = new Set()
  const productAttemptsByRequest = new WeakMap()
  await page.exposeBinding("__rootEvidence", ({frame}, record) => {
    try {
      assert(frame === page.mainFrame() && record && typeof record.document === "string", "observer source")
      if (!documents.has(record.document)) {
        assert(documents.size < 20, "document bound")
        documents.set(record.document, epoch)
      }
      const observation = {...record, epoch:documents.get(record.document)}
      observedBytes += Buffer.byteLength(JSON.stringify(record))
      assert(observedBytes <= 33554432, "observation bound")
      if (record.kind === "frame") {
        assert(frames.length < 10000, "frame bound")
        frames.push(observation)
      } else if (record.kind === "stream") {
        assert(streams.length < 100, "stream bound")
        streams.push(observation)
      } else if (record.kind === "snapshot-start" || record.kind === "snapshot") {
        assert(snapshots.length < 100, "snapshot bound")
        snapshots.push(observation)
      } else if (record.kind === "end") ended.add(record.streamId)
      else if (record.kind === "error" && !(record.aborted && observation.epoch < epoch)) observerFailure = true
    } catch { observerFailure = true }
  })
  page.on("request", request => {
    if (!isProductMessagePost(request.url(),request.method(),input.web_origin)) return
    bindProductRequest(productAttemptsByRequest,request,currentProductAttempt)
    try {
      const pathname = new URL(request.url()).pathname
      const body = request.postDataJSON()
      assert(posts.length < 2 && typeof body.content === "string" && body.content.length > 0 && Buffer.byteLength(body.content) <= 8388608, "post bound")
      posts.push({request, path:pathname, content:body.content})
    } catch { observerFailure = true }
  })
  page.on("response", response => {
    try { recordBoundProductNetwork(productAttemptsByRequest,response.request(),"response") }
    catch { /* Diagnostics never replace the journey's original result. */ }
  })
  page.on("requestfailed", request => {
    try { recordBoundProductNetwork(productAttemptsByRequest,request,"failed",request.failure()?.errorText) }
    catch { recordBoundProductNetwork(productAttemptsByRequest,request,"failed") }
  })
  await page.addInitScript(() => {
    window.localStorage.setItem("kokoro.locale", "en")
    const document = crypto.randomUUID(), tags = new WeakMap()
    let sequence = 0, queue = Promise.resolve()
    const emit = record => {
      queue = queue.then(() => window.__rootEvidence({...record, document})).catch(() => undefined)
    }
    emit({kind:"document"})
    const original = window.fetch.bind(window)
    window.fetch = async (...args) => {
      const raw = args[0] instanceof Request ? args[0].url : String(args[0])
      const url = new URL(raw, location.href), requestSequence = ++sequence
      const tag = tags.get(args[0]) ?? "ui"
      const response = await original(...args), responseSequence = ++sequence
      if (url.origin !== location.origin) return response
      if (/^\/api\/session\/sessions\/[^/]+$/u.test(url.pathname) && tag === "ui") {
        const record = {path:url.pathname,tag,status:response.status,requestSequence,responseSequence}
        emit({...record,kind:"snapshot-start"})
        void response.clone().text().then(text => {
          if (new TextEncoder().encode(text).length > 8388608) throw new Error("bound")
          emit({...record,kind:"snapshot",body:JSON.parse(text)})
        }).catch(() => emit({kind:"error"}))
      }
      if (/^\/api\/session\/sessions\/[^/]+\/events$/u.test(url.pathname)) {
        const headers = new Headers(args[1]?.headers ?? (args[0] instanceof Request ? args[0].headers : undefined))
        const streamId = `${document}:${requestSequence}`
        const record = {path:url.pathname,tag,status:response.status,lastEventId:headers.get("last-event-id"),requestSequence,responseSequence,streamId}
        emit({...record,kind:"stream"})
        if (response.status === 200 && response.body) {
          // Observe a clone only; never synthesize, delay, or replace UI bytes.
          const reader = response.clone().body.getReader()
          void (async () => {
            const decoder = new TextDecoder("utf-8", {fatal:true})
            let buffer = "", total = 0, count = 0
            const drain = () => {
              for (;;) {
                const separator = /\r?\n\r?\n/u.exec(buffer)
                if (!separator) break
                const frame = buffer.slice(0,separator.index)
                buffer = buffer.slice(separator.index + separator[0].length)
                const lines = frame.split(/\r?\n/u)
                const data = lines.filter(line => line.startsWith("data:")).map(line=>line.slice(5).trimStart()).join("\n")
                if (!data) continue
                const event = JSON.parse(data), id = lines.find(line=>line.startsWith("id:"))?.slice(3).trim()
                if (!id || id.length > 4096 || ++count > 10000) throw new Error("frame bound")
                emit({...record,kind:"frame",id,event})
              }
            }
            try {
              for (;;) {
                const {done,value} = await reader.read()
                if (done) break
                total += value.length
                if (total > 8388608) throw new Error("bound")
                buffer += decoder.decode(value,{stream:true})
                drain()
              }
              buffer += decoder.decode()
              drain()
              if (buffer.trim()) throw new Error("truncated frame")
              emit({...record,kind:"end"})
            } catch (error) {
              emit({kind:"error",aborted:error.name === "AbortError"})
              await reader.cancel().catch(()=>undefined)
            }
          })()
        }
      }
      return response
    }
    window.__rootProbeSnapshot = async target => {
      const request = new Request(new URL(target,location.href),{cache:"no-store",credentials:"same-origin"})
      tags.set(request,"probe")
      const response = await fetch(request)
      return {status:response.status,body:await response.json()}
    }
    window.__rootAuditReplay = async ({target,cursor}) => {
      const request = new Request(new URL(target,location.href),{cache:"no-store",credentials:"same-origin",headers:{"Last-Event-ID":cursor}})
      tags.set(request,"audit")
      const response = await fetch(request)
      if (response.status !== 200 || !response.body) throw new Error("audit HTTP")
      const reader = response.body.getReader()
      let total = 0
      for (;;) {
        const {done,value} = await reader.read()
        if (done) break
        if ((total += value.length) > 8388608) { await reader.cancel(); throw new Error("audit bound") }
      }
    }
  })
  const deadline = Date.now() + input.timeout_ms
  async function until(check) {
    for (;;) {
      assert(!observerFailure, "observer")
      const result = await check()
      if (result) return result
      assert(Date.now() < deadline, "journey deadline")
      await new Promise(resolve=>setTimeout(resolve,25))
    }
  }
  async function login(target, email, password) {
    const callbacks = [], consentGets = [], consentPosts = [], appGets = [], navigation = []
    target.on("response", response => {
      const url = new URL(response.url()), request = response.request()
      if (url.origin !== input.web_origin || !request.isNavigationRequest()) return
      if (url.pathname === "/iam/interactions/consent") {
        if (request.method() === "GET") {
          consentGets.push(response.status())
          navigation.push("consent-get")
        } else if (request.method() === "POST") {
          // Keep only proof flags and the decision; never retain CSRF/OAuth values.
          const form = new URLSearchParams(request.postData() ?? "")
          consentPosts.push({status:response.status(),decision:form.get("decision"),
            native:request.resourceType()==="document" && request.headers()["content-type"]?.split(";")[0]==="application/x-www-form-urlencoded",
            csrf:form.getAll("csrf_token").length===1 && Boolean(form.get("csrf_token")),
            closed:[...form.keys()].sort().join() === "csrf_token,decision" && form.getAll("decision").length===1})
          navigation.push("consent-post")
        }
      } else if (url.pathname === "/api/auth/callback/kokoro-iam") {
        callbacks.push(response.status())
        navigation.push("callback")
      } else if (url.pathname === "/app" && request.method()==="GET") {
        appGets.push(response.status())
        navigation.push("app")
      }
    })
    const entry = await target.goto(`${input.web_origin}/login`, {waitUntil:"domcontentloaded",timeout:input.timeout_ms})
    assert(entry?.status() === 200 && new URL(target.url()).pathname === "/auth/sign-in", "form")
    await target.locator('input[name="email"][type="email"]').fill(email)
    await target.locator('input[name="password"][type="password"]').fill(password)
    await target.getByRole("button",{name:"登录",exact:true}).click()
    await target.waitForURL(url => url.pathname === "/iam/interactions/consent" || url.pathname === "/app", {timeout:input.timeout_ms})
    // This journey owns fresh fixture identities with zero pre-existing consent.
    // A direct app redirect is not proof of their required first-login decision.
    assert(new URL(target.url()).origin===input.web_origin && new URL(target.url()).pathname==="/iam/interactions/consent", "first login consent missing")
    await target.getByRole("heading",{name:"Review requested access",exact:true}).waitFor({state:"visible",timeout:input.timeout_ms})
    assert(consentGets.length===1 && consentGets[0]===200 && consentPosts.length===0,"consent page")
    await target.getByRole("button",{name:"Agree and continue",exact:true}).click()
    await target.waitForURL(url => url.origin === input.web_origin && url.pathname === "/app",{waitUntil:"domcontentloaded",timeout:input.timeout_ms})
    assert(consentPosts.length===1 && [302,303].includes(consentPosts[0].status) && consentPosts[0].decision==="agree" &&
      consentPosts[0].native && consentPosts[0].csrf && consentPosts[0].closed && appGets.length===1 && appGets[0]===200 &&
      navigation.join() === "consent-get,consent-post,callback,app","first login consent sequence")
    const session = await target.evaluate(async()=>{
      const r=await fetch("/api/auth/session",{credentials:"same-origin",cache:"no-store"})
      return {status:r.status,body:await r.json()}
    })
    const cookies=(await target.context().cookies(input.web_origin)).filter(c=>c.name==="kokoro_product_session")
    assert(session.status===200 && session.body.authenticated===true && typeof session.body.subject==="string" &&
      callbacks.length===1 && callbacks[0]===303 && cookies.length===1 && cookies[0].httpOnly && cookies[0].secure && cookies[0].sameSite==="Lax", "session")
    return {subject:session.body.subject,form_status:200,callback_status:303,session_status:200,product_cookie:"HttpOnly+Secure+Lax",
      consent_status:consentGets[0],consent_post_count:consentPosts.length,consent_post_status:consentPosts[0].status,
      consent_decision:consentPosts[0].decision,native_consent:consentPosts[0].native,app_status:appGets[0]}
  }
  phase = "owner-login"
  const owner = await login(page,input.owner_email,input.owner_password)
  async function observationBoundary(stage,index,receipt) {
    process.stdout.write(JSON.stringify({kind:"observation-window",stage,index,...(receipt ? {receipt} : {})})+"\n")
    if (stage==="receipt") return
    let timer
    try {
      const line = await Promise.race([inputLines.next(),new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error("observation ACK deadline")),input.timeout_ms)})])
      const ack=JSON.parse(line.value)
      assert(ack && Object.keys(ack).sort().join()==="index,kind,stage" && ack.kind==="observation-ack" && ack.stage===stage && ack.index===index,"observation ACK")
    } finally { clearTimeout(timer) }
  }
  const receipts = []
  let conversation, eventPath, snapshotPath
  const composer = page.locator('[data-slot="composer-input"]')
  async function submit(content) {
    phase = "product-composer-visible"
    await composer.waitFor({state:"visible",timeout:input.timeout_ms})
    currentProductAttempt = newProductAttempt(receipts.length+1)
    phase = "product-response-arm"
    const receiptPromise = page.waitForResponse(response => {
      return isProductMessagePost(response.url(),response.request().method(),input.web_origin)
    },{timeout:input.timeout_ms})
    // Observe the armed waiter even if an earlier UI step fails; the awaited
    // original promise still propagates its failure below without raw diagnostics.
    receiptPromise.catch(() => {})
    phase = "product-composer-fill"
    await composer.fill(content)
    phase = "product-observation-open"
    await observationBoundary("open",receipts.length)
    phase = "product-send-click"
    currentProductAttempt.preClickUi = await boundedProductUi(page)
    await page.locator('[data-composer-action="send"]').click()
    currentProductAttempt.postClickUi = await boundedProductUi(page)
    phase = "product-response-await"
    const response = await receiptPromise
    phase = response.status()===202 ? "product-receipt-json" : "product-http-status"
    const receipt = await response.json()
    const post = posts.find(item=>item.request === response.request())
    phase = response.status()===202 ? "product-receipt-request" : "product-http-status"
    assert(response.status()===202 && post?.content===content, "receipt request")
    phase = "product-receipt-identity"
    const keys = ["run_id","user_message_id","assistant_message_id"]
    assert(receipt && Object.keys(receipt).sort().join() === keys.sort().join() &&
      keys.every(key=>typeof receipt[key]==="string" && /^[A-Za-z0-9_.:-]{1,191}$/u.test(receipt[key])), "receipt identity")
    phase = "product-conversation"
    const current = decodeURIComponent(new URL(response.url()).pathname.split("/")[4])
    assert(/^conv_[A-Za-z0-9_-]{1,186}$/u.test(current) && (!conversation || conversation===current),"conversation")
    conversation = current
    eventPath = `/api/session/sessions/${encodeURIComponent(conversation)}/events`
    snapshotPath = `/api/session/sessions/${encodeURIComponent(conversation)}`
    receipts.push(receipt)
    phase = "product-observation-receipt"
    await observationBoundary("receipt",receipts.length-1,receipt)
    phase = "product-receipt-uniqueness"
    assert(new Set(receipts.map(item=>item.run_id)).size===receipts.length &&
      new Set(receipts.flatMap(item=>[item.user_message_id,item.assistant_message_id])).size===receipts.length*2,"receipt uniqueness")
    return receipt
  }
  const uiFrames = () => frames.filter(frame=>frame.tag==="ui" && frame.path===eventPath)
  const finished = run => uniqueRunFrames(uiFrames(),run).some(frame=>frame.event.type==="RUN_FINISHED")
  async function readSnapshot() {
    const result=await page.evaluate(target=>window.__rootProbeSnapshot(target),snapshotPath)
    assert(result.status===200,"snapshot HTTP")
    return result.body
  }
  async function readRenderedMessages(messages) {
    const allowed = messages.map(message=>message.role==="user" ? [message.message_id] : [...new Set([
      message.message_id,...uniqueRunFrames(uiFrames(),message.run_id).filter(frame=>["TEXT_MESSAGE_START","TEXT_MESSAGE_CONTENT"].includes(frame.event.type))
        .map(frame=>frame.event.messageId).filter(id=>typeof id==="string" && /^[A-Za-z0-9_.:-]{1,191}$/u.test(id))
    ])].map(id=>`assistant:${message.run_id}:message:${id}`))
    const items = page.locator('[data-conversation-thread-inner="true"] > [data-slot="message-scroller-item"][data-message-id]')
    const actualIds = await items.evaluateAll(elements=>elements.map(element=>element.dataset.messageId).filter(id=>!["deliveries","resume-retry"].includes(id)))
    if (actualIds.length!==messages.length || !actualIds.every((id,index)=>allowed[index].includes(id))) return null
    const rows = []
    for (const [index,id] of actualIds.entries()) {
      // Existing MessageScrollerItem anchors identify the actual render, not a
      // synthetic probe or a second API projection. Read each after scrolling.
      const target = page.locator(`[data-slot="message-scroller-item"][data-message-id=${JSON.stringify(id)}]`)
      await target.scrollIntoViewIfNeeded()
      rows.push(await target.evaluate((element,role)=>{
        const bodies=[...element.querySelectorAll(role==="user" ? '[data-slot="user-message-body"]' : '[data-state="streaming"] > [data-slot="markdown-message"], [data-state="settled"] > [data-slot="markdown-message"]')]
        const visible=bodies.length>0 && bodies.every(body=>body.checkVisibility({checkVisibilityCSS:true,checkOpacity:true,contentVisibilityAuto:true}))
        const plain=role==="user" ? bodies.length===1 : bodies.length>0 && bodies.every(body=>
          [...body.children].length>0 && [...body.children].every(child=>child.tagName==="P" && child.children.length===0))
        return {anchor:element.dataset.messageId,role,visible,plain,
          body:bodies.map(body=>role==="user" ? body.textContent : body.textContent.trim()).join("")}
      },messages[index].role))
    }
    try { return renderedChatEvidence(rows,messages,allowed) }
    catch (error) { if (error instanceof ChatSnapshotEvidenceError) return null; throw error }
  }

  const firstMarker = `KOKORO_FIRST_TEXT_${input.marker.slice(-24)}`
  const firstContent = `/no_think\nReply exactly ${firstMarker}. Do not use tools or ask questions.`
  const firstReceipt = await submit(firstContent)
  phase = "first-text-terminal"
  await until(()=>finished(firstReceipt.run_id))
  const firstBody = await until(async()=>{
    const body = await readSnapshot()
    return body.messages?.length===2 && body.messages.every(message=>message.status==="completed") && !body.execution_head ? body : null
  })
  const firstSnapshot = terminalChatSnapshot(firstBody,[firstReceipt])
  const firstWire = runTextEvidence(uiFrames(),firstReceipt.run_id)
  assert(firstWire.content===firstSnapshot.messages[1].content && firstWire.content.includes(firstMarker),"first text")
  phase = "first-full-render"
  const firstRender = await until(()=>readRenderedMessages(firstSnapshot.messages))
  await observationBoundary("close",0,firstReceipt)
  const content = `/no_think\nFirst say exactly ${input.marker}. Then use write_file to create /real-model.txt containing exactly ${input.marker} (no newline, no quotes). Then call deliver with path /real-model.txt and title Real model work. Do not merely describe actions: execute both tools. After successful delivery reply exactly ${input.marker}. Do not ask questions.`
  const receipt = await submit(content), run = receipt.run_id
  phase = "second-partial-active"
  const beforeReload = await until(async()=>{
    const body = await readSnapshot()
    const partial = body.messages?.find(message=>message.message_id===receipt.assistant_message_id)
    assertCompletedMessagePrefixUnchanged(firstSnapshot.messages,body.messages)
    if (finished(run)) throw new Error("finished before active reload")
    return body.execution_head?.run_id===run && body.execution_head.state==="active" &&
      body.messages.length===4 && partial?.run_id===run && partial.role==="assistant" &&
      partial.status==="streaming" && typeof partial.content==="string" && partial.content.length>0 ? body : null
  })
  // No tool call, pause, throttling, or fake stream creates this active window.
  assert(!finished(run), "finished before reload")
  phase = "second-active-reload"
  epoch += 1
  const reloadEpoch = epoch
  await page.reload({waitUntil:"domcontentloaded",timeout:input.timeout_ms})
  const freshStream = await until(()=>streams.find(stream=>stream.epoch===reloadEpoch && stream.path===eventPath && stream.tag==="ui"))
  assert(freshStream.status===200,"fresh UI stream")
  // Bind the first new UI SSE request to its preceding actual UI snapshot response.
  const hydrationStart = snapshots.filter(snapshot=>snapshot.kind==="snapshot-start" && snapshot.epoch===reloadEpoch &&
    snapshot.document===freshStream.document && snapshot.path===snapshotPath &&
    snapshot.responseSequence < freshStream.requestSequence).sort((a,b)=>b.responseSequence-a.responseSequence)[0]
  assert(hydrationStart,"UI hydration missing")
  const hydrationRecord = await until(()=>snapshots.find(snapshot=>snapshot.kind==="snapshot" && snapshot.document===hydrationStart.document &&
    snapshot.responseSequence===hydrationStart.responseSequence))
  const hydration = hydrationRecord.body
  assertCompletedMessagePrefixUnchanged(firstSnapshot.messages,hydration.messages)
  assert(hydration.event_watermark===freshStream.lastEventId && hydration.execution_head?.state==="active" &&
    hydration.execution_head.run_id===run,"actual UI hydration")
  phase = "second-model-terminal"
  await until(()=>finished(run))
  const finalBody = await until(async()=>{
    const body = await readSnapshot()
    return body.messages?.length===4 && body.messages.every(message=>message.status==="completed") && !body.execution_head ? body : null
  })
  const terminalSnapshot = terminalChatSnapshot(finalBody,receipts)
  phase = "second-full-render"
  const terminalRender = await until(()=>readRenderedMessages(terminalSnapshot.messages))
  assertRenderedChatUnchanged(firstRender,terminalRender.slice(0,2))
  await observationBoundary("close",1,receipt)
  assertCompletedMessagePrefixUnchanged(firstSnapshot.messages,terminalSnapshot.messages)
  const reconstruction = hydratedRunText(hydration,uiFrames().filter(frame=>frame.epoch===reloadEpoch),receipt,freshStream.lastEventId)
  assert(reconstruction.content===terminalSnapshot.messages[3].content,"snapshot plus real tail")
  // One real, read-only durable replay verifies the complete second Run, including
  // bytes projected during navigation. It never contributes UI/live-delivery proof.
  phase = "second-full-agui-replay"
  await page.evaluate(value=>window.__rootAuditReplay(value),{target:eventPath,cursor:firstSnapshot.event_watermark})
  const audit = await until(()=>streams.find(stream=>stream.tag==="audit" && stream.path===eventPath && ended.has(stream.streamId)))
  const secondWire = runTextEvidence(frames.filter(frame=>frame.streamId===audit.streamId),run)
  assert(secondWire.content===terminalSnapshot.messages[3].content && secondWire.content.includes(input.marker),"second text")
  const deliveries = uniqueRunFrames(uiFrames(),run).filter(frame=>frame.event.type==="CUSTOM" && frame.event.name==="kokoro.delivery.created")
  assert(deliveries.length===1,"live delivery")
  const delivered = deliveries[0].event.value
  assert(deliveries[0].event.metadata?.kokoro?.session_id===conversation && delivered.content_hash===input.content_sha256 &&
    delivered.size===Buffer.byteLength(input.marker) && typeof delivered.artifact_id==="string" && typeof delivered.asset_id==="string","delivery")
  phase="terminal-owner-immutable-snapshot"
  assertChatSnapshotUnchanged(terminalSnapshot,terminalChatSnapshot(await readSnapshot(),receipts))
  assertRenderedChatUnchanged(terminalRender,await until(()=>readRenderedMessages(terminalSnapshot.messages)))
  assert(!observerFailure && posts.length===2 && posts.every(post=>post.path===`${snapshotPath}/messages`),"exact two POST")
  const turns = [firstWire,secondWire].map((wire,index)=>{
    const submitted = posts[index].content, user = terminalSnapshot.messages[index*2], assistant = terminalSnapshot.messages[index*2+1]
    assert(submitted===user.content && wire.content===assistant.content,"turn full text")
    return {receipt:receipts[index],submitted_content_sha256:sha256(submitted),snapshot_user_content_sha256:sha256(user.content),
      event_assistant_content_sha256:wire.sha256,snapshot_assistant_content_sha256:sha256(assistant.content),
      start_count:wire.start_count,finish_count:wire.finish_count,error_count:wire.error_count}
  })
  const partial = beforeReload.messages.find(message=>message.message_id===receipt.assistant_message_id)
  const activeReload = {run_id:run,state:beforeReload.execution_head.state,partial_content_length:partial.content.length,
    finished_before_reload:false,hydration_watermark:hydration.event_watermark,sse_last_event_id:freshStream.lastEventId,
    snapshot_plus_tail_sha256:reconstruction.sha256}
  phase="chat-card"
  const card=page.getByRole("button",{name:"Open delivery Real model work",exact:true})
  await card.waitFor({state:"visible",timeout:input.timeout_ms})
  assert(await card.count()===1,"card")
  await card.click()
  const canvas=page.getByRole("complementary",{name:"canvas details Real model work",exact:true})
  await canvas.waitFor({state:"visible"})
  phase="canvas-original-download"
  const pendingDownload=page.waitForEvent("download",{timeout:input.timeout_ms})
  await canvas.getByRole("button",{name:"Download",exact:true}).click()
  const download=await pendingDownload
  const downloadPath=await download.path()
  const digest=sha256(readFileSync(downloadPath))
  assert(await download.failure()===null && digest===input.content_sha256 && download.suggestedFilename()==="real-model.txt","download")
  await download.delete()
  phase="reload-snapshot"
  epoch += 1
  await page.reload({waitUntil:"domcontentloaded"})
  await card.waitFor({state:"visible",timeout:input.timeout_ms})
  assert(await card.count()===1,"reload card")
  const snapshot = {status:200,body:await readSnapshot()}
  assert(snapshot.status===200 && snapshot.body.deliveries.length===1 && snapshot.body.deliveries[0].artifact_id===delivered.artifact_id &&
    snapshot.body.deliveries[0].conversation_id===conversation && snapshot.body.deliveries[0].run_id===run &&
    snapshot.body.messages.some(m=>m.role==="assistant" && m.status==="completed" && m.content.includes(input.marker)),"snapshot")
  assertChatSnapshotUnchanged(terminalSnapshot,terminalChatSnapshot(snapshot.body,receipts))
  phase = "terminal-reload-full-render"
  const reloadedRender = await until(()=>readRenderedMessages(terminalSnapshot.messages))
  assertRenderedChatUnchanged(terminalRender,reloadedRender)
  assertRenderedChatUnchanged(firstRender,reloadedRender.slice(0,2))
  assert(!observerFailure && posts.length===2,"terminal reload POST drift")
  await page.screenshot({path:input.screenshot,fullPage:true})
  phase="member-private"
  const memberContext=await browser.newContext({ignoreHTTPSErrors:true,locale:"en-US"})
  const memberPage=await memberContext.newPage()
  const member=await login(memberPage,input.member_email,input.member_password)
  assert(member.subject!==owner.subject,"member")
  const memberStatuses=await memberPage.evaluate(async ({conversation,artifact})=>{
    const detail=`/api/hub/library/artifacts/${encodeURIComponent(conversation)}/${encodeURIComponent(artifact)}`
    const statuses=[]
    for(const target of [`/api/session/sessions/${encodeURIComponent(conversation)}`,detail,`${detail}/content`]){
      const response=await fetch(target,{credentials:"same-origin",cache:"no-store"})
      statuses.push(response.status)
      await response.arrayBuffer()
    }
    return statuses
  },{conversation,artifact:delivered.artifact_id})
  assert(memberStatuses.every(status=>status===404),"privacy")
  process.stdout.write(JSON.stringify({browser:"chromium",login:{owner,member},screenshot:input.screenshot,
    message_post_status:202,agui_status:200,conversation_id:conversation,run_id:run,artifact_id:delivered.artifact_id,asset_id:delivered.asset_id,
    text_marker_visible:true,live_delivery:true,reload_card_count:1,download_sha256:digest,member_statuses:memberStatuses,
    owner_snapshot_immutable:true,completed_reload_content_equal:true,
    assistant_content_sha256:terminalSnapshot.assistant_content_sha256,
    message_post_count:posts.length,message_post_statuses:[202,202],completed_message_count:terminalSnapshot.messages.length,
    first_turn_preserved:true,turns,active_reload:activeReload})+"\n")
} catch (error) {
  const originalPhase = phase
  phase = await safeProductAwaitFailurePhase(originalPhase,currentProductAttempt,page)
  process.stderr.write(`REAL_MODEL_FAILURE:${phase}\n`)
  if (error instanceof ChatSnapshotEvidenceError) {
    process.stderr.write(JSON.stringify({code:error.code,evidence:error.evidence})+"\n")
  }
  process.exitCode=1
} finally {
  if(browser) await browser.close()
  inputReader.close()
}
