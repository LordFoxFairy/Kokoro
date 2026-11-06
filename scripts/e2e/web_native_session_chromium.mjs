/** Real Chromium authentication journeys. Private NDJSON is the only broker channel. */
import https from 'node:https';
import {spawn} from 'node:child_process';
import {mkdtemp, readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {performance} from 'node:perf_hooks';

const MAX_LINE = 16_384;
let buffer = Buffer.alloc(0);
let waiting;
const queued = [];
let inputError;
function fail() { throw new Error('browser journey failed'); }
function requireFact(value) { if (!value) fail(); }
function inputFailure() {
  inputError = new Error('private protocol failed');
  if (waiting) { waiting.reject(inputError); waiting = undefined; }
}
function startInput() {
process.stdin.on('data', chunk => {
  buffer = Buffer.concat([buffer, chunk]);
  while (buffer.includes(10)) {
    const end = buffer.indexOf(10);
    if (end > MAX_LINE) return inputFailure();
    let value;
    try { value = JSON.parse(buffer.subarray(0, end).toString('utf8')); }
    catch { return inputFailure(); }
    buffer = buffer.subarray(end + 1);
    if (waiting) { waiting.resolve(value); waiting = undefined; }
    else if (queued.length < 2) queued.push(value);
    else return inputFailure();
  }
  if (buffer.length > MAX_LINE) inputFailure();
});
process.stdin.on('end', inputFailure);
process.stdin.on('error', inputFailure);
}
async function receive() {
  if (inputError) throw inputError;
  if (queued.length) return queued.shift();
  requireFact(!waiting);
  let timer;
  try {
    return await new Promise((resolve, reject) => {
      timer = setTimeout(() => { waiting = undefined; reject(new Error('private protocol timeout')); }, 10_000);
      waiting = {resolve, reject};
    });
  } finally { clearTimeout(timer); }
}
async function emit(value) {
  const line = JSON.stringify(value) + '\n';
  requireFact(Buffer.byteLength(line) <= MAX_LINE);
  await new Promise((resolve, reject) => process.stdout.write(line, error => error ? reject(error) : resolve()));
}
async function owner(request) {
  await emit({kind: 'owner_command', request});
  const result = await receive();
  requireFact(result && result.kind !== 'error');
  return result;
}
async function inspect(slot) {
  const result = await owner({command: 'inspect_browser_session', slot});
  requireFact(result.kind === 'browser_session' && result.slot === slot);
  return {exists: result.exists, unexpired: result.unexpired, member: result.member, active_tenant: result.active_tenant};
}
function ownerIs(value, exists, member, active, unexpired = exists) {
  requireFact(value.exists === exists && value.unexpired === unexpired && value.member === member && value.active_tenant === active);
  return value;
}
const issuerName = /^(?:__Secure-)?kokoro-issuer\.session_token$/;
async function issuerCookies(context, origin) {
  return (await context.cookies(origin)).filter(cookie => issuerName.test(cookie.name));
}
async function bind(context, origin, slot) {
  const cookies = await issuerCookies(context, origin);
  requireFact(cookies.length === 1);
  const cookie = `${cookies[0].name}=${cookies[0].value}`;
  await owner({command: 'bind_browser_session', slot, cookie});
  return cookie;
}
async function read(page, path) {
  return page.evaluate(async path => {
    const response = await fetch(path, {cache: 'no-store', redirect: 'error', signal: AbortSignal.timeout(5000)});
    const body = await response.json();
    return {status: response.status, body};
  }, path);
}
/** Smoke oracle for the owner observation, not a second application decoder. */
export function requireSessionObservation(response, authenticated, identity) {
  const keys = (value, expected) => value !== null && typeof value === 'object' && !Array.isArray(value)
    && Object.keys(value).length === expected.length && expected.every(key => Object.hasOwn(value, key));
  requireFact(response.status === 200 && typeof authenticated === 'boolean' && keys(response.body, ['data']));
  const data = response.body.data;
  requireFact(keys(data, authenticated ? ['authenticated', 'subject', 'tenant_id', 'expires_at'] : ['authenticated']));
  requireFact(data.authenticated === authenticated);
  if (authenticated) {
    requireFact(typeof identity?.subject === 'string' && identity.subject.length > 0
      && typeof identity.tenant_id === 'string' && identity.tenant_id.length > 0
      && data.subject === identity.subject && data.tenant_id === identity.tenant_id);
    requireFact(typeof data.expires_at === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$/.test(data.expires_at));
    const expiry = Date.parse(data.expires_at);
    requireFact(Number.isFinite(expiry) && expiry > Date.now()
      && new Date(expiry).toISOString().slice(0, 19) === data.expires_at.slice(0, 19));
  }
  return data;
}
export function requireAdminObservation(response, identity) {
  const value = response.body;
  requireFact(response.status === 200 && value !== null && typeof value === 'object' && !Array.isArray(value)
    && Object.keys(value).length === 4 && ['authenticated', 'subject', 'tenant_id', 'platform_admin'].every(key => Object.hasOwn(value, key))
    && value.authenticated === true && value.platform_admin === true
    && typeof identity.subject === 'string' && identity.subject.length > 0 && value.subject === identity.subject
    && typeof identity.tenant_id === 'string' && identity.tenant_id.length > 0 && value.tenant_id === identity.tenant_id);
  return true;
}
export function requirePlatformAdminObservation(record, command, enabled, version, audits) {
  requireFact(record !== null && typeof record === 'object' && !Array.isArray(record)
    && Object.keys(record).length === 5 && ['kind', 'command', 'enabled', 'version', 'succeeded_audits'].every(key => Object.hasOwn(record, key))
    && record.kind === 'browser_platform_admin' && record.command === command && record.enabled === enabled
    && Number.isInteger(record.version) && record.version === version
    && Number.isInteger(record.succeeded_audits) && record.succeeded_audits === audits);
  return {enabled: record.enabled, version: record.version, succeeded_audits: record.succeeded_audits};
}
// BetterAuth's locked owner rule allows three sign-in attempts per ten seconds.
// After the third completion, wait a full window after that latest completion.
export async function waitForLoginSlot(completed, deadline, clock = {
  now: () => performance.now(), sleep: ms => new Promise(resolve => setTimeout(resolve, ms)),
}) {
  if (completed.length < 3) return;
  const delay = Math.max(0, completed.at(-1) + 10_001 - clock.now());
  requireFact(clock.now() + delay < deadline);
  if (delay) await clock.sleep(delay);
  completed.length = 0;
}
// IAM native admission shares a 100/60s bucket across these fixture sessions.
// Separate independent journeys before opening their contexts, not after revocation
// or in response to a 429; this wait consumes the existing overall budget.
export async function waitForNativeAdmissionWindow(deadline, clock = {
  now: () => performance.now(), sleep: ms => new Promise(resolve => setTimeout(resolve, ms)),
}) {
  const startedAt = clock.now();
  requireFact(startedAt + 60_001 < deadline);
  await clock.sleep(60_001);
  const completedAt = clock.now();
  // The extra millisecond absorbs timer rounding; the full owner window must elapse.
  requireFact(completedAt - startedAt >= 60_000 && completedAt < deadline);
}
const loginCompletions = [];
let overallDeadline;
async function login(page, config, fixture) {
  await waitForLoginSlot(loginCompletions, overallDeadline);
  await page.goto(config.origin + '/login?return_to=%2Fapp', {waitUntil: 'domcontentloaded'});
  await page.locator('input[name="email"][type="email"]').fill(fixture.email);
  await page.locator('input[name="password"][type="password"]').fill(fixture.password);
  const response = page.waitForResponse(r => new URL(r.url()).pathname === '/auth/sign-in' && r.request().method() === 'POST');
  await page.getByRole('button', {name: '登录', exact: true}).click();
  const status = (await response).status();
  loginCompletions.push(performance.now());
  requireFact(status === 303);
  await page.waitForURL(url => url.pathname === '/app');
  await page.getByTestId('rail-utility-account').waitFor({state: 'visible'});
  return status;
}
async function openSettings(page) {
  await page.getByTestId('rail-utility-account').click();
  await page.getByRole('menuitem', {name: 'Account', exact: true}).click();
  await page.getByTestId('settings-modal').waitFor({state: 'visible'});
  await page.getByTestId('settings-account').waitFor({state: 'visible'});
}
async function profileSentinel(page, profile, expect) {
  requireFact(profile && typeof profile.subject === 'string' && typeof profile.name === 'string' && profile.name.length > 0);
  requireFact(typeof profile.email === 'string' && profile.email.length > 0);
  const card = page.getByTestId('settings-account');
  await expect(card.getByRole('textbox', {name: 'Full name', exact: true})).toHaveValue(profile.name);
  await expect(card.getByText(profile.email, {exact: true})).toBeVisible();
  return true;
}
async function profileVisible(page, profile, expect) {
  await profileSentinel(page, profile, expect);
  await expect(page.getByTestId('settings-account').getByRole('textbox', {name: 'Full name', exact: true})).toBeEnabled();
  return true;
}
async function openProfile(page, expect) {
  const response = page.waitForResponse(r => new URL(r.url()).pathname === '/api/account/profile' && r.request().method() === 'GET');
  await openSettings(page);
  const received = await response;
  requireFact(received.status() === 200);
  const profile = (await received.json()).data;
  await profileVisible(page, profile, expect);
  return {profile, status: received.status()};
}
export async function retired(page, profile, expect, anonymous = false, clock = {now: () => performance.now()}) {
  if (anonymous) {
    // A revoked login is now an explicit anonymous observation. The product gate
    // replaces the private page with login rather than retaining an unavailable shell.
    const deadline = clock.now() + 3000;
    const budget = () => {
      const timeout = deadline - clock.now();
      requireFact(timeout > 0);
      return {timeout};
    };
    const origin = new URL(page.url()).origin;
    const signIn = url => url.origin === origin && url.pathname === '/auth/sign-in';
    await page.waitForURL(signIn, budget());
    await expect(page.locator('input[name="password"][type="password"]')).toBeVisible(budget());
    await expect(page.getByRole('textbox', {name: 'Full name', exact: true})).toHaveCount(0, budget());
    if (profile.name) await expect(page.getByText(profile.name, {exact: true})).toHaveCount(0, budget());
    if (profile.email) await expect(page.getByText(profile.email, {exact: true})).toHaveCount(0, budget());
    await expect(page.getByText(profile.subject, {exact: true})).toHaveCount(0, budget());
    requireFact(signIn(new URL(page.url())) && clock.now() <= deadline);
    return true;
  }
  // A qualification refusal may unmount the private card, not the public shell.
  const deadline = clock.now() + 3000;
  const budget = () => {
    const timeout = deadline - clock.now();
    requireFact(timeout > 0);
    return {timeout};
  };
  const onProductPage = () => /^\/app(?:\/|$)/.test(new URL(page.url()).pathname);
  requireFact(onProductPage());
  const card = page.getByTestId('settings-account');
  await expect.poll(async () => {
    const cards = await card.count();
    // One immediate DOM snapshot also permits removal during the observation.
    const names = await page.getByRole('textbox', {name: 'Full name', exact: true}).evaluateAll(elements =>
      elements.map(element => element.matches(':disabled') && 'value' in element && element.value === '—'));
    return cards === 0 ? names.length === 0 : cards === 1 && names.length === 1 && names[0];
  }, budget()).toBe(true);
  if (profile.email) await expect(page.getByText(profile.email, {exact: true})).toHaveCount(0, budget());
  await expect(page.getByText(profile.subject, {exact: true})).toHaveCount(0, budget());
  await expect(page.locator('input[name="password"][type="password"]')).toHaveCount(0, budget());
  await expect(page.locator('[data-desktop-web="true"][data-web-skin="kokoro"]')).toBeVisible(budget());
  requireFact(onProductPage() && clock.now() <= deadline);
  return true;
}
async function preparePeer(context, origin) {
  const peer = await context.newPage();
  await peer.goto(origin + '/api/fixture-origin');
  return peer;
}
export async function focusProbe(page, peer, status, observation, identity, clock = {now: () => performance.now()}) {
  // Playwright's fixed focus override hides real tab activation. Keep these CDP
  // sessions owned by the context until close; detaching would restore the override.
  for (const target of [page, peer]) {
    const session = await target.context().newCDPSession(target);
    await session.send('Emulation.setFocusEmulationEnabled', {enabled: false});
  }
  // Only browser focus/visibility events; no synthetic dispatchEvent or private React hook.
  await peer.bringToFront();
  let acknowledge;
  const focused = new Promise(resolve => { acknowledge = resolve; });
  let binding;
  let timer;
  let live = true;
  let acknowledged = false;
  const deadline = clock.now() + 3000;
  const budget = () => {
    const timeout = deadline - clock.now();
    requireFact(timeout > 0);
    return timeout;
  };
  const expired = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error('browser journey failed')), budget());
  });
  const retireDocument = () => page.evaluate(() => window.__nativeSmokeFocusCleanup?.());
  const observationResult = (async () => {
    // Playwright 1.62 bindings survive navigation; the ACK is owned by Node,
    // not a flag in the document that an anonymous observation can replace.
    const acquired = await page.exposeBinding('__nativeSmokeTrustedFocus', source => {
      if (live && clock.now() <= deadline && source.page === page && source.frame === page.mainFrame()) {
        acknowledged = true;
        acknowledge();
      }
    });
    if (!live || clock.now() > deadline) {
      await acquired.dispose();
      fail();
    }
    binding = acquired;
    await page.evaluate(() => {
      const observe = event => {
        if (event.isTrusted && document.visibilityState === 'visible') {
          cleanup();
          void window.__nativeSmokeTrustedFocus?.().catch(() => {});
        }
      };
      const cleanup = () => {
        window.removeEventListener('focus', observe);
        document.removeEventListener('visibilitychange', observe);
        delete window.__nativeSmokeFocusCleanup;
      };
      window.__nativeSmokeFocusCleanup = cleanup;
      window.addEventListener('focus', observe, {once: true});
      document.addEventListener('visibilitychange', observe, {once: true});
    });
    if (!live || clock.now() > deadline) {
      // A late installation may only retire its own listeners, never activate.
      await retireDocument().catch(() => {});
      fail();
    }
    const response = page.waitForResponse(r => new URL(r.url()).pathname === '/api/auth/session', {timeout: budget()});
    const [received] = await Promise.all([response, focused, Promise.resolve().then(() => page.bringToFront())]);
    requireFact(live && clock.now() <= deadline);
    requireFact(received.status() === status);
    const body = await received.json();
    requireFact(live && clock.now() <= deadline);
    if (status === 200) requireSessionObservation({status: received.status(), body}, observation, identity);
    else requireFact(typeof observation === 'string' && body?.error?.code === observation);
    return true;
  })();
  let result;
  let failed = false;
  let failure;
  try {
    try { result = await Promise.race([observationResult, expired]); }
    catch (error) { failed = true; failure = error; }
    live = false;
    // A qualified callback already removed both DOM listeners before its ACK.
    // Otherwise attempt DOM retirement and binding disposal independently: a
    // navigating/hung document must not block the latter or extend this budget.
    const cleanup = Promise.allSettled([
      ...(acknowledged ? [] : [Promise.resolve().then(retireDocument)]),
      ...(binding ? [Promise.resolve().then(() => binding.dispose())] : []),
    ]);
    let cleaned;
    try { cleaned = await Promise.race([cleanup, expired]); }
    catch (error) { if (!failed) { failed = true; failure = error; } }
    requireFact(clock.now() <= deadline);
    if (failed) throw failure;
    requireFact(cleaned?.every(entry => entry.status === 'fulfilled') === true);
    return result;
  } finally {
    live = false;
    clearTimeout(timer);
  }
}
export async function retireAdminOnFocus(page, peer, identity, expect, clock = {now: () => performance.now()}) {
  const deadline = clock.now() + 3000;
  const budget = () => {
    const timeout = deadline - clock.now();
    requireFact(timeout > 0);
    return {timeout};
  };
  let timer;
  try {
    return await Promise.race([
      (async () => {
        const response = page.waitForResponse(r => new URL(r.url()).pathname === '/manage/api/v1/me' && r.request().method() === 'GET', budget());
        const [received] = await Promise.all([response, focusProbe(page, peer, 200, true, identity)]);
        const body = await received.json();
        requireFact(received.status() === 403 && body !== null && typeof body === 'object'
          && Object.keys(body).length === 1 && Object.hasOwn(body, 'error') && body.error !== null
          && typeof body.error === 'object' && Object.keys(body.error).length === 1 && body.error.code === 'admin_access_denied');
        await expect(page.getByText(identity.subject, {exact: true})).toHaveCount(0, budget());
        await expect(page.getByText('运营概览', {exact: true})).toHaveCount(0, budget());
        await expect(page.getByRole('heading', {name: 'Kokoro 管理后台', exact: true})).toBeVisible(budget());
        requireFact(clock.now() <= deadline);
        return true;
      })(),
      new Promise((_, reject) => { timer = setTimeout(() => reject(new Error('browser journey failed')), budget().timeout); }),
    ]);
  } finally { clearTimeout(timer); }
}

