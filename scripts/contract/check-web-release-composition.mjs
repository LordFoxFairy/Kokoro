#!/usr/bin/env node

import { createHash, createPublicKey, verify as verifySignature } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { isAbsolute, resolve } from "node:path";
import { pathToFileURL } from "node:url";

import Ajv2020 from "../../contract/node_modules/ajv/dist/2020.js";

const DEFAULT_REGISTRY = "contract/registry/web-release-composition.yaml";
const DEFAULT_CORPUS = "contract/corpus/web-release-composition-v1.json";
const CONTRACT_IDS = [
  "product-surface-catalog.v1",
  "surface-inventory.v1",
  "web-artifact-provenance-profile.v1",
  "web-build-intent.v1",
  "web-build-material-bundle.v1",
  "web-build-toolchain.v1",
  "web-composition-registry.v1",
  "compiled-web-manifest.v1",
].sort();
const CONTRACT_OWNERS = new Map([
  ["product-surface-catalog.v1", ["platform.product-catalog", "kokoro-platform", "none"]],
  ["surface-inventory.v1", ["platform.site", "kokoro-platform", "none"]],
  ["web-build-material-bundle.v1", ["platform.site", "kokoro-platform", "digest-bound-reference"]],
  ["web-build-toolchain.v1", ["web.release-composition", "kokoro-web", "digest-bound-reference"]],
  ["web-composition-registry.v1", ["web.release-composition", "kokoro-web", "digest-bound-reference"]],
  ["web-build-intent.v1", ["platform.site", "kokoro-platform", "dsse-kokoro-web-build-intent-v1"]],
  ["compiled-web-manifest.v1", ["web.release-composition", "kokoro-web", "provenance-bound"]],
  ["web-artifact-provenance-profile.v1", ["web.release-composition", "kokoro-web", "dsse-in-toto-slsa-provenance-v1"]],
]);
const SECRET_FRAGMENT = /(?:^|_)(?:api_?key|credential|password|private|secret|token)(?:_|$)/iu;

export class WebReleaseContractError extends Error {
  constructor(code, detail = "") {
    super(`${code}${detail ? `: ${detail}` : ""}`);
    this.name = "WebReleaseContractError";
    this.code = code;
  }
}

function fail(code, detail = "") {
  throw new WebReleaseContractError(code, detail);
}

class StrictJsonParser {
  constructor(source) {
    this.source = source;
    this.index = 0;
  }

  parse() {
    this.skipWhitespace();
    const value = this.value();
    this.skipWhitespace();
    if (this.index !== this.source.length) fail("web_release_json_syntax_invalid", `offset ${this.index}`);
    return value;
  }

  skipWhitespace() {
    while (/[\t\n\r ]/u.test(this.source[this.index] ?? "")) this.index += 1;
  }

  value() {
    this.skipWhitespace();
    const character = this.source[this.index];
    if (character === "{") return this.object();
    if (character === "[") return this.array();
    if (character === '"') return this.string();
    for (const [literal, value] of [["true", true], ["false", false], ["null", null]]) {
      if (this.source.startsWith(literal, this.index)) {
        this.index += literal.length;
        return value;
      }
    }
    return this.number();
  }

  object() {
    this.index += 1;
    this.skipWhitespace();
    const result = Object.create(null);
    const keys = new Set();
    if (this.source[this.index] === "}") {
      this.index += 1;
      return result;
    }
    for (;;) {
      if (this.source[this.index] !== '"') fail("web_release_json_syntax_invalid", `offset ${this.index}`);
      const key = this.string();
      if (keys.has(key)) fail("web_release_json_duplicate_key", key);
      keys.add(key);
      this.skipWhitespace();
      if (this.source[this.index] !== ":") fail("web_release_json_syntax_invalid", `offset ${this.index}`);
      this.index += 1;
      result[key] = this.value();
      this.skipWhitespace();
      if (this.source[this.index] === "}") {
        this.index += 1;
        return result;
      }
      if (this.source[this.index] !== ",") fail("web_release_json_syntax_invalid", `offset ${this.index}`);
      this.index += 1;
      this.skipWhitespace();
    }
  }

  array() {
    this.index += 1;
    this.skipWhitespace();
    const result = [];
    if (this.source[this.index] === "]") {
      this.index += 1;
      return result;
    }
    for (;;) {
      result.push(this.value());
      this.skipWhitespace();
      if (this.source[this.index] === "]") {
        this.index += 1;
        return result;
      }
      if (this.source[this.index] !== ",") fail("web_release_json_syntax_invalid", `offset ${this.index}`);
      this.index += 1;
    }
  }

  string() {
    const start = this.index;
    this.index += 1;
    let escaped = false;
    while (this.index < this.source.length) {
      const character = this.source[this.index];
      if (!escaped && character === '"') {
        this.index += 1;
        try {
          return JSON.parse(this.source.slice(start, this.index));
        } catch {
          fail("web_release_json_syntax_invalid", `offset ${start}`);
        }
      }
      if (!escaped && character.charCodeAt(0) < 0x20) fail("web_release_json_syntax_invalid", `offset ${this.index}`);
      if (!escaped && character === "\\") escaped = true;
      else escaped = false;
      this.index += 1;
    }
    fail("web_release_json_syntax_invalid", `offset ${start}`);
  }

  number() {
    const match = this.source.slice(this.index).match(/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/u);
    if (match === null) fail("web_release_json_syntax_invalid", `offset ${this.index}`);
    this.index += match[0].length;
    return Number(match[0]);
  }
}

