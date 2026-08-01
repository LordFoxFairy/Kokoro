#!/usr/bin/env node

import { createHash, createPublicKey, verify as verifySignature } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { isAbsolute, resolve } from "node:path";
import { pathToFileURL } from "node:url";

import Ajv2020 from "../../contract/node_modules/ajv/dist/2020.js";

const DEFAULT_REGISTRY = "contract/registry/web-release-composition.yaml";
const DEFAULT_CORPUS = "contract/corpus/web-release-composition-v1.json";
const DEFAULT_TRUST_ANCHORS = "contract/registry/trusted-web-release-producers.yaml";
const CONTRACT_IDS = [
  "activation-authority-snapshot.v1",
  "activation-eligibility-evidence.v1",
  "launch-product-profile.v1",
  "product-surface-catalog.v1",
  "release-certification-instance.v1",
  "release-certification-revocation.v1",
  "site-release-candidate.v1",
  "site-release.v1",
  "surface-inventory.v1",
  "web-artifact-provenance-profile.v1",
  "web-build-intent.v1",
  "web-build-material-bundle.v1",
  "web-build-toolchain.v1",
  "web-composition-registry.v1",
  "compiled-web-manifest.v1",
].sort();
const CONTRACT_OWNERS = new Map([
  ["activation-authority-snapshot.v1", ["platform.site", "kokoro-platform", "digest-bound-reference"]],
  ["activation-eligibility-evidence.v1", ["platform.site", "kokoro-platform", "digest-bound-reference"]],
  ["launch-product-profile.v1", ["platform.site", "kokoro-platform", "digest-bound-reference"]],
  ["product-surface-catalog.v1", ["platform.product-catalog", "kokoro-platform", "none"]],
  ["release-certification-instance.v1", ["release.certification", "kokoro-platform", "dsse-release-certification-instance-v1"]],
  ["release-certification-revocation.v1", ["release.certification", "kokoro-platform", "dsse-release-certification-revocation-v1"]],
  ["site-release-candidate.v1", ["platform.site", "kokoro-platform", "digest-bound-reference"]],
  ["site-release.v1", ["platform.site", "kokoro-platform", "digest-bound-reference"]],
  ["surface-inventory.v1", ["platform.site", "kokoro-platform", "none"]],
  ["web-build-material-bundle.v1", ["platform.site", "kokoro-platform", "digest-bound-reference"]],
  ["web-build-toolchain.v1", ["web.release-composition", "kokoro-web", "digest-bound-reference"]],
  ["web-composition-registry.v1", ["web.release-composition", "kokoro-web", "digest-bound-reference"]],
  ["web-build-intent.v1", ["platform.site", "kokoro-platform", "dsse-kokoro-web-build-intent-v1"]],
  ["compiled-web-manifest.v1", ["web.release-composition", "kokoro-web", "provenance-bound"]],
  ["web-artifact-provenance-profile.v1", ["web.release-composition", "kokoro-web", "dsse-in-toto-slsa-provenance-v1"]],
]);
const TRUST_ROLE_CAPABILITIES = new Map([
  ["web-build-intent-signer", { contracts: ["web-build-intent.v1"], payloads: ["application/vnd.kokoro.web-build-intent.v1+json"], receipts: [] }],
  ["release-certification-instance-signer", { contracts: ["release-certification-instance.v1"], payloads: ["application/vnd.kokoro.release-certification-instance.v1+json"], receipts: [] }],
  ["release-certification-revocation-signer", { contracts: ["release-certification-revocation.v1"], payloads: ["application/vnd.kokoro.release-certification-revocation.v1+json"], receipts: [] }],
  ["web-artifact-provenance-attestor", { contracts: ["web-artifact-provenance-profile.v1"], payloads: ["application/vnd.in-toto+json"], receipts: [] }],
  ["platform-site-authority-reader", { contracts: [], payloads: ["application/vnd.kokoro.owner-live-read-receipt.v1+json"], receipts: ["candidate", "active-pointer"] }],
  ["release-certification-authority-reader", { contracts: [], payloads: ["application/vnd.kokoro.owner-live-read-receipt.v1+json"], receipts: ["certification"] }],
  ["root-trust-authority-reader", { contracts: [], payloads: ["application/vnd.kokoro.owner-live-read-receipt.v1+json"], receipts: ["producer-registry", "trust-policy", "key-status"] }],
]);
const DSSE_CONTRACT_ROLES = new Map([...TRUST_ROLE_CAPABILITIES]
  .flatMap(([role, capability]) => capability.contracts.map((contractId) => [contractId, role])));
const RECEIPT_KIND_ROLES = new Map([...TRUST_ROLE_CAPABILITIES]
  .flatMap(([role, capability]) => capability.receipts.map((kind) => [kind, role])));
