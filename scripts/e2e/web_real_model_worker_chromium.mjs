#!/usr/bin/env node
/** Real model text/tool execution: no synthetic response or manual delivery. */
import { createHash, X509Certificate } from "node:crypto"
import { createRequire } from "node:module"
import { readFileSync } from "node:fs"
import path from "node:path"
import process from "node:process"
import { pathToFileURL } from "node:url"

const assert = (condition, message) => { if (!condition) throw new Error(message) }
const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex")
let browser
let phase = "input"
try {
  const input = JSON.parse(readFileSync(0, "utf8"))
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
  const page = await context.newPage()
  page.setDefaultTimeout(Math.min(input.timeout_ms, 60000))
  await page.addInitScript(() => {
    window.localStorage.setItem("kokoro.locale", "en")
    window.__modelFrames = []
    window.__modelStreams = []
    window.__modelStreamErrors = 0
    const original = window.fetch.bind(window)
    window.fetch = async (...args) => {
      const response = await original(...args)
      const raw = args[0] instanceof Request ? args[0].url : String(args[0])
      const url = new URL(raw, location.href)
      if (url.origin === location.origin && /^\/api\/session\/sessions\/[^/]+\/events$/u.test(url.pathname)) {
        const headers = new Headers(args[1]?.headers ?? (args[0] instanceof Request ? args[0].headers : undefined))
        const record = {path:url.pathname,status:response.status,lastEventId:headers.get("last-event-id")}
        window.__modelStreams.push(record)
        if (response.status === 200 && response.body) {
          // Observe a clone only; never synthesize, delay, or replace UI bytes.
          const reader = response.clone().body.getReader()
          void (async () => {
            const decoder = new TextDecoder()
            let buffer = "", total = 0
            try {
              for (;;) {
                const {done,value} = await reader.read()
                if (done) break
                total += value.length
                if (total > 8388608) throw new Error("bound")
                buffer += decoder.decode(value,{stream:true})
                for (;;) {
                  const separator = /\r?\n\r?\n/u.exec(buffer)
                  if (!separator) break
                  const frame = buffer.slice(0,separator.index)
                  buffer = buffer.slice(separator.index + separator[0].length)
                  const data = frame.split(/\r?\n/u).filter(line => line.startsWith("data:")).map(line=>line.slice(5).trimStart()).join("\n")
                  if (!data) continue
                  const event = JSON.parse(data)
                  const id = frame.split(/\r?\n/u).find(line=>line.startsWith("id:"))?.slice(3).trim()
                  if (!id || window.__modelFrames.length >= 10000) throw new Error("frame bound")
                  window.__modelFrames.push({id,event,path:url.pathname,lastEventId:record.lastEventId})
                }
              }
            } catch { window.__modelStreamErrors += 1; await reader.cancel().catch(()=>undefined) }
          })()
        }
      }
      return response
    }
  })
  async function login(target, email, password) {
    const callbacks = []
    target.on("response", response => {
      const url = new URL(response.url())
      if (url.origin === input.web_origin && url.pathname === "/api/auth/callback/kokoro-iam") callbacks.push(response.status())
    })
    const entry = await target.goto(`${input.web_origin}/login`, {waitUntil:"domcontentloaded",timeout:input.timeout_ms})
    assert(entry?.status() === 200 && new URL(target.url()).pathname === "/auth/sign-in", "form")
    await target.locator('input[name="email"][type="email"]').fill(email)
    await target.locator('input[name="password"][type="password"]').fill(password)
    await target.getByRole("button",{name:"登录",exact:true}).click()
    await target.waitForURL(url => url.pathname === "/iam/interactions/consent" || url.pathname === "/app", {timeout:input.timeout_ms})
    if (new URL(target.url()).pathname === "/iam/interactions/consent") {
      await target.getByRole("button",{name:"Agree and continue",exact:true}).click()
    }
    await target.waitForURL(url => url.origin === input.web_origin && url.pathname === "/app",{waitUntil:"domcontentloaded",timeout:input.timeout_ms})
    const session = await target.evaluate(async()=>{
      const r=await fetch("/api/auth/session",{credentials:"same-origin",cache:"no-store"})
      return {status:r.status,body:await r.json()}
    })
    const cookies=(await target.context().cookies(input.web_origin)).filter(c=>c.name==="kokoro_product_session")
    assert(session.status===200 && session.body.authenticated===true && typeof session.body.subject==="string" &&
      callbacks.length===1 && callbacks[0]===303 && cookies.length===1 && cookies[0].httpOnly && cookies[0].secure && cookies[0].sameSite==="Lax", "session")
    return {subject:session.body.subject,form_status:200,callback_status:303,session_status:200,product_cookie:"HttpOnly+Secure+Lax"}
  }
  phase = "owner-login"
  const owner = await login(page,input.owner_email,input.owner_password)
  phase = "product-post"
  const content = `/no_think\nFirst say exactly ${input.marker}. Then use write_file to create /real-model.txt containing exactly ${input.marker} (no newline, no quotes). Then call deliver with path /real-model.txt and title Real model work. Do not merely describe actions: execute both tools. After successful delivery reply exactly ${input.marker}. Do not ask questions.`
  const composer = page.locator('[data-slot="composer-input"]')
  await composer.waitFor({state:"visible",timeout:input.timeout_ms})
  const receiptPromise = page.waitForResponse(response => {
    const url=new URL(response.url())
    return url.origin===input.web_origin && /^\/api\/session\/sessions\/[^/]+\/messages$/u.test(url.pathname) && response.request().method()==="POST"
  },{timeout:input.timeout_ms})
  await composer.fill(content)
  await page.locator('[data-composer-action="send"]').click()
  const response = await receiptPromise
  assert(response.status()===202,"receipt")
  const receipt=await response.json()
  const conversation=decodeURIComponent(new URL(response.url()).pathname.split("/")[4])
  assert(/^conv_[A-Za-z0-9_-]+$/u.test(conversation) && typeof receipt.run_id==="string" && receipt.run_id,"identity")
  const run=receipt.run_id
  const eventPath=`/api/session/sessions/${encodeURIComponent(conversation)}/events`
  const snapshotPath=`/api/session/sessions/${encodeURIComponent(conversation)}`
  phase="model-text"
  await page.waitForFunction(marker=>[...document.querySelectorAll('[data-slot="markdown-message"]')].some(node=>node.textContent.includes(marker)),input.marker,{timeout:input.timeout_ms})
  phase="model-tools-delivery-terminal"
  try {
    await page.waitForFunction(({run,path})=>window.__modelFrames.some(f=>f.path===path && f.event.type==="RUN_FINISHED" && (f.event.runId??f.event.metadata?.kokoro?.run_id)===run),{run,path:eventPath},{timeout:input.timeout_ms})
  } catch {
    phase="model-terminal-frame-missing"
    throw new Error("terminal")
  }
  const wire = await page.evaluate(({run,path,marker})=>{
    const all=window.__modelFrames.filter(f=>f.path===path && (f.event.runId??f.event.metadata?.kokoro?.run_id)===run)
    const unique=[...new Map(all.map(f=>[f.id,f])).values()]
    return {delivery:unique.filter(f=>f.event.type==="CUSTOM" && f.event.name==="kokoro.delivery.created"),
      text:unique.filter(f=>f.event.type==="TEXT_MESSAGE_CONTENT").map(f=>f.event.delta).join(""),
      starts:unique.filter(f=>f.event.type==="RUN_STARTED").length,
      finishes:unique.filter(f=>f.event.type==="RUN_FINISHED").length,
      errors:unique.filter(f=>f.event.type==="RUN_ERROR").length+window.__modelStreamErrors,
      streams:window.__modelStreams.filter(s=>s.path===path && s.status===200),marker}
  },{run,path:eventPath,marker:input.marker})
  if (!(wire.starts===1 && wire.finishes===1 && wire.errors===0 && wire.text.includes(input.marker) && wire.delivery.length===1 && wire.streams.length>0)) {
    phase=`model-wire-s${wire.starts}-f${wire.finishes}-e${wire.errors}-t${Number(wire.text.includes(input.marker))}-d${wire.delivery.length}-h${wire.streams.length}`
    throw new Error("wire")
  }
  const delivered=wire.delivery[0].event.value
  assert(wire.delivery[0].event.metadata?.kokoro?.session_id===conversation && delivered.content_hash===input.content_sha256 && delivered.size===Buffer.byteLength(input.marker) && typeof delivered.artifact_id==="string" && typeof delivered.asset_id==="string","delivery")
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
  await page.reload({waitUntil:"domcontentloaded"})
  await card.waitFor({state:"visible",timeout:input.timeout_ms})
  assert(await card.count()===1,"reload card")
  const snapshot=await page.evaluate(async target=>{const r=await fetch(target,{cache:"no-store",credentials:"same-origin"});return {status:r.status,body:await r.json()}},snapshotPath)
  assert(snapshot.status===200 && snapshot.body.deliveries.length===1 && snapshot.body.deliveries[0].artifact_id===delivered.artifact_id &&
    snapshot.body.deliveries[0].conversation_id===conversation && snapshot.body.deliveries[0].run_id===run &&
    snapshot.body.messages.some(m=>m.role==="assistant" && m.status==="completed" && m.content.includes(input.marker)),"snapshot")
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
    text_marker_visible:true,live_delivery:true,reload_card_count:1,download_sha256:digest,member_statuses:memberStatuses})+"\n")
} catch {
  process.stderr.write(`REAL_MODEL_FAILURE:${phase}\n`)
  process.exitCode=1
} finally {
  if(browser) await browser.close()
}