function unicodeScalars(value) {
  for (let index = 0; index < value.length; index += 1) {
    const unit = value.charCodeAt(index);
    if (unit >= 0xd800 && unit <= 0xdbff) {
      const next = value.charCodeAt(index + 1);
      if (!(next >= 0xdc00 && next <= 0xdfff)) return false;
      index += 1;
    } else if (unit >= 0xdc00 && unit <= 0xdfff) return false;
  }
  return true;
}

function validateIJson(value) {
  if (typeof value === "string") {
    if (!unicodeScalars(value)) fail("web_release_json_lone_surrogate");
    if (value.normalize("NFC") !== value) fail("web_release_json_non_nfc");
    return;
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value) || !Number.isSafeInteger(value)) fail("web_release_json_number_unsafe");
    return;
  }
  if (Array.isArray(value)) {
    for (const item of value) validateIJson(item);
    return;
  }
  if (value !== null && typeof value === "object") {
    for (const [key, nested] of Object.entries(value)) {
      validateIJson(key);
      validateIJson(nested);
    }
  }
}

function canonicalize(value) {
  if (value === null || typeof value === "boolean" || typeof value === "number" || typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(",")}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalize(value[key])}`).join(",")}}`;
}

export function canonicalizeJsonText(source) {
  const value = new StrictJsonParser(source).parse();
  validateIJson(value);
  return canonicalize(value);
}

function canonicalBytes(value) {
  validateIJson(value);
  return Buffer.from(canonicalize(value), "utf8");
}

function digest(value) {
  return `sha256:${createHash("sha256").update(canonicalBytes(value)).digest("hex")}`;
}

function readJson(path, code) {
  let source;
  try {
    source = readFileSync(path, "utf8");
  } catch (error) {
    fail(code, `${path}: ${error.code ?? error.message}`);
  }
  return parseJsonSource(source, code, path);
}

function parseJsonSource(source, code, detail) {
  try {
    return new StrictJsonParser(source).parse();
  } catch (error) {
    if (error instanceof WebReleaseContractError) throw error;
    fail(code, `${detail}: ${error.message}`);
  }
}

function exactKeys(value, expected, code) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) fail(code);
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (actual.length !== wanted.length || actual.some((key, index) => key !== wanted[index])) fail(code, actual.join(","));
}

function unique(values, code) {
  if (new Set(values).size !== values.length) fail(code);
  return new Set(values);
}

function assertDag(nodes, dependencyField, invalidCode, cycleCode) {
  const visiting = new Set();
  const visited = new Set();
  const visit = (ref) => {
    if (visiting.has(ref)) fail(cycleCode, ref);
    if (visited.has(ref)) return;
    const node = nodes.get(ref);
    if (node === undefined) fail(invalidCode, ref);
    visiting.add(ref);
    for (const dependency of node[dependencyField]) visit(dependency);
    visiting.delete(ref);
    visited.add(ref);
  };
  for (const ref of nodes.keys()) visit(ref);
}

function canonicalSet(values) {
  return canonicalize([...values].sort());
}

function canonicalRows(values, key) {
  return canonicalize([...values].sort((left, right) => {
    const leftKey = key(left);
    const rightKey = key(right);
    return leftKey < rightKey ? -1 : leftKey > rightKey ? 1 : 0;
  }));
}

function validateCatalog(catalog) {
  const products = unique(catalog.products.map(({ productRef }) => productRef), "web_release_catalog_duplicate_ref");
  const surfaces = unique(catalog.surfaces.map(({ surfaceRef }) => surfaceRef), "web_release_catalog_duplicate_ref");
  const journeys = unique(catalog.canonicalJourneys.map(({ journeyRef }) => journeyRef), "web_release_catalog_duplicate_ref");
  const operations = unique(catalog.operationFamilyRefs, "web_release_catalog_duplicate_ref");
  const ensureRefs = (values, known) => {
    if (values.some((value) => !known.has(value))) fail("web_release_catalog_reference_invalid", values.find((value) => !known.has(value)));
  };
  for (const product of catalog.products) {
    ensureRefs(product.surfaceRefs, surfaces); ensureRefs(product.requiredProductRefs, products);
    ensureRefs(product.canonicalJourneyRefs, journeys); ensureRefs(product.operationFamilyRefs, operations);
  }
  const surfaceOwners = new Map();
  for (const product of catalog.products) {
    for (const surfaceRef of product.surfaceRefs) {
      if (surfaceOwners.has(surfaceRef)) fail("web_release_catalog_ownership_invalid", surfaceRef);
      surfaceOwners.set(surfaceRef, product.productRef);
    }
  }
  for (const surface of catalog.surfaces) {
    ensureRefs([surface.productRef], products); ensureRefs(surface.requiredSurfaceRefs, surfaces);
    ensureRefs(surface.canonicalJourneyRefs, journeys); ensureRefs(surface.operationFamilyRefs, operations);
    const product = catalog.products.find(({ productRef }) => productRef === surface.productRef);
    if (!product.surfaceRefs.includes(surface.surfaceRef) || surfaceOwners.get(surface.surfaceRef) !== surface.productRef) fail("web_release_catalog_ownership_invalid", surface.surfaceRef);
  }
  for (const journey of catalog.canonicalJourneys) {
    ensureRefs([journey.entrySurfaceRef, ...journey.requiredSurfaceRefs], surfaces); ensureRefs(journey.operationFamilyRefs, operations);
  }
  assertDag(new Map(catalog.products.map((item) => [item.productRef, item])), "requiredProductRefs", "web_release_catalog_reference_invalid", "web_release_catalog_cycle");
  assertDag(new Map(catalog.surfaces.map((item) => [item.surfaceRef, item])), "requiredSurfaceRefs", "web_release_catalog_reference_invalid", "web_release_catalog_cycle");
}