const ACTIVATION_FRESHNESS_LEASE_MILLISECONDS = 5_000;
const ACTIVATION_MAX_SNAPSHOT_AGE_MILLISECONDS = 120_000;
const SECRET_FRAGMENT = /(?:^|_)(?:api_?key|credential|password|private|secret|token)(?:_|$)/iu;
const FROZEN_NEGATIVE_CASE_DIGESTS = new Map(`
catalog-unknown-field sha256:ae9ae9cd8e89067cd28d8e93cacc538f9ecfc991c5fc774029175094490fb762
catalog-duplicate-surface sha256:b3d55aa4fe6e4910ac615033bfa2e1af484a19b892b759f58ac5c4065048531d
catalog-dangling-journey sha256:b89219959dd3f08fafde4c5ba5d37ba1e0f4ad15a7de2d6826fbcc6203d70339
inventory-overlap sha256:cca05b1dbc9b43fd1df58437dceeaf79d6b5dd693068cfb634296542a4c34319
inventory-incomplete sha256:2c007e7f80e8ba01c28d0e76a5e529170129e417c08de7ca7f4369e4377b13c0
inventory-unknown sha256:609173e12cc5285858d5a8af1b4afb26fd4f27dc5dc5318e0e3d646c08cacf9e
material-secret-key sha256:48ed5a3b5e8aaa8a25bdada389b9788dbe724e68150c25c5059ea2742762e759
material-unscanned sha256:2b467071b2dd79d6c3c54a06aaf35b54d2ecf7a399e922865a9666d187553c82
toolchain-tagged-artifact sha256:0bc28fe7388d6487c227f0b9021bde51ce38b8217ab2faada828f45ce48ac954
toolchain-network-url sha256:acbb35f7cff1a436f9a42a78add78277952afe9a8f5bf4911b395c436a6af228
intent-selects-unit sha256:09a4a481d86a787bb8962a27bfddc5fcce0e0bcd0f272a8d60c86df430cc109a
intent-expires sha256:03a0085e357ddfe0bafffddb97204e3fd9a4b2883668cbcb3f73b64676ae441f
intent-self-digest sha256:12635e451a8964d80e9a24f6a8cf8ee382becab968cf06599c8d0ab5433f2e51
manifest-unit-cycle sha256:f51500801927b6b284ee574e3d1dace66f9370843e59bf723e5f75f524b5d8ec
manifest-route-conflict sha256:818cc7cc194cbb8ecfd9813857e668cdbfca0eeac155283966a8d93961b76be8
manifest-disabled-surface sha256:e8c103579452eb94b2786775a3356f32fb8c35450ebe4a6f3907d21faf466dbd
manifest-orphan-package sha256:cb2045c7ab0addd03270d03ade40b8fc8c62984b979b3280a8a094f6e0b9c32e
provenance-toolchain-mismatch sha256:1756dd4fbc516afeaf6a8e9f819f2e09ef974cd1fcb3f4954c64a7bcf576ded2
catalog-duplicate-owner sha256:f7c4e77dc4ece591a20d03b89f7d91dbc8270a90a1a16968476dd13b5060363c
catalog-surface-cycle sha256:8b5f0536f1859121374c68d2956afa5e2973f62c74e491d55c9f574a71637483
material-duplicate-config-key sha256:a98c632277c02da04cd85c1a3defb543a1bef89f0aa7ee3758971041f6ac6cb7
material-origin-mismatch sha256:d016452d924e0b897e382f91d243c7b98327975d1805f44c518d503a8342edf9
registry-duplicate-unit sha256:6baf8c7eb41db717660377d1b3d48611f46fcf85534781cc091df9a80e371f81
registry-unit-cycle sha256:275836151168d374d08881858d471b5d69516543e8d0fe873df697c9c854cb8f
registry-dangling-package sha256:7ec5f97b1bc4e1063908d89bf4f9e8ab9cd659af1b4083d2c5efb06ccc58e8d4
registry-route-conflict sha256:a65ac52ba3ad146623d431caa6b1052e9b90aa4553cf02de8ebbe9cd752c316a
manifest-measured-tool-mismatch sha256:25ec36fac85f9e99ff55ec2cdb6af22f537b56057e9acfd4f30ac4c056e4b9e4
manifest-missing-bff-closure sha256:0de511f70b6a088d64e0f3fadd904a3b622743d9cbcf3d27984d456883f00ae9
provenance-site-mismatch sha256:21adc01a06e9d52ff8fdf27d0813409bbbf3ed91e0c9b5d9f6bb7075fb1a75e3
provenance-dependency-role-mismatch sha256:4bcfd849415e5bafbf4866d81117c982987bb7882d6111819692c4047ea2b547
profile-inventory-cycle sha256:792cb9f18d34cee514bc0416c7663e411c3d165ababec5bde492e52ebd23c9bd
profile-unknown-surface sha256:f1150dd04c6bfb3eb8ae13a3e02269ac2d702236b249a14e967016116bf4bbfe
profile-incomplete-journey sha256:d79a923fb069829b53591e9fc0b6e4057a94f00411acd698aa1a1f51449cb85d
candidate-inventory-cycle sha256:78a4003566b2dc79bc493b8373488d7cfe775f5cf6bbab85f9b3de9dc665d176
candidate-profile-mismatch sha256:c10f048d1e17b3e8b5517c60129947aed51ed1676a1cad16e002578ba2f1ac47
candidate-model-role-missing sha256:469b5a3f01f62c5b4694b5e03cac518ea9585b1b63e9dfdfc0d8e895156fa0aa
inventory-candidate-mismatch sha256:ffaaf530e45d996db90a33619ae5198ecc021111b782159e3c065e6a2328c3fc
inventory-profile-mismatch sha256:f08d06454a951794072c2f030585137e80077b395ecfbac33c63ed5a58473e03
registry-bff-authority-overlap sha256:a0ecf61a9667b4d03751b9332adcf463cbfbfe63b0465c2ceb24e9ddc61c1d85
intent-model-inventory-mismatch sha256:728460eb27c58c3044140756cc7429928b49c3c7f804c76faea73a819da2a055
manifest-bff-family-missing sha256:3a87e55cf229faff3ac0388ca7591b02b854e554b13e5854fd021b2ec59b625b
provenance-artifact-mismatch sha256:3c4747939e52bcf3900235552d3af0c60f07ebe89a879e9feb88da5bfdc1ad44
certification-expired-before-generation sha256:0868b89f12a84185538fccaef7f8fc7de45754137ca4aa1f2f7c63a3ef1b6780
certification-candidate-epoch-mismatch sha256:e3203f28ac0d31551fd1298d6343236d42e515af677ceb6880738398149e1d79
site-release-bootstrap-mismatch sha256:856779c9bc1abf7cbded12f7e57d0750f1ff5c80bbc340b367590f71017d5fb8
catalog-surface-scope-missing sha256:a2583ec4bc91b4d4acfa6d08dccc2aa18c1f1dfa972dbbf468a4e72aa2d19c6f
catalog-journey-cycle sha256:a53ae73987af16699c08823eeff47f7c4e03fb664d66b1c2b24c191476942edc
profile-missing-core-surface sha256:c0d6b2bda37877b5c206d4a976c12b0d0641d22c930646524b2dad6f9517aa92
registry-cross-group-bff-overlap sha256:e5428a1182ec86e85d67ee34b51c4270a5116e537bff585152fafe6f200b8d7b
manifest-cross-group-bff-overlap sha256:f385951d5aafdcecff02fe493a38498f2abc0e33e065e7a8cc0735a0860e6134
provenance-final-certification-cycle sha256:9c320b782af8e5ffa8564552602e33f3f8f100d94684914553fe4cd1e9d7456a
certification-inactive-key sha256:19b1f59b6da167cacd67fc3c18ae6ee7c68bfb4028a4982d133a0c63effc555b
certification-invalid-key-window sha256:47fa9f5a543e52fc821c6e04437e2144aca8c796057b60309e9ec8b8c37a0bce
revocation-certification-mismatch sha256:78cb27ffd21c2aab4ac92e46a88b52bb972dd36d85ce8e3b4f4b0b7f45039c0e
revocation-nonmonotonic-epoch sha256:05ed56a557820d9a27dbe4c2bc44759b2d13c2dde993910ecc5f228a27e3fda8
activation-authority-material-mismatch sha256:18f3d60fa5bd55812a16069d1b8f2d0472c7931a0c9a0891987deba7570729bc
activation-eligibility-material-mismatch sha256:127b849f5481e028a4dddf75a53e643b7a98524a3c7234166bf7a7dd709d963d
site-release-before-certification sha256:e2f371c928b322577c73063938e19ce849a5fdfecba15814bae2a8580d159c66
activation-first-pointer-must-be-null sha256:0752cf0b97721035abc167fdcd7e19c20e884222217631739b7911d0ab995fb5
`.trim().split("\n").map((row) => row.split(" ")));
const FROZEN_BLOCKED_ACTIVATION_SCENARIOS = new Map([
  ["candidate-revoked-between-authority-reads", {
    expectedCode: "web_release_activation_candidate_epoch_invalid",
    identity: { candidateState: "revoked", certificationState: "active", certificationRevocationEpoch: "0", keyStatus: "active", producerRegistryEpoch: "4", trustPolicyEpoch: "9", expiredAtRead: false },
  }],
  ["certification-revoked-between-authority-reads", {
    expectedCode: "web_release_activation_certification_revoked",
    identity: { candidateState: "active", certificationState: "revoked", certificationRevocationEpoch: "1", keyStatus: "active", producerRegistryEpoch: "4", trustPolicyEpoch: "9", expiredAtRead: false },
  }],
  ["key-revoked-between-authority-reads", {
    expectedCode: "web_release_activation_key_invalid",
    identity: { candidateState: "active", certificationState: "active", certificationRevocationEpoch: "0", keyStatus: "revoked", producerRegistryEpoch: "4", trustPolicyEpoch: "9", expiredAtRead: false },
  }],
  ["key-suspended-between-authority-reads", {
    expectedCode: "web_release_activation_key_invalid",
    identity: { candidateState: "active", certificationState: "active", certificationRevocationEpoch: "0", keyStatus: "suspended", producerRegistryEpoch: "4", trustPolicyEpoch: "9", expiredAtRead: false },
  }],
  ["producer-registry-epoch-between-authority-reads", {
    expectedCode: "web_release_activation_registry_epoch_invalid",
    identity: { candidateState: "active", certificationState: "active", certificationRevocationEpoch: "0", keyStatus: "active", producerRegistryEpoch: "5", trustPolicyEpoch: "9", expiredAtRead: false },
  }],
  ["trust-policy-epoch-between-authority-reads", {
    expectedCode: "web_release_activation_policy_epoch_invalid",
    identity: { candidateState: "active", certificationState: "active", certificationRevocationEpoch: "0", keyStatus: "active", producerRegistryEpoch: "4", trustPolicyEpoch: "10", expiredAtRead: false },
  }],
  ["certification-expired-between-authority-reads", {
    expectedCode: "web_release_activation_certification_expired",
    identity: { candidateState: "active", certificationState: "active", certificationRevocationEpoch: "0", keyStatus: "active", producerRegistryEpoch: "4", trustPolicyEpoch: "9", expiredAtRead: true },
  }],
]);

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

function validateNegativeCaseCoverage(negativeCases) {
  if (!Array.isArray(negativeCases) || negativeCases.length !== FROZEN_NEGATIVE_CASE_DIGESTS.size) {
    fail("web_release_negative_coverage_invalid");
  }
  for (const negative of negativeCases) {
    exactKeys(negative, ["baseCaseId", "expectedCode", "id", "mutation"], "web_release_negative_coverage_invalid");
  }
  const ids = unique(negativeCases.map(({ id }) => id), "web_release_negative_coverage_invalid");
  if (canonicalSet(ids) !== canonicalSet(FROZEN_NEGATIVE_CASE_DIGESTS.keys())) {
    fail("web_release_negative_coverage_invalid");
  }
  for (const negative of negativeCases) {
    const material = {
      baseCaseId: negative.baseCaseId,
      mutation: negative.mutation,
      expectedCode: negative.expectedCode,
    };
    if (digest(material) !== FROZEN_NEGATIVE_CASE_DIGESTS.get(negative.id)) {
      fail("web_release_negative_coverage_invalid", negative.id);
    }
  }
}

function blockedActivationSemanticIdentity(snapshot) {
  return {
    candidateState: snapshot.candidate.state,
    certificationState: snapshot.certification.state,
    certificationRevocationEpoch: snapshot.certification.revocationEpoch,
    keyStatus: snapshot.trust.keyStatus,
    producerRegistryEpoch: snapshot.trust.producerRegistryEpoch,
    trustPolicyEpoch: snapshot.trust.trustPolicyEpoch,
    expiredAtRead: snapshot.readAt === snapshot.certification.validUntil,
  };
}

function validateBlockedActivationScenarioCoverage(blockedScenarios) {
  if (!Array.isArray(blockedScenarios) || blockedScenarios.length !== FROZEN_BLOCKED_ACTIVATION_SCENARIOS.size) {
    fail("web_release_activation_scenario_invalid");
  }
  for (const blocked of blockedScenarios) {
    exactKeys(blocked, ["expectedCode", "id", "snapshot"], "web_release_activation_scenario_invalid");
  }
  const ids = unique(blockedScenarios.map(({ id }) => id), "web_release_activation_scenario_invalid");
  if (canonicalSet(ids) !== canonicalSet(FROZEN_BLOCKED_ACTIVATION_SCENARIOS.keys())) {
    fail("web_release_activation_scenario_invalid");
  }
  for (const blocked of blockedScenarios) {
    const frozen = FROZEN_BLOCKED_ACTIVATION_SCENARIOS.get(blocked.id);
    if (blocked.expectedCode !== frozen.expectedCode ||
        canonicalize(blockedActivationSemanticIdentity(blocked.snapshot)) !== canonicalize(frozen.identity)) {
      fail("web_release_activation_scenario_invalid", blocked.id);
    }
  }
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
    ensureRefs([journey.entrySurfaceRef, ...journey.requiredSurfaceRefs], surfaces); ensureRefs(journey.requiredJourneyRefs, journeys); ensureRefs(journey.operationFamilyRefs, operations);
  }
  assertDag(new Map(catalog.products.map((item) => [item.productRef, item])), "requiredProductRefs", "web_release_catalog_reference_invalid", "web_release_catalog_cycle");
  assertDag(new Map(catalog.surfaces.map((item) => [item.surfaceRef, item])), "requiredSurfaceRefs", "web_release_catalog_reference_invalid", "web_release_catalog_cycle");
  assertDag(new Map(catalog.canonicalJourneys.map((item) => [item.journeyRef, item])), "requiredJourneyRefs", "web_release_catalog_reference_invalid", "web_release_catalog_cycle");
}

function digestReference(reference, document, refField, code) {
  if (reference.ref !== document[refField] || reference.digest !== digest(document)) fail(code, refField);
}

