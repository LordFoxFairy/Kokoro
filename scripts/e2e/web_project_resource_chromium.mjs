#!/usr/bin/env node
/** Real Chromium IAM → Project/personal flows → Agent Artifact Library download/private reload. */

import { createHash, randomUUID, X509Certificate } from "node:crypto"
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
  const fields = ["web_origin", "web_host", "web_root", "screenshot", "web_certificate", "owner_email", "owner_password", "member_email", "member_password", "filename", "file_content", "timeout_ms", "artifacts"]
  if (!value || typeof value !== "object" || Array.isArray(value) ||
      Object.keys(value).sort().join(",") !== fields.sort().join(",") ||
      !fields.filter((field) => field !== "timeout_ms" && field !== "artifacts").every((field) => typeof value[field] === "string" && value[field] !== "") ||
      !Number.isInteger(value.timeout_ms) || value.timeout_ms < 20_000 || value.timeout_ms > 600_000 ||
      !Array.isArray(value.artifacts) || value.artifacts.length !== 2 ||
      !value.artifacts.every((artifact) => artifact && typeof artifact === "object" && !Array.isArray(artifact) &&
        Object.keys(artifact).sort().join(",") === ["conversation_id", "artifact_id", "filename", "content", "content_sha256"].sort().join(",") &&
        [artifact.conversation_id, artifact.artifact_id].every((id) => typeof id === "string" && /^[A-Za-z0-9][A-Za-z0-9._:-]{0,190}$/u.test(id)) &&
        typeof artifact.filename === "string" && artifact.filename.length > 0 && typeof artifact.content === "string" &&
        artifact.content.length < 1024 && typeof artifact.content_sha256 === "string" && /^[a-f0-9]{64}$/u.test(artifact.content_sha256) &&
        sha256(Buffer.from(artifact.content, "utf8")) === artifact.content_sha256) ||
      value.artifacts[0].conversation_id === value.artifacts[1].conversation_id ||
      value.artifacts[0].artifact_id === value.artifacts[1].artifact_id) {
    throw new Error("invalid Chromium milestone input")
  }
  let origin
  try { origin = new URL(value.web_origin) }
  catch { throw new Error("invalid Chromium milestone input") }
  if (origin.origin !== value.web_origin || origin.protocol !== "https:" || origin.hostname !== value.web_host ||
      !path.isAbsolute(value.screenshot) || !path.isAbsolute(value.web_certificate) ||
      path.basename(value.web_certificate) !== "web.crt" || path.dirname(value.web_certificate) !== path.dirname(value.screenshot) ||
      !/^w2-[a-f0-9]{24}\.txt$/u.test(value.filename) || Buffer.byteLength(value.file_content) > 1024) {
    throw new Error("invalid Chromium milestone input")
  }
  return value
}

