#!/usr/bin/env node
/** Real Chromium click → Project POST → file picker → CLEAN GET → reload. */

import { createHash } from "node:crypto"
import { createRequire } from "node:module"
import { readFileSync } from "node:fs"
import path from "node:path"
import process from "node:process"
import { pathToFileURL } from "node:url"

const assert = (condition, message) => { if (!condition) throw new Error(message) }
const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex")

function parseInput() {
  if (process.argv.length !== 2) throw new Error("invalid Chromium milestone input")
  let value
  try { value = JSON.parse(readFileSync(0, "utf8")) }
  catch { throw new Error("invalid Chromium milestone input") }
  const fields = ["web_origin", "web_host", "web_root", "screenshot", "owner_email", "owner_password", "member_email", "member_password", "filename", "file_content", "timeout_ms"]
  if (!value || typeof value !== "object" || Array.isArray(value) ||
      Object.keys(value).sort().join(",") !== fields.sort().join(",") ||
      !fields.filter((field) => field !== "timeout_ms").every((field) => typeof value[field] === "string" && value[field] !== "") ||
      !Number.isInteger(value.timeout_ms) || value.timeout_ms < 20_000 || value.timeout_ms > 600_000) {
    throw new Error("invalid Chromium milestone input")
  }
  let origin
  try { origin = new URL(value.web_origin) }
  catch { throw new Error("invalid Chromium milestone input") }
  if (origin.origin !== value.web_origin || origin.protocol !== "https:" || origin.hostname !== value.web_host ||
      !/^w2-[a-f0-9]{24}\.txt$/u.test(value.filename) || Buffer.byteLength(value.file_content) > 1024) {
    throw new Error("invalid Chromium milestone input")
  }
  return value
}