function validateInventory(inventory, catalog) {
  if (inventory.catalog.ref !== catalog.catalogRevisionRef || inventory.catalog.digest !== digest(catalog)) fail("web_release_inventory_catalog_invalid");
  const enabled = unique(inventory.enabledSurfaceRefs, "web_release_inventory_partition_invalid");
  const disabled = unique(inventory.disabledSurfaceRefs, "web_release_inventory_partition_invalid");
  if ([...enabled].some((ref) => disabled.has(ref))) fail("web_release_inventory_partition_invalid");
  const partition = [...enabled, ...disabled].sort();
  const expected = catalog.surfaces.map(({ surfaceRef }) => surfaceRef).sort();
  if (canonicalize(partition) !== canonicalize(expected)) fail("web_release_inventory_partition_invalid");
}

function validateMaterial(material) {
  unique(material.brand.tokens.map(({ tokenRef }) => tokenRef), "web_release_material_identity_invalid");
  unique(material.localePolicy.translations.map(({ locale }) => locale), "web_release_material_identity_invalid");
  unique(material.legal.documents.map(({ documentRef }) => documentRef), "web_release_material_identity_invalid");
  unique(material.legal.documents.map(({ kind }) => kind), "web_release_material_identity_invalid");
  unique(material.publicRuntimeConfig.map(({ key }) => key), "web_release_material_identity_invalid");
  const releaseMaterials = [
    ...material.brand.logos,
    ...material.brand.icons,
    ...material.brand.publicFonts,
    ...material.localePolicy.translations.map(({ catalog }) => catalog),
    ...material.legal.documents.map(({ content }) => content),
    ...material.seo.socialCards,
  ];
  unique(releaseMaterials.map(({ materialRef }) => materialRef), "web_release_material_identity_invalid");
  for (const item of material.publicRuntimeConfig) {
    if (SECRET_FRAGMENT.test(item.key)) fail("web_release_material_secret_invalid", item.key);
  }
  if (material.domainPolicy.canonicalHttpsOrigin !== `https://${material.domainPolicy.canonicalHost}`) fail("web_release_material_origin_invalid");
}

function validateCompositionRegistry(registry, catalog) {
  const units = new Map(registry.units.map((unit) => [unit.unitRef, unit]));
  if (units.size !== registry.units.length) fail("web_release_composition_registry_identity_invalid", "unit");
  const packages = new Map(registry.packages.map((item) => [item.packageRef, item]));
  if (packages.size !== registry.packages.length) fail("web_release_composition_registry_identity_invalid", "package");
  const knownSurfaces = new Set(catalog.surfaces.map(({ surfaceRef }) => surfaceRef));
  const surfaceProviders = [];
  const shellProviders = [];
  const routeRefs = [];
  const pathnames = [];
  const navigationRefs = [];
  const bffGroupRefs = [];
  const bffOperations = [];
  const modelRequirements = [];
  const usedPackages = new Set();
  for (const unit of registry.units) {
    for (const ref of unit.requiresUnitRefs) if (!units.has(ref)) fail("web_release_composition_registry_reference_invalid", ref);
    for (const ref of unit.packageRefs) {
      if (!packages.has(ref)) fail("web_release_composition_registry_reference_invalid", ref);
      usedPackages.add(ref);
    }
    for (const ref of unit.providesSurfaceRefs) {
      if (!knownSurfaces.has(ref)) fail("web_release_composition_registry_reference_invalid", ref);
      surfaceProviders.push(ref);
    }
    shellProviders.push(...unit.providesShellRequirementRefs);
    const unitRouteRefs = new Set(unit.routes.map(({ routeRef }) => routeRef));
    for (const route of unit.routes) {
      if (route.kind === "route-handler" && route.methods.length === 0) fail("web_release_composition_registry_route_conflict", route.routeRef);
      routeRefs.push(route.routeRef);
      pathnames.push(route.pathname);
    }
    for (const item of unit.navigation) {
      if (!unitRouteRefs.has(item.routeRef)) fail("web_release_composition_registry_reference_invalid", item.routeRef);
      navigationRefs.push(item.navigationRef);
    }
    for (const group of unit.bffOperationGroups) {
      bffGroupRefs.push(group.groupRef);
      bffOperations.push(...group.operationIds);
      if (!catalog.operationFamilyRefs.includes(group.operationFamilyRef)) fail("web_release_composition_registry_reference_invalid", group.operationFamilyRef);
    }
    for (const requirement of unit.modelCatalogRequirements) {
      if (!unit.providesSurfaceRefs.includes(requirement.surfaceRef)) fail("web_release_composition_registry_reference_invalid", requirement.surfaceRef);
      modelRequirements.push(`${requirement.surfaceRef}\0${requirement.role}`);
    }
  }
  unique(surfaceProviders, "web_release_composition_registry_identity_invalid");
  unique(shellProviders, "web_release_composition_registry_identity_invalid");
  unique(routeRefs, "web_release_composition_registry_route_conflict");
  unique(pathnames, "web_release_composition_registry_route_conflict");
  unique(navigationRefs, "web_release_composition_registry_identity_invalid");
  unique(bffGroupRefs, "web_release_composition_registry_identity_invalid");
  unique(bffOperations, "web_release_composition_registry_identity_invalid");
  unique(modelRequirements, "web_release_composition_registry_identity_invalid");
  if ([...packages.keys()].some((ref) => !usedPackages.has(ref))) fail("web_release_composition_registry_reference_invalid", "orphan package");
  assertDag(units, "requiresUnitRefs", "web_release_composition_registry_reference_invalid", "web_release_composition_registry_cycle");
}

