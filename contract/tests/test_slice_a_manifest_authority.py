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

    def test_transitive_consumer_closure_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        candidate['consumerFileClosure']['kokoro-chat'].remove('kokoro/agent/v1/agent_events.proto')
        with self.assertRaisesRegex(ManifestError,'consumer closure drift'):
            validate(candidate)

    def test_root_e2e_missing_authorization_closure_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        authorization='kokoro/iam/v1/authorization.proto'
        if authorization in candidate['consumerFileClosure']['root-e2e']:
            candidate['consumerFileClosure']['root-e2e'].remove(authorization)
        with self.assertRaisesRegex(ManifestError,'root-e2e authorization closure drift'):
            validate(candidate)

    def test_projection_nack_semantics_are_frozen(self) -> None:
        nack = self.manifest["rules"]["projectionNack"]
        self.assertEqual(nack["requestFields"], ["rejected_seq", "rejection_code"])
        self.assertEqual(nack["presence"], "both-absent-positive-or-both-present-nack")
        self.assertEqual(nack["rejectedSeq"], {"minimum": 1, "relation": "projected_seq + 1"})
        self.assertEqual(
            nack["rejectionCode"],
            {"encoding": "UTF-8", "nonblank": True, "maxBytes": 128},
        )
        self.assertEqual(
            nack["zeroWatermarkEpoch"],
            "rejected event epoch when projected_seq == 0 and no positive event exists",
        )
        self.assertEqual(
            nack["responseFields"],
            ["stored_rejected_seq", "stored_rejection_code"],
        )
        self.assertIn("absent/mismatched echo retains quarantine", nack["compatibility"])
        self.assertEqual(
            nack["errorDetail"],
            {
                "requestId": "echo validated nonblank request_id on every error",
                "message": {"maxBytes": 512, "internal": "redacted"},
                "staleFenceCurrentGeneration": "required",
            },
        )

    def test_projection_nack_rule_drift_fails(self) -> None:
        candidate = copy.deepcopy(self.manifest)
        candidate["rules"]["projectionNack"]["rejectionCode"]["maxBytes"] = 129
        with self.assertRaisesRegex(ManifestError, "projection NACK contract drift"):
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

    def test_duplicate_direct_import_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        runtime=next(file for file in candidate['protobuf']['files'] if file['path']=='kokoro/agent/v1/agent_runtime.proto')
        runtime['imports'].append(runtime['imports'][0])
        with self.assertRaisesRegex(ManifestError,'duplicate import'):
            validate(candidate)

    def test_duplicate_caller_map_service_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        candidate['consumerCallerMap']['agent'].append('ModelCatalogService')
        with self.assertRaisesRegex(ManifestError,'duplicate caller-map service'):
            validate(candidate)

    def test_http_uint64_property_type_bypass_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        schema=next(schema for schema in candidate['http']['schemas'] if schema['name']=='DecideInteractionHttpRequest')
        generation=next(prop for prop in schema['properties'] if prop['name']=='expected_generation')
        generation['type']='number'; generation.pop('maximum')
        with self.assertRaisesRegex(ManifestError,'unsafe HTTP uint64'):
            validate(candidate)

    def test_http_uint64_parameter_type_bypass_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        operation=next(op for op in candidate['http']['operations'] if op['operationId']=='streamConversationEvents')
        after_seq=next(parameter for parameter in operation['parameters'] if parameter['name']=='after_seq')
        after_seq['schema']={'type':'string'}
        with self.assertRaisesRegex(ManifestError,'unsafe HTTP uint64'):
            validate(candidate)

    def test_browser_json_uint64_mapping_drift_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        candidate['http']['browserJsonMapping']['uint64']='raw JSON number'
        with self.assertRaisesRegex(ManifestError,'browser JSON mapping drift'):
            validate(candidate)

    def test_access_jwt_contract_drift_fails(self) -> None:
        mutations=(
            lambda jwt: jwt.pop('clockSkewSeconds'),
            lambda jwt: jwt['claims'].__setitem__('sub','unverified subject'),
            lambda jwt: jwt.__setitem__('validation','signature only'),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                candidate=copy.deepcopy(self.manifest)
                mutate(candidate['rules']['accessJwt'])
                with self.assertRaisesRegex(ManifestError,'access JWT contract drift'):
                    validate(candidate)

    def test_stream_authorization_rule_drift_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        candidate['rules']['streamAuthorizationExpiry'] += ' The stream may remain open indefinitely.'
        with self.assertRaisesRegex(ManifestError,'stream authorization deadline drift'):
            validate(candidate)

    def test_snapshot_materialization_value_drift_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        candidate['rules']['snapshotMaterialization']['message.delta']='discard'
        with self.assertRaisesRegex(ManifestError,'snapshot materialization map drift'):
            validate(candidate)

    def test_agent_event_extra_oneof_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        event=next(message for message in candidate['protobuf']['messages'] if message['name']=='AgentEvent')
        event['fields'].append({'number':40,'name':'other','type':'.kokoro.agent.v1.RunFailed','label':'required','oneof':'other'})
        with self.assertRaisesRegex(ManifestError,'AgentEvent field inventory drift|AgentEvent oneof inventory drift'):
            validate(candidate)

    def test_manifest_version_and_status_drift_fail(self) -> None:
        for key,value,message in (('version',2,'unexpected manifest version'),('status','review-candidate','manifest status')):
            with self.subTest(key=key):
                candidate=copy.deepcopy(self.manifest); candidate[key]=value
                with self.assertRaisesRegex(ManifestError,message):
                    validate(candidate)

    def test_error_status_map_value_drift_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        candidate['http']['errorStatusByCode']['permission_denied']=200
        with self.assertRaisesRegex(ManifestError,'ErrorCode HTTP status map drift'):
            validate(candidate)

    def test_operation_error_status_drift_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        operation=next(op for op in candidate['http']['operations'] if op['operationId']=='submitMessage')
        operation['errorStatuses']=[200]
        with self.assertRaisesRegex(ManifestError,'operation error status drift'):
            validate(candidate)

    def test_duplicate_http_parameter_fails(self) -> None:
        candidate=copy.deepcopy(self.manifest)
        operation=next(op for op in candidate['http']['operations'] if op['operationId']=='submitMessage')
        operation['parameters'].append(copy.deepcopy(operation['parameters'][0]))
        with self.assertRaisesRegex(ManifestError,'duplicate parameter'):
            validate(candidate)

    def test_any_unenumerated_reviewed_authority_drift_fails(self) -> None:
        def drop_generation(candidate: dict) -> None:
            schema=next(schema for schema in candidate['http']['schemas'] if schema['name']=='DecideInteractionHttpRequest')
            schema['properties']=[prop for prop in schema['properties'] if prop['name']!='expected_generation']
        def drop_after_seq(candidate: dict) -> None:
            operation=next(op for op in candidate['http']['operations'] if op['operationId']=='streamConversationEvents')
            operation['parameters']=[parameter for parameter in operation['parameters'] if parameter['name']!='after_seq']
        def drift_agent_seq(candidate: dict) -> None:
            event=next(message for message in candidate['protobuf']['messages'] if message['name']=='AgentEvent')
            next(field for field in event['fields'] if field['name']=='seq')['type']='string'
        def rename_rpc(candidate: dict) -> None:
            candidate['protobuf']['services'][0]['methods'][0]['name']='RenamedMethod'
        def swap_rpc_input(candidate: dict) -> None:
            method=candidate['protobuf']['services'][0]['methods'][0]
            method['input']=candidate['protobuf']['services'][1]['methods'][0]['input']
        def drift_http_method(candidate: dict) -> None:
            operation=next(op for op in candidate['http']['operations'] if op['operationId']=='submitMessage')
            operation['method']='GET'
        for mutate in (drop_generation,drop_after_seq,drift_agent_seq,rename_rpc,swap_rpc_input,drift_http_method):
            with self.subTest(mutate=mutate.__name__):
                candidate=copy.deepcopy(self.manifest); mutate(candidate)
                with self.assertRaises(ManifestError):
                    validate(candidate)

if __name__ == '__main__':
    unittest.main()