let browser
try {
  const input = parseInput()
  const require = createRequire(pathToFileURL(path.join(input.web_root, "package.json")))
  const { chromium } = require("@playwright/test")
  browser = await chromium.launch({ headless: true, args: [`--host-resolver-rules=MAP ${input.web_host} 127.0.0.1`, "--no-proxy-server"] })
  const observations = []
  const context = await browser.newContext({ ignoreHTTPSErrors: true, locale: "en-US" })
  const page = await context.newPage()
  await page.addInitScript(() => window.localStorage.setItem("kokoro.locale", "en"))
  page.on("response", (response) => {
    const url = new URL(response.url())
    if (url.origin === input.web_origin && url.pathname.startsWith("/api/hub/projects")) {
      observations.push({ method: response.request().method(), path: url.pathname, status: response.status(), response })
    }
  })

  async function login(target, email, password) {
    const callbackStatuses = []
    target.on("response", (response) => {
      const url = new URL(response.url())
      if (url.origin === input.web_origin && url.pathname === "/api/auth/callback/kokoro-iam") callbackStatuses.push(response.status())
    })
    const entry = await target.goto(`${input.web_origin}/login`, { waitUntil: "domcontentloaded", timeout: input.timeout_ms })
    assert(entry?.status() === 200 && new URL(target.url()).pathname === "/auth/sign-in", "real IAM sign-in navigation failed")
    await target.getByRole("heading", { name: "欢迎回来", exact: true }).waitFor({ state: "visible", timeout: input.timeout_ms })
    await target.locator('input[name="email"][type="email"]').fill(email)
    await target.locator('input[name="password"][type="password"]').fill(password)
    await target.getByRole("button", { name: "登录", exact: true }).click()
    await target.getByRole("heading", { name: "Review requested access", exact: true }).waitFor({ state: "visible", timeout: input.timeout_ms })
    assert(new URL(target.url()).pathname === "/iam/interactions/consent", "fixed IAM tenant continuation drift")
    await target.getByRole("button", { name: "Agree and continue", exact: true }).click()
    await target.waitForURL((url) => url.origin === input.web_origin && url.pathname === "/app", { waitUntil: "domcontentloaded", timeout: input.timeout_ms })
    const projection = await target.evaluate(async () => {
      const response = await fetch("/api/auth/session", { credentials: "same-origin", cache: "no-store" })
      return { status: response.status, body: await response.json() }
    })
    assert(projection.status === 200 && projection.body?.authenticated === true && typeof projection.body.subject === "string", "real Product Session absent")
    const productCookies = (await target.context().cookies(input.web_origin)).filter((cookie) => cookie.name === "kokoro_product_session")
    assert(callbackStatuses.length === 1 && callbackStatuses[0] === 303, "current OAuth callback did not complete")
    assert(productCookies.length === 1 && productCookies[0].path === "/" && productCookies[0].httpOnly === true &&
      productCookies[0].secure === true && productCookies[0].sameSite === "Lax", "current Product Session cookie invalid")
    return { subject: projection.body.subject, form_status: entry.status(), callback_status: callbackStatuses[0],
      session_status: projection.status, product_cookie: "HttpOnly+Secure+Lax" }
  }

  const ownerLogin = await login(page, input.owner_email, input.owner_password)
  const ownerSubject = ownerLogin.subject
  process.stderr.write("MILESTONE:owner-login\n")
  const createResponsePromise = page.waitForResponse((response) => new URL(response.url()).origin === input.web_origin &&
    new URL(response.url()).pathname === "/api/hub/projects" && response.request().method() === "POST", { timeout: input.timeout_ms })
  await page.getByTestId("rail-new-project").click()
  await page.getByRole("menuitem", { name: "New project", exact: true }).click()
  const createResponse = await createResponsePromise
  assert(createResponse.status() === 200, `live Project POST returned ${createResponse.status()}`)
  const projectPayload = await createResponse.json()
  const project = projectPayload?.data?.project
  assert(typeof project?.id === "string" && project.id.length > 0 && typeof project.slug === "string" && project.slug.length > 0, "live Project create receipt invalid")
  await page.waitForURL((url) => url.origin === input.web_origin && url.pathname === `/app/project/${encodeURIComponent(project.id)}`, { timeout: input.timeout_ms })
  assert(!project.id.startsWith("preview-project"), "new Project clicked into preview fixture")
  process.stderr.write("MILESTONE:live-create\n")

  const resourcePath = `/api/hub/projects/${encodeURIComponent(project.id)}/resources`
  const listResponses = () => observations.filter((item) => item.method === "GET" && item.path === resourcePath && item.status === 200)
  await page.locator('[data-context-kind="resources-skills"]').getByRole("button", { name: "Files and resources", exact: true }).click()
  await page.getByRole("dialog").getByRole("heading", { name: "Files and resources" }).waitFor({ state: "visible" })
  await page.waitForFunction((path) => performance.getEntriesByType("resource").some((entry) => new URL(entry.name).pathname === path), resourcePath, { timeout: input.timeout_ms })
  const initialListCount = listResponses().length
  const uploadPromise = page.waitForResponse((response) => new URL(response.url()).origin === input.web_origin &&
    new URL(response.url()).pathname === resourcePath && response.request().method() === "POST", { timeout: input.timeout_ms })
  const bytes = Buffer.from(input.file_content, "utf8")
  await page.locator('#project-resource-upload[type="file"]').setInputFiles({ name: input.filename, mimeType: "text/plain", buffer: bytes })
  const uploadResponse = await uploadPromise
  assert(uploadResponse.status() === 200, `file-picker upload returned ${uploadResponse.status()}`)
  const uploaded = await uploadResponse.json()
  const asset = uploaded?.data?.resources?.[0]
  assert(asset?.filename === input.filename && asset?.scan_state === "clean" && asset?.content_sha256 === sha256(bytes) && asset?.size_bytes === String(bytes.length), "upload did not confirm CLEAN exact bytes")
  await page.waitForFunction(({ filename }) => [...document.querySelectorAll('[role="dialog"] [role="listitem"]')].some((item) => item.textContent?.includes(filename)), { filename: input.filename }, { timeout: input.timeout_ms })
  assert(listResponses().length > initialListCount, "browser did not reload owner GET after upload")
  const ownerList = await listResponses().at(-1).response.json()
  assert(ownerList?.data?.items?.some((item) => item.asset_id === asset.asset_id && item.scan_state === "clean"), "owner GET did not return uploaded CLEAN asset")
  process.stderr.write("MILESTONE:owner-clean-get\n")

  const listBeforeReload = listResponses().length
  await page.reload({ waitUntil: "domcontentloaded", timeout: input.timeout_ms })
  await page.locator('[data-context-kind="resources-skills"]').getByRole("button", { name: "Files and resources", exact: true }).click()
  await page.getByRole("dialog").getByRole("listitem").filter({ hasText: input.filename }).waitFor({ state: "visible", timeout: input.timeout_ms })
  assert(listResponses().length > listBeforeReload, "browser reload did not issue durable owner GET")
  const durableList = await listResponses().at(-1).response.json()
  assert(durableList?.data?.items?.some((item) => item.asset_id === asset.asset_id && item.content_sha256 === asset.content_sha256), "durable owner GET lost CLEAN asset")
  await page.screenshot({ path: input.screenshot, fullPage: true })
  process.stderr.write("MILESTONE:reload\n")

  const memberContext = await browser.newContext({ ignoreHTTPSErrors: true, locale: "en-US" })
  const memberPage = await memberContext.newPage()
  await memberPage.addInitScript(() => window.localStorage.setItem("kokoro.locale", "en"))
  const memberLogin = await login(memberPage, input.member_email, input.member_password)
  const memberSubject = memberLogin.subject
  assert(memberSubject !== ownerSubject, "privacy actor subject reused owner")
  const privacy = await memberPage.evaluate(async ({ resourcePath, filename, content }) => {
    const list = await fetch(resourcePath, { credentials: "same-origin", cache: "no-store" })
    const listBody = await list.json()
    const form = new FormData()
    form.append("files", new File([content], filename, { type: "text/plain" }))
    const write = await fetch(resourcePath, { method: "POST", credentials: "same-origin", headers: { "Idempotency-Key": crypto.randomUUID() }, body: form })
    const writeBody = await write.json()
    return { list_status: list.status, list_code: listBody?.error?.code, write_status: write.status, write_code: writeBody?.error?.code }
  }, { resourcePath, filename: input.filename, content: input.file_content })
  assert(privacy.list_status === 404 && privacy.list_code === "project_not_found" && privacy.write_status === 404 && privacy.write_code === "project_not_found", "same-tenant second subject reached private project")
  process.stderr.write("MILESTONE:member-private\n")
  await memberContext.close()
  await context.close()
  process.stdout.write(JSON.stringify({
    browser: "chromium", entry_url: `${input.web_origin}/login`, owner_subject: ownerSubject, member_subject: memberSubject,
    login: { owner: ownerLogin, member: memberLogin },
    project_id: project.id, project_slug: project.slug, project_post_status: createResponse.status(),
    asset_id: asset.asset_id, filename: asset.filename, content_sha256: asset.content_sha256,
    upload_status: uploadResponse.status(), owner_get_after_upload: true, owner_get_after_reload: true,
    screenshot: input.screenshot, privacy,
  }))
} catch (error) {
  process.stderr.write(`${error instanceof Error ? error.message : "Chromium milestone failed"}\n`)
  process.exitCode = 1
} finally {
  await browser?.close().catch(() => undefined)
}
