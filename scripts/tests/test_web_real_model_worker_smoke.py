"""Fail-closed guards for the real model composition, no infrastructure startup."""

from pathlib import Path
import importlib
import hashlib
import pytest

MODULE = "scripts.e2e.run_web_real_model_worker_smoke"


def module():
    assert Path("scripts/e2e/run_web_real_model_worker_smoke.py").is_file(), (
        "real runner absent"
    )
    return importlib.import_module(MODULE)


def test_real_mode_is_explicit_and_does_not_accept_fixture():
    m = module()
    config = m.RealModelConfig("http://127.0.0.1:11434", "qwen3:8b", "a" * 40)
    assert config.model == "qwen3:8b"
    for endpoint in (
        "http://remote.test",
        "http://127.0.0.1:3310",
        "http://127.0.0.1:11434/v1",
        "http://user:pass@127.0.0.1:11434",
    ):
        with pytest.raises(m.SmokeError):
            m.RealModelConfig(endpoint, "qwen3:8b", "a" * 40)
    for model in ("", "fixture", "smoke-model"):
        with pytest.raises(m.SmokeError):
            m.RealModelConfig("http://127.0.0.1:11434", model, "a" * 40)


def valid_evidence():
    return dict(
        browser="chromium",
        message_post_status=202,
        agui_status=200,
        conversation_id="conv_abc",
        run_id="run_abc",
        artifact_id="artifact-abc",
        asset_id="asset-abc",
        text_marker_visible=True,
        live_delivery=True,
        reload_card_count=1,
        download_sha256="b" * 64,
        member_statuses=[404, 404, 404],
        owner_snapshot_immutable=True,
        completed_reload_content_equal=True,
        assistant_content_sha256="d" * 64,
    )


def valid_run_usage():
    return dict(
        input=7,
        output=3,
        segments=[dict(generation=1, input=7, output=3)],
        completed=dict(input_tokens=7, output_tokens=3),
    )


def valid_agent_facts(index):
    usage = valid_run_usage()
    return dict(
        request_id=f"request-{index}",
        feature_key="chat",
        user_message_id="user_first" if index == 0 else "user_second",
        input_content="fixture first plain" if index == 0 else "fixture second plain",
        durable_counter=5,
        terminal_events=[
            dict(
                kind="run.completed",
                status="published",
                seq=5,
                payload=dict(status="completed", token_usage=usage["completed"]),
            )
        ],
    )


def valid_system_route():
    return dict(
        model_id="00000000-0000-4000-8000-000000000001",
        revision_id="00000000-0000-4000-8000-000000000002",
        provider_id="00000000-0000-4000-8000-000000000003",
        revision=1,
        digest="a" * 64,
        generation="1",
        tenant_generation="1",
        provider_model_name="qwen3:8b",
        transport="litellm",
        gateway_model_name="qwen3:8b",
        label_key="fixture-label",
        feature_key="chat",
    )


def valid_model_call(index, digest, response_bytes=100):
    return dict(
        sequence=index + 1,
        user_sha256=digest,
        model="qwen3:8b",
        completion_id=f"completion-{index}",
        finish_reason="stop",
        done_count=1,
        input_tokens=7,
        output_tokens=3,
        response_bytes=response_bytes,
    )


def test_stage_validation_requires_text_and_artifact_from_one_run():
    m = module()
    evidence = r68_two_turn_browser_report()
    m.validate_browser_evidence(evidence, "b" * 64)
    for key, bad in [
        ("run_id", ""),
        ("message_post_status", 200),
        ("text_marker_visible", False),
        ("live_delivery", False),
        ("reload_card_count", 2),
        ("download_sha256", "c" * 64),
        ("member_statuses", [200, 404, 404]),
        ("owner_snapshot_immutable", False),
        ("completed_reload_content_equal", False),
        ("assistant_content_sha256", ""),
    ]:
        with pytest.raises(m.SmokeError):
            m.validate_browser_evidence({**evidence, key: bad}, "b" * 64)


@pytest.mark.parametrize(
    "field",
    [
        "owner_snapshot_immutable",
        "completed_reload_content_equal",
        "assistant_content_sha256",
    ],
)
def test_model_browser_evidence_rejects_missing_snapshot_proof(field):
    evidence = r68_two_turn_browser_report()
    del evidence[field]
    with pytest.raises(module().SmokeError):
        module().validate_browser_evidence(evidence, "b" * 64)