let browser
let phase = "parse-input"
try {
  const input = parseInput()
  phase = "certificate-pin"
  const certificate = new X509Certificate(readFileSync(input.web_certificate))
  assert(certificate.checkHost(input.web_host) === input.web_host, "isolated browser certificate host drift")
  const spki = certificate.publicKey.export({ type: "spki", format: "der" })
  const certificatePin = createHash("sha256").update(spki).digest("base64")
  phase = "launch-browser"
  const require = createRequire(pathToFileURL(path.join(input.web_root, "package.json")))
  const { chromium } = require("@playwright/test")
  browser = await chromium.launch({ headless: true, args: [`--host-resolver-rules=MAP ${input.web_host} 127.0.0.1`, "--no-proxy-server", `--ignore-certificate-errors-spki-list=${certificatePin}`] })
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

  phase = "artifact-library-owner"
  await page.getByRole("tab", { name: "Agent artifacts", exact: true }).click()
  const artifactCards = page.getByTestId("library-artifacts").getByRole("listitem")
  await artifactCards.first().waitFor({ state: "visible", timeout: input.timeout_ms })
  assert(await artifactCards.count() === 2, "owner Library did not render two delivered Artifacts")
  const artifactPages = await page.evaluate(async () => {
    const first = await fetch("/api/hub/library?kind=artifact&limit=1", { credentials: "same-origin", cache: "no-store" })
    const one = await first.json()
    const cursor = one?.data?.next_cursor
    if (first.status !== 200 || typeof cursor !== "string" || !cursor) return { first: first.status, one }
    const second = await fetch(`/api/hub/library?kind=artifact&limit=1&cursor=${encodeURIComponent(cursor)}`,
      { credentials: "same-origin", cache: "no-store" })
    return { first: first.status, one, second: second.status, two: await second.json() }
  })
  const firstArtifact = artifactPages.one?.data?.items?.[0]
  const secondArtifact = artifactPages.two?.data?.items?.[0]
  assert(artifactPages.first === 200 && artifactPages.second === 200 &&
    artifactPages.one?.data?.items?.length === 1 && artifactPages.two?.data?.items?.length === 1 &&
    artifactPages.two?.data?.next_cursor === null && firstArtifact && secondArtifact &&
    input.artifacts.every((fixture) => [firstArtifact, secondArtifact].some((item) =>
      item.conversation_id === fixture.conversation_id && item.artifact_id === fixture.artifact_id &&
      item.filename === fixture.filename && item.content_sha256 === fixture.content_sha256)),
  "owner Artifact cursor pages did not preserve both binary identities")
  const ordered = await page.evaluate(async () => {
    const response = await fetch("/api/hub/library?kind=artifact&limit=50", { credentials: "same-origin", cache: "no-store" })
    return { status: response.status, body: await response.json() }
  })
  assert(ordered.status === 200 && ordered.body?.data?.items?.length === 2, "owner Artifact Library page drift")
  phase = "artifact-click-download"
  for (const [index, item] of ordered.body.data.items.entries()) {
    phase = `artifact-${index + 1}-fixture`
    const fixture = input.artifacts.find((candidate) => candidate.conversation_id === item.conversation_id &&
      candidate.artifact_id === item.artifact_id)
    assert(fixture, "visible Artifact lacks exact fixture identity")
    const selector = `/api/hub/library/artifacts/${encodeURIComponent(item.conversation_id)}/${encodeURIComponent(item.artifact_id)}`
    const eventTimeout = Math.min(input.timeout_ms, 30_000)
    const detailPromise = page.waitForResponse((response) => new URL(response.url()).pathname === selector &&
      response.request().method() === "GET", { timeout: eventTimeout })
    const downloadPromise = page.waitForEvent("download", { timeout: eventTimeout })
    const observed = Promise.allSettled([detailPromise, downloadPromise])
    phase = `artifact-${index + 1}-click-button`
    await artifactCards.nth(index).getByRole("button", { name: "Download Delivered work", exact: true }).click()
    phase = `artifact-${index + 1}-await-events`
    const [detailResult, downloadResult] = await observed
    phase = `artifact-${index + 1}-detail-observed`
    assert(detailResult.status === "fulfilled", "visible Artifact detail request absent")
    const detail = detailResult.value
    phase = `artifact-${index + 1}-detail-http-${detail.status()}`
    assert(detail.status() === 200, `visible Artifact detail returned ${detail.status()}`)
    phase = `artifact-${index + 1}-detail-wire`
    const detailPayload = await detail.json()
    assert(detailPayload?.data?.artifact_id === fixture.artifact_id &&
      detailPayload?.data?.conversation_id === fixture.conversation_id,
      "visible Artifact detail did not resolve binary identity")
    phase = `artifact-${index + 1}-download-observed`
    assert(downloadResult.status === "fulfilled", "visible Artifact browser download event absent")
    const download = downloadResult.value
    const expected = Buffer.from(fixture.content, "utf8")
    phase = `artifact-${index + 1}-suggested-filename`
    assert(download.suggestedFilename() === fixture.filename,
      "visible Artifact browser download filename drift")
    phase = `artifact-${index + 1}-authenticated-content`
    const content = await page.evaluate(async (path) => {
      const response = await fetch(path, { credentials: "same-origin", cache: "no-store" })
      const headers = response.headers
      const bytes = await response.arrayBuffer()
      const digest = bytes.byteLength <= 1024
        ? [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))].map((byte) => byte.toString(16).padStart(2, "0")).join("")
        : null
      return { status: response.status, bodySha: digest, bodyLength: bytes.byteLength,
        cacheNoStore: headers.get("cache-control")?.includes("no-store") === true,
        referrerNoReferrer: headers.get("referrer-policy") === "no-referrer",
        nosniff: headers.get("x-content-type-options") === "nosniff",
        attachment: headers.get("content-disposition")?.startsWith("attachment;") === true,
        requestIdValid: /^[\x20-\x7e]{1,128}$/u.test(headers.get("x-request-id") ?? ""),
        contentLength: Number(headers.get("content-length")) }
    }, `${selector}/content`)
    phase = `artifact-${index + 1}-content-status`
    assert(content.status === 200, `authenticated Artifact content returned ${content.status}`)
    phase = `artifact-${index + 1}-content-headers`
    assert(content.cacheNoStore && content.referrerNoReferrer && content.nosniff && content.attachment &&
      content.requestIdValid && content.contentLength === expected.length && content.bodyLength === expected.length,
    "authenticated Artifact attachment security headers drift")
    phase = `artifact-${index + 1}-content-bytes`
    assert(content.bodySha === fixture.content_sha256,
      "authenticated Artifact content changed original bytes")
    phase = `artifact-${index + 1}-saved-download`
    assert(await download.failure() === null,
      "visible Artifact browser download failed")
    assert(sha256(readFileSync(await download.path())) === fixture.content_sha256,
      "visible Artifact browser download changed original bytes")
    await download.delete()
  }
  process.stderr.write("MILESTONE:artifact-two-click-downloads\n")
  phase = "artifact-reload-mobile-source"
  await page.reload({ waitUntil: "domcontentloaded", timeout: input.timeout_ms })
  await page.getByRole("tab", { name: "Agent artifacts", exact: true }).click()
  await artifactCards.first().waitFor({ state: "visible", timeout: input.timeout_ms })
  assert(await artifactCards.count() === 2, "Artifact Library lost delivered cards after reload")
  await page.setViewportSize({ width: 320, height: 720 })
  const artifactMobile = await artifactCards.first().evaluate((card) => {
    const title = card.querySelector("[class*=cardTitle]")
    const download = card.querySelector("button[aria-label^='Download ']")
    const rect = card.getBoundingClientRect()
    const button = download?.getBoundingClientRect()
    return { viewport: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth,
      left: rect.left, right: rect.right, titleWidth: title?.getBoundingClientRect().width ?? 0,
      buttonLeft: button?.left ?? -1, buttonRight: button?.right ?? 9999,
      titleVisible: title !== null && getComputedStyle(title).visibility !== "hidden" }
  })
  assert(artifactMobile.viewport === 320 && artifactMobile.scroll <= 320 && artifactMobile.left >= 0 &&
    artifactMobile.right <= 320 && artifactMobile.titleVisible && artifactMobile.titleWidth >= 70 &&
    artifactMobile.buttonLeft >= 0 && artifactMobile.buttonRight <= 320, "Artifact card is not usable at 320px")
  await page.setViewportSize({ width: 1280, height: 720 })
  await artifactCards.first().getByRole("button", { name: "Open source session", exact: true }).click()
  await page.waitForURL((url) => url.origin === input.web_origin && url.searchParams.get("conversation") === ordered.body.data.items[0].conversation_id,
    { timeout: input.timeout_ms })
  process.stderr.write("MILESTONE:artifact-reload-mobile-source\n")

  // Library is not the Chat delivery surface. The same durable binary ID must
  // hydrate a conversation card and Canvas after crossing back into Chat.
  phase = "artifact-chat-snapshot"
  const sourceArtifact = input.artifacts.find((candidate) =>
    candidate.conversation_id === ordered.body.data.items[0].conversation_id)
  assert(sourceArtifact, "source conversation lacks exact Artifact fixture")
  const sourceSnapshotPath = `/api/session/sessions/${encodeURIComponent(sourceArtifact.conversation_id)}`
  const sourceSnapshot = await page.evaluate(async (target) => {
    const response = await fetch(target, { credentials: "same-origin", cache: "no-store" })
    return { status: response.status, body: await response.json() }
  }, sourceSnapshotPath)
  const sourceDeliveries = sourceSnapshot.body?.deliveries
  phase = "artifact-chat-snapshot-status"
  assert(sourceSnapshot.status === 200, "owner Chat snapshot unavailable")
  phase = "artifact-chat-snapshot-count"
  assert(Array.isArray(sourceDeliveries) && sourceDeliveries.length === 1,
    "owner Chat snapshot lost durable Delivery")
  phase = "artifact-chat-snapshot-watermark"
  assert(sourceSnapshot.body?.deliveries_has_more === false &&
    typeof sourceSnapshot.body?.event_watermark === "string",
  "owner Chat snapshot watermark drift")
  phase = "artifact-chat-snapshot-identity"
  assert(sourceDeliveries[0].conversation_id === sourceArtifact.conversation_id &&
    sourceDeliveries[0].artifact_id === sourceArtifact.artifact_id,
  "owner Chat snapshot binary identity drift")
  phase = "artifact-chat-snapshot-metadata"
  assert(sourceDeliveries[0].title === "Delivered work" &&
    sourceDeliveries[0].size === Buffer.byteLength(sourceArtifact.content, "utf8"),
  "owner Chat snapshot Delivery metadata drift")
  phase = "artifact-chat-card"
  const chatDelivery = page.getByRole("button", { name: `Open delivery ${sourceDeliveries[0].title}`, exact: true })
  await chatDelivery.waitFor({ state: "visible", timeout: input.timeout_ms })
  assert(await chatDelivery.count() === 1, "source Chat rendered duplicate Delivery cards")
  phase = "artifact-chat-canvas"
  await chatDelivery.click()
  const canvas = page.getByRole("complementary", { name: `canvas details ${sourceDeliveries[0].title}`, exact: true })
  await canvas.waitFor({ state: "visible", timeout: input.timeout_ms })
  assert(await canvas.getByRole("heading", { name: sourceDeliveries[0].title, exact: true }).count() === 1,
    "Chat Canvas did not resolve binary Delivery metadata")
  const canvasDownloadPromise = page.waitForEvent("download", { timeout: input.timeout_ms })
  await canvas.getByRole("button", { name: "Download", exact: true }).click()
  const canvasDownload = await canvasDownloadPromise
  assert(canvasDownload.suggestedFilename() === sourceArtifact.filename &&
    await canvasDownload.failure() === null &&
    sha256(readFileSync(await canvasDownload.path())) === sourceArtifact.content_sha256,
  "Chat Canvas native download lost original Artifact bytes")
  await canvasDownload.delete()
  phase = "artifact-chat-reload"
  await page.reload({ waitUntil: "domcontentloaded", timeout: input.timeout_ms })
  await chatDelivery.waitFor({ state: "visible", timeout: input.timeout_ms })
  assert(await chatDelivery.count() === 1, "Chat refresh lost or duplicated durable Delivery")
  process.stderr.write("MILESTONE:artifact-chat-snapshot-canvas-reload\n")

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
  phase = "artifact-member-private"
  await memberPage.getByRole("tab", { name: "Agent artifacts", exact: true }).click()
  await memberPage.getByTestId("library-empty-state").waitFor({ state: "visible", timeout: input.timeout_ms })
  const memberArtifact = await memberPage.evaluate(async ({ conversationId, artifactId }) => {
    const options = { credentials: "same-origin", cache: "no-store" }
    const list = await fetch("/api/hub/library?kind=artifact&limit=50", options)
    const listed = await list.json()
    const selector = `/api/hub/library/artifacts/${encodeURIComponent(conversationId)}/${encodeURIComponent(artifactId)}`
    const detail = await fetch(selector, options)
    const content = await fetch(`${selector}/content`, options)
    return { listStatus: list.status, items: listed?.data?.items, detailStatus: detail.status,
      contentStatus: content.status, disposition: content.headers.get("content-disposition") }
  }, { conversationId: input.artifacts[0].conversation_id, artifactId: input.artifacts[0].artifact_id })
  assert(memberArtifact.listStatus === 200 && Array.isArray(memberArtifact.items) && memberArtifact.items.length === 0 &&
    memberArtifact.detailStatus === 404 && memberArtifact.contentStatus === 404 && memberArtifact.disposition === null,
  "same-tenant other subject reached private Agent Artifact")
  const memberChat = await memberPage.evaluate(async (conversationId) => {
    const response = await fetch(`/api/session/sessions/${encodeURIComponent(conversationId)}`,
      { credentials: "same-origin", cache: "no-store" })
    return { status: response.status, body: await response.json() }
  }, sourceArtifact.conversation_id)
  assert(memberChat.status === 404 && !Array.isArray(memberChat.body?.deliveries) &&
    !Array.isArray(memberChat.body?.data?.deliveries),
    "same-tenant other subject reached private Chat Delivery snapshot")
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
    artifacts: { visible_downloads: 2, owner_pages: 2, owner_after_reload: true, member_empty: true,
      member_detail_status: memberArtifact.detailStatus, member_content_status: memberArtifact.contentStatus,
      mobile_no_overflow: true, chat_snapshot: true, chat_canvas_native_download: true,
      chat_after_reload: true, member_chat_status: memberChat.status },
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
