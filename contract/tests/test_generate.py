"""Golden-file gate for the contract generator: fixed spec -> byte-stable mirrors."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

CONTRACT = Path(__file__).resolve().parents[1]
ROOT = CONTRACT.parent
sys.path.insert(0, str(CONTRACT))

from generate import build, load  # noqa: E402

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
        ("# GENERATED — DO NOT EDIT", "// GENERATED — DO NOT EDIT", "<!-- GENERATED — DO NOT EDIT")
    )


def test_raw_and_browser_kinds() -> None:
    events = load("events.yaml")
    raw = [e["kind"] for e in events["raw_kinds"]]
    browser = list(events["browser_order"])
    assert len(raw) == 16 and "run.started" in raw
    assert len(browser) == 17
    assert "run.started" not in browser
    assert {"session.created", "run.created"}.issubset(browser)

    wire = _find("kokoro-session/src/contract/wire-events.ts")
    events_py = _find("contract/events.py")
    for kind in raw:
        assert f'z.literal("{kind}")' in wire, kind
        assert f'Literal["{kind}"]' in events_py, kind

    session = _find("kokoro-session/src/contract/session-events.ts")
    names = _find("kokoro-web/src/contract/event-names.ts")
    for kind in browser:
        assert f'z.literal("{kind}")' in session, kind
        assert f'"{kind}",' in names, kind
    # run.started is raw-only: never a browser literal.
    assert 'z.literal("run.started")' not in session


def test_no_legacy_vocabulary() -> None:
    blob = "\n".join(OUTPUTS.values())
    for banned in (
        "agui_out_web_extra",
        "conversation_id",
        "execution_style",
        "permission_mode",
        "request_id",
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
        "kokoro-web/src/contract/session-events.ts"
    )
    assert _find("kokoro-session/src/contract/control.ts") == _find(
        "kokoro-web/src/contract/control.ts"
    )
    assert _find("kokoro-session/src/contract/http.ts") == _find("kokoro-web/src/contract/http.ts")