def test_terminal_chat_snapshot_evidence_has_precise_non_sensitive_failures():
    import json
    import subprocess

    helper = Path("scripts/e2e/chat_snapshot_evidence.mjs").resolve().as_uri()
    source = """
import assert from 'node:assert/strict';
import { terminalChatSnapshot, assertChatSnapshotUnchanged } from HELPER;
const snapshot = {event_watermark:'cursor_1',messages:[
  {message_id:'msg_u',role:'user',status:'completed',content:'prompt',run_id:'run_1'},
  {message_id:'msg_a',role:'assistant',status:'completed',content:'PRIVATE_TEST_BODY',run_id:'run_1'}
]};
const receipts=[{run_id:'run_1',user_message_id:'msg_u',assistant_message_id:'msg_a'}];
const expected=terminalChatSnapshot(snapshot,receipts);
assert.equal(Object.isFrozen(expected),true);
assert.equal(expected.assistant_content_sha256.length,64);
assertChatSnapshotUnchanged(expected,terminalChatSnapshot(structuredClone(snapshot),receipts));
const invalid=[
  [{messages:[]},'CHAT_SNAPSHOT_COUNT'],
  [{messages:[snapshot.messages[1],snapshot.messages[0]]},'CHAT_SNAPSHOT_ORDER'],
  [{messages:[snapshot.messages[0],{...snapshot.messages[1],message_id:null}]},'CHAT_SNAPSHOT_ID'],
  [{messages:[snapshot.messages[0],{...snapshot.messages[1],message_id:'msg_u'}]},'CHAT_SNAPSHOT_ID'],
  [{messages:[snapshot.messages[0],{...snapshot.messages[1],status:'streaming'}]},'CHAT_SNAPSHOT_STATUS'],
  [{messages:[snapshot.messages[0],{...snapshot.messages[1],content:''}]},'CHAT_SNAPSHOT_CONTENT'],
  [{messages:[snapshot.messages[0],{...snapshot.messages[1],run_id:'run_other'}]},'CHAT_SNAPSHOT_RUN']
];
invalid.push([{...snapshot,event_watermark:null},'CHAT_SNAPSHOT_WATERMARK']);
for(const [body,code] of invalid){
 assert.throws(()=>terminalChatSnapshot(body,receipts),e=>e.code===code&&!e.message.includes('PRIVATE_TEST_BODY'));
}
for(const [key,value,code] of [
 ['message_id','other','CHAT_SNAPSHOT_ID_CHANGED'],
 ['content','PRIVATE_TEST_BODY plus text','CHAT_SNAPSHOT_CONTENT_CHANGED']
]){
 const changed=structuredClone(snapshot);changed.messages[1][key]=value;
 const changedReceipts=structuredClone(receipts);
 if(key==='message_id')changedReceipts[0].assistant_message_id=value;
 assert.throws(()=>assertChatSnapshotUnchanged(expected,terminalChatSnapshot(changed,changedReceipts)),
  e=>e.code===code&&!e.message.includes('PRIVATE_TEST_BODY')&&
  e.evidence.before.assistant_content_sha256===expected.assistant_content_sha256);
}
for(const [key,value,code] of [
 ['run_id','run_other','CHAT_SNAPSHOT_RUN_CHANGED'],
 ['role','user','CHAT_SNAPSHOT_ORDER_CHANGED'],
 ['status','streaming','CHAT_SNAPSHOT_STATUS_CHANGED']
]){
 const changed=structuredClone(expected);changed.messages[1][key]=value;
 assert.throws(()=>assertChatSnapshotUnchanged(expected,changed),
  e=>e.code===code&&!JSON.stringify(e.evidence).includes('PRIVATE_TEST_BODY'));
}
const changedWatermark=structuredClone(snapshot);changedWatermark.event_watermark='cursor_2';
assert.throws(()=>assertChatSnapshotUnchanged(expected,terminalChatSnapshot(changedWatermark,receipts)),
 e=>e.code==='CHAT_SNAPSHOT_WATERMARK_CHANGED');
snapshot.messages[1].content='mutated original';
assert.equal(expected.messages[1].content,'PRIVATE_TEST_BODY');
process.stdout.write('snapshot assertions passed\\n');
""".replace("HELPER", json.dumps(helper))
    result = subprocess.run(
        ["node", "--input-type=module", "-e", source],
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "snapshot assertions passed\n"


def test_runner_never_calls_manual_execution_or_fixture_boundary():
    module()
    source = Path("scripts/e2e/run_web_real_model_worker_smoke.py").read_text()
    for forbidden in (
        "_deliver_pending(",
        "claim_dispatch(",
        "journal_tool_started(",
        "RunEmitter",
        "system_model_fixtures(",
    ):
        assert forbidden not in source
    assert '"kokoro-agent-worker"' in source
    assert "real_model_scenario=" in source
    assert "seed_control_plane(" in source


def test_transparent_model_proxy_forwards_real_bytes_and_requires_stream():
    import http.client
    import json
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread

    m = module()
    observed = []
    payload = b'data: {"choices":[{"index":0,"delta":{"content":"real upstream"},"finish_reason":"stop"}],"id":"completion-fixture","model":"qwen3:8b","usage":{"prompt_tokens":7,"completion_tokens":3,"total_tokens":10}}\n\ndata: [DONE]\n\n'

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            observed.append(
                json.loads(self.rfile.read(int(self.headers["content-length"])))
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=upstream.serve_forever, daemon=True)
    thread.start()
    proxy = m.ObservingProxy(
        f"http://127.0.0.1:{upstream.server_port}",
        kind="model",
        token="key",
        tenant="tenant",
        model="qwen3:8b",
        revision="revision",
        timeout=2,
    )
    try:
        connection = http.client.HTTPConnection(
            "127.0.0.1", proxy.server_port, timeout=3
        )
        body = {
            "model": "qwen3:8b",
            "stream": True,
            "stream_options": {"include_usage": True},
            "messages": [{"role": "user", "content": "fixture prompt"}],
        }
        connection.request(
            "POST",
            "/v1/chat/completions",
            json.dumps(body),
            {"authorization": "Bearer key"},
        )
        response = connection.getresponse()
        assert response.status == 200
        assert response.read() == payload
        assert observed == [body]
        assert proxy.requests == proxy.successes == 1
        assert not proxy.errors
        connection.close()
        connection = http.client.HTTPConnection(
            "127.0.0.1", proxy.server_port, timeout=3
        )
        connection.request(
            "POST",
            "/v1/chat/completions",
            json.dumps({**body, "stream": False}),
            {"authorization": "Bearer key"},
        )
        with pytest.raises(http.client.RemoteDisconnected):
            connection.getresponse()
        assert len(observed) == 1
        assert proxy.errors == ["upstream_observation_failed"]
        connection.close()
    finally:
        proxy.close()
        upstream.shutdown()
        upstream.server_close()
        thread.join(timeout=3)


def test_system_proxy_rejects_wrong_tenant_without_network():
    import http.client
    import json

    m = module()
    proxy = m.ObservingProxy(
        "http://127.0.0.1:1",
        kind="system",
        token="key",
        tenant="tenant",
        model="qwen3:8b",
        revision="revision",
        timeout=1,
    )
    try:
        connection = http.client.HTTPConnection(
            "127.0.0.1", proxy.server_port, timeout=3
        )
        connection.request(
            "POST",
            "/v1/system/model-catalog/resolve",
            json.dumps({"feature_key": "chat"}),
            {
                "authorization": "Bearer key",
                "x-kokoro-tenant-id": "another",
                "x-kokoro-service": "kokoro-agent",
            },
        )
        with pytest.raises(http.client.RemoteDisconnected):
            connection.getresponse()
        assert proxy.requests == 0
        assert proxy.errors == ["upstream_observation_failed"]
        connection.close()
    finally:
        proxy.close()


def test_worker_lease_pid_must_belong_to_registered_process_group(monkeypatch):
    import socket

    m = module()
    monkeypatch.setattr(m.os, "getpgid", lambda pid: 100 if pid == 101 else 200)
    assert m.worker_owns_lease(f"{socket.gethostname()}-101", 100)
    assert not m.worker_owns_lease(f"{socket.gethostname()}-102", 100)
    assert not m.worker_owns_lease("artifact-combo-smoke", 100)


@pytest.mark.parametrize(
    "invalid", [None, {}, {"timeout_ms": 1}, {"web_origin": "https://remote.test"}]
)
def test_browser_rejects_invalid_input_before_launch(invalid):
    import json
    import subprocess

    m = module()
    result = subprocess.run(
        ["node", str(m.DRIVER)],
        input=json.dumps(invalid),
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 1
    assert result.stderr == "REAL_MODEL_FAILURE:input\n"


def test_durable_evidence_requires_worker_owned_write_and_single_delivery(monkeypatch):
    m = module()
    monkeypatch.setattr(
        m, "worker_owns_lease", lambda owner, group: owner == "worker" and group == 42
    )
    row = {
        "terminal": True,
        "generation": 1,
        "owner": "worker",
        "session": "conv_abc",
        "run_count": 2,
        **valid_agent_facts(1),
        "usage": valid_run_usage(),
        "file_writes": 1,
        "deliveries": 1,
        "events": ["run.started", "delivery.created", "run.completed"],
    }
    for change in (
        {},
        {"file_writes": 0},
        {"owner": "artifact-combo-smoke"},
        {"deliveries": 2},
        {"events": ["run.started", "run.completed", "delivery.created"]},
    ):
        results = iter(
            [
                {
                    **row,
                    **valid_agent_facts(0),
                    "file_writes": 0,
                    "deliveries": 0,
                    "events": ["run.started", "run.completed"],
                },
                {**row, **change},
                {"count": 1},
            ]
        )
        monkeypatch.setattr(m, "_query", lambda *_: next(results))
        if change:
            with pytest.raises(m.SmokeError, match="lease/journal/terminal"):
                m.durable_evidence(
                    None,
                    "owned-db",
                    r68_two_turn_browser_report(),
                    "tenant",
                    42,
                    "b" * 64,
                )
        else:
            assert m.durable_evidence(
                None, "owned-db", r68_two_turn_browser_report(), "tenant", 42, "b" * 64
            )["storage"] == {"count": 1}


def test_durable_evidence_accepts_owner_resource_ids_but_rejects_sql_input(monkeypatch):
    m = module()
    monkeypatch.setattr(m, "worker_owns_lease", lambda *_: True)
    row = {
        "terminal": True,
        "generation": 1,
        "owner": "worker",
        "session": "conv_abc",
        "run_count": 2,
        **valid_agent_facts(1),
        "usage": valid_run_usage(),
        "file_writes": 1,
        "deliveries": 1,
        "events": ["run.started", "delivery.created", "run.completed"],
    }
    evidence = {
        **r68_two_turn_browser_report(),
        "artifact_id": "artifact:abc123",
        "asset_id": "asset:abc123",
    }
    results = iter(
        [
            {
                **row,
                **valid_agent_facts(0),
                "file_writes": 0,
                "deliveries": 0,
                "events": ["run.started", "run.completed"],
            },
            row,
            {"count": 1},
        ]
    )
    monkeypatch.setattr(m, "_query", lambda *_: next(results))
    assert m.durable_evidence(None, "owned-db", evidence, "tenant", 42, "b" * 64)
    for malicious in ("artifact:' OR true --", "artifact:abc;", "artifact:abc\n"):
        with pytest.raises(m.SmokeError, match="SQL evidence identity rejected"):
            m.durable_evidence(
                None,
                "owned-db",
                {**evidence, "artifact_id": malicious},
                "tenant",
                42,
                "b" * 64,
            )


def test_failed_browser_still_registers_exact_owned_run_for_cleanup(monkeypatch):
    m = module()
    registered = []

    class Ownership:
        def register_run(self, session, run):
            registered.append((session, run))

    monkeypatch.setattr(
        m,
        "_query",
        lambda *_: [{"run": "run_bff_123", "session": "conv_123"}],
    )
    m.register_owned_worker_runs(None, "owned-db", Ownership())
    assert registered == [("conv_123", "run_bff_123")]
    monkeypatch.setattr(m, "_query", lambda *_: [{}, {}])
    with pytest.raises(m.SmokeError, match="inventory drift"):
        m.register_owned_worker_runs(None, "owned-db", Ownership())


def test_harness_registers_system_in_existing_owned_lifecycle():
    source = Path("scripts/e2e/run_web_project_resource_chromium_smoke.py").read_text()
    assert '"owner_db_url": owner_db_url' in source
    assert '"processes": process_list' in source
    assert '"proxies": proxies' in source
    assert '"infra": infra' in source
    assert source.index("for process in reversed(process_list):") < source.index(
        "infra.cleanup()"
    )
    real = Path("scripts/e2e/run_web_real_model_worker_smoke.py").read_text()
    assert (
        'system_db = stack._owner_schema_database_url(c["owner_db_url"], "system")'
        in real
    )
    assert 'c["processes"].append(system_process)' in real
    assert 'c["processes"].append(process)' in real
    assert 'c["processes"].append(browser_process)' in real


def test_terminal_chat_snapshot_accepts_two_completed_turns_from_receipts():
    import json
    import subprocess

    helper = Path("scripts/e2e/chat_snapshot_evidence.mjs").resolve().as_uri()
    source = r"""
import assert from 'node:assert/strict';
import {
  terminalChatSnapshot, assertChatSnapshotUnchanged
} from HELPER;

const receipts = [
  {run_id:'run_1', user_message_id:'msg_u1', assistant_message_id:'msg_a1'},
  {run_id:'run_2', user_message_id:'msg_u2', assistant_message_id:'msg_a2'}
];
const instant = '2026-10-01T12:00:00.000Z';
const messages = receipts.flatMap((receipt, index) => [
  {
    message_id:receipt.user_message_id, role:'user',
    content:`prompt ${index + 1}`, status:'completed',
    created_at:instant, run_id:receipt.run_id
  },
  {
    message_id:receipt.assistant_message_id, role:'assistant',
    content:`complete answer ${index + 1}`, status:'completed',
    created_at:instant, run_id:receipt.run_id
  }
]);
const body = {
  session:{
    session_id:'conv_1', title:'Two turns', owner_id:'subject_1',
    created_at:instant, updated_at:instant
  },
  messages, pending_pauses:[], files:[], deliveries:[],
  deliveries_has_more:false,
  event_watermark:'agui_0123456789abcdef0123456789abcdef'
};

// The same explicit receipt-array interface handles one or multiple turns.
const first = terminalChatSnapshot(
  {...body, messages:messages.slice(0, 2)}, [receipts[0]]
);
assert.equal(first.messages.length, 2);
process.stdout.write('SINGLE_TURN_CONTROL_OK\n');

const history = terminalChatSnapshot(body, receipts);
assert.equal(history.messages.length, 4);
assert.equal(history.run_id, receipts[1].run_id);
assert.deepEqual(
  history.messages.map(message => message.message_id),
  receipts.flatMap(receipt => [
    receipt.user_message_id, receipt.assistant_message_id
  ])
);
assert.deepEqual(history.messages.slice(0, 2), first.messages);
assert.deepEqual(
  history.messages.map(message => message.content),
  messages.map(message => message.content)
);
assert.deepEqual(
  history.messages.filter(message => message.role === 'assistant')
    .map(message => message.run_id),
  receipts.map(receipt => receipt.run_id)
);
assertChatSnapshotUnchanged(
  history, terminalChatSnapshot(structuredClone(body), receipts)
);
""".replace("HELPER", json.dumps(helper))

    result = subprocess.run(
        ["node", "--input-type=module", "-e", source],
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert "SINGLE_TURN_CONTROL_OK\n" in result.stdout, result.stderr
    assert result.returncode == 0, result.stderr


def test_terminal_chat_snapshot_rejects_receipt_and_history_identity_drift():
    import json
    import subprocess

    helper = Path("scripts/e2e/chat_snapshot_evidence.mjs").resolve().as_uri()
    source = r"""
import assert from 'node:assert/strict';
import { terminalChatSnapshot, assertChatSnapshotUnchanged } from HELPER;
const receipts=[
  {run_id:'run_1',user_message_id:'u1',assistant_message_id:'a1'},
  {run_id:'run_2',user_message_id:'u2',assistant_message_id:'a2'}
];
const body={event_watermark:'cursor_2',messages:receipts.flatMap((receipt,index)=>[
  {message_id:receipt.user_message_id,role:'user',status:'completed',content:`prompt ${index}`},
  {message_id:receipt.assistant_message_id,role:'assistant',status:'completed',
    content:`PRIVATE_HISTORY_BODY ${index}`,run_id:receipt.run_id}
])};
const expected=terminalChatSnapshot(body,receipts);
assert.equal(Object.isFrozen(expected.messages),true);
assert(expected.messages.every(Object.isFrozen));
assert.equal(expected.message_contents_sha256.length,64);
assert.equal(expected.run_id,'run_2');
function rejects(action,code){
  assert.throws(action,error=>error.code===code&&
    !JSON.stringify({message:error.message,evidence:error.evidence}).includes('PRIVATE_HISTORY_BODY'));
}
for(const invalid of [undefined,null,'run_2',[],[null],[1],[[]],new Array(1),
  [{run_id:'run_1',user_message_id:'u1'}],
  [{run_id:'',user_message_id:'u1',assistant_message_id:'a1'}],
  [{...receipts[0],extra:'PRIVATE_HISTORY_BODY'}]]){
  rejects(()=>terminalChatSnapshot(body,invalid),'CHAT_SNAPSHOT_RECEIPT');
}
const repeatedRun=structuredClone(receipts);repeatedRun[1].run_id='run_1';
rejects(()=>terminalChatSnapshot(body,repeatedRun),'CHAT_SNAPSHOT_RUN');
const repeatedReceiptId=structuredClone(receipts);repeatedReceiptId[1].user_message_id='a1';
rejects(()=>terminalChatSnapshot(body,repeatedReceiptId),'CHAT_SNAPSHOT_ID');
const wrongReceipt=structuredClone(receipts);wrongReceipt[1].assistant_message_id='other';
rejects(()=>terminalChatSnapshot(body,wrongReceipt),'CHAT_SNAPSHOT_ID');
const wrongReceiptRun=structuredClone(receipts);wrongReceiptRun[1].run_id='other-run';
rejects(()=>terminalChatSnapshot(body,wrongReceiptRun),'CHAT_SNAPSHOT_RUN');
rejects(()=>terminalChatSnapshot(body,[receipts[1],receipts[0]]),'CHAT_SNAPSHOT_ID');
const mutations=[
  [value=>{value.messages[2].message_id='u1'},'CHAT_SNAPSHOT_ID'],
  [value=>{[value.messages[0],value.messages[1]]=[value.messages[1],value.messages[0]]},'CHAT_SNAPSHOT_ORDER'],
  [value=>{value.messages=[...value.messages.slice(2),...value.messages.slice(0,2)]},'CHAT_SNAPSHOT_ID'],
  [value=>{value.messages[1].run_id='run_2'},'CHAT_SNAPSHOT_RUN'],
  [value=>{value.messages[3].run_id='run_1'},'CHAT_SNAPSHOT_RUN'],
  [value=>{value.messages[2].run_id='run_1'},'CHAT_SNAPSHOT_RUN'],
  [value=>{value.messages[2].run_id=null},'CHAT_SNAPSHOT_RUN'],
  [value=>{delete value.messages[3].run_id},'CHAT_SNAPSHOT_RUN'],
  [value=>{value.messages.pop()},'CHAT_SNAPSHOT_COUNT'],
  [value=>{value.messages.push({...value.messages[3]})},'CHAT_SNAPSHOT_COUNT'],
  [value=>{value.messages[2].status='streaming'},'CHAT_SNAPSHOT_STATUS'],
  [value=>{value.messages[3].content=''},'CHAT_SNAPSHOT_CONTENT']
];
for(const [mutate,code]of mutations){
  const changed=structuredClone(body);mutate(changed);
  rejects(()=>terminalChatSnapshot(changed,receipts),code);
}
for(const index of [0,1,2,3]){
  const changed=structuredClone(body);changed.messages[index].content+=' changed';
  rejects(()=>assertChatSnapshotUnchanged(expected,terminalChatSnapshot(changed,receipts)),
    'CHAT_SNAPSHOT_CONTENT_CHANGED');
}
for(const mutate of [value=>value.messages.pop(),value=>value.messages.push({...value.messages[0]})]){
  const changed=structuredClone(expected);mutate(changed);
  rejects(()=>assertChatSnapshotUnchanged(expected,changed),'CHAT_SNAPSHOT_COUNT');
}
const changedId=structuredClone(body);changedId.messages[2].message_id='other-user';
const changedReceipts=structuredClone(receipts);changedReceipts[1].user_message_id='other-user';
rejects(()=>assertChatSnapshotUnchanged(expected,terminalChatSnapshot(changedId,changedReceipts)),
  'CHAT_SNAPSHOT_ID_CHANGED');
const changedWatermark=structuredClone(body);changedWatermark.event_watermark='cursor_3';
rejects(()=>assertChatSnapshotUnchanged(expected,terminalChatSnapshot(changedWatermark,receipts)),
  'CHAT_SNAPSHOT_WATERMARK_CHANGED');
body.messages[1].content='changed original';receipts[1].run_id='changed receipt';
assert.equal(expected.messages[1].content,'PRIVATE_HISTORY_BODY 0');
assert.equal(expected.run_id,'run_2');
process.stdout.write('receipt and history guards passed\n');
""".replace("HELPER", json.dumps(helper))

    result = subprocess.run(
        ["node", "--input-type=module", "-e", source],
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "receipt and history guards passed\n"


def test_system_owner_selector_preserves_storage_and_agent_positive_controls():
    from urllib.parse import parse_qs, urlencode, urlsplit

    helper = module().stack._owner_schema_database_url
    database_url = "postgresql://owner@localhost/owned?" + urlencode(
        {
            "sslmode": "require",
            "application_name": "system-consumer-test",
            "schema": "kokoro_bff",
            "options": "-c search_path=public,pg_catalog -c timezone=UTC",
            "search_path": "public",
        }
    )
    source = urlsplit(database_url)
    for schema, selector in (
        ("kokoro_storage", {"schema": ["kokoro_storage"]}),
        ("kokoro_agent", {"options": ["-csearch_path=kokoro_agent"]}),
    ):
        actual = urlsplit(helper(database_url, schema))
        assert (actual.scheme, actual.netloc, actual.path) == (
            source.scheme,
            source.netloc,
            source.path,
        )
        assert parse_qs(actual.query) == {
            "sslmode": ["require"],
            "application_name": ["system-consumer-test"],
            **selector,
        }
    system_url = helper(database_url, "system")
    actual = urlsplit(system_url)
    assert (actual.scheme, actual.netloc, actual.path) == (
        source.scheme,
        source.netloc,
        source.path,
    )
    assert parse_qs(actual.query) == {
        "sslmode": ["require"],
        "application_name": ["system-consumer-test"],
        "schema": ["system"],
    }


def test_real_model_setup_passes_system_selector_to_actual_command_environment(
    monkeypatch, tmp_path
):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from urllib.parse import parse_qs, urlsplit

    m = module()
    database_url = (
        "postgresql://owner@localhost/owned"
        "?sslmode=require&application_name=system-consumer-test"
    )
    captured = []

    class SetupObserved(Exception):
        pass

    def capture_setup(command, **kwargs):
        captured.append((command, dict(kwargs["env"])))
        raise SetupObserved

    monkeypatch.setattr(m.stack, "_verify_source", Mock())
    monkeypatch.setattr(m, "provider_preflight", Mock())
    monkeypatch.setattr(m.stack, "_isolated_owner", Mock(return_value=tmp_path))
    monkeypatch.setattr(m.stack.product.runtime, "free_port", Mock(return_value=4100))
    monkeypatch.setattr(
        m.stack.product.session,
        "node_environment",
        Mock(
            return_value={
                "PGOPTIONS": "-c search_path=public,pg_catalog -c timezone=UTC"
            }
        ),
    )
    monkeypatch.setattr(m.stack, "_run_owner_command", capture_setup)
    processes = []
    agent_env = {"KOKORO_AGENT_DATABASE_URL": database_url}
    config = m.RealModelConfig("http://127.0.0.1:11434", "qwen3:8b", "a" * 40)
    with pytest.raises(SetupObserved):
        m.real_scenario(
            config,
            directory=tmp_path,
            log=Mock(),
            infra=SimpleNamespace(redis_prefix="own:"),
            node24=Path("/node24"),
            node=Path("/node22"),
            owner_db_url=database_url,
            system_redis_url="redis://localhost/0",
            agent_secret="fixture-agent-secret",
            credentials=Mock(),
            processes=processes,
            agent_env=agent_env,
        )
    assert len(captured) == 1
    command, env = captured[0]
    assert command[-1] == "scripts/apply-schema.ts"
    assert processes == []
    assert agent_env == {"KOKORO_AGENT_DATABASE_URL": database_url}
    source, actual = urlsplit(database_url), urlsplit(env["DATABASE_URL"])
    assert (actual.scheme, actual.netloc, actual.path) == (
        source.scheme,
        source.netloc,
        source.path,
    )
    assert parse_qs(actual.query) == {
        "sslmode": ["require"],
        "application_name": ["system-consumer-test"],
        "schema": ["system"],
    }
    assert "PGOPTIONS" not in env


def test_system_owner_smoke_passes_system_selector_to_actual_installer_environment(
    monkeypatch,
):
    from contextlib import nullcontext
    from types import SimpleNamespace
    from unittest.mock import Mock
    from urllib.parse import parse_qs, urlsplit

    smoke = module().system
    database_url = (
        "postgresql://owner@localhost/owned"
        "?sslmode=require&application_name=system-consumer-test"
    )
    resources = SimpleNamespace(
        run_id="a" * 24,
        postgres="postgresql://owner@localhost/postgres",
        redis="redis://localhost/0",
        namespace="own:",
        create_database=Mock(return_value=database_url),
        command=Mock(side_effect=lambda command: "PONG" if "PING" in command else "1"),
        cleanup=Mock(),
    )
    captured = []

    class SetupObserved(Exception):
        pass

    def capture_setup(command, **kwargs):
        captured.append((command, dict(kwargs["env"])))
        raise SetupObserved

    monkeypatch.setattr(smoke, "verify_release_inputs", Mock(return_value={}))
    monkeypatch.setattr(
        smoke,
        "node_environment",
        Mock(
            side_effect=lambda *_args: {
                "PGOPTIONS": "-c search_path=public,pg_catalog -c timezone=UTC"
            }
        ),
    )
    monkeypatch.setattr(smoke, "OwnedResources", Mock(return_value=resources))
    monkeypatch.setattr(smoke, "free_port", Mock(side_effect=[4100, 4200]))
    monkeypatch.setattr(
        smoke,
        "iam_admission_stub",
        Mock(return_value=nullcontext("http://127.0.0.1:4300")),
    )
    monkeypatch.setattr(smoke, "run_owned_command", capture_setup)
    with pytest.raises(SetupObserved):
        smoke.run_smoke(
            SimpleNamespace(
                node24_bin="/node24",
                node22_bin="/node22",
                postgres=resources.postgres,
                redis=resources.redis,
            )
        )
    assert len(captured) == 1
    command, env = captured[0]
    assert command == ["pnpm", "db:apply-schema"]
    assert resources.create_database.call_args_list[0].args == ("system",)
    assert resources.command.call_args_list[0].args[0] == [
        "psql",
        resources.postgres,
        "-X",
        "-Atc",
        "SELECT 1",
    ]
    resources.cleanup.assert_called_once_with()
    source, actual = urlsplit(database_url), urlsplit(env["DATABASE_URL"])
    assert (actual.scheme, actual.netloc, actual.path) == (
        source.scheme,
        source.netloc,
        source.path,
    )
    assert parse_qs(actual.query) == {
        "sslmode": ["require"],
        "application_name": ["system-consumer-test"],
        "schema": ["system"],
    }
    assert "PGOPTIONS" not in env


@pytest.mark.parametrize("count", [0, 1, 2])
def test_r66_failed_journey_registers_every_valid_owned_turn(monkeypatch, count):
    m = module()
    registered = []
    rows = [
        {"session": "conv_two_turns", "run": f"run_bff_turn_{i}"} for i in range(count)
    ]

    class Ownership:
        def register_run(self, session, run):
            registered.append((session, run))

    monkeypatch.setattr(m, "_query", lambda *_: rows)
    m.register_owned_worker_runs(None, "owned-db", Ownership())
    assert registered == [(row["session"], row["run"]) for row in rows]


@pytest.mark.parametrize(
    "rows",
    [
        None,
        {},
        [{"session": " ", "run": "run_bff_turn_0"}],
        [{"session": "conv_two_turns", "run": " "}],
        [{"session": "conv_two_turns", "run": f"run_bff_turn_{i}"} for i in range(3)],
        [
            {"session": "conv_two_turns", "run": "run_bff_turn_0"},
            {"session": "conv_two_turns", "run": "run_bff_turn_0"},
        ],
        [
            {"session": "conv_two_turns", "run": "run_bff_turn_0"},
            {"session": "conv_unrelated", "run": "run_bff_turn_1"},
        ],
        [{"session": "conv_two_turns", "run": ""}],
        [{"session": "", "run": "run_bff_turn_0"}],
        [{"session": "conv_two_turns", "run": 7}],
        [{"session": None, "run": "run_bff_turn_0"}],
        [{"session": "conv_two_turns"}],
        [{"session": "conv_two_turns", "run": "run_bff_turn_0", "extra": True}],
        [
            {"session": "conv_two_turns", "run": "run_bff_turn_0"},
            None,
        ],
    ],
)
def test_r66_failed_journey_rejects_invalid_inventory_before_registration(
    monkeypatch, rows
):
    m = module()
    registered = []

    class Ownership:
        def register_run(self, session, run):
            registered.append((session, run))

    monkeypatch.setattr(m, "_query", lambda *_: rows)
    with pytest.raises(m.SmokeError):
        m.register_owned_worker_runs(None, "owned-db", Ownership())
    assert registered == []


# Preserve the frozen R3 assertions byte-for-byte.
# fmt: off
def r68_two_turn_browser_report():
    evidence = valid_evidence()
    evidence.update(
        login=dict(
            owner=dict(
                subject="fixture-owner", form_status=200, callback_status=303,
                session_status=200, product_cookie="HttpOnly+Secure+Lax",
                consent_status=200, consent_post_count=1, consent_post_status=303,
                consent_decision="agree", native_consent=True, app_status=200,
            ),
            member=dict(
                subject="fixture-member", form_status=200, callback_status=303,
                session_status=200, product_cookie="HttpOnly+Secure+Lax",
                consent_status=200, consent_post_count=1, consent_post_status=303,
                consent_decision="agree", native_consent=True, app_status=200,
            ),
        ),
        run_id="run_second",
        message_post_count=2,
        message_post_statuses=[202, 202],
        completed_message_count=4,
        first_turn_preserved=True,
        turns=[
            dict(
                receipt=dict(run_id="run_first", user_message_id="user_first", assistant_message_id="assistant_first"),
                submitted_content_sha256=hashlib.sha256(b"fixture first plain").hexdigest(),
                snapshot_user_content_sha256=hashlib.sha256(b"fixture first plain").hexdigest(),
                event_assistant_content_sha256="2" * 64,
                snapshot_assistant_content_sha256="2" * 64,
                start_count=1, finish_count=1, error_count=0,
            ),
            dict(
                receipt=dict(run_id="run_second", user_message_id="user_second", assistant_message_id="assistant_second"),
                submitted_content_sha256=hashlib.sha256(b"fixture second plain").hexdigest(),
                snapshot_user_content_sha256=hashlib.sha256(b"fixture second plain").hexdigest(),
                event_assistant_content_sha256="d" * 64,
                snapshot_assistant_content_sha256="d" * 64,
                start_count=1, finish_count=1, error_count=0,
            ),
        ],
        active_reload=dict(
            run_id="run_second", state="active", partial_content_length=7,
            finished_before_reload=False, hydration_watermark="opaque_current_hydration",
            sse_last_event_id="opaque_current_hydration",
            snapshot_plus_tail_sha256="d" * 64,
        ),
    )
    return evidence


def test_r68_browser_report_accepts_complete_two_turn_journey_control():
    module().validate_browser_evidence(r68_two_turn_browser_report(), "b" * 64)


@pytest.mark.parametrize(
    "path,bad",
    [
        (("message_post_count",), 1),
        (("message_post_count",), 3),
        (("message_post_count",), True),
        (("message_post_statuses",), [202, 200]),
        (("message_post_statuses",), [202, 202, 202]),
        (("completed_message_count",), 2),
        (("first_turn_preserved",), False),
        (("turns", 1, "receipt", "run_id"), "run_first"),
        (("turns", 1, "receipt", "user_message_id"), "user_first"),
        (("turns", 1, "receipt", "assistant_message_id"), "assistant_first"),
        (("turns", 0, "receipt", "run_id"), " "),
        (("turns", 0, "snapshot_user_content_sha256"), "9" * 64),
        (("turns", 0, "snapshot_assistant_content_sha256"), "9" * 64),
        (("turns", 1, "event_assistant_content_sha256"), "9" * 64),
        (("turns", 0, "submitted_content_sha256"), "bad_hash"),
        (("turns", 0, "start_count"), 2),
        (("turns", 0, "finish_count"), 0),
        (("turns", 1, "finish_count"), True),
        (("turns", 1, "error_count"), 1),
        (("active_reload", "run_id"), "run_first"),
        (("active_reload", "state"), "completed"),
        (("active_reload", "partial_content_length"), 0),
        (("active_reload", "finished_before_reload"), True),
        (("active_reload", "hydration_watermark"), ""),
        (("active_reload", "sse_last_event_id"), "opaque_old_hydration"),
        (("active_reload", "snapshot_plus_tail_sha256"), "9" * 64),
    ],
)
def test_r68_browser_report_rejects_missing_real_journey_boundaries(path, bad):
    evidence = r68_two_turn_browser_report()
    target = evidence
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = bad
    with pytest.raises(module().SmokeError):
        module().validate_browser_evidence(evidence, "b" * 64)


@pytest.mark.parametrize("field", ["turns", "message_post_count", "active_reload"])
def test_r68_browser_report_rejects_missing_two_turn_proof(field):
    evidence = r68_two_turn_browser_report()
    del evidence[field]
    with pytest.raises(module().SmokeError):
        module().validate_browser_evidence(evidence, "b" * 64)


def test_r68_browser_report_rejects_single_turn_success_as_complete_journey():
    with pytest.raises(module().SmokeError):
        module().validate_browser_evidence(valid_evidence(), "b" * 64)


def r68_closed_report_mutants():
    control = r68_two_turn_browser_report()
    cases = [
        (("turns",), None),
        (("turns",), {}),
        (("turns",), []),
        (("turns",), control["turns"][:1]),
        (("turns",), control["turns"] + [control["turns"][0]]),
        (("turns", 0), {}),
        (("turns", 0), {**control["turns"][0], "extra": True}),
        (("turns", 0, "receipt"), {**control["turns"][0]["receipt"], "extra": True}),
        (("active_reload",), None),
        (("active_reload",), {**control["active_reload"], "extra": True}),
        (("run_id",), "run_first"),
    ]
    for path in [
        ("message_post_count",), ("completed_message_count",),
        ("turns", 0, "start_count"), ("turns", 0, "finish_count"),
        ("turns", 0, "error_count"), ("active_reload", "partial_content_length"),
    ]:
        for invalid in (True, 1.0, "1", None):
            cases.append((path, invalid))
    for key in ("run_id", "user_message_id", "assistant_message_id"):
        for invalid in (None, 7, True, "", " ", "x" * 192):
            cases.append((("turns", 0, "receipt", key), invalid))
    for key in ("hydration_watermark", "sse_last_event_id"):
        for invalid in (None, 7, True, " ", "x" * 4097):
            cases.append((("active_reload", key), invalid))
    for key in (
        "submitted_content_sha256", "snapshot_user_content_sha256",
        "event_assistant_content_sha256", "snapshot_assistant_content_sha256",
    ):
        for invalid in (None, "F" * 64, "a" * 65):
            cases.append((("turns", 0, key), invalid))
    for invalid in (None, "F" * 64, "a" * 65):
        cases.append((("active_reload", "snapshot_plus_tail_sha256"), invalid))
    cases.extend([
        (("message_post_statuses",), [True, 202]),
        (("message_post_statuses",), (202, 202)),
        (("active_reload", "finished_before_reload"), 0),
    ])
    for path, invalid in list(cases):
        if len(path) > 1 and path[:2] == ("turns", 0):
            mirror = ("turns", 1) + path[2:]
            if path == ("turns", 0) and isinstance(invalid, dict) and "extra" in invalid:
                invalid = {**control["turns"][1], "extra": True}
            if path == ("turns", 0, "receipt"):
                invalid = {**control["turns"][1]["receipt"], "extra": True}
            cases.append((mirror, invalid))
    return cases


@pytest.mark.parametrize("path,bad", r68_closed_report_mutants())
def test_r68_browser_report_rejects_nonclosed_or_unbounded_nested_proof(path, bad):
    evidence = r68_two_turn_browser_report()
    target = evidence
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = bad
    with pytest.raises(module().SmokeError):
        module().validate_browser_evidence(evidence, "b" * 64)


@pytest.mark.parametrize(
    "section,key",
    [
        (("turns", index), key)
        for index in (0, 1)
        for key in r68_two_turn_browser_report()["turns"][index]
    ] + [
        (("turns", index, "receipt"), key)
        for index in (0, 1)
        for key in r68_two_turn_browser_report()["turns"][index]["receipt"]
    ] + [
        (("active_reload",), key)
        for key in r68_two_turn_browser_report()["active_reload"]
    ],
)
def test_r68_browser_report_rejects_missing_nested_required_proof(section, key):
    evidence = r68_two_turn_browser_report()
    target = evidence
    for item in section:
        target = target[item]
    del target[key]
    with pytest.raises(module().SmokeError):
        module().validate_browser_evidence(evidence, "b" * 64)
# fmt: on


def test_two_turn_stream_helpers_rebuild_only_real_deduplicated_tail():
    import json
    import subprocess

    helper = Path("scripts/e2e/chat_snapshot_evidence.mjs").resolve().as_uri()
    source = """
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {assertCompletedMessagePrefixUnchanged, uniqueRunFrames, runTextEvidence, hydratedRunText} from HELPER;
const hash = text => createHash('sha256').update(text).digest('hex');
const frame = (id,type,delta) => ({id,event:{type,runId:'run_second',...(delta===undefined?{}:{delta})}});
const start=frame('c1','RUN_STARTED'), text=frame('c2','TEXT_MESSAGE_CONTENT','tail'), finish=frame('c3','RUN_FINISHED');
const whole=[start,text,text,finish];
assert.equal(uniqueRunFrames(whole,'run_second').length,3);
assert.deepEqual(runTextEvidence(whole,'run_second'),{content:'tail',sha256:hash('tail'),start_count:1,finish_count:1,error_count:0});
const receipt={run_id:'run_second',user_message_id:'user_second',assistant_message_id:'assistant_second'};
const hydration={execution_head:{run_id:'run_second',state:'active'},event_watermark:'c0',messages:[
 {message_id:'assistant_second',role:'assistant',run_id:'run_second',status:'streaming',content:'base-'}]};
assert.deepEqual(hydratedRunText(hydration,[text,text,finish],receipt,'c0'),{content:'base-tail',sha256:hash('base-tail')});
const first=[{message_id:'user_first',role:'user',status:'completed',content:'prompt'},
 {message_id:'assistant_first',role:'assistant',run_id:'run_first',status:'completed',content:'first'}];
assertCompletedMessagePrefixUnchanged(first,[...structuredClone(first),...hydration.messages]);
const rejects=(call,code)=>assert.throws(call,error=>error.code===code);
rejects(()=>assertCompletedMessagePrefixUnchanged(first,[{...first[0],content:'changed'},first[1]]),'CHAT_SNAPSHOT_CONTENT_CHANGED');
rejects(()=>assertCompletedMessagePrefixUnchanged(first,first.slice(0,1)),'CHAT_SNAPSHOT_COUNT');
rejects(()=>runTextEvidence([text,finish],'run_second'),'CHAT_STREAM_TERMINAL');
rejects(()=>runTextEvidence([start,text,finish,frame('err','RUN_ERROR')],'run_second'),'CHAT_STREAM_TERMINAL');
rejects(()=>runTextEvidence([start,text,finish,{...text,event:{...text.event,delta:'changed'}}],'run_second'),'CHAT_STREAM_CURSOR_CONFLICT');
rejects(()=>uniqueRunFrames([{...text,id:''}],'run_second'),'CHAT_STREAM_FRAME');
rejects(()=>uniqueRunFrames([{...text,id:'x'.repeat(4097)}],'run_second'),'CHAT_STREAM_FRAME');
rejects(()=>uniqueRunFrames(Array(10001).fill(text),'run_second'),'CHAT_STREAM_BOUND');
rejects(()=>runTextEvidence([start,frame('bad','TEXT_MESSAGE_CONTENT',null),finish],'run_second'),'CHAT_STREAM_TEXT');
rejects(()=>hydratedRunText(hydration,[text,finish],receipt,'stale'),'CHAT_REPLAY_WATERMARK');
rejects(()=>hydratedRunText({...hydration,event_watermark:''},[text,finish],receipt,''),'CHAT_REPLAY_WATERMARK');
rejects(()=>hydratedRunText({...hydration,execution_head:{run_id:'run_first',state:'active'}},[text,finish],receipt,'c0'),'CHAT_REPLAY_ACTIVE');
rejects(()=>hydratedRunText({...hydration,execution_head:{run_id:'run_second',state:'waiting'}},[text,finish],receipt,'c0'),'CHAT_REPLAY_ACTIVE');
for (const change of [{content:''},{status:'completed'},{run_id:'run_first'},{role:'user'},{message_id:'wrong'}]) {
 rejects(()=>hydratedRunText({...hydration,messages:[{...hydration.messages[0],...change}]},[text,finish],receipt,'c0'),'CHAT_REPLAY_PARTIAL');
}
rejects(()=>hydratedRunText(hydration,[frame('c0','TEXT_MESSAGE_CONTENT','duplicate'),text,finish],receipt,'c0'),'CHAT_REPLAY_INCLUSIVE_CURSOR');
rejects(()=>hydratedRunText(hydration,[text],receipt,'c0'),'CHAT_REPLAY_TERMINAL');
rejects(()=>hydratedRunText(hydration,[text,finish,frame('err','RUN_ERROR')],receipt,'c0'),'CHAT_REPLAY_TERMINAL');
rejects(()=>hydratedRunText(hydration,[text,finish,{...text,event:{...text.event,delta:'conflict'}}],receipt,'c0'),'CHAT_STREAM_CURSOR_CONFLICT');
""".replace("HELPER", json.dumps(helper))
    result = subprocess.run(
        ["node", "--input-type=module", "-e", source],
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "change",
    [
        {"terminal": False},
        {"owner": "other-worker"},
        {"generation": True},
        {"generation": 0},
        {"generation": 1.0},
        {"session": "conv_wrong"},
        {"run_count": 1},
        {"run_count": 3},
        {"run_count": 2.0},
        {"events": None},
        {"events": {}},
        {"events": ["run.completed"]},
        {"events": ["run.completed", "run.started"]},
        {"events": ["run.started", "run.completed", "run.failed"]},
        {"events": ["run.started", "run.started", "run.completed"]},
        {"file_writes": 1},
        {"file_writes": False},
        {"deliveries": 1},
    ],
)
def test_both_runs_require_real_worker_terminal_and_text_only_first(
    monkeypatch, change
):
    m = module()
    monkeypatch.setattr(
        m, "worker_owns_lease", lambda owner, group: owner == "worker" and group == 42
    )
    first = dict(
        terminal=True,
        owner="worker",
        generation=1,
        session="conv_abc",
        run_count=2,
        **valid_agent_facts(0),
        usage=valid_run_usage(),
        file_writes=0,
        deliveries=0,
        events=["run.started", "run.completed"],
    )
    monkeypatch.setattr(m, "_query", lambda *_: {**first, **change})
    with pytest.raises(m.SmokeError, match="lease/journal/terminal"):
        m.durable_evidence(
            None, "owned-db", r68_two_turn_browser_report(), "tenant", 42, "b" * 64
        )


@pytest.mark.parametrize(
    "outcome",
    [
        "failure",
        "timeout",
        "malformed",
        "invalid-proof",
        "durable-failure",
        "success",
        "second-no-model",
        "cross-window",
    ],
)
def test_browser_failure_quiesces_all_owned_producers_before_inventory(
    monkeypatch, tmp_path, outcome
):
    import json
    import subprocess
    from types import SimpleNamespace
    from unittest.mock import Mock

    m = module()
    record, processes = [], []
    old = SimpleNamespace(pid=10)
    system_process, worker, browser_process = (
        SimpleNamespace(pid=pid) for pid in (20, 30, 40)
    )
    processes.append(old)
    evidence = r68_two_turn_browser_report()
    marker = "KOKORO_REAL_MODEL_" + "a" * 24
    digest = m.hashlib.sha256(marker.encode()).hexdigest()
    evidence["download_sha256"] = digest
    observations = [
        dict(
            receipt=turn["receipt"],
            system=dict(
                requests=1,
                successes=1,
                response_bytes=50,
                pending=0,
                request_ids=[f"request-{index}"],
                user_sha256=[],
                routes=[valid_system_route()],
            ),
            model=dict(
                requests=1,
                successes=1,
                response_bytes=50,
                pending=0,
                request_ids=[],
                user_sha256=[turn["submitted_content_sha256"]],
                input_tokens=7,
                output_tokens=3,
                calls=[valid_model_call(index, turn["submitted_content_sha256"], 50)],
            ),
        )
        for index, turn in enumerate(evidence["turns"])
    ]
    if outcome == "second-no-model":
        observations[0]["model"]["requests"] = observations[0]["model"]["successes"] = 2
        observations[1]["model"].update(
            requests=0, successes=0, response_bytes=0, user_sha256=[]
        )
    if outcome == "cross-window":
        observations[0]["model"]["pending"] = 1
    evidence["provider_turns"] = observations
    browser_process.returncode = 1 if outcome == "failure" else 0

    def communicate(*_args, **_kwargs):
        if outcome == "timeout":
            raise subprocess.TimeoutExpired("owned-browser", 1)
        if outcome == "malformed":
            return "invalid JSON", ""
        if outcome == "invalid-proof":
            return json.dumps(valid_evidence()), ""
        return json.dumps(
            evidence
        ), "REAL_MODEL_FAILURE:second-partial-active" if outcome == "failure" else ""

    browser_process.communicate = communicate

    def read_observations(*_args):
        output, errors = communicate()
        return output, errors, observations

    monkeypatch.setattr(m, "read_driver_observations", read_observations)
    monkeypatch.setattr(m.stack, "_verify_source", Mock(return_value={}))
    monkeypatch.setattr(m, "provider_preflight", Mock(return_value={}))
    monkeypatch.setattr(m.stack, "_isolated_owner", Mock(return_value=tmp_path))
    monkeypatch.setattr(m.stack.product.runtime, "free_port", Mock(return_value=4100))
    monkeypatch.setattr(
        m.stack.product.session, "node_environment", Mock(return_value={})
    )
    monkeypatch.setattr(m.stack, "_run_owner_command", Mock())
    monkeypatch.setattr(
        m.stack.product.runtime, "start_process", Mock(return_value=system_process)
    )
    monkeypatch.setattr(m.system, "wait_ready", Mock())
    monkeypatch.setattr(
        m.system, "seed_control_plane", Mock(return_value={"revision_id": "revision"})
    )
    monkeypatch.setattr(
        m,
        "ObservingProxy",
        lambda *args, **kwargs: SimpleNamespace(
            origin="http://127.0.0.1:4100",
            errors=[],
            successes=2,
            requests=2,
            response_bytes=100,
        ),
    )
    monkeypatch.setattr(
        m.subprocess, "Popen", Mock(side_effect=[worker, browser_process])
    )

    def durable(*args):
        record.append("durable")
        if outcome == "durable-failure":
            raise m.SmokeError("durable failure")
        return {
            "agents": [
                {"request_id": "request-0", "usage": valid_run_usage()},
                {"request_id": "request-1", "usage": valid_run_usage()},
            ],
            "storage": {"count": 1},
        }

    monkeypatch.setattr(m, "durable_evidence", durable)
    monkeypatch.setattr(
        m.stack.product.runtime,
        "stop_owned_process",
        lambda child: record.append(("stop", child.pid)),
    )

    def inventory(*args):
        record.append(("inventory", [child.pid for child in processes]))

    monkeypatch.setattr(m, "register_owned_worker_runs", inventory)
    context = dict(
        directory=tmp_path,
        log=Mock(),
        infra=SimpleNamespace(redis_prefix="owned:"),
        node24=Path("/node24"),
        node=Path("/node22"),
        owner_db_url="postgresql://owner@localhost/owned",
        system_redis_url="redis://localhost/0",
        agent_secret="fixture",
        credentials=Mock(),
        processes=processes,
        proxies=[],
        agent_env={},
        ready=SimpleNamespace(tenant_id="tenant", email="owner", password="fixture"),
        run_id="a" * 24,
        timeout=20,
        storage_base="http://127.0.0.1:4200",
        object_origin="http://127.0.0.1:4300",
        origin="https://web-" + "a" * 24 + ".example.test",
        screenshot=tmp_path / "screen.png",
        certificate=tmp_path / "web.crt",
        member=SimpleNamespace(email="member", password="fixture"),
        agent_db_url="owned-db",
        agent_redis=Mock(),
    )
    config = m.RealModelConfig("http://127.0.0.1:11434", "qwen3:8b", "a" * 40)
    if outcome == "success":
        result = m.real_scenario(config, **context)
        assert result["system_requests"] == 2
        assert record == ["durable", ("inventory", [10, 20, 30, 40])]
    else:
        with pytest.raises(m.SmokeError):
            m.real_scenario(config, **context)
        assert record[-5:] == [
            ("stop", 40),
            ("stop", 30),
            ("stop", 20),
            ("stop", 10),
            ("inventory", []),
        ]
        assert processes == []


def test_actual_driver_clone_observer_tags_hydration_and_preserves_bytes_across_documents():
    import subprocess

    driver = Path("scripts/e2e/web_real_model_worker_chromium.mjs").read_text()
    start = driver.index("  await page.addInitScript(() => {")
    end = driver.index("\n  })\n  const deadline", start)
    observer = (
        "(" + driver[start:end].removeprefix("  await page.addInitScript(") + "\n})()"
    )
    source = """
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
const crypto=webcrypto, location={href:'https://local.test/app',origin:'https://local.test'};
const target='/api/session/sessions/conv_abc', events=target+'/events';
const observed=[], upstreamRequests=[];
const snapshot={event_watermark:'cursor_base',execution_head:{run_id:'run_second',state:'active'},messages:[]};
const wire='id: cursor_tail\\ndata: '+JSON.stringify({type:'TEXT_MESSAGE_CONTENT',runId:'run_second',delta:'tail'})+'\\n\\n'+
 'id: cursor_finish\\ndata: '+JSON.stringify({type:'RUN_FINISHED',runId:'run_second'})+'\\n\\n';
let window;
const fetch=(...args)=>window.fetch(...args);
function createDocument() {
 window={localStorage:{setItem(){}},__rootEvidence:async record=>{observed.push(record)},
  fetch:async(request,options)=>{
    const url=request instanceof Request?request.url:new URL(String(request),location.href).href;
    upstreamRequests.push({url,headers:new Headers(options?.headers??(request instanceof Request?request.headers:undefined))});
    return new Response(url.endsWith('/events')?wire:JSON.stringify(snapshot),{status:200});
  }};
 OBSERVER;
}
const settle=async()=>{for(let i=0;i<12;i++) await new Promise(resolve=>setTimeout(resolve,0));};
createDocument();
assert.deepEqual(await (await window.fetch(target)).json(),snapshot);
assert.deepEqual(await window.__rootProbeSnapshot(target),{status:200,body:snapshot});
const ui=await window.fetch(new Request(new URL(events,location.href),{headers:{'Last-Event-ID':'cursor_base'}}));
assert.equal(await ui.text(),wire);
await settle();
const firstDocument=observed.find(record=>record.kind==='document').document;
assert.equal(observed.filter(record=>record.kind==='snapshot-start').length,1); // probe is not UI hydration
const hydration=observed.find(record=>record.kind==='snapshot');
const stream=observed.find(record=>record.kind==='stream');
assert.equal(stream.tag,'ui');
assert.equal(stream.lastEventId,hydration.body.event_watermark);
assert.ok(hydration.responseSequence<stream.requestSequence);
assert.equal(observed.filter(record=>record.kind==='frame').length,2);
createDocument(); // earlier observation remains outside the reloaded window
assert.deepEqual(await (await window.fetch(target)).json(),snapshot);
const reloaded=await window.fetch(events,{headers:{'Last-Event-ID':'cursor_base'}});
assert.equal(await reloaded.text(),wire);
await window.__rootAuditReplay({target:events,cursor:'cursor_base'});
await settle();
const documents=observed.filter(record=>record.kind==='document');
assert.equal(documents.length,2);
assert.notEqual(documents[1].document,firstDocument);
assert.equal(observed.filter(record=>record.kind==='frame'&&record.document===firstDocument).length,2);
assert.equal(observed.filter(record=>record.kind==='frame').length,6);
const audit=observed.find(record=>record.kind==='stream'&&record.tag==='audit');
assert.ok(audit);
assert.equal(audit.lastEventId,'cursor_base');
assert.ok(observed.some(record=>record.kind==='end'&&record.streamId===audit.streamId));
assert.equal(observed.filter(record=>record.kind==='snapshot-start').length,2);
assert.equal(observed.filter(record=>record.kind==='error').length,0);
assert.equal(upstreamRequests.filter(request=>request.url.endsWith('/events')).length,3);
""".replace("OBSERVER", observer)
    result = subprocess.run(
        ["node", "--input-type=module", "-e", source],
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "page.exposeBinding" in driver
    assert "posts.length===2" in driver
    assert "firstSnapshot.event_watermark" in driver
    assert "terminalChatSnapshot(snapshot.body,receipts)" in driver


@pytest.mark.parametrize(
    "storage",
    [
        None,
        {},
        {"count": 0},
        {"count": 2},
        {"count": True},
        {"count": 1.0},
        {"count": 1, "extra": True},
    ],
)
def test_two_turn_storage_keeps_final_clean_exact_digest_guard(monkeypatch, storage):
    m = module()
    monkeypatch.setattr(m, "worker_owns_lease", lambda *_: True)
    first = dict(
        terminal=True,
        generation=1,
        owner="worker",
        session="conv_abc",
        run_count=2,
        **valid_agent_facts(0),
        usage=valid_run_usage(),
        file_writes=0,
        deliveries=0,
        events=["run.started", "run.completed"],
    )
    second = {
        **first,
        **valid_agent_facts(1),
        "file_writes": 1,
        "deliveries": 1,
        "events": ["run.started", "delivery.created", "run.completed"],
    }
    results = iter([first, second, storage])
    queries = []

    def query(_infra, _database_url, sql):
        queries.append(sql)
        return next(results)

    monkeypatch.setattr(m, "_query", query)
    with pytest.raises(m.SmokeError, match="Storage FINAL CLEAN digest"):
        m.durable_evidence(
            None, "owned-db", r68_two_turn_browser_report(), "tenant", 42, "b" * 64
        )
    assert "source_run_id='run_second'" in queries[-1]
    assert "a.state='final'" in queries[-1]
    assert "s.scan_state='clean'" in queries[-1]
    assert "a.finalized_sha256='" + "b" * 64 + "'" in queries[-1]
    assert "WHERE run_id='run_first'" in queries[0]
    assert "WHERE run_id='run_second'" in queries[1]


def test_fresh_fixture_login_requires_real_native_first_consent_before_callback_and_app():
    import subprocess

    driver = Path("scripts/e2e/web_real_model_worker_chromium.mjs").read_text()
    start = driver.index("  async function login(")
    end = driver.index('\n  phase = "owner-login"', start)
    login = driver[start:end]
    source = """
import assertNative from 'node:assert/strict';
const assert=(ok,label)=>{if(!ok)throw new Error(label)}, input={web_origin:'https://local.test',timeout_ms:20000};
LOGIN;
const targetFor = mode => {
 const listeners=[], actions=[];
 let pathname='/auth/sign-in';
 const response=(path,method,status,postData='')=>({url:()=>input.web_origin+path,status:()=>status,request:()=>({
  method:()=>method,isNavigationRequest:()=>true,resourceType:()=>mode==='non-native'?'fetch':'document',
  headers:()=>({'content-type':'application/x-www-form-urlencoded'}),postData:()=>postData})});
 const emit=(...args)=>listeners.forEach(listener=>listener(response(...args)));
 return {actions,
  on:(event,listener)=>{assertNative.equal(event,'response');listeners.push(listener)},
  goto:async()=>({status:()=>200}),url:()=>input.web_origin+pathname,
  locator:selector=>({fill:async()=>actions.push(selector)}),
  getByRole:(role,{name})=>({waitFor:async()=>{},click:async()=>{
   actions.push(name);
   if(name==='登录') {
    if(mode==='direct-app') {pathname='/app';emit('/api/auth/callback/kokoro-iam','GET',303);emit('/app','GET',200)}
    else {pathname='/iam/interactions/consent';emit(pathname,'GET',mode==='bad-page'?403:200)}
   } else if(name==='Agree and continue') {
    const form=mode==='decline'?'csrf_token=fixture&decision=decline':mode==='missing-csrf'?'decision=agree':'csrf_token=fixture&decision=agree';
    emit(pathname,'POST',mode==='failed-post'?403:303,form);
    if(mode==='duplicate')emit(pathname,'POST',303,form);
    emit('/api/auth/callback/kokoro-iam','GET',mode==='bad-callback'?302:303);
    pathname='/app';emit(pathname,'GET',200);
   }
  }}),
  waitForURL:async predicate=>{assertNative.ok(predicate(new URL(input.web_origin+pathname)))},
  evaluate:async()=>({status:200,body:{authenticated:true,subject:'fixture-owner'}}),
  context:()=>({cookies:async()=>[{name:'kokoro_product_session',httpOnly:true,secure:true,sameSite:'Lax'}]})
 };
};
const good=targetFor('good');
const proof=await login(good,'fixture-owner','fixture-password');
assertNative.equal(proof.consent_status,200);
assertNative.equal(proof.consent_post_count,1);
assertNative.equal(proof.consent_post_status,303);
assertNative.equal(proof.consent_decision,'agree');
assertNative.equal(proof.native_consent,true);
assertNative.equal(proof.callback_status,303);
assertNative.equal(proof.app_status,200);
assertNative.deepEqual(good.actions.slice(-2),['登录','Agree and continue']);
for (const mode of ['direct-app','bad-page','decline','missing-csrf','failed-post','duplicate','non-native','bad-callback']) {
 await assertNative.rejects(login(targetFor(mode),'fixture-owner','fixture-password'));
}
""".replace("LOGIN", login)
    result = subprocess.run(
        ["node", "--input-type=module", "-e", source],
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "change",
    [
        None,
        {"consent_status": 403},
        {"consent_post_count": 0},
        {"consent_post_count": True},
        {"consent_post_status": 200},
        {"consent_decision": "decline"},
        {"native_consent": False},
        {"app_status": 302},
        {"extra": True},
    ],
)
def test_real_login_report_preserves_native_first_consent_and_cookie_proof(change):
    evidence = r68_two_turn_browser_report()
    if change is None:
        module().validate_browser_evidence(evidence, "b" * 64)
    else:
        evidence["login"]["owner"].update(change)
        with pytest.raises(module().SmokeError, match="first-login"):
            module().validate_browser_evidence(evidence, "b" * 64)


def test_real_login_report_rejects_missing_first_consent_fields_and_same_actor():
    actor = r68_two_turn_browser_report()["login"]["owner"]
    for field in actor:
        evidence = r68_two_turn_browser_report()
        del evidence["login"]["owner"][field]
        with pytest.raises(module().SmokeError, match="first-login"):
            module().validate_browser_evidence(evidence, "b" * 64)
    evidence = r68_two_turn_browser_report()
    evidence["login"]["member"]["subject"] = evidence["login"]["owner"]["subject"]
    with pytest.raises(module().SmokeError, match="identity drift"):
        module().validate_browser_evidence(evidence, "b" * 64)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "none",
        "empty",
        "partial-owner",
        "partial-member",
        "same-actor",
        "non-dict",
        "extra",
    ],
)
def test_r71_p1_complete_journey_always_requires_closed_distinct_first_login(mutation):
    evidence = r68_two_turn_browser_report()
    module().validate_browser_evidence(evidence, "b" * 64)
    if mutation == "missing":
        del evidence["login"]
    elif mutation == "none":
        evidence["login"] = None
    elif mutation == "empty":
        evidence["login"] = {}
    elif mutation == "partial-owner":
        del evidence["login"]["owner"]
    elif mutation == "partial-member":
        del evidence["login"]["member"]
    elif mutation == "same-actor":
        evidence["login"]["member"]["subject"] = evidence["login"]["owner"]["subject"]
    elif mutation == "non-dict":
        evidence["login"] = []
    elif mutation == "extra":
        evidence["login"]["fallback"] = True
    with pytest.raises(module().SmokeError, match="first-login"):
        module().validate_browser_evidence(evidence, "b" * 64)


@pytest.mark.parametrize("actor", ["owner", "member"])
@pytest.mark.parametrize(
    "field",
    [
        "subject",
        "form_status",
        "callback_status",
        "session_status",
        "product_cookie",
        "consent_status",
        "consent_post_count",
        "consent_post_status",
        "consent_decision",
        "native_consent",
        "app_status",
    ],
)
def test_r71_p1_neither_actor_may_drop_any_first_login_fact(actor, field):
    evidence = r68_two_turn_browser_report()
    module().validate_browser_evidence(evidence, "b" * 64)
    del evidence["login"][actor][field]
    with pytest.raises(module().SmokeError, match="first-login"):
        module().validate_browser_evidence(evidence, "b" * 64)


@pytest.mark.parametrize("actor", ["owner", "member"])
@pytest.mark.parametrize(
    "field",
    [
        "subject",
        "form_status",
        "callback_status",
        "session_status",
        "product_cookie",
        "consent_status",
        "consent_post_count",
        "consent_post_status",
        "consent_decision",
        "native_consent",
        "app_status",
    ],
)
@pytest.mark.parametrize("bad", [None, False, 0, "", [], {}])
def test_r71_p1_both_first_login_proofs_reject_malformed_json_fields(actor, field, bad):
    evidence = r68_two_turn_browser_report()
    module().validate_browser_evidence(evidence, "b" * 64)
    evidence["login"][actor][field] = bad
    with pytest.raises(module().SmokeError, match="first-login"):
        module().validate_browser_evidence(evidence, "b" * 64)


@pytest.mark.parametrize("actor", ["owner", "member"])
def test_r71_p1_each_first_login_record_is_closed(actor):
    evidence = r68_two_turn_browser_report()
    module().validate_browser_evidence(evidence, "b" * 64)
    evidence["login"][actor]["legacy"] = True
    with pytest.raises(module().SmokeError, match="first-login"):
        module().validate_browser_evidence(evidence, "b" * 64)


@pytest.mark.parametrize("tail", [False, True])
def test_r73_illegal_stream_order_is_not_a_real_terminal_text(tail):
    import json
    import subprocess

    helper = Path("scripts/e2e/chat_snapshot_evidence.mjs").resolve().as_uri()
    source = """
import assert from 'node:assert/strict';
import {runTextEvidence,hydratedRunText} from HELPER;
const frame=(id,type,delta)=>({id,event:{runId:'run_second',type,...(delta?{delta}:{})}});
const start=frame('start','RUN_STARTED'),finish=frame('finish','RUN_FINISHED'),text=frame('text','TEXT_MESSAGE_CONTENT','tail');
const hydration={event_watermark:'base',execution_head:{run_id:'run_second',state:'active'},messages:[{message_id:'assistant_second',run_id:'run_second',role:'assistant',status:'streaming',content:'base'}]};
const receipt={run_id:'run_second',assistant_message_id:'assistant_second',user_message_id:'user_second'};
assert.throws(()=>TAIL?hydratedRunText(hydration,[finish,text],receipt,'base'):runTextEvidence([finish,start,text],'run_second'));
""".replace("HELPER", json.dumps(helper)).replace("TAIL", "true" if tail else "false")
    result = subprocess.run(
        ["node", "--input-type=module", "-e", source],
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_r73_marker_only_dom_with_missing_tail_does_not_pass_actual_render_gate():
    import json
    import subprocess

    driver = Path("scripts/e2e/web_real_model_worker_chromium.mjs").read_text()
    start = driver.index("  async function readRenderedMessages(")
    end = driver.index("\n  const firstMarker", start)
    reader = driver[start:end]
    helper = Path("scripts/e2e/chat_snapshot_evidence.mjs").resolve().as_uri()
    source = """
import assert from 'node:assert/strict';
import {ChatSnapshotEvidenceError,renderedChatEvidence,assertRenderedChatUnchanged,uniqueRunFrames} from HELPER;
const uiFrames=()=>[];
const messages=[{message_id:'user_first',role:'user',status:'completed',content:'prompt'},
 {message_id:'assistant_first',run_id:'run_first',role:'assistant',status:'completed',content:'MARKER-full-tail'},
 {message_id:'user_second',role:'user',status:'completed',content:'second prompt'},
 {message_id:'assistant_second',run_id:'run_second',role:'assistant',status:'completed',content:'MARKER-second-tail'}];
let elements;
const cell=(message,body,visible=true)=>({dataset:{messageId:message.role==='user'?message.message_id:`assistant:${message.run_id}:message:${message.message_id}`},
 querySelectorAll:()=>[{textContent:body,children:[{tagName:'P',children:[]}],checkVisibility:()=>visible}]});
const reset=()=>{elements=messages.map(message=>cell(message,message.content))};
const page={locator:selector=>selector.includes('[data-conversation-thread-inner')?{evaluateAll:async callback=>callback(elements)}:{
 scrollIntoViewIfNeeded:async()=>{},evaluate:async(callback,role)=>callback(elements.find(element=>element.dataset.messageId===JSON.parse(/data-message-id=(.+)\\]$/u.exec(selector)[1])),role)}};
READER
reset();const baseline=await readRenderedMessages(messages);assert.ok(baseline);assert.equal(baseline.length,4);
assertRenderedChatUnchanged(baseline,await readRenderedMessages(messages));
elements[3]=cell(messages[3],'MARKER');assert.equal(await readRenderedMessages(messages),null);
reset();elements[3]=cell(messages[3],messages[3].content+messages[3].content);assert.equal(await readRenderedMessages(messages),null);
reset();elements.splice(0,2);assert.equal(await readRenderedMessages(messages),null);
reset();elements.reverse();assert.equal(await readRenderedMessages(messages),null);
reset();elements[0]=cell(messages[0],'changed prompt');assert.equal(await readRenderedMessages(messages),null);
reset();elements[3]=cell(messages[3],messages[3].content,false);assert.equal(await readRenderedMessages(messages),null);
reset();elements.push(cell(messages[3],messages[3].content));assert.equal(await readRenderedMessages(messages),null);
reset();assertRenderedChatUnchanged(baseline,await readRenderedMessages(messages));
""".replace("HELPER", json.dumps(helper)).replace("READER", reader)
    result = subprocess.run(
        ["node", "--input-type=module", "-e", source],
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "none",
        "zero",
        "input-bool",
        "negative-output",
        "segment-missing",
        "segment-total",
        "duplicate-generation",
        "future-generation",
        "bool-generation",
        "completed-missing",
        "completed-total",
    ],
)
def test_r73_durable_usage_proof_requires_positive_consistent_per_run_facts(mutation):
    m = module()
    agent = dict(generation=1, usage=valid_run_usage())
    if mutation == "missing":
        del agent["usage"]
    elif mutation == "none":
        agent["usage"] = None
    elif mutation == "zero":
        agent["usage"].update(input=0, output=0)
    elif mutation == "input-bool":
        agent["usage"]["input"] = True
    elif mutation == "negative-output":
        agent["usage"]["output"] = -1
    elif mutation == "segment-missing":
        agent["usage"]["segments"] = []
    elif mutation == "segment-total":
        agent["usage"]["segments"][0]["input"] = 6
    elif mutation == "duplicate-generation":
        agent["usage"]["segments"] *= 2
    elif mutation == "future-generation":
        agent["usage"]["segments"][0]["generation"] = 2
    elif mutation == "bool-generation":
        agent["usage"]["segments"][0]["generation"] = True
    elif mutation == "completed-missing":
        agent["usage"]["completed"] = None
    elif mutation == "completed-total":
        agent["usage"]["completed"]["output_tokens"] = 2
    with pytest.raises(m.SmokeError, match="durable usage"):
        m.validate_run_usage(agent)


def valid_provider_windows(evidence):
    return [
        dict(
            receipt=turn["receipt"],
            system=dict(
                requests=1,
                successes=1,
                response_bytes=100,
                pending=0,
                request_ids=[f"request-{index}"],
                user_sha256=[],
                routes=[valid_system_route()],
            ),
            model=dict(
                requests=1,
                successes=1,
                response_bytes=100,
                pending=0,
                request_ids=[],
                user_sha256=[turn["submitted_content_sha256"]],
                input_tokens=7,
                output_tokens=3,
                calls=[valid_model_call(index, turn["submitted_content_sha256"])],
            ),
        )
        for index, turn in enumerate(evidence["turns"])
    ]


@pytest.mark.parametrize(
    "mutation",
    [
        "second-zero",
        "pending",
        "duplicate-system-id",
        "missing-system-id",
        "wrong-latest-user",
        "historical-user-only",
        "wrong-receipt",
        "second-error",
    ],
)
def test_r73_per_receipt_provider_windows_reject_aggregate_only_evidence(mutation):
    evidence = r68_two_turn_browser_report()
    windows = valid_provider_windows(evidence)
    agents = [
        dict(request_id="request-0", usage=valid_run_usage()),
        dict(request_id="request-1", usage=valid_run_usage()),
    ]
    module().validate_provider_turns(evidence, windows, agents)
    if mutation == "second-zero":
        windows[0]["model"].update(
            requests=2,
            successes=2,
            user_sha256=[evidence["turns"][0]["submitted_content_sha256"]] * 2,
        )
        windows[1]["model"].update(
            requests=0, successes=0, response_bytes=0, user_sha256=[]
        )
    elif mutation == "pending":
        windows[0]["model"]["pending"] = 1
    elif mutation == "duplicate-system-id":
        windows[1]["system"]["request_ids"] = ["request-0"]
    elif mutation == "missing-system-id":
        windows[1]["system"]["request_ids"] = []
    elif mutation in ("wrong-latest-user", "historical-user-only"):
        windows[1]["model"]["user_sha256"] = [
            evidence["turns"][0]["submitted_content_sha256"]
        ]
    elif mutation == "wrong-receipt":
        windows[1]["receipt"] = windows[0]["receipt"]
    elif mutation == "second-error":
        windows[1]["model"]["successes"] = 0
    with pytest.raises(module().SmokeError):
        module().validate_provider_turns(evidence, windows, agents)


def test_r73_harness_stdio_windows_use_two_sequential_acks_without_new_service():
    import json
    import subprocess

    m = module()
    evidence = r68_two_turn_browser_report()

    class Proxy:
        def __init__(self, kind):
            self.kind = kind
            self.index = 0

        def snapshot(self):
            count = [0, 1, 1, 2, 2][self.index]
            self.index += 1
            rows = [
                dict(
                    request_id=f"request-{i}" if self.kind == "system" else None,
                    user_sha256=evidence["turns"][i]["submitted_content_sha256"]
                    if self.kind == "model"
                    else None,
                    input_tokens=7,
                    output_tokens=3,
                    route=valid_system_route(),
                    **{
                        key: value
                        for key, value in valid_model_call(
                            i, evidence["turns"][i]["submitted_content_sha256"]
                        ).items()
                        if key not in ("input_tokens", "output_tokens", "user_sha256")
                    },
                )
                for i in range(count)
            ]
            return dict(
                requests=count,
                successes=count,
                response_bytes=count * 100,
                pending=0,
                errors=0,
                observations=rows,
            )

    source = """
const {createInterface}=require('node:readline');
const reader=createInterface({input:process.stdin,crlfDelay:Infinity});const lines=reader[Symbol.asyncIterator]();
(async()=>{const payload=JSON.parse((await lines.next()).value);
 for(const [index,turn] of payload.turns.entries()){
  for(const stage of ['open','receipt','close']){
   process.stdout.write(JSON.stringify({kind:'observation-window',stage,index,...(stage==='open'?{}:{receipt:turn.receipt})})+'\\n');
   if(stage!=='receipt'){const ack=JSON.parse((await lines.next()).value);if(ack.kind!=='observation-ack'||ack.stage!==stage||ack.index!==index)throw Error('ack');}
  }
 }
 process.stdout.write(JSON.stringify(payload)+'\\n');reader.close();})();
"""
    child = subprocess.Popen(
        ["node", "-e", source],
        text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        output, errors, windows = m.read_driver_observations(
            child, evidence, Proxy("system"), Proxy("model"), 5
        )
        assert not errors
        assert json.loads(output) == evidence
        assert child.returncode == 0
        m.validate_provider_turns(
            evidence,
            windows,
            [
                dict(request_id="request-0", usage=valid_run_usage()),
                dict(request_id="request-1", usage=valid_run_usage()),
            ],
        )
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=2)
        for stream in (child.stdin, child.stdout, child.stderr):
            stream.close()


@pytest.mark.parametrize(
    "malformed",
    [
        b'{"error":{"message":"provider error"}}',
        b'data: {"error":{"message":"provider error"}}\n\n',
        b'data: {"choices":[]}\n\ndata: [DONE]\n\n',
    ],
)
def test_r73_model_http200_error_body_is_not_a_successful_model_stream(malformed):
    import http.client
    import json
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread

    m = module()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.rfile.read(int(self.headers["content-length"]))
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(malformed)))
            self.end_headers()
            self.wfile.write(malformed)

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=upstream.serve_forever, daemon=True)
    thread.start()
    proxy = m.ObservingProxy(
        f"http://127.0.0.1:{upstream.server_port}",
        kind="model",
        token="fixture",
        tenant="fixture",
        model="qwen3:8b",
        revision="fixture",
        timeout=2,
    )
    try:
        connection = http.client.HTTPConnection(
            "127.0.0.1", proxy.server_port, timeout=2
        )
        connection.request(
            "POST",
            "/v1/chat/completions",
            json.dumps(
                dict(
                    model="qwen3:8b",
                    stream=True,
                    stream_options=dict(include_usage=True),
                    messages=[dict(role="user", content="current user")],
                )
            ),
            {"authorization": "Bearer fixture"},
        )
        response = connection.getresponse()
        assert response.status == 200
        assert response.read() == malformed
        assert proxy.successes == 0
        assert proxy.errors == ["upstream_observation_failed"]
        connection.close()
    finally:
        proxy.close()
        upstream.shutdown()
        upstream.server_close()
        thread.join(timeout=2)