async function sharedAdminJourney(context, config, identity, expect) {
  const observe = async (command, enabled, version, audits) => requirePlatformAdminObservation(
    await owner({command}), command, enabled, version, audits,
  );
  const initialOwner = await observe('inspect_browser_platform_admin', false, 0, 0);
  const grantedOwner = await observe('grant_browser_platform_admin', true, 1, 1);
  await observe('inspect_browser_platform_admin', true, 1, 1);
  const before = await issuerCookies(context, config.origin);
  requireFact(before.length === 1);
  let signIns = 0;
  const recordSignIn = request => {
    const url = new URL(request.url());
    if (url.origin === config.origin && url.pathname === '/auth/sign-in' && request.method() === 'POST') signIns++;
  };
  context.on('request', recordSignIn);
  const admin = await context.newPage();
  let peer;
  try {
    await admin.goto(config.origin + '/manage', {waitUntil: 'domcontentloaded'});
    await admin.waitForURL(url => url.pathname === '/manage/overview');
    const current = await read(admin, '/manage/api/v1/me');
    const matches = requireAdminObservation(current, identity);
    await expect(admin.getByText(identity.subject, {exact: true}).first()).toBeVisible();
    await expect(admin.getByText('运营概览', {exact: true}).first()).toBeVisible();
    const after = await issuerCookies(context, config.origin);
    const shared = after.length === 1 && after[0].name === before[0].name && after[0].value === before[0].value;
    requireFact(shared && signIns === 0);
    const revokedOwner = await observe('revoke_browser_platform_admin', false, 2, 2);
    await observe('inspect_browser_platform_admin', false, 2, 2);
    const denied = await read(admin, '/manage/api/v1/me');
    requireFact(denied.status === 403 && denied.body?.error?.code === 'admin_access_denied');
    peer = await preparePeer(context, config.origin);
    const privateRetired = await retireAdminOnFocus(admin, peer, identity, expect);
    const session = await read(admin, '/api/auth/session');
    requireSessionObservation(session, true, identity);
    const projects = await read(admin, '/api/session/projects');
    requireFact(projects.status === 200 && signIns === 0);
    const productOwner = ownerIs(await inspect('primary'), true, true, 'fixed');
    return {
      initial_owner: initialOwner, granted_owner: grantedOwner, shared_issuer_cookie: shared,
      additional_sign_in_requests: signIns, admin_me_status: current.status, admin_identity_matches: matches,
      admin_shell_visible: true, revoked_owner: revokedOwner, revoked_admin_me_status: denied.status,
      revoked_admin_error_code: denied.body.error.code, private_ui_retired: privateRetired,
      product_session_status: session.status, product_authenticated: session.body.data.authenticated,
      projects_status: projects.status, product_owner: productOwner,
    };
  } finally {
    context.off('request', recordSignIn);
    await peer?.close();
    await admin.close();
  }
}
export async function replay(config, cookie) {
  const origin = new URL(config.origin);
  return new Promise((resolve, reject) => {
    const request = https.request({
      hostname: '127.0.0.1', port: config.port, servername: origin.hostname,
      rejectUnauthorized: false, path: '/api/session/projects', method: 'GET',
      headers: {host: origin.host, origin: config.origin, cookie},
    }, response => {
      let length = 0;
      const chunks = [];
      response.on('data', chunk => {
        length += chunk.length;
        if (length > MAX_LINE) { response.destroy(); reject(new Error('replay response invalid')); }
        else chunks.push(chunk);
      });
      response.once('error', () => reject(new Error('replay response invalid')));
      response.once('end', () => {
        try { resolve({status: response.statusCode, body: JSON.parse(Buffer.concat(chunks).toString('utf8'))}); }
        catch { reject(new Error('replay response invalid')); }
      });
    });
    request.setTimeout(5000, () => request.destroy(new Error('replay timeout')));
    request.once('error', reject);
    request.end();
  });
}

