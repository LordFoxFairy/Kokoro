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
async function retired(page, profile, expect) {
  // An invalid cookie is unavailable, not anonymous: keep the shell and retire private data.
  const card = page.getByTestId('settings-account');
  await expect(card).toBeVisible();
  const name = card.getByRole('textbox', {name: 'Full name', exact: true});
  await expect(name).toBeDisabled({timeout: 3000});
  await expect(name).toHaveValue('—', {timeout: 3000});
  if (profile.email) await expect(card.getByText(profile.email, {exact: true})).toHaveCount(0);
  await expect(card.getByText(profile.subject, {exact: true})).toHaveCount(0);
  return true;
}
async function preparePeer(context, origin) {
  const peer = await context.newPage();
  await peer.goto(origin + '/api/fixture-origin');
  return peer;
}
async function focusProbe(page, peer, status) {
  // Only browser focus/visibility events; no synthetic dispatchEvent or private React hook.
  await peer.bringToFront();
  await page.evaluate(() => {
    window.__nativeSmokeFocusObserved = false;
    const observe = event => {
      if (event.isTrusted && document.visibilityState === 'visible') window.__nativeSmokeFocusObserved = true;
    };
    window.addEventListener('focus', observe, {once: true});
    document.addEventListener('visibilitychange', observe, {once: true});
  });
  const response = page.waitForResponse(r => new URL(r.url()).pathname === '/api/auth/session', {timeout: 3000});
  await page.bringToFront();
  requireFact((await response).status() === status);
  await page.waitForFunction(() => window.__nativeSmokeFocusObserved === true, null, {timeout: 3000});
  return true;
}
async function replay(config, cookie) {
  const origin = new URL(config.origin);
  return new Promise((resolve, reject) => {
    const request = https.request({
      hostname: '127.0.0.1', port: config.port, servername: origin.hostname,
      rejectUnauthorized: false, path: '/api/auth/session', method: 'GET',
      headers: {host: origin.host, origin: config.origin, cookie},
    }, response => { response.resume(); response.once('end', () => resolve(response.statusCode)); });
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
  requireFact(session.status === 200 && session.body.authenticated === true);
  const projects = await read(page, '/api/session/projects');
  requireFact(projects.status === 200);
  const initialProfile = await openProfile(page, expect);
  await bind(context, config.origin, 'primary');
  const journeys = {cold_login: {
    initial_issuer_cookies: initialCookies, sign_in_status: signIn,
    session_status: session.status, authenticated: session.body.authenticated,
    projects_status: projects.status, profile_status: initialProfile.status,
    profile_visible: await profileVisible(page, initialProfile.profile, expect),
    owner: ownerIs(await inspect('primary'), true, true, 'fixed'),
  }};

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
  requireFact(rejectedSession.status === 401 && rejectedProjects.status === 401);
  const focused = await focusProbe(page, peer, 401);
  const privateRetired = await retired(page, initialProfile.profile, expect);
  const raceObservation = await barrier.release();
  barrier = undefined;
  const race = {...raceObservation, private_ui_retired: await retired(page, initialProfile.profile, expect), cross_tab_focus: focused};

  const relogin = await login(page, config, fixture);
  await bind(context, config.origin, 'primary');
  const recoveredSession = await read(page, '/api/auth/session');
  const recoveredProjects = await read(page, '/api/session/projects');
  requireFact(recoveredSession.status === 200 && recoveredSession.body.authenticated === true && recoveredProjects.status === 200);
  const recoveredProfile = await openProfile(page, expect);
  journeys.tenant_rejection_recovery = {
    foreign_owner: foreignOwner, pre_mutation_profile_visible: visibleBeforeMutation,
    session_status: rejectedSession.status,
    projects_status: rejectedProjects.status, private_ui_retired: privateRetired,
    relogin_status: relogin, recovered_session_status: recoveredSession.status,
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
  const oldCookieStatus = await replay(config, oldCookie);
  requireFact(anonymous.status === 200 && anonymous.body.authenticated === false && outProjects.status === 401 && remainingCookies === 0 && oldCookieStatus === 401);
  journeys.ui_logout = {
    clicked: true, sign_out_status: signoutStatus,
    owner: ownerIs(await inspect('primary'), true, true, 'fixed', false),
    issuer_cookies: remainingCookies, session_status: anonymous.status,
    authenticated: anonymous.body.authenticated, projects_status: outProjects.status,
    old_cookie_status: oldCookieStatus,
  };
  await context.close();

  stage = "independent_revocation";
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
  requireFact(revokedA.status === 401 && revokedAProjects.status === 401 && survivingB.status === 200 && survivingB.body.authenticated === true);
  await focusProbe(pageA, peerA, 401);
  const aRetired = await retired(pageA, profileA.profile, expect);
  const aOwner = ownerIs(await inspect('primary'), false, true, 'none');
  const bBefore = ownerIs(await inspect('secondary'), true, true, 'fixed');
  await owner({command: 'revoke_browser_membership'});
  const bAfter = ownerIs(await inspect('secondary'), true, false, 'fixed');
  const deniedB = await read(pageB, '/api/auth/session');
  const deniedBProjects = await read(pageB, '/api/session/projects');
  requireFact(deniedB.status === 401 && deniedBProjects.status === 401);
  await focusProbe(pageB, peerB, 401);
  journeys.independent_revocation = {
    a_owner: aOwner, a_session_status: revokedA.status,
    a_projects_status: revokedAProjects.status, a_private_ui_retired: aRetired,
    b_session_status_before_membership: survivingB.status, b_owner_before_membership: bBefore,
    b_owner_after_membership: bAfter, b_session_status: deniedB.status,
    b_projects_status: deniedBProjects.status,
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