def valid_model_sse_frames():
    return [
        dict(
            id="completion-fixture",
            model="qwen3:8b",
            choices=[
                dict(index=0, delta=dict(content="plain text"), finish_reason=None)
            ],
            usage=None,
        ),
        dict(
            id="completion-fixture",
            model="qwen3:8b",
            choices=[dict(index=0, delta={}, finish_reason="stop")],
            usage=dict(prompt_tokens=7, completion_tokens=3, total_tokens=10),
        ),
    ]


@pytest.mark.parametrize(
    "mutation",
    [
        "id-drift",
        "model-drift",
        "bool-index",
        "missing-delta",
        "missing-finish",
        "bad-finish",
        "after-finish",
        "double-usage",
        "null-usage",
        "bool-usage",
        "float-usage",
        "zero-input",
        "usage-total",
        "duplicate-key",
        "nan",
        "missing-done",
        "double-done",
        "after-done",
        "truncated",
        "invalid-utf8",
        "event-error",
    ],
)
def test_r73_actual_model_sse_profile_requires_identity_usage_finish_and_closed_eof(
    mutation,
):
    import json

    m = module()
    frames = valid_model_sse_frames()
    if mutation == "id-drift":
        frames[1]["id"] = "other-completion"
    elif mutation == "model-drift":
        frames[1]["model"] = "other-model"
    elif mutation == "bool-index":
        frames[0]["choices"][0]["index"] = False
    elif mutation == "missing-delta":
        del frames[0]["choices"][0]["delta"]
    elif mutation == "missing-finish":
        frames[1]["choices"][0]["finish_reason"] = None
    elif mutation == "bad-finish":
        frames[1]["choices"][0]["finish_reason"] = "length"
    elif mutation == "after-finish":
        frames.append(
            dict(
                id=frames[0]["id"],
                model="qwen3:8b",
                choices=[dict(index=0, delta=dict(content="late"))],
            )
        )
    elif mutation == "double-usage":
        frames.append(
            dict(
                id=frames[0]["id"],
                model="qwen3:8b",
                choices=[],
                usage=frames[1]["usage"],
            )
        )
    elif mutation == "null-usage":
        frames[1]["usage"] = None
    elif mutation == "bool-usage":
        frames[1]["usage"]["prompt_tokens"] = True
    elif mutation == "float-usage":
        frames[1]["usage"]["completion_tokens"] = 3.0
    elif mutation == "zero-input":
        frames[1]["usage"].update(prompt_tokens=0, total_tokens=3)
    elif mutation == "usage-total":
        frames[1]["usage"]["total_tokens"] = 99
    raw = (
        "".join("data: " + json.dumps(frame) + "\n\n" for frame in frames).encode()
        + b"data: [DONE]\n\n"
    )
    if mutation == "duplicate-key":
        raw = raw.replace(
            b'"model": "qwen3:8b"', b'"model": "qwen3:8b", "model": "qwen3:8b"', 1
        )
    elif mutation == "nan":
        raw = raw.replace(b'"prompt_tokens": 7', b'"prompt_tokens": NaN')
    elif mutation == "missing-done":
        raw = raw.removesuffix(b"data: [DONE]\n\n")
    elif mutation == "double-done":
        raw += b"data: [DONE]\n\n"
    elif mutation == "after-done":
        raw += b"data: {}\n\n"
    elif mutation == "truncated":
        raw = raw[:-1]
    elif mutation == "invalid-utf8":
        raw = b"\xff" + raw
    elif mutation == "event-error":
        raw = b"event: error\ndata: {}\n\n" + raw
    with pytest.raises(m.SmokeError, match="model SSE"):
        m.model_stream_evidence(raw)


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_r73_actual_model_sse_accepts_usage_only_finish_and_plain_newlines(newline):
    import json

    m = module()
    frames = valid_model_sse_frames()
    usage = frames[-1].pop("usage")
    frames.append(
        dict(id="completion-fixture", model="qwen3:8b", choices=[], usage=usage)
    )
    raw = (
        "".join("data: " + json.dumps(frame) + newline * 2 for frame in frames)
        + "data: [DONE]"
        + newline * 2
    ).encode()
    assert m.model_stream_evidence(raw) == dict(
        input_tokens=7,
        output_tokens=3,
        completion_id="completion-fixture",
        model="qwen3:8b",
        finish_reason="stop",
        done_count=1,
    )


