#!/usr/bin/env python3
"""Run-owned Platform local import -> Storage/S3/ClamAV qualification."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLATFORM = ROOT / "var/dev/platform-release"
DEFAULT_STORAGE = Path("/Users/nako/.codex/worktrees/kokoro-storage-formal")
DEFAULT_RUNTIME_CONFIG = ROOT / "var/dev/page-runtime/config-private.json"
CASES = ("clean", "eicar", "ack_lost")


class QualificationError(RuntimeError):
    pass


def required(env: dict[str, str], name: str) -> str:
    value = env.get(name, "")
    if not value or value != value.strip():
        raise QualificationError(f"required private environment key missing: {name}")
    return value


def wait_json(path: Path, process: subprocess.Popen[str], timeout: float) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise QualificationError("Storage harness exited before readiness")
        if path.is_file():
            value = json.loads(path.read_text())
            if isinstance(value, dict):
                return value
        time.sleep(0.05)
    raise QualificationError("Storage harness readiness deadline exceeded")


def node24(node: str) -> None:
    result = subprocess.run(
        [node, "--version"], check=True, text=True, capture_output=True
    ).stdout.strip()
    if not result.startswith("v24."):
        raise QualificationError("qualification requires Node 24")


def validate_harness_syntax(node: str, storage: Path, source: str) -> None:
    checker = """