function validateIntent(intent, related) {
  const pairs = [
    [intent.productSurfaceCatalog, related.catalog, "catalogRevisionRef"],
    [intent.surfaceInventory, related.inventory, "inventoryRevisionRef"],
    [intent.webBuildMaterialBundle, related.material, "bundleRef"],
    [intent.webBuildToolchain, related.toolchain, "toolchainRevisionRef"],
    [intent.webCompositionRegistry, related.registry, "registryRevisionRef"],
  ];
  for (const [reference, document, refField] of pairs) {
    if (reference.ref !== document[refField] || reference.digest !== digest(document)) fail("web_release_intent_reference_invalid", refField);
  }
  if (related.catalog.state !== "published" || related.toolchain.state !== "published" || related.registry.state !== "published") fail("web_release_intent_unpublished_input");
  if (related.inventory.siteRef !== intent.siteRef || related.material.siteRef !== intent.siteRef || related.inventory.releaseCandidateRef !== intent.releaseCandidateRef || related.inventory.launchProfileRevisionRef !== intent.launchProfileRevisionRef) fail("web_release_intent_context_invalid");
  unique(intent.requiredModelCatalogs.map(({ role }) => role), "web_release_intent_reference_invalid");
}

function registryProjection(registry, inventory, intent) {
  const units = new Map(registry.units.map((unit) => [unit.unitRef, unit]));
  const selected = new Set();
  const include = (ref) => {
    if (selected.has(ref)) return;
    const unit = units.get(ref);
    if (unit === undefined) fail("web_release_manifest_registry_projection_invalid", ref);
    selected.add(ref);
    for (const dependency of unit.requiresUnitRefs) include(dependency);
  };
  for (const surfaceRef of inventory.enabledSurfaceRefs) {
    const providers = registry.units.filter(({ providesSurfaceRefs }) => providesSurfaceRefs.includes(surfaceRef));
    if (providers.length !== 1) fail("web_release_manifest_registry_projection_invalid", surfaceRef);
    include(providers[0].unitRef);
  }
  for (const shellRef of intent.shellRequirementRefs) {
    const providers = registry.units.filter(({ providesShellRequirementRefs }) => providesShellRequirementRefs.includes(shellRef));
    if (providers.length !== 1) fail("web_release_manifest_registry_projection_invalid", shellRef);
    include(providers[0].unitRef);
  }
  const selectedUnits = registry.units.filter(({ unitRef }) => selected.has(unitRef));
  const projectedUnits = selectedUnits.map((unit) => ({
    unitRef: unit.unitRef,
    revision: unit.revision,
    kind: unit.kind,
    providesSurfaceRefs: unit.providesSurfaceRefs,
    providesShellRequirementRefs: unit.providesShellRequirementRefs,
    requiresUnitRefs: unit.requiresUnitRefs,
    packageRefs: unit.packageRefs,
  }));
  const selectedPackageRefs = new Set(selectedUnits.flatMap(({ packageRefs }) => packageRefs));
  const projectedPackages = registry.packages.filter(({ packageRef }) => selectedPackageRefs.has(packageRef)).map((item) => ({
    ...item,
    unitRefs: selectedUnits.filter(({ packageRefs }) => packageRefs.includes(item.packageRef)).map(({ unitRef }) => unitRef).sort(),
  }));
  const routes = selectedUnits.flatMap((unit) => unit.routes.map((route) => ({ ...route, unitRef: unit.unitRef })));
  const navigation = selectedUnits.flatMap((unit) => unit.navigation.map((item) => ({ ...item, unitRef: unit.unitRef })));
  const bffOperationGroups = selectedUnits.flatMap((unit) => unit.bffOperationGroups.map(({ operationFamilyRef: _operationFamilyRef, ...group }) => ({ ...group, unitRef: unit.unitRef })));
  const bootstrapRequirements = [...new Set(selectedUnits.flatMap(({ bootstrapRequirements }) => bootstrapRequirements))].sort();
  const catalogsByRole = new Map(intent.requiredModelCatalogs.map(({ role, catalog }) => [role, catalog]));
  const modelCatalogRequirements = selectedUnits.flatMap((unit) => unit.modelCatalogRequirements.map((requirement) => {
    const catalog = catalogsByRole.get(requirement.role);
    if (catalog === undefined) fail("web_release_manifest_registry_projection_invalid", requirement.role);
    return { ...requirement, catalog };
  }));
  return { projectedUnits, projectedPackages, routes, navigation, bffOperationGroups, bootstrapRequirements, modelCatalogRequirements };
}

