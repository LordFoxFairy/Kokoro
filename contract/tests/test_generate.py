"""Golden-file gate for the contract generator: fixed spec -> byte-stable mirrors."""

from __future__ import annotations

import sys
import subprocess
import tempfile
from pathlib import Path

import pytest

CONTRACT = Path(__file__).resolve().parents[1]
ROOT = CONTRACT.parent
sys.path.insert(0, str(CONTRACT))

from generate import build, emit_platform_runtime_ts, load  # noqa: E402

OUTPUTS = build()


def _find(suffix: str) -> str:
    return next(c for p, c in OUTPUTS.items() if str(p).endswith(suffix))


def test_deterministic() -> None:
    assert build() == OUTPUTS


def test_mirrors_match_on_disk() -> None:
    stale = [
        str(path.relative_to(ROOT))
        for path, content in OUTPUTS.items()
        if not path.exists() or path.read_text() != content
    ]
    assert not stale, f"stale mirrors (run contract/generate.py): {stale}"


@pytest.mark.parametrize(
    "path,content",
    list(OUTPUTS.items()),
    ids=[str(p.relative_to(ROOT)) for p in OUTPUTS],
)
def test_generated_header(path: Path, content: str) -> None:
    assert content.startswith(
        (
            "# GENERATED — DO NOT EDIT",
            "// GENERATED — DO NOT EDIT",
            "<!-- GENERATED — DO NOT EDIT",
        )
    )


def test_raw_and_browser_kinds() -> None:
    events = load("events.yaml")
    raw = [e["kind"] for e in events["raw_kinds"]]
    browser = list(events["browser_order"])
    assert len(raw) == 20 and "run.started" in raw
    assert len(browser) == 21
    assert "run.started" not in browser
    assert {"session.created", "run.created"}.issubset(browser)

    wire = _find("kokoro-session/src/contract/wire-events.ts")
    events_py = _find("contract/events.py")
    for kind in raw:
        assert f'z.literal("{kind}")' in wire, kind
        assert f'Literal["{kind}"]' in events_py, kind

    session = _find("kokoro-session/src/contract/session-events.ts")
    names = _find("kokoro-web/apps/user/src/contract/event-names.ts")
    for kind in browser:
        assert f'z.literal("{kind}")' in session, kind
        assert f'"{kind}",' in names, kind
    # run.started is raw-only: never a browser literal.
    assert 'z.literal("run.started")' not in session


def test_no_legacy_vocabulary() -> None:
    # 注：request_id 曾在禁用列表,但已是合法 control 词汇——HITL submit 决策的幂等锚
    # (contract/spec/control.yaml 定义)。故移出;其余仍为应绝迹的旧词汇。
    blob = "\n".join(OUTPUTS.values())
    for banned in (
        "agui_out_web_extra",
        "conversation_id",
        "execution_style",
        "permission_mode",
        "awaiting_kind",
        'z.literal("text.delta")',
        'z.literal("text.completed")',
        'Literal["text.delta"]',
    ):
        assert banned not in blob, banned
    # the new vocabulary must be present.
    assert 'z.literal("message.delta")' in blob
    assert 'z.literal("session.created")' in blob


def test_run_request_shape() -> None:
    control_py = _find("contract/control.py")
    # handbook RunRequest: run_id + thread_id + nested input/runtime/context; no session_id top field.
    assert "thread_id: NonEmptyStr" in control_py
    assert "input: RunInput" in control_py
    assert "runtime: RuntimeConfig" in control_py
    assert "context: RuntimeContext" in control_py


def test_web_and_session_share_outbound_bytes() -> None:
    assert _find("kokoro-session/src/contract/session-events.ts") == _find(
        "kokoro-web/apps/user/src/contract/session-events.ts"
    )
    assert _find("kokoro-session/src/contract/control.ts") == _find(
        "kokoro-web/apps/user/src/contract/control.ts"
    )
    assert _find("kokoro-session/src/contract/http.ts") == _find(
        "kokoro-web/apps/user/src/contract/http.ts"
    )


def test_platform_and_session_share_runtime_contract_bytes() -> None:
    spec = load("platform-runtime.yaml")
    generated = emit_platform_runtime_ts(spec)
    assert generated == _find(
        "kokoro-platform/kokoro-platform-kit/src/contract/platform-runtime.ts"
    )
    assert generated == _find("kokoro-session/src/contract/platform-runtime.ts")
    for symbol in (
        "usageHoldRequestSchema",
        "usageSettleRequestSchema",
        "releaseCreditRequestSchema",
        "resolveModelBindingsQuerySchema",
        "listModelLabelsQuerySchema",
        "modelTransportKindSchema",
    ):
        assert f"export const {symbol}" in generated


def test_node_generator_declares_boundary_scoped_bundles() -> None:
    generator = (CONTRACT / "generate.mjs").read_text()

    for boundary in (
        "platform-admin-auth@v1",
        "platform-admin-identity@v1",
        "platform-admin-query@v2",
        "platform-admin-command@v2",
        "platform-site-lifecycle@v1",
    ):
        assert boundary in generator
    assert "await protoFiles(protoRoot)" not in generator
    assert 'schemaId: "kokoro.platform.admin.v1.AdminAuthService"' not in generator


def test_node_generator_isolates_new_boundary_output() -> None:
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "bundle"
        result = subprocess.run(
            [
                "node",
                str(CONTRACT / "generate.mjs"),
                "--boundary",
                "platform-site-lifecycle@v1",
                "--output",
                str(output),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        metadata = (output / "contract-metadata.ts").read_text()
        assert 'schemaId: "kokoro.platform.site.v1.SiteLifecycleService"' in metadata
        assert '"kokoro/platform/site/v1/site_lifecycle.proto"' in metadata
        assert '"kokoro/platform/admission/v1/admission.proto"' not in metadata
        assert (output / "kokoro/platform/site/v1/site_lifecycle_pb.ts").is_file()
        assert not (output / "kokoro/platform/admission/v1/admission_pb.ts").exists()


def test_admin_auth_v1_frozen_metadata_is_reproducible() -> None:
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "bundle"
        result = subprocess.run(
            [
                "node",
                str(CONTRACT / "generate.mjs"),
                "--boundary",
                "platform-admin-auth@v1",
                "--output",
                str(output),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        committed = (
            ROOT
            / "kokoro-platform/kokoro-platform-admin/src/generated/contracts/contract-metadata.ts"
        )
        assert (output / "contract-metadata.ts").read_bytes() == committed.read_bytes()
        committed_helper = committed.with_name("admin-auth-effect-digest.ts")
        assert (
            output / "admin-auth-effect-digest.ts"
        ).read_bytes() == committed_helper.read_bytes()
