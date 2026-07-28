#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { access, readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { collectInventory } from "./inventory.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const policyPath = resolve(root, "config/repository/infrastructure-policy.yaml");
const DEFAULT_ENV_FILE = resolve(root, "deploy/.env.dev");
const ACTIONS = new Set(["config", "ensure", "refresh", "stop", "status"]);
const MODES = new Set(["development", "ci", "production"]);
const CANONICAL_PROJECT = "kokoro-infra";
const FULL_SERVICES = ["mysql", "redis", "mongo", "minio", "litellm"];
const MANAGED_SERVICES = [...FULL_SERVICES, "postgres"];
const LEGACY_CANONICAL_SERVICES = new Set(["mysql", "redis", "mongo", "minio"]);
const STATEFUL_MOUNTS = {
  mysql: { destination: "/var/lib/mysql", suffix: "mysql", composeVolume: "mysql-data" },
  postgres: { destination: "/var/lib/postgresql", suffix: "postgres", composeVolume: "postgres-data" },
  redis: { destination: "/data", suffix: "redis", composeVolume: "redis-data" },
  mongo: { destination: "/data/db", suffix: "mongo", composeVolume: "mongo-data" },
  minio: { destination: "/data", suffix: "minio", composeVolume: "minio-data" },
};
const SERVICE_PORTS = {
  mysql: [{ variable: "KOKORO_MYSQL_PORT", fallback: "3307", target: "3306" }],
  postgres: [{ variable: "KOKORO_POSTGRES_PORT", fallback: "5433", target: "5432" }],
  redis: [{ variable: "KOKORO_REDIS_PORT", fallback: "6379", target: "6379" }],
  mongo: [{ variable: "KOKORO_MONGO_PORT", fallback: "27017", target: "27017" }],
  minio: [
    { variable: "KOKORO_MINIO_PORT", fallback: "9100", target: "9100" },
    { variable: "KOKORO_MINIO_CONSOLE_PORT", fallback: "9101", target: "9101" },
  ],
  litellm: [{ variable: "KOKORO_LITELLM_PORT", fallback: "4000", target: "4000" }],
};

class InfraError extends Error {
  constructor(code, detail = "") {
    super(`${code}${detail ? `: ${detail}` : ""}`);
    this.code = code;
  }
}

function parseArguments(argv) {
  const action = argv[0];
  if (!ACTIONS.has(action)) throw new InfraError("infra_arguments_invalid", "unknown action");
  const options = {
    action,
    dryRun: false,
    json: false,
    profiles: [],
    scope: "dev",
    envFile: DEFAULT_ENV_FILE,
    mode: "development",
  };
  for (let index = 1; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--dry-run") {
      options.dryRun = true;
      continue;
    }
    if (argument === "--json") {
      options.json = true;
      continue;
    }
    const value = argv[index + 1];
    if (!value) throw new InfraError("infra_arguments_invalid", `missing ${argument}`);
    index += 1;
    if (argument === "--profiles") options.profiles = value.split(",").filter(Boolean);
    else if (argument === "--scope") options.scope = value;
    else if (argument === "--infra-env-file") options.envFile = resolve(value);
    else if (argument === "--mode") options.mode = value;
    else throw new InfraError("infra_arguments_invalid", argument);
  }
  return options;
}

async function loadPolicy() {
  return JSON.parse(await readFile(policyPath, "utf8"));
}

