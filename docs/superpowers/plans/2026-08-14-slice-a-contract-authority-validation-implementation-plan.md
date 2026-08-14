# Slice A Contract Authority Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this cut exactly. This cut installs and validates only the reviewed machine authority; it does not render Proto/OpenAPI, modify SQL or touch child repositories.

**Goal:** Create the first executable Root barrier commit: byte-install the reviewed Slice A contract manifest and add a dependency-free fail-closed validator with mutation tests.

**Architecture:** The reviewed `.yaml` is intentionally JSON-compatible YAML, so this cut uses Python 3.11 standard-library `json` and `unittest`; it does not introduce the later Buf/Redocly toolchain. The validator proves declaration/file/consumer closure, HTTP locations/errors, Agent event inventory and mature Web SSE/control invariants before a renderer is allowed to consume the file.

**Commit:** `feat(contract): install Slice A machine authority`

- [ ] **Task 1: Install the reviewed bytes and observe RED**

**Files:**
- Create: `contract/slice-a-contract-manifest.yaml`
- Create: `contract/tests/test_slice_a_manifest_authority.py`

**Step 1: Install the exact reviewed authority**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
install -m 0644 docs/superpowers/specs/2026-08-14-slice-a-contract-manifest.yaml contract/slice-a-contract-manifest.yaml
cmp docs/superpowers/specs/2026-08-14-slice-a-contract-manifest.yaml contract/slice-a-contract-manifest.yaml
```

**Step 2: Create the test file with this complete content**

```python
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from contract.validate_slice_a_manifest import ManifestError, load_manifest, validate

SPEC = ROOT / "docs/superpowers/specs/2026-08-14-slice-a-contract-manifest.yaml"
INSTALLED = ROOT / "contract/slice-a-contract-manifest.yaml"

class SliceAManifestAuthorityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_manifest(INSTALLED)

    def test_reviewed_authority_is_installed_byte_for_byte(self) -> None:
        self.assertEqual(SPEC.read_bytes(), INSTALLED.read_bytes())
        validate(self.manifest)
        completed=subprocess.run([sys.executable,str(ROOT/'contract/validate_slice_a_manifest.py'),str(INSTALLED)],cwd=ROOT,text=True,capture_output=True,check=True)
        self.assertEqual(completed.stdout,"slice_a_manifest_valid\n")

    def test_duplicate_package_enum_symbol_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        candidate['protobuf']['messages'][0]['name']=candidate['protobuf']['enums'][0]['name']
        with self.assertRaisesRegex(ManifestError,'duplicate package symbol'):
            validate(candidate)

    def test_incomplete_field_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        del candidate['protobuf']['messages'][0]['fields'][0]['label']
        with self.assertRaisesRegex(ManifestError,'incomplete field'):
            validate(candidate)

    def test_missing_path_parameter_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        operation=next(op for op in candidate['http']['operations'] if op['operationId']=='submitMessage')
        operation['parameters']=[p for p in operation['parameters'] if p['name']!='conversation_id']
        with self.assertRaisesRegex(ManifestError,'path parameter drift'):
            validate(candidate)

    def test_web_private_owner_file_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        candidate['consumerFileClosure']['kokoro-web'].append('kokoro/agent/v1/agent_runtime.proto')
        with self.assertRaisesRegex(ManifestError,'consumer closure drift|private owner proto'):
            validate(candidate)

    def test_missing_control_arm_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        del candidate['rules']['controlDecisionPayloadSchemasByKind']['edit']
        with self.assertRaisesRegex(ManifestError,'control decision arms incomplete'):
            validate(candidate)

    def test_browser_run_identity_drift_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        field=next(field for field in candidate['sse']['dataFields'] if field['name']=='run_id')
        field['mapsFrom']='agent_run.agent_run_id'
        with self.assertRaisesRegex(ManifestError,'browser run_id must map launch_id'):
            validate(candidate)

    def test_unresolved_browser_payload_type_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        candidate['sse']['browserEvents'][0]['payload'][0]['type']='unknown-symbol'
        with self.assertRaisesRegex(ManifestError,'unresolved SSE types'):
            validate(candidate)

    def test_streaming_method_flag_drift_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        service=next(service for service in candidate['protobuf']['services'] if service['name']=='ChatQueryService')
        method=next(method for method in service['methods'] if method['name']=='StreamConversationEvents')
        method['serverStreaming']=False
        with self.assertRaisesRegex(ManifestError,'streaming method drift'):
            validate(candidate)

    def test_missing_required_import_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        runtime=next(file for file in candidate['protobuf']['files'] if file['path']=='kokoro/agent/v1/agent_runtime.proto')
        runtime['imports'].remove('kokoro/agent/v1/agent_events.proto')
        with self.assertRaisesRegex(ManifestError,'direct imports drift'):
            validate(candidate)

    def test_incomplete_consumer_closure_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        candidate['consumerFileClosure']['kokoro-agent'].remove('kokoro/model/v1/model_catalog.proto')
        with self.assertRaisesRegex(ManifestError,'consumer closure drift'):
            validate(candidate)

    def test_caller_map_drift_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        candidate['consumerCallerMap']['agent'].remove('ModelCatalogService')
        with self.assertRaisesRegex(ManifestError,'caller map drift'):
            validate(candidate)

    def test_unsafe_http_uint64_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        schema=next(schema for schema in candidate['http']['schemas'] if schema['name']=='DecideInteractionHttpRequest')
        generation=next(prop for prop in schema['properties'] if prop['name']=='expected_generation')
        del generation['maximum']
        with self.assertRaisesRegex(ManifestError,'unsafe HTTP uint64'):
            validate(candidate)

    def test_agent_event_oneof_drift_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        event=next(message for message in candidate['protobuf']['messages'] if message['name']=='AgentEvent')
        next(field for field in event['fields'] if field['number']==39)['type']='.kokoro.agent.v1.RunCompleted'
        with self.assertRaisesRegex(ManifestError,'Agent event oneof drift'):
            validate(candidate)

    def test_projection_consumer_allowlist_drift_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        candidate['rules']['projectionConsumers']['sliceA'].append('unknown')
        with self.assertRaisesRegex(ManifestError,'projection consumer allowlist drift'):
            validate(candidate)

