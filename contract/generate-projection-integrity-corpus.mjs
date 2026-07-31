#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { createHash, createPrivateKey, createPublicKey, sign } from "node:crypto";
import { readFileSync, realpathSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, isAbsolute, relative, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { create, createFileRegistry, fromBinary, fromJson, toBinary } from "@bufbuild/protobuf";
import { FileDescriptorSetSchema } from "@bufbuild/protobuf/wkt";

const CONTRACT = dirname(fileURLToPath(import.meta.url));
const MANIFEST = JSON.parse(readFileSync(resolve(CONTRACT, "spec/projection-integrity.yaml"), "utf8"));
const CORPUS = resolve(CONTRACT, "corpus/projection-integrity-v1.json");
const BUF = resolve(CONTRACT, "node_modules/.bin/buf");
// This fixed test-only seed makes public fixtures reproducible. It is never emitted,
// loaded by runtime code, or usable outside the explicitly named test key revision.
const TEST_ONLY_SEED = Buffer.from("84c5f250cb19ef8dad4635181a350e7c6d3d5283bbef5630e4f2bc84b8b4e824", "hex");
const TEST_KEY_REVISION = "projection-ed25519-fixture-v1";
const PRIVATE_KEY = createPrivateKey({
  key: Buffer.concat([Buffer.from("302e020100300506032b657004220420", "hex"), TEST_ONLY_SEED]),
  format: "der",
  type: "pkcs8",
});
const PUBLIC_KEY_BASE64 = createPublicKey(PRIVATE_KEY).export({ format: "der", type: "spki" }).toString("base64");

const FIXTURES = Object.freeze([
  Object.freeze({
    id: "media-binding-record",
    messageType: "kokoro.platform.media.v1.MediaProjectionBindingCommittedRecord",
    value: Object.freeze({ activationEventRef:"activation-1", bindingRef:"binding-1", operationRef:"operation-1", mediaCommandRef:"command-1", commandCommitReceiptRef:"receipt-1", commandCommitReceiptDigest:"a".repeat(64), producerGeneration:"1", definitionRef:"image", definitionRevisionRef:"image-r1", committedAt:"1970-01-01T00:00:00Z", sourceSequence:"1" }),
  }),
  Object.freeze({
    id: "media-event-record",
    messageType: "kokoro.platform.media.v1.MediaProjectionEventRecord",
    value: Object.freeze({ eventRef:"media-event-2", bindingRef:"binding-1", operationRef:"operation-1", operationOwnerVersion:"2", producerGeneration:"1", operationChanged:{queued:{}}, recordedAt:"1970-01-01T00:00:00Z", sourceSequence:"2", predecessorEventRef:"media-event-1", predecessorEventDigest:"b".repeat(64) }),
  }),
  Object.freeze({
    id: "credit-cost-event-record",
    messageType: "kokoro.platform.credit.v1.CreditCostProjectionEventRecord",
    value: Object.freeze({ eventRef:"credit-event-1", bindingRef:"binding-1", operationRef:"operation-1", costProjectionRef:"cost-1", ownerVersion:"1", pending:{}, recordedAt:"1970-01-01T00:00:00Z", producerGeneration:"1", sourceSequence:"1" }),
  }),
  Object.freeze({
    id: "media-head-record",
    messageType: "kokoro.platform.media.v1.MediaProjectionHead",
    value: Object.freeze({ bindingRef:"binding-1", operationRef:"operation-1", producerGeneration:"1", highWatermark:"2", headEventRef:"media-event-2", headEventDigest:"c".repeat(64), observedAt:"1970-01-01T00:00:00Z" }),
  }),
  Object.freeze({
    id: "credit-head-record",
    messageType: "kokoro.platform.credit.v1.CreditCostProjectionHead",
    value: Object.freeze({ bindingRef:"binding-1", costProjectionRef:"cost-1", producerGeneration:"1", highWatermark:"1", headEventRef:"credit-event-1", headEventDigest:"d".repeat(64), observedAt:"1970-01-01T00:00:00Z" }),
  }),
]);

function reject(code) { throw new Error(code); }
function registry() {
  const descriptorBytes = execFileSync(BUF, ["build", "proto", "--as-file-descriptor-set", "-o", "-"], { cwd: CONTRACT, encoding:"buffer", timeout:MANIFEST.limits.buf_timeout_ms, maxBuffer:MANIFEST.limits.descriptor_bytes, stdio:["ignore","pipe","pipe"] });
  return createFileRegistry(fromBinary(FileDescriptorSetSchema, descriptorBytes));
}
function signedFixture(descriptors, policies, signatureDomain, fixture) {
  const descriptor=descriptors.getMessage(fixture.messageType); const policy=policies.get(fixture.messageType);
  if (descriptor===undefined||policy===undefined) reject("PROJECTION_INTEGRITY_FIXTURE_DESCRIPTOR_MISSING");
  const record=Buffer.from(toBinary(descriptor,fromJson(descriptor,fixture.value))); const domain=Buffer.from(policy.domain_separator); const digest=createHash("sha256").update(domain).update(record).digest(); const signature=sign(null,Buffer.concat([signatureDomain,digest]),PRIVATE_KEY);
  return { id:fixture.id, messageType:fixture.messageType, domainSeparatorHex:domain.toString("hex"), canonicalRecordHex:record.toString("hex"), digestSha256:digest.toString("hex"), keyRevision:TEST_KEY_REVISION, publicKeySpkiBase64:PUBLIC_KEY_BASE64, signatureBase64:signature.toString("base64") };
}
function negativeCases(descriptors, policies, signatureDomain) {
  const event = descriptors.getMessage("kokoro.platform.media.v1.MediaProjectionEventRecord");
  const head = descriptors.getMessage("kokoro.platform.media.v1.MediaProjectionHead");
  const signatureField = event.fields.find(({ name }) => name === "signature");
  const structural = [
    { id:"nested-unknown-field-rejected", messageType:event.typeName, canonicalRecordHex:"4a039a0600", expectedErrorCode:"PROJECTION_INTEGRITY_UNKNOWN_FIELD" },
    { id:"excluded-record-digest-rejected", messageType:event.typeName, canonicalRecordHex:Buffer.from(toBinary(event,create(event,{recordDigest:"a".repeat(64)}))).toString("hex"), expectedErrorCode:"PROJECTION_INTEGRITY_EXCLUDED_FIELD" },
    { id:"signature-field-rejected", messageType:event.typeName, canonicalRecordHex:Buffer.from(toBinary(event,create(event,{signature:create(signatureField.message,{})}))).toString("hex"), expectedErrorCode:"PROJECTION_INTEGRITY_SIGNATURE_FIELD" },
    { id:"non-minimal-varint-rejected", messageType:head.typeName, canonicalRecordHex:"188100", expectedErrorCode:"PROJECTION_INTEGRITY_NON_CANONICAL_PROTOBUF" },
    { id:"explicit-default-rejected", messageType:head.typeName, canonicalRecordHex:"2000", expectedErrorCode:"PROJECTION_INTEGRITY_NON_CANONICAL_PROTOBUF" },
    { id:"invalid-utf8-rejected", messageType:head.typeName, canonicalRecordHex:"0a01ff", expectedErrorCode:"PROJECTION_INTEGRITY_PROTOBUF_INVALID" },
    { id:"required-field-missing-rejected", messageType:head.typeName, canonicalRecordHex:Buffer.from(toBinary(head,create(head,{bindingRef:"x"}))).toString("hex"), expectedErrorCode:"PROJECTION_INTEGRITY_CONSTRAINT_VIOLATION" },
  ];
  const mutations = [
    { ...FIXTURES[0], id:"binding-constraint-rejected", value:{...FIXTURES[0].value,sourceSequence:"2"} },
    { ...FIXTURES[1], id:"media-event-constraint-rejected", value:{...FIXTURES[1].value,sourceSequence:"1"} },
    { ...FIXTURES[2], id:"credit-event-constraint-rejected", value:{...FIXTURES[2].value,sourceSequence:"2"} },
    { ...FIXTURES[3], id:"media-head-constraint-rejected", value:{...FIXTURES[3].value,highWatermark:"0"} },
    { ...FIXTURES[4], id:"credit-head-constraint-rejected", value:{...FIXTURES[4].value,highWatermark:"0"} },
  ].map((fixture)=>({...signedFixture(descriptors,policies,signatureDomain,fixture),authenticated:true,expectedErrorCode:"PROJECTION_INTEGRITY_CONSTRAINT_VIOLATION"}));
  return [...structural,...mutations];
}
function generateCorpus() {
  const descriptors = registry();
  const signatureDomain = Buffer.from(MANIFEST.signature_domain_hex,"hex");
  const policies = new Map(MANIFEST.surfaces.map((surface)=>[surface.message_type,surface]));
  const cases = FIXTURES.map((fixture)=>signedFixture(descriptors,policies,signatureDomain,fixture));
  return `${JSON.stringify({schemaVersion:1,signatureDomainHex:MANIFEST.signature_domain_hex,cases,negativeCases:negativeCases(descriptors,policies,signatureDomain)},null,2)}\n`;
}
function temporaryOutput(path) {
  if (!isAbsolute(path)) reject("PROJECTION_INTEGRITY_FIXTURE_OUTPUT_INVALID");
  const output=resolve(realpathSync(dirname(path)),basename(path)); const rel=relative(realpathSync(tmpdir()),output);
  if(rel.startsWith("..")||isAbsolute(rel)) reject("PROJECTION_INTEGRITY_FIXTURE_OUTPUT_INVALID"); return output;
}
function main(argv) {
  const generated=generateCorpus();
  if(argv.length===1&&argv[0]==="--check") { let current; try{current=JSON.parse(readFileSync(CORPUS,"utf8"));}catch{reject("PROJECTION_INTEGRITY_CORPUS_STALE");} if(JSON.stringify(current)!==JSON.stringify(JSON.parse(generated))) reject("PROJECTION_INTEGRITY_CORPUS_STALE"); process.stdout.write("projection_integrity_corpus_reproducible\n"); return; }
  if(argv.length===2&&argv[0]==="--output") { const output=temporaryOutput(argv[1]); writeFileSync(output,generated,{encoding:"utf8",flag:"wx"}); process.stdout.write(`projection_integrity_corpus_generated:${output}\n`); return; }
  reject("PROJECTION_INTEGRITY_FIXTURE_ARGUMENT_INVALID");
}

if(import.meta.url===pathToFileURL(process.argv[1]??"").href) main(process.argv.slice(2));
