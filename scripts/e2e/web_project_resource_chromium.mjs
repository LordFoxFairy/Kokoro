#!/usr/bin/env node
/** Real Chromium IAM → Project upload → personal Library upload/download/private reload. */

import { createHash, randomUUID } from "node:crypto"
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
let phase = "parse-input"
try {
  const input = parseInput()
  phase = "launch-browser"
  const require = createRequire(pathToFileURL(path.join(input.web_root, "package.json")))
  const { chromium } = require("@playwright/test")
  browser = await chromium.launch({ headless: true, args: [`--host-resolver-rules=MAP ${input.web_host} 127.0.0.1`, "--no-proxy-server"] })
  const observations = []
  const libraryObservations = []
  const context = await browser.newContext({ ignoreHTTPSErrors: true, locale: "en-US" })
  const page = await context.newPage()
  await page.addInitScript(() => window.localStorage.setItem("kokoro.locale", "en"))
  page.on("response", (response) => {
    const url = new URL(response.url())
    if (url.origin === input.web_origin && url.pathname.startsWith("/api/hub/projects")) {
      observations.push({ method: response.request().method(), path: url.pathname, status: response.status(), response })
    }
    if (url.origin === input.web_origin && url.pathname === "/api/hub/library" && response.request().method() === "GET") {
      libraryObservations.push({ status: response.status(), response })
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
  phase = "expand-project-rail"
  if (!(await page.getByTestId("rail-new-project").isVisible())) {
    await page.getByRole("button", { name: "Expand sidebar", exact: true }).click()
  }
  await page.getByTestId("rail-new-project").waitFor({ state: "visible", timeout: input.timeout_ms })
  process.stderr.write("MILESTONE:project-rail-visible\n")
  phase = "open-project-menu"
  const createResponsePromise = page.waitForResponse((response) => new URL(response.url()).origin === input.web_origin &&
    new URL(response.url()).pathname === "/api/hub/projects" && response.request().method() === "POST", { timeout: input.timeout_ms })
  await page.getByTestId("rail-new-project").click()
  phase = "select-project-create"
  await page.getByRole("menuitem", { name: "New project", exact: true }).click()
  phase = "await-project-post"
  const createResponse = await createResponsePromise
  phase = "validate-project-receipt"
  assert(createResponse.status() === 200, `live Project POST returned ${createResponse.status()}`)
  const projectPayload = await createResponse.json()
  const project = projectPayload?.data?.project
  assert(typeof project?.id === "string" && project.id.length > 0 && typeof project.slug === "string" && project.slug.length > 0, "live Project create receipt invalid")
  phase = "navigate-project"
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

  phase = "personal-file-product-post"
  const personalFilename = `personal-${input.filename}`
  const personalBytes = Buffer.from(`W2 personal library bytes ${input.file_content}`, "utf8")
  const personalKey = `w2-personal-${randomUUID()}`
  const postPersonal = (content, filename = personalFilename, key = personalKey, copies = 1) => page.evaluate(async ({ filename, content, key, copies }) => {
    const send = async () => {
      const form = new FormData()
      form.append("files", new File([content], filename, { type: "text/plain" }))
      const response = await fetch("/api/hub/library/files", {
        method: "POST", credentials: "same-origin", cache: "no-store",
        headers: { "Idempotency-Key": key }, body: form,
      })
      return { status: response.status, body: await response.json(), cacheControl: response.headers.get("cache-control") }
    }
    const results = await Promise.all(Array.from({ length: copies }, send))
    return copies === 1 ? results[0] : results
  }, { filename, content, key, copies })
  const concurrent = await postPersonal(personalBytes.toString("utf8"), personalFilename, personalKey, 2)
  assert(Array.isArray(concurrent) && concurrent.length === 2 &&
    concurrent.every((result) => result.status === 200 || (result.status === 409 && result.body?.error?.code === "idempotency_in_progress")) &&
    concurrent.some((result) => result.status === 200), "same-key concurrent personal POST was not serialized or replayed")
  const personalPost = concurrent.find((result) => result.status === 200)
  assert(concurrent.filter((result) => result.status === 200).every((result) =>
    result.body?.data?.file?.asset_id === personalPost.body?.data?.file?.asset_id), "concurrent personal POST returned distinct assets")
  const personalFile = personalPost.body?.data?.file
  assert(personalPost.status === 200 && personalFile?.kind === "file" && /^asset:[a-f0-9]{64}$/u.test(personalFile.asset_id) &&
    personalFile.filename === personalFilename && personalFile.mime_type === "text/plain" &&
    personalFile.size_bytes === String(personalBytes.length) && personalFile.content_sha256 === sha256(personalBytes) &&
    personalFile.scan_state === "clean" && typeof personalPost.body?.meta?.request_id === "string" &&
    personalPost.cacheControl?.includes("no-store"), "personal Product POST did not return CLEAN exact file")
  const personalReplay = await postPersonal(personalBytes.toString("utf8"))
  assert(personalReplay.status === 200 && personalReplay.body?.data?.file?.asset_id === personalFile.asset_id,
    "same-key personal Product POST did not replay original asset")
  const personalConflict = await postPersonal(`${personalBytes.toString("utf8")} changed`)
  assert(personalConflict.status === 409 && personalConflict.body?.error?.code === "idempotency_conflict",
    "same-key different personal content did not conflict")
  phase = "personal-file-infected"
  const infectedFilename = `infected-${input.filename}`
  const infectedKey = `w2-infected-${randomUUID()}`
  const eicar = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
  const infected = await postPersonal(eicar, infectedFilename, infectedKey)
  assert(infected.status === 422 && infected.body?.error?.code === "library_file_infected",
    "real ClamAV did not terminally deny infected personal file")
  const infectedReplay = await postPersonal(eicar, infectedFilename, infectedKey)
  assert(infectedReplay.status === 422 && infectedReplay.body?.error?.code === "library_file_infected",
    "infected personal file replay was not terminal")
  process.stderr.write("MILESTONE:personal-post-clean-replay-infected\n")

  phase = "personal-file-library-ui"
  await page.goto(`${input.web_origin}/app/library`, { waitUntil: "domcontentloaded", timeout: input.timeout_ms })
  await page.getByTestId("library-page").waitFor({ state: "visible", timeout: input.timeout_ms })
  assert(await page.getByRole("tab", { name: "Personal files", exact: true }).getAttribute("data-state") === "active",
    "personal files tab is not default")
  await page.locator(`[data-testid="library-files"] [data-asset-id="${personalFile.asset_id}"]`).waitFor({ state: "visible", timeout: input.timeout_ms })
  assert(await page.locator(`[data-testid="library-files"] [data-asset-id="${personalFile.asset_id}"]`).getByText(personalFilename).count() === 1,
    "personal file not visible in Library card")
  const libraryGet = libraryObservations.filter((item) => item.status === 200)
  assert(libraryGet.length > 0, "Library UI did not issue successful personal GET")
  const libraryPage = await libraryGet.at(-1).response.json()
  assert(libraryPage?.data?.items?.some((item) => item.asset_id === personalFile.asset_id &&
    item.content_sha256 === personalFile.content_sha256 && item.scan_state === "clean"), "Library GET omitted personal CLEAN asset")
  assert(!libraryPage?.data?.items?.some((item) => item.filename === infectedFilename), "Library GET exposed infected file")
  phase = "personal-file-visible-upload"
  const visibleFilename = `visible-${input.filename}`
  const visibleBytes = Buffer.from(`W2 visible personal file ${input.file_content}`, "utf8")
  const beforeVisibleGet = libraryObservations.filter((item) => item.status === 200).length
  const visiblePostPromise = page.waitForResponse((response) => new URL(response.url()).origin === input.web_origin &&
    new URL(response.url()).pathname === "/api/hub/library/files" && response.request().method() === "POST", { timeout: input.timeout_ms })
  await page.locator('#library-personal-file[type="file"]').setInputFiles({ name: visibleFilename, mimeType: "text/plain", buffer: visibleBytes })
  await page.getByRole("button", { name: "Upload personal file", exact: true }).click()
  const visiblePostResponse = await visiblePostPromise
  assert(visiblePostResponse.status() === 200, `visible personal upload returned ${visiblePostResponse.status()}`)
  const visiblePostBody = await visiblePostResponse.json()
  const visibleFile = visiblePostBody?.data?.file
  assert(visibleFile?.kind === "file" && /^asset:[a-f0-9]{64}$/u.test(visibleFile.asset_id) &&
    visibleFile.filename === visibleFilename && visibleFile.size_bytes === String(visibleBytes.length) &&
    visibleFile.content_sha256 === sha256(visibleBytes) && visibleFile.scan_state === "clean",
    "visible personal upload did not return CLEAN exact bytes")
  await page.locator(`[data-testid="library-files"] [data-asset-id="${visibleFile.asset_id}"]`).waitFor({ state: "visible", timeout: input.timeout_ms })
  assert(libraryObservations.filter((item) => item.status === 200).length > beforeVisibleGet,
    "visible personal upload did not refresh owner GET")
  const visibleGet = await libraryObservations.filter((item) => item.status === 200).at(-1).response.json()
  assert(visibleGet?.data?.items?.some((item) => item.asset_id === visibleFile.asset_id && item.scan_state === "clean"),
    "visible file card did not come from owner GET")
  process.stderr.write("MILESTONE:personal-visible-upload\n")
  const libraryGetCount = libraryObservations.filter((item) => item.status === 200).length
  phase = "personal-file-library-reload"
  await page.reload({ waitUntil: "domcontentloaded", timeout: input.timeout_ms })
  await page.locator(`[data-testid="library-files"] [data-asset-id="${personalFile.asset_id}"]`).waitFor({ state: "visible", timeout: input.timeout_ms })
  await page.locator(`[data-testid="library-files"] [data-asset-id="${visibleFile.asset_id}"]`).waitFor({ state: "visible", timeout: input.timeout_ms })
  assert(libraryObservations.filter((item) => item.status === 200).length > libraryGetCount,
    "Library reload did not issue durable personal GET")
  process.stderr.write("MILESTONE:personal-library-reload\n")

  async function verifyVisibleDownload(file, expectedBytes) {
    phase = "personal-download-click"
    const card = page.locator(`[data-testid="library-files"] [data-asset-id="${file.asset_id}"]`)
    const pathname = `/api/hub/library/files/${encodeURIComponent(file.asset_id)}/content`
    const responsePromise = page.waitForResponse((response) => new URL(response.url()).origin === input.web_origin &&
      new URL(response.url()).pathname === pathname && response.request().method() === "GET", { timeout: input.timeout_ms })
    const downloadPromise = page.waitForEvent("download", { timeout: input.timeout_ms })
    await card.getByTestId("library-file-download").click()
    const [response, download] = await Promise.all([responsePromise, downloadPromise])
    phase = "personal-download-http-status"
    assert(response.status() === 200, `visible personal download returned ${response.status()}`)
    const headers = response.headers()
    phase = "personal-download-cache"
    assert(headers["cache-control"]?.includes("no-store"), "visible personal download cache header drift")
    phase = "personal-download-referrer"
    assert(headers["referrer-policy"] === "no-referrer", "visible personal download referrer header drift")
    phase = "personal-download-nosniff"
    assert(headers["x-content-type-options"] === "nosniff", "visible personal download type header drift")
    phase = "personal-download-disposition"
    assert(headers["content-disposition"]?.startsWith("attachment;"), "visible personal download disposition drift")
    phase = "personal-download-request-id"
    assert(/^[\x20-\x7e]{1,128}$/u.test(headers["x-request-id"] ?? ""), "visible personal download request ID drift")
    phase = "personal-download-length"
    assert(Number(headers["content-length"]) === expectedBytes.length, "visible personal download length drift")
    phase = "personal-download-http-bytes"
    assert(sha256(await response.body()) === sha256(expectedBytes), "visible personal HTTP bytes drift")
    phase = "personal-download-filename"
    assert(download.suggestedFilename() === file.filename, "visible personal download filename drift")
    phase = "personal-download-saved-bytes"
    assert(sha256(readFileSync(await download.path())) === sha256(expectedBytes), "visible personal saved bytes drift")
    await download.delete()
  }
  phase = "personal-file-visible-download"
  await verifyVisibleDownload(personalFile, personalBytes)
  process.stderr.write("MILESTONE:personal-download-first\n")
  await verifyVisibleDownload(visibleFile, visibleBytes)
  process.stderr.write("MILESTONE:personal-visible-download\n")
  phase = "personal-file-mobile-layout"
  await page.setViewportSize({ width: 320, height: 720 })
  const mobile = await page.locator(`[data-testid="library-files"] [data-asset-id="${personalFile.asset_id}"]`).evaluate((card, filename) => {
    const title = [...card.querySelectorAll("span")].find((element) => element.textContent?.trim() === filename)
    const button = card.querySelector('[data-testid="library-file-download"]')
    const cardRect = card.getBoundingClientRect()
    const titleRect = title?.getBoundingClientRect()
    const buttonRect = button?.getBoundingClientRect()
    return { viewport: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth,
      cardLeft: cardRect.left, cardRight: cardRect.right, titleWidth: titleRect?.width ?? 0,
      buttonLeft: buttonRect?.left ?? -1, buttonRight: buttonRect?.right ?? 9999,
      titleVisible: title !== null && getComputedStyle(title).visibility !== "hidden", buttonVisible: button !== null && getComputedStyle(button).visibility !== "hidden" }
  }, personalFilename)
  assert(mobile.viewport === 320 && mobile.scroll <= mobile.viewport && mobile.cardLeft >= 0 && mobile.cardRight <= mobile.viewport &&
    mobile.titleVisible && mobile.titleWidth >= 120 && mobile.buttonVisible && mobile.buttonLeft >= 0 && mobile.buttonRight <= mobile.viewport,
  "personal file card is not readable at 320px")
  await page.setViewportSize({ width: 1280, height: 720 })
  process.stderr.write("MILESTONE:personal-mobile-layout\n")

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
  phase = "personal-file-member-private"
  await memberPage.goto(`${input.web_origin}/app/library`, { waitUntil: "domcontentloaded", timeout: input.timeout_ms })
  await memberPage.getByTestId("library-files-empty").waitFor({ state: "visible", timeout: input.timeout_ms })
  assert(await memberPage.getByText(personalFilename).count() === 0, "member Library rendered owner's personal file")
  assert(await memberPage.getByText(visibleFilename).count() === 0, "member Library rendered owner's visibly uploaded file")
  const memberLibrary = await memberPage.evaluate(async () => {
    const response = await fetch("/api/hub/library?kind=file&limit=50", { credentials: "same-origin", cache: "no-store" })
    return { status: response.status, body: await response.json() }
  })
  assert(memberLibrary.status === 200 && Array.isArray(memberLibrary.body?.data?.items) && memberLibrary.body.data.items.length === 0,
    "member personal Library GET was not an empty own scope")
  const memberDownload = await memberPage.evaluate(async (assetId) => {
    const response = await fetch(`/api/hub/library/files/${encodeURIComponent(assetId)}/content`,
      { credentials: "same-origin", cache: "no-store" })
    const body = await response.json()
    return { status: response.status, code: body?.error?.code, disposition: response.headers.get("content-disposition") }
  }, personalFile.asset_id)
  assert(memberDownload.status === 404 && typeof memberDownload.code === "string" &&
    memberDownload.disposition === null, "member received another subject's personal download")
  process.stderr.write("MILESTONE:member-private\n")
  await memberContext.close()
  await context.close()
  process.stdout.write(JSON.stringify({
    browser: "chromium", entry_url: `${input.web_origin}/login`, owner_subject: ownerSubject, member_subject: memberSubject,
    login: { owner: ownerLogin, member: memberLogin },
    project_id: project.id, project_slug: project.slug, project_post_status: createResponse.status(),
    asset_id: asset.asset_id, filename: asset.filename, content_sha256: asset.content_sha256,
    upload_status: uploadResponse.status(), owner_get_after_upload: true, owner_get_after_reload: true,
    personal: { asset_id: personalFile.asset_id, filename: personalFilename, content_sha256: personalFile.content_sha256,
      post_status: personalPost.status, replay_status: personalReplay.status, conflict_status: personalConflict.status,
      concurrent_statuses: concurrent.map((result) => result.status),
      infected_status: infected.status, infected_replay_status: infectedReplay.status,
      visible_asset_id: visibleFile.asset_id, visible_filename: visibleFilename,
      visible_content_sha256: visibleFile.content_sha256, visible_post_status: visiblePostResponse.status(), visible_owner_get: true,
      owner_get_after_post: true, owner_get_after_reload: true, visible_downloads: 2,
      member_get_status: memberLibrary.status, member_empty: true, member_download_status: memberDownload.status },
    screenshot: input.screenshot, privacy,
  }))
} catch {
  // Playwright exceptions can include signed OAuth URLs and input selectors.
  // Report only the fixed phase identifier; the runner retains safe ownership
  // metadata when a phase fails, never raw browser or process logs.
  process.stderr.write(`FAILURE_PHASE:${phase}\n`)
  process.exitCode = 1
} finally {
  await browser?.close().catch(() => undefined)
}