if __name__ == '__main__':
    unittest.main()
```

**Step 3: Run RED**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
python3 -m unittest contract.tests.test_slice_a_manifest_authority -v
```

Expected: import failure for `contract.validate_slice_a_manifest`; no test is skipped.

- [ ] **Task 2: Add the complete dependency-free validator**

**Files:**
- Create: `contract/validate_slice_a_manifest.py`

**Step 1: Create the validator with this complete content**

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCALARS = {"double","float","int32","int64","uint32","uint64","sint32","sint64","fixed32","fixed64","sfixed32","sfixed64","bool","string","bytes"}
LABELS = {"required","optional","repeated"}
GOOGLE_TYPES = {".google.protobuf.Timestamp"}
GOOGLE_IMPORTS = {"google/protobuf/timestamp.proto"}
EXPECTED_AGENT_KINDS = [
    "run.started","thinking.delta","message.delta","message.completed","tool.invoked","tool.output.delta",
    "tool.awaiting_approval","tool.returned","todo.updated","subagent.started","subagent.finished",
    "subagent.thinking.delta","subagent.text.delta","subagent.text.completed","subagent.tool.invoked",
    "subagent.tool.returned","delivery.created","run.control.receipt","run.completed","run.failed",
]

class ManifestError(ValueError):
    pass

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)

def load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"manifest unreadable: {exc}") from exc
    require(isinstance(data, dict), "manifest root must be object")
    return data

def duplicates(values: list[Any]) -> list[Any]:
    return sorted(value for value, count in Counter(values).items() if count > 1)