function validateManifest(manifest, related) {
  const { inventory, intent, registry, toolchain } = related;
  if (manifest.intentRef !== intent.intentRef || manifest.buildIntentDigest !== digest(intent) || manifest.releaseCandidateRef !== intent.releaseCandidateRef) fail("web_release_manifest_reference_invalid", "intent");
  if (manifest.catalog.ref !== intent.productSurfaceCatalog.ref || manifest.catalog.digest !== intent.productSurfaceCatalog.digest ||
      manifest.surfaceInventory.ref !== intent.surfaceInventory.ref || manifest.surfaceInventory.digest !== intent.surfaceInventory.digest ||
      manifest.registry.ref !== registry.registryRevisionRef || manifest.registry.digest !== digest(registry) ||
      manifest.registry.ref !== intent.webCompositionRegistry.ref || manifest.registry.digest !== intent.webCompositionRegistry.digest ||
      manifest.toolchain.ref !== intent.webBuildToolchain.ref || manifest.toolchain.digest !== intent.webBuildToolchain.digest) fail("web_release_manifest_reference_invalid", "owner revision");
  const units = new Map(manifest.units.map((unit) => [unit.unitRef, unit]));
  if (units.size !== manifest.units.length) fail("web_release_manifest_reference_invalid", "duplicate unit");
  const packages = new Map(manifest.packages.map((item) => [item.packageRef, item]));
  if (packages.size !== manifest.packages.length) fail("web_release_manifest_reference_invalid", "duplicate package");
  for (const unit of manifest.units) {
    if (unit.requiresUnitRefs.some((ref) => !units.has(ref)) || unit.packageRefs.some((ref) => !packages.has(ref))) fail("web_release_manifest_reference_invalid", unit.unitRef);
    for (const packageRef of unit.packageRefs) if (!packages.get(packageRef).unitRefs.includes(unit.unitRef)) fail("web_release_manifest_reference_invalid", packageRef);
  }
  for (const item of manifest.packages) {
    if (item.unitRefs.some((ref) => !units.has(ref) || !units.get(ref).packageRefs.includes(item.packageRef))) fail("web_release_manifest_reference_invalid", item.packageRef);
  }
  assertDag(units, "requiresUnitRefs", "web_release_manifest_reference_invalid", "web_release_manifest_cycle");
  const routeRefs = unique(manifest.routes.map(({ routeRef }) => routeRef), "web_release_manifest_route_conflict");
  const pathnames = [];
  for (const route of manifest.routes) {
    if (!units.has(route.unitRef)) fail("web_release_manifest_reference_invalid", route.unitRef);
    if (route.kind === "route-handler" && route.methods.length === 0) fail("web_release_manifest_route_conflict", route.routeRef);
    pathnames.push(route.pathname);
  }
  unique(pathnames, "web_release_manifest_route_conflict");
  for (const item of manifest.navigation) if (!units.has(item.unitRef) || !routeRefs.has(item.routeRef)) fail("web_release_manifest_reference_invalid", item.navigationRef);
  unique(manifest.navigation.map(({ navigationRef }) => navigationRef), "web_release_manifest_reference_invalid");
  unique(manifest.bffOperationGroups.map(({ groupRef }) => groupRef), "web_release_manifest_bff_conflict");
  const bffOperations = [];
  for (const group of manifest.bffOperationGroups) {
    if (!units.has(group.unitRef)) fail("web_release_manifest_reference_invalid", group.groupRef);
    bffOperations.push(...group.operationIds);
  }
  unique(bffOperations, "web_release_manifest_bff_conflict");
  const expectedSurfaces = [...inventory.enabledSurfaceRefs].sort();
  const advertised = [...manifest.advertisedSurfaceRefs].sort();
  const provided = manifest.units.flatMap(({ providesSurfaceRefs }) => providesSurfaceRefs).sort();
  if (canonicalize(advertised) !== canonicalize(expectedSurfaces) || canonicalize(provided) !== canonicalize(expectedSurfaces)) fail("web_release_manifest_surface_leak");
  const providedShells = manifest.units.flatMap(({ providesShellRequirementRefs }) => providesShellRequirementRefs).sort();
  if (canonicalize(providedShells) !== canonicalize([...intent.shellRequirementRefs].sort()) || canonicalize(providedShells) !== canonicalize([...inventory.shellRequirementRefs].sort())) fail("web_release_manifest_shell_closure_invalid");
  if (manifest.modelCatalogRequirements.some(({ surfaceRef }) => !inventory.enabledSurfaceRefs.includes(surfaceRef))) fail("web_release_manifest_surface_leak");
  const measuredTools = new Map(manifest.measuredToolArtifacts.map((item) => [item.role, item]));
  if (measuredTools.size !== manifest.measuredToolArtifacts.length || manifest.compilerRevisionRef !== toolchain.compilerRevisionRef) fail("web_release_manifest_toolchain_mismatch", "measured tools");
  const expectedTools = new Map([
    ["compiler", toolchain.compilerArtifact],
    ["inspector", toolchain.inspectorArtifact],
    ["build-sandbox", toolchain.buildSandboxImage],
    ["inspection-sandbox", toolchain.inspectionSandboxImage],
  ]);
  if (measuredTools.size !== expectedTools.size) fail("web_release_manifest_toolchain_mismatch", "measured tools");
  for (const [role, expected] of expectedTools) {
    const actual = measuredTools.get(role);
    if (actual === undefined || actual.repositoryRef !== expected.repositoryRef || actual.digest !== expected.digest) fail("web_release_manifest_toolchain_mismatch", role);
  }
  const projection = registryProjection(registry, inventory, intent);
  const comparisons = [
    [manifest.units, projection.projectedUnits, ({ unitRef }) => unitRef],
    [manifest.packages, projection.projectedPackages, ({ packageRef }) => packageRef],
    [manifest.routes, projection.routes, ({ routeRef }) => routeRef],
    [manifest.navigation, projection.navigation, ({ navigationRef }) => navigationRef],
    [manifest.bffOperationGroups, projection.bffOperationGroups, ({ groupRef }) => groupRef],
    [manifest.modelCatalogRequirements, projection.modelCatalogRequirements, ({ surfaceRef, role }) => `${surfaceRef}\0${role}`],
  ];
  for (const [actual, expected, key] of comparisons) {
    if (canonicalRows(actual, key) !== canonicalRows(expected, key)) fail("web_release_manifest_registry_projection_invalid");
  }
  if (canonicalSet(manifest.bootstrapRequirements) !== canonicalSet(projection.bootstrapRequirements)) fail("web_release_manifest_registry_projection_invalid", "bootstrap");
}