function validateProfile(profile, catalog) {
  digestReference(profile.productSurfaceCatalog, catalog, "catalogRevisionRef", "web_release_profile_reference_invalid");
  if (catalog.state !== "published") fail("web_release_profile_reference_invalid", "unpublished catalog");
  const surfaces = new Map(catalog.surfaces.map((surface) => [surface.surfaceRef, surface]));
  const enabled = unique(profile.enabledSurfaceRefs, "web_release_profile_surface_invalid");
  for (const surface of catalog.surfaces) {
    if (surface.scopeClass === "core-always" && !enabled.has(surface.surfaceRef)) fail("web_release_profile_surface_invalid", surface.surfaceRef);
  }
  for (const surfaceRef of enabled) {
    const surface = surfaces.get(surfaceRef);
    if (surface === undefined || surface.requiredSurfaceRefs.some((required) => !enabled.has(required))) fail("web_release_profile_surface_invalid", surfaceRef);
  }
  const products = new Map(catalog.products.map((product) => [product.productRef, product]));
  const requiredProducts = new Set([...enabled].map((surfaceRef) => surfaces.get(surfaceRef).productRef));
  const visitProduct = (productRef) => {
    const product = products.get(productRef);
    if (product === undefined || product.surfaceRefs.some((surfaceRef) => !enabled.has(surfaceRef))) fail("web_release_profile_surface_invalid", productRef);
    for (const requiredProductRef of product.requiredProductRefs) {
      if (!requiredProducts.has(requiredProductRef)) {
        requiredProducts.add(requiredProductRef);
        visitProduct(requiredProductRef);
      }
    }
  };
  for (const productRef of [...requiredProducts]) visitProduct(productRef);
  const journeyRefs = new Set();
  for (const surfaceRef of enabled) {
    const surface = surfaces.get(surfaceRef);
    for (const journeyRef of surface.canonicalJourneyRefs) journeyRefs.add(journeyRef);
    for (const journeyRef of products.get(surface.productRef).canonicalJourneyRefs) journeyRefs.add(journeyRef);
  }
  const journeys = new Map(catalog.canonicalJourneys.map((journey) => [journey.journeyRef, journey]));
  const visitJourney = (journeyRef) => {
    const journey = journeys.get(journeyRef);
    if (journey === undefined || !enabled.has(journey.entrySurfaceRef) || journey.requiredSurfaceRefs.some((surfaceRef) => !enabled.has(surfaceRef))) fail("web_release_profile_journey_invalid", journeyRef);
    for (const requiredJourneyRef of journey.requiredJourneyRefs) {
      if (!journeyRefs.has(requiredJourneyRef)) {
        journeyRefs.add(requiredJourneyRef);
        visitJourney(requiredJourneyRef);
      }
    }
  };
  for (const journeyRef of [...journeyRefs]) visitJourney(journeyRef);
  const expected = [...journeyRefs].sort().map((journeyRef) => ({ journeyRef, revision: journeys.get(journeyRef).revision }));
  unique(profile.journeyClosure.journeys.map(({ journeyRef }) => journeyRef), "web_release_profile_journey_invalid");
  if (canonicalRows(profile.journeyClosure.journeys, ({ journeyRef }) => journeyRef) !== canonicalize(expected) || profile.journeyClosure.digest !== digest(expected)) fail("web_release_profile_journey_invalid");
}

function validateCandidate(candidate, related) {
  digestReference(candidate.launchProductProfile, related.profile, "profileRevisionRef", "web_release_candidate_reference_invalid");
  digestReference(candidate.productSurfaceCatalog, related.catalog, "catalogRevisionRef", "web_release_candidate_reference_invalid");
  if (candidate.launchProductProfile.digest !== digest(related.profile) || related.profile.productSurfaceCatalog.digest !== candidate.productSurfaceCatalog.digest) fail("web_release_candidate_reference_invalid");
  unique(candidate.modelRequirements.map(({ modelRoleRef }) => modelRoleRef), "web_release_candidate_model_invalid");
  const enabled = new Set(related.profile.enabledSurfaceRefs);
  const expectedRoles = new Set(related.catalog.surfaces.filter(({ surfaceRef }) => enabled.has(surfaceRef)).flatMap(({ requiredModelRoleRefs }) => requiredModelRoleRefs));
  if (canonicalSet(expectedRoles) !== canonicalSet(candidate.modelRequirements.map(({ modelRoleRef }) => modelRoleRef))) fail("web_release_candidate_model_invalid", "role coverage");
  for (const requirement of candidate.modelRequirements) {
    if (requirement.modelInventory.ref === requirement.modelCatalog.ref || requirement.modelInventory.digest === requirement.modelCatalog.digest) fail("web_release_candidate_model_invalid", requirement.modelRoleRef);
  }
  const bindings = candidate.businessBindings;
  if (bindings.webBuildMaterialBundle.ref !== related.material.bundleRef || bindings.webBuildMaterialBundle.digest !== digest(related.material)) fail("web_release_candidate_reference_invalid", "material");
}

function validateInventory(inventory, related) {
  const { catalog, profile, candidate } = related;
  digestReference(inventory.siteReleaseCandidate, candidate, "candidateRef", "web_release_inventory_candidate_invalid");
  digestReference(inventory.launchProductProfile, profile, "profileRevisionRef", "web_release_inventory_profile_invalid");
  digestReference(inventory.productSurfaceCatalog, catalog, "catalogRevisionRef", "web_release_inventory_catalog_invalid");
  if (inventory.siteRef !== candidate.siteRef) fail("web_release_inventory_candidate_invalid", "site");
  const enabled = unique(inventory.enabledSurfaceRefs, "web_release_inventory_partition_invalid");
  const disabled = unique(inventory.disabledSurfaceRefs, "web_release_inventory_partition_invalid");
  if ([...enabled].some((ref) => disabled.has(ref))) fail("web_release_inventory_partition_invalid");
  const partition = [...enabled, ...disabled].sort();
  const expected = catalog.surfaces.map(({ surfaceRef }) => surfaceRef).sort();
  if (canonicalize(partition) !== canonicalize(expected)) fail("web_release_inventory_partition_invalid");
  if (canonicalSet(enabled) !== canonicalSet(profile.enabledSurfaceRefs) || canonicalSet(inventory.shellRequirementRefs) !== canonicalSet(profile.shellRequirementRefs)) fail("web_release_inventory_profile_invalid");
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
  unique(registry.packages.map(({ name, version }) => `${name}\0${version}`), "web_release_composition_registry_identity_invalid");
  const knownSurfaces = new Set(catalog.surfaces.map(({ surfaceRef }) => surfaceRef));
  const surfaceProviders = [];
  const shellProviders = [];
  const routeRefs = [];
  const pathnames = [];
  const navigationRefs = [];
  const bffGroupRefs = [];
  const sameOriginOperations = [];
  const downstreamOperations = [];
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
      sameOriginOperations.push(...group.sameOriginHandlerOperationIds);
      downstreamOperations.push(...group.downstreamOperationIds);
      if (group.sameOriginHandlerOperationIds.some((operationId) => group.downstreamOperationIds.includes(operationId))) fail("web_release_composition_registry_identity_invalid", group.groupRef);
      if (!catalog.operationFamilyRefs.includes(group.operationFamilyRef)) fail("web_release_composition_registry_reference_invalid", group.operationFamilyRef);
    }
    for (const requirement of unit.modelCatalogRequirements) {
      if (!unit.providesSurfaceRefs.includes(requirement.surfaceRef)) fail("web_release_composition_registry_reference_invalid", requirement.surfaceRef);
      modelRequirements.push(`${requirement.surfaceRef}\0${requirement.modelRoleRef}`);
    }
  }
  unique(surfaceProviders, "web_release_composition_registry_identity_invalid");
  unique(shellProviders, "web_release_composition_registry_identity_invalid");
  unique(routeRefs, "web_release_composition_registry_route_conflict");
  unique(pathnames, "web_release_composition_registry_route_conflict");
  unique(navigationRefs, "web_release_composition_registry_identity_invalid");
  unique(bffGroupRefs, "web_release_composition_registry_identity_invalid");
  unique(sameOriginOperations, "web_release_composition_registry_identity_invalid");
  unique(downstreamOperations, "web_release_composition_registry_identity_invalid");
  if (sameOriginOperations.some((operationId) => downstreamOperations.includes(operationId))) fail("web_release_composition_registry_identity_invalid", "cross-group BFF authority overlap");
  unique(modelRequirements, "web_release_composition_registry_identity_invalid");
  if ([...packages.keys()].some((ref) => !usedPackages.has(ref))) fail("web_release_composition_registry_reference_invalid", "orphan package");
  assertDag(units, "requiresUnitRefs", "web_release_composition_registry_reference_invalid", "web_release_composition_registry_cycle");
}