def validate(manifest: dict[str, Any]) -> None:
    require(manifest.get("artifact") == "slice-a-contract-manifest", "unexpected artifact")
    require(manifest.get("authority") == "machine", "authority must be machine")
    proto = manifest.get("protobuf")
    require(isinstance(proto, dict), "protobuf must be object")
    files = proto.get("files", []); enums = proto.get("enums", []); messages = proto.get("messages", []); services = proto.get("services", [])
    require(len(files) == 9, "expected 9 proto files")
    require(len(services) == 8, "expected 8 services")
    require(sum(len(service.get("methods", [])) for service in services) == 19, "expected 19 methods")

    declarations: dict[tuple[str,str,str], dict[str,Any]] = {}
    package_symbols: dict[str,list[str]] = defaultdict(list)
    known_types = set(GOOGLE_TYPES)
    for kind, group in (("enum",enums),("message",messages),("service",services)):
        for item in group:
            key=(kind,item["package"],item["name"])
            require(key not in declarations, f"duplicate declaration {key}")
            declarations[key]=item
            package_symbols[item["package"]].append(item["name"])
            if kind in {"enum","message"}: known_types.add(f'.{item["package"]}.{item["name"]}')

    for enum in enums:
        values=enum.get("values",[])
        require(values and values[0].get("number") == 0, f"enum {enum['name']} must start at zero")
        names=[value.get("name") for value in values]; numbers=[value.get("number") for value in values]
        prefix=re.sub(r"(?<!^)(?=[A-Z])","_",enum["name"]).upper()+"_"
        require(all(isinstance(name,str) and name.startswith(prefix) for name in names), f"enum value prefix drift in {enum['name']}")
        require(not duplicates(names), f"duplicate enum value name in {enum['name']}")
        require(not duplicates(numbers), f"duplicate enum value number in {enum['name']}")
        package_symbols[enum["package"]].extend(names)
    for package,symbols in package_symbols.items():
        require(not duplicates(symbols), f"duplicate package symbol in {package}: {duplicates(symbols)}")

    for message in messages:
        fields=message.get("fields",[])
        require(not duplicates([field.get("number") for field in fields]), f"duplicate field number in {message['name']}")
        require(not duplicates([field.get("name") for field in fields]), f"duplicate field name in {message['name']}")
        for field in fields:
            require({"number","name","type","label"}.issubset(field), f"incomplete field in {message['name']}")
            require(field["label"] in LABELS, f"invalid field label in {message['name']}.{field['name']}")
            require(field["type"] in SCALARS or field["type"] in known_types, f"unknown protobuf type {field['type']}")
            if "oneof" in field:
                require(field["label"] == "required", f"oneof field must be required: {message['name']}.{field['name']}")

    file_paths=[file.get("path") for file in files]
    require(not duplicates(file_paths), "duplicate proto file path")
    file_by_path={file["path"]:file for file in files}
    declaration_file: dict[str,str] = {}
    assigned=[]
    for file in files:
        for imported in file.get("imports",[]):
            require(imported in file_paths or imported in GOOGLE_IMPORTS, f"unknown import {imported}")
        for declaration in file.get("declarations",[]):
            key=(declaration.get("kind"),file.get("package"),declaration.get("name"))
            require(key in declarations, f"unknown assigned declaration {key}")
            assigned.append(key)
            declaration_file[f".{file['package']}.{declaration['name']}"]=file["path"]
    require(not duplicates(assigned), f"declaration assigned twice: {duplicates(assigned)}")
    require(set(assigned)==set(declarations), f"unassigned declaration: {sorted(set(declarations)-set(assigned))}")

    for file in files:
        required_imports: set[str] = set()
        for declaration in file["declarations"]:
            item=declarations[(declaration["kind"],file["package"],declaration["name"])]
            references=[]
            if declaration["kind"]=="message":
                references=[field["type"] for field in item.get("fields",[]) if field["type"] not in SCALARS]
            elif declaration["kind"]=="service":
                references=[ref for method in item.get("methods",[]) for ref in (method["input"],method["output"])]
            for reference in references:
                if reference in GOOGLE_TYPES:
                    required_imports.add("google/protobuf/timestamp.proto")
                else:
                    target=declaration_file[reference]
                    if target != file["path"]:
                        required_imports.add(target)
        require(set(file.get("imports",[]))==required_imports, f"direct imports drift for {file['path']}")

    for service in services:
        for method in service.get("methods",[]):
            require(set(method) <= {"name","input","output","caller","serverStreaming"}, f"unknown method key for {service['name']}.{method.get('name')}")
            require(method.get("caller") in {"web","chat","agent"}, f"invalid caller for {service['name']}.{method.get('name')}")
            require(method.get("input") in known_types and method.get("output") in known_types, f"unknown method type for {service['name']}.{method.get('name')}")
            require(isinstance(method.get("serverStreaming",False),bool), f"invalid streaming flag for {service['name']}.{method.get('name')}")
            expected_stream = service["name"] == "ChatQueryService" and method.get("name") == "StreamConversationEvents"
            require(method.get("serverStreaming",False) is expected_stream, f"streaming method drift for {service['name']}.{method.get('name')}")

    caller_map=manifest.get("consumerCallerMap",{})
    expected_caller_map: dict[str,list[str]] = defaultdict(list)
    for service in services:
        callers={method["caller"] for method in service.get("methods",[])}
        require(len(callers)==1, f"mixed callers for {service['name']}")
        expected_caller_map[next(iter(callers))].append(service["name"])
    require(set(caller_map)=={"web","chat","agent","public"}, "unexpected caller-map keys")
    for caller in ("web","chat","agent"):
        require(set(caller_map.get(caller,[]))==set(expected_caller_map[caller]), f"caller map drift for {caller}")
    require(caller_map.get("public")==["GET /.well-known/jwks.json"], "public caller map drift")

    closures=manifest.get("consumerFileClosure",{})
    require(set(closures)=={"kokoro-site","kokoro-iam","kokoro-model","kokoro-capability","kokoro-chat","kokoro-agent","kokoro-web","root-e2e"}, "unexpected consumer set")
    owner_packages={
        "kokoro-site":"kokoro.site.v1", "kokoro-iam":"kokoro.iam.v1", "kokoro-model":"kokoro.model.v1",
        "kokoro-capability":"kokoro.capability.v1", "kokoro-chat":"kokoro.chat.v1", "kokoro-agent":"kokoro.agent.v1",
    }
    consumer_caller={"kokoro-chat":"chat","kokoro-agent":"agent","kokoro-web":"web","root-e2e":"web"}
    common_path="kokoro/common/v1/common.proto"
    for consumer,closure in closures.items():
        require(not duplicates(closure), f"duplicate file in {consumer} closure")
        require(set(closure)<=set(file_paths), f"unknown file in {consumer} closure")
        seeds={common_path}
        owner_package=owner_packages.get(consumer)
        if owner_package:
            seeds.update(file["path"] for file in files if file["package"]==owner_package)
        caller=consumer_caller.get(consumer)
        if caller:
            for service_name in caller_map[caller]:
                seeds.add(declaration_file[next(name for name in declaration_file if name.endswith(f".{service_name}"))])
        expected=set(seeds); pending=list(seeds)
        while pending:
            current=pending.pop()
            for imported in file_by_path[current].get("imports",[]):
                if imported in GOOGLE_IMPORTS or imported in expected:
                    continue
                expected.add(imported); pending.append(imported)
        require(set(closure)==expected, f"consumer closure drift for {consumer}")
    forbidden=("kokoro/agent/","kokoro/model/","kokoro/capability/")
    for consumer in ("kokoro-web","root-e2e"):
        require(not any(path.startswith(forbidden) for path in closures[consumer]), f"private owner proto in {consumer}")

    events=manifest.get("agentEvents",{}).get("variants",[])
    require(len(events)==20, "expected 20 Agent event variants")
    require([event.get("fieldNumber") for event in events]==list(range(20,40)), "Agent event field numbers must be 20..39")
    agent_event=next(message for message in messages if message["package"]=="kokoro.agent.v1" and message["name"]=="AgentEvent")
    event_fields=[field for field in agent_event["fields"] if field.get("oneof")=="payload"]
    require(
        [(event["fieldNumber"],event["fieldName"],event["message"]) for event in events]
        == [(field["number"],field["name"],field["type"]) for field in event_fields],
        "Agent event oneof drift",
    )
    require([event["internalKind"] for event in events]==EXPECTED_AGENT_KINDS, "Agent event kind drift")

    http=manifest.get("http",{}); operations=http.get("operations",[])
    require(len(operations)==10, "expected 10 HTTP operations")
    require(not duplicates([op.get("operationId") for op in operations]), "duplicate operationId")
    for op in operations:
        parameters=op.get("parameters",[])
        for parameter in parameters:
            require(parameter.get("in") in {"path","query","header","cookie"}, f"invalid parameter location in {op['operationId']}")
            require(isinstance(parameter.get("required"),bool) and isinstance(parameter.get("schema"),dict), f"incomplete parameter in {op['operationId']}")
        path_names=set(re.findall(r"{([^}]+)}",op.get("path","")))
        declared={parameter["name"] for parameter in parameters if parameter["in"]=="path" and parameter["required"]}
        require(path_names==declared, f"path parameter drift in {op['operationId']}")
        require(isinstance(op.get("errorStatuses"), list) and all(isinstance(x,int) for x in op["errorStatuses"]), f"invalid error statuses in {op['operationId']}")
    uint64_request_names={field["name"] for message in messages if message["name"].endswith("Request") for field in message.get("fields",[]) if field["type"]=="uint64"}
    safe_max=9007199254740991
    for schema in http.get("schemas",[]):
        for prop in schema.get("properties",[]):
            if prop.get("name") in uint64_request_names and prop.get("type")=="integer":
                require(prop.get("minimum")==0 and prop.get("maximum")==safe_max, f"unsafe HTTP uint64 in {schema['name']}.{prop['name']}")
    for op in operations:
        for parameter in op.get("parameters",[]):
            schema=parameter.get("schema",{})
            if parameter.get("name") in uint64_request_names and schema.get("type")=="integer":
                require(schema.get("minimum")==0 and schema.get("maximum")==safe_max, f"unsafe HTTP uint64 in {op['operationId']}.{parameter['name']}")
    error_body=http.get("errorBody",{})
    require(error_body.get("type")=="object" and error_body.get("additionalProperties") is False, "error body must be strict object")
    error_enum=next(enum for enum in enums if enum["name"]=="ErrorCode")
    codes={value["name"].lower().removeprefix("error_code_") for value in error_enum["values"] if value["number"]}
    require(set(http.get("errorStatusByCode",{}))==codes, "ErrorCode HTTP status map incomplete")

    submit=next(message for message in messages if message["name"]=="SubmitMessageRequest")
    submit_names={field["name"] for field in submit["fields"]}
    require(not ({"message_id","expected_conversation_generation"}&submit_names), "SubmitMessage contains client identity/generation")
    run_view=next(message for message in messages if message["package"]=="kokoro.chat.v1" and message["name"]=="RunView")
    require(run_view["fields"][0]=={"number":1,"name":"launch_id","type":"string","label":"required"}, "RunView launch identity drift")
    require(run_view["fields"][1]=={"number":2,"name":"agent_run_id","type":"string","label":"optional"}, "RunView pre-admission identity drift")
    agent_messages=[message for message in messages if message["package"]=="kokoro.agent.v1"]
    for message in agent_messages:
        tenant={field["name"] for field in message["fields"]}&{"site_id","organization_id"}
        require(not tenant or message["name"]=="LaunchRunRequest", f"tenant axis leaked into {message['name']}")

    sse=manifest.get("sse",{})
    require(len(sse.get("browserEvents",[]))==21, "expected 21 browser event kinds")
    require([field["name"] for field in sse.get("dataFields",[])]==["event_id","seq","session_id","run_id","timestamp","kind","payload"], "browser SSE envelope drift")
    run_id=next(field for field in sse["dataFields"] if field["name"]=="run_id")
    require(run_id.get("mapsFrom")=="chat_run_launch.launch_id", "browser run_id must map launch_id")
    awaiting=next(event for event in sse["browserEvents"] if event["kind"]=="tool.awaiting_approval")
    awaiting_names={field["name"] for field in awaiting["payload"] if field.get("required")}
    require({"interaction_id","interaction_generation"}<=awaiting_names, "HITL browser identity incomplete")
    rules=manifest.get("rules",{})
    require("globally monotonic" in rules.get("agentEventSequence","") and "never resets seq" in rules.get("agentEventSequence",""), "Agent event cursor semantics missing")
    require(rules.get("projectionConsumers",{}).get("sliceA")==["chat"], "projection consumer allowlist drift")
    arms=rules.get("controlDecisionPayloadSchemasByKind",{})
    require(set(arms)=={"approve","edit","reject","respond","submit"}, "control decision arms incomplete")
    require(all(arm.get("additionalProperties") is False for arm in arms.values()), "control decision arm must be strict")
    require("HMAC-SHA256" in rules.get("magicLinkNonceDerivation",""), "magic-link nonce derivation missing")
    access_jwt=rules.get("accessJwt",{})
    require(access_jwt.get("header")=={"alg":"RS256","typ":"JWT","kid":"nonempty active JWKS key id"}, "access JWT header drift")
    require(set(access_jwt.get("claims",{}))=={"iss","aud","sub","site_id","organization_id","auth_session_id","iat","exp"}, "access JWT claims drift")
    require(access_jwt.get("claims",{}).get("iss")=="kokoro-iam" and access_jwt.get("claims",{}).get("aud")=="kokoro-user-backend", "access JWT issuer/audience drift")
    require(access_jwt.get("nbf")=="absent" and access_jwt.get("maxTtlSeconds")==900, "access JWT lifetime drift")
    require("exp + 30-second" in rules.get("streamAuthorizationExpiry",""), "stream authorization deadline missing")
    require(rules.get("sessionCookiePolicy",{}).get("maxAgeSeconds")==2592000, "session cookie cap drift")
    require(rules.get("paginationDefaults",{}).get("listConversationsLimit")==50, "list conversation default drift")
    require("Array.from(content).slice(0, 80)" in rules.get("firstConversationTitle",{}).get("algorithm",""), "first conversation title rule missing")
    materialization=rules.get("snapshotMaterialization",{})
    require(set(materialization)-{"retentionRule"}=={event["kind"] for event in sse["browserEvents"]}, "snapshot materialization map incomplete")
    require("Unknown or not-yet-materialized" in materialization.get("retentionRule",""), "retention safety rule missing")
    definitions=sse.get("typeDefinitions",{})
    primitives={"string","boolean","json-object","safe-nonnegative-integer"}
    unresolved={(event["kind"],field["type"]) for event in sse["browserEvents"] for field in event["payload"] if field["type"] not in primitives and field["type"] not in definitions}
    require(not unresolved, f"unresolved SSE types: {sorted(unresolved)}")
    mapping=sse.get("projectionMappings",{})
    require(mapping.get("interactionKind",{}).get("INTERACTION_KIND_APPROVAL")=="tool_approval", "approval projection drift")
    require(mapping.get("subagentSource",{}).get("SUBAGENT_SOURCE_BUILT_IN")=="built-in", "subagent source projection drift")

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('manifest',type=Path)
    args=parser.parse_args()
    validate(load_manifest(args.manifest))
    print('slice_a_manifest_valid')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