function validateProvenance(provenance, related) {
  const parameters = provenance.predicate.buildDefinition.externalParameters;
  if (parameters.intentRef !== related.intent.intentRef || parameters.buildIntentDigest !== digest(related.intent) ||
      parameters.compiledWebManifestRef !== related.manifest.manifestRef || parameters.compiledWebManifestDigest !== digest(related.manifest) ||
      parameters.toolchain.ref !== related.toolchain.toolchainRevisionRef || parameters.toolchain.digest !== digest(related.toolchain)) fail("web_release_provenance_reference_invalid");
  if (parameters.siteRef !== related.intent.siteRef || parameters.releaseCandidateRef !== related.intent.releaseCandidateRef ||
      parameters.releaseCandidateRef !== related.manifest.releaseCandidateRef || parameters.candidateAuthorizationEpoch !== related.intent.candidateAuthorizationEpoch) fail("web_release_provenance_context_mismatch");
  const dependencies = new Map(provenance.predicate.buildDefinition.resolvedDependencies.map(({ uri, digest: value }) => [uri, value.sha256]));
  if (dependencies.size !== provenance.predicate.buildDefinition.resolvedDependencies.length) fail("web_release_provenance_reference_invalid", "duplicate dependency");
  const unprefixed = (value) => value.slice("sha256:".length);
  const expectedDependencies = new Map([
    [`git.${related.toolchain.baseSource.repositoryRef}.commit`, unprefixed(related.toolchain.baseSource.commitDigest)],
    [`git.${related.toolchain.baseSource.repositoryRef}.tree`, unprefixed(related.toolchain.baseSource.treeDigest)],
    [related.toolchain.baseTemplate.ref, unprefixed(related.toolchain.baseTemplate.digest)],
    [related.intent.webBuildMaterialBundle.ref, unprefixed(related.intent.webBuildMaterialBundle.digest)],
    [related.toolchain.compilerArtifact.repositoryRef, unprefixed(related.toolchain.compilerArtifact.digest)],
    [related.toolchain.inspectorArtifact.repositoryRef, unprefixed(related.toolchain.inspectorArtifact.digest)],
    [related.toolchain.buildSandboxImage.repositoryRef, unprefixed(related.toolchain.buildSandboxImage.digest)],
    [related.toolchain.inspectionSandboxImage.repositoryRef, unprefixed(related.toolchain.inspectionSandboxImage.digest)],
    [`lockfile.${related.manifest.manifestRef}`, unprefixed(related.manifest.lockfileDigest)],
    ...related.manifest.packages.map(({ packageRef, digest: value }) => [packageRef, unprefixed(value)]),
  ]);
  if (dependencies.size !== expectedDependencies.size) fail("web_release_provenance_reference_invalid", "dependency set");
  for (const [uri, expectedDigest] of expectedDependencies) {
    if (dependencies.get(uri) !== expectedDigest) fail("web_release_provenance_dependency_mismatch", uri);
  }
  const byproducts = unique(provenance.predicate.runDetails.byproducts.map(({ name }) => name), "web_release_provenance_reference_invalid");
  for (const required of ["certification", "inspection-report", "sbom", "vulnerability-scan"]) if (!byproducts.has(required)) fail("web_release_provenance_reference_invalid", required);
}

function pointerSegments(path) {
  if (path === "") return [];
  if (!path.startsWith("/")) fail("web_release_corpus_mutation_invalid", path);
  return path.slice(1).split("/").map((segment) => segment.replaceAll("~1", "/").replaceAll("~0", "~"));
}

function pointerParent(document, path) {
  const segments = pointerSegments(path);
  const key = segments.pop();
  let parent = document;
  for (const segment of segments) {
    if (parent === null || typeof parent !== "object" || !(segment in parent)) fail("web_release_corpus_mutation_invalid", path);
    parent = parent[segment];
  }
  return { parent, key };
}

function pointerValue(document, path) {
  let value = document;
  for (const segment of pointerSegments(path)) {
    if (value === null || typeof value !== "object" || !(segment in value)) fail("web_release_corpus_mutation_invalid", path);
    value = value[segment];
  }
  return value;
}

function mutate(base, mutation) {
  const document = structuredClone(base);
  if (mutation.op === "copy") {
    const value = structuredClone(pointerValue(document, mutation.path));
    const { parent, key } = pointerParent(document, mutation.target);
    if (Array.isArray(parent) && key === "-") parent.push(value); else parent[key] = value;
    return document;
  }
  const { parent, key } = pointerParent(document, mutation.path);
  if (mutation.op === "remove") {
    if (Array.isArray(parent)) parent.splice(Number(key), 1); else delete parent[key];
  } else if (mutation.op === "replace") parent[key] = structuredClone(mutation.value);
  else if (mutation.op === "add") {
    if (Array.isArray(parent) && key === "-") parent.push(structuredClone(mutation.value)); else parent[key] = structuredClone(mutation.value);
  } else fail("web_release_corpus_mutation_invalid", mutation.op);
  return document;
}

function dssePae(payloadType, payload) {
  const type = Buffer.from(payloadType, "utf8");
  return Buffer.concat([Buffer.from(`DSSEv1 ${type.length} `), type, Buffer.from(` ${payload.length} `), payload]);
}

function validateDsseVectors(corpus, casesById, envelopeValidators) {
  for (const vector of corpus.dsseVectors) {
    const contractCase = casesById.get(vector.caseId);
    const document = contractCase.document;
    const payload = canonicalBytes(document);
    const envelope = { payloadType: vector.payloadType, payload: payload.toString("base64"), signatures: [{ keyid: vector.keyId, sig: vector.signatureBase64 }] };
    const envelopeValidator = envelopeValidators.get(contractCase.contractId);
    if (envelopeValidator === undefined || !envelopeValidator(envelope)) fail("web_release_dsse_envelope_invalid", `${vector.id}: ${JSON.stringify(envelopeValidator?.errors ?? [])}`);
    const expectedKeyId = contractCase.contractId === "web-build-intent.v1"
      ? document.issuer.signingKeyId
      : document.predicate.runDetails.builder.kokoro_signingKeyId;
    if (vector.keyId !== expectedKeyId) fail("web_release_dsse_keyid_mismatch", vector.id);
    const pae = dssePae(vector.payloadType, payload);
    const actual = createHash("sha256").update(pae).digest("hex");
    if (actual !== vector.expectedPaeSha256) fail("web_release_dsse_vector_invalid", vector.id);
    let key;
    try { key = createPublicKey({ key: Buffer.from(vector.publicKeySpkiDerBase64, "base64"), format: "der", type: "spki" }); }
    catch { fail("web_release_dsse_vector_invalid", vector.id); }
    if (!verifySignature(null, pae, key, Buffer.from(vector.signatureBase64, "base64"))) fail("web_release_dsse_vector_invalid", vector.id);
  }
}