@pytest.mark.parametrize(
    "mode", ["valid", "missing-request-id", "duplicate-request-id", "wrong-response-id"]
)
def test_r73_real_system_proxy_requires_unique_echoed_request_id_and_actual_route(mode):
    import http.client
    import json
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread

    m = module()
    route = valid_system_route()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.rfile.read(int(self.headers["content-length"]))
            body = json.dumps(dict(data=route)).encode()
            self.send_response(200)
            self.send_header(
                "x-request-id",
                "wrong"
                if mode == "wrong-response-id"
                else self.headers["x-request-id"],
            )
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=upstream.serve_forever, daemon=True)
    thread.start()
    seed = dict(
        revision_id=route["revision_id"],
        provider_id=route["provider_id"],
        label_key=route["label_key"],
        model_name="qwen3:8b",
    )
    proxy = m.ObservingProxy(
        f"http://127.0.0.1:{upstream.server_port}",
        kind="system",
        token="fixture",
        tenant="tenant",
        model="qwen3:8b",
        revision=route["revision_id"],
        timeout=2,
        expected_route=seed,
    )
    try:
        for index in range(2 if mode in ("valid", "duplicate-request-id") else 1):
            connection = http.client.HTTPConnection(
                "127.0.0.1", proxy.server_port, timeout=2
            )
            headers = {
                "authorization": "Bearer fixture",
                "x-kokoro-service": "kokoro-agent",
                "x-kokoro-tenant-id": "tenant",
            }
            if mode != "missing-request-id":
                headers["x-request-id"] = (
                    "request-0"
                    if mode == "duplicate-request-id"
                    else f"request-{index}"
                )
            connection.request(
                "POST",
                "/v1/system/model-catalog/resolve",
                json.dumps(dict(feature_key="chat")),
                headers,
            )
            if mode == "missing-request-id" or (
                mode == "duplicate-request-id" and index == 1
            ):
                with pytest.raises(http.client.RemoteDisconnected):
                    connection.getresponse()
            else:
                response = connection.getresponse()
                assert response.status == 200
                response.read()
            connection.close()
        state = proxy.snapshot()
        if mode == "valid":
            assert state["successes"] == 2
            assert [row["request_id"] for row in state["observations"]] == [
                "request-0",
                "request-1",
            ]
            assert all(row["route"] == route for row in state["observations"])
            assert state["errors"] == state["pending"] == 0
        else:
            assert state["errors"] == 1
            assert state["successes"] == (1 if mode == "duplicate-request-id" else 0)
    finally:
        proxy.close()
        upstream.shutdown()
        upstream.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong-message",
        "wrong-input",
        "wrong-feature",
        "counter-bool",
        "terminal-unpublished",
        "terminal-duplicate",
        "terminal-seq",
        "terminal-status",
        "usage-missing-current",
    ],
)
def test_r73_durable_run_binds_receipt_input_terminal_tail_and_current_usage_generation(
    monkeypatch, mutation
):
    m = module()
    monkeypatch.setattr(m, "worker_owns_lease", lambda *_: True)
    first = dict(
        terminal=True,
        generation=1,
        owner="worker",
        session="conv_abc",
        run_count=2,
        file_writes=0,
        deliveries=0,
        events=["run.started", "run.completed"],
        usage=valid_run_usage(),
        **valid_agent_facts(0),
    )
    if mutation == "wrong-message":
        first["user_message_id"] = "user_second"
    elif mutation == "wrong-input":
        first["input_content"] = "unrelated earlier user"
    elif mutation == "wrong-feature":
        first["feature_key"] = "other"
    elif mutation == "counter-bool":
        first["durable_counter"] = True
    elif mutation == "terminal-unpublished":
        first["terminal_events"][0]["status"] = "queued"
    elif mutation == "terminal-duplicate":
        first["terminal_events"] *= 2
    elif mutation == "terminal-seq":
        first["terminal_events"][0]["seq"] = 4
    elif mutation == "terminal-status":
        first["terminal_events"][0]["payload"]["status"] = "failed"
    elif mutation == "usage-missing-current":
        first["generation"] = 2
    monkeypatch.setattr(m, "_query", lambda *_: first)
    with pytest.raises(m.SmokeError):
        m.durable_evidence(
            None, "owned-db", r68_two_turn_browser_report(), "tenant", 42, "b" * 64
        )