function parseEnv(source) {
  const values = {};
  for (const rawLine of source.split(/\r?\n/u)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const separator = line.indexOf("=");
    if (separator <= 0) continue;
    const key = line.slice(0, separator).trim();
    let value = line.slice(separator + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    values[key] = value;
  }
  return values;
}

function validateOptions(options, policy) {
  const scopePattern = new RegExp(policy.authority.environmentScopePattern, "u");
  if (
    !scopePattern.test(options.scope) ||
    policy.authority.forbiddenScopePrefixes.some((prefix) => options.scope.startsWith(prefix))
  ) {
    throw new InfraError("infra_scope_invalid", options.scope);
  }
  if (!MODES.has(options.mode)) throw new InfraError("infra_arguments_invalid", options.mode);
  if (options.profiles.length === 0) {
    throw new InfraError("infra_arguments_invalid", "--profiles is required");
  }
  for (const profile of options.profiles) {
    if (!Object.hasOwn(policy.profiles, profile)) {
      throw new InfraError("infra_arguments_invalid", `unknown profile ${profile}`);
    }
  }
}

function expandSelection(profileNames, policy) {
  const services = new Set();
  const composeProfiles = new Set();
  for (const profile of profileNames) {
    for (const service of policy.profiles[profile]) services.add(service);
    if (profile === "full") {
      for (const name of ["platform", "runtime", "storage", "model"]) {
        composeProfiles.add(name);
      }
    } else {
      composeProfiles.add(profile);
    }
  }
  return {
    profiles: [...new Set(profileNames)].sort(),
    composeProfiles: [...composeProfiles].sort(),
    services: [...services],
  };
}

function requiredVariables(services) {
  const required = new Set();
  if (services.includes("mysql")) {
    for (const name of ["MYSQL_ROOT_PASSWORD", "MYSQL_PASSWORD"]) required.add(name);
  }
  if (services.includes("postgres")) required.add("POSTGRES_PASSWORD");
  if (services.includes("minio")) {
    required.add("MINIO_ROOT_USER");
    required.add("MINIO_ROOT_PASSWORD");
  }
  if (services.includes("litellm")) {
    for (const name of [
      "LITELLM_MASTER_KEY",
      "OPENAI_API_KEY",
      "ANTHROPIC_API_KEY",
      "OPENAI_COMPAT_BASE_URL",
      "OPENAI_COMPAT_API_KEY",
    ]) {
      required.add(name);
    }
  }
  return [...required];
}

function composeArgv({ action, composeProfiles, services, envFile }) {
  const argv = [
    "compose",
    "--project-name",
    "kokoro-infra",
    "--env-file",
    envFile,
    "-f",
    "docker-compose.infra.yml",
  ];
  for (const profile of composeProfiles) argv.push("--profile", profile);
  if (action === "config") argv.push("config", "--quiet");
  else if (action === "ensure") {
    argv.push("up", "-d", "--wait");
    if (services.some((service) => Object.hasOwn(STATEFUL_MOUNTS, service))) {
      argv.push("--no-recreate");
    }
    argv.push(...services);
  }
  else if (action === "refresh") {
    if (services.some((service) => Object.hasOwn(STATEFUL_MOUNTS, service))) {
      throw new InfraError("infra_destructive_operation_forbidden", "stateful refresh");
    }
    argv.push("up", "-d", "--wait", "--force-recreate", ...services);
  }
  else if (action === "stop") argv.push("stop", ...services);
  else if (action === "status") argv.push("ps", ...services);
  return argv;
}

function assertSafeDockerArguments(args) {
  const [group] = args;
  const destructiveCommand =
    (group === "compose" && args.includes("down")) ||
    (["system", "volume", "image", "builder"].includes(group) &&
      args.some((argument) => ["prune", "rm"].includes(argument)));
  const destructiveFlag = args.some((argument) =>
    ["--volumes", "--remove-orphans"].includes(argument) || argument === "-v");
  if (destructiveCommand || destructiveFlag) {
    throw new InfraError("infra_destructive_operation_forbidden");
  }
  return true;
}

function dockerProjection(args, options = {}) {
  assertSafeDockerArguments(args);
  return spawnSync("docker", args, {
    encoding: "utf8",
    shell: false,
    maxBuffer: 1024 * 1024,
    ...(options.input === undefined ? {} : { input: options.input }),
  });
}

function checkedProjection(runDocker, args) {
  const result = runDocker(args);
  if (result.error || result.status !== 0) {
    throw new InfraError("infra_scope_inspection_failed");
  }
  return result.stdout;
}

function inspectCanonicalContainers(runDocker = dockerProjection) {
  const ids = checkedProjection(runDocker, [
    "ps",
    "-aq",
    "--filter",
    `label=com.docker.compose.project=${CANONICAL_PROJECT}`,
  ]).split(/\r?\n/u).filter(Boolean);
  return ids.map((id) => {
    const [
      service = "",
      rawScope = "",
      rawProfile = "",
      rawDataMarker = "",
      rawAuthMarker = "",
    ] = checkedProjection(runDocker, [
      "inspect",
      "--format",
      '{{index .Config.Labels "com.docker.compose.service"}}\t{{index .Config.Labels "io.kokoro.infra.scope"}}\t{{index .Config.Labels "io.kokoro.infra.profile"}}\t{{index .Config.Labels "io.kokoro.infra.data-marker"}}\t{{index .Config.Labels "io.kokoro.infra.auth-marker"}}',
      id,
    ]).trim().split("\t");
    const mounts = checkedProjection(runDocker, [
      "inspect",
      "--format",
      '{{range .Mounts}}{{printf "%s\\t%s\\t%s\\n" .Type .Name .Destination}}{{end}}',
      id,
    ]).split(/\r?\n/u).filter(Boolean).map((line) => {
      const [type, source, destination] = line.split("\t");
      return { type, source, destination };
    });
    return {
      id,
      service,
      scope: rawScope === "<no value>" ? "" : rawScope,
      profile: rawProfile === "<no value>" ? "" : rawProfile,
      dataMarker: rawDataMarker === "<no value>" ? "" : rawDataMarker,
      authMarker: rawAuthMarker === "<no value>" ? "" : rawAuthMarker,
      mounts,
    };
  });
}

function expectedPersistentTargets(plan) {
  return plan.services.filter((service) => Object.hasOwn(STATEFUL_MOUNTS, service)).map((service) => {
    const mount = STATEFUL_MOUNTS[service];
    return {
      service,
      name: `${plan.resourcePrefix}-${mount.suffix}`,
      composeVolume: mount.composeVolume,
      dataMarker: `${service}-data-v1`,
    };
  });
}

function inspectPersistentTargets(plan, runDocker = dockerProjection) {
  return expectedPersistentTargets(plan).map((expected) => {
    const rows = checkedProjection(runDocker, [
      "volume",
      "ls",
      "--filter",
      `name=^${expected.name}$`,
      "--format",
      '{{.Name}}\t{{.Label "com.docker.compose.project"}}\t{{.Label "com.docker.compose.volume"}}\t{{.Label "io.kokoro.infra.data-marker"}}',
    ]).split(/\r?\n/u).filter(Boolean);
    const row = rows.find((candidate) => candidate.split("\t", 1)[0] === expected.name);
    if (!row) return { service: expected.service, name: expected.name, exists: false, mountUsers: [] };
    const [, rawProject = "", rawComposeVolume = "", rawDataMarker = ""] = row.split("\t");
    const ids = checkedProjection(runDocker, [
      "ps", "-aq", "--filter", `volume=${expected.name}`,
    ]).split(/\r?\n/u).filter(Boolean);
    const mountUsers = ids.map((id) => {
      const [rawProjectName = "", rawService = "", rawName = "", ports = ""] =
        checkedProjection(runDocker, [
          "inspect",
          "--format",
          '{{index .Config.Labels "com.docker.compose.project"}}\t{{index .Config.Labels "com.docker.compose.service"}}\t{{.Name}}\t{{json .NetworkSettings.Ports}}',
          id,
        ]).trim().split("\t");
      const clean = (value) => value === "<no value>" ? "" : value;
      return {
        id,
        project: clean(rawProjectName),
        service: clean(rawService),
        name: clean(rawName).replace(/^\//u, ""),
        ports,
      };
    });
    const clean = (value) => value === "<no value>" ? "" : value;
    return {
      service: expected.service,
      name: expected.name,
      exists: true,
      project: clean(rawProject),
      composeVolume: clean(rawComposeVolume),
      dataMarker: clean(rawDataMarker),
      mountUsers,
    };
  });
}

function assertPersistentTargetCompatibility(plan, containers, targets) {
  const expectedByService = new Map(expectedPersistentTargets(plan).map((target) => [target.service, target]));
  const legacyServices = new Set();
  for (const target of targets) {
    const expected = expectedByService.get(target.service);
    if (!expected) continue;
    const container = containers.find((candidate) => candidate.service === target.service);
    if (!target.exists) {
      if (container) throw new InfraError("infra_persistent_volume_inspection_failed", target.service);
      continue;
    }
    if (!target.project || !target.composeVolume) {
      throw new InfraError("infra_persistent_volume_ownership_missing", target.service);
    }
    if (target.project !== CANONICAL_PROJECT || target.composeVolume !== expected.composeVolume) {
      throw new InfraError("infra_persistent_volume_ownership_drift", target.service);
    }
    if (!container) throw new InfraError("infra_persistent_volume_orphaned", target.service);
    if (
      target.mountUsers.length === 0 ||
      target.mountUsers.some(({ id, project, service }) =>
        id !== container.id || project !== CANONICAL_PROJECT || service !== target.service)
    ) {
      throw new InfraError("infra_persistent_volume_unknown_mount", target.service);
    }
    if (!target.dataMarker) {
      const legacyCanonical =
        LEGACY_CANONICAL_SERVICES.has(target.service) &&
        containerMatchesPlan(container, plan) &&
        !container.profile &&
        !container.dataMarker &&
        !container.authMarker;
      if (!legacyCanonical) {
        throw new InfraError("infra_persistent_data_marker_missing", target.service);
      }
      legacyServices.add(target.service);
      continue;
    }
    if (target.dataMarker !== expected.dataMarker) {
      throw new InfraError("infra_persistent_data_marker_drift", target.service);
    }
  }
  return { legacyServices };
}

function containerMatchesPlan(container, plan) {
  if (!MANAGED_SERVICES.includes(container.service)) return false;
  if (container.scope !== plan.environmentScope) return false;
  const expected = STATEFUL_MOUNTS[container.service];
  if (!expected) return true;
  return container.mounts.some(
    ({ type, source, destination }) =>
      type === "volume" &&
      source === `${plan.resourcePrefix}-${expected.suffix}` &&
      destination === expected.destination,
  );
}

function convergeCanonicalScope(plan, containers) {
  if (containers.length === 0) return { ...plan, scopeTransition: "absent" };
  if (containers.every((container) => containerMatchesPlan(container, plan))) {
    return { ...plan, scopeTransition: "matching" };
  }
  if (["stop", "status"].includes(plan.action)) {
    throw new InfraError("infra_scope_mismatch");
  }
  throw new InfraError("infra_scope_transition_requires_explicit_activation");
}

function assertPersistentAuthCompatibility(containers, expectedMarkers, evidence = {}) {
  const legacyServices = evidence.legacyServices ?? new Set();
  for (const [service, expectedMarker] of Object.entries(expectedMarkers)) {
    if (!expectedMarker) continue;
    const container = containers.find((candidate) => candidate.service === service);
    if (!container) continue;
    const persistentMount = STATEFUL_MOUNTS[service];
    if (!persistentMount || !container.mounts.some(({ type, destination }) =>
      type === "volume" && destination === persistentMount.destination)) continue;
    if (!container.authMarker && service === "minio" && !legacyServices.has(service)) {
      throw new InfraError("infra_persistent_auth_marker_missing", service);
    }
    if (container.authMarker && container.authMarker !== expectedMarker) {
      throw new InfraError("infra_persistent_auth_drift", service);
    }
  }
  return true;
}

function credentialProbe(runDocker, service, containerId, args, secret) {
  const result = runDocker(["exec", "-i", containerId, "sh", "-c", ...args], {
    input: `${secret}\n`,
  });
  if (result.error || result.status !== 0) {
    throw new InfraError("infra_persistent_auth_probe_failed", service);
  }
}

function probePersistentCredentials(plan, containers, values, runDocker = dockerProjection) {
  for (const service of plan.services.filter((candidate) => ["mysql", "postgres"].includes(candidate))) {
    const container = containers.find((candidate) => candidate.service === service);
    if (!container) continue;
    if (service === "mysql") {
      const readPassword = 'IFS= read -r MYSQL_PWD; export MYSQL_PWD; ';
      credentialProbe(runDocker, service, container.id, [
        `${readPassword}exec mysqladmin ping -h 127.0.0.1 -u"$1" --silent`,
        "sh", "root",
      ], values.MYSQL_ROOT_PASSWORD);
      credentialProbe(runDocker, service, container.id, [
        `${readPassword}exec mysql --protocol=TCP -h127.0.0.1 -u"$1" --database="$2" --execute="SELECT 1"`,
        "sh", values.MYSQL_USER ?? "kokoro", values.MYSQL_DATABASE ?? "kokoro",
      ], values.MYSQL_PASSWORD);
    } else {
      credentialProbe(runDocker, service, container.id, [
        'IFS= read -r PGPASSWORD; export PGPASSWORD; exec psql -v ON_ERROR_STOP=1 -h 127.0.0.1 -U "$1" -d "$2" -c "SELECT 1"',
        "sh", values.POSTGRES_USER ?? "postgres", values.POSTGRES_DB ?? "postgres",
      ], values.POSTGRES_PASSWORD);
    }
  }
  return true;
}

function assertCanonicalPostcondition(plan, containers) {
  const presentServices = new Set(containers.map(({ service }) => service));
  if (
    containers.length === 0 ||
    !containers.every((container) => containerMatchesPlan(container, plan)) ||
    !plan.services.every((service) => presentServices.has(service))
  ) {
    throw new InfraError("infra_scope_convergence_failed");
  }
}

function hasCompetingActiveAuthority(inventory, plan = null, values = {}) {
  const selectedServices = plan?.services ?? MANAGED_SERVICES;
  const exactNames = new Set(selectedServices.flatMap((service) => [
    `${CANONICAL_PROJECT}-${service}-1`,
    `${CANONICAL_PROJECT}_${service}_1`,
  ]));
  const exactVolumes = new Set(
    selectedServices.filter((service) => Object.hasOwn(STATEFUL_MOUNTS, service))
      .map((service) => `${plan?.resourcePrefix ?? "kokoro-infra_kokoro"}-${STATEFUL_MOUNTS[service].suffix}`),
  );
  const exactPorts = selectedServices.flatMap((service) => SERVICE_PORTS[service] ?? []).map(
    ({ variable, fallback, target }) => `${values[variable] ?? fallback}->${target}/tcp`,
  );
  return inventory.containers.some(
    ({ project, service, name, status, volumes = [], ports = "" }) => {
      if (project === CANONICAL_PROJECT || !/(?:up|running)/iu.test(status)) return false;
      const projectSignal = /^(?:kokoro|kokoro[-_])/u.test(project ?? "") &&
        selectedServices.some((candidate) => (service || name).includes(candidate));
      const nameSignal = exactNames.has(name);
      const volumeSignal = volumes.some((volume) => exactVolumes.has(volume.split(":", 1)[0]));
      const portSignal = exactPorts.some((port) => ports.includes(port));
      return projectSignal || nameSignal || volumeSignal || portSignal;
    },
  );
}

async function buildPlan(options) {
  const policy = await loadPolicy();
  validateOptions(options, policy);
  const selection = expandSelection(options.profiles, policy);
  const resourcePrefix =
    policy.authority.resourcePrefixes[options.scope] ??
    policy.authority.defaultResourcePrefixTemplate.replace("{scope}", options.scope);
  const argv = composeArgv({
    action: options.action,
    composeProfiles: selection.composeProfiles,
    services: selection.services,
    envFile: options.envFile,
  });
  return {
    projectName: policy.authority.projectName,
    action: options.action,
    environmentScope: options.scope,
    resourcePrefix,
    profiles: selection.profiles,
    services: selection.services,
    envFile: "<provided>",
    mode: options.mode,
    mutatesState: ["ensure", "refresh", "stop"].includes(options.action),
    argv: argv.map((value) => (value === options.envFile ? "<provided>" : value)),
    executionArgv: argv,
    requiredVariables: requiredVariables(selection.services),
    environment: {
      KOKORO_INFRA_SCOPE: resourcePrefix,
      KOKORO_INFRA_ENVIRONMENT_SCOPE: options.scope,
      KOKORO_INFRA_RESTART_POLICY: policy.restartPolicy[options.mode],
    },
  };
}

async function execute(plan, options) {
  await access(options.envFile);
  const values = parseEnv(await readFile(options.envFile, "utf8"));
  const missing = plan.requiredVariables.filter((name) => !values[name]);
  if (missing.length > 0) {
    throw new InfraError("infra_required_environment_missing", missing.join(","));
  }
  let executionPlan = plan;
  if (["ensure", "refresh"].includes(plan.action)) {
    const inventory = collectInventory();
    if (hasCompetingActiveAuthority(inventory, plan, values)) {
      throw new InfraError("infra_competing_authority_active");
    }
  }
  if (["ensure", "refresh", "stop", "status"].includes(plan.action)) {
    const containers = inspectCanonicalContainers();
    executionPlan = convergeCanonicalScope(plan, containers);
    if (["ensure", "refresh"].includes(plan.action)) {
      const markerDefaults = {
        mysql: "mysql-auth-v1",
        postgres: "postgres-auth-v1",
        minio: "minio-auth-v1",
      };
      const expectedMarkers = Object.fromEntries(
        plan.services
          .filter((service) => Object.hasOwn(markerDefaults, service))
          .map((service) => [
            service,
            values[`KOKORO_${service.toUpperCase()}_AUTH_MARKER`] ?? markerDefaults[service],
          ]),
      );
      const targets = inspectPersistentTargets(plan);
      const persistentEvidence = assertPersistentTargetCompatibility(plan, containers, targets);
      assertPersistentAuthCompatibility(containers, expectedMarkers, persistentEvidence);
      probePersistentCredentials(plan, containers, values);
    }
  }
  assertSafeDockerArguments(executionPlan.executionArgv);
  const result = spawnSync("docker", executionPlan.executionArgv, {
    cwd: root,
    encoding: "utf8",
    shell: false,
    stdio: options.json ? "pipe" : "inherit",
    env: {
      ...process.env,
      ...values,
      ...executionPlan.environment,
    },
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new InfraError("infra_compose_failed", `exit ${result.status}`);
  }
  if (["ensure", "refresh"].includes(executionPlan.action)) {
    assertCanonicalPostcondition(executionPlan, inspectCanonicalContainers());
  }
  return executionPlan;
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const plan = await buildPlan(options);
  const completedPlan = options.dryRun ? plan : await execute(plan, options);
  const sanitized = { ...completedPlan };
  delete sanitized.executionArgv;
  delete sanitized.requiredVariables;
  delete sanitized.environment;
  if (options.json) process.stdout.write(`${JSON.stringify(sanitized)}\n`);
  else {
    process.stdout.write(
      `infra_${options.dryRun ? "plan" : "ok"}: ${plan.action} ` +
        `profiles=${completedPlan.profiles.join(",")} services=${completedPlan.services.join(",")}\n`,
    );
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}

export {
  assertCanonicalPostcondition,
  assertPersistentAuthCompatibility,
  assertPersistentTargetCompatibility,
  assertSafeDockerArguments,
  buildPlan,
  convergeCanonicalScope,
  hasCompetingActiveAuthority,
  inspectCanonicalContainers,
  inspectPersistentTargets,
  parseEnv,
  probePersistentCredentials,
  requiredVariables,
};