/** Hold bytes from the genuine owner response; never manufacture success data. */
export async function profileBarrier(page, config) {
  const origin = new URL(config.origin);
  requireFact(origin.protocol === 'https:' && origin.origin === config.origin);
  requireFact(Number.isInteger(config.port) && config.port > 0 && config.port <= 65535);
  let release;
  let upstreamReady;
  let upstreamReject;
  const ready = new Promise((resolve, reject) => { upstreamReady = resolve; upstreamReject = reject; });
  const gate = new Promise(resolve => { release = resolve; });
  let request;
  let started;
  let observation;
  let upstreamStatus;
  let completionResolve;
  const completed = new Promise(resolve => { completionResolve = resolve; });
  const failed = candidate => {
    if (candidate === request && candidate.failure()?.errorText === 'net::ERR_ABORTED') observation = 'cancelled';
  };
  const finished = candidate => { if (candidate === request && observation !== 'cancelled') observation = 'delivered_and_retired'; };
  page.on('requestfailed', failed);
  page.on('requestfinished', finished);
  const handler = async route => {
    if (request) return route.continue();
    request = route.request();
    started = performance.now();
    try {
      requireFact(request.method() === 'GET' && request.url() === origin.origin + '/api/account/profile');
      // route.fetch uses Node, not Chromium's host-resolver-rules. Preserve the
      // intercepted request's cookies and virtual host at our owned TLS proxy.
      const response = await route.fetch({
        url: `https://127.0.0.1:${config.port}/api/account/profile`,
        headers: {...await request.allHeaders(), host: origin.host},
        timeout: 4500, maxRetries: 0, maxRedirects: 0,
      });
      upstreamStatus = response.status();
      requireFact(upstreamStatus === 200);
      // Parse without editing, ensuring this barrier captured a genuine profile.
      requireFact(typeof (await response.json()).data?.subject === 'string');
      upstreamReady();
      await gate;
      if (observation !== 'cancelled') await route.fulfill({response});
      else await route.abort().catch(() => undefined);
    } catch {
      upstreamReject(new Error('profile barrier failed'));
      if (observation !== 'cancelled') observation = 'failed';
    } finally { completionResolve(); }
  };
  await page.route('**/api/account/profile', handler);
  return {
    ready,
    async release() {
      // Prove retirement happened before the product's own five-second timeout.
      const withinBudget = started !== undefined && performance.now() - started < 4500;
      release();
      await completed;
      requireFact(withinBudget);
      if (!observation) {
        await Promise.race([
          new Promise(resolve => { page.once('requestfinished', resolve); page.once('requestfailed', resolve); }),
          new Promise(resolve => setTimeout(resolve, 1000)),
        ]);
      }
      requireFact(observation === 'cancelled' || observation === 'delivered_and_retired');
      await page.unroute('**/api/account/profile', handler);
      page.off('requestfailed', failed);
      page.off('requestfinished', finished);
      return {upstream_profile_status: upstreamStatus, observation};
    },
    cancel() { release(); },
  };
}