def test_r73_live_segment_anchors_bind_real_frames_then_match_owner_reload_full_content():
    import json
    import subprocess

    helper = Path("scripts/e2e/chat_snapshot_evidence.mjs").resolve().as_uri()
    source = """
import assert from 'node:assert/strict';
import {renderedChatEvidence,assertRenderedChatUnchanged} from HELPER;
const messages=[{message_id:'user_first',role:'user',content:'literal /no_think\\ninput'},
 {message_id:'assistant_first',role:'assistant',run_id:'run_first',content:'MARKER\\n\\nfull tail'}];
const rows=[{anchor:'user_first',role:'user',visible:true,plain:true,body:messages[0].content},
 {anchor:'assistant:run_first:message:segment_native',role:'assistant',visible:true,plain:true,body:'MARKER\\nfull tail'}];
const allowed=[['user_first'],['assistant:run_first:message:segment_native','assistant:run_first:message:assistant_first']];
const live=renderedChatEvidence(rows,messages,allowed);
const reloaded=renderedChatEvidence([rows[0],{...rows[1],anchor:'assistant:run_first:message:assistant_first'}],messages,allowed);
assertRenderedChatUnchanged(live,reloaded);
assert.throws(()=>renderedChatEvidence([rows[0],{...rows[1],anchor:'assistant:wrong_run:message:segment_native'}],messages,allowed));
assert.throws(()=>renderedChatEvidence([rows[0],{...rows[1],body:'MARKER'}],messages,allowed));
""".replace("HELPER", json.dumps(helper))
    result = subprocess.run(
        ["node", "--input-type=module", "-e", source],
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_r73_actual_tool_call_sse_requires_complete_arguments_and_terminal_usage():
    import json

    m = module()
    frames = [
        dict(
            id="completion-tool",
            model="qwen3:8b",
            choices=[
                dict(
                    index=0,
                    delta=dict(
                        tool_calls=[
                            dict(
                                index=0,
                                id="call-1",
                                type="function",
                                function=dict(name="write_file", arguments='{"path":'),
                            )
                        ]
                    ),
                    finish_reason=None,
                )
            ],
        ),
        dict(
            id="completion-tool",
            model="qwen3:8b",
            choices=[
                dict(
                    index=0,
                    delta=dict(
                        tool_calls=[
                            dict(index=0, function=dict(arguments='"/real-model.txt"}'))
                        ]
                    ),
                    finish_reason="tool_calls",
                )
            ],
            usage=dict(prompt_tokens=7, completion_tokens=3, total_tokens=10),
        ),
    ]

    def encode(rows):
        return (
            "".join("data: " + json.dumps(row) + "\n\n" for row in rows)
            + "data: [DONE]\n\n"
        ).encode()

    assert m.model_stream_evidence(encode(frames))["finish_reason"] == "tool_calls"
    frames[1]["choices"][0]["delta"]["tool_calls"][0]["function"]["arguments"] = (
        "broken"
    )
    with pytest.raises(m.SmokeError, match="model SSE"):
        m.model_stream_evidence(encode(frames))


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-call",
        "bool-done",
        "wrong-model",
        "wrong-user",
        "call-usage",
        "call-bytes",
        "call-sequence",
    ],
)
def test_r73_model_call_details_are_actual_bounded_and_sum_to_durable_usage(mutation):
    evidence = r68_two_turn_browser_report()
    windows = valid_provider_windows(evidence)
    agents = [
        dict(request_id="request-0", usage=valid_run_usage()),
        dict(request_id="request-1", usage=valid_run_usage()),
    ]
    module().validate_provider_turns(evidence, windows, agents)
    call = windows[1]["model"]["calls"][0]
    if mutation == "missing-call":
        windows[1]["model"]["calls"] = []
    elif mutation == "bool-done":
        call["done_count"] = True
    elif mutation == "wrong-model":
        call["model"] = "other-model"
    elif mutation == "wrong-user":
        call["user_sha256"] = evidence["turns"][0]["submitted_content_sha256"]
    elif mutation == "call-usage":
        call["input_tokens"] = 6
    elif mutation == "call-bytes":
        call["response_bytes"] = 99
    elif mutation == "call-sequence":
        call["sequence"] = 1
    with pytest.raises(module().SmokeError):
        module().validate_provider_turns(evidence, windows, agents)