function schemaAjv() {
  return new Ajv2020({ allErrors: true, strict: true, validateFormats: false });
}

function validateRegistry(registry) {
  exactKeys(registry, ["breakingPolicy", "canonicalProfile", "contracts", "registryId", "schemaAuthority", "schemaVersion"], "web_release_registry_shape_invalid");
  if (registry.schemaVersion !== 1 || registry.registryId !== "kokoro.web-release-composition-contracts.v1" || registry.schemaAuthority !== "root.contract") fail("web_release_registry_shape_invalid");
  exactKeys(registry.canonicalProfile, ["canonicalization", "digestAlgorithm", "digestEncoding", "integerEncoding", "jsonProfile", "selfDigest", "timestampEncoding", "unknownFields"], "web_release_registry_shape_invalid");
  if (registry.canonicalProfile.jsonProfile !== "I-JSON-NFC-KOKORO-V1" || registry.canonicalProfile.canonicalization !== "RFC8785-JCS" || registry.canonicalProfile.digestAlgorithm !== "sha256" || registry.canonicalProfile.digestEncoding !== "sha256-lowercase-hex" || registry.canonicalProfile.integerEncoding !== "canonical-decimal-string" || registry.canonicalProfile.timestampEncoding !== "utc-rfc3339-millisecond" || registry.canonicalProfile.unknownFields !== "reject" || registry.canonicalProfile.selfDigest !== "forbidden") fail("web_release_registry_shape_invalid");
  exactKeys(registry.breakingPolicy, ["policy", "rule"], "web_release_registry_shape_invalid");
  if (registry.breakingPolicy.policy !== "immutable-major-schema") fail("web_release_registry_shape_invalid");
  const ids = registry.contracts.map(({ id }) => id).sort();
  if (canonicalize(ids) !== canonicalize(CONTRACT_IDS)) fail("web_release_registry_contract_set_invalid");
  for (const entry of registry.contracts) {
    exactKeys(entry, ["businessOwner", "consumers", "id", "lifecycle", "publisherRepository", "schemaId", "schemaPath", "signatureProfile"], "web_release_registry_entry_invalid");
    if (entry.lifecycle !== "contract-only" || !entry.schemaPath.startsWith("contract/spec/") || !entry.schemaPath.endsWith(".yaml")) fail("web_release_registry_entry_invalid", entry.id);
    const expected = CONTRACT_OWNERS.get(entry.id);
    if (expected === undefined || entry.businessOwner !== expected[0] || entry.publisherRepository !== expected[1] || entry.signatureProfile !== expected[2]) fail("web_release_registry_owner_invalid", entry.id);
  }
}

function validateDocument(contractId, document, validators) {
  validateIJson(document);
  const validator = validators.get(contractId);
  if (validator === undefined || !validator(document)) fail("web_release_positive_schema_invalid", `${contractId}: ${JSON.stringify(validator?.errors ?? [])}`);
}

function semanticValidate(contractId, document, related) {
  if (contractId === "product-surface-catalog.v1") validateCatalog(document);
  else if (contractId === "surface-inventory.v1") validateInventory(document, related.catalog);
  else if (contractId === "web-build-material-bundle.v1") validateMaterial(document);
  else if (contractId === "web-composition-registry.v1") validateCompositionRegistry(document, related.catalog);
  else if (contractId === "web-build-intent.v1") validateIntent(document, related);
  else if (contractId === "compiled-web-manifest.v1") validateManifest(document, related);
  else if (contractId === "web-artifact-provenance-profile.v1") validateProvenance(document, related);
}

function loadBundle(root, registryPath = resolve(root, DEFAULT_REGISTRY)) {
  const registry = readJson(registryPath, "web_release_registry_read_failed");
  validateRegistry(registry);
  const schemas = new Map();
  const ajv = schemaAjv();
  const validators = new Map();
  const envelopeValidators = new Map();
  for (const entry of registry.contracts) {
    const schema = readJson(resolve(root, entry.schemaPath), "web_release_schema_read_failed");
    if (schema.$id !== entry.schemaId) fail("web_release_registry_schema_id_invalid", entry.id);
    schemas.set(entry.id, schema);
    try {
      validators.set(entry.id, ajv.compile(schema));
      if (schema.$defs?.dsseEnvelope !== undefined) {
        envelopeValidators.set(entry.id, ajv.compile({ ...schema.$defs.dsseEnvelope, $defs: schema.$defs }));
      }
    }
    catch (error) { fail("web_release_schema_compile_invalid", `${entry.id}: ${error.message}`); }
  }
  return { registry, schemas, validators, envelopeValidators };
}

function loadGitBundle(root, revision) {
  const show = (path) => {
    try {
      return execFileSync("git", ["show", `${revision}:${path}`], {
        cwd: root,
        encoding: "utf8",
        timeout: 10_000,
        maxBuffer: 4 * 1024 * 1024,
        stdio: ["ignore", "pipe", "pipe"],
      });
    } catch {
      fail("web_release_breaking_baseline_invalid", `${revision}:${path}`);
    }
  };
  const registry = parseJsonSource(show(DEFAULT_REGISTRY), "web_release_breaking_baseline_invalid", `${revision}:${DEFAULT_REGISTRY}`);
  validateRegistry(registry);
  const schemas = new Map();
  for (const entry of registry.contracts) {
    schemas.set(entry.id, parseJsonSource(show(entry.schemaPath), "web_release_breaking_baseline_invalid", `${revision}:${entry.schemaPath}`));
  }
  return { registry, schemas };
}

