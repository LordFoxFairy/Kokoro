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
const STATEFUL_MOUNTS = {
  mysql: { destination: "/var/lib/mysql", suffix: "mysql" },
  redis: { destination: "/data", suffix: "redis" },
  mongo: { destination: "/data/db", suffix: "mongo" },
  minio: { destination: "/data", suffix: "minio" },
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
  else if (action === "ensure") argv.push("up", "-d", "--wait", ...services);
  else if (action === "refresh") argv.push("up", "-d", "--wait", "--force-recreate", ...services);
  else if (action === "stop") argv.push("stop", ...services);
  else if (action === "status") argv.push("ps", ...services);
  return argv;
}

function dockerProjection(args) {
  return spawnSync("docker", args, {
    encoding: "utf8",
    shell: false,
    maxBuffer: 1024 * 1024,
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
    const [service = "", rawScope = ""] = checkedProjection(runDocker, [
      "inspect",
      "--format",
      '{{index .Config.Labels "com.docker.compose.service"}}\t{{index .Config.Labels "io.kokoro.infra.scope"}}',
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
      service,
      scope: rawScope === "<no value>" ? "" : rawScope,
      mounts,
    };
  });
}

function containerMatchesPlan(container, plan) {
  if (!FULL_SERVICES.includes(container.service)) return false;
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

function forceFullRecreate(argv) {
  const upIndex = argv.indexOf("up");
  if (upIndex < 0) throw new InfraError("infra_scope_transition_invalid");
  return [
    ...argv.slice(0, upIndex + 1),
    "-d",
    "--wait",
    "--force-recreate",
    ...FULL_SERVICES,
  ];
}

function convergeCanonicalScope(plan, containers) {
  if (containers.length === 0) return { ...plan, scopeTransition: "absent" };
  if (containers.every((container) => containerMatchesPlan(container, plan))) {
    return { ...plan, scopeTransition: "matching" };
  }
  if (["stop", "status"].includes(plan.action)) {
    throw new InfraError("infra_scope_mismatch");
  }
  if (
    !["ensure", "refresh"].includes(plan.action) ||
    !plan.profiles.includes("full")
  ) {
    throw new InfraError("infra_scope_transition_requires_full");
  }
  return {
    ...plan,
    services: [...FULL_SERVICES],
    executionArgv: forceFullRecreate(plan.executionArgv),
    argv: forceFullRecreate(plan.argv),
    scopeTransition: "force-full-recreate",
  };
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

function hasCompetingActiveAuthority(inventory) {
  return inventory.containers.some(
    ({ project, service, name, status }) =>
      project !== "kokoro-infra" &&
      /^(?:kokoro|kokoro[-_])/u.test(project ?? "") &&
      /(?:mysql|redis|mongo|minio|litellm)/u.test(service || name) &&
      /(?:up|running)/iu.test(status),
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
    if (hasCompetingActiveAuthority(inventory)) {
      throw new InfraError("infra_competing_authority_active");
    }
  }
  if (["ensure", "refresh", "stop", "status"].includes(plan.action)) {
    executionPlan = convergeCanonicalScope(plan, inspectCanonicalContainers());
  }
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
  buildPlan,
  convergeCanonicalScope,
  hasCompetingActiveAuthority,
  inspectCanonicalContainers,
  parseEnv,
  requiredVariables,
};