@pytest.mark.parametrize(
    ("failure", "expected_phase"),
    [
        ("composer-visible", "product-composer-visible"),
        ("response-arm", "product-response-arm"),
        ("composer-fill", "product-composer-fill"),
        ("composer-fill-pending-rejection", "product-composer-fill"),
        ("observation-open", "product-observation-open"),
        ("send-click", "product-send-click"),
        ("response-await", "product-response-await"),
        ("http-json", "product-http-status"),
        ("http-non-json", "product-http-status"),
        ("receipt-json", "product-receipt-json"),
        ("receipt-request", "product-receipt-request"),
        ("receipt-identity", "product-receipt-identity"),
        ("conversation", "product-conversation"),
        ("observation-receipt", "product-observation-receipt"),
        ("receipt-uniqueness", "product-receipt-uniqueness"),
        ("second-composer-fill", "product-composer-fill"),
        ("none", None),
    ],
)
def test_r79_actual_submit_failure_has_static_specific_phase_without_sensitive_error(
    failure, expected_phase
):
    import json
    import subprocess

    driver = Path("scripts/e2e/web_real_model_worker_chromium.mjs").read_text()
    start = driver.index("  async function submit(content) {")
    end = driver.index("\n  const uiFrames =", start)
    submit = driver[start:end]
    catch = driver[driver.rindex("} catch (error) {") : driver.rindex("} finally {")]
    # Execute the actual submit and actual outer error formatter, not a parallel
    # diagnostic implementation. Playwright I/O is replaced only at its boundary.
    source = r"""
const assert = (condition, message) => { if (!condition) throw new Error(message) };
class ChatSnapshotEvidenceError extends Error {}
const failure = FAILURE;
const secret = 'https://private.example/iam?code=PRIVATE_OAUTH&token=PRIVATE_TOKEN password=PRIVATE_PASSWORD content=PRIVATE_CONTENT <div>PRIVATE_DOM</div>';
const fail = () => { throw new Error(secret) };
const input = {web_origin:'https://web-fixture.example.test',timeout_ms:20000};
let phase='owner-login',conversation,eventPath,snapshotPath;
const receipts=[],posts=[],boundaries=[],steps=[];
let currentResponse;
const isFailure = name => failure===name || (failure==='second-composer-fill' && name==='composer-fill' && receipts.length===1);
const composer = {
 waitFor:async options=>{steps.push('wait');assert(options.timeout===20000,'timeout');if(isFailure('composer-visible'))fail()},
 fill:async content=>{steps.push('fill');if(isFailure('composer-fill') || failure==='composer-fill-pending-rejection')fail()}
};
const page = {
 waitForResponse:(predicate,options)=>{
  steps.push('arm');assert(options.timeout===20000,'timeout');if(isFailure('response-arm'))fail();
  const request={method:()=> 'POST'};
  const index=receipts.length;
  const receipt={run_id:'run_'+index,user_message_id:'user_'+index,assistant_message_id:'assistant_'+index};
  if(isFailure('receipt-identity'))receipt.extra=secret;
  if(isFailure('receipt-uniqueness') && index===1)receipt.run_id='run_0';
  const badHttp=isFailure('http-json') || isFailure('http-non-json');
  currentResponse={
   url:()=>input.web_origin+'/api/session/sessions/'+(isFailure('conversation')?'private-invalid':'conv_fixture')+'/messages',
   request:()=>request,status:()=>badHttp?503:202,
   json:async()=>{if(isFailure('receipt-json') || isFailure('http-non-json'))fail();return receipt}
  };
  assert(predicate(currentResponse),'response predicate');
  posts.push({request,content:isFailure('receipt-request')?secret:'PRIVATE_CONTENT'});
  if(isFailure('response-await') || failure==='composer-fill-pending-rejection')
   return new Promise((_,reject)=>setTimeout(()=>reject(new Error(secret)),0));
  return Promise.resolve(currentResponse);
 },
 locator:selector=>{assert(selector==='[data-composer-action="send"]','selector');return {click:async()=>{steps.push('click');if(isFailure('send-click'))fail()}}}
};
async function observationBoundary(stage,index,receipt){
 boundaries.push({stage,index});
 if(isFailure('observation-'+stage))fail();
}
SUBMIT
try {
 await submit('PRIVATE_CONTENT');
 if(failure==='none' || failure==='receipt-uniqueness' || failure==='second-composer-fill')await submit('PRIVATE_CONTENT');
 assert(receipts.length===2,'two receipts');
 assert(steps.join(',')==='wait,arm,fill,click,wait,arm,fill,click','original steps');
 assert(JSON.stringify(boundaries)===JSON.stringify([{stage:'open',index:0},{stage:'receipt',index:0},{stage:'open',index:1},{stage:'receipt',index:1}]),'original boundaries');
 process.stdout.write('two actual submit controls retained\n');
CATCH
}
"""
    source = (
        source.replace("FAILURE", json.dumps(failure))
        .replace("SUBMIT", submit)
        .replace("CATCH", catch)
    )
    result = subprocess.run(
        ["node", "--input-type=module", "-e", source],
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    if expected_phase is None:
        assert result.returncode == 0, result.stderr
        assert result.stdout == "two actual submit controls retained\n"
        assert result.stderr == ""
    else:
        assert result.returncode == 1
        assert result.stdout == ""
        assert result.stderr == f"REAL_MODEL_FAILURE:{expected_phase}\n"
        assert all(
            secret not in result.stderr
            for secret in (
                "private.example",
                "PRIVATE_OAUTH",
                "PRIVATE_TOKEN",
                "PRIVATE_PASSWORD",
                "PRIVATE_CONTENT",
                "PRIVATE_DOM",
            )
        )
