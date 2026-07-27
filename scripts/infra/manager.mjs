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
  if (services.includes("litellm")) required.add("LITELLM_MASTER_KEY");
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
  else if (action === "ensure") argv.push("up", "-d", "--wait", "--no-recreate", ...services);
  else if (action === "refresh") argv.push("up", "-d", "--wait", "--force-recreate", ...services);
  else if (action === "stop") argv.push("stop", ...services);
  else if (action === "status") argv.push("ps", ...services);
  return argv;
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
  if (["ensure", "refresh"].includes(plan.action)) {
    const inventory = collectInventory();
    if (hasCompetingActiveAuthority(inventory)) {
      throw new InfraError("infra_competing_authority_active");
    }
  }
  const result = spawnSync("docker", plan.executionArgv, {
    cwd: root,
    encoding: "utf8",
    shell: false,
    stdio: options.json ? "pipe" : "inherit",
    env: {
      ...process.env,
      ...values,
      ...plan.environment,
    },
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new InfraError("infra_compose_failed", `exit ${result.status}`);
  }
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const plan = await buildPlan(options);
  if (!options.dryRun) await execute(plan, options);
  const sanitized = { ...plan };
  delete sanitized.executionArgv;
  delete sanitized.requiredVariables;
  delete sanitized.environment;
  if (options.json) process.stdout.write(`${JSON.stringify(sanitized)}\n`);
  else {
    process.stdout.write(
      `infra_${options.dryRun ? "plan" : "ok"}: ${plan.action} ` +
        `profiles=${plan.profiles.join(",")} services=${plan.services.join(",")}\n`,
    );
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}

export { buildPlan, hasCompetingActiveAuthority, parseEnv, requiredVariables };