```

**Step 2: Run GREEN twice, once as library tests and once as CLI**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
python3 -m unittest contract.tests.test_slice_a_manifest_authority -v
python3 contract/validate_slice_a_manifest.py contract/slice-a-contract-manifest.yaml | grep -Fx slice_a_manifest_valid
```

Expected: fifteen tests pass and CLI prints exactly `slice_a_manifest_valid`.

- [ ] **Task 3: Document the authority boundary**

**Files:**
- Create: `contract/SLICE_A_AUTHORITY.md`

**Step 1: Create this non-generated authority note**

```markdown
## Slice A machine authority

`slice-a-contract-manifest.yaml` is a byte-for-byte installed copy of the reviewed Root design authority. Run:

    python3 contract/validate_slice_a_manifest.py contract/slice-a-contract-manifest.yaml

before rendering or generation. The validator is dependency-free and fail-closed. This commit does not yet render Proto/OpenAPI; the next independently reviewed JIT cut does that. Child repositories never edit or copy this file manually.
```

**Step 2: Verify the authority note and installed bytes**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
rg -n 'Slice A machine authority|validate_slice_a_manifest.py' contract/SLICE_A_AUTHORITY.md
cmp docs/superpowers/specs/2026-08-14-slice-a-contract-manifest.yaml contract/slice-a-contract-manifest.yaml
python3 -m unittest contract.tests.test_slice_a_manifest_authority -v
```

Expected: section found, byte comparison succeeds, fifteen tests pass.

- [ ] **Task 4: Freeze, review and commit the exact cut**

**Step 1: Run the complete gate**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
python3 -m unittest contract.tests.test_slice_a_manifest_authority -v
python3 contract/validate_slice_a_manifest.py contract/slice-a-contract-manifest.yaml | grep -Fx slice_a_manifest_valid
python3 -m compileall -q contract/validate_slice_a_manifest.py contract/tests/test_slice_a_manifest_authority.py
git diff --check -- contract/slice-a-contract-manifest.yaml contract/tests/test_slice_a_manifest_authority.py contract/SLICE_A_AUTHORITY.md contract/validate_slice_a_manifest.py
```

Expected: all commands exit zero.

**Step 2: Request independent review before staging**

Reviewer checks the installed bytes, mutation-test coverage, package-scope protobuf collision detection, exact file/declaration ownership, consumer privacy, HTTP parameter locations/error map, magic-link command/nonce rules, Agent 20-event inventory and Web SSE launch-ID/control schemas. Any finding must first gain a failing mutation test.

**Step 3: Stage exactly four paths and commit**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
git add -- \
  contract/slice-a-contract-manifest.yaml \
  contract/tests/test_slice_a_manifest_authority.py \
  contract/SLICE_A_AUTHORITY.md \
  contract/validate_slice_a_manifest.py
test "$(git diff --cached --name-only | wc -l | tr -d ' ')" = 4
git diff --cached --check
git commit -m "feat(contract): install Slice A machine authority"
test -z "$(git status --short --untracked-files=no)"
```

Expected: one Root commit with exactly four paths. Do not start child generation until the separately reviewed Proto/OpenAPI renderer cut is complete.