const ts=require('typescript');let source='';
process.stdin.setEncoding('utf8');process.stdin.on('data',c=>source+=c);
process.stdin.on('end',()=>{const value=ts.transpileModule(source,{reportDiagnostics:true,compilerOptions:{target:ts.ScriptTarget.ES2024,module:ts.ModuleKind.ESNext}});const errors=(value.diagnostics??[]).filter(d=>d.category===ts.DiagnosticCategory.Error);if(errors.length){process.stderr.write(errors.map(d=>ts.flattenDiagnosticMessageText(d.messageText,' ')).join('\\n'));process.exit(1);}});
"""
    subprocess.run(
        [node, "-e", checker],
        cwd=storage,
        input=source,
        text=True,
        check=True,
        stdout=subprocess.DEVNULL,
    )


def write_manifest(path: Path, value: dict[str, object]) -> None:
    temporary = path.with_suffix(".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(json.dumps(value) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    os.replace(temporary, path)


def open_private_log(path: Path):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    return os.fdopen(descriptor, "w")


def update_failure_manifest(path: Path, error: BaseException, log_path: Path) -> None:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        value = {"version": 1}
    if not isinstance(value, dict):
        value = {"version": 1}
    value.update(
        {
            "phase": "failed-preserved",
            "errorClass": type(error).__name__,
            "logPath": str(log_path),
        }
    )
    write_manifest(path, value)


def prepare_journal_root(environment: dict[str, str], owner: Path) -> None:
    journal = Path(environment["KOKORO_SMOKE_JOURNAL_ROOT"])
    if journal.parent.resolve() != owner.resolve() or journal.name != "journal":
        raise QualificationError("journal root is outside this run")
    journal.mkdir(mode=0o700)
    journal.chmod(0o700)


def validate_harness_load(
    node: str, storage: Path, storage_config: dict[str, str]
) -> None:
    evidence = Path(tempfile.mkdtemp(prefix="kokoro-storage-qualify-load-"))
    harness_directory = storage / ".tmp" / f"qualify-load-{secrets.token_hex(8)}"
    harness_directory.mkdir(parents=True, mode=0o700)
    harness_directory.chmod(0o700)
    harness = harness_directory / "storage-harness.ts"
    try:
        harness.write_text(harness_source(storage))
        env, _credential = case_environment(
            dict(os.environ), storage_config, evidence, "clean"
        )
        prepare_journal_root(env, evidence)
        env["QUALIFY_LOAD_ONLY"] = "1"
        env["QUALIFY_MANIFEST"] = str(evidence / "resource-manifest.json")
        write_manifest(
            Path(env["QUALIFY_MANIFEST"]),
            {
                "version": 1,
                "caseId": env["QUALIFY_CASE_ID"],
                "caseKind": "clean",
                "bucket": env["KOKORO_OBJECT_STORE_BUCKET"],
                "phase": "pre-resource-load",
            },
        )
        subprocess.run(
            [node, str(storage / "node_modules/tsx/dist/cli.mjs"), str(harness)],
            cwd=storage,
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        async_ack_manifest = evidence / "async-ack-manifest.json"
        env["QUALIFY_LOAD_ONLY"] = "0"
        env["QUALIFY_ASYNC_ACK_TEST"] = "1"
        env["QUALIFY_MANIFEST"] = str(async_ack_manifest)
        write_manifest(
            async_ack_manifest,
            {
                "version": 1,
                "caseId": env["QUALIFY_CASE_ID"],
                "caseKind": "clean",
                "bucket": env["KOKORO_OBJECT_STORE_BUCKET"],
                "phase": "async-ack-start",
            },
        )
        subprocess.run(
            [node, str(storage / "node_modules/tsx/dist/cli.mjs"), str(harness)],
            cwd=storage,
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        async_ack_result = json.loads(async_ack_manifest.read_text())
        if async_ack_result.get("asyncAckObserved") is not True:
            raise QualificationError("asynchronous IPC acknowledgement was not observed")
        teardown_manifest = evidence / "teardown-manifest.json"
        env["QUALIFY_ASYNC_ACK_TEST"] = "0"
        env["QUALIFY_TEARDOWN_TEST"] = "1"
        env["QUALIFY_MANIFEST"] = str(teardown_manifest)
        write_manifest(
            teardown_manifest,
            {
                "version": 1,
                "caseId": env["QUALIFY_CASE_ID"],
                "caseKind": "clean",
                "bucket": env["KOKORO_OBJECT_STORE_BUCKET"],
                "phase": "teardown-negative-start",
            },
        )
        negative = subprocess.run(
            [node, str(storage / "node_modules/tsx/dist/cli.mjs"), str(harness)],
            cwd=storage,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        if negative.returncode == 0:
            raise QualificationError("teardown preservation negative unexpectedly passed")
        result = json.loads(teardown_manifest.read_text())
        if (
            result.get("phase") != "preserved"
            or result.get("bucketCreated") is not False
            or result.get("runtimeStopped") is not False
            or result.get("databaseOutcome") != "preserved"
            or result.get("runtimeStopReached") is not True
            or result.get("providerPreserved") is not True
            or result.get("databasePreserved") is not True
            or result.get("activeSockets") != 0
        ):
            raise QualificationError(
                "teardown preservation negative drifted: "
                + json.dumps(
                    {
                        key: result.get(key)
                        for key in (
                            "phase",
                            "bucketCreated",
                            "runtimeStopped",
                            "databaseOutcome",
                            "runtimeStopReached",
                            "providerPreserved",
                            "databasePreserved",
                            "activeSockets",
                        )
                    }
                )
            )
    finally:
        shutil.rmtree(harness_directory, ignore_errors=True)
        shutil.rmtree(evidence, ignore_errors=True)


def harness_source(storage: Path) -> str:
    fixture = storage / "test/fixtures"
    generated = storage / "src/generated/proto/kokoro/storage/v3/storage_pb.ts"
    asset_constants = storage / "src/assets/asset.constants.ts"
    return f'''import {{ createConnection, createServer }} from "node:net";
import {{ chmod, readFile, rename, rm, writeFile }} from "node:fs/promises";
import {{ createHash }} from "node:crypto";
import {{ create, fromBinary, toBinary }} from "@bufbuild/protobuf";
import {{
  CreateBucketCommand, DeleteBucketCommand, GetBucketVersioningCommand,
  HeadBucketCommand, ListObjectVersionsCommand, PutBucketVersioningCommand,
  S3Client
}} from "@aws-sdk/client-s3";
import {{ loadSmokeProviderConfig }} from {json.dumps(str(fixture / 'smoke-provider.schema.ts'))};
import {{ SmokeProvider }} from {json.dumps(str(fixture / 'smoke-provider.ts'))};
import {{ SmokeRuntime }} from {json.dumps(str(fixture / 'smoke-runtime.ts'))};
import {{ SmokeStorageMetadata }} from {json.dumps(str(fixture / 'smoke-storage-metadata.ts'))};
import {{ isolatedPrisma }} from {json.dumps(str(fixture / 'isolated-prisma.ts'))};
import {{ CreateUploadRequestSchema, CompleteUploadRequestSchema, CompleteUploadResponseSchema, ScanState as WireScanState }} from {json.dumps(str(generated))};
import {{ ScanState as FixtureScanState }} from {json.dumps(str(asset_constants))};

const need = (name) => {{ const value=process.env[name]; if(!value || value!==value.trim()) throw new Error(name+" required"); return value; }};
const readyPath=need("QUALIFY_READY"), donePath=need("QUALIFY_DONE"), socketPath=need("QUALIFY_SOCKET"), token=need("QUALIFY_TOKEN"), caseId=need("QUALIFY_CASE_ID"), caseKind=need("QUALIFY_CASE"), manifestPath=need("QUALIFY_MANIFEST");
const bucket=need("KOKORO_OBJECT_STORE_BUCKET"), subjectId="fixture-subject";
const config=loadSmokeProviderConfig(process.env);
const sdk=new S3Client({{region:config.runtime.objectStore.region,forcePathStyle:config.runtime.objectStore.forcePathStyle,...(config.runtime.objectStore.endpoint?{{endpoint:config.runtime.objectStore.endpoint}}:{{}}),...(config.runtime.objectStore.accessKeyId&&config.runtime.objectStore.secretAccessKey?{{credentials:{{accessKeyId:config.runtime.objectStore.accessKeyId,secretAccessKey:config.runtime.objectStore.secretAccessKey}}}}:{{}})}});
let provider, owned, metadata, runtime, server, createRequest, completeRequest, stagingKey, completeAsset, expectedScanState, bucketCreated=false, teardownSocket, runtimeStopReached=false, providerPreserved=false, databasePreserved=false, asyncAckObserved=false;
const activeSockets=new Set();
const cache=new Map(); let expectedSeq=1, failure;
const digest=(value)=>createHash("sha256").update(value).digest("hex");
const commandIdentity=(wire)=>{{if(!wire?.commandId || !wire.requestDigest)throw new Error("wire command identity missing");return {{commandId:wire.commandId,requestDigest:wire.requestDigest}};}};
const createClientInput=(wire)=>({{...commandIdentity(wire.command),filename:wire.filename,mimeType:wire.mimeType,sizeBytes:wire.sizeBytes,contentSha256:wire.contentSha256,uploadPurpose:wire.uploadPurpose}});
const completeClientInput=(wire)=>({{...commandIdentity(wire.command),sourceVersionId:wire.sourceVersionId,uploadId:wire.uploadId,contentSha256:wire.contentSha256,sizeBytes:wire.sizeBytes}});
const clientCommandId=(input)=>{{if(!input?.commandId || "command" in input)throw new Error("owner command projection invalid");return input.commandId;}};
let ipcKind="none",ipcStage="idle";
const privateIpcFailure=(error)=>{{const errorClass=error instanceof Error?error.name:"NonError";const errorMessage=error instanceof Error?error.message:"non-error thrown";process.stderr.write(JSON.stringify({{event:"qualification_ipc_failed",kind:ipcKind,stage:ipcStage,errorClass,errorMessage}})+"\\n");}};
async function manifest(phase,extra={{}}) {{ const value={{version:1,caseId,caseKind,bucket,phase,...extra}}; const temporary=manifestPath+".tmp"; await writeFile(temporary,JSON.stringify(value)+"\\n",{{mode:0o600}}); await chmod(temporary,0o600); await rename(temporary,manifestPath); }}
const exactHeaders=(h, skillId) => {{
  const expected={{"x-kokoro-service":"kokoro-platform","x-kokoro-tenant-id":provider.tenantId,"x-kokoro-subject-id":subjectId,"x-kokoro-scope-kind":"skill_package","x-kokoro-scope-id":skillId}};
  const allowed=[...Object.keys(expected),"x-kokoro-request-id"].sort();
  if(!h || Object.keys(h).sort().join("\0")!==allowed.join("\0"))throw new Error("trusted Storage header set drift");
  for(const [k,v] of Object.entries(expected)) if(h?.[k]!==v) throw new Error("trusted Storage identity drift");
  if(typeof h?.["x-kokoro-request-id"]!=="string" || !h["x-kokoro-request-id"]) throw new Error("request identity missing");
  return h["x-kokoro-request-id"];
}};
const messageFingerprint=(message)=>{{
  if(message.kind!=="register_canonical")return digest(JSON.stringify([message.kind,message.payload]));
  const p=message.payload,wire=fromBinary(CompleteUploadRequestSchema,Buffer.from(p.request,"base64")),complete=completeClientInput(wire),response=fromBinary(CompleteUploadResponseSchema,Buffer.from(p.response,"base64"));
  exactHeaders(p.headers,metadata.scopeId);
  if(!completeRequest || complete.commandId!==completeRequest.commandId || complete.requestDigest!==completeRequest.requestDigest || complete.sourceVersionId!==completeRequest.sourceVersionId || complete.uploadId!==completeRequest.uploadId || complete.contentSha256!==completeRequest.contentSha256 || complete.sizeBytes!==completeRequest.sizeBytes)throw new Error("canonical request differs from prepared completion");
  const expectedWireScanState=expectedScanState===FixtureScanState.Infected?WireScanState.INFECTED:WireScanState.CLEAN;
  if(response.uploadId!==complete.uploadId || !response.assetId || response.scanState!==expectedWireScanState)throw new Error("canonical response differs from prepared completion");
  return digest(JSON.stringify([message.kind,complete.commandId,complete.requestDigest,complete.sourceVersionId,complete.uploadId,complete.contentSha256,complete.sizeBytes.toString(),response.uploadId,response.assetId,response.scanState,metadata.scopeId]));
}};
async function handle(message) {{
  if(message?.version!==1 || message.caseId!==caseId || message.token!==token || message.seq!==expectedSeq++ || !["bind_scope","put_version","prepare_complete","register_canonical"].includes(message.kind)) throw new Error("closed IPC envelope denied");
  ipcKind=message.kind;ipcStage="envelope_validated";
  const fingerprint=messageFingerprint(message);
  const prior=cache.get(message.kind);
  if(prior) {{ if(prior.fingerprint!==fingerprint) throw new Error("IPC replay drift"); return prior.phase; }}
  const p=message.payload;
  if(message.kind==="bind_scope") {{
    ipcStage="decode_create";const createWire=fromBinary(CreateUploadRequestSchema,Buffer.from(p.createRequest,"base64"));createRequest={{...createClientInput(createWire),requestId:exactHeaders(p.headers,p.skillId)}};
    if(createRequest.filename!==`${{caseKind}}.skill` || p.uploadId==="" || !["clean","infected"].includes(p.expectedScanState)) throw new Error("bind scope payload invalid");
    expectedScanState=p.expectedScanState==="infected"?FixtureScanState.Infected:FixtureScanState.Clean;
    ipcStage="bind_metadata";metadata=new SmokeStorageMetadata(owned,{{tenantId:provider.tenantId,ownerId:subjectId,scopeKind:"skill_package",scopeId:p.skillId,serviceId:"kokoro-platform"}});
    provider.bindMetadata(metadata);
    ipcStage="prove_create";
    stagingKey=await metadata.staging({{create:createRequest,uploadId:p.uploadId}});
    await provider.beginWrite({{key:stagingKey,sha256:createRequest.contentSha256,sizeBytes:Number(createRequest.sizeBytes)}});
    cache.set(message.kind,{{fingerprint,phase:"scope_bound"}}); return "scope_bound";
  }}
  if(message.kind==="put_version") {{
    if(!stagingKey || typeof p.versionId!=="string" || p.versionId==="null" || typeof p.etag!=="string") throw new Error("PUT identity invalid");
    await provider.registerVersion({{key:stagingKey,version:p.versionId,etag:p.etag}});
    cache.set(message.kind,{{fingerprint,phase:"put_registered"}}); return "put_registered";
  }}
  if(message.kind==="prepare_complete") {{
    ipcStage="decode_complete";const completeWire=fromBinary(CompleteUploadRequestSchema,Buffer.from(p.request,"base64"));completeRequest={{...completeClientInput(completeWire),requestId:exactHeaders(p.headers,metadata.scopeId)}};
    ipcStage="prove_complete";await provider.expectCompletion({{create:createRequest,complete:completeRequest,expectedScanState}});
    cache.set(message.kind,{{fingerprint,phase:"complete_expected"}}); return "complete_expected";
  }}
  if(!completeRequest) throw new Error("complete expectation missing");
  const response=fromBinary(CompleteUploadResponseSchema,Buffer.from(p.response,"base64"));
  exactHeaders(p.headers,metadata.scopeId);
  const expectedWireScanState=expectedScanState===FixtureScanState.Infected?WireScanState.INFECTED:WireScanState.CLEAN;
  if(response.scanState!==expectedWireScanState)throw new Error("wire scan state differs from fixture expectation");
  if(response.assetId!==completeAsset && completeAsset!==undefined) throw new Error("canonical replay asset drift");
  if(completeAsset===undefined) {{ await provider.registerCanonical({{commandId:clientCommandId(completeRequest),assetId:response.assetId}}); completeAsset=response.assetId; }}
  cache.set(message.kind,{{fingerprint,phase:"canonical_registered"}}); return "canonical_registered";
}}
async function emptyBucket() {{
  let keyMarker, versionMarker;
  for(let page=0;page<1000;page++) {{
    const value=await sdk.send(new ListObjectVersionsCommand({{Bucket:bucket,MaxKeys:100,...(keyMarker?{{KeyMarker:keyMarker}}:{{}}),...(versionMarker?{{VersionIdMarker:versionMarker}}:{{}})}}));
    if((value.Versions?.length??0)!==0 || (value.DeleteMarkers?.length??0)!==0) throw new Error("owned bucket is not empty after exact cleanup");
    if(!value.IsTruncated) return;
    if(!value.NextKeyMarker || !value.NextVersionIdMarker) throw new Error("bucket inventory made no progress");
    keyMarker=value.NextKeyMarker; versionMarker=value.NextVersionIdMarker;
  }} throw new Error("bucket inventory page bound reached");
}}
async function stopServer() {{
 if(!server)return;
 const closing=server;server=undefined;
 const closed=Promise.withResolvers(); closing.close(error=>error?closed.reject(error):closed.resolve());
 let graceful=true;
 await Promise.race([closed.promise,new Promise(resolve=>setTimeout(()=>{{graceful=false;resolve();}},250))]);
 if(!graceful){{const sockets=[...activeSockets],socketsClosed=Promise.all(sockets.map(socket=>socket.destroyed?Promise.resolve():new Promise(resolve=>socket.once("close",resolve))));for(const socket of sockets)socket.destroy();await Promise.race([Promise.all([closed.promise,socketsClosed]),new Promise((_,reject)=>setTimeout(()=>reject(new Error("IPC forced drain deadline exceeded")),2000))]);throw new Error("IPC server drain deadline exceeded");}}
}}
async function main() {{
 if(process.env.QUALIFY_ASYNC_ACK_TEST==="1") {{
   await rm(socketPath,{{force:true}});
   server=createServer({{allowHalfOpen:true}},socket=>{{activeSockets.add(socket);socket.once("close",()=>activeSockets.delete(socket));let text="";socket.setEncoding("utf8");socket.on("data",chunk=>text+=chunk);socket.on("end",()=>void (async()=>{{await new Promise(resolve=>setTimeout(resolve,25));const message=JSON.parse(text);socket.end(JSON.stringify({{version:1,caseId,seq:message.seq,ok:true,phase:"async_ack"}}));}})());}});
   await new Promise((resolve,reject)=>server.listen(socketPath,resolve).once("error",reject));
   const response=await new Promise((resolve,reject)=>{{const client=createConnection(socketPath);let text="";client.setEncoding("utf8");client.once("connect",()=>client.end(JSON.stringify({{version:1,caseId,seq:1}})));client.on("data",chunk=>text+=chunk);client.once("end",()=>resolve(text));client.once("error",reject);}});
   const acknowledgement=JSON.parse(response);if(acknowledgement.ok!==true || acknowledgement.phase!=="async_ack")throw new Error("asynchronous IPC acknowledgement drifted");asyncAckObserved=true;
   await stopServer();await rm(socketPath,{{force:true}});await manifest("async-ack-passed");return;
 }}
 if(process.env.QUALIFY_TEARDOWN_TEST==="1") {{
   runtime={{stoppedConfirmed:false,stop:async()=>{{runtimeStopReached=true;throw new Error("injected runtime stop failure");}}}};
   provider={{preserveDatabase:false,close:async(options)=>{{provider.preserveDatabase=options?.preserveObjects===true;if(!provider.preserveDatabase)throw new Error("objects were not preserved");}}}};
   owned={{evidence:{{databaseName:"dry-run-owned",outcome:"not-dropped"}},close:async(options)=>{{if(options?.preserveDatabase!==true)throw new Error("database was not preserved");owned.evidence.outcome="preserved";}}}};
   await rm(socketPath,{{force:true}}); server=createServer(socket=>{{activeSockets.add(socket);socket.once("close",()=>activeSockets.delete(socket));}});
   await new Promise((resolve,reject)=>server.listen(socketPath,resolve).once("error",reject)); teardownSocket=createConnection(socketPath); await new Promise((resolve,reject)=>teardownSocket.once("connect",resolve).once("error",reject));
   return;
 }}
 if(process.env.QUALIFY_LOAD_ONLY==="1") {{ let rejected=false;try{{createClientInput({{command:undefined}});}}catch{{rejected=true;}}if(!rejected)throw new Error("wire projection negative did not reject");const projected=completeClientInput({{command:{{commandId:"fixture-command",requestDigest:"fixture-digest"}},sourceVersionId:"fixture-version",uploadId:"fixture-upload",contentSha256:"0".repeat(64),sizeBytes:1n}});if(clientCommandId(projected)!=="fixture-command" || "command" in projected)throw new Error("owner command projection drifted");if(FixtureScanState.Clean!=="clean" || FixtureScanState.Infected!=="infected" || WireScanState.CLEAN!==2 || WireScanState.INFECTED!==3 || Object.is(FixtureScanState.Clean,WireScanState.CLEAN) || Object.is(FixtureScanState.Infected,WireScanState.INFECTED))throw new Error("fixture and wire scan state semantics collapsed");provider={{tenantId:"fixture-tenant"}};metadata={{scopeId:"fixture-skill"}};const headers={{"x-kokoro-service":"kokoro-platform","x-kokoro-tenant-id":"fixture-tenant","x-kokoro-subject-id":subjectId,"x-kokoro-request-id":"create-request","x-kokoro-scope-kind":"skill_package","x-kokoro-scope-id":"fixture-skill"}};let extraRejected=false;try{{exactHeaders({{...headers,"x-untrusted-extra":"denied"}},"fixture-skill");}}catch{{extraRejected=true;}}if(!extraRejected)throw new Error("closed header negative did not reject");if(exactHeaders(headers,"fixture-skill")!=="create-request" || exactHeaders({{...headers,"x-kokoro-request-id":"complete-request"}},"fixture-skill")!=="complete-request")throw new Error("independent request identity was not returned");completeRequest={{...projected,requestId:"complete-request"}};expectedScanState=FixtureScanState.Clean;const request=(overrides={{}})=>Buffer.from(toBinary(CompleteUploadRequestSchema,create(CompleteUploadRequestSchema,{{command:{{commandId:overrides.commandId??"fixture-command",requestDigest:overrides.requestDigest??"fixture-digest"}},sourceVersionId:overrides.sourceVersionId??"fixture-version",uploadId:overrides.uploadId??"fixture-upload",contentSha256:overrides.contentSha256??"0".repeat(64),sizeBytes:overrides.sizeBytes??1n}}))).toString("base64"),response=(replayed,overrides={{}})=>Buffer.from(toBinary(CompleteUploadResponseSchema,create(CompleteUploadResponseSchema,{{uploadId:overrides.uploadId??"fixture-upload",assetId:overrides.assetId??"fixture-asset",scanState:overrides.scanState??WireScanState.CLEAN,replayed}}))).toString("base64"),canonical=(replayed,requestOverrides={{}},responseOverrides={{}})=>({{kind:"register_canonical",payload:{{request:request(requestOverrides),response:response(replayed,responseOverrides),headers:{{...headers,"x-kokoro-request-id":"complete-request"}}}}}});if(messageFingerprint(canonical(false))!==messageFingerprint(canonical(true)))throw new Error("legal replay changed canonical semantic fingerprint");for(const [name,message] of [["command",canonical(false,{{commandId:"other-command"}})],["digest",canonical(false,{{requestDigest:"other-digest"}})],["source version",canonical(false,{{sourceVersionId:"other-version"}})],["content digest",canonical(false,{{contentSha256:"1".repeat(64)}})],["size",canonical(false,{{sizeBytes:2n}})],["upload request",canonical(false,{{uploadId:"other-upload"}})],["upload response",canonical(false,{{}},{{uploadId:"other-upload"}})],["empty asset",canonical(false,{{}},{{assetId:""}})],["scan",canonical(false,{{}},{{scanState:WireScanState.INFECTED}})]]){{let denied=false;try{{messageFingerprint(message);}}catch{{denied=true;}}if(!denied)throw new Error("canonical "+name+" drift was accepted on first attempt");}}provider=undefined;metadata=undefined;const probe=new SmokeProvider(config);await probe.journal.initialize();await probe.journal.close();await rm(probe.journal.directory,{{recursive:true,force:true}});await manifest("load-only");return; }}
 await manifest("bucket-create-start");
 await sdk.send(new CreateBucketCommand({{Bucket:bucket,ObjectLockEnabledForBucket:true}})); bucketCreated=true; await manifest("bucket-created");
 await sdk.send(new PutBucketVersioningCommand({{Bucket:bucket,VersioningConfiguration:{{Status:"Enabled"}}}}));
 const versioning=await sdk.send(new GetBucketVersioningCommand({{Bucket:bucket}})); if(versioning.Status!=="Enabled") throw new Error("versioning not enabled");
 provider=new SmokeProvider(config); await provider.initialize();
 owned=await isolatedPrisma(config.runtime.postgresUrl); await manifest("storage-database-created",{{databaseName:owned.evidence.databaseName}});
 runtime=new SmokeRuntime({{...process.env,KOKORO_POSTGRES_URL:owned.url,KOKORO_STORAGE_HOST:"127.0.0.1",KOKORO_STORAGE_PORT:"0"}});
 const baseUrl=await runtime.start(); await manifest("runtime-started",{{databaseName:owned.evidence.databaseName}});
 await rm(socketPath,{{force:true}}); server=createServer({{allowHalfOpen:true}},(socket)=>{{activeSockets.add(socket);socket.once("close",()=>activeSockets.delete(socket));let text=""; socket.setEncoding("utf8"); socket.on("data",c=>{{text+=c;if(text.length>65536)socket.destroy();}}); socket.on("end",()=>void (async()=>{{try{{const m=JSON.parse(text);const phase=await handle(m);ipcStage="acknowledged";socket.end(JSON.stringify({{version:1,caseId,seq:m.seq,ok:true,phase}}));}}catch(e){{failure=e;privateIpcFailure(e);socket.end(JSON.stringify({{version:1,caseId,seq:JSON.parse(text||"{{}}").seq,ok:false,error:"qualification IPC denied"}}));}}}})());}});
 await new Promise((resolve,reject)=>server.listen(socketPath,()=>resolve()).once("error",reject)); await chmod(socketPath,0o600);
 await writeFile(readyPath,JSON.stringify({{baseUrl,tenantId:provider.tenantId,subjectId}}),{{mode:0o600}}); await manifest("test-running",{{databaseName:owned.evidence.databaseName}});
 while(true){{try{{const done=JSON.parse(await readFile(donePath,"utf8"));if(done.success!==true && !failure)failure=new Error("Platform qualification child failed; preserve run evidence");break;}}catch{{await new Promise(r=>setTimeout(r,50));}}}}
}}
async function close() {{
 const failures=[]; let preserve=Boolean(failure);
 try{{await stopServer();}}catch(e){{failures.push(e);preserve=true;for(const socket of activeSockets)socket.destroy();}}
 try{{if(runtime){{runtimeStopReached=true;await runtime.stop();if(!runtime.stoppedConfirmed)throw new Error("runtime stop was not confirmed");}}}}catch(e){{failures.push(e);preserve=true;}}
 try{{await metadata?.close();}}catch(e){{failures.push(e);preserve=true;}}
 try{{if(provider)await provider.close({{preserveObjects:preserve}});}}catch(e){{failures.push(e);preserve=true;}}finally{{providerPreserved=provider?.preserveDatabase===true;}}
 if(bucketCreated && !preserve){{try{{await emptyBucket();await sdk.send(new DeleteBucketCommand({{Bucket:bucket}}));bucketCreated=false;try{{await sdk.send(new HeadBucketCommand({{Bucket:bucket}}));throw new Error("bucket still exists");}}catch(e){{if(e?.$metadata?.httpStatusCode!==404)throw e;}}}}catch(e){{failures.push(e);preserve=true;}}}}
 try{{if(owned){{const preserveDatabase=preserve||provider?.preserveDatabase===true;await owned.close({{preserveDatabase}});}}}}catch(e){{failures.push(e);preserve=true;}}finally{{databasePreserved=owned?.evidence.outcome==="preserved";}}
 try{{await manifest(preserve?"preserved":"cleanup-complete",{{...(owned?{{databaseName:owned.evidence.databaseName,databaseOutcome:owned.evidence.outcome}}:{{}}),bucketCreated,runtimeStopped:runtime?.stoppedConfirmed===true,runtimeStopReached,providerPreserved,databasePreserved,asyncAckObserved,activeSockets:activeSockets.size}});}}catch(e){{failures.push(e);preserve=true;}}
 teardownSocket?.destroy(); sdk.destroy(); await rm(socketPath,{{force:true}}); if(failures.length)throw new AggregateError(failures,"qualification cleanup failed");
}}
try{{await main();}}catch(e){{failure=e;}}finally{{try{{await close();}}catch(e){{failure=failure?new AggregateError([failure,e]):e;}}}} if(failure)throw failure;
'''


def case_environment(
    source: dict[str, str],
    storage_config: dict[str, str],
    directory: Path,
    case: str,
) -> tuple[dict[str, str], str]:
    credential = secrets.token_hex(32)
    bucket = f"kokoro-platform-import-{secrets.token_hex(10)}"
    env = {
        **source,
        "NODE_ENV": "development",
        "KOKORO_POSTGRES_URL": required(storage_config, "KOKORO_POSTGRES_URL"),
        "KOKORO_REDIS_URL": required(storage_config, "KOKORO_REDIS_URL"),
        "KOKORO_STORAGE_SERVICE_CREDENTIALS": f"kokoro-platform={credential}",
        "KOKORO_OBJECT_STORE_DRIVER": "s3",
        "KOKORO_OBJECT_STORE_PROFILE": "custom",
        "KOKORO_OBJECT_STORE_BUCKET": bucket,
        "KOKORO_OBJECT_STORE_REGION": required(storage_config, "KOKORO_OBJECT_STORE_REGION"),
        "KOKORO_OBJECT_STORE_ENDPOINT": required(storage_config, "KOKORO_OBJECT_STORE_ENDPOINT"),
        "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT": required(storage_config, "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT"),
        "KOKORO_OBJECT_STORE_ACCESS_KEY_ID": required(storage_config, "KOKORO_OBJECT_STORE_ACCESS_KEY_ID"),
        "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY": required(storage_config, "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY"),
        "KOKORO_OBJECT_STORE_FORCE_PATH_STYLE": "true",
        "KOKORO_SCANNER_DRIVER": "clamav",
        "KOKORO_SCANNER_HOST": required(storage_config, "KOKORO_SCANNER_HOST"),
        "KOKORO_SCANNER_PORT": required(storage_config, "KOKORO_SCANNER_PORT"),
        "KOKORO_SMOKE_JOURNAL_ROOT": str(directory / "journal"),
        "QUALIFY_READY": str(directory / "ready.json"),
        "QUALIFY_DONE": str(directory / "done.json"),
        "QUALIFY_SOCKET": str(directory / "control.sock"),
        "QUALIFY_TOKEN": secrets.token_hex(32),
        "QUALIFY_CASE_ID": secrets.token_hex(16),
        "QUALIFY_CASE": case,
    }
    return env, credential


def run_case(
    platform: Path,
    storage: Path,
    node: str,
    storage_config: dict[str, str],
    case: str,
) -> None:
    directory = Path(tempfile.mkdtemp(prefix=f"kokoro-storage-qualify-{case}-"))
    harness_directory = storage / ".tmp" / f"qualify-{case}-{secrets.token_hex(8)}"
    harness_directory.mkdir(parents=True, mode=0o700)
    harness_directory.chmod(0o700)
    succeeded = False
    try:
        harness = harness_directory / "storage-harness.ts"
        harness.write_text(harness_source(storage))
        env, credential = case_environment(
            dict(os.environ), storage_config, directory, case
        )
        prepare_journal_root(env, directory)
        env["QUALIFY_MANIFEST"] = str(directory / "resource-manifest.json")
        write_manifest(
            Path(env["QUALIFY_MANIFEST"]),
            {
                "version": 1,
                "caseId": env["QUALIFY_CASE_ID"],
                "caseKind": case,
                "bucket": env["KOKORO_OBJECT_STORE_BUCKET"],
                "phase": "pre-resource-load",
            },
        )
        log_path = directory / "harness.log"
        command = [node, str(storage / "node_modules/tsx/dist/cli.mjs"), str(harness)]
        log_handle = open_private_log(log_path)
        try:
            process = subprocess.Popen(
                command,
                cwd=storage,
                env=env,
                text=True,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
            )
        except BaseException as error:
            log_handle.close()
            update_failure_manifest(Path(env["QUALIFY_MANIFEST"]), error, log_path)
            raise
        log_handle.close()
        test_error: BaseException | None = None
        try:
            ready = wait_json(Path(env["QUALIFY_READY"]), process, 90)
            test_env = {
                **os.environ,
                "KOKORO_E2E": "1",
                "KOKORO_TEST_POSTGRES_ADMIN_URL": env["KOKORO_POSTGRES_URL"],
                "KOKORO_STORAGE_URL": str(ready["baseUrl"]),
                "KOKORO_PLATFORM_STORAGE_SERVICE_CREDENTIAL": credential,
                "KOKORO_STORAGE_QUALIFY_CASE": case,
                "KOKORO_STORAGE_QUALIFY_TENANT_ID": str(ready["tenantId"]),
                "KOKORO_STORAGE_QUALIFY_SUBJECT_ID": str(ready["subjectId"]),
                "KOKORO_STORAGE_QUALIFY_CASE_ID": env["QUALIFY_CASE_ID"],
                "KOKORO_STORAGE_QUALIFY_SOCKET": env["QUALIFY_SOCKET"],
                "KOKORO_STORAGE_QUALIFY_TOKEN": env["QUALIFY_TOKEN"],
            }
            subprocess.run(
                [
                    node,
                    str(platform / "node_modules/vitest/vitest.mjs"),
                    "run",
                    "test/smoke/local-skill-import-storage.e2e.test.ts",
                    "--no-file-parallelism",
                ],
                cwd=platform,
                env=test_env,
                check=True,
            )
        except BaseException as error:
            test_error = error
        finally:
            Path(env["QUALIFY_DONE"]).write_text(
                json.dumps({"success": test_error is None}) + "\n"
            )
            try:
                process.wait(timeout=120)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                if test_error is None:
                    test_error = QualificationError("Storage harness cleanup timeout")
            if process.returncode != 0 and test_error is None:
                test_error = QualificationError("Storage harness failed; inspect private log")
            if test_error is not None:
                update_failure_manifest(
                    Path(env["QUALIFY_MANIFEST"]), test_error, log_path
                )
        if test_error is not None:
            raise test_error
        succeeded = True
    finally:
        if succeeded:
            shutil.rmtree(directory)
            shutil.rmtree(harness_directory)
        else:
            print(
                json.dumps(
                    {
                        "status": "failed-preserved",
                        "case": case,
                        "evidence_directory": str(directory),
                        "harness_directory": str(harness_directory),
                    }
                )
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", type=Path, default=DEFAULT_PLATFORM)
    parser.add_argument("--storage", type=Path, default=DEFAULT_STORAGE)
    parser.add_argument("--runtime-config", type=Path, default=DEFAULT_RUNTIME_CONFIG)
    parser.add_argument(
        "--node", default="/opt/homebrew/Cellar/node@24/24.20.0/bin/node"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    node24(args.node)
    for path in (args.platform, args.storage):
        if not path.is_dir():
            raise QualificationError(f"owner checkout missing: {path}")
    document = json.loads(args.runtime_config.read_text())
    storage_config = document.get("storage") if isinstance(document, dict) else None
    if not isinstance(storage_config, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in storage_config.items()
    ):
        raise QualificationError("private runtime config has no closed storage object")
    source = harness_source(args.storage.resolve())
    validate_harness_syntax(args.node, args.storage.resolve(), source)
    for key in (
        "KOKORO_POSTGRES_URL",
        "KOKORO_REDIS_URL",
        "KOKORO_OBJECT_STORE_REGION",
        "KOKORO_OBJECT_STORE_ENDPOINT",
        "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT",
        "KOKORO_OBJECT_STORE_ACCESS_KEY_ID",
        "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY",
        "KOKORO_SCANNER_HOST",
        "KOKORO_SCANNER_PORT",
    ):
        required(storage_config, key)
    validate_harness_load(args.node, args.storage.resolve(), storage_config)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry-run-passed",
                    "cases": list(CASES),
                    "ipc": [
                        "bind_scope",
                        "put_version",
                        "prepare_complete",
                        "register_canonical",
                    ],
                    "resources_started": 0,
                }
            )
        )
        return 0
    for case in CASES:
        run_case(
            args.platform.resolve(),
            args.storage.resolve(),
            args.node,
            storage_config,
            case,
        )
    print(json.dumps({"status": "passed", "cases": list(CASES), "owned_resources_remaining": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