export async function validateRepository(options = {}) {
  const root = resolve(options.root ?? process.cwd());
  const registryPath = resolve(root, options.registry ?? DEFAULT_REGISTRY);
  const corpusPath = isAbsolute(options.corpus ?? "") ? options.corpus : resolve(root, options.corpus ?? DEFAULT_CORPUS);
  const bundle = loadBundle(root, registryPath);
  const corpus = readJson(corpusPath, "web_release_corpus_read_failed");
  validateIJson(corpus);
  exactKeys(corpus, ["canonicalProfile", "canonicalVectors", "dsseVectors", "negativeCases", "positiveCases", "schema"], "web_release_corpus_shape_invalid");
  if (corpus.schema !== "kokoro.web-release-composition.corpus.v1" || corpus.positiveCases.length !== 8 || corpus.negativeCases.length !== 30 || corpus.canonicalVectors.length !== 8 || corpus.dsseVectors.length !== 2) fail("web_release_corpus_shape_invalid");
  const casesById = new Map(corpus.positiveCases.map((item) => [item.id, item]));
  if (casesById.size !== corpus.positiveCases.length || new Set(corpus.positiveCases.map(({ contractId }) => contractId)).size !== 8) fail("web_release_corpus_shape_invalid");
  const byContract = new Map(corpus.positiveCases.map((item) => [item.contractId, item.document]));
  const related = {
    catalog: byContract.get("product-surface-catalog.v1"), inventory: byContract.get("surface-inventory.v1"),
    material: byContract.get("web-build-material-bundle.v1"), toolchain: byContract.get("web-build-toolchain.v1"),
    registry: byContract.get("web-composition-registry.v1"), intent: byContract.get("web-build-intent.v1"), manifest: byContract.get("compiled-web-manifest.v1"),
  };
  for (const item of corpus.positiveCases) {
    validateDocument(item.contractId, item.document, bundle.validators);
    semanticValidate(item.contractId, item.document, related);
  }
  for (const vector of corpus.canonicalVectors) {
    const item = casesById.get(vector.caseId);
    if (item === undefined || digest(item.document) !== vector.expectedDigest) fail("web_release_canonical_vector_invalid", vector.id);
  }
  validateDsseVectors(corpus, casesById, bundle.envelopeValidators);
  for (const negative of corpus.negativeCases) {
    const base = casesById.get(negative.baseCaseId);
    if (base === undefined) fail("web_release_corpus_shape_invalid", negative.id);
    const document = mutate(base.document, negative.mutation);
    let code = null;
    try {
      validateDocument(base.contractId, document, bundle.validators);
      semanticValidate(base.contractId, document, related);
    } catch (error) {
      if (!(error instanceof WebReleaseContractError)) throw error;
      code = error.code;
    }
    if (code !== negative.expectedCode) fail("web_release_negative_vector_invalid", `${negative.id}: ${code ?? "accepted"}`);
  }
  return { contracts: bundle.registry.contracts.length, positiveCases: corpus.positiveCases.length, negativeCases: corpus.negativeCases.length, canonicalVectors: corpus.canonicalVectors.length, dsseVectors: corpus.dsseVectors.length };
}

export function assertFrozenV1Compatible(baseline, candidate) {
  const baselineRows = new Map(baseline.registry.contracts.map((entry) => [entry.id, entry]));
  const candidateRows = new Map(candidate.registry.contracts.map((entry) => [entry.id, entry]));
  for (const [id, row] of baselineRows) {
    const next = candidateRows.get(id);
    if (next === undefined || canonicalize(row) !== canonicalize(next)) fail("web_release_v1_registry_breaking", id);
    const oldSchema = baseline.schemas.get(id); const newSchema = candidate.schemas.get(id);
    if (oldSchema === undefined || newSchema === undefined || canonicalize(oldSchema) !== canonicalize(newSchema)) fail("web_release_v1_schema_breaking", id);
  }
}

function parseArguments(argv) {
  const options = { root: process.cwd(), registry: DEFAULT_REGISTRY, corpus: DEFAULT_CORPUS, baselineRoot: null, breakingAgainst: null };
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index]; const value = argv[index + 1];
    const key = { "--root": "root", "--registry": "registry", "--corpus": "corpus", "--baseline-root": "baselineRoot", "--breaking-against": "breakingAgainst" }[flag];
    if (key === undefined || value === undefined) fail("web_release_arguments_invalid", flag ?? "");
    options[key] = value;
  }
  return options;
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const result = await validateRepository(options);
  if (options.baselineRoot !== null) {
    const baselineRoot = resolve(options.baselineRoot);
    const candidateRoot = resolve(options.root);
    assertFrozenV1Compatible(loadBundle(baselineRoot), loadBundle(candidateRoot));
  }
  if (options.breakingAgainst !== null) {
    const root = resolve(options.root);
    assertFrozenV1Compatible(loadGitBundle(root, options.breakingAgainst), loadGitBundle(root, "HEAD"));
  }
  process.stdout.write(`web_release_contracts_ok:${result.contracts} contracts, ${result.positiveCases}+${result.negativeCases} corpus, ${result.canonicalVectors} canonical, ${result.dsseVectors} dsse\n`);
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  main().catch((error) => {
    process.stderr.write(`${error instanceof WebReleaseContractError ? error.message : error.stack ?? error.message}\n`);
    process.exitCode = 1;
  });
}