async function launchOwnedChromium(chromium, config) {
  const profile = await mkdtemp(join(config.work_dir, 'chromium-'));
  // Unlike Playwright's detached launcher, this child and Chromium descendants
  // remain in the runner-owned driver process group, including launch failures.
  const process = spawn(chromium.executablePath(), [
    '--headless', '--no-first-run', '--no-default-browser-check',
    '--disable-background-networking', '--disable-component-update',
    '--disable-default-apps', '--disable-extensions', '--disable-sync',
    '--disable-breakpad', '--disable-crash-reporter', '--disable-popup-blocking',
    '--disable-renderer-backgrounding', '--disable-background-timer-throttling',
    '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0',
    `--user-data-dir=${profile}`,
    `--host-resolver-rules=MAP ${new URL(config.origin).hostname}:443 127.0.0.1:${config.port}`,
    '--no-proxy-server', 'about:blank',
  ], {detached: false, stdio: 'ignore'});
  let spawnFailed = false;
  process.on('error', () => { spawnFailed = true; });
  const deadline = performance.now() + 15_000;
  while (performance.now() < deadline && process.exitCode === null && !spawnFailed) {
    try {
      const [port, path] = (await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).trim().split('\n');
      requireFact(/^[0-9]+$/.test(port) && path.startsWith('/devtools/browser/'));
      return await chromium.connectOverCDP(`ws://127.0.0.1:${port}${path}`, {timeout: 5000});
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
    await new Promise(resolve => setTimeout(resolve, 25));
  }
  fail();
}

/** Only categorical error type and this driver's numeric call site cross the pipe. */
export function browserFailure(stage, error) {
  let errorType = 'Error';
  let driverLine = null;
  let driverColumn = null;
  try {
    if (error?.name === 'TimeoutError') errorType = 'TimeoutError';
    if (typeof error?.stack === 'string') {
      const ownLocations = [import.meta.url + ':', fileURLToPath(import.meta.url) + ':'];
      for (const frame of error.stack.slice(0, 65_536).split('\n').slice(1)) {
        if (/^\s*at (?:fail|requireFact) \(/.test(frame)) continue;
        if (!ownLocations.some(location => frame.includes(location))) continue;
        const position = frame.match(/:(\d+):(\d+)\)?$/);
        if (!position) continue;
        const line = Number(position[1]);
        const column = Number(position[2]);
        if (Number.isInteger(line) && Number.isInteger(column) && line >= 1 && line <= 100_000 && column >= 1 && column <= 100_000) {
          driverLine = line;
          driverColumn = column;
          break;
        }
      }
    }
  } catch { /* Never reflect unexpected error objects or getter failures. */ }
  return {kind: 'browser_failure', stage, error_type: errorType, driver_line: driverLine, driver_column: driverColumn};
}

async function main() {
startInput();
overallDeadline = performance.now() + 175_000;
let stage = "config";
let browser;
let barrier;
let exitCode = 1;
// Overall watchdog has no diagnostic payload. Parent additionally kills/verifies the process group.
const watchdog = setTimeout(() => process.exit(1), 175_000);
try {
  const config = await receive();
  requireFact(config?.kind === 'config' && new URL(config.origin).protocol === 'https:');
  const require = createRequire(config.app + '/package.json');
  const {chromium, expect} = require('@playwright/test');
  const fixture = await owner({command: 'browser_fixture'});
  requireFact(fixture.kind === 'browser_fixture' && fixture.web_origin === config.origin);
  browser = await launchOwnedChromium(chromium, config);
  async function newContext() {
    const context = await browser.newContext({ignoreHTTPSErrors: true, locale: 'en-US'});
    context.setDefaultTimeout(30_000);
    await context.addInitScript(() => localStorage.setItem('kokoro.locale', 'en'));
    return context;
  }
  stage = "cold_login";
  const context = await newContext();
  const page = await context.newPage();
  const initialCookies = (await issuerCookies(context, config.origin)).length;
  requireFact(initialCookies === 0);
  const signIn = await login(page, config, fixture);
  const session = await read(page, '/api/auth/session');
  const projects = await read(page, '/api/session/projects');
  requireFact(projects.status === 200);
  const initialProfile = await openProfile(page, expect);
  const identity = {subject: initialProfile.profile.subject, tenant_id: fixture.tenant_id};
  requireSessionObservation(session, true, identity);
  await bind(context, config.origin, 'primary');
  const journeys = {cold_login: {
    initial_issuer_cookies: initialCookies, sign_in_status: signIn,
    session_status: session.status, authenticated: session.body?.data?.authenticated,
    projects_status: projects.status, profile_status: initialProfile.status,
    profile_visible: await profileVisible(page, initialProfile.profile, expect),
    owner: ownerIs(await inspect('primary'), true, true, 'fixed'),
  }};

  stage = "shared_admin";
  journeys.shared_admin = await sharedAdminJourney(context, config, identity, expect);

  stage = "tenant_rejection_recovery";
  // Keep this SettingsPanel snapshot boundary mounted across a real tab switch.
  // The Account panel remount starts revalidation; the prior name/email must still
  // be displayed while its real new response is held (editing may be disabled).
  const peer = await preparePeer(context, config.origin);
  await page.bringToFront();
  await page.getByTestId('settings-tab-appearance').click();
  await expect(page.getByTestId('settings-account')).toHaveCount(0);
  barrier = await profileBarrier(page, config);
  await page.getByTestId('settings-tab-account').click();
  await barrier.ready;
  const visibleBeforeMutation = await profileSentinel(page, initialProfile.profile, expect);
  await owner({command: 'activate_browser_tenant', slot: 'primary', tenant: 'other'});
  const foreignOwner = ownerIs(await inspect('primary'), true, true, 'other');
  const rejectedSession = await read(page, '/api/auth/session');
  const rejectedProjects = await read(page, '/api/session/projects');
  requireFact(rejectedSession.status === 403 && rejectedSession.body?.error?.code === 'product_tenant_forbidden');
  requireFact(rejectedProjects.status === 403 && rejectedProjects.body?.error?.code === 'product_tenant_forbidden');
  const focused = await focusProbe(page, peer, 403, 'product_tenant_forbidden');
  const privateRetired = await retired(page, initialProfile.profile, expect);
  const raceObservation = await barrier.release();
  barrier = undefined;
  const race = {...raceObservation, private_ui_retired: await retired(page, initialProfile.profile, expect), cross_tab_focus: focused};

  const relogin = await login(page, config, fixture);
  await bind(context, config.origin, 'primary');
  const recoveredSession = await read(page, '/api/auth/session');
  const recoveredProjects = await read(page, '/api/session/projects');
  requireSessionObservation(recoveredSession, true, identity);
  requireFact(recoveredProjects.status === 200);
  const recoveredProfile = await openProfile(page, expect);
  requireFact(recoveredProfile.profile.subject === identity.subject);
  journeys.tenant_rejection_recovery = {
    foreign_owner: foreignOwner, pre_mutation_profile_visible: visibleBeforeMutation,
    session_status: rejectedSession.status,
    session_error_code: rejectedSession.body.error.code,
    projects_status: rejectedProjects.status,
    projects_error_code: rejectedProjects.body.error.code,
    private_ui_retired: privateRetired,
    relogin_status: relogin, recovered_session_status: recoveredSession.status,
    recovered_authenticated: recoveredSession.body.data.authenticated,
    recovered_projects_status: recoveredProjects.status,
    recovered_profile_status: recoveredProfile.status,
    recovered_profile_visible: await profileVisible(page, recoveredProfile.profile, expect),
    recovered_owner: ownerIs(await inspect('primary'), true, true, 'fixed'),
  };

  stage = "ui_logout";
  const cookies = await issuerCookies(context, config.origin);
  requireFact(cookies.length === 1);
  const oldCookie = `${cookies[0].name}=${cookies[0].value}`;
  const signoutResponse = page.waitForResponse(r => new URL(r.url()).pathname === '/iam/sign-out' && r.request().method() === 'POST');
  await page.getByTestId('settings-logout').click();
  const signoutStatus = (await signoutResponse).status();
  requireFact(signoutStatus === 200);
  await page.waitForURL(url => url.pathname === '/');
  const anonymous = await read(page, '/api/auth/session');
  const outProjects = await read(page, '/api/session/projects');
  const remainingCookies = (await issuerCookies(context, config.origin)).length;
  const oldCookieProjects = await replay(config, oldCookie);
  requireSessionObservation(anonymous, false);
  requireFact(outProjects.status === 401 && outProjects.body?.error?.code === 'session_authentication_required' && remainingCookies === 0 && oldCookieProjects.status === 401 && oldCookieProjects.body?.error?.code === 'session_invalid');
  journeys.ui_logout = {
    clicked: true, sign_out_status: signoutStatus,
    owner: ownerIs(await inspect('primary'), true, true, 'fixed', false),
    issuer_cookies: remainingCookies, session_status: anonymous.status,
    authenticated: anonymous.body?.data?.authenticated, projects_status: outProjects.status,
    projects_error_code: outProjects.body.error.code,
    old_cookie_projects_status: oldCookieProjects.status,
    old_cookie_projects_error_code: oldCookieProjects.body.error.code,
  };
  await context.close();

  stage = "independent_revocation";
  await waitForNativeAdmissionWindow(overallDeadline);
  const a = await newContext();
  const b = await newContext();
  const pageA = await a.newPage();
  const pageB = await b.newPage();
  await login(pageA, config, fixture);
  await bind(a, config.origin, 'primary');
  const profileA = await openProfile(pageA, expect);
  const peerA = await preparePeer(a, config.origin);
  await login(pageB, config, fixture);
  await bind(b, config.origin, 'secondary');
  const profileB = await openProfile(pageB, expect);
  requireFact(profileA.profile.subject === profileB.profile.subject);
  const peerB = await preparePeer(b, config.origin);
  await owner({command: 'revoke_browser_session', slot: 'primary'});
  const revokedA = await read(pageA, '/api/auth/session');
  const revokedAProjects = await read(pageA, '/api/session/projects');
  const survivingB = await read(pageB, '/api/auth/session');
  requireSessionObservation(revokedA, false);
  requireSessionObservation(survivingB, true, {subject: profileB.profile.subject, tenant_id: fixture.tenant_id});
  requireFact(revokedAProjects.status === 401 && revokedAProjects.body?.error?.code === 'session_authentication_required');
  await focusProbe(pageA, peerA, 200, false);
  const aRetired = await retired(pageA, profileA.profile, expect, true);
  const aOwner = ownerIs(await inspect('primary'), false, true, 'none');
  const bBefore = ownerIs(await inspect('secondary'), true, true, 'fixed');
  await owner({command: 'revoke_browser_membership'});
  const bAfter = ownerIs(await inspect('secondary'), true, false, 'fixed');
  const deniedB = await read(pageB, '/api/auth/session');
  const deniedBProjects = await read(pageB, '/api/session/projects');
  requireFact(deniedB.status === 403 && deniedB.body?.error?.code === 'session_forbidden' && deniedBProjects.status === 403 && deniedBProjects.body?.error?.code === 'session_forbidden');
  await focusProbe(pageB, peerB, 403, 'session_forbidden');
  journeys.independent_revocation = {
    a_owner: aOwner, a_session_status: revokedA.status,
    a_authenticated: revokedA.body.data.authenticated,
    a_projects_status: revokedAProjects.status,
    a_projects_error_code: revokedAProjects.body.error.code, a_private_ui_retired: aRetired,
    b_session_status_before_membership: survivingB.status,
    b_authenticated_before_membership: survivingB.body.data.authenticated,
    b_owner_before_membership: bBefore,
    b_owner_after_membership: bAfter, b_session_status: deniedB.status,
    b_session_error_code: deniedB.body.error.code,
    b_projects_status: deniedBProjects.status,
    b_projects_error_code: deniedBProjects.body.error.code,
    private_ui_retired: await retired(pageB, profileB.profile, expect),
  };
  stage = "browser_close";
  await a.close();
  await b.close();
  await browser.close();
  browser = undefined;
  await emit({kind: 'browser_result', journeys, race});
  exitCode = 0;
} catch (error) {
  // Never stringify Playwright errors: locators and assertions can contain identities.
  await emit(browserFailure(stage, error)).catch(() => undefined);
} finally {
  barrier?.cancel();
  if (browser) await browser.close().catch(() => undefined);
  clearTimeout(watchdog);
  process.stdin.pause();
}
process.exit(exitCode);

}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) await main();
