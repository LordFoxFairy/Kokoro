"""Fail-closed guards for the real model composition, no infrastructure startup."""

from pathlib import Path
import importlib
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


def test_stage_validation_requires_text_and_artifact_from_one_run():
    m = module()
    evidence = valid_evidence()
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
    evidence = valid_evidence()
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
    payload = (
        b'data: {"choices":[{"delta":{"content":"real upstream"}}]}\n\ndata: [DONE]\n\n'
    )

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
        body = {"model": "qwen3:8b", "stream": True, "messages": []}
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
        results = iter([{**row, **change}, {"count": 1}])
        monkeypatch.setattr(m, "_query", lambda *_: next(results))
        if change:
            with pytest.raises(m.SmokeError, match="lease/journal/terminal"):
                m.durable_evidence(
                    None, "owned-db", valid_evidence(), "tenant", 42, "b" * 64
                )
        else:
            assert m.durable_evidence(
                None, "owned-db", valid_evidence(), "tenant", 42, "b" * 64
            )["storage"] == {"count": 1}


def test_durable_evidence_accepts_owner_resource_ids_but_rejects_sql_input(monkeypatch):
    m = module()
    monkeypatch.setattr(m, "worker_owns_lease", lambda *_: True)
    row = {
        "terminal": True,
        "generation": 1,
        "owner": "worker",
        "file_writes": 1,
        "deliveries": 1,
        "events": ["delivery.created", "run.completed"],
    }
    evidence = {
        **valid_evidence(),
        "artifact_id": "artifact:abc123",
        "asset_id": "asset:abc123",
    }
    results = iter([row, {"count": 1}])
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
    assert 'system_db = stack._owner_schema_database_url(c["owner_db_url"], "system")' in real
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
        Mock(return_value={"PGOPTIONS": "-c search_path=public,pg_catalog -c timezone=UTC"}),
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
        Mock(side_effect=lambda *_args: {"PGOPTIONS": "-c search_path=public,pg_catalog -c timezone=UTC"}),
    )
    monkeypatch.setattr(smoke, "OwnedResources", Mock(return_value=resources))
    monkeypatch.setattr(smoke, "free_port", Mock(side_effect=[4100, 4200]))
    monkeypatch.setattr(
        smoke, "iam_admission_stub", Mock(return_value=nullcontext("http://127.0.0.1:4300"))
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
        "psql", resources.postgres, "-X", "-Atc", "SELECT 1"
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
        {"session": "conv_two_turns", "run": f"run_bff_turn_{i}"}
        for i in range(count)
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
        [
            {"session": "conv_two_turns", "run": f"run_bff_turn_{i}"}
            for i in range(3)
        ],
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
