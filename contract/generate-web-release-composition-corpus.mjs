#!/usr/bin/env node

import { createHash, createPrivateKey, createPublicKey, sign } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

import { canonicalizeJsonText } from "../scripts/contract/check-web-release-composition.mjs";

const DEFAULT_ROOT = resolve(import.meta.dirname, "..");
const CORPUS_PATH = "contract/corpus/web-release-composition-v1.json";
const TRUST_ANCHORS_PATH = "contract/registry/trusted-web-release-producers.yaml";
const PKCS8_ED25519_SEED_PREFIX = Buffer.from("302e020100300506032b657004220420", "hex");
const TEST_KEY_DOMAIN = "kokoro.web-release-composition.public-conformance-key.v1";

function canonicalBytes(value) {
  return Buffer.from(canonicalizeJsonText(JSON.stringify(value)), "utf8");
}

function canonicalDigest(value) {
  return `sha256:${createHash("sha256").update(canonicalBytes(value)).digest("hex")}`;
}

function revisionBinding(document, refField) {
  return { ref: document[refField], revision: document.revision, digest: canonicalDigest(document) };
}

function candidateAuthorityBinding(candidate) {
  return {
    ref: candidate.candidateRef,
    version: candidate.revision,
    authorizationEpoch: candidate.candidateAuthorizationEpoch,
    digest: canonicalDigest(candidate),
  };
}

function ensureRevisionBinding(reference, revision = "1") {
  return { ref: reference.ref, revision, digest: reference.digest };
}

function dssePae(payloadType, payload) {
  const type = Buffer.from(payloadType, "utf8");
  return Buffer.concat([Buffer.from(`DSSEv1 ${type.length} `), type, Buffer.from(` ${payload.length} `), payload]);
}

function deterministicPrivateKey(anchor) {
  // These fixed public-conformance seeds make checked-in signatures reproducible.
  // They are scoped to fixture key identities and are never loaded by runtime code.
  const seed = createHash("sha256")
    .update(`${TEST_KEY_DOMAIN}\0${anchor.keyId}\0${anchor.keyVersion}`, "utf8")
    .digest();
  return createPrivateKey({
    key: Buffer.concat([PKCS8_ED25519_SEED_PREFIX, seed]),
    format: "der",
    type: "pkcs8",
  });
}

function documentSigner(contractCase) {
  if (contractCase.contractId === "web-build-intent.v1") return contractCase.document.issuer;
  if (contractCase.contractId === "web-artifact-provenance-profile.v1") {
    return contractCase.document.predicate.runDetails.builder;
  }
  return contractCase.document.producer;
}

function refreshSigningIdentities(corpus, anchors) {
  const privateKeys = new Map();
  for (const anchor of anchors.producers) {
    const privateKey = deterministicPrivateKey(anchor);
    const publicDer = createPublicKey(privateKey).export({ format: "der", type: "spki" });
    anchor.publicKeySpkiDerBase64 = publicDer.toString("base64");
    anchor.publicKeyFingerprint = `sha256:${createHash("sha256").update(publicDer).digest("hex")}`;
    privateKeys.set(anchor.keyId, privateKey);
  }
  for (const vector of corpus.dsseVectors) {
    const contractCase = corpus.positiveCases.find(({ id }) => id === vector.caseId);
    const anchor = anchors.producers.find(({ keyId }) => keyId === vector.keyId);
    if (contractCase === undefined || anchor === undefined) throw new Error(`web_release_fixture_signer_missing:${vector.id}`);
    documentSigner(contractCase).publicKeyFingerprint = anchor.publicKeyFingerprint;
  }
  return privateKeys;
}

