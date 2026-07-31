#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { parseEnv } from "node:util";

import { validateSiteReleaseImageReference } from "./site-release-image.mjs";

function parseArguments(argv) {
  if (argv.length !== 2 || argv[0] !== "--env-file" || argv[1].length === 0) {
    throw new Error("site_release_image_arguments_invalid");
  }
  return resolve(argv[1]);
}

async function main() {
  const envFile = parseArguments(process.argv.slice(2));
  const fileEnvironment = parseEnv(await readFile(envFile, "utf8"));
  const reference = Object.hasOwn(process.env, "KOKORO_SITE_IMAGE")
    ? process.env.KOKORO_SITE_IMAGE
    : fileEnvironment.KOKORO_SITE_IMAGE;
  validateSiteReleaseImageReference(reference);
  process.stdout.write("site_release_image_ok\n");
}

main().catch((error) => {
  const code = typeof error?.code === "string" && error.code.startsWith("site_release_image_")
    ? error.code
    : error?.message?.startsWith("site_release_image_")
      ? error.message
      : "site_release_image_preflight_failed";
  process.stderr.write(`${code}\n`);
  process.exitCode = 1;
});