function validateIntent(intent, related) {
  const pairs = [
    [intent.siteReleaseCandidate, related.candidate, "candidateRef"],
    [intent.launchProductProfile, related.profile, "profileRevisionRef"],
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
  if (related.inventory.siteRef !== intent.siteRef || related.material.siteRef !== intent.siteRef || related.candidate.siteRef !== intent.siteRef ||
      related.inventory.siteReleaseCandidate.ref !== intent.siteReleaseCandidate.ref || related.inventory.launchProductProfile.ref !== intent.launchProductProfile.ref ||
      related.candidate.candidateAuthorizationEpoch !== intent.candidateAuthorizationEpoch || related.candidate.environment !== intent.environment) fail("web_release_intent_context_invalid");
  unique(intent.modelRequirements.map(({ modelRoleRef }) => modelRoleRef), "web_release_intent_reference_invalid");
  if (canonicalRows(intent.modelRequirements, ({ modelRoleRef }) => modelRoleRef) !== canonicalRows(related.candidate.modelRequirements, ({ modelRoleRef }) => modelRoleRef)) fail("web_release_intent_reference_invalid", "model requirements");
  const bindingPairs = [[intent.webBuildMaterialBundle, "webBuildMaterialBundle"], [intent.siteConfig, "siteConfig"], [intent.legalPolicy, "legalPolicy"], [intent.salesPolicy, "salesPolicy"], [intent.capabilityAssignment, "capabilityAssignment"]];
  for (const [actual, key] of bindingPairs) if (canonicalize(actual) !== canonicalize(related.candidate.businessBindings[key])) fail("web_release_intent_reference_invalid", key);
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
  const bffOperationGroups = selectedUnits.flatMap((unit) => unit.bffOperationGroups.map((group) => ({ ...group, unitRef: unit.unitRef })));
  const bootstrapRequirements = [...new Set(selectedUnits.flatMap(({ bootstrapRequirements }) => bootstrapRequirements))].sort();
  const modelsByRole = new Map(intent.modelRequirements.map((requirement) => [requirement.modelRoleRef, requirement]));
  const modelCatalogRequirements = selectedUnits.flatMap((unit) => unit.modelCatalogRequirements.map((requirement) => {
    const model = modelsByRole.get(requirement.modelRoleRef);
    if (model === undefined) fail("web_release_manifest_registry_projection_invalid", requirement.modelRoleRef);
    return { ...requirement, modelInventory: model.modelInventory, modelCatalog: model.modelCatalog };
  }));
  return { projectedUnits, projectedPackages, routes, navigation, bffOperationGroups, bootstrapRequirements, modelCatalogRequirements };
}

function validateManifest(manifest, related) {
  const { inventory, intent, registry, toolchain } = related;
  if (manifest.intentRef !== intent.intentRef || manifest.buildIntentDigest !== digest(intent) || canonicalize(manifest.siteReleaseCandidate) !== canonicalize(intent.siteReleaseCandidate)) fail("web_release_manifest_reference_invalid", "intent");
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
  const sameOriginOperations = [];
  const downstreamOperations = [];
  for (const group of manifest.bffOperationGroups) {
    if (!units.has(group.unitRef)) fail("web_release_manifest_reference_invalid", group.groupRef);
    sameOriginOperations.push(...group.sameOriginHandlerOperationIds);
    downstreamOperations.push(...group.downstreamOperationIds);
    if (group.sameOriginHandlerOperationIds.some((operationId) => group.downstreamOperationIds.includes(operationId))) fail("web_release_manifest_bff_conflict", group.groupRef);
  }
  unique(sameOriginOperations, "web_release_manifest_bff_conflict");
  unique(downstreamOperations, "web_release_manifest_bff_conflict");
  if (sameOriginOperations.some((operationId) => downstreamOperations.includes(operationId))) fail("web_release_manifest_bff_conflict", "cross-group BFF authority overlap");
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
    [manifest.modelCatalogRequirements, projection.modelCatalogRequirements, ({ surfaceRef, modelRoleRef }) => `${surfaceRef}\0${modelRoleRef}`],
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
  if (parameters.siteRef !== related.intent.siteRef || parameters.releaseCandidateRef !== related.intent.siteReleaseCandidate.ref ||
      parameters.releaseCandidateRef !== related.manifest.siteReleaseCandidate.ref || parameters.candidateAuthorizationEpoch !== related.intent.candidateAuthorizationEpoch) fail("web_release_provenance_context_mismatch");
  const artifactDigest = provenance.predicate.runDetails.webArtifactDigest;
  if (artifactDigest !== `sha256:${provenance.subject[0].digest.sha256}`) fail("web_release_provenance_artifact_invalid");
  const dependencies = new Map(provenance.predicate.buildDefinition.resolvedDependencies.map(({ uri, digest: value }) => [uri, value.sha256]));
  if (dependencies.size !== provenance.predicate.buildDefinition.resolvedDependencies.length) fail("web_release_provenance_reference_invalid", "duplicate dependency");
  const unprefixed = (value) => value.slice("sha256:".length);
  const sourceUri = (role) => `git+https://source.kokoro.dev/repositories/${encodeURIComponent(related.toolchain.baseSource.repositoryRef)}#${role}`;
  const ociUri = (role, { repositoryRef }) => `oci://registry.kokoro.dev/${role}/${encodeURIComponent(repositoryRef)}`;
  const packageUri = ({ packageRef, name, version }) =>
    `pkg:npm/${encodeURIComponent(name).replaceAll("%2F", "/")}@${version}?kokoro_package_ref=${encodeURIComponent(packageRef)}`;
  const expectedDependencyRows = [
    [sourceUri("commit"), unprefixed(related.toolchain.baseSource.commitDigest)],
    [sourceUri("tree"), unprefixed(related.toolchain.baseSource.treeDigest)],
    [`kokoro:template/${related.toolchain.baseTemplate.ref}`, unprefixed(related.toolchain.baseTemplate.digest)],
    [`kokoro:material-bundle/${related.intent.webBuildMaterialBundle.ref}`, unprefixed(related.intent.webBuildMaterialBundle.digest)],
    [ociUri("compiler", related.toolchain.compilerArtifact), unprefixed(related.toolchain.compilerArtifact.digest)],
    [ociUri("inspector", related.toolchain.inspectorArtifact), unprefixed(related.toolchain.inspectorArtifact.digest)],
    [ociUri("build-sandbox", related.toolchain.buildSandboxImage), unprefixed(related.toolchain.buildSandboxImage.digest)],
    [ociUri("inspection-sandbox", related.toolchain.inspectionSandboxImage), unprefixed(related.toolchain.inspectionSandboxImage.digest)],
    [`kokoro:lockfile/${related.manifest.manifestRef}`, unprefixed(related.manifest.lockfileDigest)],
    ...related.manifest.packages.map((item) => [packageUri(item), unprefixed(item.digest)]),
  ];
  if (new Set(expectedDependencyRows.map(([uri]) => uri)).size !== expectedDependencyRows.length) {
    fail("web_release_provenance_reference_invalid", "expected dependency URI collision");
  }
  const expectedDependencies = new Map(expectedDependencyRows);
  if (dependencies.size !== expectedDependencies.size) fail("web_release_provenance_reference_invalid", "dependency set");
  for (const [uri, expectedDigest] of expectedDependencies) {
    if (dependencies.get(uri) !== expectedDigest) fail("web_release_provenance_dependency_mismatch", uri);
  }
  const byproducts = unique(provenance.predicate.runDetails.byproducts.map(({ name }) => name), "web_release_provenance_reference_invalid");
  for (const required of ["pre-certification-evidence", "inspection-report", "sbom", "vulnerability-scan"]) if (!byproducts.has(required)) fail("web_release_provenance_reference_invalid", required);
}

function sameDigestRef(left, right) {
  return canonicalize(left) === canonicalize(right);
}

function validateCertification(certification, related) {
  const pairs = [
    [certification.siteReleaseCandidate, related.intent.siteReleaseCandidate],
    [certification.launchProductProfile, related.intent.launchProductProfile],
    [certification.productSurfaceCatalog, related.intent.productSurfaceCatalog],
    [certification.surfaceInventory, related.intent.surfaceInventory],
    [certification.webBuildIntent, { ref: related.intent.intentRef, digest: digest(related.intent) }],
    [certification.compiledWebManifest, { ref: related.manifest.manifestRef, digest: digest(related.manifest) }],
    [certification.webArtifactProvenance, { ref: related.provenance.provenanceRef, digest: digest(related.provenance) }],
  ];
  if (pairs.some(([left, right]) => !sameDigestRef(left, right))) fail("web_release_certification_reference_invalid");
  if (certification.siteRef !== related.intent.siteRef || certification.environment !== related.intent.environment ||
      certification.candidateAuthorizationEpoch !== related.intent.candidateAuthorizationEpoch) fail("web_release_certification_context_invalid");
  const producer = certification.producer;
  if (certification.certificationRevocationEpoch !== "0" || certification.generatedAt >= certification.validUntil ||
      producer.environment !== certification.environment || producer.keyStatus !== "active" ||
      producer.keyValidFrom > certification.generatedAt || producer.keyValidUntil < certification.validUntil ||
      certification.webArtifactDigest !== related.provenance.predicate.runDetails.webArtifactDigest) fail("web_release_certification_validity_invalid");
}

function authorityMaterial(snapshot) {
  return {
    activationAttempt: snapshot.activationAttempt,
    activationCommand: snapshot.activationCommand,
    casCommandRef: snapshot.casCommandRef,
    casFence: snapshot.casFence,
    phase: snapshot.phase,
    siteRef: snapshot.siteRef,
    environment: snapshot.environment,
    siteRelease: snapshot.siteRelease,
    candidate: snapshot.candidate,
    certification: snapshot.certification,
    trust: snapshot.trust,
    expectedActivePointerGeneration: snapshot.expectedActivePointerGeneration,
    activePointer: snapshot.activePointer,
    ownerReadReceipts: snapshot.ownerReadReceipts,
    readAt: snapshot.readAt,
  };
}

function eligibilityMaterial(evidence) {
  return {
    activationAttempt: evidence.activationAttempt,
    activationCommand: evidence.activationCommand,
    casCommandRef: evidence.casCommandRef,
    casFence: evidence.casFence,
    siteRelease: evidence.siteRelease,
    beginAuthoritySnapshot: evidence.beginAuthoritySnapshot,
    immediateBeforePointerCasAuthoritySnapshot: evidence.immediateBeforePointerCasAuthoritySnapshot,
    expectedActivePointerGeneration: evidence.expectedActivePointerGeneration,
    casPreconditionDigest: evidence.casPreconditionDigest,
    freshnessLease: evidence.freshnessLease,
    decision: evidence.decision,
    evaluatedAt: evidence.evaluatedAt,
  };
}

const ACTIVATION_RECEIPT_KINDS = ["candidate", "certification", "producer-registry", "trust-policy", "key-status", "active-pointer"];

function anchorFacts(anchor) {
  return {
    producerRegistry: anchor.producerRegistry, producerRegistryEpoch: anchor.producerRegistryEpoch,
    trustPolicy: anchor.trustPolicy, trustPolicyEpoch: anchor.trustPolicyEpoch, keyId: anchor.keyId,
    keyVersion: anchor.keyVersion, publicKeyFingerprint: anchor.publicKeyFingerprint, keyStatus: anchor.keyStatus,
    keyValidFrom: anchor.keyValidFrom, keyValidUntil: anchor.keyValidUntil,
    signatureAudience: anchor.signatureAudience, environment: anchor.environment,
  };
}

function resolveTrustedProducer(tuple, trustAnchors, signedAt, code) {
  const anchor = trustAnchors?.producers.get(`${tuple.keyId}@${tuple.keyVersion}`);
  if (anchor === undefined || tuple.producerIdentityRef !== anchor.producerIdentityRef ||
      canonicalize({
        producerRegistry: tuple.producerRegistry, producerRegistryEpoch: tuple.producerRegistryEpoch,
        trustPolicy: tuple.trustPolicy, trustPolicyEpoch: tuple.trustPolicyEpoch, keyId: tuple.keyId,
        keyVersion: tuple.keyVersion, publicKeyFingerprint: tuple.publicKeyFingerprint, keyStatus: tuple.keyStatus,
        keyValidFrom: tuple.keyValidFrom, keyValidUntil: tuple.keyValidUntil,
        signatureAudience: tuple.signatureAudience, environment: tuple.environment,
      }) !== canonicalize(anchorFacts(anchor)) || signedAt < anchor.keyValidFrom || signedAt >= anchor.keyValidUntil) {
    fail(code, `${tuple.keyId}@${tuple.keyVersion}`);
  }
  return anchor;
}

function activePointerCasMaterial(snapshot) {
  return {
    activationAttempt: snapshot.activationAttempt,
    activationCommand: snapshot.activationCommand,
    casCommandRef: snapshot.casCommandRef,
    casFence: snapshot.casFence,
    siteRef: snapshot.siteRef,
    environment: snapshot.environment,
    state: snapshot.activePointer.state,
    pointerRef: snapshot.activePointer.pointerRef,
    currentReleaseRef: snapshot.activePointer.currentReleaseRef,
    currentGeneration: snapshot.activePointer.currentGeneration,
    expectedGeneration: snapshot.activePointer.expectedGeneration,
  };
}

function receiptResult(snapshot, kind) {
  if (kind === "candidate") return snapshot.candidate;
  if (kind === "certification") return snapshot.certification;
  if (kind === "producer-registry") return { producerRegistry: snapshot.trust.producerRegistry, producerRegistryEpoch: snapshot.trust.producerRegistryEpoch };
  if (kind === "trust-policy") return { trustPolicy: snapshot.trust.trustPolicy, trustPolicyEpoch: snapshot.trust.trustPolicyEpoch };
  if (kind === "key-status") return {
    keyId: snapshot.trust.keyId, keyVersion: snapshot.trust.keyVersion,
    publicKeyFingerprint: snapshot.trust.publicKeyFingerprint, keyStatus: snapshot.trust.keyStatus,
    keyValidFrom: snapshot.trust.keyValidFrom, keyValidUntil: snapshot.trust.keyValidUntil,
  };
  return snapshot.activePointer;
}

function expectedReceiptIdentity(snapshot, kind) {
  if (kind === "candidate") return [snapshot.candidate.siteReleaseCandidate.ref, snapshot.candidate.authorizationEpoch];
  if (kind === "certification") return [snapshot.certification.releaseCertification.ref, snapshot.certification.revocationEpoch];
  if (kind === "producer-registry") return [snapshot.trust.producerRegistry.ref, snapshot.trust.producerRegistryEpoch];
  if (kind === "trust-policy") return [snapshot.trust.trustPolicy.ref, snapshot.trust.trustPolicyEpoch];
  if (kind === "key-status") return [snapshot.trust.keyId, snapshot.trust.keyVersion];
  return [snapshot.activePointer.pointerRef, snapshot.activePointer.currentGeneration];
}

function validateOwnerReadReceipts(snapshot, trustAnchors) {
  if (!Array.isArray(snapshot.ownerReadReceipts) || snapshot.ownerReadReceipts.length !== ACTIVATION_RECEIPT_KINDS.length) {
    fail("web_release_activation_live_read_receipt_invalid");
  }
  const byKind = new Map(snapshot.ownerReadReceipts.map((receipt) => [receipt.aggregateKind, receipt]));
  if (byKind.size !== ACTIVATION_RECEIPT_KINDS.length ||
      canonicalSet(byKind.keys()) !== canonicalSet(ACTIVATION_RECEIPT_KINDS)) fail("web_release_activation_live_read_receipt_invalid");
  unique(snapshot.ownerReadReceipts.map(({ readReceiptRef }) => readReceiptRef), "web_release_activation_live_read_receipt_invalid");
  unique(snapshot.ownerReadReceipts.map(({ headEventRef }) => headEventRef), "web_release_activation_live_read_receipt_invalid");
  for (const kind of ACTIVATION_RECEIPT_KINDS) {
    const receipt = byKind.get(kind);
    const [aggregateRef, revision] = expectedReceiptIdentity(snapshot, kind);
    const resultDigest = digest(receiptResult(snapshot, kind));
    const queryDigest = digest({
      activationAttempt: snapshot.activationAttempt, phase: snapshot.phase, aggregateKind: kind,
      aggregateRef, siteRef: snapshot.siteRef, environment: snapshot.environment,
      activationCommand: snapshot.activationCommand, casCommandRef: snapshot.casCommandRef, casFence: snapshot.casFence,
      expectedActivePointerGeneration: snapshot.expectedActivePointerGeneration,
    });
    if (receipt.aggregateRef !== aggregateRef || receipt.revision !== revision || receipt.observedAt !== snapshot.readAt ||
        receipt.resultDigest !== resultDigest || receipt.queryDigest !== queryDigest ||
        receipt.headDigest !== digest({ aggregateRef, revision, headEventRef: receipt.headEventRef, ownerEventDigest: receipt.ownerEventDigest, resultDigest }) ||
        receipt.signature.keyId !== receipt.provider.keyId ||
        receipt.signature.payloadType !== "application/vnd.kokoro.owner-live-read-receipt.v1+json") {
      fail("web_release_activation_live_read_receipt_invalid", kind);
    }
    const anchor = resolveTrustedProducer(receipt.provider, trustAnchors, receipt.observedAt, "web_release_activation_live_read_trust_invalid");
    if (anchor.environment !== snapshot.environment || anchor.producerRole !== RECEIPT_KIND_ROLES.get(kind) ||
        !anchor.allowedReceiptAggregateKinds.includes(kind) || !anchor.allowedPayloadTypes.includes(receipt.signature.payloadType)) {
      fail("web_release_activation_receipt_capability_invalid", kind);
    }
    const { signature, ...material } = receipt;
    const payload = canonicalBytes(material);
    const signed = verifySignature(null, dssePae(signature.payloadType, payload), anchor.key,
      Buffer.from(signature.signatureBase64, "base64"));
    if (!signed) fail("web_release_activation_live_read_signature_invalid", kind);
  }
  return byKind;
}

function validateActivationAuthoritySnapshot(snapshot, related) {
  if (snapshot.authorityMaterialDigest !== digest(authorityMaterial(snapshot))) fail("web_release_activation_authority_material_invalid");
  const expectedRelease = { ref: related.release.siteReleaseRef, digest: digest(related.release) };
  if (snapshot.siteRef !== related.release.siteRef || snapshot.environment !== related.release.environment) {
    fail("web_release_activation_context_invalid");
  }
  if (!sameDigestRef(snapshot.siteRelease, expectedRelease) || !sameDigestRef(snapshot.candidate.siteReleaseCandidate, related.release.siteReleaseCandidate) ||
      !sameDigestRef(snapshot.certification.releaseCertification, related.release.releaseCertification)) fail("web_release_activation_authority_reference_invalid");
  const firstActivation = snapshot.activePointer.state === "first-activation" && snapshot.activePointer.currentReleaseRef === null &&
    snapshot.activePointer.currentGeneration === "0" && snapshot.activePointer.expectedGeneration === "0";
  const existingActivation = snapshot.activePointer.state === "existing" && snapshot.activePointer.currentReleaseRef !== null &&
    /^[1-9][0-9]*$/u.test(snapshot.activePointer.currentGeneration) && /^[1-9][0-9]*$/u.test(snapshot.activePointer.expectedGeneration);
  if (snapshot.expectedActivePointerGeneration !== snapshot.activePointer.expectedGeneration ||
      snapshot.activePointer.currentGeneration !== snapshot.activePointer.expectedGeneration ||
      (!firstActivation && !existingActivation) ||
      snapshot.activePointer.casPreconditionDigest !== digest(activePointerCasMaterial(snapshot))) {
    fail("web_release_activation_pointer_cas_invalid");
  }
  validateOwnerReadReceipts(snapshot, related.trustAnchors);
}

function assertActivationFreshness(evidence, begin, beforeCas, certification) {
  const serverReceipt = beforeCas.ownerReadReceipts.find(({ aggregateKind }) => aggregateKind === "active-pointer");
  const issuedAt = Date.parse(evidence.freshnessLease.issuedAt);
  const notAfter = Date.parse(evidence.freshnessLease.notAfter);
  const evaluatedAt = Date.parse(evidence.evaluatedAt);
  const beginReadAt = Date.parse(begin.readAt);
  const beforeCasReadAt = Date.parse(beforeCas.readAt);
  if (![issuedAt, notAfter, evaluatedAt, beginReadAt, beforeCasReadAt].every(Number.isFinite)) {
    fail("web_release_activation_freshness_invalid");
  }
  const expectedNotAfter = new Date(issuedAt + ACTIVATION_FRESHNESS_LEASE_MILLISECONDS).toISOString();
  if (serverReceipt === undefined || evidence.freshnessLease.serverTimeReceiptRef !== serverReceipt.readReceiptRef ||
      evidence.freshnessLease.issuedAt !== serverReceipt.observedAt || evidence.freshnessLease.notAfter !== expectedNotAfter ||
      evidence.freshnessLease.maxSnapshotAgeMilliseconds !== String(ACTIVATION_MAX_SNAPSHOT_AGE_MILLISECONDS) ||
      evaluatedAt < issuedAt || evaluatedAt >= notAfter ||
      evaluatedAt - beginReadAt > ACTIVATION_MAX_SNAPSHOT_AGE_MILLISECONDS ||
      evaluatedAt - beforeCasReadAt > ACTIVATION_MAX_SNAPSHOT_AGE_MILLISECONDS ||
      evidence.evaluatedAt >= certification.validUntil || evidence.evaluatedAt >= beforeCas.trust.keyValidUntil) {
    fail("web_release_activation_freshness_invalid");
  }
}

function assertActivationEvidenceEligible(evidence, begin, beforeCas, release, certification, trustAnchors) {
  if (begin.phase !== "activation-begin" || beforeCas.phase !== "immediate-before-pointer-cas") fail("web_release_activation_phase_invalid");
  if (!sameDigestRef(begin.activationAttempt, evidence.activationAttempt) || !sameDigestRef(beforeCas.activationAttempt, evidence.activationAttempt) ||
      begin.snapshotRef === beforeCas.snapshotRef || digest(begin) === digest(beforeCas) || begin.readAt >= beforeCas.readAt ||
      beforeCas.readAt > evidence.evaluatedAt) fail("web_release_activation_snapshot_pair_invalid");
  const releaseRef = { ref: release.siteReleaseRef, digest: digest(release) };
  if (!sameDigestRef(evidence.siteRelease, releaseRef) || !sameDigestRef(begin.siteRelease, releaseRef) || !sameDigestRef(beforeCas.siteRelease, releaseRef) ||
      !sameDigestRef(evidence.beginAuthoritySnapshot, { ref: begin.snapshotRef, digest: digest(begin) }) ||
      !sameDigestRef(evidence.immediateBeforePointerCasAuthoritySnapshot, { ref: beforeCas.snapshotRef, digest: digest(beforeCas) })) fail("web_release_activation_authority_reference_invalid");
  if (!sameDigestRef(begin.activationCommand, evidence.activationCommand) || !sameDigestRef(beforeCas.activationCommand, evidence.activationCommand) ||
      begin.casCommandRef !== evidence.casCommandRef || beforeCas.casCommandRef !== evidence.casCommandRef ||
      canonicalize(begin.casFence) !== canonicalize(evidence.casFence) || canonicalize(beforeCas.casFence) !== canonicalize(evidence.casFence)) {
    fail("web_release_activation_pointer_cas_invalid");
  }
  if (begin.expectedActivePointerGeneration !== beforeCas.expectedActivePointerGeneration ||
      evidence.expectedActivePointerGeneration !== beforeCas.expectedActivePointerGeneration ||
      begin.activePointer.casPreconditionDigest !== beforeCas.activePointer.casPreconditionDigest ||
      evidence.casPreconditionDigest !== beforeCas.activePointer.casPreconditionDigest) fail("web_release_activation_pointer_cas_invalid");
  const beginReceipts = new Map(begin.ownerReadReceipts.map((receipt) => [receipt.aggregateKind, receipt]));
  const beforeReceipts = new Map(beforeCas.ownerReadReceipts.map((receipt) => [receipt.aggregateKind, receipt]));
  for (const kind of ACTIVATION_RECEIPT_KINDS) {
    const first = beginReceipts.get(kind); const second = beforeReceipts.get(kind);
    if (first === undefined || second === undefined || first.readReceiptRef === second.readReceiptRef ||
        first.observedAt >= second.observedAt) fail("web_release_activation_snapshot_pair_invalid", kind);
  }
  if (certification.generatedAt > release.publishedAt || release.publishedAt > begin.readAt ||
      beforeCas.readAt > evidence.evaluatedAt) fail("web_release_activation_time_order_invalid");
  for (const snapshot of [begin, beforeCas]) {
    if (snapshot.candidate.state !== "active" || snapshot.candidate.authorizationEpoch !== release.candidateAuthorizationEpoch ||
        !sameDigestRef(snapshot.candidate.siteReleaseCandidate, release.siteReleaseCandidate)) fail("web_release_activation_candidate_epoch_invalid");
    if (snapshot.certification.state !== "active" || snapshot.certification.revocationEpoch !== release.certificationRevocationEpoch ||
        !sameDigestRef(snapshot.certification.releaseCertification, release.releaseCertification)) fail("web_release_activation_certification_revoked");
    if (snapshot.certification.validUntil !== certification.validUntil || snapshot.readAt >= certification.validUntil) fail("web_release_activation_certification_expired");
    if (!sameDigestRef(snapshot.trust.producerRegistry, certification.producer.producerRegistry) ||
        snapshot.trust.producerRegistryEpoch !== certification.producer.producerRegistryEpoch) fail("web_release_activation_registry_epoch_invalid");
    if (!sameDigestRef(snapshot.trust.trustPolicy, certification.producer.trustPolicy) ||
        snapshot.trust.trustPolicyEpoch !== certification.producer.trustPolicyEpoch) fail("web_release_activation_policy_epoch_invalid");
    const stableTrust = ["producerIdentityRef", "keyId", "keyVersion", "publicKeyFingerprint", "signatureAudience", "environment"];
    if (stableTrust.some((field) => snapshot.trust[field] !== certification.producer[field]) ||
        snapshot.trust.keyStatus !== "active" || snapshot.readAt < snapshot.trust.keyValidFrom ||
        snapshot.readAt >= snapshot.trust.keyValidUntil) fail("web_release_activation_key_invalid");
    if (trustAnchors !== undefined) resolveTrustedProducer(snapshot.trust, trustAnchors, snapshot.readAt, "web_release_activation_key_invalid");
  }
  assertActivationFreshness(evidence, begin, beforeCas, certification);
}

function validateActivationEligibilityEvidence(evidence, related) {
  if (evidence.eligibilityMaterialDigest !== digest(eligibilityMaterial(evidence))) fail("web_release_activation_eligibility_material_invalid");
  assertActivationEvidenceEligible(evidence, related.activationBeginSnapshot, related.activationBeforeCasSnapshot,
    related.release, related.certification, related.trustAnchors);
}

function validateActivationEligibilityScenarios(scenarios, casesById, validators, related) {
  if (!Array.isArray(scenarios) || scenarios.length !== 1) fail("web_release_activation_scenario_invalid");
  const scenario = scenarios[0];
  exactKeys(scenario, ["beginSnapshotCaseId", "blockedImmediateBeforePointerCasReads", "evidenceCaseId", "id", "immediateBeforePointerCasSnapshotCaseId"], "web_release_activation_scenario_invalid");
  if (scenario.id !== "dual-authority-revalidation-before-pointer-cas" ||
      casesById.get(scenario.beginSnapshotCaseId)?.document !== related.activationBeginSnapshot ||
      casesById.get(scenario.immediateBeforePointerCasSnapshotCaseId)?.document !== related.activationBeforeCasSnapshot ||
      casesById.get(scenario.evidenceCaseId)?.document !== related.activationEvidence) fail("web_release_activation_scenario_invalid");
  validateBlockedActivationScenarioCoverage(scenario.blockedImmediateBeforePointerCasReads);
  for (const blocked of scenario.blockedImmediateBeforePointerCasReads) {
    const snapshot = structuredClone(blocked.snapshot);
    validateDocument("activation-authority-snapshot.v1", snapshot, validators);
    validateActivationAuthoritySnapshot(snapshot, related);
    const candidateEvidence = structuredClone(related.activationEvidence);
    candidateEvidence.immediateBeforePointerCasAuthoritySnapshot = { ref: snapshot.snapshotRef, digest: digest(snapshot) };
    if (candidateEvidence.evaluatedAt < snapshot.readAt) candidateEvidence.evaluatedAt = snapshot.readAt;
    const serverReceipt = snapshot.ownerReadReceipts.find(({ aggregateKind }) => aggregateKind === "active-pointer");
    candidateEvidence.freshnessLease.serverTimeReceiptRef = serverReceipt.readReceiptRef;
    candidateEvidence.freshnessLease.issuedAt = serverReceipt.observedAt;
    candidateEvidence.freshnessLease.notAfter = new Date(Date.parse(serverReceipt.observedAt) + ACTIVATION_FRESHNESS_LEASE_MILLISECONDS).toISOString();
    candidateEvidence.eligibilityMaterialDigest = digest(eligibilityMaterial(candidateEvidence));
    let code = null;
    try {
      assertActivationEvidenceEligible(candidateEvidence, related.activationBeginSnapshot, snapshot,
        related.release, related.certification, related.trustAnchors);
    } catch (error) {
      if (!(error instanceof WebReleaseContractError)) throw error;
      code = error.code;
    }
    if (code !== blocked.expectedCode) fail("web_release_activation_scenario_invalid", `${blocked.id}:${code ?? "accepted"}`);
  }
}

function validateRevocation(revocation, related) {
  const certification = related.revokedCertification;
  if (!sameDigestRef(revocation.releaseCertification, { ref: certification.certificationRef, digest: digest(certification) }) ||
      !sameDigestRef(revocation.siteReleaseCandidate, certification.siteReleaseCandidate) || revocation.candidateAuthorizationEpoch !== certification.candidateAuthorizationEpoch ||
      revocation.environment !== certification.environment || revocation.siteRef !== certification.siteRef) fail("web_release_certification_revocation_reference_invalid");
  if (BigInt(revocation.certificationRevocationEpoch) <= BigInt(certification.certificationRevocationEpoch) || revocation.revokedAt < certification.generatedAt) fail("web_release_certification_revocation_epoch_invalid");
  const producer = revocation.producer;
  if (producer.environment !== revocation.environment || producer.keyStatus !== "active" || revocation.revokedAt < producer.keyValidFrom || revocation.revokedAt >= producer.keyValidUntil) fail("web_release_certification_revocation_trust_invalid");
}

function validateSiteRelease(release, related) {
  const expected = [
    [release.siteReleaseCandidate, related.intent.siteReleaseCandidate], [release.launchProductProfile, related.intent.launchProductProfile],
    [release.productSurfaceCatalog, related.intent.productSurfaceCatalog], [release.surfaceInventory, related.intent.surfaceInventory],
    [release.webBuildIntent, { ref: related.intent.intentRef, digest: digest(related.intent) }],
    [release.compiledWebManifest, { ref: related.manifest.manifestRef, digest: digest(related.manifest) }],
    [release.webArtifactProvenance, related.certification.webArtifactProvenance],
    [release.releaseCertification, { ref: related.certification.certificationRef, digest: digest(related.certification) }],
  ];
  if (expected.some(([left, right]) => !sameDigestRef(left, right))) fail("web_release_site_release_reference_invalid");
  if (release.siteRef !== related.intent.siteRef || release.environment !== related.intent.environment ||
      release.candidateAuthorizationEpoch !== related.intent.candidateAuthorizationEpoch || release.certificationRevocationEpoch !== "0") fail("web_release_site_release_context_invalid");
  if (release.webArtifactDigest !== related.certification.webArtifactDigest || release.publishedAt < related.certification.generatedAt || release.publishedAt >= related.certification.validUntil) fail("web_release_site_release_certification_invalid");
  if (related.revocation.releaseCertification.ref === release.releaseCertification.ref && related.revocation.releaseCertification.digest === release.releaseCertification.digest) fail("web_release_site_release_revoked");
  if (canonicalize(release.businessBindings) !== canonicalize(related.candidate.businessBindings)) fail("web_release_site_release_reference_invalid", "business bindings");
  const bootstrap = release.bootstrapBindings;
  if (!sameDigestRef(bootstrap.compiledWebManifest, release.compiledWebManifest) || !sameDigestRef(bootstrap.productSurfaceCatalog, release.productSurfaceCatalog) ||
      !sameDigestRef(bootstrap.surfaceInventory, release.surfaceInventory) || !sameDigestRef(bootstrap.webCompositionRegistry, related.intent.webCompositionRegistry) ||
      !sameDigestRef(bootstrap.webBuildToolchain, related.intent.webBuildToolchain)) fail("web_release_site_release_bootstrap_invalid");
  if (canonicalRows(release.contractFloor, ({ contractRef }) => contractRef) !== canonicalRows(related.intent.contractFloor, ({ contractRef }) => contractRef)) fail("web_release_site_release_reference_invalid", "contract floor");
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

function validateTrustAnchors(anchors) {
  validateIJson(anchors);
  exactKeys(anchors, ["authority", "currentEpochs", "producers", "revision", "schema"], "web_release_trust_registry_invalid");
  if (anchors.schema !== "kokoro.trusted-web-release-producers.v1" || anchors.authority !== "root.contract" ||
      anchors.revision !== "1" || !Array.isArray(anchors.currentEpochs) || !Array.isArray(anchors.producers) ||
      anchors.currentEpochs.length === 0 || anchors.producers.length === 0) fail("web_release_trust_registry_invalid");
  const epochs = new Map();
  for (const current of anchors.currentEpochs) {
    exactKeys(current, ["environment", "producerRegistryEpoch", "trustPolicyEpoch"], "web_release_trust_registry_invalid");
    if (epochs.has(current.environment) || !/^(?:0|[1-9][0-9]*)$/u.test(current.producerRegistryEpoch) ||
        !/^(?:0|[1-9][0-9]*)$/u.test(current.trustPolicyEpoch)) fail("web_release_trust_registry_invalid");
    epochs.set(current.environment, current);
  }
  const producers = new Map();
  const expectedFields = ["allowedContractIds", "allowedPayloadTypes", "allowedReceiptAggregateKinds", "environment",
    "keyId", "keyStatus", "keyType", "keyValidFrom", "keyValidUntil", "keyVersion", "producerIdentityRef", "producerRegistry",
    "producerRegistryEpoch", "producerRole", "publicKeyFingerprint", "publicKeySpkiDerBase64", "signatureAudience", "trustPolicy", "trustPolicyEpoch"];
  for (const producer of anchors.producers) {
    exactKeys(producer, expectedFields, "web_release_trust_registry_invalid");
    const identity = `${producer.keyId}@${producer.keyVersion}`;
    const current = epochs.get(producer.environment);
    const capability = TRUST_ROLE_CAPABILITIES.get(producer.producerRole);
    if (producers.has(identity) || current === undefined || producer.keyStatus !== "active" ||
        producer.keyType !== "ed25519" || capability === undefined ||
        !Array.isArray(producer.allowedContractIds) || !Array.isArray(producer.allowedPayloadTypes) ||
        !Array.isArray(producer.allowedReceiptAggregateKinds) ||
        canonicalSet(producer.allowedContractIds) !== canonicalSet(capability?.contracts ?? []) ||
        canonicalSet(producer.allowedPayloadTypes) !== canonicalSet(capability?.payloads ?? []) ||
        canonicalSet(producer.allowedReceiptAggregateKinds) !== canonicalSet(capability?.receipts ?? []) ||
        producer.producerRegistryEpoch !== current.producerRegistryEpoch || producer.trustPolicyEpoch !== current.trustPolicyEpoch ||
        producer.keyValidFrom >= producer.keyValidUntil || typeof producer.producerIdentityRef !== "string" ||
        producer.producerIdentityRef.length < 3 || producer.producerIdentityRef.length > 512) {
      fail("web_release_trust_registry_invalid", identity);
    }
    let der;
    let key;
    try {
      der = Buffer.from(producer.publicKeySpkiDerBase64, "base64");
      key = createPublicKey({ key: der, format: "der", type: "spki" });
    } catch { fail("web_release_trust_registry_invalid", identity); }
    const fingerprint = `sha256:${createHash("sha256").update(der).digest("hex")}`;
    if (producer.publicKeyFingerprint !== fingerprint || key.asymmetricKeyType !== "ed25519") fail("web_release_trust_registry_invalid", identity);
    producers.set(identity, Object.freeze({ ...producer, key }));
  }
  for (const [kind, role] of RECEIPT_KIND_ROLES) {
    const owners = [...producers.values()].filter((producer) => producer.allowedReceiptAggregateKinds.includes(kind));
    if (owners.length !== 1 || owners[0].producerRole !== role) fail("web_release_trust_registry_invalid", kind);
  }
  return Object.freeze({ epochs, producers });
}

function dsseSigner(document, contractId) {
  if (contractId === "web-build-intent.v1") {
    return { signedAt: document.issuedAt, identity: document.issuer.issuerRef, facts: {
      producerRegistry: document.issuer.producerRegistry, producerRegistryEpoch: document.issuer.producerRegistryEpoch,
      trustPolicy: document.issuer.trustPolicy, trustPolicyEpoch: document.issuer.trustPolicyEpoch,
      keyId: document.issuer.signingKeyId, keyVersion: document.issuer.keyVersion,
      publicKeyFingerprint: document.issuer.publicKeyFingerprint, keyStatus: document.issuer.keyStatus,
      keyValidFrom: document.issuer.keyValidFrom, keyValidUntil: document.issuer.keyValidUntil,
      signatureAudience: document.issuer.signatureAudience, environment: document.issuer.environment,
    } };
  }
  if (contractId === "web-artifact-provenance-profile.v1") {
    const builder = document.predicate.runDetails.builder;
    return { signedAt: document.predicate.runDetails.metadata.finishedOn, identity: builder.id, facts: {
      producerRegistry: builder.producerRegistry, producerRegistryEpoch: builder.producerRegistryEpoch,
      trustPolicy: builder.trustPolicy, trustPolicyEpoch: builder.trustPolicyEpoch,
      keyId: builder.kokoro_signingKeyId, keyVersion: builder.keyVersion,
      publicKeyFingerprint: builder.publicKeyFingerprint, keyStatus: builder.keyStatus,
      keyValidFrom: builder.keyValidFrom, keyValidUntil: builder.keyValidUntil,
      signatureAudience: builder.signatureAudience, environment: builder.environment,
    } };
  }
  const producer = document.producer;
  return { signedAt: contractId === "release-certification-revocation.v1" ? document.revokedAt : document.generatedAt,
    identity: producer.producerIdentityRef, facts: {
      producerRegistry: producer.producerRegistry, producerRegistryEpoch: producer.producerRegistryEpoch,
      trustPolicy: producer.trustPolicy, trustPolicyEpoch: producer.trustPolicyEpoch,
      keyId: producer.keyId, keyVersion: producer.keyVersion, publicKeyFingerprint: producer.publicKeyFingerprint,
      keyStatus: producer.keyStatus, keyValidFrom: producer.keyValidFrom, keyValidUntil: producer.keyValidUntil,
      signatureAudience: producer.signatureAudience, environment: producer.environment,
    } };
}

function validateDsseVectors(corpus, casesById, envelopeValidators, trustAnchors) {
  for (const vector of corpus.dsseVectors) {
    exactKeys(vector, ["caseId", "expectedPaeSha256", "id", "keyId", "payloadType", "signatureBase64"], "web_release_dsse_vector_invalid");
    const contractCase = casesById.get(vector.caseId);
    if (contractCase === undefined) fail("web_release_dsse_coverage_invalid", vector.caseId);
    const document = contractCase.document;
    const payload = canonicalBytes(document);
    const envelope = { payloadType: vector.payloadType, payload: payload.toString("base64"), signatures: [{ keyid: vector.keyId, sig: vector.signatureBase64 }] };
    const envelopeValidator = envelopeValidators.get(contractCase.contractId);
    if (envelopeValidator === undefined || !envelopeValidator(envelope)) fail("web_release_dsse_envelope_invalid", `${vector.id}: ${JSON.stringify(envelopeValidator?.errors ?? [])}`);
    const expectedKeyId = contractCase.contractId === "web-build-intent.v1"
      ? document.issuer.signingKeyId
      : ["release-certification-instance.v1", "release-certification-revocation.v1"].includes(contractCase.contractId)
        ? document.producer.keyId
        : document.predicate.runDetails.builder.kokoro_signingKeyId;
    if (vector.keyId !== expectedKeyId) fail("web_release_dsse_keyid_mismatch", vector.id);
    const signer = dsseSigner(document, contractCase.contractId);
    const anchor = trustAnchors.producers.get(`${vector.keyId}@${signer.facts.keyVersion}`);
    if (anchor === undefined || signer.identity !== anchor.producerIdentityRef) fail("web_release_dsse_trust_anchor_missing", vector.id);
    if (anchor.producerRole !== DSSE_CONTRACT_ROLES.get(contractCase.contractId) ||
        !anchor.allowedContractIds.includes(contractCase.contractId) || !anchor.allowedPayloadTypes.includes(vector.payloadType) ||
        anchor.allowedReceiptAggregateKinds.length !== 0) fail("web_release_dsse_capability_invalid", vector.id);
    const anchoredFacts = {
      producerRegistry: anchor.producerRegistry, producerRegistryEpoch: anchor.producerRegistryEpoch,
      trustPolicy: anchor.trustPolicy, trustPolicyEpoch: anchor.trustPolicyEpoch, keyId: anchor.keyId,
      keyVersion: anchor.keyVersion, publicKeyFingerprint: anchor.publicKeyFingerprint, keyStatus: anchor.keyStatus,
      keyValidFrom: anchor.keyValidFrom, keyValidUntil: anchor.keyValidUntil,
      signatureAudience: anchor.signatureAudience, environment: anchor.environment,
    };
    if (canonicalize(signer.facts) !== canonicalize(anchoredFacts) || signer.signedAt < anchor.keyValidFrom ||
        signer.signedAt >= anchor.keyValidUntil) fail("web_release_dsse_trust_anchor_invalid", vector.id);
    const pae = dssePae(vector.payloadType, payload);
    const actual = createHash("sha256").update(pae).digest("hex");
    if (actual !== vector.expectedPaeSha256) fail("web_release_dsse_vector_invalid", vector.id);
    if (!verifySignature(null, pae, anchor.key, Buffer.from(vector.signatureBase64, "base64"))) fail("web_release_dsse_vector_invalid", vector.id);
  }
}

function schemaAjv() {
  return new Ajv2020({ allErrors: true, strict: true, validateFormats: false });
}

function validateRegistry(registry, { requireCurrentSet = true } = {}) {
  exactKeys(registry, ["breakingPolicy", "canonicalProfile", "contracts", "registryId", "schemaAuthority", "schemaVersion"], "web_release_registry_shape_invalid");
  if (registry.schemaVersion !== 1 || registry.registryId !== "kokoro.web-release-composition-contracts.v1" || registry.schemaAuthority !== "root.contract") fail("web_release_registry_shape_invalid");
  exactKeys(registry.canonicalProfile, ["canonicalization", "digestAlgorithm", "digestEncoding", "integerEncoding", "jsonProfile", "selfDigest", "timestampEncoding", "unknownFields"], "web_release_registry_shape_invalid");
  if (registry.canonicalProfile.jsonProfile !== "I-JSON-NFC-KOKORO-V1" || registry.canonicalProfile.canonicalization !== "RFC8785-JCS" || registry.canonicalProfile.digestAlgorithm !== "sha256" || registry.canonicalProfile.digestEncoding !== "sha256-lowercase-hex" || registry.canonicalProfile.integerEncoding !== "canonical-decimal-string" || registry.canonicalProfile.timestampEncoding !== "utc-rfc3339-millisecond" || registry.canonicalProfile.unknownFields !== "reject" || registry.canonicalProfile.selfDigest !== "forbidden") fail("web_release_registry_shape_invalid");
  exactKeys(registry.breakingPolicy, ["policy", "rule"], "web_release_registry_shape_invalid");
  if (registry.breakingPolicy.policy !== "immutable-major-schema") fail("web_release_registry_shape_invalid");
  if (!Array.isArray(registry.contracts) || registry.contracts.length === 0 || registry.contracts.length > CONTRACT_IDS.length) fail("web_release_registry_contract_set_invalid");
  const ids = registry.contracts.map(({ id }) => id);
  unique(ids, "web_release_registry_contract_set_invalid");
  if (requireCurrentSet && canonicalSet(ids) !== canonicalSet(CONTRACT_IDS)) fail("web_release_registry_contract_set_invalid");
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
  else if (contractId === "launch-product-profile.v1") validateProfile(document, related.catalog);
  else if (contractId === "site-release-candidate.v1") validateCandidate(document, related);
  else if (contractId === "surface-inventory.v1") validateInventory(document, related);
  else if (contractId === "web-build-material-bundle.v1") validateMaterial(document);
  else if (contractId === "web-composition-registry.v1") validateCompositionRegistry(document, related.catalog);
  else if (contractId === "web-build-intent.v1") validateIntent(document, related);
  else if (contractId === "compiled-web-manifest.v1") validateManifest(document, related);
  else if (contractId === "web-artifact-provenance-profile.v1") validateProvenance(document, related);
  else if (contractId === "release-certification-instance.v1") validateCertification(document, related);
  else if (contractId === "release-certification-revocation.v1") validateRevocation(document, related);
  else if (contractId === "site-release.v1") validateSiteRelease(document, related);
  else if (contractId === "activation-authority-snapshot.v1") validateActivationAuthoritySnapshot(document, related);
  else if (contractId === "activation-eligibility-evidence.v1") validateActivationEligibilityEvidence(document, related);
}

function loadBundle(root, registryPath = resolve(root, DEFAULT_REGISTRY), registryOptions = {}) {
  const registry = readJson(registryPath, "web_release_registry_read_failed");
  validateRegistry(registry, registryOptions);
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

function loadGitBundle(root, revision, registryOptions = {}) {
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
  validateRegistry(registry, registryOptions);
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
  const trustAnchors = validateTrustAnchors(readJson(resolve(root, DEFAULT_TRUST_ANCHORS), "web_release_trust_registry_read_failed"));
  const corpus = readJson(corpusPath, "web_release_corpus_read_failed");
  validateIJson(corpus);
  exactKeys(corpus, ["activationEligibilityScenarios", "canonicalProfile", "canonicalVectors", "dsseVectors", "negativeCases", "positiveCases", "schema"], "web_release_corpus_shape_invalid");
  if (corpus.schema !== "kokoro.web-release-composition.corpus.v1" || corpus.positiveCases.length !== 17 || corpus.negativeCases.length !== FROZEN_NEGATIVE_CASE_DIGESTS.size || corpus.canonicalVectors.length !== 17 || corpus.dsseVectors.length !== 5) fail("web_release_corpus_shape_invalid");
  validateNegativeCaseCoverage(corpus.negativeCases);
  const casesById = new Map(corpus.positiveCases.map((item) => [item.id, item]));
  if (casesById.size !== corpus.positiveCases.length || new Set(corpus.positiveCases.map(({ contractId }) => contractId)).size !== 15) fail("web_release_corpus_shape_invalid");
  unique(corpus.canonicalVectors.map(({ id }) => id), "web_release_canonical_coverage_invalid");
  const canonicalCaseIds = unique(corpus.canonicalVectors.map(({ caseId }) => caseId), "web_release_canonical_coverage_invalid");
  if (canonicalSet(canonicalCaseIds) !== canonicalSet(casesById.keys())) fail("web_release_canonical_coverage_invalid");
  unique(corpus.dsseVectors.map(({ id }) => id), "web_release_dsse_coverage_invalid");
  const dsseCaseIds = unique(corpus.dsseVectors.map(({ caseId }) => caseId), "web_release_dsse_coverage_invalid");
  const dsseContractIds = new Set(bundle.registry.contracts.filter(({ signatureProfile }) => signatureProfile.startsWith("dsse-")).map(({ id }) => id));
  const requiredDsseCaseIds = corpus.positiveCases.filter(({ contractId }) => dsseContractIds.has(contractId)).map(({ id }) => id);
  if (canonicalSet(dsseCaseIds) !== canonicalSet(requiredDsseCaseIds)) fail("web_release_dsse_coverage_invalid");
  const byContract = new Map(corpus.positiveCases.map((item) => [item.contractId, item.document]));
  const related = {
    catalog: byContract.get("product-surface-catalog.v1"), profile: byContract.get("launch-product-profile.v1"), candidate: byContract.get("site-release-candidate.v1"), inventory: byContract.get("surface-inventory.v1"),
    material: byContract.get("web-build-material-bundle.v1"), toolchain: byContract.get("web-build-toolchain.v1"),
    registry: byContract.get("web-composition-registry.v1"), intent: byContract.get("web-build-intent.v1"), manifest: byContract.get("compiled-web-manifest.v1"),
    provenance: byContract.get("web-artifact-provenance-profile.v1"),
    certification: casesById.get("certification-site-alpha")?.document, revokedCertification: casesById.get("certification-obsolete")?.document,
    revocation: byContract.get("release-certification-revocation.v1"), release: byContract.get("site-release.v1"),
    activationBeginSnapshot: casesById.get("activation-authority-begin")?.document,
    activationBeforeCasSnapshot: casesById.get("activation-authority-before-cas")?.document,
    activationEvidence: casesById.get("activation-eligibility-alpha")?.document,
    trustAnchors,
  };
  if (Object.values(related).some((document) => document === undefined)) fail("web_release_corpus_shape_invalid", "related chain");
  for (const item of corpus.positiveCases) {
    validateDocument(item.contractId, item.document, bundle.validators);
    semanticValidate(item.contractId, item.document, related);
  }
  validateActivationEligibilityScenarios(corpus.activationEligibilityScenarios, casesById, bundle.validators, related);
  for (const vector of corpus.canonicalVectors) {
    const item = casesById.get(vector.caseId);
    if (item === undefined || digest(item.document) !== vector.expectedDigest) fail("web_release_canonical_vector_invalid", vector.id);
  }
  validateDsseVectors(corpus, casesById, bundle.envelopeValidators, trustAnchors);
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
    assertFrozenV1Compatible(loadBundle(baselineRoot, undefined, { requireCurrentSet: false }), loadBundle(candidateRoot));
  }
  if (options.breakingAgainst !== null) {
    const root = resolve(options.root);
    assertFrozenV1Compatible(loadGitBundle(root, options.breakingAgainst, { requireCurrentSet: false }), loadGitBundle(root, "HEAD"));
  }
  process.stdout.write(`web_release_contracts_ok:${result.contracts} contracts, ${result.positiveCases}+${result.negativeCases} corpus, ${result.canonicalVectors} canonical, ${result.dsseVectors} dsse\n`);
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  main().catch((error) => {
    process.stderr.write(`${error instanceof WebReleaseContractError ? error.message : error.stack ?? error.message}\n`);
    process.exitCode = 1;
  });
}