function resignVector(corpus, caseId, privateKey) {
  const vector = corpus.dsseVectors.find((candidate) => candidate.caseId === caseId);
  const document = corpus.positiveCases.find((candidate) => candidate.id === caseId)?.document;
  if (vector === undefined || document === undefined || privateKey === undefined) {
    throw new Error(`web_release_fixture_vector_missing:${caseId}`);
  }
  const payload = canonicalBytes(document);
  const pae = dssePae(vector.payloadType, payload);
  vector.expectedPaeSha256 = createHash("sha256").update(pae).digest("hex");
  vector.signatureBase64 = sign(null, pae, privateKey).toString("base64");
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

function receiptMaterial(receipt) {
  const { signature, ...material } = receipt;
  return material;
}

function receiptResult(snapshot, kind) {
  if (kind === "candidate") return snapshot.candidate;
  if (kind === "certification") return snapshot.certification;
  if (kind === "producer-registry") {
    return { producerRegistry: snapshot.trust.producerRegistry, producerRegistryEpoch: snapshot.trust.producerRegistryEpoch };
  }
  if (kind === "trust-policy") {
    return { trustPolicy: snapshot.trust.trustPolicy, trustPolicyEpoch: snapshot.trust.trustPolicyEpoch };
  }
  if (kind === "key-status") {
    return {
      keyId: snapshot.trust.keyId,
      keyVersion: snapshot.trust.keyVersion,
      publicKeyFingerprint: snapshot.trust.publicKeyFingerprint,
      keyStatus: snapshot.trust.keyStatus,
      keyValidFrom: snapshot.trust.keyValidFrom,
      keyValidUntil: snapshot.trust.keyValidUntil,
    };
  }
  return snapshot.activePointer;
}

function refreshReceipts(snapshot, suffix, anchors, privateKeys) {
  snapshot.activePointer.casPreconditionDigest = canonicalDigest(activePointerCasMaterial(snapshot));
  for (const receipt of snapshot.ownerReadReceipts) {
    const anchor = anchors.producers.find(({ keyId }) => keyId === receipt.provider.keyId);
    if (anchor === undefined) throw new Error(`web_release_fixture_receipt_signer_missing:${receipt.aggregateKind}`);
    const {
      publicKeySpkiDerBase64,
      keyType,
      producerRole,
      allowedContractIds,
      allowedPayloadTypes,
      allowedReceiptAggregateKinds,
      ...provider
    } = anchor;
    receipt.provider = structuredClone(provider);
    receipt.observedAt = snapshot.readAt;
    receipt.readReceiptRef = `read-receipt.${receipt.aggregateKind.replaceAll("-", ".")}.${suffix}.1`;
    receipt.revision = receipt.aggregateKind === "candidate"
      ? snapshot.candidate.siteReleaseCandidate.authorizationEpoch
      : receipt.aggregateKind === "certification"
        ? snapshot.certification.revocationEpoch
        : receipt.aggregateKind === "producer-registry"
          ? snapshot.trust.producerRegistryEpoch
          : receipt.aggregateKind === "trust-policy"
            ? snapshot.trust.trustPolicyEpoch
            : receipt.aggregateKind === "key-status"
              ? snapshot.trust.keyVersion
              : snapshot.activePointer.currentGeneration;
    receipt.resultDigest = canonicalDigest(receiptResult(snapshot, receipt.aggregateKind));
    receipt.ownerEventDigest = canonicalDigest({
      aggregateKind: receipt.aggregateKind,
      aggregateRef: receipt.aggregateRef,
      revision: receipt.revision,
      headEventRef: receipt.headEventRef,
      resultDigest: receipt.resultDigest,
    });
    receipt.headDigest = canonicalDigest({
      aggregateRef: receipt.aggregateRef,
      revision: receipt.revision,
      headEventRef: receipt.headEventRef,
      ownerEventDigest: receipt.ownerEventDigest,
      resultDigest: receipt.resultDigest,
    });
    receipt.queryDigest = canonicalDigest({
      activationAttempt: snapshot.activationAttempt,
      phase: snapshot.phase,
      aggregateKind: receipt.aggregateKind,
      aggregateRef: receipt.aggregateRef,
      siteRef: snapshot.siteRef,
      environment: snapshot.environment,
      activationCommand: snapshot.activationCommand,
      casCommandRef: snapshot.casCommandRef,
      casFence: snapshot.casFence,
      expectedActivePointerGeneration: snapshot.expectedActivePointerGeneration,
    });
    const payload = canonicalBytes(receiptMaterial(receipt));
    receipt.signature = {
      payloadType: "application/vnd.kokoro.owner-live-read-receipt.v1+json",
      keyId: provider.keyId,
      signatureBase64: sign(
        null,
        dssePae("application/vnd.kokoro.owner-live-read-receipt.v1+json", payload),
        privateKeys.get(provider.keyId),
      ).toString("base64"),
    };
  }
  snapshot.authorityMaterialDigest = canonicalDigest(authorityMaterial(snapshot));
}

function refreshBlockedSnapshots(corpus, beforeCasSnapshot, anchors, privateKeys) {
  const blockedScenarios = corpus.activationEligibilityScenarios[0].blockedImmediateBeforePointerCasReads;
  for (const [index, blocked] of blockedScenarios.entries()) {
    const snapshot = structuredClone(beforeCasSnapshot);
    snapshot.snapshotRef = blocked.snapshot.snapshotRef;
    if (blocked.id.startsWith("candidate-revoked")) snapshot.candidate.state = "revoked";
    else if (blocked.id.startsWith("certification-revoked")) {
      snapshot.certification.state = "revoked";
      snapshot.certification.revocationEpoch = "1";
    } else if (blocked.id.startsWith("key-revoked")) snapshot.trust.keyStatus = "revoked";
    else if (blocked.id.startsWith("key-suspended")) snapshot.trust.keyStatus = "suspended";
    else if (blocked.id.startsWith("producer-registry")) snapshot.trust.producerRegistryEpoch = "5";
    else if (blocked.id.startsWith("trust-policy")) snapshot.trust.trustPolicyEpoch = "10";
    else snapshot.readAt = snapshot.certification.validUntil;
    refreshReceipts(snapshot, `blocked.${index + 1}`, anchors, privateKeys);
    blocked.snapshot = snapshot;
  }
}

function refreshNegativeCases(corpus) {
  const byId = new Map(corpus.negativeCases.map((entry) => [entry.id, entry]));
  const certificationEpoch = byId.get("certification-candidate-epoch-mismatch");
  if (certificationEpoch !== undefined) {
    certificationEpoch.mutation.path = "/siteReleaseCandidate/authorizationEpoch";
  }
  const additions = [
    {
      id: "certification-candidate-digest-missing",
      baseCaseId: "certification-site-alpha",
      mutation: { op: "remove", path: "/siteReleaseCandidate/digest" },
      expectedCode: "web_release_positive_schema_invalid",
    },
    {
      id: "intent-candidate-version-missing",
      baseCaseId: "intent-site-alpha",
      mutation: { op: "remove", path: "/siteReleaseCandidate/version" },
      expectedCode: "web_release_positive_schema_invalid",
    },
    {
      id: "provenance-intent-revision-missing",
      baseCaseId: "provenance-site-alpha",
      mutation: { op: "remove", path: "/predicate/buildDefinition/externalParameters/webBuildIntent/revision" },
      expectedCode: "web_release_positive_schema_invalid",
    },
    {
      id: "site-release-candidate-epoch-missing",
      baseCaseId: "site-release-alpha",
      mutation: { op: "remove", path: "/siteReleaseCandidate/authorizationEpoch" },
      expectedCode: "web_release_positive_schema_invalid",
    },
    {
      id: "site-release-certification-revision-missing",
      baseCaseId: "site-release-alpha",
      mutation: { op: "remove", path: "/releaseCertification/revision" },
      expectedCode: "web_release_positive_schema_invalid",
    },
  ];
  for (const addition of additions) if (!byId.has(addition.id)) corpus.negativeCases.push(addition);
  corpus.negativeCases.sort((left, right) => left.id < right.id ? -1 : left.id > right.id ? 1 : 0);
}

function refreshCoherentChain(corpus, anchors) {
  const privateKeys = refreshSigningIdentities(corpus, anchors);
  const documents = new Map(corpus.positiveCases.map(({ contractId, document }) => [contractId, document]));
  const cases = new Map(corpus.positiveCases.map(({ id, document }) => [id, document]));
  const catalog = documents.get("product-surface-catalog.v1");
  const profile = documents.get("launch-product-profile.v1");
  const candidate = documents.get("site-release-candidate.v1");
  const inventory = documents.get("surface-inventory.v1");
  const material = documents.get("web-build-material-bundle.v1");
  const toolchain = documents.get("web-build-toolchain.v1");
  const registry = documents.get("web-composition-registry.v1");
  const intent = documents.get("web-build-intent.v1");
  const manifest = documents.get("compiled-web-manifest.v1");
  const provenance = documents.get("web-artifact-provenance-profile.v1");
  const certification = cases.get("certification-site-alpha");
  const revokedCertification = cases.get("certification-obsolete");
  const revocation = cases.get("revocation-obsolete-certification");
  const siteRelease = documents.get("site-release.v1");
  const beginSnapshot = cases.get("activation-authority-begin");
  const beforeCasSnapshot = cases.get("activation-authority-before-cas");
  const activationEvidence = cases.get("activation-eligibility-alpha");
  if ([catalog, profile, candidate, inventory, material, toolchain, registry, intent, manifest, provenance,
    certification, revokedCertification, revocation, siteRelease, beginSnapshot, beforeCasSnapshot,
    activationEvidence].some((value) => value === undefined)) {
    throw new Error("web_release_fixture_chain_incomplete");
  }

  profile.productSurfaceCatalog = revisionBinding(catalog, "catalogRevisionRef");
  profile.journeyClosure.digest = canonicalDigest(profile.journeyClosure.journeys);
  candidate.launchProductProfile = revisionBinding(profile, "profileRevisionRef");
  candidate.productSurfaceCatalog = revisionBinding(catalog, "catalogRevisionRef");
  candidate.businessBindings.webBuildMaterialBundle = revisionBinding(material, "bundleRef");
  inventory.siteReleaseCandidate = candidateAuthorityBinding(candidate);
  inventory.launchProductProfile = revisionBinding(profile, "profileRevisionRef");
  inventory.productSurfaceCatalog = revisionBinding(catalog, "catalogRevisionRef");

  intent.revision ??= "1";
  intent.siteReleaseCandidate = candidateAuthorityBinding(candidate);
  intent.launchProductProfile = revisionBinding(profile, "profileRevisionRef");
  intent.productSurfaceCatalog = revisionBinding(catalog, "catalogRevisionRef");
  intent.surfaceInventory = revisionBinding(inventory, "inventoryRevisionRef");
  intent.webBuildMaterialBundle = revisionBinding(material, "bundleRef");
  intent.webBuildToolchain = revisionBinding(toolchain, "toolchainRevisionRef");
  intent.webCompositionRegistry = revisionBinding(registry, "registryRevisionRef");
  intent.businessBindings.webBuildMaterialBundle = structuredClone(intent.webBuildMaterialBundle);
  delete intent.candidateAuthorizationEpoch;

  manifest.revision ??= "1";
  manifest.webBuildIntent = revisionBinding(intent, "intentRef");
  delete manifest.intentRef;
  delete manifest.buildIntentDigest;
  manifest.siteReleaseCandidate = structuredClone(intent.siteReleaseCandidate);
  manifest.catalog = structuredClone(intent.productSurfaceCatalog);
  manifest.surfaceInventory = structuredClone(intent.surfaceInventory);
  manifest.registry = structuredClone(intent.webCompositionRegistry);
  manifest.toolchain = structuredClone(intent.webBuildToolchain);

  provenance.revision ??= "1";
  const parameters = provenance.predicate.buildDefinition.externalParameters;
  parameters.webBuildIntent = revisionBinding(intent, "intentRef");
  parameters.compiledWebManifest = revisionBinding(manifest, "manifestRef");
  parameters.siteReleaseCandidate = structuredClone(intent.siteReleaseCandidate);
  parameters.toolchain = revisionBinding(toolchain, "toolchainRevisionRef");
  for (const property of ["intentRef", "buildIntentDigest", "compiledWebManifestRef", "compiledWebManifestDigest",
    "releaseCandidateRef", "candidateAuthorizationEpoch"]) delete parameters[property];
  const materialDependency = provenance.predicate.buildDefinition.resolvedDependencies.find(
    ({ uri }) => uri === `kokoro:material-bundle/${intent.webBuildMaterialBundle.ref}`,
  );
  if (materialDependency !== undefined) {
    materialDependency.digest.sha256 = canonicalDigest(material).slice("sha256:".length);
  }

  certification.siteReleaseCandidate = structuredClone(intent.siteReleaseCandidate);
  certification.launchProductProfile = structuredClone(intent.launchProductProfile);
  certification.productSurfaceCatalog = structuredClone(intent.productSurfaceCatalog);
  certification.surfaceInventory = structuredClone(intent.surfaceInventory);
  certification.webBuildIntent = revisionBinding(intent, "intentRef");
  certification.compiledWebManifest = revisionBinding(manifest, "manifestRef");
  certification.webArtifactProvenance = revisionBinding(provenance, "provenanceRef");
  certification.evidenceBundle = ensureRevisionBinding(certification.evidenceBundle);
  delete certification.candidateAuthorizationEpoch;
  for (const field of ["siteReleaseCandidate", "launchProductProfile", "productSurfaceCatalog", "surfaceInventory",
    "webBuildIntent", "compiledWebManifest", "webArtifactProvenance"]) {
    revokedCertification[field] = structuredClone(certification[field]);
  }
  revokedCertification.evidenceBundle = ensureRevisionBinding(revokedCertification.evidenceBundle);
  delete revokedCertification.candidateAuthorizationEpoch;
  revocation.releaseCertification = revisionBinding(revokedCertification, "certificationRef");
  revocation.siteReleaseCandidate = structuredClone(revokedCertification.siteReleaseCandidate);
  delete revocation.candidateAuthorizationEpoch;

  siteRelease.siteReleaseCandidate = structuredClone(intent.siteReleaseCandidate);
  siteRelease.launchProductProfile = structuredClone(intent.launchProductProfile);
  siteRelease.productSurfaceCatalog = structuredClone(intent.productSurfaceCatalog);
  siteRelease.surfaceInventory = structuredClone(intent.surfaceInventory);
  siteRelease.webBuildIntent = revisionBinding(intent, "intentRef");
  siteRelease.compiledWebManifest = revisionBinding(manifest, "manifestRef");
  siteRelease.webArtifactProvenance = revisionBinding(provenance, "provenanceRef");
  siteRelease.releaseCertification = revisionBinding(certification, "certificationRef");
  siteRelease.businessBindings = structuredClone(candidate.businessBindings);
  delete siteRelease.candidateAuthorizationEpoch;
  siteRelease.bootstrapBindings = {
    compiledWebManifest: structuredClone(siteRelease.compiledWebManifest),
    productSurfaceCatalog: structuredClone(siteRelease.productSurfaceCatalog),
    surfaceInventory: structuredClone(siteRelease.surfaceInventory),
    webCompositionRegistry: structuredClone(intent.webCompositionRegistry),
    webBuildToolchain: structuredClone(intent.webBuildToolchain),
  };

  for (const snapshot of [beginSnapshot, beforeCasSnapshot]) {
    snapshot.activationAttempt = ensureRevisionBinding(snapshot.activationAttempt);
    snapshot.activationCommand = ensureRevisionBinding(snapshot.activationCommand);
    snapshot.siteRelease = revisionBinding(siteRelease, "siteReleaseRef");
    snapshot.siteRef ??= siteRelease.siteRef;
    snapshot.environment ??= siteRelease.environment;
    snapshot.candidate.siteReleaseCandidate = structuredClone(siteRelease.siteReleaseCandidate);
    delete snapshot.candidate.authorizationEpoch;
    snapshot.certification.releaseCertification = structuredClone(siteRelease.releaseCertification);
    snapshot.certification.revocationEpoch = siteRelease.certificationRevocationEpoch;
    snapshot.certification.validUntil = certification.validUntil;
    snapshot.trust = structuredClone(certification.producer);
    refreshReceipts(
      snapshot,
      snapshot.phase === "activation-begin" ? "begin" : "before-cas",
      anchors,
      privateKeys,
    );
  }
  refreshBlockedSnapshots(corpus, beforeCasSnapshot, anchors, privateKeys);

  activationEvidence.activationAttempt = ensureRevisionBinding(activationEvidence.activationAttempt);
  activationEvidence.siteRelease = revisionBinding(siteRelease, "siteReleaseRef");
  activationEvidence.activationCommand ??= structuredClone(beforeCasSnapshot.activationCommand);
  activationEvidence.activationCommand = ensureRevisionBinding(activationEvidence.activationCommand);
  activationEvidence.casCommandRef ??= beforeCasSnapshot.casCommandRef;
  activationEvidence.casFence ??= structuredClone(beforeCasSnapshot.casFence);
  activationEvidence.beginAuthoritySnapshot = revisionBinding(beginSnapshot, "snapshotRef");
  activationEvidence.immediateBeforePointerCasAuthoritySnapshot = revisionBinding(beforeCasSnapshot, "snapshotRef");
  activationEvidence.expectedActivePointerGeneration = beforeCasSnapshot.expectedActivePointerGeneration;
  activationEvidence.casPreconditionDigest = beforeCasSnapshot.activePointer.casPreconditionDigest;
  const serverReceipt = beforeCasSnapshot.ownerReadReceipts.find(({ aggregateKind }) => aggregateKind === "active-pointer");
  if (activationEvidence.freshnessLease !== undefined && serverReceipt !== undefined) {
    activationEvidence.freshnessLease.serverTimeReceiptRef = serverReceipt.readReceiptRef;
    activationEvidence.freshnessLease.issuedAt = serverReceipt.observedAt;
    activationEvidence.freshnessLease.notAfter = new Date(Date.parse(serverReceipt.observedAt) + 5_000).toISOString();
  }
  activationEvidence.eligibilityMaterialDigest = canonicalDigest(eligibilityMaterial(activationEvidence));

  refreshNegativeCases(corpus);
  for (const vector of corpus.canonicalVectors) {
    const document = corpus.positiveCases.find(({ id }) => id === vector.caseId)?.document;
    if (document === undefined) throw new Error(`web_release_fixture_canonical_case_missing:${vector.id}`);
    vector.expectedDigest = canonicalDigest(document);
  }
  for (const vector of corpus.dsseVectors) resignVector(corpus, vector.caseId, privateKeys.get(vector.keyId));
}

function parseArguments(argv) {
  let check = false;
  let root = DEFAULT_ROOT;
  for (let index = 0; index < argv.length; index += 1) {
    if (argv[index] === "--check") {
      check = true;
      continue;
    }
    if (argv[index] === "--root" && argv[index + 1] !== undefined) {
      root = resolve(argv[index + 1]);
      index += 1;
      continue;
    }
    throw new Error(`web_release_fixture_arguments_invalid:${argv[index]}`);
  }
  return { check, root };
}

function main(argv) {
  const options = parseArguments(argv);
  const corpusPath = resolve(options.root, CORPUS_PATH);
  const anchorsPath = resolve(options.root, TRUST_ANCHORS_PATH);
  const corpusSource = readFileSync(corpusPath, "utf8");
  const anchorsSource = readFileSync(anchorsPath, "utf8");
  const corpus = JSON.parse(corpusSource);
  const anchors = JSON.parse(anchorsSource);
  refreshCoherentChain(corpus, anchors);
  const generatedCorpus = `${JSON.stringify(corpus, null, 2)}\n`;
  const generatedAnchors = `${JSON.stringify(anchors, null, 2)}\n`;
  if (options.check) {
    if (corpusSource !== generatedCorpus || anchorsSource !== generatedAnchors) {
      throw new Error("web_release_composition_corpus_stale");
    }
    process.stdout.write(`web_release_composition_corpus_ok:${Buffer.byteLength(generatedCorpus)} corpus bytes, ${Buffer.byteLength(generatedAnchors)} trust bytes\n`);
    return;
  }
  writeFileSync(corpusPath, generatedCorpus, "utf8");
  writeFileSync(anchorsPath, generatedAnchors, "utf8");
  process.stdout.write(`web_release_composition_corpus_generated:${corpusPath}\n`);
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  try {
    main(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(`${error.stack ?? error.message}\n`);
    process.exitCode = 1;
  }
}
