const REPOSITORY_COMPONENT = /^[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*$/u;
const REGISTRY_LABEL = /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/u;
const DIGEST = /^[0-9a-f]{64}$/u;

class SiteReleaseImageError extends Error {
  constructor(code) {
    super(code);
    this.code = code;
  }
}

function reject(code) {
  throw new SiteReleaseImageError(code);
}

function validateRegistry(registry) {
  const separator = registry.lastIndexOf(":");
  const host = separator === -1 ? registry : registry.slice(0, separator);
  const port = separator === -1 ? undefined : registry.slice(separator + 1);
  if (
    host.length === 0 ||
    host.length > 253 ||
    !host.split(".").every((label) => REGISTRY_LABEL.test(label))
  ) {
    reject("site_release_image_invalid");
  }
  if (port !== undefined) {
    if (!/^[1-9][0-9]{0,4}$/u.test(port) || Number(port) > 65535) {
      reject("site_release_image_invalid");
    }
  }
}

export function validateSiteReleaseImageReference(reference) {
  if (typeof reference !== "string" || reference.length === 0) {
    reject("site_release_image_missing");
  }
  if (reference !== reference.trim() || reference !== reference.toLowerCase()) {
    reject("site_release_image_invalid");
  }

  const digestSeparator = "@sha256:";
  const separator = reference.indexOf(digestSeparator);
  if (separator === -1 || separator !== reference.lastIndexOf(digestSeparator)) {
    reject("site_release_image_invalid");
  }
  const name = reference.slice(0, separator);
  const digest = reference.slice(separator + digestSeparator.length);
  if (name.length === 0 || name.length > 255 || !DIGEST.test(digest)) {
    reject("site_release_image_invalid");
  }

  const slash = name.indexOf("/");
  if (slash <= 0 || slash === name.length - 1) reject("site_release_image_invalid");
  validateRegistry(name.slice(0, slash));

  const repositoryComponents = name.slice(slash + 1).split("/");
  if (!repositoryComponents.every((component) => REPOSITORY_COMPONENT.test(component))) {
    reject("site_release_image_invalid");
  }
  if (repositoryComponents.some((component) => component.includes("reference-site"))) {
    reject("site_release_image_forbidden_fixture");
  }
  return reference;
}
